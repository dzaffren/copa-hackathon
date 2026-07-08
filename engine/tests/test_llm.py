"""Tests for engine.llm — shared Azure client seam + defensive JSON parsing.

Covers spec section "New module: engine/llm.py" (docs/specs/rulebook-radar/
spec-llm-parser-connection-finder.md). Only the pure `parse_json_response`
logic and the credential-guard of `call_chat` are exercised — `call_chat`'s
network path is a seam that is never called for real here (no credentials in
CI).
"""

import pytest

from engine.llm import LLMResponseError, parse_json_response


def test_parses_bare_json_array() -> None:
    assert parse_json_response("[1, 2, 3]") == [1, 2, 3]


def test_parses_bare_json_object() -> None:
    assert parse_json_response('{"a": 1, "b": 2}') == {"a": 1, "b": 2}


def test_strips_json_fenced_block() -> None:
    raw = '```json\n[{"clause": "RMiT 17.1"}]\n```'
    assert parse_json_response(raw) == [{"clause": "RMiT 17.1"}]


def test_strips_plain_fenced_block() -> None:
    raw = '```\n{"ok": true}\n```'
    assert parse_json_response(raw) == {"ok": True}


def test_handles_surrounding_whitespace() -> None:
    assert parse_json_response("   \n  [1]  \n ") == [1]


def test_empty_string_raises() -> None:
    with pytest.raises(LLMResponseError):
        parse_json_response("")


def test_whitespace_only_raises() -> None:
    with pytest.raises(LLMResponseError):
        parse_json_response("   \n\t ")


def test_malformed_json_raises() -> None:
    with pytest.raises(LLMResponseError):
        parse_json_response("{not json")


def test_parses_json_lines_into_list() -> None:
    """Claude sometimes returns one JSON object per line instead of an array;
    parse_json_response collects those into a list."""
    raw = (
        '{"clause_number": "11.1", "parent": null}\n'
        '{"clause_number": "11.2", "parent": null}'
    )
    assert parse_json_response(raw) == [
        {"clause_number": "11.1", "parent": None},
        {"clause_number": "11.2", "parent": None},
    ]


def test_parses_fenced_json_lines_into_list() -> None:
    raw = '```json\n{"a": 1}\n{"a": 2}\n```'
    assert parse_json_response(raw) == [{"a": 1}, {"a": 2}]


def test_json_lines_with_one_bad_line_raises() -> None:
    """JSONL is all-or-nothing — a single unparseable line fails the whole
    response rather than returning a partial parse."""
    raw = '{"a": 1}\n{not json}'
    with pytest.raises(LLMResponseError):
        parse_json_response(raw)


def test_call_chat_without_credentials_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """No network: with creds unset, call_chat raises a clear RuntimeError."""
    import engine.llm as llm

    monkeypatch.setattr(llm, "AZURE_FOUNDRY_ENDPOINT", None)
    monkeypatch.setattr(llm, "AZURE_FOUNDRY_API_KEY", None)
    with pytest.raises(RuntimeError, match="AZURE_FOUNDRY"):
        llm.call_chat("some-deployment", "system prompt", "user prompt")
