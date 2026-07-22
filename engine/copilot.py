"""Live Drafting Copilot chat (Azure AI Foundry Claude) + citation guardrail.

Supersedes `engine/copilot_scripts.py`'s canned-script approach (ADR 0004,
"curated demo-safe fixtures for MVP1" — since reversed): the Copilot now makes
a real `engine.llm.call_chat` call, using the same two-layer guardrail
`engine.connections` already established for the finder→critic loop —

- **Prompt layer**: the system prompt supplies only verbatim, already-resolved
  clause text as "the ONLY clauses you may cite" and instructs the model to
  say "No matching clause found" rather than invent one.
- **Code layer** (the real guardrail): `_validate_reply` drops any citation
  whose `clause_number` was not actually supplied in that grounding context,
  and always re-quotes citation text from the grounded set — never from the
  model's echo. A prompt-only guardrail is not trusted here any more than it
  is in `engine.connections`.

Grounding context is assembled from two sources, both already verbatim:
the task node's own document's clauses (when its `document_id` is in the
built clause index — most workstream documents are not, per
`engine/api.py`'s note that the index today covers only the RMiT documents),
and any `@`-referenced accepted findings' `source_clauses`/`target_clauses`
(already-verbatim citations stored on the finding record itself, per
`engine.findings`).
"""

from pathlib import Path
from typing import Any, Callable, Optional

from engine import findings
from engine.clauses import ClauseIndex
from engine.config import COPILOT_DEPLOYMENT
from engine.llm import call_chat, parse_json_response

# The seven intent presets — moved from `copilot_scripts.py`, which this
# module replaces. Cosmetic beyond a light system-prompt framing hint; the
# dropdown itself is a frontend/product concept, not a script key any more.
INTENTS: tuple[str, ...] = (
    "PD",
    "DP",
    "ED",
    "FAQ",
    "Engagement Deck",
    "Feedback Template for Industry",
    "Peer Benchmarking",
)

# The phrase the Copilot must say instead of inventing a citation — the
# CLAUDE.md verbatim-citation hard rule, verbatim.
NO_MATCHING_CLAUSE: str = "No matching clause found"


class CopilotError(Exception):
    """Raised when the live Copilot call cannot proceed or fails (bad
    credentials, network, or a malformed model reply) — the API route turns
    this into a 502, never a silent scripted fallback."""


# The turn function is an injectable seam, mirroring `engine.connections`'s
# `finder_fn`/`critic_fn` — real callers use `_copilot_turn` (network); tests
# inject a stub, so no credentials are needed in CI.
CopilotTurnFn = Callable[[str, list[dict[str, str]]], str]


def _copilot_turn(system: str, messages: list[dict[str, str]]) -> str:
    """Call the live Copilot LLM (Azure AI Foundry) with a full turn history.

    `user` is passed as an empty placeholder — `call_chat` ignores it when
    `messages` is given (see `engine.llm.call_chat`'s docstring)."""
    return call_chat(COPILOT_DEPLOYMENT, system, "", messages=messages)


def _build_grounding_context(
    node: dict[str, Any],
    clause_index: ClauseIndex,
    workstreams_dir: Path,
    workstream_id: str,
    referenced_finding_ids: list[str],
) -> tuple[str, dict[str, str]]:
    """Assemble the ONLY clause text the model may cite, plus the same set as
    a lookup for the post-hoc validator.

    Returns `(context_text, grounded_clauses)` — `grounded_clauses` maps
    `clause_number -> verbatim text` for every clause included in
    `context_text`. Both sources here are already-verbatim (fetched by
    `ClauseIndex` or copied from a finding's own stored citation) — nothing is
    model-produced.

    A `referenced_finding_ids` entry that doesn't resolve (malformed id, an
    edge with no findings file, or an id absent from that edge's findings) is
    silently skipped, never surfaced as an error — a missing reference just
    means fewer usable citations, never a fabricated one.
    """
    blocks: list[str] = []
    grounded: dict[str, str] = {}

    document_id = node.get("document_id")
    if document_id:
        entries = clause_index.entries_for_document(document_id)
        if entries:
            lines = [f"Task document ({document_id}) clauses:"]
            for entry in entries:
                lines.append(f"{entry['clause_number']}: {entry['text']}")
                grounded[entry["clause_number"]] = entry["text"]
            blocks.append("\n".join(lines))

    for ref_id in referenced_finding_ids:
        if "~" not in ref_id:
            continue
        edge_id = ref_id.rsplit("~", 1)[0]
        try:
            edge_findings = findings.load(workstreams_dir, workstream_id, edge_id)
        except findings.FindingsNotAnalysedError:
            continue
        finding = next((f for f in edge_findings if f["id"] == ref_id), None)
        if finding is None:
            continue
        lines = [
            f"Accepted finding {ref_id} ({finding.get('label')}): "
            f"{finding.get('summary')}"
        ]
        clauses = (finding.get("source_clauses") or []) + (
            finding.get("target_clauses") or []
        )
        for clause in clauses:
            number = clause.get("clause_number")
            text = clause.get("text")
            if not number or not text:
                continue
            lines.append(f"{number}: {text}")
            grounded[number] = text
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks), grounded


def _system_prompt(task_title: str, intent: str, context: str) -> str:
    """The citation-grounding system prompt — mirrors `engine.connections`'s
    "prompt says don't invent" layer, backed by `_validate_reply`'s
    deterministic enforcement, never trusted alone."""
    return (
        f'You are the Drafting Copilot for a Bank Negara Malaysia policy '
        f'drafter working on "{task_title}". You help draft prose, answer '
        f"questions, and suggest redrafts — but you must NEVER invent a "
        f"clause citation.\n\n"
        f"You are given, below, the ONLY clauses you may cite:\n"
        f"<CONTEXT>\n{context or '(no clauses available for this task)'}\n"
        f"</CONTEXT>\n\n"
        "CITATION RULE (strict, non-negotiable):\n"
        "- Every factual claim about what a regulation or a linked finding "
        "says MUST be backed by a clause_number that appears verbatim in "
        "<CONTEXT> above.\n"
        f'- If no clause in <CONTEXT> supports a claim you would otherwise '
        f'make, you MUST say "{NO_MATCHING_CLAUSE}" instead of citing '
        "anything — never invent, paraphrase into a citation, guess a "
        "clause number, or cite a clause not shown above.\n"
        "- When you do cite, quote the clause TEXT exactly as given in "
        "<CONTEXT>, with its exact clause_number.\n\n"
        "Return your answer as a JSON object:\n"
        '{"text": <your prose reply>, '
        '"citations": [{"clause_number": ..., "text": ...}, ...] '
        "(omit or empty if none), "
        '"snippet_html": <optional HTML draft snippet, omit if not asked '
        "for one>}\n\n"
        f"The drafter's chosen intent preset is: {intent} — treat this as "
        'light framing for tone/format only (e.g. "DP" = discussion-paper '
        'question framing, "PD" = policy-document prose), never as license '
        "to invent content.\n\n"
        "Return ONLY the JSON object — no prose outside it."
    )


def _validate_reply(raw_reply: dict[str, Any], grounded: dict[str, str]) -> dict[str, Any]:
    """The deterministic guardrail: drop any citation not actually grounded,
    and always re-quote citation text from the grounded set — never trust the
    model's echo of a citation it was given."""
    text = raw_reply.get("text") or NO_MATCHING_CLAUSE
    citations_out = []
    for citation in raw_reply.get("citations") or []:
        number = citation.get("clause_number")
        if number not in grounded:
            continue
        citations_out.append({"clause_number": number, "text": grounded[number]})

    result: dict[str, Any] = {"role": "copilot", "text": text}
    if citations_out:
        result["citations"] = citations_out
    snippet_html = raw_reply.get("snippet_html")
    if snippet_html:
        result["snippet_html"] = snippet_html
    return result


def copilot_reply(
    *,
    node: dict[str, Any],
    intent: str,
    history: list[dict[str, str]],
    message: str,
    referenced_finding_ids: list[str],
    clause_index: ClauseIndex,
    workstreams_dir: Path,
    workstream_id: str,
    turn_fn: Optional[CopilotTurnFn] = None,
) -> dict[str, Any]:
    """Ground, call, and validate one live Copilot turn.

    Args:
        node: the task node dict (from the workstream graph) — its `title`
            frames the system prompt and its `document_id` (if any) supplies
            grounding clause text.
        intent: one of `INTENTS` — a light system-prompt framing hint.
        history: prior turns as `[{"role": "user" | "copilot", "text": ...}]`
            — the server holds no conversation state, so the full history
            travels on every call (the client is the source of truth).
        message: the drafter's new message.
        referenced_finding_ids: `@`-mentioned accepted-finding ids
            (`{edge_id}~{index}`) — resolved to verbatim clause text for
            grounding; an id that doesn't resolve is silently skipped.
        clause_index: the built clause index, for the task document's own
            clauses.
        workstreams_dir, workstream_id: where to resolve
            `referenced_finding_ids` against `engine.findings`.
        turn_fn: injectable seam for the network call; defaults to
            `_copilot_turn` (real Azure AI Foundry call). Tests inject a stub.

    Returns:
        `{"role": "copilot", "text": ..., "citations"?: [...],
        "snippet_html"?: ...}` — every citation guaranteed grounded.

    Raises:
        CopilotError: the model's reply did not parse as a JSON object.
        engine.llm.LLMResponseError: the model's reply was not valid JSON at
            all (propagates from `parse_json_response`).
        RuntimeError: Foundry credentials are unset (propagates from
            `call_chat`).
    """
    turn = turn_fn if turn_fn is not None else _copilot_turn

    context, grounded = _build_grounding_context(
        node, clause_index, workstreams_dir, workstream_id, referenced_finding_ids
    )
    system = _system_prompt(node.get("title") or "this task", intent, context)

    messages: list[dict[str, str]] = []
    for turn_msg in history:
        role = "assistant" if turn_msg.get("role") == "copilot" else "user"
        text = turn_msg.get("text", "")
        if text:
            messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": message})

    raw = turn(system, messages)
    parsed = parse_json_response(raw)
    if not isinstance(parsed, dict):
        raise CopilotError(
            f"Expected a JSON object reply; got {type(parsed).__name__}"
        )
    return _validate_reply(parsed, grounded)
