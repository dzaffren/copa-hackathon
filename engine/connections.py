"""Two-agent connection-finding (finder + critic) + citation validator.

Design (see docs/specs/rulebook-radar/spec-knowledge-graph-engine.md,
"Stage 4 is a two-agent loop: finder → critic → verifier"): stage 4 is a small
agentic loop over a *pair* of documents' clause text, not a single LLM call:

- **[4a] Finder agent** reads the two documents' clause text and proposes
  candidate connections, each citing clause number(s).
- **[4b] Critic agent** (i) refutes weak candidates / scopes them (e.g. adds a
  ``scope_note`` about an exemption) and (ii) surfaces connections the finder
  missed (recall). It emits the scoped/refuted set *plus* newly-found
  connections.
- **[5] Citation validator** — deterministic *code*, not an agent. For every
  surviving candidate it looks up every cited clause number in the supplied
  ``ClauseIndex``. A candidate whose clauses ALL resolve goes to ``connections``
  with ``supported: true`` and verbatim clause text attached (fetched from the
  index by number — never model-produced). A candidate with ANY missing clause
  goes to ``unsupported`` with ``supported: false`` and message
  "No matching clause found". Nothing is ever fabricated; an unsupported
  candidate is never written as a low-confidence connection.

Both agent turns are **injectable seams** (``finder_fn`` / ``critic_fn``) with
real Azure-AI-Foundry defaults that mirror the network seam already established
in ``engine.clauses.find_clause_anchors`` (a thin function that constructs the
Azure ``ChatCompletionsClient`` and is never called by tests). Tests stub BOTH
turns with recorded/hand-written responses — no network access, no credentials.

Every run records a ``connection-trace-{pair}.json`` (model id, timestamp, raw
finder output, raw critic output, and the full validation trace) — the demo
backstop that proves connections were AI-found (not curated) and the
deterministic fallback if the live API hiccups mid-pitch. Each surviving finding
is classified with a five-label semantic taxonomy — ``aligns-with``,
``differs-on`` (optionally refined by a ``tighten``/``loosen``/``neutral``
sentiment), ``conflicts-with``, ``silent-on``, or ``goes-beyond`` — under the
fixed direction convention that document A is "we/ours" and document B is
"they/theirs" (so ``silent-on`` and ``goes-beyond`` swap when the pair flips).
The clause TEXT and clause NUMBERS shown to users still come only from the
``ClauseIndex`` — the label describes the relationship, never the citation.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Literal, Optional, TypedDict

from engine.clauses import ClauseIndex
from engine.config import FINDER_CRITIC_DEPLOYMENT
from engine.llm import LLMResponseError, call_chat, parse_json_response

logger = logging.getLogger(__name__)


class ClauseCitation(TypedDict):
    """A clause reference on a supported connection, with verbatim text
    fetched from the ``ClauseIndex`` by number — never model-produced."""

    clause_number: str
    text: str


class Connection(TypedDict):
    """A supported clause-anchored connection (matches the spec's
    ``POST /connections/find`` 200 ``connections[]`` shape).

    ``label`` is the semantic classification of the finding (one of the five
    mutually-exclusive, exhaustive values). ``sentiment`` refines a
    ``differs-on`` finding as tighten/loosen/neutral and is ``None`` for every
    other label. Direction convention: document A is "we/ours", document B is
    "they/theirs", so ``silent-on`` (ours is silent) and ``goes-beyond`` (ours
    goes further) swap when the pair is flipped."""

    summary: str
    label: Literal[
        "aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"
    ]
    sentiment: Optional[Literal["tighten", "loosen", "neutral"]]
    source_clauses: list[ClauseCitation]
    target_clauses: list[ClauseCitation]
    scope_note: Optional[str]
    supported: bool


class UnsupportedConnection(TypedDict):
    """A candidate that cited at least one clause absent from the index —
    reported honestly, never invented, never promoted to a connection.

    ``label`` and ``sentiment`` record what the model attempted before the
    citation validator dropped it (the audit trail); either may be ``None`` when
    the candidate proposed none."""

    summary: str
    label: Optional[str]
    sentiment: Optional[str]
    message: str
    supported: bool


class FindConnectionsResult(TypedDict):
    connections: list[Connection]
    unsupported: list[UnsupportedConnection]


# A finder turn reads the two documents (via the clause index) and returns raw
# candidate dicts: {summary, source_clauses: [clause_number, ...],
# target_clauses: [...], scope_note?: str}. A critic turn additionally receives
# the finder's candidates and returns the scoped/refuted set plus newly-found
# connections, in the same raw shape.
FinderFn = Callable[[str, str, ClauseIndex], list[dict]]
CriticFn = Callable[[str, str, ClauseIndex, list[dict]], list[dict]]

_MESSAGE_NO_CLAUSE = "No matching clause found"

# The five mutually-exclusive, exhaustive semantic labels a finding may carry,
# and the three sentiments that MAY refine a ``differs-on`` finding (and only
# that one). Kept as tuples so error messages can list the allowed values.
CONNECTION_LABELS = (
    "aligns-with",
    "differs-on",
    "conflicts-with",
    "silent-on",
    "goes-beyond",
)
SENTIMENT_VALUES = ("tighten", "loosen", "neutral")
_SENTIMENT_LABEL = "differs-on"


class ConnectionFindError(Exception):
    """Raised when connection-finding cannot proceed (e.g. no Foundry
    credentials for the real finder/critic seam)."""


def find_connections(
    doc_a_id: str,
    doc_b_id: str,
    clause_index: ClauseIndex,
    finder_fn: Optional[FinderFn] = None,
    critic_fn: Optional[CriticFn] = None,
    output_dir: Optional[Path] = None,
    now: Optional[datetime] = None,
    model_id: str = FINDER_CRITIC_DEPLOYMENT,
) -> FindConnectionsResult:
    """Run the pairwise finder → critic → citation-validator loop.

    Args:
        doc_a_id, doc_b_id: the two documents to search for connections
            between (the pairwise unit — see spec Solution Design).
        clause_index: the built ``ClauseIndex``; used both to give the agents
            clause text and, deterministically, to validate every citation and
            fetch verbatim text for supported connections.
        finder_fn: stage 4a seam — proposes candidate connections. Defaults to
            the real Azure-AI-Foundry call (``_finder_turn``); tests inject a
            stub so no network/credentials are needed.
        critic_fn: stage 4b seam — refutes/scopes and surfaces missed
            connections. Defaults to ``_critic_turn``; tests inject a stub.
        output_dir: where to write ``connection-trace-{pair}.json``. Defaults
            to ``data/artifacts/`` (the tracked demo backstop) — tests pass a
            tmp dir so no nondeterministic file lands in the tracked artifacts.
        now: timestamp for the trace, injectable for deterministic tests;
            defaults to wall-clock UTC at runtime.
        model_id: the deployment id recorded in the trace; defaults to
            ``FINDER_CRITIC_DEPLOYMENT``.

    Returns:
        ``{"connections": [...], "unsupported": [...]}`` — supported
        connections carry verbatim clause text; unsupported candidates are
        reported with "No matching clause found", never invented.
    """
    finder = finder_fn if finder_fn is not None else _finder_turn
    critic = critic_fn if critic_fn is not None else _critic_turn
    timestamp = now if now is not None else datetime.now(timezone.utc)

    # [4a] finder proposes; [4b] critic scopes/refutes + surfaces missed.
    finder_output = finder(doc_a_id, doc_b_id, clause_index)
    critic_output = critic(doc_a_id, doc_b_id, clause_index, finder_output)

    # [5] deterministic citation validator gates whatever survives the critic.
    connections, unsupported, validation = _validate_candidates(
        critic_output, clause_index
    )

    _write_trace(
        doc_a_id=doc_a_id,
        doc_b_id=doc_b_id,
        model_id=model_id,
        timestamp=timestamp,
        finder_output=finder_output,
        critic_output=critic_output,
        validation=validation,
        output_dir=output_dir,
    )

    return {"connections": connections, "unsupported": unsupported}


def _validate_candidates(
    candidates: list[dict], clause_index: ClauseIndex
) -> tuple[list[Connection], list[UnsupportedConnection], list[dict]]:
    """Split candidates into supported/unsupported by looking up every cited
    clause number in the index (the anti-hallucination guardrail).

    A candidate is supported only when EVERY clause it cites (source and
    target) resolves in the index; its clause text is then fetched verbatim by
    number — never taken from the candidate/model. Any missing clause drops the
    candidate to ``unsupported`` with "No matching clause found".

    Also returns a per-candidate validation trace (each cited clause and
    whether it resolved) for the recorded ``connection-trace``.

    The candidate's semantic ``label`` and ``sentiment`` are carried through
    verbatim onto every built record (supported and unsupported) and the trace —
    the model's classification of the relationship. This never touches the
    clause-resolution guardrail: clause TEXT is still fetched only via
    ``_cite``/``ClauseIndex`` by number.
    """
    connections: list[Connection] = []
    unsupported: list[UnsupportedConnection] = []
    validation: list[dict] = []

    for candidate in candidates:
        summary = candidate.get("summary", "")
        label = candidate.get("label")
        sentiment = candidate.get("sentiment")
        source_numbers = candidate.get("source_clauses", [])
        target_numbers = candidate.get("target_clauses", [])

        cited_results = [
            {"clause_number": number, "resolved": clause_index.get(number) is not None}
            for number in source_numbers + target_numbers
        ]
        all_resolved = all(item["resolved"] for item in cited_results)

        validation.append(
            {
                "summary": summary,
                "label": label,
                "sentiment": sentiment,
                "cited_clauses": cited_results,
                "supported": all_resolved,
            }
        )

        if all_resolved:
            connections.append(
                {
                    "summary": summary,
                    "label": label,
                    "sentiment": sentiment,
                    "source_clauses": _cite(source_numbers, clause_index),
                    "target_clauses": _cite(target_numbers, clause_index),
                    "scope_note": candidate.get("scope_note"),
                    "supported": True,
                }
            )
        else:
            unsupported.append(
                {
                    "summary": summary,
                    "label": label,
                    "sentiment": sentiment,
                    "message": _MESSAGE_NO_CLAUSE,
                    "supported": False,
                }
            )

    return connections, unsupported, validation


def _cite(clause_numbers: list[str], clause_index: ClauseIndex) -> list[ClauseCitation]:
    """Build verbatim citations for a list of resolved clause numbers.

    The quoted ``text`` ALWAYS comes back through ``ClauseIndex.get(...)["text"]``
    by number — never from the model. Callers must have already confirmed each
    number resolves (see ``_validate_candidates``); a missing entry here is a
    programming error, not a hallucination path.
    """
    citations: list[ClauseCitation] = []
    for number in clause_numbers:
        entry = clause_index.get(number)
        if entry is None:  # pragma: no cover - guarded by _validate_candidates
            raise ConnectionFindError(
                f"_cite called for unresolved clause '{number}' — validation "
                f"must gate citations before this point"
            )
        citations.append({"clause_number": number, "text": entry["text"]})
    return citations


def _write_trace(
    doc_a_id: str,
    doc_b_id: str,
    model_id: str,
    timestamp: datetime,
    finder_output: list[dict],
    critic_output: list[dict],
    validation: list[dict],
    output_dir: Optional[Path],
) -> Path:
    """Record the run's demo backstop: model id, timestamp, both raw agent
    outputs, and the full validation trace. Written to ``output_dir`` (a tmp
    dir in tests) or ``data/artifacts/`` by default."""
    if output_dir is None:
        from engine.config import REPO_ROOT

        output_dir = REPO_ROOT / "data" / "artifacts"

    output_dir.mkdir(parents=True, exist_ok=True)
    pair = f"{doc_a_id}__{doc_b_id}"
    trace_path = output_dir / f"connection-trace-{pair}.json"
    trace = {
        "model_id": model_id,
        "timestamp": timestamp.isoformat(),
        "document_ids": [doc_a_id, doc_b_id],
        "finder_output": finder_output,
        "critic_output": critic_output,
        "validation": validation,
    }
    trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return trace_path


# Shared taxonomy contract embedded in both agent prompts, so the finder and the
# critic classify findings the same way. States the fixed direction convention,
# the five mutually-exclusive labels, and the differs-on-only sentiment rule.
_TAXONOMY_PROMPT_BLOCK = (
    "DIRECTION CONVENTION (fixed): the first document is document A — treat it "
    'as "we/ours"; the second is document B — treat it as "they/theirs". Two '
    "labels are directional and would swap if the pair were flipped.\n\n"
    "Classify each connection with EXACTLY ONE label (these five are mutually "
    "exclusive and exhaustive):\n"
    "  - aligns-with: same axis; the two clauses agree, or one adopts the other "
    "without narrowing or widening.\n"
    "  - differs-on: same axis, different position. MAY carry a sentiment.\n"
    "  - conflicts-with: the two cannot both be followed (incompatible).\n"
    "  - silent-on: coverage asymmetry — OUR side (document A) does NOT cover "
    "it, THEIR side (document B) does.\n"
    "  - goes-beyond: coverage asymmetry — OUR side (document A) covers it, "
    "THEIR side (document B) does not.\n\n"
    "SENTIMENT (optional) attaches ONLY to a differs-on label and is exactly "
    "one of tighten / loosen / neutral (tighten = our position is stricter, "
    "loosen = more permissive, neutral = different but neither stricter nor "
    "looser). Omit sentiment for every other label.\n\n"
)

FINDER_SYSTEM_PROMPT = (
    "You are a policy analyst finding cross-policy CONNECTIONS between two "
    "Bank Negara Malaysia policy documents. You are given, for each document, "
    "its full list of clauses as `{clause_number}: {text}` lines, grouped "
    "under a document-id label.\n\n"
    "Find connections where a clause in one document relates to a clause in "
    "the other. " + _TAXONOMY_PROMPT_BLOCK + "For each connection, return an "
    "object:\n"
    '  {"summary": <one-sentence description>,\n'
    '   "label": <one of aligns-with|differs-on|conflicts-with|silent-on'
    "|goes-beyond>,\n"
    '   "sentiment": <tighten|loosen|neutral, ONLY on differs-on; omit '
    "otherwise>,\n"
    '   "source_clauses": [<clause_number>, ...],\n'
    '   "target_clauses": [<clause_number>, ...],\n'
    '   "scope_note": <optional caveat/exemption, omit if none>}\n\n'
    "CITATION RULE (strict): every clause_number in `source_clauses` and "
    "`target_clauses` MUST be copied EXACTLY from the clause lists provided. "
    "Never invent, guess, reformat, or paraphrase a clause number. Do not "
    "cite a clause that is not in the lists.\n\n"
    "Return ONLY a JSON array of these objects — no prose, no markdown, no "
    "commentary. Return an empty array `[]` if there are no connections."
)

CRITIC_SYSTEM_PROMPT = (
    "You are a senior policy reviewer critiquing a set of candidate "
    "cross-policy connections proposed by a finder agent. You are given both "
    "documents' full clause lists as `{clause_number}: {text}` lines grouped "
    "by document-id, plus the finder's candidate connections as a JSON array.\n\n"
    "Do two things:\n"
    "1. REFUTE or SCOPE weak candidates — drop any that do not hold, correct a "
    "wrong label, and for those that do hold add or refine a `scope_note` "
    "capturing any exemption, condition, or limit (e.g. an affiliate exemption "
    "clause).\n"
    "2. SURFACE MISSED connections the finder did not propose (recall).\n\n"
    + _TAXONOMY_PROMPT_BLOCK
    + "Return the scoped/refuted surviving candidates PLUS any newly-found "
    "connections, all in the SAME object shape:\n"
    '  {"summary": ..., "label": <one of aligns-with|differs-on|conflicts-with'
    "|silent-on|goes-beyond>, "
    '"sentiment": <tighten|loosen|neutral, ONLY on differs-on>, '
    '"source_clauses": [...], "target_clauses": [...], '
    '"scope_note": <optional>}\n\n'
    "CITATION RULE (strict): every clause_number MUST be copied EXACTLY from "
    "the provided clause lists. Never invent, guess, reformat, or paraphrase "
    "a clause number.\n\n"
    "Return ONLY a JSON array of these objects — no prose, no markdown."
)


def _format_clause_context(
    clause_index: ClauseIndex, doc_a_id: str, doc_b_id: str
) -> str:
    """Build the clause-context text block the agents read.

    Lists every clause of both documents as ``{clause_number}: {text}`` lines,
    grouped under a per-document label. Pure given the index — the clause text
    comes straight from ``ClauseIndex.entries_for_document`` (verbatim), never
    the model. Used by both turns so the finder and critic see the same corpus.
    """
    blocks: list[str] = []
    for document_id in (doc_a_id, doc_b_id):
        lines = [f"Document: {document_id}"]
        for entry in clause_index.entries_for_document(document_id):
            lines.append(f"{entry['clause_number']}: {entry['text']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _parse_candidate_list(raw: str, *, require_taxonomy: bool = True) -> list[dict]:
    """Parse an agent's raw reply into a candidate ``list[dict]``.

    Delegates to ``parse_json_response`` (strips fences, ``json.loads``) then
    enforces the raw candidate shape the citation validator consumes: a list of
    dict objects. Raises ``LLMResponseError`` (not a silent coercion) if the
    model returned a non-list or list items that are not objects.

    ``require_taxonomy`` (default ``True``) additionally enforces the five-label
    semantic taxonomy — each object MUST carry a valid ``label`` and, only on
    ``differs-on``, an optional ``sentiment``. The PAIRWISE finder/critic use the
    default. The two-branch ``_branch_finder_turn`` (which answers a DIFFERENT
    question — *which sources bear on a paragraph* — and correctly emits
    label-free candidates) passes ``require_taxonomy=False`` to skip that check.
    """
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        snippet = raw.strip()[:200]
        raise LLMResponseError(
            f"Expected a JSON array of connection objects; got "
            f"{type(parsed).__name__}. Raw (truncated): {snippet!r}"
        )
    bad = [
        (i, type(item).__name__)
        for i, item in enumerate(parsed)
        if not isinstance(item, dict)
    ]
    if bad:
        snippet = raw.strip()[:200]
        raise LLMResponseError(
            f"Expected every list item to be a JSON object; found "
            f"non-object items at {bad}. Raw (truncated): {snippet!r}"
        )
    if require_taxonomy:
        for i, item in enumerate(parsed):
            _validate_label_and_sentiment(item, i, raw)
    return parsed


def _validate_label_and_sentiment(item: dict, index: int, raw: str) -> None:
    """Enforce the semantic-taxonomy contract on one raw candidate object.

    Every candidate MUST carry a ``label`` drawn from ``CONNECTION_LABELS``. A
    ``sentiment`` (when present, i.e. not ``None``) MUST attach only to the
    ``differs-on`` label and MUST be one of ``SENTIMENT_VALUES``. Anything else
    raises ``LLMResponseError`` — the model's mistake is surfaced, never coerced.
    """
    snippet = raw.strip()[:200]
    label = item.get("label")
    if label is None:
        raise LLMResponseError(
            f"Candidate at index {index} is missing the required 'label' "
            f"(one of {list(CONNECTION_LABELS)}). Raw (truncated): {snippet!r}"
        )
    if label not in CONNECTION_LABELS:
        raise LLMResponseError(
            f"Candidate at index {index} has invalid label {label!r}; must be "
            f"one of {list(CONNECTION_LABELS)}. Raw (truncated): {snippet!r}"
        )
    sentiment = item.get("sentiment")
    if sentiment is None:
        return
    if label != _SENTIMENT_LABEL:
        raise LLMResponseError(
            f"Candidate at index {index} carries sentiment {sentiment!r} on "
            f"label {label!r}; sentiment attaches ONLY to '{_SENTIMENT_LABEL}'. "
            f"Raw (truncated): {snippet!r}"
        )
    if sentiment not in SENTIMENT_VALUES:
        raise LLMResponseError(
            f"Candidate at index {index} has invalid sentiment {sentiment!r}; "
            f"must be one of {list(SENTIMENT_VALUES)}. "
            f"Raw (truncated): {snippet!r}"
        )


def _finder_turn(
    doc_a_id: str, doc_b_id: str, clause_index: ClauseIndex
) -> list[dict]:
    """Call the finder LLM (Azure AI Foundry) to propose candidate connections.

    Builds the two-document clause context, sends it with
    ``FINDER_SYSTEM_PROMPT`` to ``FINDER_CRITIC_DEPLOYMENT`` (the confirmed
    high-reasoning deployment for this stage), and parses the reply into the
    raw candidate ``list[dict]`` shape ``_validate_candidates`` consumes. This
    is the network seam — real callers use it; tests inject ``finder_fn``.
    """
    context = _format_clause_context(clause_index, doc_a_id, doc_b_id)
    return _call_candidates_with_retry(FINDER_SYSTEM_PROMPT, context)


def _critic_turn(
    doc_a_id: str,
    doc_b_id: str,
    clause_index: ClauseIndex,
    candidates: list[dict],
) -> list[dict]:
    """Call the critic LLM (Azure AI Foundry) — refute/scope + surface missed
    connections (recall).

    Sends the same two-document clause context PLUS the finder's ``candidates``
    (serialised as JSON) with ``CRITIC_SYSTEM_PROMPT``, and parses the reply
    into the raw candidate ``list[dict]`` shape. The network seam for stage 4b;
    real callers use it, tests inject ``critic_fn``.
    """
    context = _format_clause_context(clause_index, doc_a_id, doc_b_id)
    user = (
        f"{context}\n\n"
        f"Finder candidate connections (JSON):\n{json.dumps(candidates)}"
    )
    return _call_candidates_with_retry(CRITIC_SYSTEM_PROMPT, user)


def _call_candidates_with_retry(
    system: str,
    user: str,
    attempts: int = 3,
    max_tokens: int = 16384,
    *,
    require_taxonomy: bool = True,
) -> list[dict]:
    """Call the finder/critic LLM and parse candidates, retrying on non-JSON.

    Claude occasionally returns prose instead of the requested JSON array; the
    failure is sporadic, so a re-ask usually succeeds. Call up to ``attempts``
    times, returning the first reply `_parse_candidate_list` accepts, else
    re-raise the last `LLMResponseError` so the run fails loudly rather than
    silently losing connections.

    ``require_taxonomy`` is forwarded to ``_parse_candidate_list`` — the pairwise
    finder/critic keep the default (True); the branch finder passes False.
    """
    last_error: LLMResponseError | None = None
    for attempt in range(1, attempts + 1):
        raw = call_chat(FINDER_CRITIC_DEPLOYMENT, system, user, max_tokens=max_tokens)
        try:
            return _parse_candidate_list(raw, require_taxonomy=require_taxonomy)
        except LLMResponseError as exc:
            last_error = exc
            logger.warning(
                "finder/critic returned non-JSON (attempt %d/%d): %s",
                attempt,
                attempts,
                exc,
            )
    assert last_error is not None
    raise last_error


# ---------------------------------------------------------------------------
# Two-branch paragraph orchestration (source-connection engine, spec Task 5).
#
# Distinct from the pairwise ``find_connections`` above (which stays green for
# its existing consumers): this analyses ONE paragraph of the uploaded vehicle
# document against a *split* source universe —
#
#   * Branch ① (cited)   — the sources the document itself cites.
#   * Branch ② (uncited) — relevant sources the document did NOT cite, matched
#                          against the preloaded curated library.
#
# Each branch runs a finder over its own candidate source ids; the combined,
# branch-tagged, guardrail-filtered candidate list is the input to the verdict
# stage (``engine.verdicts.propose_verdicts``), which the API runs afterwards.
# An EMPTY return is the signal the caller turns into ``no_matching_source``.
# ---------------------------------------------------------------------------

# Branch labels for the two-branch split. Branch ① is the document's own cited
# sources; branch ② is the un-cited curated library. They match the ``branch``
# values on the frozen ``engine.config.AI_DP_CONNECTIONS`` fixtures.
BRANCH_CITED = "cited"
BRANCH_UNCITED = "uncited"

# The default vehicle document id (the analysed AI Discussion Paper). Passed in
# so the deterministic candidate ``id`` matches the AI_DP_CONNECTIONS convention
# (``{document_id}:{paragraph}::{source}:{clause}``); overridable for other docs.
DEFAULT_DOCUMENT_ID = "ai-dp-2025"

# A branch finder turn reads one paragraph's text + a set of candidate sources
# (by document id, via the clause index) for a single branch and returns raw
# candidate dicts: each carries at least ``source_document_id`` +
# ``clause_number`` + ``confidence_score`` and MAY carry ``status:
# "could_not_retrieve"`` (+ ``reason``) for a blocked source, or ``verification:
# "pending_extraction"`` for a real source whose passage is not yet extracted.
BranchFinderFn = Callable[[str, str, ClauseIndex, str, list[str]], list[dict]]


def connections_for_paragraph(
    connections: list[dict], paragraph_number: str
) -> list[dict]:
    """Filter a list of connection specs to those touching ``paragraph_number``.

    The pre-baked read path uses this to slice the frozen showcase connections
    (shaped like ``engine.config.AI_DP_CONNECTIONS``) down to a single
    paragraph. Pure and side-effect-free — a straight ``paragraph ==`` match, so
    a paragraph with no connections yields an empty list (the caller turns that
    into ``no_matching_source`` / ``not_analysed`` as appropriate).
    """
    return [
        connection
        for connection in connections
        if connection.get("paragraph") == paragraph_number
    ]


def _candidate_id(
    document_id: str,
    paragraph_number: str,
    source_document_id: Optional[str],
    clause_number: Optional[str],
) -> str:
    """Build a deterministic connection id matching the AI_DP_CONNECTIONS
    convention: ``{document_id}:{paragraph}::{source}:{clause}`` when a clause is
    cited, and ``{document_id}:{paragraph}::{source}`` for a blocked source that
    carries no clause (e.g. MAS FEAT). Same inputs → same id, every run."""
    base = f"{document_id}:{paragraph_number}::{source_document_id}"
    if clause_number:
        return f"{base}:{clause_number}"
    return base


def _tag_candidate(
    candidate: dict,
    branch: str,
    paragraph_number: str,
    document_id: str,
) -> dict:
    """Stamp a raw finder candidate with the branch that produced it, the
    paragraph it touches, and a deterministic id.

    ``branch`` and ``paragraph`` are authoritative from the orchestration (the
    candidate came from this branch's finder call for this paragraph), so they
    are always set. The ``id`` is generated deterministically but only when the
    candidate does not already carry one, so a caller that pre-assigns an id (or
    a frozen fixture) is respected. Returns a shallow copy — the caller's raw
    dict is never mutated in place.
    """
    tagged = dict(candidate)
    tagged["branch"] = branch
    tagged["paragraph"] = paragraph_number
    tagged.setdefault(
        "id",
        _candidate_id(
            document_id,
            paragraph_number,
            candidate.get("source_document_id"),
            candidate.get("clause_number"),
        ),
    )
    return tagged


def _candidate_survives_guardrail(candidate: dict, clause_index: ClauseIndex) -> bool:
    """Anti-hallucination guardrail, mirroring ``verdicts.propose_verdicts``.

    A candidate is kept only when its cited ``clause_number`` resolves verbatim
    in the index, EXCEPT the two honest carve-outs that need no resolved clause:
    a blocked source (``status == "could_not_retrieve"``) and a
    ``pending_extraction`` source (a real source whose passage is not yet
    extracted — the read layer renders its quote text as null). Every other
    candidate whose clause does not resolve is dropped here, BEFORE the verdict
    stage, so anything returned is verbatim-resolvable or explicitly
    blocked/pending — never a fabricated citation.
    """
    if candidate.get("status") == "could_not_retrieve":
        return True
    if candidate.get("verification") == "pending_extraction":
        return True
    clause_number = candidate.get("clause_number")
    return clause_number is not None and clause_index.get(clause_number) is not None


def analyse_paragraph(
    paragraph_number: str,
    paragraph_text: str,
    clause_index: ClauseIndex,
    cited_source_ids: list[str],
    curated_source_ids: list[str],
    finder_fn: Optional[BranchFinderFn] = None,
    now: Optional[datetime] = None,
    output_dir: Optional[Path] = None,
    document_id: str = DEFAULT_DOCUMENT_ID,
) -> list[dict]:
    """Run the LIVE two-branch analysis for one paragraph (``POST …/analyse``).

    Branch ① runs a finder over the document's own ``cited_source_ids``; branch
    ② runs a finder over ``curated_source_ids`` (the un-cited library, matched by
    topic). Each raw candidate is branch-tagged, given a deterministic id, and
    passed through the same citation guardrail as the verdict stage. The combined
    branch-①+② candidate list is returned; the caller (the API) runs
    ``engine.verdicts.propose_verdicts`` over it and renders the records.

    Args:
        paragraph_number: the bare paragraph number (e.g. ``"3.2"``).
        paragraph_text: the paragraph's verbatim text — the finder reads it.
        clause_index: the built index; gates the guardrail and (downstream)
            supplies verbatim quote text by clause number.
        cited_source_ids: branch ① — the source document ids the document cites.
        curated_source_ids: branch ② — the un-cited curated library's source ids.
        finder_fn: injectable branch-finder seam. Defaults to the Azure-backed
            ``_branch_finder_turn`` (never called by tests); tests inject a stub
            returning canned candidates per branch, so no network is touched.
        now: timestamp for the optional trace; defaults to wall-clock UTC.
        output_dir: when provided, an ``analyse-trace-{paragraph}.json`` backstop
            is written there (mirroring ``find_connections``); ``None`` writes no
            trace (so a live API call leaves nothing in the tracked artifacts).
        document_id: the analysed document's id, used for the candidate ids;
            defaults to the vehicle DP (``ai-dp-2025``).

    Returns:
        The combined, branch-tagged, guardrail-filtered candidate list. An EMPTY
        list is the explicit signal for ``no_matching_source`` at the API — never
        a fabricated connection.
    """
    finder = finder_fn if finder_fn is not None else _branch_finder_turn
    timestamp = now if now is not None else datetime.now(timezone.utc)

    branch_specs = [
        (BRANCH_CITED, cited_source_ids),
        (BRANCH_UNCITED, curated_source_ids),
    ]

    candidates: list[dict] = []
    raw_by_branch: dict[str, list[dict]] = {}
    for branch, source_ids in branch_specs:
        raw = finder(paragraph_number, paragraph_text, clause_index, branch, source_ids)
        raw_by_branch[branch] = raw
        for candidate in raw:
            tagged = _tag_candidate(candidate, branch, paragraph_number, document_id)
            if _candidate_survives_guardrail(tagged, clause_index):
                candidates.append(tagged)

    if output_dir is not None:
        _write_analyse_trace(
            paragraph_number=paragraph_number,
            document_id=document_id,
            timestamp=timestamp,
            raw_by_branch=raw_by_branch,
            candidates=candidates,
            output_dir=output_dir,
        )

    return candidates


def _write_analyse_trace(
    paragraph_number: str,
    document_id: str,
    timestamp: datetime,
    raw_by_branch: dict[str, list[dict]],
    candidates: list[dict],
    output_dir: Path,
) -> Path:
    """Record the analyse run's demo backstop: each branch's raw finder output
    and the combined surviving candidate list. Written to ``output_dir`` (a tmp
    dir in tests) — the caller only asks for a trace when it supplies a dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = output_dir / f"analyse-trace-{paragraph_number}.json"
    trace = {
        "document_id": document_id,
        "paragraph": paragraph_number,
        "timestamp": timestamp.isoformat(),
        "raw_by_branch": raw_by_branch,
        "candidates": candidates,
    }
    trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    return trace_path


BRANCH_FINDER_SYSTEM_PROMPT = (
    "You are a policy analyst finding which SOURCES bear on a single paragraph "
    "of a Bank Negara Malaysia policy document. You are given the paragraph's "
    "text, the branch you are searching (`cited` = sources the document already "
    "cites; `uncited` = relevant sources it did not cite), and, for each "
    "candidate source, its clauses as `{clause_number}: {text}` lines grouped "
    "under a source-id label.\n\n"
    "For each source that genuinely bears on the paragraph, return an object:\n"
    '  {"source_document_id": <source id>,\n'
    '   "clause_number": <the single clause number that supports it>,\n'
    '   "confidence_score": <0.0-1.0>}\n\n'
    "CITATION RULE (strict): every `clause_number` MUST be copied EXACTLY from "
    "the clause lists provided. Never invent, guess, reformat, or paraphrase a "
    "clause number, and never claim a source that does not genuinely bear on "
    "the paragraph.\n\n"
    "Return ONLY a JSON array of these objects — no prose, no markdown. Return "
    "an empty array `[]` if no source in this branch bears on the paragraph."
)


def _format_source_context(
    clause_index: ClauseIndex, candidate_source_ids: list[str]
) -> str:
    """Build the candidate-source clause-context block the branch finder reads.

    Lists every clause of each candidate source as ``{clause_number}: {text}``
    lines, grouped under a per-source label. Pure given the index — the clause
    text comes straight from ``ClauseIndex.entries_for_document`` (verbatim),
    never the model. A source with no ingested passage (e.g. a blocked or
    node-only source) simply contributes its label and no clause lines.
    """
    blocks: list[str] = []
    for source_id in candidate_source_ids:
        lines = [f"Source: {source_id}"]
        for entry in clause_index.entries_for_document(source_id):
            lines.append(f"{entry['clause_number']}: {entry['text']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _branch_finder_turn(
    paragraph_number: str,
    paragraph_text: str,
    clause_index: ClauseIndex,
    branch: str,
    candidate_source_ids: list[str],
) -> list[dict]:
    """Call the branch-finder LLM (Azure AI Foundry) for one branch.

    Builds the paragraph + candidate-source clause context, sends it with
    ``BRANCH_FINDER_SYSTEM_PROMPT`` to ``FINDER_CRITIC_DEPLOYMENT``, and parses
    the reply into the raw candidate ``list[dict]`` shape ``analyse_paragraph``
    consumes. This is the network seam — real callers use it (the live
    ``POST …/analyse`` path); tests inject ``finder_fn`` so no network or
    credentials are needed.

    The branch finder answers a different question than the pairwise finder — it
    reports *which sources bear on a paragraph* (``{source_document_id,
    clause_number, confidence_score}``), NOT a five-label finding — so it opts
    out of the taxonomy check with ``require_taxonomy=False``.
    """
    context = _format_source_context(clause_index, candidate_source_ids)
    user = (
        f"Paragraph {paragraph_number}:\n{paragraph_text}\n\n"
        f"Branch: {branch}\n\n"
        f"Candidate sources:\n{context}"
    )
    return _call_candidates_with_retry(
        BRANCH_FINDER_SYSTEM_PROMPT, user, require_taxonomy=False
    )
