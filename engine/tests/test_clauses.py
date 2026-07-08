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
    ClauseCompletenessError,
    ClauseIndex,
    ClausePrimaryIndexCollisionError,
    ClauseVersionNotFoundError,
    _CLAUSE_START_RE,
    _parse_anchor_response,
    _split_chunks,
    _strip_noise,
    build_clause_index,
    find_clause_anchors,
    merge_clause_indexes,
)
from engine.llm import LLMResponseError

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


# ---------------------------------------------------------------------------
# Stage-2 parser (find_clause_anchors) — split + parse + merge wiring.
#
# No network: `_strip_noise`, `_split_chunks` and `_parse_anchor_response` are
# pure, and the `find_clause_anchors` orchestration test monkeypatches
# `call_chat` with a fake returning canned per-chunk JSON.
# ---------------------------------------------------------------------------

# Mimics real MarkItDown output of a BNM PDF: a table of contents with dotted
# leaders, repeated "Issued on:" running headers, "N of M" page footers, a
# form-feed page break (\x0c), and lone "PART X" dividers — all noise — around
# the genuine numbered clauses.
MARKITDOWN_STYLE_MARKDOWN = (
    "Outsourcing\n\n"
    "PART A  OVERVIEW ...................................... 2\n"
    "Interpretation ....................................... 3\n"
    "PART C  REGULATORY PROCESS ........................... 12\n\n"
    "Issued on: 23 October 2019\n\n"
    "\x0c"
    "PART C  REGULATORY PROCESS\n\n"
    "12\n\n"
    "Approval for material outsourcing arrangements\n\n"
    "12.1 A financial institution must obtain the Bank's written approval.\n\n"
    "Issued on: 23 October 2019\n\n"
    "3 of 20\n\n"
    "17 Cloud services\n\n"
    "17.1 A financial institution shall notify the Bank within 14 days.\n"
)


def test_strip_noise_removes_toc_headers_footers_and_page_breaks():
    cleaned = _strip_noise(MARKITDOWN_STYLE_MARKDOWN)

    # Table-of-contents dotted-leader lines are gone.
    assert "......" not in cleaned
    assert "PART A  OVERVIEW" not in cleaned
    # Running header and page-number footer are gone.
    assert "Issued on:" not in cleaned
    assert "3 of 20" not in cleaned
    # Lone "PART X" divider is gone; form-feed is normalised away.
    assert "PART C  REGULATORY PROCESS" not in cleaned
    assert "\x0c" not in cleaned
    # The genuine clauses survive.
    assert "12.1 A financial institution must obtain" in cleaned
    assert "17.1 A financial institution shall notify" in cleaned


def test_split_chunks_bounds_size_and_breaks_on_paragraphs():
    # A body of many small paragraphs, well over one chunk's budget.
    paragraphs = [f"{i}.1 Requirement paragraph number {i}." for i in range(1, 60)]
    body = "\n\n".join(paragraphs)

    chunks = _split_chunks(body, max_chars=200)

    assert len(chunks) > 1
    # Never exceeds the budget except where a single paragraph already does.
    assert all(len(c) <= 200 or "\n\n" not in c for c in chunks)
    # No clause paragraph is split across a chunk boundary.
    rejoined = "\n\n".join(chunks)
    for p in paragraphs:
        assert p in rejoined


def test_split_chunks_returns_document_order():
    chunks = _split_chunks(MARKITDOWN_STYLE_MARKDOWN, max_chars=120)
    joined = "\n\n".join(chunks)
    assert joined.index("12.1") < joined.index("17.1")


def test_split_chunks_on_all_noise_returns_empty():
    all_noise = (
        "PART A  OVERVIEW ...................... 2\n"
        "Issued on: 23 October 2019\n"
        "3 of 20\n"
    )
    assert _split_chunks(all_noise) == []


# Clause-aware chunking: a chunk must never START in the middle of a clause
# (a headless fragment made the parser LLM echo source text instead of JSON).
# This fixture packs several clauses, each with sub-items, past a small budget.
CLAUSE_BODY_MARKDOWN = (
    "10.1  A financial institution must do the first thing.\n\n"
    "10.2  A financial institution must do the second thing, having first:\n"
    "(a)  completed step a;\n"
    "(b)  completed step b; and\n"
    "(c)  completed step c.\n\n"
    "10.3  A financial institution must do the third thing.\n\n"
    "11.1  Cloud services require notification.\n"
)


def test_split_chunks_every_chunk_starts_at_a_clause_boundary():
    # Small budget forces multiple chunks; each must begin at an N.M clause.
    chunks = _split_chunks(CLAUSE_BODY_MARKDOWN, max_chars=120)

    assert len(chunks) > 1
    for chunk in chunks:
        assert _CLAUSE_START_RE.match(chunk), (
            f"chunk starts mid-clause: {chunk[:50]!r}"
        )


def test_split_chunks_never_splits_a_clause_across_chunks():
    chunks = _split_chunks(CLAUSE_BODY_MARKDOWN, max_chars=120)

    # Clause 10.2's sub-items (a)(b)(c) must all live in the same chunk as 10.2.
    chunk_with_102 = next(c for c in chunks if "10.2" in c)
    assert "(a)  completed step a" in chunk_with_102
    assert "(b)  completed step b" in chunk_with_102
    assert "(c)  completed step c" in chunk_with_102


def test_split_chunks_falls_back_to_paragraphs_without_clause_numbers():
    # Prose with no clause numbers → paragraph packing still yields chunks.
    prose = "\n\n".join(f"Paragraph number {i} of some prose." for i in range(1, 40))
    chunks = _split_chunks(prose, max_chars=200)

    assert len(chunks) > 1
    rejoined = "\n\n".join(chunks)
    assert "Paragraph number 1 of some prose." in rejoined
    assert "Paragraph number 39 of some prose." in rejoined


VALID_ANCHOR_JSON = """[
  {"clause_number": "12.1",
   "starts_with": "A financial institution must obtain the Bank's written approval",
   "heading": "12 Approval for material outsourcing arrangements",
   "parent": null}
]"""


def test_parse_anchor_response_parses_unfenced_json_array():
    anchors = _parse_anchor_response(VALID_ANCHOR_JSON)

    assert anchors == [
        {
            "clause_number": "12.1",
            "starts_with": (
                "A financial institution must obtain the Bank's written approval"
            ),
            "heading": "12 Approval for material outsourcing arrangements",
            "parent": None,
        }
    ]


def test_parse_anchor_response_parses_fenced_json_array():
    fenced = f"```json\n{VALID_ANCHOR_JSON}\n```"

    anchors = _parse_anchor_response(fenced)

    assert anchors[0]["clause_number"] == "12.1"
    assert anchors[0]["parent"] is None


def test_parse_anchor_response_raises_on_non_list():
    with pytest.raises(LLMResponseError):
        _parse_anchor_response('{"clause_number": "12.1"}')


def test_parse_anchor_response_raises_when_element_missing_required_key():
    # Missing "parent".
    bad = (
        '[{"clause_number": "12.1", "starts_with": "A financial institution", '
        '"heading": "12 Approval"}]'
    )

    with pytest.raises(LLMResponseError):
        _parse_anchor_response(bad)


def test_parse_anchor_response_raises_when_element_is_not_a_dict():
    with pytest.raises(LLMResponseError):
        _parse_anchor_response('["12.1", "12.2"]')


def test_parse_anchor_response_accepts_empty_array_for_clauseless_chunk():
    # A table-of-contents / definitions chunk legitimately has no clauses.
    assert _parse_anchor_response("[]") == []


def test_find_clause_anchors_calls_per_chunk_and_merges_in_order(
    monkeypatch: pytest.MonkeyPatch,
):
    import engine.clauses as clauses

    calls: list[str] = []

    def fake_call_chat(deployment: str, system: str, user: str) -> str:
        calls.append(user)
        # A noise/TOC chunk returns [] (tolerated); clause chunks return anchors
        # keyed off which clause text the chunk contains.
        if "12.1 A financial institution" in user:
            return (
                '[{"clause_number": "12.1", "starts_with": "A financial '
                'institution must obtain the Bank\'s written approval", '
                '"heading": "12 Approval for material outsourcing '
                'arrangements", "parent": null}]'
            )
        if "17.1 A financial institution" in user:
            return (
                '[{"clause_number": "17.1", "starts_with": "A financial '
                'institution shall notify the Bank within 14 days", '
                '"heading": "17 Cloud services", "parent": null}]'
            )
        return "[]"

    monkeypatch.setattr(clauses, "call_chat", fake_call_chat)

    # Small max_chars so the fixture splits into multiple chunks; noise is
    # stripped first, so TOC/headers never reach the model.
    monkeypatch.setattr(clauses, "_MAX_CHUNK_CHARS", 120)
    anchors = find_clause_anchors(MARKITDOWN_STYLE_MARKDOWN, "outsourcing-v1-2019")

    # Merged anchor list preserves document order across chunks; clause-less
    # chunks contribute nothing without failing the run.
    assert [a["clause_number"] for a in anchors] == ["12.1", "17.1"]
    assert all(
        set(a.keys()) == {"clause_number", "starts_with", "heading", "parent"}
        for a in anchors
    )


def test_find_clause_anchors_retries_on_non_json_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
):
    """A sporadic prose reply is retried; the second attempt's JSON is used,
    so one flaky chunk does not kill the build."""
    import engine.clauses as clauses

    attempts: list[int] = [0]

    def flaky_call_chat(deployment: str, system: str, user: str) -> str:
        attempts[0] += 1
        if attempts[0] == 1:
            # First reply: the model echoes source prose instead of JSON.
            return "necessary to perform the obligations under the agreement;"
        return (
            '[{"clause_number": "12.1", "starts_with": "A financial '
            'institution must obtain the Bank\'s written approval", '
            '"heading": "12", "parent": null}]'
        )

    monkeypatch.setattr(clauses, "call_chat", flaky_call_chat)

    single_chunk = (
        "12.1 A financial institution must obtain the Bank's written approval.\n"
    )
    anchors = find_clause_anchors(single_chunk, "outsourcing-v1-2019")

    assert attempts[0] == 2  # retried once
    assert [a["clause_number"] for a in anchors] == ["12.1"]


def test_find_clause_anchors_raises_after_exhausting_retries(
    monkeypatch: pytest.MonkeyPatch,
):
    """If every attempt returns non-JSON, the build fails loudly rather than
    silently dropping the chunk (a dropped chunk = missing clauses)."""
    import engine.clauses as clauses

    monkeypatch.setattr(
        clauses, "call_chat", lambda deployment, system, user: "still not json"
    )

    with pytest.raises(LLMResponseError):
        find_clause_anchors("12.1 Some clause text.\n", "outsourcing-v1-2019")


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
