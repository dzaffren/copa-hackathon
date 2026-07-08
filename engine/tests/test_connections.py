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

from engine.clauses import ClauseIndex, build_clause_index, merge_clause_indexes
from engine.connections import find_connections

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
