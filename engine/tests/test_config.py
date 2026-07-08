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
