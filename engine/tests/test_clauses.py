"""Tests for engine.clauses — clause parser (anchor-slice) + ClauseIndex.

Covers spec Test Scenarios 1, 2, 4, 9 (docs/specs/rulebook-radar/
spec-knowledge-graph-engine.md) plus the loud-failure and collision
invariants called out in Task 2 of the implementation plan.

No network access: the LLM anchor-finding seam (`find_clause_anchors`) is
never called here — every test hand-writes its own anchor list and calls
`build_clause_index` directly.
"""

import pytest

from engine.clauses import (
    ClauseAnchorAmbiguousError,
    ClauseAnchorNotFoundError,
    ClauseCompletenessError,
    ClauseIndex,
    ClausePrimaryIndexCollisionError,
    ClauseVersionNotFoundError,
    build_clause_index,
    merge_clause_indexes,
)

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


def test_every_entry_text_is_a_verbatim_substring_of_the_source():
    entries, _ = _build_rmit_nested_index()

    for clause_number, entry in entries.items():
        assert (
            entry["text"] in RMIT_NESTED_MARKDOWN
        ), f"{clause_number}'s text is not a substring of the source"


def test_option_c_parent_stem_excludes_child_text_and_children_link_correctly():
    entries, index = _build_rmit_nested_index()

    parent = index.get("RMiT 17.1")
    child_a = index.get("RMiT 17.1(a)")
    child_b = index.get("RMiT 17.1(b)")
    child_c = index.get("RMiT 17.1(c)")

    assert parent["children"] == ["RMiT 17.1(a)", "RMiT 17.1(b)", "RMiT 17.1(c)"]
    assert child_a["parent"] == "RMiT 17.1"
    assert child_b["parent"] == "RMiT 17.1"
    assert child_c["parent"] == "RMiT 17.1"

    # Sub-item text is never duplicated inside the parent's stem-only text.
    assert child_b["text"] not in parent["text"]


def test_full_text_composes_stem_and_children_as_a_contiguous_source_span():
    entries, index = _build_rmit_nested_index()

    full_text = index.full_text("RMiT 17.1")
    stem = index.get("RMiT 17.1")["text"]

    assert full_text.startswith(stem)
    assert full_text in RMIT_NESTED_MARKDOWN


def test_anchor_not_found_raises_clear_exception_naming_the_clause():
    bad_anchors = [
        {
            "clause_number": "99.9",
            "starts_with": "This phrase does not appear anywhere in the source",
            "heading": None,
            "parent": None,
        }
    ]

    with pytest.raises(ClauseAnchorNotFoundError, match="99.9"):
        build_clause_index(
            anchors=bad_anchors,
            markdown=OUTSOURCING_MARKDOWN,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
        )


def test_ambiguous_anchor_raises_clear_exception_naming_the_clause():
    ambiguous_markdown = (
        "12.1 A financial institution must comply.\n\n"
        "12.2 A financial institution must comply.\n"
    )
    ambiguous_anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must comply",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "12.2",
            "starts_with": "A financial institution must comply",
            "heading": None,
            "parent": None,
        },
    ]

    with pytest.raises(ClauseAnchorAmbiguousError, match="12.1"):
        build_clause_index(
            anchors=ambiguous_anchors,
            markdown=ambiguous_markdown,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
        )


def test_completeness_check_raises_when_an_expected_clause_is_missing():
    anchors_missing_12_2 = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain the Bank's written approval",
            "heading": None,
            "parent": None,
        },
    ]

    with pytest.raises(ClauseCompletenessError, match="Outsourcing 12.2"):
        build_clause_index(
            anchors=anchors_missing_12_2,
            markdown=OUTSOURCING_MARKDOWN,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
            expected_clauses={"Outsourcing 12.1", "Outsourcing 12.2"},
        )


def test_missing_clause_returns_none_not_an_exception_or_fabricated_value():
    anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain the Bank's written approval",
            "heading": None,
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

    assert index.get("Outsourcing 99.9") is None


RMIT_V1_PUBLISHED_MARKDOWN = """Risk Management in Technology (RMiT)

17 Cloud services

17.1 A financial institution shall consult the Bank prior to the first-time adoption of a public cloud service for a critical system.

17.2 A financial institution shall consult the Bank on any subsequent adoption of a public cloud service for a critical system.
"""

RMIT_V1_ANCHORS = [
    {
        "clause_number": "17.1",
        "starts_with": "A financial institution shall consult the Bank prior to the first-time adoption",
        "heading": "17 Cloud services",
        "parent": None,
    },
    {
        "clause_number": "17.2",
        "starts_with": "A financial institution shall consult the Bank on any subsequent adoption",
        "heading": "17 Cloud services",
        "parent": None,
    },
]

RMIT_V2_DRAFT_MARKDOWN = """Risk Management in Technology (RMiT) — Exposure Draft v2

17 Cloud services

17.1 A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud service for a critical system, having first:
(a) completed the risk assessment under paragraph 10.50;
(b) a senior management and board readiness confirmation; and
(c) an independent third-party pre-implementation review.
"""

RMIT_V2_ANCHORS = [
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
]


def _build_rmit_versioned_index():
    v1_entries = build_clause_index(
        anchors=RMIT_V1_ANCHORS,
        markdown=RMIT_V1_PUBLISHED_MARKDOWN,
        document_id="rmit-v1-2020",
        policy_id="rmit",
        source="published",
    )
    v2_entries = build_clause_index(
        anchors=RMIT_V2_ANCHORS,
        markdown=RMIT_V2_DRAFT_MARKDOWN,
        document_id="rmit-v2-2026-draft",
        policy_id="rmit",
        source="draft",
    )
    primary, versions = merge_clause_indexes(
        [
            ("rmit-v1-2020", v1_entries),
            ("rmit-v2-2026-draft", v2_entries),
        ],
        current_document_id="rmit-v2-2026-draft",
    )
    return ClauseIndex(primary, versions)


def test_version_keying_current_draft_wins_and_superseded_reachable_by_version():
    index = _build_rmit_versioned_index()

    current = index.get("RMiT 17.1")
    assert current is not None
    assert current["source"] == "draft"
    assert current["document_id"] == "rmit-v2-2026-draft"
    assert "notify the Bank within 14 days" in current["text"]
    assert current["superseded_versions"] == ["rmit-v1-2020"]

    historical = index.get("RMiT 17.1", version="rmit-v1-2020")
    assert historical is not None
    assert historical["source"] == "published"
    assert "consult the Bank prior to" in historical["text"]


def test_version_keying_raises_distinctly_for_unknown_version_of_known_clause():
    index = _build_rmit_versioned_index()

    with pytest.raises(ClauseVersionNotFoundError, match="RMiT 17.1"):
        index.get("RMiT 17.1", version="rmit-v9-unknown")


def test_ambiguous_primary_collision_raises_rather_than_silently_picking_one():
    doc_a_markdown = "5.1 A financial institution must file an annual return.\n"
    doc_b_markdown = "5.1 A financial institution must file a quarterly return.\n"
    shared_anchor = [
        {
            "clause_number": "5.1",
            "starts_with": "A financial institution must file",
            "heading": None,
            "parent": None,
        },
    ]

    doc_a_entries = build_clause_index(
        anchors=shared_anchor,
        markdown=doc_a_markdown,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )
    doc_b_entries = build_clause_index(
        anchors=shared_anchor,
        markdown=doc_b_markdown,
        document_id="outsourcing-v0-hypothetical",
        policy_id="outsourcing",
        source="published",
    )

    with pytest.raises(ClausePrimaryIndexCollisionError, match="Outsourcing 5.1"):
        merge_clause_indexes(
            [
                ("outsourcing-v1-2019", doc_a_entries),
                ("outsourcing-v0-hypothetical", doc_b_entries),
            ],
            # Neither document is "current" -- an equal-precedence collision.
            current_document_id="outsourcing-v9-not-in-corpus",
        )
