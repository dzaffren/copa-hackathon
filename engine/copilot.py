"""Live Drafting Copilot chat (Azure AI Foundry Claude) + citation guardrail.

Supersedes `engine/copilot_scripts.py`'s canned-script approach (ADR 0004,
"curated demo-safe fixtures for MVP1", since reversed): the Copilot now makes
a real `engine.llm.call_chat` call, using the same two-layer guardrail
`engine.connections` established for the finder/critic loop.

- **Prompt layer**: the system prompt supplies only verbatim, already-resolved
  clause text as "the ONLY clauses you may cite" and instructs the model to
  say "No matching clause found" rather than invent one.
- **Code layer** (the real guardrail): `_validate_reply` drops any citation
  whose `clause_number` was not actually supplied in that grounding context,
  and always re-quotes citation text from the grounded set, never from the
  model's echo. A prompt-only guardrail is not trusted here any more than it
  is in `engine.connections`.

Output contract: the model writes clean Markdown prose first, then (only when
it has citations or a draft snippet to return) a line containing the
`<<<META>>>` sentinel followed by a JSON object `{"citations": [...],
"snippet_html": "..."}`. Streaming forwards only the prose before the sentinel
as tokens, so the drafter sees formatted prose stream in rather than raw JSON;
the structured metadata is parsed after the stream exhausts. `_split_reply`
handles the split for both the streaming and non-streaming paths.

Grounding context is assembled from citable clauses (the task node's own
document clauses when its `document_id` is in the built clause index, plus any
`@`-referenced accepted findings' clauses) and, as non-citable context only,
the drafter's current working draft and highlighted selection so the Copilot
can answer questions like "what are your suggestions on this part".
"""

import json
from pathlib import Path
from typing import Any, Callable, Generator, Optional

from engine import findings
from engine.clauses import ClauseIndex
from engine.config import COPILOT_DEPLOYMENT
from engine.llm import LLMResponseError, call_chat, call_chat_stream, parse_json_response

# The phrase the Copilot must say instead of inventing a citation, the
# CLAUDE.md verbatim-citation hard rule, verbatim.
NO_MATCHING_CLAUSE: str = "No matching clause found"

# Sentinel separating the model's Markdown prose from its trailing JSON
# metadata block. Chosen so it is vanishingly unlikely to appear in normal
# policy prose, and so a partial sentinel split across streaming chunks can be
# held back safely (see `copilot_reply_stream`).
META_SENTINEL: str = "<<<META>>>"


# The turn function is an injectable seam, mirroring `engine.connections`'s
# `finder_fn`/`critic_fn`: real callers use `_copilot_turn` (network); tests
# inject a stub, so no credentials are needed in CI.
CopilotTurnFn = Callable[[str, list[dict[str, str]]], str]
CopilotStreamFn = Callable[[str, list[dict[str, str]]], Generator[str, None, None]]


def _copilot_turn(system: str, messages: list[dict[str, str]]) -> str:
    """Call the live Copilot LLM (Azure AI Foundry) with a full turn history.

    `user` is passed as an empty placeholder; `call_chat` ignores it when
    `messages` is given (see `engine.llm.call_chat`'s docstring)."""
    return call_chat(COPILOT_DEPLOYMENT, system, "", messages=messages)


def _copilot_stream_turn(system: str, messages: list[dict[str, str]]) -> Generator[str, None, None]:
    """Real streaming seam: calls call_chat_stream against Azure AI Foundry."""
    yield from call_chat_stream(COPILOT_DEPLOYMENT, system, messages)


def _build_messages(
    history: list[dict[str, str]], message: str
) -> list[dict[str, str]]:
    """Build a strictly user/assistant-alternating Messages-API turn list.

    The client sends its own conversation state as `history`, including any
    prior turn that never got a reply (e.g. a call that errored, or an id the
    client retried after a network hiccup). Appending the new `message` after
    an unanswered "user" turn would leave two consecutive "user" turns, which
    the Messages API rejects outright ("roles must alternate"), surfacing as a
    502 on every subsequent call, not just the one that failed. Consecutive
    same-role turns are merged (concatenated) rather than dropped, so no
    drafter input is silently lost.
    """
    turns: list[dict[str, str]] = []
    for turn_msg in history:
        role = "assistant" if turn_msg.get("role") == "copilot" else "user"
        text = turn_msg.get("text", "")
        if not text:
            continue
        if turns and turns[-1]["role"] == role:
            turns[-1]["content"] = f"{turns[-1]['content']}\n\n{text}"
        else:
            turns.append({"role": role, "content": text})
    if turns and turns[-1]["role"] == "user":
        turns[-1]["content"] = f"{turns[-1]['content']}\n\n{message}"
    else:
        turns.append({"role": "user", "content": message})
    return turns


def _build_grounding_context(
    node: dict[str, Any],
    clause_index: ClauseIndex,
    workstreams_dir: Path,
    workstream_id: str,
    referenced_finding_ids: list[str],
    draft_text: Optional[str] = None,
    selection_text: Optional[str] = None,
) -> tuple[str, dict[str, str]]:
    """Assemble the model's context, plus the citable-clause lookup the
    post-hoc validator uses.

    Returns `(context_text, grounded_clauses)`. `grounded_clauses` maps
    `clause_number -> verbatim text` for every CITABLE clause (task-document
    clauses + referenced-finding clauses); it is the ONLY set a citation may
    resolve against. The drafter's current draft and highlighted selection, when
    provided, are appended to `context_text` as clearly-labelled NON-citable
    context so the Copilot understands what the drafter is working on, but they
    never enter `grounded_clauses` and so can never be quoted as a citation.

    A `referenced_finding_ids` entry that doesn't resolve (malformed id, an edge
    with no findings file, or an id absent from that edge's findings) is silently
    skipped: a missing reference just means fewer usable citations, never a
    fabricated one.
    """
    clause_blocks: list[str] = []
    grounded: dict[str, str] = {}

    document_id = node.get("document_id")
    if document_id:
        entries = clause_index.entries_for_document(document_id)
        if entries:
            lines = [f"Task document ({document_id}) clauses:"]
            for entry in entries:
                lines.append(f"{entry['clause_number']}: {entry['text']}")
                grounded[entry["clause_number"]] = entry["text"]
            clause_blocks.append("\n".join(lines))

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
        clause_blocks.append("\n".join(lines))

    citable = (
        "\n\n".join(clause_blocks)
        if clause_blocks
        else "(no clauses available for this task)"
    )
    sections = ["=== CITABLE CLAUSES ===\n" + citable]

    if draft_text and draft_text.strip():
        sections.append(
            "=== THE DRAFTER'S CURRENT WORKING DRAFT (their own work in "
            "progress, context only, never citable) ===\n" + draft_text.strip()
        )
    if selection_text and selection_text.strip():
        sections.append(
            "=== THE PASSAGE THE DRAFTER HAS HIGHLIGHTED AND IS ASKING ABOUT "
            "(their own text, context only, never citable) ===\n"
            + selection_text.strip()
        )

    return "\n\n".join(sections), grounded


def _system_prompt(
    task_title: str,
    intent: str,
    context: str,
    playbook_section: str = "",
) -> str:
    """The citation-grounding system prompt: mirrors `engine.connections`'s
    "prompt says don't invent" layer, backed by `_validate_reply`'s
    deterministic enforcement, never trusted alone. Also sets the writing
    register (formal, no em dashes, Markdown) and the prose + `<<<META>>>` JSON
    output contract."""
    sentinel = META_SENTINEL
    return (
        f"You are the Drafting Copilot for a Bank Negara Malaysia (BNM) policy "
        f'drafter working on "{task_title}". You help them draft prose, answer '
        f"questions about their document, and suggest concrete clause text. You "
        f"must never invent a clause citation.\n\n"
        f"CONTEXT you have been given:\n{context}\n\n"
        "GROUNDING AND CITATION RULES (strict, non-negotiable):\n"
        "1. The section labelled CITABLE CLAUSES contains the ONLY text you may "
        "quote as a citation. Every factual claim about what a regulation or a "
        "linked finding says must be backed by a clause_number that appears "
        "verbatim in that section.\n"
        f'2. If no citable clause supports a claim you would otherwise make, say '
        f'"{NO_MATCHING_CLAUSE}" rather than citing anything. Never invent, '
        "guess, or paraphrase a clause number, and never cite a clause that is "
        "not in the CITABLE CLAUSES section.\n"
        "3. The drafter's CURRENT WORKING DRAFT and any HIGHLIGHTED PASSAGE are "
        "the drafter's own work in progress. Use them to understand what the "
        "drafter is asking about and to tailor your suggestions, but never "
        "treat them as a citable source and never quote them as a clause "
        "citation. When the drafter refers to 'this part', 'this section', or "
        "'what I am drafting', they mean the highlighted passage if one is "
        "given, otherwise their current working draft.\n\n"
        "WRITING STYLE:\n"
        "- Write in plain, direct professional English the drafter understands "
        "on the first read. Be concise and precise. Prefer short sentences and "
        "everyday words; avoid dense, stacked-clause phrasing that obscures the "
        "point. Proposed clause text you suggest for the document may keep a "
        "formal policy register, but your explanation to the drafter must stay "
        "plain.\n"
        "- Do NOT use em dashes. Use commas, colons, semicolons, or separate "
        "sentences instead.\n"
        "- Use Markdown for structure and emphasis: bold for key terms, bullet "
        "lists for enumerations, and short headings where they aid clarity.\n\n"
        f"DELIVERABLE KIND: this task is a '{intent}'. Treat this as "
        "light framing for tone and format only (for example 'DP' favours "
        "discussion-paper question framing, 'PD' favours policy-document "
        "prose). It never licenses inventing content.\n\n"
        "OUTPUT FORMAT (important):\n"
        "First, write your reply to the drafter as clean Markdown prose. Do not "
        "wrap it in JSON and do not print any code fence around it.\n"
        "When, and only when, you are proposing concrete clause or paragraph "
        "text the drafter could add to their document, also provide it as an "
        "HTML draft snippet so they can insert it directly. Use only these HTML "
        "tags in the snippet: h2, h3, p, strong, em, ul, ol, li, br.\n"
        "After your prose, if and only if you have citations or a draft snippet "
        "to return, output a line containing exactly " + sentinel + " and then "
        "a single JSON object on the following lines, for example:\n"
        + sentinel + "\n"
        '{"citations": [{"clause_number": "OpRes PD 5.3", "text": "..."}], '
        '"snippet_html": "<h2>6.3 Accountability</h2><p>...</p>"}\n'
        "Include only the keys you actually have. Omit citations if you cited "
        "nothing. Omit snippet_html if you are not proposing draft text. If you "
        "have neither, do not output the " + sentinel + " line at all. Never "
        "put anything after the JSON object."
        # The drafter's own standing instruction for THIS stage, appended LAST and
        # deliberately AFTER the grounding and citation rules above. A playbook
        # instruction shapes how the Copilot writes; it cannot loosen what it may
        # cite, because that guarantee is enforced by `_validate_reply` in code
        # rather than by this prompt. An empty section adds nothing at all, so a
        # workstream with no playbook produces a byte-identical prompt to the one
        # it produced before playbooks existed.
        + (
            "\n\nTHE DRAFTER'S PLAYBOOK FOR THIS STAGE — her own standing "
            "instructions, in her words. Follow them unless they would conflict "
            "with the grounding and citation rules above, which always win:\n"
            + playbook_section.strip()
            if playbook_section.strip()
            else ""
        )
    )


def _split_reply(raw: str) -> tuple[str, dict[str, Any]]:
    """Split a raw model reply into `(prose, meta)`.

    Everything before the first `<<<META>>>` sentinel is the Markdown prose
    shown to the drafter; the JSON object after it carries the structured
    metadata (`citations`, `snippet_html`). Defensive by design: no sentinel, a
    non-JSON tail, or a non-object tail all degrade to `(whole_reply, {})`, so
    the drafter always gets the answer even when the model ignores the format
    (it just loses the citations/snippet block). Reused by the streaming and
    non-streaming paths so the two never drift.
    """
    idx = raw.find(META_SENTINEL)
    if idx == -1:
        return raw.strip(), {}
    prose = raw[:idx].strip()
    tail = raw[idx + len(META_SENTINEL):].strip()
    if not tail:
        return prose, {}
    try:
        meta = parse_json_response(tail)
    except LLMResponseError:
        return prose, {}
    if not isinstance(meta, dict):
        return prose, {}
    return prose, meta


def _validate_reply(
    prose: str, meta: dict[str, Any], grounded: dict[str, str]
) -> dict[str, Any]:
    """The deterministic guardrail: keep only citations whose `clause_number`
    is in the grounded (citable) set, and always re-quote their text from that
    set, never from the model's echo. Returns the reply shape the API/frontend
    consume: `{"role": "copilot", "text": ..., "citations"?: [...],
    "snippet_html"?: ...}`."""
    text = prose or NO_MATCHING_CLAUSE
    citations_out = []
    for citation in meta.get("citations") or []:
        number = citation.get("clause_number") if isinstance(citation, dict) else None
        if number in grounded:
            citations_out.append({"clause_number": number, "text": grounded[number]})

    result: dict[str, Any] = {"role": "copilot", "text": text}
    if citations_out:
        result["citations"] = citations_out
    snippet_html = meta.get("snippet_html")
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
    draft_text: Optional[str] = None,
    selection_text: Optional[str] = None,
    turn_fn: Optional[CopilotTurnFn] = None,
    playbook_section: str = "",
) -> dict[str, Any]:
    """Ground, call, split, and validate one live Copilot turn (non-streaming).

    Args:
        node: the task node dict (from the workstream graph); its `title` frames
            the system prompt and its `document_id` (if any) supplies grounding
            clause text.
        intent: one of `engine.workstreams.TASK_TYPES`'s codes, a light
            system-prompt framing hint.
        history: prior turns as `[{"role": "user" | "copilot", "text": ...}]`;
            the server holds no conversation state, so the full history travels
            on every call (the client is the source of truth).
        message: the drafter's new message.
        referenced_finding_ids: `@`-mentioned accepted-finding ids
            (`{edge_id}~{index}`), resolved to verbatim clause text for
            grounding; an id that doesn't resolve is silently skipped.
        clause_index: the built clause index, for the task document's clauses.
        workstreams_dir, workstream_id: where to resolve
            `referenced_finding_ids` against `engine.findings`.
        draft_text: the drafter's current working draft as plain text
            (non-citable context, so the Copilot can see what they are drafting).
        selection_text: the passage the drafter has highlighted (non-citable
            focused context for "suggestions on this part").
        turn_fn: injectable seam for the network call; defaults to
            `_copilot_turn`. Tests inject a stub.

    Returns:
        `{"role": "copilot", "text": ..., "citations"?: [...],
        "snippet_html"?: ...}`, every citation guaranteed grounded.

    Raises:
        RuntimeError: Foundry credentials are unset (propagates from
            `call_chat`).
    """
    turn = turn_fn if turn_fn is not None else _copilot_turn

    context, grounded = _build_grounding_context(
        node, clause_index, workstreams_dir, workstream_id,
        referenced_finding_ids, draft_text, selection_text,
    )
    system = _system_prompt(
        node.get("title") or "this task", intent, context, playbook_section
    )
    messages = _build_messages(history, message)

    raw = turn(system, messages)
    prose, meta = _split_reply(raw)
    return _validate_reply(prose, meta, grounded)


def copilot_reply_stream(
    *,
    node: dict[str, Any],
    intent: str,
    history: list[dict[str, str]],
    message: str,
    referenced_finding_ids: list[str],
    clause_index: ClauseIndex,
    workstreams_dir: Path,
    workstream_id: str,
    draft_text: Optional[str] = None,
    selection_text: Optional[str] = None,
    stream_fn: Optional[CopilotStreamFn] = None,
    playbook_section: str = "",
) -> Generator[str, None, None]:
    """Stream a Copilot turn as SSE frames.

    Emits `event: token` frames for the Markdown prose as it arrives, stopping
    at the `<<<META>>>` sentinel so the metadata JSON is never streamed as
    tokens (the drafter sees clean prose stream in, not raw JSON). After the
    stream exhausts, parses the metadata and emits one `event: done` frame with
    the validated citations and snippet. On any exception mid-stream, emits an
    `event: error` frame and stops, never a bare 502 from a partial stream.

    Wire format (each yielded string is a complete SSE frame):
        event: token\\ndata: {"t": "chunk"}\\n\\n
        event: done\\ndata: {"text": "...", "citations": [...], "snippet_html": "..."}\\n\\n
        event: error\\ndata: {"code": "COPILOT_FAILED", "message": "..."}\\n\\n

    `stream_fn` is an injectable seam; tests pass a stub generator so no live
    credentials are needed in CI. Defaults to `_copilot_stream_turn`.
    """
    streamer = stream_fn if stream_fn is not None else _copilot_stream_turn

    context, grounded = _build_grounding_context(
        node, clause_index, workstreams_dir, workstream_id,
        referenced_finding_ids, draft_text, selection_text,
    )
    system = _system_prompt(
        node.get("title") or "this task", intent, context, playbook_section
    )
    messages_list = _build_messages(history, message)

    accumulated = ""
    emitted = 0  # chars of prose already sent as token frames
    sentinel_seen = False
    holdback = len(META_SENTINEL) - 1
    try:
        for chunk in streamer(system, messages_list):
            accumulated += chunk
            if sentinel_seen:
                continue  # everything past the sentinel is metadata
            idx = accumulated.find(META_SENTINEL)
            if idx != -1:
                to_emit = accumulated[emitted:idx]
                sentinel_seen = True
            else:
                # Hold back the trailing `holdback` chars in case they are the
                # start of a sentinel that will complete on a later chunk.
                safe_end = max(emitted, len(accumulated) - holdback)
                to_emit = accumulated[emitted:safe_end]
            if to_emit:
                emitted += len(to_emit)
                yield f"event: token\ndata: {json.dumps({'t': to_emit})}\n\n"
    except Exception as exc:  # live model / creds / network failure mid-stream
        yield f"event: error\ndata: {json.dumps({'code': 'COPILOT_FAILED', 'message': str(exc)})}\n\n"
        return

    # No sentinel ever appeared: flush the held-back tail so no prose is lost.
    if not sentinel_seen and emitted < len(accumulated):
        tail = accumulated[emitted:]
        yield f"event: token\ndata: {json.dumps({'t': tail})}\n\n"

    prose, meta = _split_reply(accumulated)
    validated = _validate_reply(prose, meta, grounded)
    done_payload: dict[str, Any] = {"text": validated["text"]}
    if validated.get("citations"):
        done_payload["citations"] = validated["citations"]
    if validated.get("snippet_html"):
        done_payload["snippet_html"] = validated["snippet_html"]
    yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
