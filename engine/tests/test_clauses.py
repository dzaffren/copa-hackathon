"""Tests for engine.clauses — clause parser (anchor-slice) + ClauseIndex.

Covers spec Test Scenarios 1, 2, 4, 9 (docs/specs/rulebook-radar/
spec-knowledge-graph-engine.md) plus the loud-failure and collision
invariants called out in Task 2 of the implementation plan.

No network access: the LLM anchor-finding seam (`find_clause_anchors`) is
never called here — every test hand-writes its own anchor list and calls
`build_clause_index` directly.
"""

from engine.clauses import ClauseIndex, build_clause_index

OUTSOURCING_MARKDOWN = """Outsourcing

12 Approval for material outsourcing arrangements

12.1 A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement.

12.2 An application for approval under paragraph 12.1 must be submitted at least ninety days before the proposed commencement date.
"""


def test_verbatim_clause_fetch_returns_exact_text_and_echoes_clause_number():
    anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain the Bank's written approval",
            "heading": "12 Approval for material outsourcing arrangements",
            "parent": None,
        },
        {
            "clause_number": "12.2",
            "starts_with": "An application for approval under paragraph 12.1",
            "heading": "12 Approval for material outsourcing arrangements",
            "parent": None,
        },
    ]

    entries = build_clause_index(
        anchors=anchors,
        markdown=OUTSOURCING_MARKDOWN,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )
    index = ClauseIndex(entries)

    entry = index.get("Outsourcing 12.1")

    assert entry is not None
    assert entry["clause_number"] == "Outsourcing 12.1"
    assert entry["text"] == (
        "A financial institution must obtain the Bank's written approval "
        "before entering into a new material outsourcing arrangement."
    )
