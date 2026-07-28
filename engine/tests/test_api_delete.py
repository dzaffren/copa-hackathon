"""Tests for DELETE node / DELETE edge.

Deletion cascades so nothing is left referencing something that no longer
exists: removing a node also removes every edge touching it, those edges'
findings, and the node's own anchors and axis cache. The focal task node is
protected — it is the workstream's anchor and `primary_task_id` points at it.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine import ws_anchors
from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"
_BCBS = "bcbs-opres-2021"
_BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"


def _anchor(anchor_id: str, document_id: str):
    return {
        "anchor_id": anchor_id,
        "anchor_label": anchor_id,
        "text": f"Text of {anchor_id}.",
        "doc_class": "semi-structured",
        "document_id": document_id,
        "heading_path": [],
        "page_span": None,
        "parent_anchor": None,
    }


def _client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    # Give the BCBS node the artefacts a chunked node would carry.
    ws_anchors.save(dst, _OPRES, _BCBS, [_anchor("BCBS 1.1", _BCBS)])
    axes = dst / _OPRES / "axes"
    axes.mkdir(parents=True, exist_ok=True)
    (axes / f"axes-{_BCBS}.json").write_text(
        json.dumps({"document_id": _BCBS, "model": "m", "anchors": []}),
        encoding="utf-8",
    )
    return TestClient(create_app(workstreams_dir=dst)), dst


def _graph(dst, workstream=_OPRES):
    return json.loads((dst / workstream / "graph.json").read_text(encoding="utf-8"))


def _ids(dst):
    g = _graph(dst)
    return {n["id"] for n in g["nodes"]}, {e["id"] for e in g["edges"]}


# --- DELETE a node ----------------------------------------------------------


def test_deleting_a_node_cascades_to_its_edges_and_artefacts(tmp_path):
    client, dst = _client(tmp_path)
    assert (dst / _OPRES / "findings" / f"{_BCBS_EDGE}.json").exists()

    res = client.delete(f"/api/workstreams/{_OPRES}/nodes/{_BCBS}")

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["id"] == _BCBS
    assert _BCBS_EDGE in body["removed_edges"]

    nodes, edges = _ids(dst)
    assert _BCBS not in nodes
    assert _BCBS_EDGE not in edges
    # Nothing left pointing at a node that is gone.
    assert not (dst / _OPRES / "findings" / f"{_BCBS_EDGE}.json").exists()
    assert not ws_anchors.anchors_path(dst, _OPRES, _BCBS).exists()
    assert not (dst / _OPRES / "axes" / f"axes-{_BCBS}.json").exists()


def test_deleting_a_node_leaves_every_other_node_and_edge_intact(tmp_path):
    client, dst = _client(tmp_path)
    before_nodes, before_edges = _ids(dst)

    client.delete(f"/api/workstreams/{_OPRES}/nodes/{_BCBS}")

    nodes, edges = _ids(dst)
    # Only the target node and the edges touching it went.
    assert nodes == before_nodes - {_BCBS}
    assert all(_BCBS not in e for e in edges)
    assert _TASK in nodes


def test_a_deleted_node_is_gone_from_the_graph_route(tmp_path):
    client, dst = _client(tmp_path)
    client.delete(f"/api/workstreams/{_OPRES}/nodes/{_BCBS}")

    body = client.get(f"/api/workstreams/{_OPRES}/graph").json()

    assert _BCBS not in [n["id"] for n in body["nodes"]]
    assert client.get(f"/api/workstreams/{_OPRES}/nodes/{_BCBS}").status_code == 404


def test_the_focal_task_node_cannot_be_deleted(tmp_path):
    """It is the workstream's anchor: primary_task_id points at it and every
    document connects to it."""
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = client.delete(f"/api/workstreams/{_OPRES}/nodes/{_TASK}")

    assert res.status_code == 409
    assert res.json()["code"] == "FOCAL_NODE_PROTECTED"
    assert _graph(dst) == before


def test_deleting_an_unknown_node_is_404(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = client.delete(f"/api/workstreams/{_OPRES}/nodes/ghost")

    assert res.status_code == 404
    assert res.json()["code"] == "NODE_NOT_FOUND"
    assert _graph(dst) == before


def test_deleting_a_node_in_an_unknown_workstream_is_404(tmp_path):
    client, _ = _client(tmp_path)
    res = client.delete(f"/api/workstreams/nope/nodes/{_BCBS}")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- DELETE an edge ---------------------------------------------------------


def test_deleting_an_edge_removes_it_and_its_findings(tmp_path):
    client, dst = _client(tmp_path)
    assert (dst / _OPRES / "findings" / f"{_BCBS_EDGE}.json").exists()

    res = client.delete(f"/api/workstreams/{_OPRES}/edges/{_BCBS_EDGE}")

    assert res.status_code == 200, res.text
    assert res.json()["id"] == _BCBS_EDGE
    _, edges = _ids(dst)
    assert _BCBS_EDGE not in edges
    assert not (dst / _OPRES / "findings" / f"{_BCBS_EDGE}.json").exists()


def test_deleting_an_edge_keeps_both_endpoint_nodes(tmp_path):
    """Removing a linkage un-links two documents; it does not remove them."""
    client, dst = _client(tmp_path)

    client.delete(f"/api/workstreams/{_OPRES}/edges/{_BCBS_EDGE}")

    nodes, _ = _ids(dst)
    assert _TASK in nodes
    assert _BCBS in nodes
    # The document's own passages survive — only the linkage went.
    assert ws_anchors.anchors_path(dst, _OPRES, _BCBS).exists()


def test_deleting_an_unknown_edge_is_404(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = client.delete(f"/api/workstreams/{_OPRES}/edges/e-nope--nope")

    assert res.status_code == 404
    assert res.json()["code"] == "EDGE_NOT_FOUND"
    assert _graph(dst) == before


def test_an_unanalysed_edge_deletes_cleanly(tmp_path):
    """No findings file to remove is the common case, not an error."""
    client, dst = _client(tmp_path)
    fsb = "e-opres_v0_3--fsb_3rd_party"
    assert not (dst / _OPRES / "findings" / f"{fsb}.json").exists()

    res = client.delete(f"/api/workstreams/{_OPRES}/edges/{fsb}")

    assert res.status_code == 200
    _, edges = _ids(dst)
    assert fsb not in edges
