"""Tests for the Workstream Brain — Graph Screen API routes.

Each test copies the real seeded `data/workstreams/` fixtures into a `tmp_path`
and points `create_app(workstreams_dir=...)` at the copy. GET tests therefore
double as integrity checks on the seeded demo data, while the mutating POST /
analyze tests touch only the throwaway copy. No network, credentials, or real
artifacts are required — the API is a projection over the fixture store alone.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"
_BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"  # seeded analysed edge (3 findings)
_FSB_EDGE = "e-opres_v0_3--fsb_3rd_party"  # unanalysed; the analyze demo pair


def _make_client(tmp_path, find_connections_fn=None) -> tuple[TestClient, "object"]:
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    kwargs = {}
    if find_connections_fn is not None:
        kwargs["find_connections_fn"] = find_connections_fn
    app = create_app(workstreams_dir=dst, **kwargs)
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
    assert len(body["nodes"]) == 8  # one PD + seven anchors (sibling draft excluded)
    assert len(body["edges"]) == 7
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
    assert len(body["first_order_neighbours"]) == 7
    assert body["issuer"] == "BNM"
    assert body["second_order_neighbours"] == {
        "status": "placeholder",
        "message": "N/A in demo",
    }
    assert len(body["recent_activity"]) >= 1


def test_GET_node_detail_concepts_placeholder_when_not_enriched(tmp_path):
    """A node the offline enrichment script has not touched still gets the
    MVP1 placeholder — never an error, never a guess."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/nodes/bcbs-opres-2021").json()
    assert body["concepts"] == {
        "status": "placeholder",
        "message": "Concept extraction not enabled in MVP1",
    }
    assert body["ismp_classification"] is None
    assert body["pursuant_to"] is None


def test_GET_node_detail_concepts_available_when_offline_enriched(tmp_path):
    """opres-pd-v0-3 has been through scripts/enrich_node_metadata.py: its
    statutory basis is derived from the real, supported FSA finding, and its
    owner is reused verbatim rather than re-derived."""
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/nodes/{_TASK}").json()
    assert body["concepts"]["status"] == "available"
    assert body["concepts"]["policy_owner"] == "Aisyah R."
    assert body["concepts"]["empowerment_framework"] == (
        "This policy document is issued pursuant to section 143(2) of the "
        "Financial Services Act 2013."
    )
    # A field the enrichment script could not honestly derive stays null.
    assert body["concepts"]["applicability"] is None
    assert body["pursuant_to"] == "FSA 2013 §143"


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


# --- GET/PATCH /api/workstreams/{id}/tasks/{node_id}/workflow (Maker-Checker) -


def test_GET_task_includes_default_draft_workflow_when_never_touched(tmp_path):
    client, _ = _make_client(tmp_path)
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}").json()
    assert body["workflow"] == {
        "status": "draft",
        "checker": None,
        "approved_by": None,
        "approved_at": None,
    }


def test_PATCH_workflow_to_pending_review_records_the_checker_and_persists(tmp_path):
    client, dst = _make_client(tmp_path)
    res = client.patch(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/workflow",
        json={"status": "pending_review", "actor_id": "fm"},
    )
    assert res.status_code == 200
    workflow = res.json()["workflow"]
    assert workflow["status"] == "pending_review"
    assert workflow["checker"] == {"id": "fm", "name": "Farid M."}

    # Persisted — a fresh GET on the task sees the same workflow.
    body = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}").json()
    assert body["workflow"] == workflow
    on_disk = json.loads(
        (dst / _OPRES / "task_workflow" / f"{_TASK}.json").read_text(encoding="utf-8")
    )
    assert on_disk == workflow


def test_PATCH_workflow_to_approved_records_who_and_when(tmp_path):
    client, _ = _make_client(tmp_path)
    client.patch(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/workflow",
        json={"status": "pending_review", "actor_id": "fm"},
    )
    res = client.patch(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/workflow",
        json={"status": "approved", "actor_id": "fm"},
    )
    workflow = res.json()["workflow"]
    assert workflow["status"] == "approved"
    assert workflow["approved_by"] == {"id": "fm", "name": "Farid M."}
    assert workflow["approved_at"] is not None


def test_PATCH_workflow_rejects_unknown_state_400_INVALID_WORKFLOW_STATE(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.patch(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/workflow",
        json={"status": "done", "actor_id": "fm"},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_WORKFLOW_STATE"


def test_PATCH_workflow_rejects_unknown_actor_400_INVALID_ACTOR(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.patch(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/workflow",
        json={"status": "pending_review", "actor_id": "ghost"},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_ACTOR"


def test_PATCH_workflow_on_non_task_node_returns_400_NOT_A_TASK(tmp_path):
    client, _ = _make_client(tmp_path)
    res = client.patch(
        f"/api/workstreams/{_OPRES}/tasks/bcbs-opres-2021/workflow",
        json={"status": "pending_review", "actor_id": "fm"},
    )
    assert res.status_code == 400
    assert res.json()["code"] == "NOT_A_TASK"


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


def test_POST_edge_analyze_409_when_a_node_has_no_ingested_document(tmp_path):
    # The old canned-demo-pair replay is retired: `create_app` now takes a live
    # `find_connections_fn` seam, and the route only reaches it when both edge
    # endpoints carry a `document_id`. Neither opres-pd-v0-3 nor fsb-3rd-party
    # has one in the seeded fixture, so this edge is NOT_ANALYSABLE rather than
    # a path that replays canned findings — see test_api_analyze_live.py for the
    # live success/failure paths on a fixture built with `document_id`s.
    def boom(a, b, idx):
        raise AssertionError("must not reach the finder when a node is unmapped")

    client, _ = _make_client(tmp_path, find_connections_fn=boom)
    res = client.post(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}/analyze")
    assert res.status_code == 409
    assert res.json()["code"] == "NOT_ANALYSABLE"


def test_POST_edge_analyze_writes_findings_file_and_flips_edge_analysed_flag(tmp_path):
    def stub(a, b, idx):
        return {
            "connections": [
                {
                    "summary": "stubbed",
                    "label": "aligns-with",
                    "sentiment": None,
                    "scope_note": None,
                    "supported": True,
                    "source_clauses": [],
                    "target_clauses": [],
                }
            ],
            "unsupported": [],
        }

    client, dst = _make_client(tmp_path, find_connections_fn=stub)
    # opres-pd-v0-3 -> rmit-pd-2025 is genuinely analysable: both carry a
    # document_id AND they differ (opres-v1-2025-draft vs rmit-v2-2025). It is
    # seeded analysed, so delete its findings file to establish the unanalysed
    # precondition. (The opres-dp edge is a same-document self-comparison — 409.)
    edge_id = "e-opres_v0_3--rmit_pd_2025"
    (dst / _OPRES / "findings" / f"{edge_id}.json").unlink()
    # Before: unanalysed.
    assert (
        client.get(f"/api/workstreams/{_OPRES}/edges/{edge_id}").json()["status"]
        == "not_analysed"
    )
    res = client.post(f"/api/workstreams/{_OPRES}/edges/{edge_id}/analyze")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "analysed"
    assert body["findings_count"] == 1
    # After: findings file exists and every read reports analysed.
    assert (dst / _OPRES / "findings" / f"{edge_id}.json").exists()
    graph = client.get(f"/api/workstreams/{_OPRES}/graph").json()
    edge = next(e for e in graph["edges"] if e["id"] == edge_id)
    assert edge["analysed"] is True
    assert edge["findings_count"] == 1
    assert (
        client.get(f"/api/workstreams/{_OPRES}/edges/{edge_id}").json()["status"]
        == "analysed"
    )
