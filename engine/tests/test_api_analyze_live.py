import json
from pathlib import Path

from fastapi.testclient import TestClient

from engine.api import create_app

CONN = {
    "summary": "Both require BCP.",
    "label": "aligns-with",
    "sentiment": None,
    "source_clauses": [{"clause_number": "RMiT 10.50", "text": "cloud..."}],
    "target_clauses": [{"clause_number": "Operational Resilience 4.3", "text": "bcp..."}],
    "scope_note": None,
    "supported": True,
}


def _ws(tmp_path: Path) -> Path:
    root = tmp_path / "workstreams"
    ws = root / "opres-v2"
    (ws / "findings").mkdir(parents=True)
    (ws / "graph.json").write_text(json.dumps({
        "nodes": [
            {"id": "opres-pd-v0-3", "title": "OpRes", "node_type": "task",
             "document_id": "opres-v1-2025-draft"},
            {"id": "rmit-pd-2025", "title": "RMiT", "node_type": "internal-published",
             "document_id": "rmit-v2-2025"},
            {"id": "bcbs", "title": "BCBS", "node_type": "international-standard"},
        ],
        "edges": [
            {"id": "e-live", "source": "opres-pd-v0-3", "target": "rmit-pd-2025",
             "edge_type": "parallel-to"},
            {"id": "e-noref", "source": "opres-pd-v0-3", "target": "bcbs",
             "edge_type": "contributes-to"},
        ],
    }), "utf-8")
    (ws / "workstream.json").write_text(json.dumps(
        {"id": "opres-v2", "name": "OpRes", "primary_task_id": "opres-pd-v0-3"}), "utf-8")
    return root


def _client(tmp_path, fn):
    return TestClient(create_app(workstreams_dir=_ws(tmp_path), find_connections_fn=fn))


def test_live_analyze_saves_findings_and_returns_analysed(tmp_path):
    def fake_fn(a, b, idx):
        assert a == "opres-v1-2025-draft" and b == "rmit-v2-2025"  # source first
        return {"connections": [CONN], "unsupported": []}

    client = _client(tmp_path, fake_fn)
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "analysed"
    assert body["findings_count"] == 1
    assert body["findings"][0]["review_state"] == "pending"


def test_edge_with_unmapped_node_is_not_analysable(tmp_path):
    def fake_fn(a, b, idx):
        raise AssertionError("must not be called")

    client = _client(tmp_path, fake_fn)
    r = client.post("/api/workstreams/opres-v2/edges/e-noref/analyze")
    assert r.status_code == 409
    assert r.json()["code"] == "NOT_ANALYSABLE"


def test_finder_failure_returns_502_and_writes_nothing(tmp_path):
    def boom(a, b, idx):
        raise RuntimeError("no creds")

    root = _ws(tmp_path)
    client = TestClient(create_app(workstreams_dir=root, find_connections_fn=boom))
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 502
    assert r.json()["code"] == "ANALYZE_FAILED"
    assert not (root / "opres-v2" / "findings" / "e-live.json").exists()
