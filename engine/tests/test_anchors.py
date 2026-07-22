import pytest

from engine.anchors import (
    DOC_CLASSES,
    AnchorIndex,
    AnchorTextNotFoundError,
    verify_substring,
)


def _anchor(anchor_id="EU AI Act Article 1", text="Providers shall ensure",
            doc_class="legislative", document_id="eu-ai-act"):
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id.split(" ", 2)[-1],
        "text": text,
        "doc_class": doc_class,
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


def test_doc_classes_include_legislative_and_framework():
    assert "legislative" in DOC_CLASSES
    assert "framework" in DOC_CLASSES
    assert "structured-rules" in DOC_CLASSES
    assert "prose" in DOC_CLASSES


def test_verify_substring_passes_when_text_is_a_substring():
    source = "... Providers shall ensure that the technical ..."
    verify_substring(_anchor(text="Providers shall ensure"), source)  # no raise


def test_verify_substring_raises_when_text_absent():
    with pytest.raises(AnchorTextNotFoundError) as exc:
        verify_substring(_anchor(text="not present here"), "totally different source")
    assert "EU AI Act Article 1" in str(exc.value)


def test_index_get_returns_none_on_miss():
    idx = AnchorIndex([_anchor()])
    assert idx.get("nope") is None
    assert idx.get("EU AI Act Article 1") is not None


def test_index_by_document_filters_in_insertion_order():
    a = _anchor(anchor_id="EU AI Act Article 1", document_id="eu-ai-act")
    b = _anchor(anchor_id="RMiT 10.16", document_id="rmit-v2-2025",
                doc_class="structured-rules")
    idx = AnchorIndex([a, b])
    got = idx.by_document("eu-ai-act")
    assert [x["anchor_id"] for x in got] == ["EU AI Act Article 1"]
    assert len(idx) == 2
    assert "RMiT 10.16" in idx


def test_duplicate_anchor_id_raises_at_construction():
    with pytest.raises(ValueError):
        AnchorIndex([_anchor(), _anchor()])
