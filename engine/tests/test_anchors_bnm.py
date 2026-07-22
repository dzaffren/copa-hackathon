from engine.anchors import verify_substring
from engine.anchors_bnm import structured_rules_segment

# Minimal BNM-shaped markdown: "10.1" then a sub-item.
BNM_MD = (
    "10 Governance\n\n"
    "10.1 A financial institution must establish a robust framework.\n\n"
    "(a) The board shall approve the framework.\n\n"
    "10.2 The board shall oversee the framework.\n"
)


def test_structured_rules_emits_anchors_with_clause_number_ids():
    anchors = structured_rules_segment(
        "rmit-v2-2025", BNM_MD, policy_id="rmit", source="rmit.pdf")
    ids = {a["anchor_id"] for a in anchors}
    assert "RMiT 10.1" in ids
    assert "RMiT 10.2" in ids
    for a in anchors:
        assert a["doc_class"] == "structured-rules"
        assert a["document_id"] == "rmit-v2-2025"
        verify_substring(a, BNM_MD)


def test_structured_rules_canonicalizes_parent_anchor():
    # segment_clauses already returns `parent` in canonical form (e.g. 'RMiT 10.1',
    # not bare '10.1' — see engine/clauses.py _assemble_entries / test_clauses.py:350).
    # structured_rules_segment passes it straight through as parent_anchor, so
    # parent_anchor matches the anchor_id convention. This test pins that: a child's
    # parent_anchor is the canonical 'RMiT 10.1', and a top-level clause's
    # parent_anchor is None.
    anchors = structured_rules_segment(
        "rmit-v2-2025", BNM_MD, policy_id="rmit", source="rmit.pdf")
    by_id = {a["anchor_id"]: a for a in anchors}

    child = by_id["RMiT 10.1(a)"]
    assert child["parent_anchor"] == "RMiT 10.1"
    assert not child["parent_anchor"].startswith("10.")

    top_level = by_id["RMiT 10.1"]
    assert top_level["parent_anchor"] is None
