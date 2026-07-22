"""Tests for engine.copilot — live Copilot grounding + citation guardrail.

No network access: the turn function (`turn_fn`) is always an injected stub,
mirroring `test_connections.py`'s `finder_fn`/`critic_fn` stubbing. Covers the
two-layer guardrail (`_build_grounding_context` assembling only verbatim
text, `_validate_reply` dropping anything not actually grounded) plus the
`copilot_reply` orchestration.
"""

import json

from engine import findings
from engine.clauses import ClauseIndex
from engine.copilot import (
    INTENTS,
    NO_MATCHING_CLAUSE,
    CopilotError,
    _build_grounding_context,
    _validate_reply,
    copilot_reply,
)

_WORKSTREAM = "opres-v2"
_EDGE = "e-opres_v0_3--bcbs_opres_2021"


def _clause_index(entries: dict[str, dict]) -> ClauseIndex:
    """Build a ClauseIndex directly from hand-written entries — no markdown
    parsing needed for these tests, just a verbatim clause_number -> entry map."""
    primary = {
        number: {
            "clause_number": number,
            "policy_id": "OpRes",
            "document_id": entry["document_id"],
            "text": entry["text"],
            "heading": None,
            "source": "test",
            "parent": None,
            "children": [],
            "superseded_versions": [],
        }
        for number, entry in entries.items()
    }
    return ClauseIndex(primary)


def _write_finding(workstreams_dir, edge_id: str, finding: dict) -> None:
    (workstreams_dir / _WORKSTREAM / "findings").mkdir(parents=True, exist_ok=True)
    findings.save(workstreams_dir, _WORKSTREAM, edge_id, [finding])


# --- _build_grounding_context ------------------------------------------------


def test_grounding_context_includes_task_documents_own_clauses(tmp_path):
    clause_index = _clause_index(
        {"OpRes PD 5.3": {"document_id": "opres-pd-v0-3", "text": "Scenario testing annually."}}
    )
    node = {"id": "opres-pd-v0-3", "title": "OpRes PD", "document_id": "opres-pd-v0-3"}

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, []
    )

    assert "OpRes PD 5.3" in context
    assert "Scenario testing annually." in context
    assert grounded["OpRes PD 5.3"] == "Scenario testing annually."


def test_grounding_context_is_empty_when_node_has_no_document_id(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, []
    )

    assert context == ""
    assert grounded == {}


def test_grounding_context_includes_referenced_finding_clauses(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}
    _write_finding(
        tmp_path,
        _EDGE,
        {
            "summary": "Both cover incident reporting.",
            "label": "aligns-with",
            "sentiment": None,
            "source_clauses": [{"clause_number": "OpRes PD 4.4", "text": "Report within 24 hours."}],
            "target_clauses": [{"clause_number": "BCBS 12", "text": "Notify supervisors promptly."}],
        },
    )

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, [f"{_EDGE}~0"]
    )

    assert "OpRes PD 4.4" in context
    assert "Report within 24 hours." in context
    assert grounded["OpRes PD 4.4"] == "Report within 24 hours."
    assert grounded["BCBS 12"] == "Notify supervisors promptly."


def test_referenced_finding_id_with_no_tilde_is_skipped_not_errored(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, ["not-a-valid-id"]
    )

    assert context == ""
    assert grounded == {}


def test_referenced_finding_id_for_unanalysed_edge_is_skipped_not_errored(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, ["e-never-analysed~0"]
    )

    assert context == ""
    assert grounded == {}


def test_referenced_finding_id_not_present_on_the_edge_is_skipped(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}
    _write_finding(
        tmp_path,
        _EDGE,
        {
            "summary": "x",
            "label": "aligns-with",
            "sentiment": None,
            "source_clauses": [],
            "target_clauses": [],
        },
    )

    # Only index 0 exists on this edge — index 5 does not resolve.
    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, [f"{_EDGE}~5"]
    )

    assert context == ""
    assert grounded == {}


# --- _validate_reply ---------------------------------------------------------


def test_validator_drops_a_citation_whose_clause_number_is_not_grounded():
    grounded = {"OpRes PD 5.3": "Scenario testing annually."}
    raw = {
        "text": "Cites both a real and a fabricated clause.",
        "citations": [
            {"clause_number": "OpRes PD 5.3", "text": "Scenario testing annually."},
            {"clause_number": "Made Up 9.9", "text": "This clause does not exist."},
        ],
    }

    result = _validate_reply(raw, grounded)

    assert len(result["citations"]) == 1
    assert result["citations"][0]["clause_number"] == "OpRes PD 5.3"


def test_validator_always_re_quotes_from_grounded_text_never_the_models_echo():
    grounded = {"OpRes PD 5.3": "Scenario testing annually."}
    raw = {
        "text": "x",
        "citations": [
            {"clause_number": "OpRes PD 5.3", "text": "a paraphrased, WRONG echo"},
        ],
    }

    result = _validate_reply(raw, grounded)

    assert result["citations"][0]["text"] == "Scenario testing annually."


def test_validator_defaults_to_no_matching_clause_when_text_is_empty():
    result = _validate_reply({"text": ""}, {})
    assert result["text"] == NO_MATCHING_CLAUSE


def test_validator_omits_citations_key_when_none_survive():
    result = _validate_reply({"text": "no clause supports this"}, {})
    assert "citations" not in result


def test_validator_passes_through_snippet_html_when_present():
    result = _validate_reply({"text": "x", "snippet_html": "<p>draft</p>"}, {})
    assert result["snippet_html"] == "<p>draft</p>"


def test_validator_omits_snippet_html_when_absent():
    result = _validate_reply({"text": "x"}, {})
    assert "snippet_html" not in result


# --- copilot_reply (orchestration) ------------------------------------------


def test_copilot_reply_returns_the_validated_turn_fn_output(tmp_path):
    clause_index = _clause_index(
        {"OpRes PD 5.3": {"document_id": "opres-pd-v0-3", "text": "Scenario testing annually."}}
    )
    node = {"id": "opres-pd-v0-3", "title": "OpRes PD", "document_id": "opres-pd-v0-3"}

    def stub_turn(system, messages):
        assert "OpRes PD 5.3" in system  # grounding reached the prompt
        return json.dumps(
            {
                "text": "Here is a redraft citing OpRes PD 5.3.",
                "citations": [{"clause_number": "OpRes PD 5.3", "text": "irrelevant"}],
            }
        )

    reply = copilot_reply(
        node=node,
        intent="PD",
        history=[{"role": "user", "text": "hi"}, {"role": "copilot", "text": "hello"}],
        message="draft something",
        referenced_finding_ids=[],
        clause_index=clause_index,
        workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM,
        turn_fn=stub_turn,
    )

    assert reply["role"] == "copilot"
    assert reply["citations"][0]["text"] == "Scenario testing annually."


def test_copilot_reply_sends_history_as_user_assistant_turns(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}
    captured = {}

    def stub_turn(system, messages):
        captured["messages"] = messages
        return json.dumps({"text": "ok"})

    copilot_reply(
        node=node,
        intent="PD",
        history=[{"role": "user", "text": "hi"}, {"role": "copilot", "text": "hello"}],
        message="next",
        referenced_finding_ids=[],
        clause_index=clause_index,
        workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM,
        turn_fn=stub_turn,
    )

    assert captured["messages"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "next"},
    ]


def test_copilot_reply_raises_copilot_error_on_non_object_json(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_turn(system, messages):
        return json.dumps(["not", "an", "object"])

    try:
        copilot_reply(
            node=node,
            intent="PD",
            history=[],
            message="hi",
            referenced_finding_ids=[],
            clause_index=clause_index,
            workstreams_dir=tmp_path,
            workstream_id=_WORKSTREAM,
            turn_fn=stub_turn,
        )
        assert False, "expected CopilotError"
    except CopilotError:
        pass


def test_intents_tuple_has_the_seven_presets():
    assert len(INTENTS) == 7
    assert "PD" in INTENTS
