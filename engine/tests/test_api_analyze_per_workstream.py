"""Analysis reads the workstream's OWN passages, not a shared pre-built store.

Before this, the default `run_arm_g_fn` loaded one global
`data/artifacts/anchor-index.json`, so a document a drafter added and chunked
inside the app was invisible to analysis. These tests pin the repointed
behaviour: with per-workstream anchors present and NO artifacts file at all, an
edge is still analysable, and the axis cache used is the workstream's own (so a
cache warmed by "Extract concepts" is reused rather than re-derived).

`engine.arm_g.run_arm_g` itself is stubbed — the pipeline's internals are
covered in `test_arm_g.py`; what matters here is which index and axes dir the
route hands it.
"""

import json
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from engine import ws_anchors
import engine.api as api_module
from engine.api import create_app

CONN = {
    "summary": "Both require scenario testing.",
    "label": "aligns-with",
    "sentiment": None,
    "source_clauses": [{"clause_number": "OpRes 1.1", "text": "testing..."}],
    "target_clauses": [{"clause_number": "BCBS 1.1", "text": "testing..."}],
    "scope_note": None,
    "supported": True,
}


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


def _ws(tmp_path: Path) -> Path:
    """A workstream whose two documents were chunked in-app: their anchors live
    per-node under the workstream, and there is no artifacts store anywhere."""
    root = tmp_path / "workstreams"
    ws = root / "opres-v2"
    (ws / "findings").mkdir(parents=True)
    (ws / "graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "opres-pd-v0-3",
                        "title": "OpRes PD v0.3",
                        "node_type": "task",
                        "document_id": "opres-pd-v0-3",
                    },
                    {
                        "id": "bcbs-opres-2021",
                        "title": "BCBS OpRes 2021",
                        "node_type": "international-standard",
                        "document_id": "bcbs-opres-2021",
                    },
                ],
                "edges": [
                    {
                        "id": "e-live",
                        "source": "opres-pd-v0-3",
                        "target": "bcbs-opres-2021",
                        "edge_type": "contributes-to",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ws / "workstream.json").write_text(
        json.dumps(
            {"id": "opres-v2", "name": "OpRes", "primary_task_id": "opres-pd-v0-3"}
        ),
        encoding="utf-8",
    )
    ws_anchors.save(
        root, "opres-v2", "opres-pd-v0-3", [_anchor("OpRes 1.1", "opres-pd-v0-3")]
    )
    ws_anchors.save(
        root, "opres-v2", "bcbs-opres-2021", [_anchor("BCBS 1.1", "bcbs-opres-2021")]
    )
    return root


@pytest.fixture
def spy_run_arm_g(monkeypatch):
    """Capture what the default adapter hands the pipeline."""
    seen: dict = {}

    def fake(anchor_index, doc_a, doc_b, **kwargs):
        seen["anchor_ids"] = sorted(a["anchor_id"] for a in anchor_index.all())
        seen["doc_a"] = doc_a
        seen["doc_b"] = doc_b
        seen["axes_dir"] = kwargs.get("axes_dir")
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    monkeypatch.setattr(api_module, "_run_arm_g", fake)
    return seen


def test_analysis_uses_the_workstreams_own_anchors(tmp_path, spy_run_arm_g):
    """No artifacts dir exists at all — the index comes from the workstream."""
    root = _ws(tmp_path)
    client = TestClient(
        create_app(workstreams_dir=root, artifacts_dir=tmp_path / "does-not-exist")
    )

    res = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")

    assert res.status_code == 200, res.text
    assert res.json()["status"] == "analysed"
    # Both chunked documents' anchors were unioned into the index.
    assert spy_run_arm_g["anchor_ids"] == ["BCBS 1.1", "OpRes 1.1"]
    assert spy_run_arm_g["doc_a"] == "opres-pd-v0-3"
    assert spy_run_arm_g["doc_b"] == "bcbs-opres-2021"


def test_analysis_points_stage_one_at_the_workstream_axes_cache(
    tmp_path, spy_run_arm_g
):
    """So a cache warmed by "Extract concepts" is reused, not re-derived."""
    root = _ws(tmp_path)
    client = TestClient(create_app(workstreams_dir=root))

    client.post("/api/workstreams/opres-v2/edges/e-live/analyze")

    assert spy_run_arm_g["axes_dir"] == root / "opres-v2" / "axes"


def test_findings_persist_for_the_workstream(tmp_path, spy_run_arm_g):
    root = _ws(tmp_path)
    client = TestClient(create_app(workstreams_dir=root))

    client.post("/api/workstreams/opres-v2/edges/e-live/analyze")

    saved = root / "opres-v2" / "findings" / "e-live.json"
    assert saved.exists()
    detail = client.get("/api/workstreams/opres-v2/edges/e-live").json()
    assert detail["status"] == "analysed"
    assert len(detail["findings"]) == 1


def test_an_unchunked_endpoint_yields_no_anchors_but_still_refuses_cleanly(
    tmp_path, monkeypatch
):
    """A node with a document_id but no anchors cannot produce findings; the
    pipeline is still handed an index and any failure surfaces as 502, never a
    half-analysed edge."""
    root = _ws(tmp_path)
    # Drop one side's anchors to simulate a node that was never chunked.
    ws_anchors.anchors_path(root, "opres-v2", "bcbs-opres-2021").unlink()

    def boom(anchor_index, doc_a, doc_b, **kwargs):
        raise RuntimeError("no anchors for one side")

    monkeypatch.setattr(api_module, "_run_arm_g", boom)
    client = TestClient(create_app(workstreams_dir=root))

    res = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")

    assert res.status_code == 502
    assert res.json()["code"] == "ANALYZE_FAILED"
    assert not (root / "opres-v2" / "findings" / "e-live.json").exists()


def test_no_linkages_found_leaves_the_edge_re_analysable(tmp_path, monkeypatch):
    monkeypatch.setattr(
        api_module,
        "_run_arm_g",
        lambda index, a, b, **kw: {
            "connections": [],
            "unsupported": [],
            "trace": {},
        },
    )
    root = _ws(tmp_path)
    client = TestClient(create_app(workstreams_dir=root))

    res = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")

    assert res.status_code == 200
    assert res.json()["status"] == "no_linkages_found"
    # Nothing written → the edge is still unanalysed and can be run again.
    assert not (root / "opres-v2" / "findings" / "e-live.json").exists()
    detail = client.get("/api/workstreams/opres-v2/edges/e-live").json()
    assert detail["status"] == "not_analysed"


def test_an_injected_seam_still_overrides_the_default(tmp_path):
    """The `(src_doc, tgt_doc)` injection point is unchanged, so every existing
    stub keeps working."""
    root = _ws(tmp_path)
    calls: list = []

    def fake_fn(a, b):
        calls.append((a, b))
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    client = TestClient(create_app(workstreams_dir=root, run_arm_g_fn=fake_fn))

    res = client.post("/api/workstreams/opres-v2/edges/e-live/analyze")

    assert res.status_code == 200
    assert calls == [("opres-pd-v0-3", "bcbs-opres-2021")]
