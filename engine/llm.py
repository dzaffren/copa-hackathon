"""Shared Azure AI Foundry chat client seam + defensive JSON response parsing.

New module: engine/llm.py (see docs/specs/rulebook-radar/
spec-llm-parser-connection-finder.md, "New module: engine/llm.py"). This is
the single place Tasks B/C/D import to talk to Azure AI Foundry and to turn a
model's raw text reply into parsed JSON.

- `call_chat` is the network seam — a thin function that constructs the Azure
  `ChatCompletionsClient`, sends a system+user message pair, and returns the
  reply text. It mirrors `engine.clauses.find_clause_anchors`: credentials come
  from `engine.config`, and it is never called by tests (no live credentials in
  CI).
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


def call_chat(deployment: str, system: str, user: str) -> str:
    """Call an Azure AI Foundry chat deployment and return the reply text.

    Constructs a `ChatCompletionsClient` from the endpoint/key in
    `engine.config`, sends `[SystemMessage(system), UserMessage(user)]` to the
    named `deployment`, and returns `response.choices[0].message.content`.

    This is the network seam — real callers (Tasks B/C/D) use it; tests never
    call it for real (no credentials in CI). Raises a clear `RuntimeError` when
    the endpoint or key is unset, mirroring
    `engine.clauses.find_clause_anchors`.
    """
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    if not AZURE_FOUNDRY_ENDPOINT or not AZURE_FOUNDRY_API_KEY:
        raise RuntimeError(
            "AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_API_KEY must be set "
            "in the environment to call call_chat"
        )

    client = ChatCompletionsClient(
        endpoint=AZURE_FOUNDRY_ENDPOINT,
        credential=AzureKeyCredential(AZURE_FOUNDRY_API_KEY),
    )
    response = client.complete(
        model=deployment,
        messages=[SystemMessage(system), UserMessage(user)],
    )
    return response.choices[0].message.content


def parse_json_response(raw: str) -> list | dict:
    """Parse an LLM's raw text reply into a JSON list or dict, defensively.

    Strips leading/trailing whitespace and a single markdown code fence if
    present (```json … ``` or ``` … ```), then `json.loads` the remainder.
    Raises `LLMResponseError` (with a truncated snippet of `raw`) if `raw` is
    empty/whitespace-only or the remainder is not valid JSON. Never returns a
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
        snippet = stripped[:200]
        raise LLMResponseError(
            f"LLM output was not valid JSON: {exc}. Raw (truncated): {snippet!r}"
        ) from exc
