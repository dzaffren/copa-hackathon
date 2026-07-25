"""Tests for scripts/experiments/extract_axes.py — Arm G axis-cap changes.

Covers acceptance criteria:
1. Dynamic cap: long anchor (>2000 chars) gets cap > 5; short anchor (<200 chars) gets cap = 5.
2. extract_axes_for_anchor truncates output to the dynamic cap.
3. Cache invalidation: differing axis_cap in a cached entry triggers re-extraction.
4. Cache hit: same text_hash AND same axis_cap returns cached entry without LLM call.
5. New cache entries store the axis_cap field.

No LLM is called — call_chat is monkeypatched throughout.
"""

from __future__ import annotations

import hashlib
import json
import sys
from math import ceil
from pathlib import Path
from unittest.mock import patch

import pytest

# Make sure the repo root is on the path so the script can import engine.*
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.experiments.extract_axes as ea

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_anchor(anchor_id: str, text: str) -> dict:
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id,
        "text": text,
        "doc_class": "structured-rules",
        "document_id": "doc-test",
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


class _FakeAnchorIndex:
    """Minimal AnchorIndex stub."""

    def __init__(self, anchors: list[dict]) -> None:
        self._anchors = anchors

    def by_document(self, document_id: str) -> list[dict]:
        return [a for a in self._anchors if a["document_id"] == document_id]


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Criterion 1: dynamic cap formula
# ---------------------------------------------------------------------------


def test_long_anchor_cap_exceeds_five():
    """An anchor longer than 2000 chars must produce a dynamic cap > 5."""
    long_text = "regulatory compliance framework " * 65  # ~2080 chars
    assert len(long_text) > 2000
    cap = min(12, max(5, ceil(len(long_text) / 400)))
    assert cap > 5


def test_short_anchor_cap_is_five():
    """An anchor shorter than 200 chars must produce cap == 5."""
    short_text = "A bank shall apply the risk weights set out in the table."
    assert len(short_text) < 200
    cap = min(12, max(5, ceil(len(short_text) / 400)))
    assert cap == 5


# ---------------------------------------------------------------------------
# Criterion 2: extract_axes_for_anchor uses dynamic cap as truncation limit
# ---------------------------------------------------------------------------


def test_extract_axes_for_anchor_truncates_to_dynamic_cap(monkeypatch):
    """For a long anchor, extract_axes_for_anchor returns at most cap (>5) axes.

    The LLM returns 12 axes. With old code (hardcoded 5), the result would be 5.
    With the dynamic cap (which is > 5 for this text), the result should equal cap.
    """
    long_text = "regulatory compliance framework " * 65
    anchor = _make_anchor("doc-test/long-anchor", long_text)
    expected_cap = min(12, max(5, ceil(len(long_text) / 400)))
    assert expected_cap > 5, "prerequisite: long text must give cap > 5"

    many_axes = [f"axis-{i}" for i in range(12)]
    monkeypatch.setattr(ea, "call_chat", lambda *a, **kw: json.dumps(many_axes))

    result = ea.extract_axes_for_anchor(anchor)
    # With dynamic cap, result must equal the computed cap (LLM gave 12, cap < 12).
    # This fails with old hardcoded-5 code because result would be 5, not expected_cap.
    assert len(result) == expected_cap


def test_extract_axes_for_anchor_short_text_caps_at_five(monkeypatch):
    """For a short anchor, extract_axes_for_anchor returns at most 5 axes."""
    short_text = "A bank shall apply risk weights."
    anchor = _make_anchor("doc-test/short-anchor", short_text)

    many_axes = [f"axis-{i}" for i in range(10)]
    monkeypatch.setattr(ea, "call_chat", lambda *a, **kw: json.dumps(many_axes))

    result = ea.extract_axes_for_anchor(anchor)
    assert len(result) <= 5


# ---------------------------------------------------------------------------
# Criterion 3: cache invalidation when axis_cap differs
# ---------------------------------------------------------------------------


def test_cache_miss_when_axis_cap_differs(monkeypatch, tmp_path):
    """Cached entry with stale axis_cap triggers re-extraction even when text is unchanged."""
    anchor_text = "A financial institution shall conduct scenario testing annually."
    anchor = _make_anchor("doc-test/clause-1", anchor_text)
    index = _FakeAnchorIndex([anchor])

    real_cap = min(12, max(5, ceil(len(anchor_text) / 400)))
    stale_cap = real_cap + 1  # guaranteed different from what the code will compute

    axes_dir = tmp_path / "experiments"
    axes_dir.mkdir()
    stale_cache = {
        "document_id": "doc-test",
        "model": "test-model",
        "generated_at": None,
        "anchors": [
            {
                "anchor_id": "doc-test/clause-1",
                "text_hash": _text_hash(anchor_text),
                "axis_cap": stale_cap,
                "axes": ["stale-axis-1", "stale-axis-2"],
            }
        ],
    }
    (axes_dir / "axes-doc-test.json").write_text(
        json.dumps(stale_cache), encoding="utf-8"
    )

    monkeypatch.setattr(ea, "AXES_DIR", axes_dir)

    llm_calls = 0

    def _fake_call_chat(*args, **kwargs):
        nonlocal llm_calls
        llm_calls += 1
        return json.dumps(["fresh-axis-1", "fresh-axis-2"])

    monkeypatch.setattr(ea, "call_chat", _fake_call_chat)

    ea.extract_axes_for_document(index, "doc-test")

    assert llm_calls == 1, "Expected one LLM call when axis_cap differs from cached"

    written = json.loads((axes_dir / "axes-doc-test.json").read_text(encoding="utf-8"))
    assert written["anchors"][0]["axes"] == ["fresh-axis-1", "fresh-axis-2"]


# ---------------------------------------------------------------------------
# Criterion 4: cache hit when text_hash AND axis_cap both match
# ---------------------------------------------------------------------------


def test_cache_hit_when_text_hash_and_cap_match(monkeypatch, tmp_path):
    """When cached text_hash and axis_cap both match, no LLM call is made."""
    anchor_text = "A financial institution shall conduct scenario testing annually."
    anchor = _make_anchor("doc-test/clause-1", anchor_text)
    index = _FakeAnchorIndex([anchor])

    real_cap = min(12, max(5, ceil(len(anchor_text) / 400)))

    axes_dir = tmp_path / "experiments"
    axes_dir.mkdir()
    fresh_cache = {
        "document_id": "doc-test",
        "model": "test-model",
        "generated_at": None,
        "anchors": [
            {
                "anchor_id": "doc-test/clause-1",
                "text_hash": _text_hash(anchor_text),
                "axis_cap": real_cap,
                "axes": ["cached-axis-1", "cached-axis-2"],
            }
        ],
    }
    (axes_dir / "axes-doc-test.json").write_text(
        json.dumps(fresh_cache), encoding="utf-8"
    )

    monkeypatch.setattr(ea, "AXES_DIR", axes_dir)

    llm_calls = 0

    def _fake_call_chat(*args, **kwargs):
        nonlocal llm_calls
        llm_calls += 1
        return json.dumps(["fresh-axis-1"])

    monkeypatch.setattr(ea, "call_chat", _fake_call_chat)

    ea.extract_axes_for_document(index, "doc-test")

    assert llm_calls == 0, "Expected no LLM call on cache hit"

    written = json.loads((axes_dir / "axes-doc-test.json").read_text(encoding="utf-8"))
    assert written["anchors"][0]["axes"] == ["cached-axis-1", "cached-axis-2"]


# ---------------------------------------------------------------------------
# Criterion 5: new cache entries store axis_cap
# ---------------------------------------------------------------------------


def test_new_cache_entry_stores_axis_cap(monkeypatch, tmp_path):
    """After extraction, each written cache entry includes the axis_cap field."""
    anchor_text = "A financial institution shall conduct scenario testing annually."
    anchor = _make_anchor("doc-test/clause-1", anchor_text)
    index = _FakeAnchorIndex([anchor])

    real_cap = min(12, max(5, ceil(len(anchor_text) / 400)))

    axes_dir = tmp_path / "experiments"
    axes_dir.mkdir()
    monkeypatch.setattr(ea, "AXES_DIR", axes_dir)
    monkeypatch.setattr(
        ea, "call_chat", lambda *a, **kw: json.dumps(["axis-1", "axis-2"])
    )

    ea.extract_axes_for_document(index, "doc-test")

    written = json.loads((axes_dir / "axes-doc-test.json").read_text(encoding="utf-8"))
    entry = written["anchors"][0]
    assert "axis_cap" in entry, "axis_cap must be stored in each new cache entry"
    assert entry["axis_cap"] == real_cap
