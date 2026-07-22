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
from engine.config import DOCUMENTS


def test_every_document_declares_a_valid_doc_class():
    for document_id, doc in DOCUMENTS.items():
        assert "doc_class" in doc, f"{document_id} missing doc_class"
        assert doc["doc_class"] in DOC_CLASSES, (
            f"{document_id} has doc_class {doc['doc_class']!r} not in {DOC_CLASSES}")


def test_bnm_documents_are_structured_rules():
    # The nine BNM policy docs keep the deterministic offline lane.
    assert DOCUMENTS["rmit-v2-2025"]["doc_class"] == "structured-rules"
    assert DOCUMENTS["opres-v1-2025-draft"]["doc_class"] == "structured-rules"
