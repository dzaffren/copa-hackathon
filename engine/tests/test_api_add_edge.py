"""Tests for POST /api/workstreams/{id}/edges — connect two existing nodes.

Until now an edge could only be declared while adding a NEW node, so two
documents already on the canvas could never be linked without removing and
re-adding one. This route closes that gap.

Every failure path must leave `graph.json` byte-identical: a refused connection
never half-writes.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"
_BCBS = "bcbs-opres-2021"
_HKMA = "hkma-spm-or2"


def _client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst)), dst


def _graph(dst, workstream=_OPRES):
    return json.loads((dst / workstream / "graph.json").read_text(encoding="utf-8"))


def _post(client, source, target, edge_type="references", workstream=_OPRES):
    return client.post(
        f"/api/workstreams/{workstream}/edges",
        json={
            "source_node_id": source,
            "target_node_id": target,
            "edge_type": edge_type,
        },
    )


# --- Happy path -------------------------------------------------------------


def test_connects_two_existing_anchor_nodes(tmp_path):
    client, dst = _client(tmp_path)
    before = len(_graph(dst)["edges"])

    res = _post(client, _BCBS, _HKMA, "references")

    assert res.status_code == 201, res.text
    body = res.json()
    assert body["source"] == _BCBS
    assert body["target"] == _HKMA
    assert body["edge_type"] == "references"
    assert body["analysed"] is False

    edges = _graph(dst)["edges"]
    assert len(edges) == before + 1
    assert any(e["id"] == body["id"] for e in edges)


def test_a_task_endpoint_is_forced_to_be_the_source(tmp_path):
    """The seeded convention is task → anchor: the Task Screen lists a task's
    OUTGOING edges, so a connection drawn toward the draft is stored reversed."""
    client, dst = _client(tmp_path)

    # `references` — the fixture already has task→BCBS as contributes-to.
    body = _post(client, _BCBS, _TASK, "references").json()

    assert body["source"] == _TASK
    assert body["target"] == _BCBS


def test_a_new_edge_survives_a_reload(tmp_path):
    client, dst = _client(tmp_path)
    created = _post(client, _BCBS, _HKMA).json()

    # The graph route projects the primary subgraph (task + its anchors), so
    # assert persistence on disk — the anchor↔anchor edge is outside that view.
    assert any(e["id"] == created["id"] for e in _graph(dst)["edges"])


def test_the_new_edge_is_not_analysed_and_writes_no_findings(tmp_path):
    client, dst = _client(tmp_path)
    body = _post(client, _BCBS, _HKMA).json()

    detail = client.get(f"/api/workstreams/{_OPRES}/edges/{body['id']}").json()
    assert detail["status"] == "not_analysed"
    assert detail["findings"] == []
    assert not (dst / _OPRES / "findings" / f"{body['id']}.json").exists()


def test_each_of_the_four_edge_types_is_accepted(tmp_path):
    for edge_type in ("supersedes", "references", "contributes-to", "parallel-to"):
        client, dst = _client(tmp_path / edge_type)
        res = _post(client, _BCBS, _HKMA, edge_type)
        assert res.status_code == 201, edge_type
        assert res.json()["edge_type"] == edge_type


def test_a_different_type_between_the_same_pair_is_allowed(tmp_path):
    client, dst = _client(tmp_path)
    first = _post(client, _BCBS, _HKMA, "references")
    assert first.status_code == 201

    second = _post(client, _BCBS, _HKMA, "parallel-to")

    assert second.status_code == 201
    assert second.json()["edge_type"] == "parallel-to"


# --- Failure paths ----------------------------------------------------------


def test_a_self_connection_is_refused(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _BCBS, _BCBS)

    assert res.status_code == 400
    assert res.json()["code"] == "SELF_LOOP"
    assert _graph(dst) == before


def test_an_exact_duplicate_is_refused(tmp_path):
    client, dst = _client(tmp_path)
    _post(client, _BCBS, _HKMA, "references")
    after_first = _graph(dst)

    res = _post(client, _BCBS, _HKMA, "references")

    assert res.status_code == 409
    assert res.json()["code"] == "DUPLICATE_EDGE"
    assert _graph(dst) == after_first


def test_a_seeded_edge_cannot_be_duplicated(tmp_path):
    """The fixture already links the task to BCBS with contributes-to."""
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _TASK, _BCBS, "contributes-to")

    assert res.status_code == 409
    assert res.json()["code"] == "DUPLICATE_EDGE"
    assert _graph(dst) == before


def test_an_unknown_edge_type_is_refused(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _BCBS, _HKMA, "supersedes-ish")

    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_EDGE_TYPE"
    assert _graph(dst) == before


def test_an_unknown_endpoint_is_404(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    missing_target = _post(client, _BCBS, "nope")
    missing_source = _post(client, "nope", _BCBS)

    assert missing_target.status_code == 404
    assert missing_target.json()["code"] == "NODE_NOT_FOUND"
    assert "nope" in missing_target.json()["message"]
    assert missing_source.status_code == 404
    assert _graph(dst) == before


def test_missing_fields_are_refused(tmp_path):
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = client.post(
        f"/api/workstreams/{_OPRES}/edges",
        json={"source_node_id": _BCBS},
    )

    assert res.status_code == 400
    assert res.json()["code"] == "EDGE_REQUIRED"
    assert _graph(dst) == before


def test_an_unknown_workstream_is_404(tmp_path):
    client, _ = _client(tmp_path)
    res = _post(client, _BCBS, _HKMA, workstream="nope")
    assert res.status_code == 404
    assert res.json()["code"] == "WORKSTREAM_NOT_FOUND"


def test_a_cross_workstream_endpoint_is_not_found(tmp_path):
    """Same-workstream only: a node from another workstream is simply unknown
    here (cross-workstream linkage is a separate spec)."""
    client, dst = _client(tmp_path)
    before = _graph(dst)

    res = _post(client, _BCBS, "of-ed-2025")

    assert res.status_code == 404
    assert res.json()["code"] == "NODE_NOT_FOUND"
    assert _graph(dst) == before
