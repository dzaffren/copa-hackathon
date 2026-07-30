"""Tests for engine.copilot — live Copilot grounding + citation guardrail.

No network access: the turn/stream seam is always an injected stub, mirroring
`test_connections.py`'s `finder_fn`/`critic_fn` stubbing. Covers the two-layer
guardrail (`_build_grounding_context` assembling only citable clauses,
`_validate_reply` dropping anything not grounded), the prose/`<<<META>>>` split
(`_split_reply`), draft/selection awareness, and both reply orchestrations.
"""

import json

from engine import copilot, findings, workstreams
from engine.clauses import ClauseIndex
from engine.copilot import (
    META_SENTINEL,
    NO_MATCHING_CLAUSE,
    _build_grounding_context,
    _build_messages,
    _split_reply,
    _validate_reply,
    copilot_reply,
    copilot_reply_stream,
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


def _meta(payload: dict) -> str:
    """The trailing metadata block a model appends after its prose."""
    return f"\n{META_SENTINEL}\n{json.dumps(payload)}"


def _collect_sse(gen) -> list[dict]:
    """Parse SSE frames from the generator into a list of {event, data} dicts."""
    events = []
    for frame in gen:
        lines = frame.strip().split("\n")
        event = next(
            (l[len("event: "):] for l in lines if l.startswith("event: ")), "message"
        )
        data_line = next(
            (l[len("data: "):] for l in lines if l.startswith("data: ")), "{}"
        )
        events.append({"event": event, "data": json.loads(data_line)})
    return events


# --- _build_grounding_context ------------------------------------------------


def test_grounding_context_includes_task_documents_own_clauses(tmp_path):
    clause_index = _clause_index(
        {"OpRes PD 5.3": {"document_id": "opres-pd-v0-3", "text": "Scenario testing annually."}}
    )
    node = {"id": "opres-pd-v0-3", "title": "OpRes PD", "document_id": "opres-pd-v0-3"}

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, []
    )

    assert "CITABLE CLAUSES" in context
    assert "OpRes PD 5.3" in context
    assert "Scenario testing annually." in context
    assert grounded["OpRes PD 5.3"] == "Scenario testing annually."


def test_grounding_context_reports_no_clauses_when_node_has_no_document_id(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    context, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, []
    )

    assert "no clauses available" in context
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

    _, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, ["not-a-valid-id"]
    )

    assert grounded == {}


def test_referenced_finding_id_for_unanalysed_edge_is_skipped_not_errored(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    _, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, ["e-never-analysed~0"]
    )

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
    _, grounded = _build_grounding_context(
        node, clause_index, tmp_path, _WORKSTREAM, [f"{_EDGE}~5"]
    )

    assert grounded == {}


def test_grounding_context_includes_draft_and_selection_as_non_citable(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    context, grounded = _build_grounding_context(
        node,
        clause_index,
        tmp_path,
        _WORKSTREAM,
        [],
        draft_text="PART F\nThis Part does not displace existing requirements.",
        selection_text="This Part does not displace existing requirements.",
    )

    assert "CURRENT WORKING DRAFT" in context
    assert "PART F" in context
    assert "HIGHLIGHTED" in context
    # The draft and selection are context only — never citable.
    assert grounded == {}


# --- _split_reply ------------------------------------------------------------


def test_split_reply_no_sentinel_is_all_prose():
    prose, meta = _split_reply("Just some prose, no metadata.")
    assert prose == "Just some prose, no metadata."
    assert meta == {}


def test_split_reply_splits_prose_and_meta():
    raw = "Here is my answer." + _meta(
        {"citations": [{"clause_number": "X 1.1", "text": "t"}], "snippet_html": "<p>s</p>"}
    )
    prose, meta = _split_reply(raw)
    assert prose == "Here is my answer."
    assert meta["citations"][0]["clause_number"] == "X 1.1"
    assert meta["snippet_html"] == "<p>s</p>"


def test_split_reply_bad_json_tail_degrades_to_prose_only():
    prose, meta = _split_reply(f"Answer.\n{META_SENTINEL}\nnot valid json {{")
    assert prose == "Answer."
    assert meta == {}


def test_split_reply_empty_tail_is_prose_only():
    prose, meta = _split_reply(f"Answer.\n{META_SENTINEL}\n   ")
    assert prose == "Answer."
    assert meta == {}


# --- _validate_reply ---------------------------------------------------------


def test_validator_drops_a_citation_whose_clause_number_is_not_grounded():
    grounded = {"OpRes PD 5.3": "Scenario testing annually."}
    result = _validate_reply(
        "Cites both a real and a fabricated clause.",
        {
            "citations": [
                {"clause_number": "OpRes PD 5.3", "text": "Scenario testing annually."},
                {"clause_number": "Made Up 9.9", "text": "This clause does not exist."},
            ]
        },
        grounded,
    )

    assert len(result["citations"]) == 1
    assert result["citations"][0]["clause_number"] == "OpRes PD 5.3"


def test_validator_always_re_quotes_from_grounded_text_never_the_models_echo():
    grounded = {"OpRes PD 5.3": "Scenario testing annually."}
    result = _validate_reply(
        "x",
        {"citations": [{"clause_number": "OpRes PD 5.3", "text": "a paraphrased, WRONG echo"}]},
        grounded,
    )

    assert result["citations"][0]["text"] == "Scenario testing annually."


def test_validator_defaults_to_no_matching_clause_when_text_is_empty():
    result = _validate_reply("", {}, {})
    assert result["text"] == NO_MATCHING_CLAUSE


def test_validator_omits_citations_key_when_none_survive():
    result = _validate_reply("no clause supports this", {}, {})
    assert "citations" not in result


def test_validator_passes_through_snippet_html_when_present():
    result = _validate_reply("x", {"snippet_html": "<p>draft</p>"}, {})
    assert result["snippet_html"] == "<p>draft</p>"


def test_validator_omits_snippet_html_when_absent():
    result = _validate_reply("x", {}, {})
    assert "snippet_html" not in result


# --- copilot_reply (orchestration) ------------------------------------------


def test_copilot_reply_returns_the_validated_turn_fn_output(tmp_path):
    clause_index = _clause_index(
        {"OpRes PD 5.3": {"document_id": "opres-pd-v0-3", "text": "Scenario testing annually."}}
    )
    node = {"id": "opres-pd-v0-3", "title": "OpRes PD", "document_id": "opres-pd-v0-3"}

    def stub_turn(system, messages):
        assert "OpRes PD 5.3" in system  # grounding reached the prompt
        return "Here is a redraft citing OpRes PD 5.3." + _meta(
            {"citations": [{"clause_number": "OpRes PD 5.3", "text": "irrelevant"}]}
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
    assert reply["text"] == "Here is a redraft citing OpRes PD 5.3."
    assert reply["citations"][0]["text"] == "Scenario testing annually."


def test_copilot_reply_threads_draft_and_selection_into_the_prompt(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}
    captured = {}

    def stub_turn(system, messages):
        captured["system"] = system
        return "ok"

    copilot_reply(
        node=node,
        intent="PD",
        history=[],
        message="suggestions on this?",
        referenced_finding_ids=[],
        clause_index=clause_index,
        workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM,
        draft_text="PART F relationship with other policy documents",
        selection_text="PART F",
        turn_fn=stub_turn,
    )

    assert "CURRENT WORKING DRAFT" in captured["system"]
    assert "PART F relationship with other policy documents" in captured["system"]
    assert "HIGHLIGHTED" in captured["system"]


def test_copilot_reply_returns_prose_only_when_no_meta(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_turn(system, messages):
        return "Yes, the paper acknowledges overlap with existing policy documents."

    reply = copilot_reply(
        node=node,
        intent="PD",
        history=[],
        message="does it overlap?",
        referenced_finding_ids=[],
        clause_index=clause_index,
        workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM,
        turn_fn=stub_turn,
    )

    assert reply["role"] == "copilot"
    assert "overlap" in reply["text"]
    assert "citations" not in reply


def test_copilot_reply_sends_history_as_user_assistant_turns(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}
    captured = {}

    def stub_turn(system, messages):
        captured["messages"] = messages
        return "ok"

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


# --- _build_messages (alternation guardrail) --------------------------------
# Regression coverage for a real bug: a prior turn that never got a reply
# (e.g. a failed live call) left an unanswered "user" turn in the client's
# history. Appending the next message after it produced two consecutive
# "user" turns, which the Messages API rejects outright ("roles must
# alternate"), turning one failed call into every subsequent call failing too.


def test_build_messages_normal_alternating_history():
    messages = _build_messages(
        [{"role": "user", "text": "hi"}, {"role": "copilot", "text": "hello"}],
        "next",
    )
    assert messages == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "next"},
    ]


def test_build_messages_merges_an_unanswered_user_turn_instead_of_duplicating_role():
    messages = _build_messages([{"role": "user", "text": "first failed message"}], "next")
    assert messages == [
        {"role": "user", "content": "first failed message\n\nnext"},
    ]


def test_build_messages_merges_consecutive_copilot_turns_too():
    messages = _build_messages(
        [
            {"role": "user", "text": "hi"},
            {"role": "copilot", "text": "first reply"},
            {"role": "copilot", "text": "a second reply somehow logged"},
        ],
        "next",
    )
    assert messages == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "first reply\n\na second reply somehow logged"},
        {"role": "user", "content": "next"},
    ]
    assert all(
        messages[i]["role"] != messages[i + 1]["role"] for i in range(len(messages) - 1)
    )


def test_build_messages_skips_empty_turns():
    messages = _build_messages([{"role": "user", "text": ""}], "hi")
    assert messages == [{"role": "user", "content": "hi"}]


# --- copilot_reply_stream (SSE streaming generator) -------------------------


def test_copilot_reply_stream_streams_prose_tokens_then_done(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        yield "Hello"
        yield " world"

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    token_events = [e for e in events if e["event"] == "token"]
    done = next(e for e in events if e["event"] == "done")
    # Token boundaries are re-chunked by the sentinel hold-back; assert on the
    # concatenation, which is what the client reassembles.
    assert "".join(t["data"]["t"] for t in token_events) == "Hello world"
    assert done["data"]["text"] == "Hello world"
    assert not any(e["event"] == "error" for e in events)


def test_copilot_reply_stream_does_not_stream_the_meta_block(tmp_path):
    clause_index = _clause_index(
        {"OpRes PD 5.3": {"document_id": "opres-pd-v0-3", "text": "Annually."}}
    )
    node = {"id": "opres-pd-v0-3", "title": "OpRes PD", "document_id": "opres-pd-v0-3"}

    def stub_stream(system, messages):
        yield "Here is my answer."
        yield _meta(
            {
                "citations": [{"clause_number": "OpRes PD 5.3", "text": "ignored"}],
                "snippet_html": "<p>s</p>",
            }
        )

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    token_events = [e for e in events if e["event"] == "token"]
    joined = "".join(t["data"]["t"] for t in token_events)
    done = next(e for e in events if e["event"] == "done")

    assert META_SENTINEL not in joined
    assert "citations" not in joined  # the JSON metadata never streamed as prose
    assert joined.strip() == "Here is my answer."
    assert done["data"]["text"] == "Here is my answer."
    assert done["data"]["citations"][0]["text"] == "Annually."  # re-quoted, grounded
    assert done["data"]["snippet_html"] == "<p>s</p>"


def test_copilot_reply_stream_handles_sentinel_split_across_chunks(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        yield "Answer."
        yield "<<<"
        yield "META"
        yield ">>>"
        yield "\n" + json.dumps({"citations": []})

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    token_events = [e for e in events if e["event"] == "token"]
    joined = "".join(t["data"]["t"] for t in token_events)
    done = next(e for e in events if e["event"] == "done")

    assert META_SENTINEL not in joined
    assert joined == "Answer."
    assert done["data"]["text"] == "Answer."


def test_copilot_reply_stream_done_has_no_citations_when_none_are_grounded(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        yield "Cites a hallucinated clause."
        yield _meta({"citations": [{"clause_number": "MADE UP 99.9", "text": "fake"}]})

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    done = next(e for e in events if e["event"] == "done")
    assert done["data"]["text"] == "Cites a hallucinated clause."
    assert "citations" not in done["data"]


def test_copilot_reply_stream_yields_error_event_on_stream_fn_exception(tmp_path):
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "n1", "document_id": None}

    def stub_stream(system, messages):
        raise RuntimeError("Foundry credentials missing")
        yield  # make it a generator

    events = _collect_sse(copilot_reply_stream(
        node=node, intent="PD", history=[], message="hi",
        referenced_finding_ids=[],
        clause_index=clause_index, workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM, stream_fn=stub_stream,
    ))

    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) == 1
    assert "COPILOT_FAILED" in error_events[0]["data"]["code"]
    assert "credentials" in error_events[0]["data"]["message"]


def test_the_prompt_states_the_kind_without_claiming_the_drafter_chose_it(tmp_path):
    """The drafter no longer selects a kind, so the prompt must not tell the model
    they did — it states what the document IS. The citation guardrail either side
    of that line is unchanged, and asserted here so a reword cannot quietly take
    it with it."""
    clause_index = _clause_index({})
    node = {"id": "n1", "title": "RMiT FAQ", "document_id": None}
    captured = {}

    def stub_turn(system, messages):
        captured["system"] = system
        return "ok"

    copilot_reply(
        node=node,
        intent="FAQ",
        history=[],
        message="help me draft a section",
        referenced_finding_ids=[],
        clause_index=clause_index,
        workstreams_dir=tmp_path,
        workstream_id=_WORKSTREAM,
        turn_fn=stub_turn,
    )

    system = captured["system"]
    assert "FAQ" in system
    assert "has selected" not in system
    # The guardrail must survive the reword verbatim.
    assert "never licenses inventing content" in system
    assert copilot.NO_MATCHING_CLAUSE in system


def test_the_deliverable_vocabulary_is_the_eight_shared_task_types():
    """The Copilot no longer owns a vocabulary of its own: its old seven-preset
    `INTENTS` tuple is gone, replaced by the one shared `TASK_TYPES` map."""
    assert list(workstreams.TASK_TYPES) == [
        "PD", "DP", "ED", "FAQ", "DECK", "FEEDBACK", "BENCHMARK", "OTHERS",
    ]
    assert workstreams.TASK_TYPES["PD"] == "Policy Document"
    assert not hasattr(copilot, "INTENTS")
