"""Shared Azure AI Foundry chat client seam + defensive JSON response parsing.

New module: engine/llm.py (see docs/specs/rulebook-radar/
spec-llm-parser-connection-finder.md, "New module: engine/llm.py"). This is
the single place Tasks B/C/D import to talk to Azure AI Foundry and to turn a
model's raw text reply into parsed JSON.

- `call_chat` is the network seam — a thin function that constructs the
  `anthropic` SDK's `AnthropicFoundry` client (Claude on Foundry speaks the
  Anthropic Messages API, not the generic chat-completions API), sends a
  system + user prompt, and returns the reply text. Credentials come from
  `engine.config`, and it is never called by tests (no live credentials in CI).
- `parse_json_response` is pure, network-free, and fully unit-tested: it strips
  whitespace and any markdown code fence, then `json.loads` the remainder,
  raising `LLMResponseError` on empty/malformed output rather than corrupting
  downstream state silently.
"""

import json

from engine.config import (
    AZURE_FOUNDRY_API_KEY,
    AZURE_FOUNDRY_ENDPOINT,
)


class LLMResponseError(Exception):
    """The LLM returned malformed or empty output (unparseable as JSON)."""


def call_chat(
    deployment: str, system: str, user: str, max_tokens: int = 8192
) -> str:
    """Call a Claude deployment on Azure AI Foundry and return the reply text.

    Claude models on Foundry are served through the **Anthropic Messages API**,
    not the generic `azure-ai-inference` chat-completions API (which returns
    `api_not_supported` for these deployments). This uses the `anthropic` SDK's
    `AnthropicFoundry` client with API-key auth against a base URL ending in
    `/anthropic` (e.g. `https://<resource>.services.ai.azure.com/anthropic`),
    per the Microsoft Foundry Claude docs. `system` is passed as the top-level
    Messages-API `system` parameter (not a message with role "system").

    Constructs the client from the endpoint/key in `engine.config`, sends the
    system + user prompt to the named `deployment`, and returns the concatenated
    text of the response content blocks.

    This is the network seam — real callers (Tasks B/C/D) use it; tests never
    call it for real (no credentials in CI). Raises a clear `RuntimeError` when
    the endpoint or key is unset, mirroring
    `engine.clauses.find_clause_anchors`.
    """
    from anthropic import AnthropicFoundry

    if not AZURE_FOUNDRY_ENDPOINT or not AZURE_FOUNDRY_API_KEY:
        raise RuntimeError(
            "AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_API_KEY must be set "
            "in the environment to call call_chat"
        )

    client = AnthropicFoundry(
        api_key=AZURE_FOUNDRY_API_KEY,
        base_url=AZURE_FOUNDRY_ENDPOINT,
    )
    message = client.messages.create(
        model=deployment,
        system=system,
        messages=[{"role": "user", "content": user}],
        max_tokens=max_tokens,
    )
    # Messages API returns a list of content blocks; concatenate the text of
    # every text block (tool/thinking blocks, if any, carry no `.text`).
    return "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )


def parse_json_response(raw: str) -> list | dict:
    """Parse an LLM's raw text reply into a JSON list or dict, defensively.

    Strips leading/trailing whitespace and a single markdown code fence if
    present (```json … ``` or ``` … ```), then parses the remainder. Accepts
    either a single JSON value (array or object) **or** JSON Lines — one JSON
    object per line, which Claude sometimes emits instead of a JSON array; in
    that case the objects are collected into a list. Raises `LLMResponseError`
    (with a truncated snippet of `raw`) if `raw` is empty/whitespace-only or
    the remainder is not valid JSON either way. Never returns a
    partially-parsed or fabricated value.
    """
    stripped = raw.strip()
    if not stripped:
        raise LLMResponseError("LLM returned empty output; expected JSON")

    body = stripped
    if body.startswith("```"):
        # Drop the opening fence line (```json or ```) and the closing fence.
        lines = body.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        body = "\n".join(lines).strip()

    try:
        return json.loads(body)
    except (json.JSONDecodeError, ValueError) as exc:
        # Fall back to JSON Lines: one JSON object per line (a shape Claude
        # sometimes returns in place of a JSON array). Every non-empty line
        # must parse, else the whole response is treated as malformed — never
        # a partial parse.
        jsonl = _try_parse_jsonl(body)
        if jsonl is not None:
            return jsonl
        snippet = stripped[:200]
        raise LLMResponseError(
            f"LLM output was not valid JSON: {exc}. Raw (truncated): {snippet!r}"
        ) from exc


def _try_parse_jsonl(body: str) -> list | None:
    """Parse `body` as JSON Lines → a list of values, or `None` if it is not
    valid JSONL (so the caller can report the original error).

    Requires at least two non-empty lines that each parse as JSON — a single
    line is just a scalar/object already handled by the primary parse, so
    treating it as JSONL here would mask a genuine single-value parse error.
    """
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    if len(lines) < 2:
        return None
    parsed: list = []
    for line in lines:
        try:
            parsed.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            return None
    return parsed
