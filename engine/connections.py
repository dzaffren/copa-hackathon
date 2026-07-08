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
deterministic fallback if the live API hiccups mid-pitch. Do NOT classify
connections as Conflict/Duplication/Gap — that is the ripple story (#8). This
engine emits raw clause-anchored connections only.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, TypedDict

from engine.clauses import ClauseIndex
from engine.config import FINDER_CRITIC_DEPLOYMENT
from engine.llm import LLMResponseError, call_chat, parse_json_response


class ClauseCitation(TypedDict):
    """A clause reference on a supported connection, with verbatim text
    fetched from the ``ClauseIndex`` by number — never model-produced."""

    clause_number: str
    text: str


class Connection(TypedDict):
    """A supported clause-anchored connection (matches the spec's
    ``POST /connections/find`` 200 ``connections[]`` shape)."""

    summary: str
    source_clauses: list[ClauseCitation]
    target_clauses: list[ClauseCitation]
    scope_note: Optional[str]
    supported: bool


class UnsupportedConnection(TypedDict):
    """A candidate that cited at least one clause absent from the index —
    reported honestly, never invented, never promoted to a connection."""

    summary: str
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
    """
    connections: list[Connection] = []
    unsupported: list[UnsupportedConnection] = []
    validation: list[dict] = []

    for candidate in candidates:
        summary = candidate.get("summary", "")
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
                "cited_clauses": cited_results,
                "supported": all_resolved,
            }
        )

        if all_resolved:
            connections.append(
                {
                    "summary": summary,
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
                    "message": _MESSAGE_NO_CLAUSE,
                    "supported": False,
                }
            )

    return connections, unsupported, validation


def _cite(
    clause_numbers: list[str], clause_index: ClauseIndex
) -> list[ClauseCitation]:
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
    trace_path.write_text(json.dumps(trace, indent=2))
    return trace_path


FINDER_SYSTEM_PROMPT = (
    "You are a policy analyst finding cross-policy CONNECTIONS between two "
    "Bank Negara Malaysia policy documents. You are given, for each document, "
    "its full list of clauses as `{clause_number}: {text}` lines, grouped "
    "under a document-id label.\n\n"
    "Find connections where a clause in one document relates to a clause in "
    "the other — e.g. a conflict, a dependency, a duplication, or a scoping "
    "relationship. For each connection, return an object:\n"
    '  {"summary": <one-sentence description>,\n'
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
    "1. REFUTE or SCOPE weak candidates — drop any that do not hold, and for "
    "those that do, add or refine a `scope_note` capturing any exemption, "
    "condition, or limit (e.g. an affiliate exemption clause).\n"
    "2. SURFACE MISSED connections the finder did not propose (recall).\n\n"
    "Return the scoped/refuted surviving candidates PLUS any newly-found "
    "connections, all in the SAME object shape:\n"
    '  {"summary": ..., "source_clauses": [...], "target_clauses": [...], '
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


def _parse_candidate_list(raw: str) -> list[dict]:
    """Parse an agent's raw reply into a candidate ``list[dict]``.

    Delegates to ``parse_json_response`` (strips fences, ``json.loads``) then
    enforces the raw candidate shape the citation validator consumes: a list of
    dict objects. Raises ``LLMResponseError`` (not a silent coercion) if the
    model returned a non-list or list items that are not objects.
    """
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list) or not all(
        isinstance(item, dict) for item in parsed
    ):
        snippet = raw.strip()[:200]
        raise LLMResponseError(
            f"Expected a JSON array of connection objects; got "
            f"{type(parsed).__name__}. Raw (truncated): {snippet!r}"
        )
    return parsed


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
    raw = call_chat(FINDER_CRITIC_DEPLOYMENT, FINDER_SYSTEM_PROMPT, context)
    return _parse_candidate_list(raw)


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
    raw = call_chat(FINDER_CRITIC_DEPLOYMENT, CRITIC_SYSTEM_PROMPT, user)
    return _parse_candidate_list(raw)
