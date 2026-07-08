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


RMIT_NESTED_MARKDOWN = """RMiT

10 Technology Operations Management

10.5 A financial institution must maintain a technology asset register.

10.50 A financial institution must fully understand the inherent risk of adopting cloud services.

17 Cloud services

17.1 A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud service for a critical system, having first:
(a) completed the risk assessment under paragraph 10.50;
(b) a senior management and board readiness confirmation; and
(c) an independent third-party pre-implementation review.

12.3 Every material outsourcing arrangement must be reviewed periodically, including-
(e) an assessment of the service provider's ongoing financial soundness.

Appendix 10 Illustrative risk assessment checklist for cloud adoption.
"""

RMIT_NESTED_ANCHORS = [
    {
        "clause_number": "10.5",
        "starts_with": "A financial institution must maintain a technology asset register",
        "heading": "10 Technology Operations Management",
        "parent": None,
    },
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
        "clause_number": "17.1(a)",
        "starts_with": "completed the risk assessment under paragraph 10.50",
        "heading": "17 Cloud services",
        "parent": "17.1",
    },
    {
        "clause_number": "17.1(b)",
        "starts_with": "a senior management and board readiness confirmation",
        "heading": "17 Cloud services",
        "parent": "17.1",
    },
    {
        "clause_number": "17.1(c)",
        "starts_with": "an independent third-party pre-implementation review",
        "heading": "17 Cloud services",
        "parent": "17.1",
    },
    {
        "clause_number": "12.3",
        "starts_with": "Every material outsourcing arrangement must be reviewed periodically",
        "heading": "12 Outsourcing review",
        "parent": None,
    },
    {
        "clause_number": "12.3(e)",
        "starts_with": "an assessment of the service provider's ongoing financial soundness",
        "heading": "12 Outsourcing review",
        "parent": "12.3",
    },
    {
        "clause_number": "Appendix 10",
        "starts_with": "Illustrative risk assessment checklist for cloud adoption",
        "heading": "Appendix 10",
        "parent": None,
    },
]


def _build_rmit_nested_index():
    entries = build_clause_index(
        anchors=RMIT_NESTED_ANCHORS,
        markdown=RMIT_NESTED_MARKDOWN,
        document_id="rmit-v2-2026-draft",
        policy_id="rmit",
        source="draft",
    )
    return entries, ClauseIndex(entries)


def test_nested_numbering_boundaries_do_not_bleed_between_sibling_clauses():
    entries, index = _build_rmit_nested_index()

    clause_17_1 = index.get("RMiT 17.1")
    clause_17_1a = index.get("RMiT 17.1(a)")
    clause_17_1b = index.get("RMiT 17.1(b)")
    clause_10_5 = index.get("RMiT 10.5")
    clause_10_50 = index.get("RMiT 10.50")
    appendix_10 = index.get("RMiT Appendix 10")

    # 17.1's stem does not bleed into 17.1(a).
    assert "completed the risk assessment" not in clause_17_1["text"]
    # 17.1(a) and 17.1(b) are distinct.
    assert clause_17_1a["text"] != clause_17_1b["text"]
    assert "completed the risk assessment" in clause_17_1a["text"]
    assert "senior management and board readiness" in clause_17_1b["text"]
    # 10.50 is not confused with 10.5.
    assert clause_10_5["text"] != clause_10_50["text"]
    assert "technology asset register" in clause_10_5["text"]
    assert "inherent risk of adopting cloud services" in clause_10_50["text"]
    # Appendix 10 is addressable.
    assert appendix_10 is not None
    assert "Illustrative risk assessment checklist" in appendix_10["text"]
