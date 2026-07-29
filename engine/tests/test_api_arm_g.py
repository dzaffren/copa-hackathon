"""Tests for the analyze route wired onto the Arm G pipeline (Story 3).

The route now calls the injectable `run_arm_g_fn` seam — `(src_doc, tgt_doc) ->
{"connections", "unsupported", "trace"}` — instead of the old
`find_connections_fn`. These tests inject a stub for that seam so no anchor
index, model, or credentials are needed; each test builds a throwaway
`workstreams_dir` under `tmp_path`. The `find_connections_fn` seam is retained
as the rollback path and is exercised in `test_api_analyze_live.py`.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from engine.api import create_app

CONN = {
    "summary": "Both require BCP.",
    "label": "aligns-with",
    "sentiment": None,
    "source_clauses": [{"clause_number": "RMiT 10.50", "text": "cloud..."}],
    "target_clauses": [
        {"clause_number": "Operational Resilience 4.3", "text": "bcp..."}
    ],
    "scope_note": None,
    "supported": True,
}


def _ws(tmp_path: Path) -> Path:
    root = tmp_path / "workstreams"
    ws = root / "opres-v2"
    (ws / "findings").mkdir(parents=True)
    (ws / "graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "opres-pd-v0-3",
                        "title": "OpRes",
                        "node_type": "task",
                        "document_id": "opres-v1-2025-draft",
                    },
                    {
                        "id": "rmit-pd-2025",
                        "title": "RMiT",
                        "node_type": "internal-published",
                        "document_id": "rmit-v2-2025",
                    },
                    {
                        "id": "bcbs",
                        "title": "BCBS",
                        "node_type": "international-standard",
                        "document_id": "bcbs-opres-2021",
                    },
                    {
                        "id": "noref",
                        "title": "NoRef",
                        "node_type": "international-standard",
                    },
                ],
                "edges": [
                    {
                        "id": "e-live",
                        "source": "opres-pd-v0-3",
                        "target": "rmit-pd-2025",
                        "edge_type": "parallel-to",
                    },
                    {
                        "id": "e-sibling",
                        "source": "opres-pd-v0-3",
                        "target": "bcbs",
                        "edge_type": "references",
                    },
                    {
                        "id": "e-noref",
                        "source": "opres-pd-v0-3",
                        "target": "noref",
                        "edge_type": "references",
                    },
                ],
            }
        ),
        "utf-8",
    )
    (ws / "workstream.json").write_text(
        json.dumps(
            {"id": "opres-v2", "name": "OpRes", "primary_task_id": "opres-pd-v0-3"}
        ),
        "utf-8",
    )
    return root


def _client(tmp_path, fn):
    return TestClient(create_app(workstreams_dir=_ws(tmp_path), run_arm_g_fn=fn))


def test_analyze_returns_findings_through_arm_g_seam(tmp_path):
    def fake_fn(a, b):
        assert a == "opres-v1-2025-draft" and b == "rmit-v2-2025"  # source first
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    client = _client(tmp_path, fake_fn)
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"id", "status", "findings", "findings_count"}
    assert body["id"] == "e-live"
    assert body["status"] == "analysed"
    assert body["findings_count"] == 1
    assert body["findings"][0]["review_state"] == "pending"


def test_route_calls_the_injected_stub_not_the_real_pipeline(tmp_path):
    # The stub returns a FIXED set of two findings for any input; the route must
    # honour it (never reach the real Arm G pipeline / anchor index) and report
    # a count that matches the stub's output.
    calls = []

    def stub(a, b):
        calls.append((a, b))
        return {"connections": [CONN, CONN], "unsupported": [], "trace": {}}

    client = _client(tmp_path, stub)
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 200
    assert calls == [("opres-v1-2025-draft", "rmit-v2-2025")]
    assert r.json()["findings_count"] == 2


def test_empty_connections_yield_no_linkages_found_and_write_nothing(tmp_path):
    root = _ws(tmp_path)
    client = TestClient(
        create_app(
            workstreams_dir=root,
            run_arm_g_fn=lambda a, b: {
                "connections": [],
                "unsupported": [],
                "trace": {},
            },
        )
    )
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 200
    assert r.json()["status"] == "no_linkages_found"
    assert r.json()["findings_count"] == 0
    assert not (root / "opres-v2" / "findings" / "e-live.json").exists()


def test_edge_with_unmapped_node_is_not_analysable(tmp_path):
    def stub(a, b):
        raise AssertionError("must not reach the pipeline when a node is unmapped")

    client = _client(tmp_path, stub)
    r = client.post("/api/workstreams/opres-v2/edges/e-noref/analyze")
    assert r.status_code == 409
    assert r.json()["code"] == "NOT_ANALYSABLE"


def test_reanalyze_replaces_only_the_target_edge_findings_file(tmp_path):
    # Analysing e-live must never touch a sibling edge's findings file.
    root = _ws(tmp_path)
    client = TestClient(
        create_app(
            workstreams_dir=root,
            run_arm_g_fn=lambda a, b: {
                "connections": [CONN],
                "unsupported": [],
                "trace": {},
            },
        )
    )
    findings_dir = root / "opres-v2" / "findings"
    # Seed the sibling edge with a pre-existing findings file; capture its bytes.
    sibling = findings_dir / "e-sibling.json"
    sibling.write_text(json.dumps([{"id": "pre-existing"}]), "utf-8")
    sibling_before = sibling.read_bytes()

    # First analysis of the target edge writes its own file.
    client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    live = findings_dir / "e-live.json"
    assert live.exists()

    # Re-analysing the target edge replaces only its own file; the sibling's
    # stored findings are left byte-for-byte untouched.
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 200
    assert r.json()["status"] == "analysed"
    assert sibling.read_bytes() == sibling_before


def test_coverage_pass_failure_returns_502_and_writes_nothing(tmp_path):
    # A whole-doc coverage-pass failure surfaces as an error with NO partial
    # write; the edge stays unanalysed and re-analysable.
    def boom(a, b):
        raise RuntimeError("coverage pass failed")

    root = _ws(tmp_path)
    client = TestClient(create_app(workstreams_dir=root, run_arm_g_fn=boom))
    r = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")
    assert r.status_code == 502
    assert r.json()["code"] == "ANALYZE_FAILED"
    assert not (root / "opres-v2" / "findings" / "e-live.json").exists()
    # Edge remains unanalysed.
    detail = client.get("/api/workstreams/opres-v2/edges/e-live").json()
    assert detail["status"] == "not_analysed"
