"""Tests for engine.anchors — the widened AnchorIndex + segmenter registry.

Task 2 of `docs/specs/workstream-brain/spec-engine-anchor-segmentation.md`:
core types + index only. Segmenter strategies land in Tasks 3-5 and register
themselves via `SegmenterRegistry` — this file exercises the empty-registry
foundation they will all call into.
"""

import pytest

from engine.anchors import (
    Anchor,
    AnchorIndex,
    AnchorTextNotFoundError,
    SegmenterRegistry,
    UnknownDocClassError,
    UnknownDocumentIdError,
    prose_segment,
    segment,
    semi_structured_segment,
    structured_rules_segment,
    verify_substring,
)


def _make_anchor(
    anchor_id: str,
    *,
    text: str = "some verbatim clause text",
    document_id: str = "doc-a",
    doc_class: str = "structured-rules",
    anchor_label: str | None = None,
) -> Anchor:
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_label if anchor_label is not None else anchor_id,
        "text": text,
        "doc_class": doc_class,  # type: ignore[typeddict-item]
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


def test_anchor_index_get_returns_none_for_missing_id():
    index = AnchorIndex([_make_anchor("MAS 637 §7.3.15")])
    assert index.get("Nonexistent 99.9") is None


def test_anchor_index_get_returns_anchor_for_present_id():
    anchor = _make_anchor("BoE Ch3 §4.2", text="Retail exposures shall...")
    index = AnchorIndex([anchor])

    entry = index.get("BoE Ch3 §4.2")

    assert entry is not None
    assert entry["anchor_id"] == "BoE Ch3 §4.2"
    assert entry["text"] == "Retail exposures shall..."


def test_anchor_index_all_returns_insertion_order():
    a = _make_anchor("A 1", document_id="doc-a")
    b = _make_anchor("B 1", document_id="doc-b")
    c = _make_anchor("C 1", document_id="doc-c")
    index = AnchorIndex([a, b, c])

    assert [entry["anchor_id"] for entry in index.all()] == ["A 1", "B 1", "C 1"]


def test_anchor_index_by_document_filters_correctly():
    a1 = _make_anchor("A 1", document_id="doc-a")
    a2 = _make_anchor("A 2", document_id="doc-a")
    b1 = _make_anchor("B 1", document_id="doc-b")
    index = AnchorIndex([a1, b1, a2])

    doc_a = index.by_document("doc-a")

    # Preserves insertion order, keeps only doc-a entries.
    assert [entry["anchor_id"] for entry in doc_a] == ["A 1", "A 2"]
    assert index.by_document("no-such-doc") == []


def test_anchor_index_rejects_duplicate_ids():
    first = _make_anchor("MAS 637 §7.3.15", text="first version")
    dup = _make_anchor("MAS 637 §7.3.15", text="second version")

    with pytest.raises(ValueError, match="MAS 637"):
        AnchorIndex([first, dup])


def test_verify_substring_passes_when_text_is_in_source():
    source = "Some preamble.\n\n4.2 A financial institution must maintain capital.\n"
    anchor = _make_anchor(
        "BoE Ch3 §4.2",
        text="A financial institution must maintain capital.",
    )

    # No exception means pass.
    verify_substring(anchor, source)


def test_verify_substring_raises_when_text_not_in_source():
    source = "A short markdown source with limited content."
    anchor = _make_anchor(
        "BoE Ch3 §4.2",
        text="This phrase does not appear anywhere in the source markdown.",
    )

    with pytest.raises(AnchorTextNotFoundError) as excinfo:
        verify_substring(anchor, source)

    msg = str(excinfo.value)
    assert "BoE Ch3 §4.2" in msg
    # First 80 chars of anchor.text (or the whole thing if shorter) are echoed.
    assert "This phrase does not appear" in msg
    # Note the source length.
    assert str(len(source)) in msg


def test_segmenter_registry_stores_and_retrieves_functions():
    registry = SegmenterRegistry()

    def fake_segmenter(document_id: str, source_markdown: str) -> list[Anchor]:
        return [_make_anchor(f"{document_id} §1", document_id=document_id)]

    registry.register("structured-rules", fake_segmenter)

    fn = registry.get("structured-rules")
    assert fn is not None
    result = fn("doc-a", "irrelevant")
    assert result[0]["anchor_id"] == "doc-a §1"

    # Unregistered class returns None.
    assert registry.get("prose") is None


# ---------------------------------------------------------------------------
# Task 3: structured-rules segmenter (wraps engine.clauses.segment_clauses).
#
# BNM policy documents (RMiT, Outsourcing, OpRes, etc.) flow through this path
# unchanged — the segmenter is a thin re-wrapper of the existing ClauseIndex
# pipeline, so every emitted anchor is byte-identical to today's clause text.

_STRUCTURED_RULES_MARKDOWN = """1 Introduction

1.1 A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement.

1.2 An application for approval under paragraph 1.1 must be submitted at least ninety days before the proposed commencement date.
"""


def test_structured_rules_segment_wraps_clauses_as_anchors():
    anchors = structured_rules_segment("outsourcing", _STRUCTURED_RULES_MARKDOWN)

    assert len(anchors) == 2

    first, second = anchors
    assert first["anchor_id"] == "Outsourcing 1.1"
    assert first["anchor_label"] == "Outsourcing 1.1"
    assert first["doc_class"] == "structured-rules"
    assert first["document_id"] == "outsourcing"
    assert first["heading_path"] == []
    assert first["page_span"] is None
    assert first["parent_anchor"] is None
    assert first["text"] in _STRUCTURED_RULES_MARKDOWN
    assert first["text"].startswith("A financial institution")

    assert second["anchor_id"] == "Outsourcing 1.2"
    assert second["text"] in _STRUCTURED_RULES_MARKDOWN


def test_structured_rules_uses_policy_short_name_for_anchor_id():
    # `"rmit"` maps to `"RMiT"` in POLICY_SHORT_NAMES — the anchor_id must use
    # the canonical shortname (mixed case), NOT the raw lowercase document_id.
    rmit_markdown = (
        "1 Introduction\n\n"
        "1.1 Financial institutions must invest in the required expertise.\n"
    )

    anchors = structured_rules_segment("rmit", rmit_markdown)

    assert len(anchors) == 1
    assert anchors[0]["anchor_id"] == "RMiT 1.1"
    assert not anchors[0]["anchor_id"].startswith("rmit ")


def test_structured_rules_raises_for_unknown_document_id():
    # A document_id with no entry in POLICY_SHORT_NAMES must raise a clear
    # wrapped error, not a bare KeyError. Naming the offending document_id in
    # the message is the "diagnose without a debugger" contract.
    with pytest.raises(UnknownDocumentIdError, match="not-a-real-doc"):
        structured_rules_segment("not-a-real-doc", "1.1 Some clause text.\n")


def test_structured_rules_registered_by_default():
    # The module-level `segment(...)` uses the default registry, which Task 3
    # populates at import time with the structured-rules strategy. No explicit
    # `.register(...)` call by the caller is required.
    anchors = segment(
        document_id="outsourcing",
        source_markdown=_STRUCTURED_RULES_MARKDOWN,
        doc_class="structured-rules",
    )

    assert len(anchors) >= 1
    assert all(a["doc_class"] == "structured-rules" for a in anchors)
    assert anchors[0]["anchor_id"].startswith("Outsourcing ")


def test_structured_rules_round_trips_bnm_clauses_byte_identical():
    """The structured-rules segmenter wraps ClauseIndex output — a BNM clause's
    text MUST match byte-for-byte what ClauseIndex returns today.

    Runs the same real BNM markdown (`data/mock/rmit-v2-2026-draft.md`) through
    BOTH pipelines and compares selected clause texts. Any drift here would be
    an anchor-wrapper bug corrupting the verbatim-citation guarantee — the
    whole point of Task 3 is that this round-trip is a no-op.
    """
    from pathlib import Path

    import pytest

    from engine.clauses import ClauseIndex, segment_clauses

    md_path = Path("data/mock/rmit-v2-2026-draft.md")
    if not md_path.exists():
        pytest.skip(
            "data/mock/rmit-v2-2026-draft.md not committed to this branch — "
            "regression guard runs when the anchor-segmentation fixture is present"
        )
    markdown = md_path.read_text(encoding="utf-8")

    # Baseline: what ClauseIndex returns today.
    entries = segment_clauses(
        markdown=markdown,
        document_id="rmit",
        policy_id="rmit",
        source="published",
    )
    baseline_index = ClauseIndex(entries)

    # Anchor path: what Task 3's segmenter emits.
    anchors = structured_rules_segment("rmit", markdown)
    anchors_by_id = {a["anchor_id"]: a for a in anchors}

    # Every ClauseIndex clause is present as an Anchor with byte-identical text.
    for clause_number, baseline in entries.items():
        anchor = anchors_by_id.get(clause_number)
        assert anchor is not None, f"missing anchor for {clause_number}"
        assert anchor["text"] == baseline["text"], (
            f"text drift for {clause_number}: "
            f"anchor {anchor['text'][:40]!r} vs baseline "
            f"{baseline['text'][:40]!r}"
        )

    # Spot-check a few well-known BNM clause_numbers explicitly, so a future
    # regression flags loudly on named clauses instead of an aggregate diff.
    for clause_number in ("RMiT 1.1", "RMiT 1.1(a)", "RMiT 1.2"):
        baseline_entry = baseline_index.get(clause_number)
        assert baseline_entry is not None
        assert anchors_by_id[clause_number]["text"] == baseline_entry["text"]


def test_segment_raises_unknown_doc_class():
    # Tasks 3-5 register `"structured-rules"`, `"semi-structured"`, `"prose"`
    # at import time. An arbitrary unregistered class must still raise a clear
    # UnknownDocClassError naming the offending class in the message.
    with pytest.raises(UnknownDocClassError, match="not-a-real-class"):
        segment(
            document_id="doc-a",
            source_markdown="ignored",
            doc_class="not-a-real-class",
        )


# ---------------------------------------------------------------------------
# Task 4: semi-structured segmenter (deterministic markdown-heading walker).
#
# Detects `#`/`##`/`###` headings AND numbered-list-as-heading patterns
# (`4.4 Title`, `(a)`, `(i)`, `20.3(a)`). Emits one Anchor per leaf section.
# NO LLM calls — pure Python parsing.


_BCBS_CRE_MARKDOWN = """20.1 The standardised approach for credit risk applies to all banking book exposures unless explicitly exempted.

20.2 Banks shall assign risk weights to on-balance sheet exposures using the tables set out in this chapter.

20.3(a) For residential real estate exposures, banks shall apply the risk weight determined by the loan-to-value ratio.

20.3(b) For commercial real estate exposures, banks shall apply the risk weight determined by paragraph 20.9.
"""


def test_semi_structured_bcbs_cre_numbered_paragraphs():
    """BCBS-style numbered paragraphs (`20.1`, `20.2`, `20.3(a)`, `20.3(b)`)
    each become one leaf anchor. BCBS shortnames render WITHOUT the `§` mark
    (unlike MAS/BoE) — the caller passes `section_mark=False` (the default).
    """
    anchors = semi_structured_segment(
        document_id="bcbs-cre",
        source_markdown=_BCBS_CRE_MARKDOWN,
        shortname="BCBS CRE",
    )

    assert [a["anchor_id"] for a in anchors] == [
        "BCBS CRE 20.1",
        "BCBS CRE 20.2",
        "BCBS CRE 20.3(a)",
        "BCBS CRE 20.3(b)",
    ]
    for anchor in anchors:
        assert anchor["doc_class"] == "semi-structured"
        assert anchor["document_id"] == "bcbs-cre"
        assert anchor["text"] in _BCBS_CRE_MARKDOWN


_MAS_637_MARKDOWN = """# Section 7 Credit Risk

Introductory paragraph for section 7 that must be dropped because Section 7 has children.

## 7.3 Standardised Approach

Introductory paragraph for 7.3 that must be dropped because 7.3 has a child.

### 7.3.15 Residential mortgage risk weights

A financial institution shall apply a risk weight of 35% to a residential mortgage loan that meets the eligibility criteria set out in this paragraph.

The loan must be secured by a first legal charge over the property.
"""


def test_semi_structured_mas_637_headings():
    """MAS 637-style 3-level markdown heading (`# Section 7 → ## 7.3 → ### 7.3.15`).

    Only the leaf `7.3.15` gets an anchor; parents are internal nodes. The
    `heading_path` records the enclosing headings, most-general first, with
    header prefixes stripped. `section_mark=True` inserts `§` between the
    shortname and the numeric path — the MAS/BoE citation convention.
    """
    anchors = semi_structured_segment(
        document_id="mas-637-2024-07",
        source_markdown=_MAS_637_MARKDOWN,
        shortname="MAS 637",
        section_mark=True,
    )

    assert len(anchors) == 1
    leaf = anchors[0]
    assert leaf["anchor_id"] == "MAS 637 §7.3.15"
    assert leaf["anchor_label"] == "MAS 637 §7.3.15"
    assert leaf["doc_class"] == "semi-structured"
    assert leaf["document_id"] == "mas-637-2024-07"
    assert leaf["heading_path"] == [
        "Section 7 Credit Risk",
        "7.3 Standardised Approach",
    ]
    # Text starts with the leaf's own paragraph and is a substring of source.
    assert leaf["text"].startswith("A financial institution shall apply")
    assert leaf["text"] in _MAS_637_MARKDOWN


def test_semi_structured_uses_only_leaves():
    """A heading with both text under it AND child headings is INTERNAL — its
    own paragraph text is dropped. This is the documented leaf-only rule; the
    parent's intro paragraph is not a legal citation because it has no unique
    numeric key of its own without a leaf.
    """
    mixed_content = """# 1 Overview

An intro paragraph attached to the section 1 heading itself — MUST NOT appear
as its own anchor because section 1 has child headings.

## 1.1 First principle

The first principle body text.

## 1.2 Second principle

The second principle body text.
"""

    anchors = semi_structured_segment(
        document_id="mixed",
        source_markdown=mixed_content,
        shortname="X",
    )

    # Only leaves 1.1 and 1.2. Parent `1` is DROPPED.
    assert [a["anchor_id"] for a in anchors] == ["X 1.1", "X 1.2"]
    for anchor in anchors:
        # The parent's intro paragraph is not in any leaf anchor.
        assert (
            "An intro paragraph attached to the section 1 heading" not in anchor["text"]
        )


def test_semi_structured_verifies_substring(monkeypatch):
    """Every emitted anchor's `text` MUST pass `verify_substring` — the
    verbatim-citation guardrail. Wraps `verify_substring` with a spy and
    asserts one call per emitted anchor, all passing.
    """
    import engine.anchors as anchors_module

    calls: list[tuple[str, str]] = []
    real_verify = anchors_module.verify_substring

    def spy(anchor: Anchor, source: str) -> None:
        calls.append((anchor["anchor_id"], anchor["text"]))
        real_verify(anchor, source)

    monkeypatch.setattr(anchors_module, "verify_substring", spy)

    anchors = anchors_module.semi_structured_segment(
        document_id="bcbs-cre",
        source_markdown=_BCBS_CRE_MARKDOWN,
        shortname="BCBS CRE",
    )

    # One call per emitted anchor, in emission order.
    assert len(calls) == len(anchors) == 4
    assert [call[0] for call in calls] == [a["anchor_id"] for a in anchors]
    # Every text is a genuine substring of the source (real_verify would raise
    # otherwise — this line asserts no exceptions leaked through).
    for anchor in anchors:
        assert anchor["text"] in _BCBS_CRE_MARKDOWN


def test_semi_structured_registered_by_default():
    """`segment(...)` uses the default registry, which Task 4 populates at
    import time with the semi-structured strategy. No explicit `.register(...)`
    call by the caller is required.
    """
    anchors = segment(
        document_id="bcbs-cre",
        source_markdown=_BCBS_CRE_MARKDOWN,
        doc_class="semi-structured",
    )

    assert len(anchors) == 4
    assert all(a["doc_class"] == "semi-structured" for a in anchors)
    # anchor_ids use document_id as prefix when segment() is called without a
    # shortname override — the build pipeline (Task 7) wires manifest-driven
    # shortnames via a functools.partial, but the module-level dispatcher
    # falls back to document_id here.
    assert anchors[0]["anchor_id"] == "bcbs-cre 20.1"


# ---------------------------------------------------------------------------
# Task 5: prose segmenter (semantic paragraph chunker).
#
# Deterministic Python — no LLM. Three rules from the spec:
#   1. Split on paragraph boundaries (`\n\s*\n`).
#   2. Min-length merge — paragraphs under 200 chars merge into the NEXT.
#   3. Max-length split — chunks over 1500 chars split at the nearest
#      sentence boundary before the 1500-char mark.
# Every emitted anchor's `text` is a literal substring of `source_markdown`
# (Option A: byte-offset tracking through merges, never string concatenation).


def test_prose_paragraph_split_basic():
    """Three well-separated paragraphs of ~300 chars each become three anchors —
    each is above the 200-char merge floor and below the 1500-char split ceiling.
    """
    para = (
        "The bank shall maintain a comprehensive operational resilience framework "
        "that identifies critical business services and sets impact tolerances "
        "for disruption. The framework must be reviewed annually and updated "
        "whenever material changes to the operating model occur."
    )
    assert 200 <= len(para) <= 1500  # sanity: within the plain-chunk band
    source = f"{para}\n\n{para}\n\n{para}\n"

    anchors = prose_segment("boe-op-res", source)

    assert len(anchors) == 3
    for anchor in anchors:
        assert anchor["doc_class"] == "prose"
        assert anchor["document_id"] == "boe-op-res"
        assert anchor["text"] in source


def test_prose_min_length_merge():
    """Paragraphs under 200 chars merge into the NEXT paragraph. Source has
    three paragraphs of lengths 80, 60, 900 chars: the two short leading
    paragraphs both fold into the 900-char follower, yielding ONE anchor
    (~1040 chars — still under the 1500-char split ceiling).
    """
    short_a = "Short paragraph A. " * 4  # ~76 chars
    short_b = "Short B. " * 7  # ~63 chars
    long_para = (
        "This is the substantive paragraph that carries the citable regulatory "
        "content. It must be at least nine hundred characters long so that when "
        "the two short precursor paragraphs merge into it under the min-length "
        "rule, the resulting chunk still sits above the two-hundred-character "
        "floor and below the fifteen-hundred-character split ceiling. To reach "
        "that length we describe in careful, redundant detail the framework "
        "requirements: institutions shall document their approach, obtain "
        "senior management approval, and review the framework at least "
        "annually or whenever material changes occur. The framework shall also "
        "identify critical business services, set impact tolerances, and "
        "specify recovery objectives that align with the institution's risk "
        "appetite and strategic objectives. Every element of the framework is "
        "subject to independent review by the internal audit function on a "
        "risk-based cycle."
    )
    assert len(short_a) < 200
    assert len(short_b) < 200
    assert 700 < len(long_para) < 1200
    source = f"{short_a}\n\n{short_b}\n\n{long_para}\n"

    anchors = prose_segment("boe-op-res", source)

    # All three paragraphs collapsed into ONE chunk because both short heads
    # fold forward into the long tail.
    assert len(anchors) == 1
    text = anchors[0]["text"]
    # The merged text is a literal slice of the source (contains the blank
    # lines between the original paragraphs).
    assert text in source
    # And it contains snippets from all three original paragraphs.
    assert "Short paragraph A." in text
    assert "Short B." in text
    assert "substantive paragraph" in text


def test_prose_max_length_sentence_split():
    """A single 2400-char paragraph with four sentence boundaries splits at
    the sentence boundary NEAREST 1500 chars — yielding two anchors, both
    ending in `.`, `!`, or `?`.
    """
    # Four sentences, each ~600 chars, joined with a single space. The whole
    # paragraph is one block of prose (no paragraph boundaries) so the
    # segmenter's max-length rule is the only thing that can split it.
    sentence = (
        "This sentence describes in patient detail the operational "
        "resilience requirements that the framework imposes on regulated "
        "institutions and their material third parties, including the "
        "obligation to identify critical business services, set impact "
        "tolerances denominated in time or units of loss, test the "
        "recovery objectives against a range of severe but plausible "
        "scenarios, and document the outcomes of those tests in a form "
        "that internal audit and the supervisor can inspect on demand and "
        "compare against prior-year exercises to establish trend lines."
    )
    assert 550 < len(sentence) < 650
    paragraph = f"{sentence} {sentence} {sentence} {sentence}"
    assert 2200 < len(paragraph) < 2600

    anchors = prose_segment("boe-op-res", paragraph)

    assert len(anchors) == 2
    for anchor in anchors:
        # Every emitted chunk ends with a sentence terminator.
        assert anchor["text"].rstrip()[-1] in {".", "!", "?"}
        # Every chunk is a literal substring of the source.
        assert anchor["text"] in paragraph
    # First chunk sits at or under 1500 chars (split before the ceiling).
    assert len(anchors[0]["text"]) <= 1500


def test_prose_page_span_from_page_marker():
    """Azure Document Intelligence emits `<!-- page N -->` breadcrumbs inline.
    The prose segmenter reads the nearest page marker above the chunk to fill
    `page_span=(N, N)`, and the resulting anchor_id embeds `p.N`.
    """
    para = (
        "The Prudential Regulation Authority expects firms to establish and "
        "maintain governance arrangements that are proportionate to the nature, "
        "scale, and complexity of their business. Firms shall document these "
        "arrangements and review them at least annually against evolving "
        "regulatory expectations and industry practice."
    )
    assert len(para) >= 200
    source = f"<!-- page 5 -->\n\n{para}\n"

    anchors = prose_segment("boe-op-res", source, shortname="BoE OpRes")

    assert len(anchors) == 1
    anchor = anchors[0]
    assert anchor["page_span"] == (5, 5)
    assert "p.5" in anchor["anchor_id"]
    # Shortname prefix landed in the anchor_id.
    assert anchor["anchor_id"].startswith("BoE OpRes ")


def test_prose_verify_substring_passes():
    """Every emitted anchor's `text` is a LITERAL substring of the input
    (Option A: byte-offset tracking, never string concatenation with `" "`).
    Uses a mixed source with short + long paragraphs plus a heading, exercising
    all three merge/split code paths, and checks each anchor round-trips.
    """
    heading = "# Chapter 3 Credit Risk"
    short = "Very short intro."
    long_a = "A" * 300 + " " + "B" * 300 + " " + "C" * 300 + " " + "D" * 300
    long_b = "E" * 250 + " " + "F" * 250
    source = f"{heading}\n\n{short}\n\n{long_a}\n\n{long_b}\n"

    anchors = prose_segment("chapter-3", source)

    # Whatever the segmenter emits, every chunk text must be findable
    # verbatim in the source markdown.
    assert len(anchors) >= 1
    for anchor in anchors:
        assert anchor["text"] in source, (
            f"anchor {anchor['anchor_id']!r} text is not a literal substring "
            f"(starts: {anchor['text'][:60]!r})"
        )


def test_prose_no_headings_uses_chunk_index():
    """When there is neither a page marker nor a markdown heading above a
    chunk, the anchor_id falls back to `{shortname} chunk#{i}` — the
    index-based disambiguator.
    """
    para_a = "First substantive paragraph. " * 12
    para_b = "Second substantive paragraph. " * 12
    assert len(para_a) >= 200 and len(para_b) >= 200
    source = f"{para_a}\n\n{para_b}\n"

    anchors = prose_segment("plain-doc", source, shortname="Plain")

    assert len(anchors) == 2
    assert anchors[0]["anchor_id"] == "Plain chunk#0"
    assert anchors[1]["anchor_id"] == "Plain chunk#1"
    for anchor in anchors:
        assert anchor["heading_path"] == []
        assert anchor["page_span"] is None


def test_prose_registered_by_default():
    """The default registry ships with `"prose"` installed at import time,
    matching `structured-rules` / `semi-structured`. `segment(...)` therefore
    works on prose without any explicit `.register(...)` call.
    """
    para = "A" * 250
    source = f"{para}\n\n{para}\n"

    anchors = segment(
        document_id="prose-doc",
        source_markdown=source,
        doc_class="prose",
    )

    assert len(anchors) == 2
    assert all(a["doc_class"] == "prose" for a in anchors)
    assert all(a["document_id"] == "prose-doc" for a in anchors)
