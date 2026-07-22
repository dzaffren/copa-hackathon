from engine.anchors import AnchorTextNotFoundError
from engine.anchors_llm import llm_boundary_segment

SOURCE = (
    "REGULATION (EU) 2024/1689\n\n"
    "Article 1\n\n"
    "This Regulation lays down harmonised rules on artificial intelligence.\n\n"
    "Article 2\n\n"
    "This Regulation applies to providers placing AI systems on the market.\n"
)


def _boundaries(document_id, source_markdown, doc_class):
    return [
        {"anchor_label": "Article 1",
         "starts_with": "This Regulation lays down harmonised rules",
         "parent": None},
        {"anchor_label": "Article 2",
         "starts_with": "This Regulation applies to providers",
         "parent": None},
    ]


def test_boundary_segment_produces_citable_verbatim_anchors():
    anchors = llm_boundary_segment(
        "eu-ai-act", SOURCE, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=_boundaries,
    )
    assert [a["anchor_id"] for a in anchors] == [
        "EU AI Act Article 1", "EU AI Act Article 2"]
    # citable label
    assert anchors[0]["anchor_label"] == "Article 1"
    # verbatim: text is a real substring of the source
    for a in anchors:
        assert a["text"] in SOURCE
        assert a["text"].strip()
    assert anchors[0]["doc_class"] == "legislative"


def test_boundary_not_found_is_dropped_not_raised():
    def bad(document_id, source_markdown, doc_class):
        return [{"anchor_label": "Article 9",
                 "starts_with": "text that is absent from source",
                 "parent": None}]
    report: list[dict] = []
    anchors = llm_boundary_segment(
        "eu-ai-act", SOURCE, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=bad, dropped_report=report,
    )
    assert anchors == []
    assert report and report[0]["reason"] == "not_found"
    assert report[0]["anchor_label"] == "Article 9"


def test_every_returned_anchor_passes_verify_substring():
    # Guard: llm_boundary_segment must never emit an anchor whose text is not a
    # substring — a defensive re-check on its own output.
    anchors = llm_boundary_segment(
        "eu-ai-act", SOURCE, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=_boundaries,
    )
    from engine.anchors import verify_substring
    for a in anchors:
        verify_substring(a, SOURCE)  # must not raise


def test_verify_substring_rejects_a_fabricated_anchor():
    # Guard the verbatim guarantee directly: an anchor whose text is NOT in the
    # source must raise, proving verify_substring is a real gate.
    import pytest

    from engine.anchors import verify_substring

    bad_anchor = {
        "anchor_id": "EU AI Act Article 99",
        "anchor_label": "Article 99",
        "text": "this text does not appear anywhere in the source document",
        "doc_class": "legislative",
        "document_id": "eu-ai-act",
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }
    with pytest.raises(AnchorTextNotFoundError):
        verify_substring(bad_anchor, SOURCE)
