"""Tests for engine.connections — two-agent finder+critic + citation validator.

Covers spec Test Scenarios 6 and 7 (docs/specs/rulebook-radar/
spec-knowledge-graph-engine.md, "Stage 4 is a two-agent loop"):

- Test 6 stubs BOTH agent turns: the finder returns the RMiT 17.1 ↔
  Outsourcing 12.1 conflict; the critic scopes it (the 12.4 affiliate
  exemption → `scope_note`) and ADDS the missed `RMiT 17.2` → `RMiT 17.1`
  dependency (the recall pass). Both surviving candidates cite clauses that
  resolve in the index, so both land in `connections`, verbatim.
- Test 7 stubs the critic turn to emit a candidate citing `Cyber 4.4`
  (absent from the index) — proving the deterministic code verifier gates
  the critic's output too, not just the finder's.

No network access: both agent turns are injected stubs, and the clause index
is hand-built markdown + `build_clause_index` (matching engine/tests/
test_graph.py and test_clauses.py). Traces are written to a tmp dir, never the
tracked `data/artifacts/`.
"""

import json
from datetime import datetime, timezone

import pytest

from engine.clauses import (
    ClauseIndex,
    build_clause_index,
    build_reference_clause,
    merge_clause_indexes,
)
from engine.connections import (
    CRITIC_SYSTEM_PROMPT,
    FINDER_SYSTEM_PROMPT,
    Connection,
    _critic_turn,
    _finder_turn,
    _format_clause_context,
    _parse_candidate_list,
    analyse_paragraph,
    connections_for_paragraph,
    find_connections,
)
from engine.llm import LLMResponseError

# --- Corpus fixtures (verbatim markdown + hand-written anchors) -------------

RMIT_V2_MARKDOWN = """RMiT — Exposure Draft v2

17 Cloud services

17.1 A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud service for a critical system.

17.2 A financial institution shall notify the Bank of any subsequent adoption of a public cloud service for a critical system.
"""

RMIT_V2_ANCHORS = [
    {
        "clause_number": "17.1",
        "starts_with": "A financial institution shall notify the Bank within 14 days",
        "heading": "17 Cloud services",
        "parent": None,
    },
    {
        "clause_number": "17.2",
        "starts_with": "A financial institution shall notify the Bank of any subsequent",
        "heading": "17 Cloud services",
        "parent": None,
    },
]

OUTSOURCING_MARKDOWN = """Outsourcing

12 Approval for material outsourcing arrangements

12.1 A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement.

12.4 The approval requirement does not apply to an outsourcing arrangement with an affiliate within the same financial group.
"""

OUTSOURCING_ANCHORS = [
    {
        "clause_number": "12.1",
        "starts_with": "A financial institution must obtain the Bank's written approval",
        "heading": "12 Approval for material outsourcing arrangements",
        "parent": None,
    },
    {
        "clause_number": "12.4",
        "starts_with": "The approval requirement does not apply to an outsourcing arrangement",
        "heading": "12 Approval for material outsourcing arrangements",
        "parent": None,
    },
]

OUTSOURCING_12_1_TEXT = (
    "A financial institution must obtain the Bank's written approval before "
    "entering into a new material outsourcing arrangement."
)


def _build_fixture_clause_index() -> ClauseIndex:
    rmit_entries = build_clause_index(
        anchors=RMIT_V2_ANCHORS,
        markdown=RMIT_V2_MARKDOWN,
        document_id="rmit-v2-2026-draft",
        policy_id="rmit",
        source="draft",
    )
    outsourcing_entries = build_clause_index(
        anchors=OUTSOURCING_ANCHORS,
        markdown=OUTSOURCING_MARKDOWN,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )
    primary, versions = merge_clause_indexes(
        [
            ("rmit-v2-2026-draft", rmit_entries),
            ("outsourcing-v1-2019", outsourcing_entries),
        ],
        current_document_id="rmit-v2-2026-draft",
    )
    return ClauseIndex(primary, versions)


FIXED_NOW = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)


# --- Stub agent turns -------------------------------------------------------


def _finder_returns_conflict(doc_a_id, doc_b_id, clause_index):
    """Finder pass: proposes the 12.1 ↔ 17.1 conflict, no scope note yet."""
    return [
        {
            "summary": (
                "RMiT 17.1 (notify-after amendment) conflicts with Outsourcing "
                "12.1 (approve-before)."
            ),
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["Outsourcing 12.1"],
        }
    ]


def _critic_scopes_and_adds_dependency(doc_a_id, doc_b_id, clause_index, candidates):
    """Critic pass: scopes the finder's conflict with the 12.4 affiliate
    exemption AND surfaces the missed 17.2 → 17.1 dependency (recall)."""
    return [
        {
            "summary": (
                "RMiT 17.1 (notify-after amendment) conflicts with Outsourcing "
                "12.1 (approve-before) where the cloud service is also a "
                "material outsourcing."
            ),
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["Outsourcing 12.1"],
            "scope_note": (
                "Applies only where the cloud service is a material outsourcing; "
                "Outsourcing 12.4 exempts intra-group affiliate arrangements."
            ),
        },
        {
            "summary": (
                "RMiT 17.2 depends on a prior 17.1 consultation that the "
                "amendment removes."
            ),
            "source_clauses": ["RMiT 17.2"],
            "target_clauses": ["RMiT 17.1"],
        },
    ]


def test_two_agent_loop_surfaces_conflict_and_critic_found_dependency(tmp_path):
    clause_index = _build_fixture_clause_index()

    result = find_connections(
        "rmit-v2-2026-draft",
        "outsourcing-v1-2019",
        clause_index,
        finder_fn=_finder_returns_conflict,
        critic_fn=_critic_scopes_and_adds_dependency,
        output_dir=tmp_path,
        now=FIXED_NOW,
    )

    connections = result["connections"]
    assert result["unsupported"] == []

    # The finder's conflict, scoped by the critic, quoting 12.1 verbatim.
    conflict = next(
        c
        for c in connections
        if any(sc["clause_number"] == "RMiT 17.1" for sc in c["source_clauses"])
        and any(
            tc["clause_number"] == "Outsourcing 12.1" for tc in c["target_clauses"]
        )
    )
    assert conflict["supported"] is True
    target_12_1 = next(
        tc
        for tc in conflict["target_clauses"]
        if tc["clause_number"] == "Outsourcing 12.1"
    )
    assert target_12_1["text"] == OUTSOURCING_12_1_TEXT
    assert "affiliate" in conflict["scope_note"]

    # The critic-surfaced dependency (proves the recall pass).
    dependency = next(
        c
        for c in connections
        if any(sc["clause_number"] == "RMiT 17.2" for sc in c["source_clauses"])
        and any(tc["clause_number"] == "RMiT 17.1" for tc in c["target_clauses"])
    )
    assert dependency["supported"] is True

    # A connection-trace was written with both raw agent outputs.
    traces = list(tmp_path.glob("connection-trace-*.json"))
    assert len(traces) == 1
    trace = json.loads(traces[0].read_text())
    assert trace["model_id"]
    assert trace["timestamp"] == FIXED_NOW.isoformat()
    assert trace["finder_output"] == _finder_returns_conflict(
        "rmit-v2-2026-draft", "outsourcing-v1-2019", clause_index
    )
    assert trace["critic_output"] == _critic_scopes_and_adds_dependency(
        "rmit-v2-2026-draft", "outsourcing-v1-2019", clause_index, []
    )
    assert trace["validation"]


def test_unsupported_candidate_from_critic_is_flagged_not_invented(tmp_path):
    clause_index = _build_fixture_clause_index()

    def critic_emits_absent_clause(doc_a_id, doc_b_id, clause_index, candidates):
        return [
            {
                "summary": "RMiT 17.1 conflicts with a cyber-resilience requirement.",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Cyber 4.4"],
            }
        ]

    result = find_connections(
        "rmit-v2-2026-draft",
        "outsourcing-v1-2019",
        clause_index,
        finder_fn=_finder_returns_conflict,
        critic_fn=critic_emits_absent_clause,
        output_dir=tmp_path,
        now=FIXED_NOW,
    )

    # The candidate citing the absent Cyber 4.4 never reaches `connections`.
    for connection in result["connections"]:
        cited = [
            c["clause_number"]
            for c in connection["source_clauses"] + connection["target_clauses"]
        ]
        assert "Cyber 4.4" not in cited

    assert len(result["unsupported"]) == 1
    unsupported = result["unsupported"][0]
    assert unsupported["supported"] is False
    assert unsupported["message"] == "No matching clause found"
    # No fabricated clause text is attached to an unsupported candidate.
    assert "source_clauses" not in unsupported
    assert "target_clauses" not in unsupported


# --- Turn helpers (pure + parsing, no network) ------------------------------


def test_format_clause_context_labels_both_documents_with_numbers_and_text():
    clause_index = _build_fixture_clause_index()

    context = _format_clause_context(
        clause_index, "rmit-v2-2026-draft", "outsourcing-v1-2019"
    )

    # Both document ids appear as labels.
    assert "rmit-v2-2026-draft" in context
    assert "outsourcing-v1-2019" in context
    # Every clause number of both documents appears...
    assert "RMiT 17.1" in context
    assert "RMiT 17.2" in context
    assert "Outsourcing 12.1" in context
    assert "Outsourcing 12.4" in context
    # ...alongside its verbatim text.
    assert "shall notify the Bank within 14 days" in context
    assert OUTSOURCING_12_1_TEXT in context


def test_finder_turn_parses_call_chat_json_array(monkeypatch):
    clause_index = _build_fixture_clause_index()
    canned = json.dumps(
        [
            {
                "summary": "RMiT 17.1 conflicts with Outsourcing 12.1.",
                "label": "conflicts-with",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]
    )
    captured = {}

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured["deployment"] = deployment
        captured["system"] = system
        captured["user"] = user
        return canned

    monkeypatch.setattr("engine.connections.call_chat", fake_call_chat)

    result = _finder_turn("rmit-v2-2026-draft", "outsourcing-v1-2019", clause_index)

    assert result == json.loads(canned)
    # The finder handed the model both documents' clause context.
    assert "RMiT 17.1" in captured["user"]
    assert "Outsourcing 12.1" in captured["user"]


def test_critic_turn_includes_finder_candidates_in_prompt(monkeypatch):
    clause_index = _build_fixture_clause_index()
    finder_candidates = [
        {
            "summary": "RMiT 17.1 conflicts with Outsourcing 12.1.",
            "label": "conflicts-with",
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["Outsourcing 12.1"],
        }
    ]
    canned = json.dumps(
        finder_candidates
        + [
            {
                "summary": "RMiT 17.2 depends on RMiT 17.1.",
                "label": "aligns-with",
                "source_clauses": ["RMiT 17.2"],
                "target_clauses": ["RMiT 17.1"],
            }
        ]
    )
    captured = {}

    def fake_call_chat(deployment, system, user, max_tokens=None):
        captured["user"] = user
        return canned

    monkeypatch.setattr("engine.connections.call_chat", fake_call_chat)

    result = _critic_turn(
        "rmit-v2-2026-draft",
        "outsourcing-v1-2019",
        clause_index,
        finder_candidates,
    )

    assert result == json.loads(canned)
    # The critic prompt carries the finder's candidates for it to scope/refute.
    assert "RMiT 17.1 conflicts with Outsourcing 12.1." in captured["user"]
    # ...and still the clause context.
    assert "Outsourcing 12.4" in captured["user"]


def test_finder_turn_raises_on_non_json(monkeypatch):
    clause_index = _build_fixture_clause_index()
    monkeypatch.setattr(
        "engine.connections.call_chat",
        lambda deployment, system, user, max_tokens=None: "sorry, no JSON here",
    )
    with pytest.raises(LLMResponseError):
        _finder_turn("rmit-v2-2026-draft", "outsourcing-v1-2019", clause_index)


def test_critic_turn_raises_on_non_list_json(monkeypatch):
    clause_index = _build_fixture_clause_index()
    monkeypatch.setattr(
        "engine.connections.call_chat",
        lambda deployment, system, user, max_tokens=None: json.dumps({"not": "a list"}),
    )
    with pytest.raises(LLMResponseError):
        _critic_turn(
            "rmit-v2-2026-draft", "outsourcing-v1-2019", clause_index, []
        )


# --- Two-branch paragraph orchestration (spec Task 5) -----------------------

# A source-clause fixture index for the two-branch tests: BCBS 239 P4 (a cited
# source) + PDPA 129 (an un-cited library source). Built with
# `build_reference_clause`, mirroring test_verdicts.py's no-network discipline.
PDPA_129_TEXT = (
    "A data controller may transfer any personal data of a data subject to any "
    "place outside Malaysia if— (a) there is in that place in force any law "
    "which is substantially similar to this Act."
)
BCBS_239_P4_TEXT = (
    "A bank should be able to capture and aggregate all material risk data "
    "across the banking group."
)


def _build_source_index() -> ClauseIndex:
    primary: dict = {}
    versions: dict = {}
    refs = {
        **build_reference_clause(
            "pdpa-2010", "pdpa", "129", "Section 129(2)", PDPA_129_TEXT
        ),
        **build_reference_clause(
            "bcbs-239", "bcbs-239", "P4", "Principle 4", BCBS_239_P4_TEXT
        ),
    }
    for clause_number, entry in refs.items():
        primary[clause_number] = entry
        versions.setdefault(clause_number, {})[entry["document_id"]] = entry
    return ClauseIndex(primary, versions)


def test_connections_for_paragraph_filters_by_paragraph():
    connections = [
        {"id": "a", "paragraph": "3.5"},
        {"id": "b", "paragraph": "4.6"},
        {"id": "c", "paragraph": "3.5"},
    ]
    result = connections_for_paragraph(connections, "3.5")
    assert [c["id"] for c in result] == ["a", "c"]
    # A paragraph with no matching connection yields an empty list (the caller
    # turns that into no_matching_source / not_analysed).
    assert connections_for_paragraph(connections, "9.9") == []


def test_analyse_paragraph_combines_and_tags_both_branches(tmp_path):
    """Branch ① (cited) + branch ② (uncited) candidates are combined and each is
    branch-tagged; the stub finder returns a different candidate per branch."""
    index = _build_source_index()

    def stub_finder(paragraph_number, paragraph_text, clause_index, branch, source_ids):
        if branch == "cited":
            return [
                {
                    "source_document_id": "bcbs-239",
                    "clause_number": "BCBS 239 P4",
                    "confidence_score": 0.88,
                    "verification": "verified",
                    "verdict": "Consensus",
                }
            ]
        return [
            {
                "source_document_id": "pdpa-2010",
                "clause_number": "PDPA 129",
                "confidence_score": 0.90,
                "verification": "verified",
                "verdict": "Conflict",
            }
        ]

    result = analyse_paragraph(
        "4.6",
        "As AI applications process personal data...",
        index,
        cited_source_ids=["bcbs-239"],
        curated_source_ids=["pdpa-2010"],
        finder_fn=stub_finder,
        now=FIXED_NOW,
        output_dir=tmp_path,
    )

    assert len(result) == 2
    by_source = {c["source_document_id"]: c for c in result}
    assert by_source["bcbs-239"]["branch"] == "cited"
    assert by_source["pdpa-2010"]["branch"] == "uncited"
    # Each candidate carries the paragraph and a deterministic AI_DP-style id.
    assert all(c["paragraph"] == "4.6" for c in result)
    assert by_source["pdpa-2010"]["id"] == "ai-dp-2025:4.6::pdpa-2010:PDPA 129"
    assert by_source["bcbs-239"]["id"] == "ai-dp-2025:4.6::bcbs-239:BCBS 239 P4"

    # A trace backstop was written for the analysed paragraph.
    traces = list(tmp_path.glob("analyse-trace-*.json"))
    assert len(traces) == 1


def test_analyse_paragraph_empty_both_branches_returns_empty():
    """When both branches surface nothing, the result is [] — the signal the API
    turns into no_matching_source (never a fabricated connection)."""
    index = _build_source_index()

    def empty_finder(paragraph_number, paragraph_text, clause_index, branch, source_ids):
        return []

    result = analyse_paragraph(
        "3.2",
        "The board and senior management...",
        index,
        cited_source_ids=["bcbs-239"],
        curated_source_ids=["pdpa-2010"],
        finder_fn=empty_finder,
    )
    assert result == []


def test_analyse_paragraph_guardrail_drops_unresolved_keeps_blocked_and_pending():
    """The guardrail drops a candidate citing an unresolved clause, but KEEPS a
    blocked (could_not_retrieve) candidate and a pending_extraction candidate."""
    index = _build_source_index()  # resolves PDPA 129 + BCBS 239 P4, NOT others

    def stub_finder(paragraph_number, paragraph_text, clause_index, branch, source_ids):
        if branch == "cited":
            return [
                # Unresolved clause → dropped by the guardrail.
                {
                    "source_document_id": "cyber-x",
                    "clause_number": "Cyber 4.4",
                    "confidence_score": 0.9,
                    "verdict": "Gap",
                },
                # Blocked source, no clause → KEPT (honest could_not_retrieve).
                {
                    "source_document_id": "mas-feat",
                    "status": "could_not_retrieve",
                    "reason": "The MAS site blocks automated access.",
                },
            ]
        return [
            # Pending extraction, clause not in the index → KEPT.
            {
                "source_document_id": "basel-osfi",
                "clause_number": "Basel RBC20",
                "confidence_score": 0.84,
                "verification": "pending_extraction",
                "verdict": "Consensus",
            }
        ]

    result = analyse_paragraph(
        "3.5",
        "A major challenge of AI...",
        index,
        cited_source_ids=["cyber-x", "mas-feat"],
        curated_source_ids=["basel-osfi"],
        finder_fn=stub_finder,
    )

    kept_sources = {c["source_document_id"] for c in result}
    assert kept_sources == {"mas-feat", "basel-osfi"}
    # The unresolved-clause candidate never survives to the verdict stage.
    assert "cyber-x" not in kept_sources
    blocked = next(c for c in result if c["source_document_id"] == "mas-feat")
    assert blocked["status"] == "could_not_retrieve"
    pending = next(c for c in result if c["source_document_id"] == "basel-osfi")
    assert pending["verification"] == "pending_extraction"


# --- Semantic linkage taxonomy (label + optional sentiment) -----------------


def test_widened_connection_typeddict():
    """A Connection now carries a five-value ``label`` and, only on
    ``differs-on``, an optional ``sentiment`` — both reported by
    ``get_type_hints`` and constructible with the documented values."""
    import typing

    aligned: Connection = {
        "summary": "RMiT 17.1 adopts the same notification window as its source.",
        "label": "aligns-with",
        "sentiment": None,
        "source_clauses": [],
        "target_clauses": [],
        "scope_note": None,
        "supported": True,
    }
    differs: Connection = {
        "summary": "RMiT 17.1 shortens the notification window its source allows.",
        "label": "differs-on",
        "sentiment": "tighten",
        "source_clauses": [],
        "target_clauses": [],
        "scope_note": None,
        "supported": True,
    }

    assert aligned["label"] == "aligns-with"
    assert aligned["sentiment"] is None
    assert differs["label"] == "differs-on"
    assert differs["sentiment"] == "tighten"

    hints = typing.get_type_hints(Connection)
    assert "label" in hints
    assert "sentiment" in hints


def test_parse_rejects_missing_label():
    """A candidate with no ``label`` is rejected loudly (never coerced)."""
    raw = json.dumps(
        [
            {
                "summary": "x",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]
    )
    with pytest.raises(LLMResponseError) as exc:
        _parse_candidate_list(raw)
    assert "label" in str(exc.value)


def test_parse_rejects_unknown_label():
    """A ``label`` outside the five-value set is rejected."""
    raw = json.dumps(
        [
            {
                "summary": "x",
                "label": "duplicates",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]
    )
    with pytest.raises(LLMResponseError) as exc:
        _parse_candidate_list(raw)
    assert "duplicates" in str(exc.value)


def test_parse_rejects_sentiment_on_nondiffers():
    """``sentiment`` on any label other than ``differs-on`` is rejected."""
    raw = json.dumps(
        [
            {
                "summary": "x",
                "label": "aligns-with",
                "sentiment": "tighten",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]
    )
    with pytest.raises(LLMResponseError) as exc:
        _parse_candidate_list(raw)
    message = str(exc.value)
    assert "sentiment" in message
    assert "differs-on" in message


def test_parse_rejects_unknown_sentiment():
    """A ``sentiment`` outside tighten/loosen/neutral is rejected even on
    ``differs-on``."""
    raw = json.dumps(
        [
            {
                "summary": "x",
                "label": "differs-on",
                "sentiment": "stricter",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]
    )
    with pytest.raises(LLMResponseError) as exc:
        _parse_candidate_list(raw)
    assert "stricter" in str(exc.value)


def test_parse_accepts_sentiment_on_differs():
    """A well-formed ``differs-on`` candidate with a sentiment parses cleanly,
    both fields intact, no coercion."""
    raw = json.dumps(
        [
            {
                "summary": "x",
                "label": "differs-on",
                "sentiment": "tighten",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]
    )
    result = _parse_candidate_list(raw)
    assert len(result) == 1
    assert result[0]["label"] == "differs-on"
    assert result[0]["sentiment"] == "tighten"


def _finder_direction_aware(doc_a_id, doc_b_id, clause_index):
    """Emit ``goes-beyond`` when RMiT is the OUR side (doc A) and ``silent-on``
    when it is the THEIR side (doc B) — the same finding, direction-flipped. The
    cited clauses resolve in both directions so only the label changes."""
    label = "goes-beyond" if doc_a_id == "rmit-v2-2026-draft" else "silent-on"
    return [
        {
            "summary": "Our side names a cloud-governance officer the other omits.",
            "label": label,
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["Outsourcing 12.1"],
        }
    ]


def _critic_passthrough(doc_a_id, doc_b_id, clause_index, candidates):
    """Critic that neither refutes nor scopes — it passes candidates through so
    the test isolates direction handling in the validator."""
    return list(candidates)


def test_direction_flip_swaps_silent_and_goesbeyond(tmp_path):
    """Swapping the pair flips ``silent-on`` ⇄ ``goes-beyond`` (a coverage
    asymmetry is directional), while the verbatim citations are unchanged."""
    clause_index = _build_fixture_clause_index()

    forward = find_connections(
        "rmit-v2-2026-draft",
        "outsourcing-v1-2019",
        clause_index,
        finder_fn=_finder_direction_aware,
        critic_fn=_critic_passthrough,
        output_dir=tmp_path,
        now=FIXED_NOW,
    )
    reverse = find_connections(
        "outsourcing-v1-2019",
        "rmit-v2-2026-draft",
        clause_index,
        finder_fn=_finder_direction_aware,
        critic_fn=_critic_passthrough,
        output_dir=tmp_path,
        now=FIXED_NOW,
    )

    forward_finding = forward["connections"][0]
    reverse_finding = reverse["connections"][0]
    assert forward_finding["label"] == "goes-beyond"
    assert reverse_finding["label"] == "silent-on"
    # A coverage-asymmetry finding never carries a sentiment.
    assert forward_finding["sentiment"] is None
    assert reverse_finding["sentiment"] is None
    # The verbatim citations are identical in both directions — only the label
    # flips (the guardrail is untouched).
    for finding in (forward_finding, reverse_finding):
        assert [c["clause_number"] for c in finding["source_clauses"]] == ["RMiT 17.1"]
        assert [c["clause_number"] for c in finding["target_clauses"]] == [
            "Outsourcing 12.1"
        ]


def test_write_trace_records_label_and_sentiment(tmp_path):
    """Every ``validation`` entry in the connection-trace records the finding's
    ``label`` and ``sentiment`` alongside summary/cited_clauses/supported."""
    clause_index = _build_fixture_clause_index()

    def finder(doc_a_id, doc_b_id, clause_index):
        return [
            {
                "summary": "RMiT 17.1 shortens the window Outsourcing 12.1 allows.",
                "label": "differs-on",
                "sentiment": "tighten",
                "source_clauses": ["RMiT 17.1"],
                "target_clauses": ["Outsourcing 12.1"],
            }
        ]

    find_connections(
        "rmit-v2-2026-draft",
        "outsourcing-v1-2019",
        clause_index,
        finder_fn=finder,
        critic_fn=_critic_passthrough,
        output_dir=tmp_path,
        now=FIXED_NOW,
    )

    trace_path = next(tmp_path.glob("connection-trace-*.json"))
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    entry = trace["validation"][0]
    assert entry["label"] == "differs-on"
    assert entry["sentiment"] == "tighten"


@pytest.mark.parametrize("prompt", [FINDER_SYSTEM_PROMPT, CRITIC_SYSTEM_PROMPT])
def test_prompts_describe_taxonomy_and_direction(prompt):
    """Both system prompts must state the five labels, the sentiment values
    (and that they attach only to ``differs-on``), and the fixed direction
    convention (document A = we/ours, document B = they/theirs)."""
    for label in (
        "aligns-with",
        "differs-on",
        "conflicts-with",
        "silent-on",
        "goes-beyond",
    ):
        assert label in prompt
    for sentiment in ("tighten", "loosen", "neutral"):
        assert sentiment in prompt
    # Sentiment is scoped to differs-on only.
    assert "sentiment" in prompt
    # Direction convention tokens.
    assert "we/ours" in prompt
    assert "they/theirs" in prompt
    # The strict citation rule survives the rewrite.
    assert "CITATION RULE" in prompt
