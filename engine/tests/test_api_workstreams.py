"""Tests for the Workstream Brain — Graph Screen API routes.

Each test copies the real seeded `data/workstreams/` fixtures into a `tmp_path`
and points `create_app(workstreams_dir=...)` at the copy. GET tests therefore
double as integrity checks on the seeded demo data, while the mutating POST /
analyze tests touch only the throwaway copy. No network, credentials, or real
artifacts are required — the clause index / graph are empty stubs the workstream
routes never touch.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.clauses import ClauseIndex
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"
_BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"  # seeded analysed edge (3 findings)
_FSB_EDGE = "e-opres_v0_3--fsb_3rd_party"  # unanalysed; the analyze demo pair


def _boom(*_args, **_kwargs):  # pragma: no cover - must never be called
    raise AssertionError("finder_fn must not be called by the workstream routes")


def _make_client(tmp_path, finder_fn=None) -> tuple[TestClient, "object"]:
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    app = create_app(
        clause_index=ClauseIndex({}),
        graph={"nodes": [], "edges": []},
        workstreams_dir=dst,
        finder_fn=finder_fn,
        analyze_delay=0,
    )
    return TestClient(app), dst


def _graph_on_disk(dst, workstream=_OPRES) -> dict:
    return json.loads((dst / workstream / "graph.json").read_text(encoding="utf-8"))


# --- GET /api/workstreams ---------------------------------------------------


def test_GET_workstreams_lists_three_seeded_workstreams(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get("/api/workstreams").json()
    ids = {w["id"] for w in body["workstreams"]}
    assert {"opres-v2", "outsourcing-v2", "rmit-v2-2025"} <= ids
    roles = {w["id"]: w["role"] for w in body["workstreams"]}
    assert roles["opres-v2"] == "own"
    assert roles["outsourcing-v2"] == "review"
    assert roles["rmit-v2-2025"] == "delivered"


# --- GET /api/workstreams/{id}/graph ----------------------------------------


def test_GET_graph_returns_seeded_opres_workstream(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/graph").json()
    assert len(body["nodes"]) == 7  # one PD + six anchors (sibling draft excluded)
    assert len(body["edges"]) == 6
    assert body["primary_task_id"] == _TASK
    edges = {e["id"]: e for e in body["edges"]}
    assert edges[_BCBS_EDGE]["analysed"] is True
    assert edges[_BCBS_EDGE]["findings_count"] == 3
    assert edges[_FSB_EDGE]["analysed"] is False
    # Nodes carry the type + issuer/short_type the canvas + node panel render.
    node = next(n for n in body["nodes"] if n["id"] == "bcbs-opres-2021")
    assert node["node_type"] == "international-standard"
    assert node["issuer"] == "BCBS"


def test_GET_graph_unknown_workstream_returns_404(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get("/api/workstreams/nope/graph")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- GET /api/workstreams/{id}/nodes/{node_id} ------------------------------


def test_GET_node_detail_returns_first_order_neighbours_for_task_node(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/nodes/{_TASK}").json()
    assert body["node_type"] == "task"
    assert len(body["first_order_neighbours"]) == 6
    assert body["issuer"] == "BNM"
    assert body["second_order_neighbours"] == {
        "status": "placeholder",
        "message": "N/A in demo",
    }
    assert body["concepts"]["status"] == "placeholder"
    assert len(body["recent_activity"]) >= 1


def test_GET_node_detail_resource_node_lists_only_primary_task(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/nodes/bcbs-opres-2021").json()
    assert body["node_type"] == "international-standard"
    neighbour_ids = [n["id"] for n in body["first_order_neighbours"]]
    # bcbs also has an edge to the empty sibling draft, but the node panel is
    # scoped to the primary subgraph, so only the v0.3 draft shows.
    assert neighbour_ids == [_TASK]


def test_GET_node_detail_unknown_node_returns_404(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/{_OPRES}/nodes/ghost")
    assert res.status_code == 404
    assert res.json()["code"] == "NODE_NOT_FOUND"


# --- GET /api/workstreams/{id}/edges/{edge_id} ------------------------------


def test_GET_edge_detail_returns_not_analysed_when_findings_file_absent(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}").json()
    assert body["status"] == "not_analysed"
    assert body["findings"] == []
    assert body["edge_type"] == "contributes-to"
    assert body["source"]["id"] == _TASK
    assert body["target"]["id"] == "fsb-3rd-party"


def test_GET_edge_detail_returns_analysed_with_findings_when_file_present(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/edges/{_BCBS_EDGE}").json()
    assert body["status"] == "analysed"
    assert len(body["findings"]) == 3
    for finding in body["findings"]:
        assert finding["label"]
        assert finding["summary"]


def test_GET_edge_detail_unknown_edge_returns_404_EDGE_NOT_FOUND(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.get(f"/api/workstreams/{_OPRES}/edges/e-nope")
    assert res.status_code == 404
    assert res.json()["code"] == "EDGE_NOT_FOUND"


# --- POST /api/workstreams/{id}/nodes ---------------------------------------


def test_POST_node_rejects_empty_edges_400_EDGE_REQUIRED(tmp_path):
    client, dst = _make_client(tmp_path)
    before = len(_graph_on_disk(dst)["nodes"])
    res = client.post(
        f"/api/workstreams/{_OPRES}/nodes",
        json={"node_type": "international-standard", "title": "X", "edges": []},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "EDGE_REQUIRED"
    assert len(_graph_on_disk(dst)["nodes"]) == before  # graph.json untouched


def test_POST_node_rejects_invalid_node_type_400_INVALID_NODE_TYPE(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        f"/api/workstreams/{_OPRES}/nodes",
        json={
            "node_type": "cluster",
            "title": "X",
            "edges": [{"target_node_id": _TASK, "edge_type": "contributes-to"}],
        },
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_NODE_TYPE"


def test_POST_node_rejects_invalid_edge_type_400_INVALID_EDGE_TYPE(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        f"/api/workstreams/{_OPRES}/nodes",
        json={
            "node_type": "international-standard",
            "title": "X",
            "edges": [{"target_node_id": _TASK, "edge_type": "differs-on"}],
        },
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_EDGE_TYPE"


def test_POST_node_writes_graph_and_returns_created_edges(tmp_path):
    client, dst = _make_client(tmp_path)
    res = client.post(
        f"/api/workstreams/{_OPRES}/nodes",
        json={
            "node_type": "international-standard",
            "title": "BCBS OpRes 2021 Companion Guide",
            "description": "Companion to the 2021 principles",
            "edges": [{"target_node_id": _TASK, "edge_type": "contributes-to"}],
        },
    )
    assert res.status_code == 201
    payload = res.json()
    new_id = payload["id"]
    assert payload["node_type"] == "international-standard"
    assert len(payload["created_edges"]) == 1
    # The task is kept as the edge SOURCE (seeded convention: task → anchor).
    assert payload["created_edges"][0]["source"] == _TASK
    assert payload["created_edges"][0]["target"] == new_id
    # Persisted: reload graph.json and confirm the node + edge landed.
    disk = _graph_on_disk(dst)
    assert any(n["id"] == new_id for n in disk["nodes"])
    # And it now shows on the canvas subgraph (it connects to the primary task).
    graph = client.get(f"/api/workstreams/{_OPRES}/graph").json()
    assert any(n["id"] == new_id for n in graph["nodes"])
    # Cross-screen: the new anchor also appears as a Task Screen neighbour,
    # which reads the task node's OUTGOING edges only.
    task = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}").json()
    assert new_id in {n["node_id"] for n in task["neighbours"]}


def test_POST_node_rejects_edge_to_unknown_target_400_INVALID_EDGE_TARGET(tmp_path):
    client, dst = _make_client(tmp_path)
    before = len(_graph_on_disk(dst)["nodes"])
    res = client.post(
        f"/api/workstreams/{_OPRES}/nodes",
        json={
            "node_type": "international-standard",
            "title": "X",
            "edges": [{"target_node_id": "ghost-node", "edge_type": "contributes-to"}],
        },
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_EDGE_TARGET"
    assert len(_graph_on_disk(dst)["nodes"]) == before  # graph.json untouched


def test_POST_node_unknown_workstream_returns_404_WORKSTREAM_NOT_FOUND(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.post(
        "/api/workstreams/nope/nodes",
        json={
            "node_type": "international-standard",
            "title": "X",
            "edges": [{"target_node_id": _TASK, "edge_type": "contributes-to"}],
        },
    )
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


# --- POST /api/workstreams/{id}/edges/{edge_id}/analyze ---------------------


def test_POST_edge_analyze_replays_canned_findings_for_demo_pair(tmp_path):
    # finder_fn is wired to explode; the demo pair must NOT reach it.
    client, _ = _make_client(tmp_path, finder_fn=_boom)
    res = client.post(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}/analyze")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "analysed"
    assert body["findings_count"] == 3
    assert body["findings"][0]["label"] == "aligns-with"


def test_POST_edge_analyze_writes_findings_file_and_flips_edge_analysed_flag(tmp_path):
    client, dst = _make_client(tmp_path)
    # Before: unanalysed.
    assert (
        client.get(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}").json()["status"]
        == "not_analysed"
    )
    client.post(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}/analyze")
    # After: findings file exists and every read reports analysed.
    assert (dst / _OPRES / "findings" / f"{_FSB_EDGE}.json").exists()
    graph = client.get(f"/api/workstreams/{_OPRES}/graph").json()
    fsb_edge = next(e for e in graph["edges"] if e["id"] == _FSB_EDGE)
    assert fsb_edge["analysed"] is True
    assert fsb_edge["findings_count"] == 3
    assert (
        client.get(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}").json()["status"]
        == "analysed"
    )
