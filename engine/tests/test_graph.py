"""Tests for engine.graph — node/edge model, curated builder, status derivation.

Covers spec Test Scenarios 5 and 8 (docs/specs/rulebook-radar/
spec-knowledge-graph-engine.md) plus the version-lineage invariant called
out in Task 3 of the implementation plan.

No network access: fixtures are hand-built markdown + anchors (matching
engine/tests/test_clauses.py's pattern), never the real corpus.
"""

import pytest

from engine.clauses import ClauseIndex, build_clause_index
from engine.graph import GraphBuildError, build_graph

RMIT_V1_MARKDOWN = """RMiT

17 Cloud services

17.1 A financial institution shall consult the Bank prior to the first-time adoption of a public cloud service for a critical system.
"""

RMIT_V1_ANCHORS = [
    {
        "clause_number": "17.1",
        "starts_with": "A financial institution shall consult the Bank prior",
        "heading": "17 Cloud services",
        "parent": None,
    },
]

RMIT_V2_MARKDOWN = """RMiT — Exposure Draft v2

10 Technology Operations Management

10.50 A financial institution must fully understand the inherent risk of adopting cloud services.

17 Cloud services

17.1 A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud service for a critical system.

17.2 A financial institution shall notify the Bank of any subsequent adoption of a public cloud service for a critical system.
"""

RMIT_V2_ANCHORS = [
    {
        "clause_number": "10.50",
        "starts_with": "A financial institution must fully understand the inherent risk",
        "heading": "10 Technology Operations Management",
        "parent": None,
    },
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

OPRES_MARKDOWN = """Operational Resilience

6 Critical operations

6.11 A financial institution must maintain a register of critical cloud and third-party services.
"""

OPRES_ANCHORS = [
    {
        "clause_number": "6.11",
        "starts_with": "A financial institution must maintain a register",
        "heading": "6 Critical operations",
        "parent": None,
    },
]

BCM_MARKDOWN = """Business Continuity Management

5 Continuity arrangements

5.1 A financial institution must maintain continuity arrangements for critical systems.
"""

BCM_ANCHORS = [
    {
        "clause_number": "5.1",
        "starts_with": "A financial institution must maintain continuity arrangements",
        "heading": "5 Continuity arrangements",
        "parent": None,
    },
]


DOCUMENTS = {
    "rmit-v1-2020": {
        "policy_id": "rmit",
        "document_id": "rmit-v1-2020",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v1 · 2020",
        "cluster": "technology-risk",
    },
    "rmit-v2-2026-draft": {
        "policy_id": "rmit",
        "document_id": "rmit-v2-2026-draft",
        "title": "Risk Management in Technology (RMiT)",
        "version": "v2 · 2026 draft",
        "cluster": "technology-risk",
    },
    "opres-v1-2025": {
        "policy_id": "opres",
        "document_id": "opres-v1-2025",
        "title": "Operational Resilience",
        "version": "v1 · 2025",
        "cluster": "technology-risk",
    },
    "bcm-v1-2022": {
        "policy_id": "bcm",
        "document_id": "bcm-v1-2022",
        "title": "Business Continuity Management",
        "version": "v1 · 2022",
        "cluster": "technology-risk",
    },
}


def _build_fixture_clause_index() -> ClauseIndex:
    rmit_v1_entries = build_clause_index(
        anchors=RMIT_V1_ANCHORS,
        markdown=RMIT_V1_MARKDOWN,
        document_id="rmit-v1-2020",
        policy_id="rmit",
        source="published",
    )
    rmit_v2_entries = build_clause_index(
        anchors=RMIT_V2_ANCHORS,
        markdown=RMIT_V2_MARKDOWN,
        document_id="rmit-v2-2026-draft",
        policy_id="rmit",
        source="draft",
    )
    opres_entries = build_clause_index(
        anchors=OPRES_ANCHORS,
        markdown=OPRES_MARKDOWN,
        document_id="opres-v1-2025",
        policy_id="opres",
        source="published",
    )
    bcm_entries = build_clause_index(
        anchors=BCM_ANCHORS,
        markdown=BCM_MARKDOWN,
        document_id="bcm-v1-2022",
        policy_id="bcm",
        source="published",
    )

    from engine.clauses import merge_clause_indexes

    primary, versions = merge_clause_indexes(
        [
            ("rmit-v1-2020", rmit_v1_entries),
            ("rmit-v2-2026-draft", rmit_v2_entries),
            ("opres-v1-2025", opres_entries),
            ("bcm-v1-2022", bcm_entries),
        ],
        current_document_id="rmit-v2-2026-draft",
    )
    return ClauseIndex(primary, versions)


DRAFT_REGISTRY = {"live_drafts": ["rmit", "opres"]}

CURATED_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "opres",
        "type": "overlaps",
        "reason": (
            "Both govern the register of critical cloud/third-party "
            "services. RMiT 10.50 overlaps Operational Resilience 6.11."
        ),
        "source_clauses": ["RMiT 10.50"],
        "target_clauses": ["Operational Resilience 6.11"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]


def test_curated_edge_has_reason_clause_anchors_and_resolves_in_index():
    clause_index = _build_fixture_clause_index()

    graph = build_graph(
        documents=DOCUMENTS,
        curated_edges=CURATED_EDGES,
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
    )

    non_lineage = [e for e in graph["edges"] if e["type"] != "version-lineage"]
    assert len(non_lineage) == 1
    edge = non_lineage[0]

    assert edge["source"] == "rmit-v2-2026-draft"
    assert edge["target"] == "opres-v1-2025"
    assert edge["reason"]
    assert len(edge["source_clauses"]) >= 1
    assert len(edge["target_clauses"]) >= 1
    for clause_number in edge["source_clauses"] + edge["target_clauses"]:
        assert clause_index.get(clause_number) is not None
    assert edge["provenance"] in {"structural", "curated", "llm-found"}
    assert 0.0 <= edge["confidence"] <= 1.0
    assert edge["confidence"] == 1.0


def test_curated_edge_citing_unknown_clause_raises_graph_build_error():
    clause_index = _build_fixture_clause_index()
    bad_edges = [
        {
            "source_policy_id": "rmit",
            "target_policy_id": "opres",
            "type": "overlaps",
            "reason": "A made-up connection.",
            "source_clauses": ["RMiT 99.9"],
            "target_clauses": ["Operational Resilience 6.11"],
            "provenance": "curated",
            "confidence": 1.0,
        },
    ]

    with pytest.raises(GraphBuildError, match="RMiT 99.9"):
        build_graph(
            documents=DOCUMENTS,
            curated_edges=bad_edges,
            clause_index=clause_index,
            draft_registry=DRAFT_REGISTRY,
        )


def test_curated_edge_with_empty_reason_raises_graph_build_error():
    clause_index = _build_fixture_clause_index()
    bad_edges = [
        {
            "source_policy_id": "rmit",
            "target_policy_id": "opres",
            "type": "overlaps",
            "reason": "",
            "source_clauses": ["RMiT 10.50"],
            "target_clauses": ["Operational Resilience 6.11"],
            "provenance": "curated",
            "confidence": 1.0,
        },
    ]

    with pytest.raises(GraphBuildError, match="no reason"):
        build_graph(
            documents=DOCUMENTS,
            curated_edges=bad_edges,
            clause_index=clause_index,
            draft_registry=DRAFT_REGISTRY,
        )


def test_curated_edge_with_empty_clause_list_raises_graph_build_error():
    clause_index = _build_fixture_clause_index()
    bad_edges = [
        {
            "source_policy_id": "rmit",
            "target_policy_id": "opres",
            "type": "overlaps",
            "reason": "A connection with no clause anchor on one side.",
            "source_clauses": [],
            "target_clauses": ["Operational Resilience 6.11"],
            "provenance": "curated",
            "confidence": 1.0,
        },
    ]

    with pytest.raises(GraphBuildError, match="source_clauses"):
        build_graph(
            documents=DOCUMENTS,
            curated_edges=bad_edges,
            clause_index=clause_index,
            draft_registry=DRAFT_REGISTRY,
        )


def test_edges_are_sorted_by_source_target_type_for_determinism():
    clause_index = _build_fixture_clause_index()
    # A second curated edge whose source ("bcm-...") sorts alphabetically
    # before both the version-lineage edge's source ("rmit-v1-2020") and
    # the first curated edge's source ("rmit-v2-...") — so natural
    # insertion order (lineage, then curated edges in list order) would
    # NOT already be sorted; only an explicit sort makes this pass.
    edges_out_of_natural_order = CURATED_EDGES + [
        {
            "source_policy_id": "bcm",
            "target_policy_id": "opres",
            "type": "overlaps",
            "reason": "Both cover recovery of critical operations.",
            "source_clauses": ["BCM 5.1"],
            "target_clauses": ["Operational Resilience 6.11"],
            "provenance": "curated",
            "confidence": 1.0,
        },
    ]

    graph = build_graph(
        documents=DOCUMENTS,
        curated_edges=edges_out_of_natural_order,
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
    )

    sort_keys = [(e["source"], e["target"], e["type"]) for e in graph["edges"]]
    assert sort_keys == sorted(sort_keys)
    assert sort_keys[0][0] == "bcm-v1-2022"


def _node(graph: dict, document_id: str) -> dict:
    matches = [n for n in graph["nodes"] if n["id"] == document_id]
    assert matches, f"no node with id '{document_id}' in graph"
    return matches[0]


def test_status_is_derived_from_draft_registry_never_hand_set():
    clause_index = _build_fixture_clause_index()

    graph = build_graph(
        documents=DOCUMENTS,
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
    )

    assert _node(graph, "rmit-v2-2026-draft")["status"] == "In progress"
    assert _node(graph, "opres-v1-2025")["status"] == "In progress"
    assert _node(graph, "bcm-v1-2022")["status"] == "In force"
    assert _node(graph, "rmit-v1-2020")["status"] == "Superseded"


def test_version_lineage_edge_links_older_document_to_newer_of_same_policy():
    clause_index = _build_fixture_clause_index()

    graph = build_graph(
        documents=DOCUMENTS,
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
    )

    lineage_edges = [e for e in graph["edges"] if e["type"] == "version-lineage"]
    assert len(lineage_edges) == 1
    edge = lineage_edges[0]
    assert edge["source"] == "rmit-v1-2020"
    assert edge["target"] == "rmit-v2-2026-draft"
    assert edge["reason"]
    assert edge["provenance"] == "structural"
    assert edge["confidence"] == 1.0
    assert edge["source_clauses"] == []
    assert edge["target_clauses"] == []
