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
                        "edge_type": "contributes-to",
                    },
                    {
                        "id": "e-noref",
                        "source": "opres-pd-v0-3",
                        "target": "noref",
                        "edge_type": "contributes-to",
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
