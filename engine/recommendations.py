"""Written recommendations synthesised from the findings a drafter has accepted.

    data/workstreams/{workstream_id}/recommendations/{node_id}.json
        {"generated_at", "dimensions_used", "recommendations": [...]}

The step the tool used to stop short of. Triage leaves Aisyah holding thirty
accepted comparisons — "our clause 8.4 is silent where HKMA's 4.2 is not" — and
no answer to what the policy document should say. This module turns those into
recommendations: what to do, why, and on which clause.

Three properties do the real work:

**Dimensions come from the drafter, not the tool.** The working draft's own
`policy_requirement` field (a comma-separated list she maintains) supplies the
axes. The tool never invents its own categories, so a recommendation is always
framed in vocabulary she authored and therefore understands. No requirements
recorded → no generation, and the route says so.

**Evidence is only what she accepted.** Scope is
`workstreams.neighbourhood_edges` — the same rule the Pairwise Findings box
uses, called rather than reimplemented so the two surfaces cannot disagree about
what is in scope. On `open-finance-pd-2026` the task node has ONE edge and that
pair has no findings file at all, so any narrower rule yields nothing.

**The evidence floor is enforced in code, not merely prompted.** After parsing,
every citation is resolved against the accepted set; a recommendation whose
citations all fail to resolve is DROPPED before anything is persisted. That is
what makes the repo's verbatim-citation rule structural here rather than a hope
about prompt adherence — see `enforce_evidence_floor`. Clause text is copied off
the finding record, never re-derived, so a recommendation cannot cite text its
own evidence does not contain.

Generation is a SINGLE model pass, deliberately unlike the finder→critic loop in
`engine.finder_pipeline`. The guardrails are constraints inside that one call, not a second
scoring stage — which is also why no relevance score reaches the interface: there
is no independent judgement to report, and a self-assigned score would invite
trust it has not earned.
"""

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from engine import findings as findings_mod
from engine import guardrails as guardrails_mod
from engine import node_metadata, workstreams
from engine.config import RECOMMENDATIONS_DEPLOYMENT
from engine.llm import call_chat, parse_json_response

# The fields a persisted recommendation carries. Mirrors the columns the BNM
# reviewer actually worked with in the sample assessment — Recommendation,
# Rationale, Action for BNM, Referenced rows — minus Type and Relevance score
# (both deliberately dropped, see the spec's resolved questions), plus the four
# this feature introduces: dimensions, confidence_note, bookmarked, revisions.
RECOMMENDATION_FIELDS: tuple[str, ...] = (
    "id",
    "title",
    "rationale",
    "action",
    "dimensions",
    "evidence",
    "confidence_note",
    "bookmarked",
    "comments",
    "revisions",
)


class RecommendationsError(Exception):
    """Generation or rewriting failed. Carries a stable `code` so the route can
    map it without a second lookup."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def recommendations_path(
    workstreams_dir: Path, workstream_id: str, node_id: str
) -> Path:
    return workstreams_dir / workstream_id / "recommendations" / f"{node_id}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_recommendation_id() -> str:
    """An opaque 12-hex id, matching the ids the `open-finance-*` findings
    fixtures already ship (`4f9f91c02ef5`).

    Deliberately NOT index-derived like `findings.finding_id`: a regeneration
    reorders the list, so `{node}~{i}` would silently re-point a bookmark at a
    different recommendation. Opacity is the safety property here.
    """
    return secrets.token_hex(6)


# --------------------------------------------------------------------------
# Dimensions — the drafter's own policy requirements
# --------------------------------------------------------------------------


def parse_dimensions(profile: Optional[dict[str, Any]]) -> list[str]:
    """The axes recommendations are formulated on, from `policy_requirement`.

    Splits every member on commas, strips whitespace, drops empties, and
    de-duplicates while preserving first-seen order — so
    `["consent management, API security", " consent management "]` yields
    `["consent management", "API security"]`.

    Tolerates a bare string as well as a list, because side-files written before
    the field became a list carry scalars (the three retired fixtures still store
    `applicability` that way). An absent profile or field yields `[]`, which is
    what gates generation.
    """
    if not profile:
        return []
    raw = profile.get("policy_requirement")
    if raw is None:
        return []
    members = [raw] if isinstance(raw, str) else raw
    if not isinstance(members, list):
        return []

    out: list[str] = []
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, str):
            continue
        for part in member.split(","):
            cleaned = part.strip()
            if not cleaned or cleaned.lower() in seen:
                continue
            seen.add(cleaned.lower())
            out.append(cleaned)
    return out


def dimensions_for_task(
    workstreams_dir: Path, workstream_id: str, node_id: str
) -> list[str]:
    """The task's own dimensions. Neighbours' requirements are NOT pooled in —
    that would make the set unpredictable and require every neighbouring
    document to be enriched first."""
    profile = node_metadata.load_metadata(workstreams_dir, workstream_id, node_id)
    return parse_dimensions(profile)


# --------------------------------------------------------------------------
# Evidence — accepted findings across the task's neighbourhood
# --------------------------------------------------------------------------


def _node_title(ws_graph: dict[str, Any], node_id: str) -> Optional[str]:
    for node in ws_graph.get("nodes", []):
        if node["id"] == node_id:
            return node.get("title")
    return None


def _first_clause(clauses: Any) -> tuple[Optional[str], Optional[str]]:
    """The clause number and its verbatim text, or `(None, None)`."""
    if not clauses:
        return (None, None)
    first = clauses[0]
    return (first.get("clause_number"), first.get("text"))


def collect_evidence(
    workstreams_dir: Path, workstream_id: str, node_id: str, ws_graph: dict[str, Any]
) -> list[dict[str, Any]]:
    """Every ACCEPTED finding in the task's neighbourhood, as evidence records.

    Clause text is copied straight off the finding, never re-derived from the
    corpus — that is the verbatim-citation guarantee on this path. Dismissed and
    pending findings are not evidence: a recommendation rests only on what the
    drafter has agreed with.
    """
    scope = workstreams.neighbourhood_edges(ws_graph.get("edges", []), node_id)
    evidence: list[dict[str, Any]] = []
    for edge in scope:
        try:
            edge_findings = findings_mod.load(
                workstreams_dir, workstream_id, edge["id"]
            )
        except findings_mod.FindingsNotAnalysedError:
            continue  # unanalysed edge — nothing to have accepted yet
        for finding in edge_findings:
            if finding.get("review_state") != "accepted":
                continue
            src_num, src_text = _first_clause(finding.get("source_clauses"))
            tgt_num, tgt_text = _first_clause(finding.get("target_clauses"))
            evidence.append(
                {
                    "finding_id": finding["id"],
                    "edge_id": edge["id"],
                    "label": finding.get("label"),
                    "sentiment": finding.get("sentiment"),
                    "summary": finding.get("summary"),
                    "left": {
                        "id": edge["source"],
                        "title": _node_title(ws_graph, edge["source"]),
                    },
                    "right": {
                        "id": edge["target"],
                        "title": _node_title(ws_graph, edge["target"]),
                    },
                    "source_clause_number": src_num,
                    "source_clause_text": src_text,
                    "target_clause_number": tgt_num,
                    "target_clause_text": tgt_text,
                }
            )
    return evidence


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------


def empty_record(dimensions: list[str]) -> dict[str, Any]:
    """What a task with no generated set looks like. `generated_at` is `None`,
    which is how the interface tells "never generated" from "generated, empty"."""
    return {
        "generated_at": None,
        "dimensions_used": dimensions,
        "recommendations": [],
    }


def load(workstreams_dir: Path, workstream_id: str, node_id: str) -> dict[str, Any]:
    """The stored set, or an empty record. A missing file is never an error —
    a task exists long before its recommendations do."""
    path = recommendations_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        return empty_record([])
    return json.loads(path.read_text(encoding="utf-8"))


def save(
    workstreams_dir: Path, workstream_id: str, node_id: str, record: dict[str, Any]
) -> dict[str, Any]:
    """Persist the whole record. UTF-8 always — evidence carries clause text with
    § and en-dashes, which the cp1252 platform default mangles on Windows."""
    path = recommendations_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


class RecommendationNotFoundError(Exception):
    """No recommendation on this task carries the given id."""


MAX_COMMENT_CHARS: int = 4_000


class CommentTooLargeError(Exception):
    """The comment exceeds MAX_COMMENT_CHARS."""


class EmptyCommentError(Exception):
    """The comment was whitespace-only."""


def add_comment(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    rec_id: str,
    text: str,
    author: dict[str, Any],
) -> dict[str, Any]:
    """Append a comment to one recommendation, and persist. No model call.

    The comment stays ON THE CARD. It informs that card's rewrite and is available
    to the Copilot, and it goes with the card when a regeneration replaces it.
    Nothing here writes to the guardrails: promoting a situated note into a
    standing rule would have a model authoring the rules it then follows, and an
    over-broad rule would suppress good recommendations invisibly. Making a
    correction permanent is the drafter's own deliberate edit.
    """
    cleaned = text.strip()
    if not cleaned:
        raise EmptyCommentError()
    if len(cleaned) > MAX_COMMENT_CHARS:
        raise CommentTooLargeError(len(cleaned))

    path = recommendations_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        raise FileNotFoundError(path)

    record = json.loads(path.read_text(encoding="utf-8"))
    for rec in record.get("recommendations", []):
        if rec.get("id") == rec_id:
            rec.setdefault("comments", []).append(
                {"author": author, "at": _now(), "text": cleaned}
            )
            save(workstreams_dir, workstream_id, node_id, record)
            return rec
    raise RecommendationNotFoundError(rec_id)


def build_rewrite_prompt(
    rec: dict[str, Any],
    evidence: list[dict[str, Any]],
    guardrails_body: str,
) -> str:
    """The user turn for rewriting ONE recommendation.

    Carries the card as it stands, every comment on it, and the same evidence pool
    the original was drawn from. The comments are the point: they hold what the
    drafter knows and the corpus does not.
    """
    parts: list[str] = []

    if guardrails_body.strip():
        parts.append(
            "GUARDRAILS — the drafter's standing rules. The rewrite must obey "
            "these:\n" + guardrails_body.strip() + "\n"
        )

    parts.append(
        "THE RECOMMENDATION AS IT STANDS — rewrite this one, and only this one:\n"
        f"title: {rec.get('title', '')}\n"
        f"rationale: {rec.get('rationale', '')}\n"
        f"action: {rec.get('action', '')}\n"
        f"dimensions: {', '.join(rec.get('dimensions') or [])}\n"
    )

    comments = rec.get("comments") or []
    if comments:
        parts.append(
            "THE DRAFTER'S CORRECTIONS — why it misses. These carry institutional "
            "knowledge the documents do not contain; take them as authoritative:\n"
            + "\n".join(f"- {c.get('text', '')}" for c in comments)
            + "\n"
        )

    lines: list[str] = []
    for item in evidence:
        left = item["left"].get("title") or item["left"]["id"]
        right = item["right"].get("title") or item["right"]["id"]
        lines.append(f"finding_id: {item['finding_id']}")
        lines.append(f"  relationship: {item.get('label')}")
        if item.get("summary"):
            lines.append(f"  summary: {item['summary']}")
        if item.get("source_clause_number"):
            lines.append(
                f"  {left} clause {item['source_clause_number']}: "
                f"{item.get('source_clause_text') or ''}"
            )
        if item.get("target_clause_number"):
            lines.append(
                f"  {right} clause {item['target_clause_number']}: "
                f"{item.get('target_clause_text') or ''}"
            )
        lines.append("")
    parts.append(
        "ACCEPTED FINDINGS — the ONLY evidence you may cite:\n" + "\n".join(lines)
    )

    parts.append(
        'Return ONLY a JSON object: {"recommendations": [ ... one object ... ]}, '
        "in the same shape and under the same field formats as a fresh "
        "recommendation."
    )
    return "\n".join(parts)


def rewrite_one(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    rec_id: str,
    ws_graph: dict[str, Any],
    *,
    generate_fn: Any,
) -> dict[str, Any]:
    """Rewrite one recommendation from its comments, and persist.

    Preserves identity — `id`, `bookmarked`, `dimensions`, `comments`, and the
    card's position in the list. Appends the superseded text to `revisions`, so a
    rewrite is auditable rather than silent (the same append-only discipline
    `linkage_review.py`'s `audit` uses).

    **The evidence floor applies here too.** If the rewritten version resolves no
    citations, the rewrite is REJECTED and the original kept — a rewrite may never
    launder a recommendation past the citation rule.

    Nothing is written until parsing and the floor have both passed, so a failed
    rewrite leaves the file byte-identical and the comment intact.
    """
    path = recommendations_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        raise FileNotFoundError(path)

    record = json.loads(path.read_text(encoding="utf-8"))
    index = next(
        (
            i
            for i, rec in enumerate(record.get("recommendations", []))
            if rec.get("id") == rec_id
        ),
        None,
    )
    if index is None:
        raise RecommendationNotFoundError(rec_id)

    current = record["recommendations"][index]
    evidence = collect_evidence(workstreams_dir, workstream_id, node_id, ws_graph)

    raw = generate_fn(
        dimensions=current.get("dimensions") or [],
        evidence=evidence,
        guardrails_body=guardrails_mod.body_for_prompt(workstreams_dir, workstream_id),
        pinned_titles=[],
        draft_title=None,
        rewrite_of=current,
    )
    fresh, _dropped = enforce_evidence_floor(parse_response(raw), evidence)
    if not fresh:
        raise RecommendationsError(
            "REWRITE_FAILED",
            "The rewrite could not be completed. The recommendation is unchanged.",
        )

    rewritten = fresh[0]
    record["recommendations"][index] = {
        # Identity carries over: a rewrite is the same recommendation, restated.
        "id": current["id"],
        "bookmarked": current.get("bookmarked", False),
        "dimensions": current.get("dimensions") or [],
        "comments": current.get("comments") or [],
        # Append-only: the superseded text, so the change is visible. `evidence`
        # is deliberately not snapshotted — it projects accepted findings that
        # still exist and are still quotable.
        "revisions": (current.get("revisions") or [])
        + [
            {
                "at": _now(),
                "title": current.get("title", ""),
                "rationale": current.get("rationale", ""),
                "action": current.get("action", ""),
                "confidence_note": current.get("confidence_note", ""),
            }
        ],
        "title": rewritten["title"],
        "rationale": rewritten["rationale"],
        "action": rewritten["action"],
        "evidence": rewritten["evidence"],
        "confidence_note": rewritten["confidence_note"],
    }
    save(workstreams_dir, workstream_id, node_id, record)
    return record["recommendations"][index]


def set_bookmarked(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    rec_id: str,
    bookmarked: bool,
) -> dict[str, Any]:
    """Mark or unmark one recommendation, and persist. Idempotent.

    Returns the updated recommendation. Raises `RecommendationNotFoundError` when
    `rec_id` is not in the file, or `FileNotFoundError` when nothing has been
    generated for this task yet — those are different mistakes and the route
    reports them differently.

    `rec_id` only ever indexes a list in memory; the file is keyed by `node_id`,
    which the route resolves against the graph first. So this parameter cannot
    reach the filesystem.
    """
    path = recommendations_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        raise FileNotFoundError(path)

    record = json.loads(path.read_text(encoding="utf-8"))
    for rec in record.get("recommendations", []):
        if rec.get("id") == rec_id:
            rec["bookmarked"] = bookmarked
            save(workstreams_dir, workstream_id, node_id, record)
            return rec
    raise RecommendationNotFoundError(rec_id)


def coverage(
    record: dict[str, Any], evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Accepted findings that no recommendation drew on.

    **Derived on every read, never stored.** A persisted figure would drift from
    the findings it describes the moment a review state changed — the drafter
    dismisses one finding and the count silently becomes a lie.
    """
    cited = {
        item.get("finding_id")
        for rec in record.get("recommendations", [])
        for item in rec.get("evidence", [])
    }
    return [item for item in evidence if item["finding_id"] not in cited]


# --------------------------------------------------------------------------
# Prompt assembly
# --------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You advise a Bank Negara Malaysia (BNM) policy drafter on what her working draft \
should say. She has reviewed AI-found linkages between her draft's neighbourhood \
of documents and ACCEPTED the ones she agrees with. Turn those accepted findings \
into written recommendations.

FIELD FORMATS — these are hard limits, not preferences. A field that breaks its \
format is wrong even if its content is right.

title
  One line, MAXIMUM 80 characters. Begin with a verb: Add, Clarify, Retain, \
Align, Reconsider, Reconcile. No trailing explanation.
  GOOD: "Publish the authorised data consumer list"
  BAD:  "Confirm the draft's data-protection compliance anchor is retained as \
the core requirement for data sharing"

rationale
  A bullet list. 2 to 4 bullets. Each bullet on its OWN LINE, beginning with \
"- ". One sentence per bullet, MAXIMUM 30 words. Quote or cite a clause in at \
least one bullet. NO paragraph before or after the list. Never return the \
rationale as continuous prose.
  GOOD:
  - ED S 10.4 requires the consent dashboard to reflect real-time status.
  - HKMA's framework sets no equivalent dashboard requirement.
  - The draft therefore goes beyond the peer baseline here.
  BAD: "The draft's S 10.4 requires that the consent dashboard reflects the \
real-time status of consent and is updated immediately, and clause 11 insists \
on explicit consent, so this is a genuine enhancement rather than a shared \
baseline."

action
  1 to 2 sentences, MAXIMUM 40 words total. Operative and concrete — a drafter \
must be able to act on it without asking what you meant.

dimensions
  Which of the drafter's policy requirements this touches, in her exact wording. \
Several is fine.

evidence
  The accepted findings this rests on, by finding_id. Cite only ids from the \
ACCEPTED FINDINGS section. Never invent one.

confidence_note
  ONE sentence. MAXIMUM 25 words. Begin "Cannot verify" or "Assumes". No \
semicolons, no second clause, no restating the recommendation. Name the single \
most important thing you could not establish from the documents — often \
institutional knowledge, like who owns an implementation plan or which \
department owns an instrument. If nothing is unverified: "Nothing unverified."
  GOOD: "Cannot verify which department owns the consent dashboard \
specification."
  BAD:  "I cannot verify from the documents which BNM department owns the \
consent-dashboard technical specification or how the dashboard interoperates \
with platform operators; I assume the PD itself is the governing instrument."

TONE, everywhere
Professional, authoritative, objective. State positions; do not hedge. Plain \
words over technical ones where they do the same work. Every sentence carries a \
fact, a clause reference, or a consequence — cut anything that only restates the \
title or fills space. Never pad to look thorough. Avoid "leverage", "robust", \
"holistic", "seeks to", "it is worth noting", "in order to".

How many recommendations you write is up to the evidence. A dimension may attract \
several or none. Do NOT write a recommendation for a dimension no accepted \
finding bears on — say nothing rather than inventing support.

Return ONLY a JSON object of the form \
{"recommendations": [{"title": ..., "rationale": ..., "action": ..., \
"dimensions": [...], "evidence": [{"finding_id": ...}], "confidence_note": ...}]} \
— no prose, no markdown fences around the JSON itself.\
"""


def build_prompt(
    dimensions: list[str],
    evidence: list[dict[str, Any]],
    guardrails_body: str,
    pinned_titles: list[str],
    draft_title: Optional[str] = None,
) -> str:
    """The user-turn prompt: guardrails, dimensions, evidence, and what is already
    taken forward.

    `pinned_titles` are the bookmarked recommendations. They enter the prompt for
    exactly one reason — so the new batch does not restate them in different
    words. Their evidence deliberately STAYS in the evidence pool: a finding that
    legitimately bears on two dimensions must still be able to support a new
    recommendation about the second.
    """
    parts: list[str] = []

    if draft_title:
        parts.append(f"WORKING DRAFT: {draft_title}\n")

    # Guardrails first, and framed as non-negotiable: they are the drafter's own
    # standing rules, and four of the five encode a way the tool has already been
    # observed to get this wrong.
    if guardrails_body.strip():
        parts.append(
            "GUARDRAILS — the drafter's standing rules. Every recommendation must "
            "obey these; they take precedence over anything else here:\n"
            f"{guardrails_body.strip()}\n"
        )

    parts.append(
        "POLICY REQUIREMENTS — the dimensions to reason over. These are the "
        "drafter's own words; use them verbatim in `dimensions`:\n"
        + "\n".join(f"- {d}" for d in dimensions)
        + "\n"
    )

    if pinned_titles:
        parts.append(
            "ALREADY TAKEN FORWARD — the drafter has bookmarked these. Do NOT "
            "restate them, in these words or reworded. Recommend something else:\n"
            + "\n".join(f"- {t}" for t in pinned_titles)
            + "\n"
        )

    lines: list[str] = []
    for item in evidence:
        left = item["left"].get("title") or item["left"]["id"]
        right = item["right"].get("title") or item["right"]["id"]
        lines.append(f"finding_id: {item['finding_id']}")
        lines.append(f"  relationship: {item.get('label')}")
        if item.get("sentiment"):
            lines.append(f"  sentiment: {item['sentiment']}")
        if item.get("summary"):
            lines.append(f"  summary: {item['summary']}")
        if item.get("source_clause_number"):
            lines.append(
                f"  {left} clause {item['source_clause_number']}: "
                f"{item.get('source_clause_text') or ''}"
            )
        if item.get("target_clause_number"):
            lines.append(
                f"  {right} clause {item['target_clause_number']}: "
                f"{item.get('target_clause_text') or ''}"
            )
        lines.append("")
    parts.append(
        "ACCEPTED FINDINGS — the ONLY evidence you may cite. Every `finding_id` "
        "you return must appear here:\n" + "\n".join(lines)
    )

    return "\n".join(parts)


# --------------------------------------------------------------------------
# Response parsing + the evidence floor
# --------------------------------------------------------------------------


def parse_response(raw: str) -> list[dict[str, Any]]:
    """The model's recommendations, or `RecommendationsError`.

    Accepts either `{"recommendations": [...]}` or a bare array — both are shapes
    a model plausibly returns, and rejecting the second on a technicality would
    fail a generation that is otherwise fine.
    """
    try:
        parsed = parse_json_response(raw)
    except Exception as exc:
        raise RecommendationsError(
            "RECOMMENDATIONS_FAILED", f"Model response was not valid JSON: {exc}"
        ) from exc

    if isinstance(parsed, dict):
        items = parsed.get("recommendations")
    elif isinstance(parsed, list):
        items = parsed
    else:
        items = None

    if not isinstance(items, list):
        raise RecommendationsError(
            "RECOMMENDATIONS_FAILED",
            "Model response had no `recommendations` array.",
        )
    return [item for item in items if isinstance(item, dict)]


def _normalise_rationale(raw: Any) -> str:
    """A newline-separated `- ` bullet list, whatever shape the model returned.

    The prompt asks for a bullet list. A model may honour that as a single string
    with newlines, or as a JSON array of bullets — both are reasonable readings,
    and `str()` on the array would render `['- one', '- two']` on the card,
    brackets and quotes included. Normalising here keeps that shape question out
    of the frontend, which should not have to know how the model felt that day.

    Bullet markers are normalised to `- ` and added where a list item lacks one,
    so the card's renderer has exactly one format to parse.
    """
    if raw is None:
        return ""

    if isinstance(raw, list):
        lines = [str(entry).strip() for entry in raw]
    else:
        lines = [line.strip() for line in str(raw).split("\n")]

    out: list[str] = []
    for line in lines:
        if not line:
            continue
        # A single unbulleted paragraph stays a paragraph — the card renders that
        # correctly too, and forcing a bullet onto continuous prose would imply a
        # structure the model did not write.
        if len(lines) > 1 or line.startswith(("-", "*", "•")):
            line = "- " + line.lstrip("-*• ").strip()
        out.append(line)
    return "\n".join(out)


def enforce_evidence_floor(
    items: list[dict[str, Any]], evidence: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    """Resolve every citation against the accepted set; drop what cannot stand.

    Returns `(kept, dropped_count)`. A recommendation survives only if at least
    one of its `evidence[].finding_id` values names a real accepted finding, and
    it keeps only the citations that resolved. Each surviving citation is replaced
    wholesale by the evidence record we built from the finding itself — so the
    clause number and clause text are ours, copied from disk, never the model's
    paraphrase of them.

    This is the difference between the citation rule being enforced and being
    merely requested. A model that hallucinates an id gets its recommendation
    dropped, not published.
    """
    by_id = {item["finding_id"]: item for item in evidence}
    kept: list[dict[str, Any]] = []
    dropped = 0

    for item in items:
        cited = item.get("evidence")
        resolved: list[dict[str, Any]] = []
        seen: set[str] = set()
        if isinstance(cited, list):
            for citation in cited:
                fid = (
                    citation.get("finding_id")
                    if isinstance(citation, dict)
                    else citation
                )
                if isinstance(fid, str) and fid in by_id and fid not in seen:
                    seen.add(fid)
                    resolved.append(by_id[fid])

        if not resolved:
            dropped += 1
            continue

        dimensions = item.get("dimensions")
        kept.append(
            {
                "id": new_recommendation_id(),
                "title": str(item.get("title") or "").strip(),
                "rationale": _normalise_rationale(item.get("rationale")),
                "action": str(item.get("action") or "").strip(),
                "dimensions": [
                    str(d) for d in dimensions if isinstance(d, str)
                ]
                if isinstance(dimensions, list)
                else [],
                "evidence": resolved,
                "confidence_note": str(item.get("confidence_note") or "").strip(),
                "bookmarked": False,
                "comments": [],
                "revisions": [],
            }
        )

    return kept, dropped


# --------------------------------------------------------------------------
# The model seam
# --------------------------------------------------------------------------


def generate_recommendations(
    *,
    dimensions: list[str],
    evidence: list[dict[str, Any]],
    guardrails_body: str,
    pinned_titles: list[str],
    draft_title: Optional[str] = None,
    rewrite_of: Optional[dict[str, Any]] = None,
    deployment: str = RECOMMENDATIONS_DEPLOYMENT,
) -> str:
    """Call the model once and return its RAW text.

    Raw, not parsed, so the seam a test injects is as thin as possible: a stub
    returns a JSON string and every layer above it — parsing, the evidence floor,
    persistence — runs for real in the test.

    ONE seam serves both paths. With `rewrite_of` set the prompt is the
    single-card rewrite (its current text plus the drafter's comments); otherwise
    it is a fresh generation. A test that stubs this covers both, and the system
    prompt's field formats apply either way.
    """
    user = (
        build_rewrite_prompt(rewrite_of, evidence, guardrails_body)
        if rewrite_of is not None
        else build_prompt(
            dimensions, evidence, guardrails_body, pinned_titles, draft_title
        )
    )
    return call_chat(deployment, _SYSTEM_PROMPT, user, max_tokens=16384)


def generate(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    ws_graph: dict[str, Any],
    *,
    generate_fn: Any = generate_recommendations,
    draft_title: Optional[str] = None,
) -> dict[str, Any]:
    """Generate a fresh set, keeping bookmarked recommendations byte-for-byte.

    Raises `RecommendationsError` with `NO_POLICY_REQUIREMENTS` or
    `NO_ACCEPTED_FINDINGS` before any model call — a gate that spends a model
    call to discover it is closed is not a gate.

    The write happens only after a successful, floor-passing parse, so a failed
    generation leaves the previous set byte-identical on disk.
    """
    dimensions = dimensions_for_task(workstreams_dir, workstream_id, node_id)
    if not dimensions:
        raise RecommendationsError(
            "NO_POLICY_REQUIREMENTS",
            "Recommendations are formulated on the draft's policy requirements, "
            "and none are recorded.",
        )

    evidence = collect_evidence(workstreams_dir, workstream_id, node_id, ws_graph)
    if not evidence:
        raise RecommendationsError(
            "NO_ACCEPTED_FINDINGS",
            "No findings have been accepted yet. Accept findings in the Pairwise "
            "findings box first.",
        )

    existing = load(workstreams_dir, workstream_id, node_id)
    pinned = [
        rec for rec in existing.get("recommendations", []) if rec.get("bookmarked")
    ]

    raw = generate_fn(
        dimensions=dimensions,
        evidence=evidence,
        guardrails_body=guardrails_mod.body_for_prompt(workstreams_dir, workstream_id),
        pinned_titles=[rec.get("title", "") for rec in pinned],
        draft_title=draft_title,
    )
    fresh, dropped = enforce_evidence_floor(parse_response(raw), evidence)

    record = {
        "generated_at": _now(),
        "dimensions_used": dimensions,
        # Pinned first and untouched: a bookmark is a decision the drafter made,
        # and regenerating must not cost her that decision.
        "recommendations": pinned + fresh,
    }
    save(workstreams_dir, workstream_id, node_id, record)
    return {**record, "dropped_unsupported": dropped}
