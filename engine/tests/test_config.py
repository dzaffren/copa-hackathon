"""Tests for engine.config — CURATED_SEED_EDGES shape invariant.

Covers Task 3's requirement that every curated seed edge carries a
non-empty reason and at least one clause anchor on each side (the shape
`engine.graph.build_graph` validates against the real ClauseIndex at build
time; this test only checks the static shape config.py ships, not that the
clause numbers resolve in the real corpus).
"""

from engine.config import CURATED_SEED_EDGES


def test_every_curated_seed_edge_has_reason_and_clause_anchors_on_both_sides():
    for edge in CURATED_SEED_EDGES:
        assert edge["reason"], f"edge {edge['source_policy_id']} -> {edge['target_policy_id']} has no reason"
        assert edge["source_clauses"], (
            f"edge {edge['source_policy_id']} -> {edge['target_policy_id']} "
            f"has no source_clauses"
        )
        assert edge["target_clauses"], (
            f"edge {edge['source_policy_id']} -> {edge['target_policy_id']} "
            f"has no target_clauses"
        )


from engine.anchors import DOC_CLASSES
from engine.config import DOCUMENTS, REFERENCE_DOCUMENTS


def test_every_document_declares_a_valid_segmenter_class():
    for document_id, doc in DOCUMENTS.items():
        assert "segmenter_class" in doc, f"{document_id} missing segmenter_class"
        assert doc["segmenter_class"] in DOC_CLASSES, (
            f"{document_id} has segmenter_class {doc['segmenter_class']!r} "
            f"not in {DOC_CLASSES}"
        )


def test_bnm_documents_are_structured_rules():
    # The nine BNM policy docs keep the deterministic offline lane.
    assert DOCUMENTS["rmit-v2-2025"]["segmenter_class"] == "structured-rules"
    assert DOCUMENTS["opres-v1-2025-draft"]["segmenter_class"] == "structured-rules"


def test_reference_documents_declare_segmenter_class():
    # The segmentation dispatch key is distinct from the graph's `doc_class`
    # field (GraphNode.doc_class, asserted separately by test_graph.py).
    assert REFERENCE_DOCUMENTS["eu-ai-act"]["segmenter_class"] == "legislative"
    assert REFERENCE_DOCUMENTS["pdpa-2010"]["segmenter_class"] == "legislative"
    assert REFERENCE_DOCUMENTS["nist-ai-rmf"]["segmenter_class"] == "framework"
    assert REFERENCE_DOCUMENTS["oecd-ai"]["segmenter_class"] == "framework"
    assert REFERENCE_DOCUMENTS["basel-por-2021"]["segmenter_class"] == "framework"
    assert REFERENCE_DOCUMENTS["mas-trm-2021"]["segmenter_class"] == "framework"
    assert REFERENCE_DOCUMENTS["bcbs-239"]["segmenter_class"] == "framework"


def test_reference_documents_graph_doc_class_untouched():
    # Tagging segmenter_class must not disturb the pre-existing graph
    # doc_class field (engine/graph.py::GraphNode.doc_class), which uses an
    # unrelated "technical"/"principle" vocabulary asserted by test_graph.py.
    assert REFERENCE_DOCUMENTS["bcbs-239"]["doc_class"] == "principle"
