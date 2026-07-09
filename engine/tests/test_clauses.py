"""Tests for engine.clauses — clause segmentation + ClauseIndex.

Covers spec Test Scenarios 1, 2, 4, 9 (docs/specs/rulebook-radar/
spec-knowledge-graph-engine.md) plus the loud-failure and collision
invariants called out in Task 2 of the implementation plan.

No network access and no model: stage 2 is the deterministic `segment_clauses`
(rule-primary). Lower-level tests hand-write anchor lists and call
`build_clause_index` directly (the phrase-anchor helper that shares the same
verbatim-slicing assembly).
"""

import pytest

from engine.clauses import (
    ClauseCompletenessError,
    ClauseIndex,
    ClausePrimaryIndexCollisionError,
    ClauseVersionNotFoundError,
    build_clause_index,
    merge_clause_indexes,
    segment_clauses,
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


# BNM clauses are each preceded by a lone "S" (Standard) or "G" (Guidance)
# marker line. Without trimming, the next clause's marker + number leak onto the
# tail of the current clause's text (e.g. "...arrangement.\n\nS\n\n12.2").
SG_MARKER_MARKDOWN = (
    "12 Approval\n\n"
    "S\n\n"
    "12.1  A financial institution must obtain approval before making a\n"
    "material outsourcing arrangement.\n\n"
    "S\n\n"
    "12.2  An application must be submitted ninety days in advance.\n\n"
    "G\n\n"
    "12.3  The Bank may request further information.\n"
)


def test_trailing_standard_guidance_marker_is_trimmed():
    anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain approval",
            "heading": "12 Approval",
            "parent": None,
        },
        {
            "clause_number": "12.2",
            "starts_with": "An application must be submitted",
            "heading": "12 Approval",
            "parent": None,
        },
        {
            "clause_number": "12.3",
            "starts_with": "The Bank may request further information",
            "heading": "12 Approval",
            "parent": None,
        },
    ]

    entries = build_clause_index(
        anchors=anchors,
        markdown=SG_MARKER_MARKDOWN,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )

    # No clause text carries the next clause's S/G marker or number.
    for cn in ("Outsourcing 12.1", "Outsourcing 12.2"):
        text = entries[cn]["text"]
        assert not text.rstrip().endswith(("S", "G")), text
        assert "12.2" not in text and "12.3" not in text, text
    # 12.1 ends cleanly at its own content.
    assert entries["Outsourcing 12.1"]["text"].endswith("outsourcing arrangement.")


def test_composed_full_text_also_trims_trailing_marker():
    # The parent's composed full_text (stem + children) must end as cleanly as
    # each child's own text — no trailing S/G marker or next-clause number.
    anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain approval",
            "heading": "12 Approval",
            "parent": None,
        },
        {
            "clause_number": "12.1(a)",
            "starts_with": "the first condition",
            "heading": "12 Approval",
            "parent": "12.1",
        },
        {
            "clause_number": "12.2",
            "starts_with": "An application must be submitted",
            "heading": "12 Approval",
            "parent": None,
        },
    ]
    markdown = (
        "S\n\n"
        "12.1  A financial institution must obtain approval subject to:\n"
        "(a)  the first condition being met.\n\n"
        "S\n\n"
        "12.2  An application must be submitted ninety days in advance.\n"
    )

    entries = build_clause_index(
        anchors=anchors,
        markdown=markdown,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )

    full = entries["Outsourcing 12.1"]["_full_text"]
    assert "12.2" not in full, full
    assert not full.rstrip().endswith(("S", "G")), full


# Real MarkItDown output of BNM PDFs contains runs of doubled spaces and
# mid-sentence newlines (a layout artifact). The parser LLM normalises those to
# single spaces when it quotes `starts_with`, so an exact match would miss.
DOUBLE_SPACED_MARKDOWN = (
    "6\n\n"
    "6.1\n\n"
    "This  policy  document  must  be  read  together  with  other  relevant\n"
    "legal  instruments.\n\n"
    "6.2\n\n"
    "The  Bank  may  issue  further  guidance.\n"
)


def test_anchor_located_despite_normalised_whitespace_text_stays_verbatim():
    # `starts_with` is single-spaced (as the model quotes it); the source is
    # double-spaced. The anchor must still be located, and the stored text must
    # preserve the source's original spacing (verbatim by slicing).
    anchors = [
        {
            "clause_number": "6.1",
            "starts_with": "This policy document must be read together",
            "heading": "6 Interpretation",
            "parent": None,
        },
        {
            "clause_number": "6.2",
            "starts_with": "The Bank may issue further guidance",
            "heading": "6 Interpretation",
            "parent": None,
        },
    ]

    entries = build_clause_index(
        anchors=anchors,
        markdown=DOUBLE_SPACED_MARKDOWN,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )
    index = ClauseIndex(entries)

    entry = index.get("Outsourcing 6.1")
    assert entry is not None
    # Verbatim: the stored text keeps the source's double spaces, not the
    # single-spaced form the model quoted.
    assert "This  policy  document  must  be  read  together" in entry["text"]
    assert entry["text"] in DOUBLE_SPACED_MARKDOWN


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


def test_anchor_not_found_is_skipped_with_warning(caplog):
    # A phrase absent from the source (paraphrased / from a garbled region) is
    # dropped with a loud warning rather than crashing the whole build.
    import logging

    anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain the Bank's written approval",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "99.9",
            "starts_with": "This phrase does not appear anywhere in the source",
            "heading": None,
            "parent": None,
        },
    ]

    with caplog.at_level(logging.WARNING):
        entries = build_clause_index(
            anchors=anchors,
            markdown=OUTSOURCING_MARKDOWN,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
        )

    # 99.9 dropped; the real 12.1 still built.
    assert "Outsourcing 99.9" not in entries
    assert "Outsourcing 12.1" in entries
    assert any("99.9" in rec.message for rec in caplog.records)


def test_dropped_report_captures_dropped_clause_for_human_review():
    # "Flag for human review": when a dropped_report list is supplied, every
    # dropped anchor is appended as a structured {document_id, clause_number,
    # reason, ...} record — a reviewable artifact, not just a log line. The
    # supported clause is NOT reported (only genuine drops are).
    anchors = [
        {
            "clause_number": "12.1",
            "starts_with": "A financial institution must obtain the Bank's written approval",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "99.9",
            "starts_with": "This phrase does not appear anywhere in the source",
            "heading": "9 Nonexistent",
            "parent": None,
        },
    ]
    dropped_report: list[dict] = []

    entries = build_clause_index(
        anchors=anchors,
        markdown=OUTSOURCING_MARKDOWN,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
        dropped_report=dropped_report,
    )

    assert "Outsourcing 12.1" in entries  # supported clause still built
    assert len(dropped_report) == 1
    record = dropped_report[0]
    assert record["document_id"] == "outsourcing-v1-2019"
    assert record["clause_number"] == "99.9"  # bare number as emitted by the LLM
    assert record["reason"] == "not_found"
    assert record["heading"] == "9 Nonexistent"


def test_orphaned_child_parent_missing_is_promoted_not_crashed():
    # A child clause whose declared parent was never emitted (a bare section
    # heading, or a parent whose own anchor was dropped) must NOT crash the
    # build. The child is promoted to top-level (parent -> None) and flagged for
    # review — the "flag for human, don't crash" principle.
    markdown = (
        "10.1  The first requirement under section ten applies to all firms.\n\n"
        "10.2  The second requirement under section ten applies as well.\n"
    )
    anchors = [
        # Both children point at parent "10", which is never emitted as a clause.
        {
            "clause_number": "10.1",
            "starts_with": "The first requirement under section ten",
            "heading": "10 Section Ten",
            "parent": "10",
        },
        {
            "clause_number": "10.2",
            "starts_with": "The second requirement under section ten",
            "heading": "10 Section Ten",
            "parent": "10",
        },
    ]
    dropped_report: list[dict] = []

    entries = build_clause_index(
        anchors=anchors,
        markdown=markdown,
        document_id="rmit-v1-2020",
        policy_id="rmit",
        source="published",
        dropped_report=dropped_report,
    )

    # Both children built and were promoted to top-level (no KeyError).
    assert entries["RMiT 10.1"]["parent"] is None
    assert entries["RMiT 10.2"]["parent"] is None
    assert "RMiT 10" not in entries  # the phantom parent was never invented
    # Both flagged for review with the orphaned-parent reason.
    assert len(dropped_report) == 2
    assert all(r["reason"] == "orphaned_parent:RMiT 10" for r in dropped_report)


def test_dropped_report_none_keeps_warn_only_default(caplog):
    # Passing no dropped_report (the default) must not change behaviour — the
    # clause is still dropped and warned, nothing raised.
    import logging

    anchors = [
        {
            "clause_number": "99.9",
            "starts_with": "This phrase does not appear anywhere in the source",
            "heading": None,
            "parent": None,
        },
    ]
    with caplog.at_level(logging.WARNING):
        entries = build_clause_index(
            anchors=anchors,
            markdown=OUTSOURCING_MARKDOWN,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
        )
    assert "Outsourcing 99.9" not in entries
    assert any("99.9" in rec.message for rec in caplog.records)


def test_ambiguous_anchor_is_skipped_with_warning(caplog):
    # The phrase recurs AND the clause's own label ("8.4") precedes neither
    # occurrence — label disambiguation can't single one out, so the anchor is
    # dropped with a warning rather than crashing.
    import logging

    ambiguous_markdown = (
        "8.4  A financial institution must, including a repeated phrase, act.\n\n"
        "9.1  See also a repeated phrase in a different clause entirely.\n"
    )
    ambiguous_anchors = [
        {
            "clause_number": "8.4",
            "starts_with": "a repeated phrase",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "9.1",
            "starts_with": "See also",
            "heading": None,
            "parent": None,
        },
    ]

    with caplog.at_level(logging.WARNING):
        entries = build_clause_index(
            anchors=ambiguous_anchors,
            markdown=ambiguous_markdown,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
        )

    # 8.4 (ambiguous) dropped with a warning; 9.1 still built.
    assert "Outsourcing 8.4" not in entries
    assert "Outsourcing 9.1" in entries
    assert any("8.4" in rec.message and "ambiguous" in rec.message.lower()
               for rec in caplog.records)


def test_empty_starts_with_anchor_is_skipped_not_fatal(caplog):
    # 8.2 has no quotable text (PDF layout lost its body); its anchor has an
    # empty starts_with. It is skipped with a warning; the other clauses build.
    markdown = (
        "8.1  Financial institutions shall have strong oversight.\n\n"
        "8.4  The board and senior management shall be accountable.\n"
    )
    anchors = [
        {
            "clause_number": "8.1",
            "starts_with": "Financial institutions shall have strong oversight",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "8.2",
            "starts_with": "",  # body lost in conversion
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "8.4",
            "starts_with": "The board and senior management shall be accountable",
            "heading": None,
            "parent": None,
        },
    ]

    import logging

    with caplog.at_level(logging.WARNING):
        entries = build_clause_index(
            anchors=anchors,
            markdown=markdown,
            document_id="outsourcing-v1-2019",
            policy_id="outsourcing",
            source="published",
        )

    # 8.2 dropped; 8.1 and 8.4 present.
    assert "Outsourcing 8.2" not in entries
    assert "Outsourcing 8.1" in entries
    assert "Outsourcing 8.4" in entries
    # The drop was logged loudly, naming the clause.
    assert any("8.2" in rec.message for rec in caplog.records)


def test_recurring_phrase_disambiguated_by_clause_label():
    # The same phrase appears twice: once mid-sentence inside clause 8.3, and
    # once as the real 8.4(c) start (preceded by its "(c)" label). The label
    # disambiguates → 8.4(c) resolves to the correct, label-preceded span.
    markdown = (
        "8.3  The institution must retain oversight resources, including where "
        "the outsourced activity is undertaken by an affiliate of the group; and\n\n"
        "8.4  The institution must ensure that:\n"
        "(c)  where the outsourced activity is undertaken by an affiliate, it "
        "retains effective control.\n"
    )
    anchors = [
        {
            "clause_number": "8.3",
            "starts_with": "The institution must retain oversight resources",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "8.4",
            "starts_with": "The institution must ensure that",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "8.4(c)",
            "starts_with": "where the outsourced activity is undertaken by an affiliate",
            "heading": None,
            "parent": "8.4",
        },
    ]

    entries = build_clause_index(
        anchors=anchors,
        markdown=markdown,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )

    entry = entries["Outsourcing 8.4(c)"]
    # Resolved to the real (c) clause, not the mid-sentence repeat in 8.3.
    assert entry["text"].startswith("where the outsourced activity is undertaken")
    assert "retains effective control" in entry["text"]


def test_multi_level_nested_clause_disambiguated_by_deepest_label():
    # A phrase appears under 9.6(b) and again under the deeper 9.6(c)(i). The
    # in-text label for 9.6(c)(i) is its DEEPEST group "(i)", not "(c)(i)" — so
    # disambiguation must match "(i)" to resolve the triple-nested clause.
    markdown = (
        "9.6  The agreement must address:\n"
        "(b)  responsibilities of the service provider, with defined roles; and\n"
        "(c)  conflict of interest issues, including:\n"
        "(i)  responsibilities of the service provider with respect to disclosure.\n"
    )
    anchors = [
        {
            "clause_number": "9.6",
            "starts_with": "The agreement must address",
            "heading": None,
            "parent": None,
        },
        {
            "clause_number": "9.6(b)",
            "starts_with": "responsibilities of the service provider, with defined roles",
            "heading": None,
            "parent": "9.6",
        },
        {
            "clause_number": "9.6(c)",
            "starts_with": "conflict of interest issues, including",
            "heading": None,
            "parent": "9.6",
        },
        {
            "clause_number": "9.6(c)(i)",
            "starts_with": "responsibilities of the service provider with respect to disclosure",
            "heading": None,
            "parent": "9.6(c)",
        },
    ]

    entries = build_clause_index(
        anchors=anchors,
        markdown=markdown,
        document_id="outsourcing-v1-2019",
        policy_id="outsourcing",
        source="published",
    )

    entry = entries["Outsourcing 9.6(c)(i)"]
    assert entry["text"].startswith(
        "responsibilities of the service provider with respect to disclosure"
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


def test_entries_for_document_returns_that_documents_clauses_in_order():
    rmit_entries = build_clause_index(
        anchors=RMIT_NESTED_ANCHORS,
        markdown=RMIT_NESTED_MARKDOWN,
        document_id="rmit-v2-2026-draft",
        policy_id="rmit",
        source="draft",
    )
    outsourcing_entries = build_clause_index(
        anchors=[
            {
                "clause_number": "12.1",
                "starts_with": "A financial institution must obtain the Bank's written approval",
                "heading": "12 Approval for material outsourcing arrangements",
                "parent": None,
            },
        ],
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
    index = ClauseIndex(primary, versions)

    rmit = index.entries_for_document("rmit-v2-2026-draft")

    # Only that document's clauses, in insertion (document) order.
    assert [e["clause_number"] for e in rmit] == [
        "RMiT 10.5",
        "RMiT 10.50",
        "RMiT 17.1",
        "RMiT 17.1(a)",
        "RMiT 17.1(b)",
        "RMiT 17.1(c)",
        "RMiT 12.3",
        "RMiT 12.3(e)",
        "RMiT Appendix 10",
    ]
    assert all(e["document_id"] == "rmit-v2-2026-draft" for e in rmit)

    outsourcing = index.entries_for_document("outsourcing-v1-2019")
    assert [e["clause_number"] for e in outsourcing] == ["Outsourcing 12.1"]

    assert index.entries_for_document("no-such-document") == []


# ---------------------------------------------------------------------------
# Deterministic clause segmentation (`segment_clauses`) — the rule-primary
# stage-2 that supersedes the LLM anchor parser. These exercise the real BNM
# line-start grammar; all network-free.

# A compact document in real BNM format: a table of contents (which must be
# skipped), PART dividers, section headings, numbered clauses, sub-items,
# a deep decimal (10.50, distinct from 10.5), a footnote (out-of-sequence bare
# number, must NOT become a heading), and an appendix.
_BNM_DOC = """Risk Management in Technology

TABLE OF CONTENTS

PART A OVERVIEW

1 Introduction
2 Cloud services

PART A

OVERVIEW

1 Introduction

1.1 A financial institution must manage technology risk, and must-
(a) invest in controls; and
(b) maintain oversight.

1.2 This paragraph refers to footnote 44 for detail.

44 This is an explanatory footnote, not a clause heading.

2 Cloud services

2.1 A financial institution shall consult the Bank before adopting cloud.

10.50 A financial institution must fully understand cloud risk.

Appendix 1

The appendix provides supplementary guidance.
"""


def test_segment_clauses_basic_grammar_and_hierarchy():
    entries = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    index = ClauseIndex(entries)

    # Numbered clauses, sub-items, deep decimal and appendix all present.
    for number in [
        "RMiT 1.1",
        "RMiT 1.1(a)",
        "RMiT 1.1(b)",
        "RMiT 1.2",
        "RMiT 2.1",
        "RMiT 10.50",
        "RMiT Appendix 1",
    ]:
        assert index.get(number) is not None, f"{number} missing"

    # Sub-items attach structurally to their parent.
    assert index.get("RMiT 1.1(a)")["parent"] == "RMiT 1.1"
    assert index.get("RMiT 1.1")["children"] == ["RMiT 1.1(a)", "RMiT 1.1(b)"]
    # Top-level clause has no parent.
    assert index.get("RMiT 2.1")["parent"] is None
    # Heading assigned from the enclosing section.
    assert index.get("RMiT 2.1")["heading"] == "2 Cloud services"


def test_segment_clauses_text_is_verbatim_substring_of_source():
    entries = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    # The core guarantee: every stored text is a byte-for-byte slice of the
    # ORIGINAL markdown (never a mutated/stripped copy).
    for entry in entries.values():
        assert entry["text"] in _BNM_DOC


def test_segment_clauses_deep_decimal_not_confused_with_shallow():
    entries = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    # 10.50 is its own clause; there is no phantom "10.5".
    assert "RMiT 10.50" in entries
    assert "RMiT 10.5" not in entries


def test_segment_clauses_skips_table_of_contents_and_footnote():
    entries = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    # The TOC lists "1 Introduction"/"2 Cloud services" before the body; the
    # body's real "1 Introduction" restarts the section counter, so 2.1 is
    # found (would be missed if the TOC had run the counter past 2).
    assert index_has(entries, "RMiT 2.1")
    # The footnote "44 ..." is out of sequence → not a heading, not a clause.
    assert "RMiT 44" not in entries
    # 1.2's text must not swallow the footnote line as a heading boundary bug;
    # it stays verbatim and stops at its own content.
    assert "explanatory footnote" not in entries["RMiT 1.2"]["text"]


def index_has(entries, number):
    return number in entries


def test_segment_clauses_heading_does_not_bleed_into_previous_clause():
    entries = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    # 1.2 is the last clause under section 1; the "2 Cloud services" heading
    # (and the PART divider) must not bleed into its text.
    text = entries["RMiT 1.2"]["text"]
    assert "Cloud services" not in text
    assert "PART" not in text


def test_segment_clauses_is_deterministic():
    a = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    b = segment_clauses(_BNM_DOC, "rmit-v1", "rmit", "published")
    # Same bytes in -> identical entries out (freeze-as-fixtures relies on this).
    assert list(a.keys()) == list(b.keys())
    assert all(a[k]["text"] == b[k]["text"] for k in a)
