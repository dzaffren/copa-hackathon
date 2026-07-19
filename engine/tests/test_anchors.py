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
    segment,
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


def test_segment_raises_unknown_doc_class():
    # Module-level `segment` uses the module-level registry which is empty on
    # import — Tasks 3-5 register the real strategies. Any doc_class raises.
    with pytest.raises(UnknownDocClassError, match="structured-rules"):
        segment(
            document_id="doc-a",
            source_markdown="ignored",
            doc_class="structured-rules",
        )
