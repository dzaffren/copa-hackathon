"""Tests for the Arm G finding pipeline (engine/arm_g.py).

Covers the spec's Test Scenarios 1-9
(docs/specs/workstream-brain/spec-engine-arm-g-pipeline.md). No live model
calls — every stage's ``call_chat`` is monkeypatched, mirroring how the existing
engine tests stub the network seam. Deployment routing is asserted by capturing
the ``deployment`` argument each ``call_chat`` receives.
"""

import json

import pytest

from engine.anchors import Anchor, AnchorIndex


def _anchor(anchor_id: str, document_id: str, text: str) -> Anchor:
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id,
        "text": text,
        "doc_class": "structured-rules",
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


# ---------------------------------------------------------------------------
# Test 8 — cache invalidation on cap change.
# ---------------------------------------------------------------------------


def test_axis_cache_invalidated_on_cap_change(tmp_path, monkeypatch):
    """A cache entry written with axis_cap=5 whose anchor text now yields a
    different cap is a MISS → re-extraction → the entry is rewritten with the
    new cap."""
    import engine.arm_g as arm_g

    monkeypatch.setattr(arm_g, "AXES_DIR", tmp_path)

    # A long anchor: cap = min(12, max(5, ceil(len/400))). ~2400 chars → cap 6.
    long_text = "x" * 2400
    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", long_text)])

    # Seed a stale cache entry with axis_cap=5 (wrong for this text).
    stale = {
        "document_id": "doc-a",
        "model": "old-model",
        "anchors": [
            {
                "anchor_id": "DOC 1.1",
                "text_hash": arm_g._text_hash(long_text),
                "axis_cap": 5,
                "axes": ["stale axis"],
            }
        ],
    }
    (tmp_path / "axes-doc-a.json").write_text(json.dumps(stale), encoding="utf-8")

    calls = []

    def fake_call_chat(deployment, system, user, max_tokens=None):
        calls.append(deployment)
        return json.dumps(["fresh axis one", "fresh axis two"])

    monkeypatch.setattr(arm_g, "call_chat", fake_call_chat)

    result = arm_g.extract_axes_for_document(index, "doc-a")

    # Cap change forced a re-extraction (one model call).
    assert len(calls) == 1
    assert result["DOC 1.1"] == ["fresh axis one", "fresh axis two"]

    # The entry is rewritten with the correct new cap.
    rewritten = json.loads((tmp_path / "axes-doc-a.json").read_text(encoding="utf-8"))
    entry = rewritten["anchors"][0]
    assert entry["axis_cap"] == arm_g._axis_cap(long_text)
    assert entry["axis_cap"] != 5
    assert entry["axes"] == ["fresh axis one", "fresh axis two"]


def test_axis_cache_hit_skips_extraction(tmp_path, monkeypatch):
    """When text_hash AND axis_cap both match, the entry is reused with no model
    call."""
    import engine.arm_g as arm_g

    monkeypatch.setattr(arm_g, "AXES_DIR", tmp_path)

    text = "A short clause about consent."
    index = AnchorIndex([_anchor("DOC 1.1", "doc-a", text)])

    fresh = {
        "document_id": "doc-a",
        "model": "m",
        "anchors": [
            {
                "anchor_id": "DOC 1.1",
                "text_hash": arm_g._text_hash(text),
                "axis_cap": arm_g._axis_cap(text),
                "axes": ["cached axis"],
            }
        ],
    }
    (tmp_path / "axes-doc-a.json").write_text(json.dumps(fresh), encoding="utf-8")

    def boom(*a, **k):  # pragma: no cover - must not be called
        raise AssertionError("call_chat should not run on a cache hit")

    monkeypatch.setattr(arm_g, "call_chat", boom)

    result = arm_g.extract_axes_for_document(index, "doc-a")
    assert result["DOC 1.1"] == ["cached axis"]


def test_axis_cap_scales_with_length():
    """A long dense anchor gets a higher cap than a short one, both bounded."""
    import engine.arm_g as arm_g

    short = arm_g._axis_cap("A single short sentence.")
    long = arm_g._axis_cap("x" * 4000)
    assert short == 5
    assert long > short
    assert long <= 12
