"""Tests for the per-node anchor store (`engine/ws_anchors.py`).

Everything writes under `tmp_path` — the committed fixture store is never
touched. Anchor text deliberately carries Unicode (§, en-dash, U+2212) so the
UTF-8 / `ensure_ascii=False` guarantee is pinned rather than assumed.
"""

import json

import pytest

from engine import ws_anchors
from engine.anchors import Anchor


def _anchor(anchor_id: str, document_id: str, text: str = "") -> Anchor:
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id,
        "text": text or f"Text for {anchor_id}",
        "doc_class": "semi-structured",
        "document_id": document_id,
        "heading_path": ["Operational resilience"],
        "page_span": None,
        "parent_anchor": None,
    }


def test_anchors_path_is_per_node_under_the_workstream(tmp_path):
    path = ws_anchors.anchors_path(tmp_path, "opres-v2", "bcbs-opres-2021")
    assert path == tmp_path / "opres-v2" / "anchors" / "bcbs-opres-2021.json"


def test_save_then_load_round_trips(tmp_path):
    anchors = [
        _anchor("BCBS-OpRes-2021 §Principle 6", "bcbs-opres-2021"),
        _anchor("BCBS-OpRes-2021 §Principle 7", "bcbs-opres-2021"),
    ]
    ws_anchors.save(tmp_path, "opres-v2", "bcbs-opres-2021", anchors)

    assert ws_anchors.load(tmp_path, "opres-v2", "bcbs-opres-2021") == anchors


def test_save_preserves_unicode_unescaped(tmp_path):
    """§, en-dash and U+2212 must survive as real characters, not \\uXXXX."""
    text = "Clause §17.1 requires 3–5 days and a −2% buffer."
    ws_anchors.save(
        tmp_path, "opres-v2", "rmit", [_anchor("RMiT 17.1", "rmit", text=text)]
    )

    raw = ws_anchors.anchors_path(tmp_path, "opres-v2", "rmit").read_text(
        encoding="utf-8"
    )
    assert "§17.1" in raw
    assert "3–5" in raw
    assert "−2%" in raw
    assert "\\u00a7" not in raw
    assert ws_anchors.load(tmp_path, "opres-v2", "rmit")[0]["text"] == text


def test_load_on_an_unsegmented_node_raises(tmp_path):
    (tmp_path / "opres-v2").mkdir(parents=True)
    with pytest.raises(ws_anchors.AnchorsNotSegmentedError):
        ws_anchors.load(tmp_path, "opres-v2", "never-chunked")


def test_build_index_unions_every_nodes_anchors(tmp_path):
    ws_anchors.save(
        tmp_path,
        "opres-v2",
        "bcbs-opres-2021",
        [_anchor("BCBS §6", "bcbs-opres-2021"), _anchor("BCBS §7", "bcbs-opres-2021")],
    )
    ws_anchors.save(
        tmp_path, "opres-v2", "boe-chapter-3", [_anchor("BoE p.4", "boe-chapter-3")]
    )

    index = ws_anchors.build_index(tmp_path, "opres-v2")

    assert len(index) == 3
    assert index.get("BCBS §6") is not None
    assert index.get("BoE p.4") is not None
    # by_document keeps each node's anchors addressable on its own document_id
    assert len(index.by_document("bcbs-opres-2021")) == 2
    assert len(index.by_document("boe-chapter-3")) == 1


def test_build_index_on_a_workstream_with_no_anchors_is_empty(tmp_path):
    (tmp_path / "opres-v2").mkdir(parents=True)
    assert len(ws_anchors.build_index(tmp_path, "opres-v2")) == 0


def test_build_index_raises_on_a_duplicate_anchor_id_across_nodes(tmp_path):
    """A collision is a loud failure, not a silent drop — two documents must
    never claim the same anchor_id."""
    ws_anchors.save(tmp_path, "opres-v2", "node-a", [_anchor("SHARED §1", "node-a")])
    ws_anchors.save(tmp_path, "opres-v2", "node-b", [_anchor("SHARED §1", "node-b")])

    with pytest.raises(ValueError, match="Duplicate anchor_id"):
        ws_anchors.build_index(tmp_path, "opres-v2")


def test_save_is_idempotent_and_overwrites_rather_than_appends(tmp_path):
    ws_anchors.save(tmp_path, "opres-v2", "rmit", [_anchor("RMiT 17.1", "rmit")])
    ws_anchors.save(tmp_path, "opres-v2", "rmit", [_anchor("RMiT 17.2", "rmit")])

    loaded = ws_anchors.load(tmp_path, "opres-v2", "rmit")
    assert [a["anchor_id"] for a in loaded] == ["RMiT 17.2"]


def test_saved_file_is_a_bare_json_list(tmp_path):
    """The on-disk shape mirrors findings/{edge_id}.json — a bare list, so a
    human diff stays readable and no wrapper key needs migrating later."""
    ws_anchors.save(tmp_path, "opres-v2", "rmit", [_anchor("RMiT 17.1", "rmit")])
    raw = json.loads(
        ws_anchors.anchors_path(tmp_path, "opres-v2", "rmit").read_text(
            encoding="utf-8"
        )
    )
    assert isinstance(raw, list)
    assert raw[0]["anchor_id"] == "RMiT 17.1"
