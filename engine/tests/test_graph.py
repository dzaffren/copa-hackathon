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
    "rmit-vnext-draft": {
        "policy_id": "rmit",
        "document_id": "rmit-vnext-draft",
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
        document_id="rmit-vnext-draft",
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
            ("rmit-vnext-draft", rmit_v2_entries),
            ("opres-v1-2025", opres_entries),
            ("bcm-v1-2022", bcm_entries),
        ],
        current_document_id="rmit-vnext-draft",
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

    assert edge["source"] == "rmit-vnext-draft"
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


def test_llm_found_edge_is_included_and_may_carry_confidence_below_one():
    clause_index = _build_fixture_clause_index()
    llm_found_edges = [
        {
            "source": "rmit-vnext-draft",
            "target": "opres-v1-2025",
            "type": "depends-on",
            "reason": "RMiT 17.1 depends on the OpRes register staying in sync.",
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["Operational Resilience 6.11"],
            "provenance": "llm-found",
            "confidence": 0.82,
        },
    ]

    graph = build_graph(
        documents=DOCUMENTS,
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
        llm_found_edges=llm_found_edges,
    )

    llm_edges = [e for e in graph["edges"] if e["provenance"] == "llm-found"]
    assert len(llm_edges) == 1
    assert llm_edges[0]["confidence"] == 0.82


def test_curated_edge_with_confidence_not_one_raises_graph_build_error():
    clause_index = _build_fixture_clause_index()
    bad_edges = [
        {
            "source_policy_id": "rmit",
            "target_policy_id": "opres",
            "type": "overlaps",
            "reason": "Both govern the cloud register.",
            "source_clauses": ["RMiT 10.50"],
            "target_clauses": ["Operational Resilience 6.11"],
            "provenance": "curated",
            "confidence": 0.9,
        },
    ]

    with pytest.raises(GraphBuildError, match="confidence"):
        build_graph(
            documents=DOCUMENTS,
            curated_edges=bad_edges,
            clause_index=clause_index,
            draft_registry=DRAFT_REGISTRY,
        )


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

    assert _node(graph, "rmit-vnext-draft")["status"] == "In progress"
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
    assert edge["target"] == "rmit-vnext-draft"
    assert edge["reason"]
    assert edge["provenance"] == "structural"
    assert edge["confidence"] == 1.0
    assert edge["source_clauses"] == []
    assert edge["target_clauses"] == []


# --- External reference nodes/edges (#26 Reference Radar) -------------------

PDPA_PASSAGE = (
    "A data controller may transfer any personal data of a data subject to any "
    "place outside Malaysia if— (a) there is in that place in force any law which "
    "is substantially similar to this Act; or (b) that place ensures an adequate "
    "level of protection..."
)

REFERENCE_DOCUMENTS = {
    "pdpa-2010": {
        "policy_id": "pdpa",
        "document_id": "pdpa-2010",
        "title": "Personal Data Protection Act 2010 (Malaysia)",
        "version": "2010 · Act 709",
        "cluster": "technology-risk",
        "kind": "reference",
        "source_type": "act",
        "access": "public",
        "preview": False,
        "source_url": "https://example.test/pdpa",
    },
    "bnm-handbook": {
        "policy_id": "bnm-handbook",
        "document_id": "bnm-handbook",
        "title": "Regulatory Handbook (BNM)",
        "version": "internal",
        "cluster": "technology-risk",
        "kind": "reference",
        "source_type": "handbook",
        "access": "restricted",
        "preview": False,
    },
    "trend-cloud-signals": {
        "policy_id": "trend-cloud-signals",
        "document_id": "trend-cloud-signals",
        "title": "Trends · News · foreign policies",
        "version": "preview",
        "cluster": "technology-risk",
        "kind": "reference",
        "source_type": "trend",
        "access": "public",
        "preview": True,
    },
}

REFERENCE_EDGES = [
    {
        "source_policy_id": "rmit",
        "target_policy_id": "pdpa",
        "type": "references",
        "reason": "A cloud region outside Malaysia engages the PDPA transfer test.",
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["PDPA 129"],
        "provenance": "llm-found",
        "confidence": 0.9,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "bnm-handbook",
        "type": "references",
        "reason": "The handbook connects to this clause; content confidential.",
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["BNM Handbook — Cloud & Outsourcing Manual"],
        "provenance": "curated",
        "confidence": 1.0,
    },
    {
        "source_policy_id": "rmit",
        "target_policy_id": "trend-cloud-signals",
        "type": "references",
        "reason": "In-country cloud regions and EU DORA — a preview, not committed.",
        "source_clauses": ["RMiT 17.1"],
        "target_clauses": ["Trend — in-country cloud regions"],
        "provenance": "curated",
        "confidence": 1.0,
    },
]


def _clause_index_with_pdpa_reference() -> ClauseIndex:
    """Fixture index: the RMiT v2 clauses (so `RMiT 17.1` resolves as the edge
    source) plus the single PDPA public reference passage (`PDPA 129`)."""
    from engine.clauses import build_reference_clause, merge_clause_indexes

    rmit_v2 = build_clause_index(
        anchors=RMIT_V2_ANCHORS,
        markdown=RMIT_V2_MARKDOWN,
        document_id="rmit-vnext-draft",
        policy_id="rmit",
        source="draft",
    )
    primary, versions = merge_clause_indexes(
        [("rmit-vnext-draft", rmit_v2)],
        current_document_id="rmit-vnext-draft",
    )
    for clause_number, entry in build_reference_clause(
        "pdpa-2010", "pdpa", "129", "Section 129(2)", PDPA_PASSAGE
    ).items():
        primary[clause_number] = entry
        versions.setdefault(clause_number, {})[entry["document_id"]] = entry
    return ClauseIndex(primary, versions)


def test_reference_nodes_carry_kind_source_type_access_preview():
    clause_index = _clause_index_with_pdpa_reference()

    graph = build_graph(
        documents={**DOCUMENTS, **REFERENCE_DOCUMENTS},
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
        reference_edges=REFERENCE_EDGES,
    )

    pdpa = _node(graph, "pdpa-2010")
    assert pdpa["kind"] == "reference"
    assert pdpa["source_type"] == "act"
    assert pdpa["access"] == "public"
    assert pdpa["preview"] is False
    assert pdpa["source_url"] == "https://example.test/pdpa"

    # Policy nodes default to kind "policy" (backward compatible).
    assert _node(graph, "rmit-vnext-draft")["kind"] == "policy"

    # The restricted handbook carries no source_url; the trend node is preview.
    handbook = _node(graph, "bnm-handbook")
    assert handbook["access"] == "restricted"
    assert "source_url" not in handbook
    assert _node(graph, "trend-cloud-signals")["preview"] is True


def test_reference_nodes_carry_structural_metadata():
    """Structural-metadata fields surface on a source node when the manifest
    declares them, and stay absent on a source that does not (they are optional)."""
    clause_index = _clause_index_with_pdpa_reference()

    reference_documents = {
        "bcbs-239": {
            "policy_id": "bcbs-239",
            "document_id": "bcbs-239",
            "title": "BCBS 239 — Principles for effective risk data aggregation",
            "version": "2013",
            "cluster": "ai-financial-sector",
            "kind": "reference",
            "source_type": "international_standard",
            "access": "public",
            "preview": False,
            "mother_document": "Basel Committee on Banking Supervision",
            "precedence": "international standard",
            "legislated": False,
            "standard_setting_party": "Basel Committee on Banking Supervision",
            "doc_class": "principle",
        },
        # A source with no structural metadata declared (control).
        "trend-cloud-signals": REFERENCE_DOCUMENTS["trend-cloud-signals"],
    }

    graph = build_graph(
        documents={**DOCUMENTS, **reference_documents},
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
        reference_edges=[],
    )

    bcbs = _node(graph, "bcbs-239")
    assert bcbs["source_type"] == "international_standard"
    assert bcbs["mother_document"] == "Basel Committee on Banking Supervision"
    assert bcbs["precedence"] == "international standard"
    assert bcbs["legislated"] is False
    assert bcbs["standard_setting_party"] == (
        "Basel Committee on Banking Supervision"
    )
    assert bcbs["doc_class"] == "principle"

    # A source that declares no structural metadata does not gain the fields.
    trend = _node(graph, "trend-cloud-signals")
    assert "precedence" not in trend
    assert "doc_class" not in trend


def test_industry_feedback_nodes_carry_source_type_and_stance():
    """An industry_feedback source node carries the widened source_type and the
    sector's stance; a non-feedback node carries no stance."""
    clause_index = _clause_index_with_pdpa_reference()

    reference_documents = {
        "industry-fsp-3": {
            "policy_id": "industry-fsp-3",
            "document_id": "industry-fsp-3",
            "title": "Industry feedback — 3 FSP respondents",
            "version": "consultation response",
            "cluster": "ai-financial-sector",
            "kind": "reference",
            "source_type": "industry_feedback",
            "access": "public",
            "preview": False,
            "stance": "partial",
        },
    }

    graph = build_graph(
        documents={**DOCUMENTS, **reference_documents},
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
        reference_edges=[],
    )

    fsp = _node(graph, "industry-fsp-3")
    assert fsp["kind"] == "reference"
    assert fsp["source_type"] == "industry_feedback"
    assert fsp["stance"] == "partial"

    # A policy node (not a reference) never carries a stance.
    assert "stance" not in _node(graph, "rmit-vnext-draft")


def test_reference_edges_build_with_restricted_and_preview_carveout():
    clause_index = _clause_index_with_pdpa_reference()

    graph = build_graph(
        documents={**DOCUMENTS, **REFERENCE_DOCUMENTS},
        curated_edges=[],
        clause_index=clause_index,
        draft_registry=DRAFT_REGISTRY,
        reference_edges=REFERENCE_EDGES,
    )

    ref_edges = [e for e in graph["edges"] if e["type"] == "references"]
    assert {e["target"] for e in ref_edges} == {
        "pdpa-2010",
        "bnm-handbook",
        "trend-cloud-signals",
    }
    assert all(e["source"] == "rmit-vnext-draft" for e in ref_edges)

    by_target = {e["target"]: e for e in ref_edges}
    assert by_target["pdpa-2010"]["provenance"] == "llm-found"
    assert by_target["pdpa-2010"]["confidence"] == 0.9
    assert by_target["bnm-handbook"]["provenance"] == "curated"
    # The carve-out let the handbook/trend edges build even though their target
    # labels never resolve in the index (their passages are never ingested).
    assert clause_index.get("BNM Handbook — Cloud & Outsourcing Manual") is None
    assert clause_index.get("Trend — in-country cloud regions") is None


def test_public_reference_edge_with_unresolved_passage_raises():
    clause_index = _clause_index_with_pdpa_reference()
    bad_edges = [
        {
            "source_policy_id": "rmit",
            "target_policy_id": "pdpa",
            "type": "references",
            "reason": "Cites a PDPA passage that is not in the index.",
            "source_clauses": ["RMiT 17.1"],
            "target_clauses": ["PDPA 999"],
            "provenance": "llm-found",
            "confidence": 0.9,
        },
    ]

    with pytest.raises(GraphBuildError, match="PDPA 999"):
        build_graph(
            documents={**DOCUMENTS, **REFERENCE_DOCUMENTS},
            curated_edges=[],
            clause_index=clause_index,
            draft_registry=DRAFT_REGISTRY,
            reference_edges=bad_edges,
        )
