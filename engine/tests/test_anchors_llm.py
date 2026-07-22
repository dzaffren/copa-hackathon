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


def test_unit_text_excludes_next_units_heading():
    # Regression: the slice from this unit's body to the NEXT unit's body picked
    # up the next unit's heading/label line(s), contaminating the citation. The
    # trim must stop unit 1's text at its own content.
    source = (
        "REGULATION (EU) 2024/1689\n\n"
        "## Article 1 Subject matter\n\n"
        "This Regulation lays down harmonised rules on artificial "
        "intelligence for start-ups.\n\n"
        "## Article 2 Scope\n\n"
        "This Regulation applies to providers placing AI systems on the market.\n"
    )

    def boundaries(document_id, source_markdown, doc_class):
        return [
            {"anchor_label": "Article 1",
             "starts_with": "This Regulation lays down harmonised rules",
             "parent": None},
            {"anchor_label": "Article 2",
             "starts_with": "This Regulation applies to providers",
             "parent": None},
        ]

    anchors = llm_boundary_segment(
        "eu-ai-act", source, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=boundaries,
    )
    art1 = next(a for a in anchors if a["anchor_label"] == "Article 1")
    # Article 1's citation must NOT include Article 2's heading or label.
    assert "Article 2" not in art1["text"]
    assert "## Article 2" not in art1["text"]
    assert "Scope" not in art1["text"]
    # It DOES still carry its own body, verbatim.
    assert art1["text"].endswith("start-ups.")
    assert art1["text"] in source
    # Sanity: Article 2 (the last unit) still slices its own body to source end.
    art2 = next(a for a in anchors if a["anchor_label"] == "Article 2")
    assert "This Regulation applies to providers" in art2["text"]
    assert art2["text"] in source


def test_unit_text_excludes_multiple_bled_heading_blocks():
    # Regression: the gap between two units can contain MULTIPLE heading blocks
    # (a "## SECTION 3 ..." divider immediately followed by the next unit's
    # "## Article 5 ..." heading). A single-block trim only strips the last one,
    # leaving the SECTION divider bled into the previous unit's text. The trim
    # must loop and strip ALL trailing scaffolding blocks.
    source = (
        "## Article 4 Data governance\n\n"
        "Providers shall address bias arising from confidentiality attacks "
        "or model flaws.\n\n"
        "## SECTION 3 Obligations of providers\n\n"
        "## Article 5 Transparency\n\n"
        "Providers shall ensure transparency to users.\n"
    )

    def boundaries(document_id, source_markdown, doc_class):
        return [
            {"anchor_label": "Article 4",
             "starts_with": "Providers shall address bias",
             "parent": None},
            {"anchor_label": "Article 5",
             "starts_with": "Providers shall ensure transparency",
             "parent": None},
        ]

    anchors = llm_boundary_segment(
        "eu-ai-act", source, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=boundaries,
    )
    art4 = next(a for a in anchors if a["anchor_label"] == "Article 4")
    assert "SECTION 3" not in art4["text"]
    assert "Article 5" not in art4["text"]
    assert art4["text"].endswith("model flaws.")
    assert art4["text"] in source


def test_unit_text_keeps_legitimate_multi_paragraph_body():
    # Guard against over-trimming: a unit whose body legitimately spans multiple
    # "\n\n"-separated paragraphs (with no trailing heading of its own) must be
    # returned intact — the loop must stop the moment a trailing block is real
    # body content, not keep eating paragraphs.
    source = (
        "## Article 1 Subject matter\n\n"
        "First paragraph of body.\n\n"
        "Second paragraph of body continues normally.\n\n"
        "## Article 2 Scope\n\n"
        "Providers text body.\n"
    )

    def boundaries(document_id, source_markdown, doc_class):
        return [
            {"anchor_label": "Article 1",
             "starts_with": "First paragraph of body",
             "parent": None},
            {"anchor_label": "Article 2",
             "starts_with": "Providers text body",
             "parent": None},
        ]

    anchors = llm_boundary_segment(
        "eu-ai-act", source, doc_class="legislative",
        shortname="EU AI Act", boundary_fn=boundaries,
    )
    art1 = next(a for a in anchors if a["anchor_label"] == "Article 1")
    assert "First paragraph of body." in art1["text"]
    assert art1["text"].endswith("Second paragraph of body continues normally.")
    assert "Article 2" not in art1["text"]
    assert art1["text"] in source


def test_default_boundary_fn_parses_fenced_json(monkeypatch):
    # The live model wraps its array in a ```json fence; the boundary fn must
    # still parse it (regression: raw json.loads failed on the fence).
    import engine.anchors_llm as mod

    fenced = '```json\n[{"anchor_label": "Article 1", "starts_with": "This Regulation", "parent": null}]\n```'
    monkeypatch.setattr(mod, "call_chat", lambda *a, **k: fenced)
    units = mod._default_boundary_fn("eu-ai-act", "This Regulation lays down rules.", "legislative")
    assert units == [{"anchor_label": "Article 1", "starts_with": "This Regulation", "parent": None}]
