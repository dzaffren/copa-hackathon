"""Tests for POST /api/workstreams/{id}/nodes/{node_id}/extract-concepts.

Extraction is synchronous and the only side effects — the axis cache and the
"axes extracted" activity entry — must land ONLY after a fully successful run.
The extractor is injected (`extract_axes_fn`) so no live model is reached; the
real `arm_g.extract_axes_for_document` is exercised in `test_arm_g.py`.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine import ws_anchors
from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_NODE = "bcbs-opres-2021"

AXES_A = ["operational resilience testing frequency", "scenario testing cadence"]
AXES_B = ["third-party dependency management", "scenario testing cadence"]
# Deduped union, first-seen order.
UNION = [
    "operational resilience testing frequency",
    "scenario testing cadence",
    "third-party dependency management",
]


def _anchor(anchor_id: str, document_id: str, text: str):
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id,
        "text": text,
        "doc_class": "semi-structured",
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


def _fake_extractor(axes_by_anchor: dict[str, list[str]], calls: list):
    """Stand in for arm_g.extract_axes_for_document: writes the same cache shape
    it would, so the route's read-back path is exercised for real."""

    def fn(anchor_index, document_id, axes_dir=None, **kwargs):
        calls.append(document_id)
        anchors = anchor_index.by_document(document_id)
        cache = {
            "document_id": document_id,
            "model": "fake-extractor",
            "anchors": [
                {
                    "anchor_id": a["anchor_id"],
                    "text_hash": "hash",
                    "axis_cap": 5,
                    "axes": axes_by_anchor.get(a["anchor_id"], []),
                }
                for a in anchors
            ],
        }
        axes_dir.mkdir(parents=True, exist_ok=True)
        (axes_dir / f"axes-{document_id}.json").write_text(
            json.dumps(cache), encoding="utf-8"
        )
        return {e["anchor_id"]: e["axes"] for e in cache["anchors"]}

    return fn


def _client(tmp_path, extractor=None, segmented=True):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    if segmented:
        ws_anchors.save(
            dst,
            _OPRES,
            _NODE,
            [
                _anchor(f"{_NODE}::p3", _NODE, "Principle 3 text."),
                _anchor(f"{_NODE}::p7", _NODE, "Principle 7 text."),
            ],
        )
    calls: list = []
    app = create_app(
        workstreams_dir=dst,
        extract_axes_fn=extractor
        or _fake_extractor({f"{_NODE}::p3": AXES_A, f"{_NODE}::p7": AXES_B}, calls),
    )
    return TestClient(app), dst, calls


def _graph(dst):
    return json.loads((dst / _OPRES / "graph.json").read_text(encoding="utf-8"))


def _node(dst, node_id=_NODE):
    return next(n for n in _graph(dst)["nodes"] if n["id"] == node_id)


def _extract(client, node_id=_NODE, workstream=_OPRES):
    return client.post(
        f"/api/workstreams/{workstream}/nodes/{node_id}/extract-concepts"
    )


# --- Happy path -------------------------------------------------------------


def test_extraction_returns_the_deduped_union_of_axes(tmp_path):
    client, dst, calls = _client(tmp_path)

    res = _extract(client)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["node_id"] == _NODE
    assert body["concepts"]["status"] == "extracted"
    assert body["concepts"]["axes"] == UNION
    assert len(calls) == 1
    assert (dst / _OPRES / "axes" / f"axes-{_NODE}.json").exists()


def test_extraction_appends_the_axes_extracted_activity_entry(tmp_path):
    client, dst, _ = _client(tmp_path)

    body = _extract(client).json()

    assert any(e.get("event") == "axes extracted" for e in body["recent_activity"])
    persisted = _node(dst)["recent_activity"]
    assert [e.get("event") for e in persisted].count("axes extracted") == 1


def test_node_detail_shows_the_axes_after_extraction(tmp_path):
    client, dst, _ = _client(tmp_path)
    _extract(client)

    detail = client.get(f"/api/workstreams/{_OPRES}/nodes/{_NODE}").json()

    assert detail["concepts"] == {"status": "extracted", "axes": UNION}


def test_a_second_extraction_does_not_duplicate_the_activity_entry(tmp_path):
    """Idempotent: re-running on unchanged anchors yields the same axes and the
    trail keeps exactly one "axes extracted" line."""
    client, dst, calls = _client(tmp_path)

    first = _extract(client).json()
    second = _extract(client).json()

    assert second["concepts"]["axes"] == first["concepts"]["axes"]
    persisted = _node(dst)["recent_activity"]
    assert [e.get("event") for e in persisted].count("axes extracted") == 1


# --- Failure paths ----------------------------------------------------------


def test_extraction_failure_is_atomic(tmp_path):
    """A failed extraction writes no axes and no activity entry — the node is
    exactly as it was, and the reader still says not_extracted."""

    def boom(anchor_index, document_id, axes_dir=None, **kwargs):
        raise RuntimeError("extraction service unavailable")

    client, dst, _ = _client(tmp_path, extractor=boom)
    before = _graph(dst)

    res = _extract(client)

    assert res.status_code == 502
    assert res.json()["code"] == "EXTRACTION_FAILED"
    assert not (dst / _OPRES / "axes").exists()
    assert _graph(dst) == before

    detail = client.get(f"/api/workstreams/{_OPRES}/nodes/{_NODE}").json()
    assert detail["concepts"] == {"status": "not_extracted", "axes": []}
    assert not any(
        e.get("event") == "axes extracted" for e in detail["recent_activity"]
    )


def test_an_unsegmented_node_is_rejected(tmp_path):
    client, dst, calls = _client(tmp_path, segmented=False)

    res = _extract(client)

    assert res.status_code == 409
    assert res.json()["code"] == "NOT_SEGMENTED"
    assert calls == []
    assert not (dst / _OPRES / "axes").exists()


def test_an_unknown_workstream_is_404(tmp_path):
    client, _, _ = _client(tmp_path)
    res = _extract(client, workstream="nope")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


def test_an_unknown_node_is_404(tmp_path):
    client, _, _ = _client(tmp_path)
    res = _extract(client, node_id="nope")
    assert res.status_code == 404
    assert res.json()["code"] == "NODE_NOT_FOUND"


# --- Node-detail contract ---------------------------------------------------


def test_node_detail_orders_the_four_blocks_and_stubs_metadata(tmp_path):
    """neighbours → recent activity → metadata → concepts, and metadata is the
    nine-field regulatory profile (not the axes)."""
    client, _, _ = _client(tmp_path)

    body = client.get(f"/api/workstreams/{_OPRES}/nodes/{_NODE}").json()
    keys = [
        k
        for k in body
        if k in {"first_order_neighbours", "recent_activity", "metadata", "concepts"}
    ]

    assert keys == [
        "first_order_neighbours",
        "recent_activity",
        "metadata",
        "concepts",
    ]
    assert body["concepts"] == {"status": "not_extracted", "axes": []}
    assert "status" in body["metadata"]
