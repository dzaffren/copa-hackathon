"""Demo-day smoke test for the 3 Aug 2026 hackathon.

Walks the exact display path a presenter shows on stage — against the real
committed `open-finance-pd-2026` workstream (the built-from-scratch demo whose
anchors, axes and findings are persisted, so no model call is needed on the
day). Read-only: it copies the seeded workstreams into a tmp dir and points
`create_app` at the copy, then asserts each demo screen's API returns real,
well-formed content. Red here means the demo is broken; the failing assertion
names the screen.

This is the acceptance gate for the demo. It deliberately exercises the
*persisted* path (the one shown on stage), not a live model call.
"""

import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_WS = "open-finance-pd-2026"  # the demo workstream (only un-hidden one)
_TASK = "open-finance-pd-2026-pd"  # its focal working-draft node
_ANALYSED_EDGE = "e-hkma_open_api_framework--ed_open_finance_2025"  # 47 findings
_CROSS_EDGE = "x-open_finance_ed--opres_dp_2025"  # the cross-workstream fixture
_LABELS = {"aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"}


def _client(tmp_path) -> TestClient:
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    return TestClient(create_app(workstreams_dir=dst))


def _assert_finding_wellformed(f: dict, where: str) -> None:
    assert f.get("label") in _LABELS, f"{where}: bad/missing label {f.get('label')!r}"
    cited = (f.get("source_clauses") or []) + (f.get("target_clauses") or [])
    assert cited, f"{where}: finding cites no clauses"
    assert all(c.get("text") for c in cited), f"{where}: a cited clause has no verbatim text"
    assert all(c.get("clause_number") for c in cited), f"{where}: a cited clause has no number"


def test_demo_workstream_is_the_only_listed_one(tmp_path):
    client = _client(tmp_path)
    body = client.get("/api/workstreams").json()
    ids = {w["id"] for w in body["workstreams"]}
    # STAGE sidebar — the demo workstream is present; the hidden legacy fixtures are not.
    assert _WS in ids, "STAGE sidebar: demo workstream missing"
    assert "opres-v2" not in ids, "STAGE sidebar: a hidden fixture leaked into the list"


def test_demo_graph_has_focal_node_and_analysed_edges(tmp_path):
    client = _client(tmp_path)
    graph = client.get(f"/api/workstreams/{_WS}/graph")
    assert graph.status_code == 200, f"STAGE graph: {graph.text}"
    g = graph.json()
    assert g.get("primary_task_id") == _TASK, "STAGE graph: focal task node missing"
    node_ids = {n["id"] for n in g["nodes"]}
    assert _TASK in node_ids and len(g["nodes"]) >= 3, "STAGE graph: too few nodes"
    analysed = [e for e in g["edges"] if e.get("analysed")]
    assert analysed, "STAGE graph: no analysed edges to demo"
    assert any(
        e["id"] == _ANALYSED_EDGE and e.get("findings_count", 0) > 0 for e in analysed
    ), "STAGE graph: the demo's analysed edge has no findings"


def test_demo_review_screen_shows_verbatim_labelled_findings(tmp_path):
    client = _client(tmp_path)
    review = client.get(f"/api/workstreams/{_WS}/edges/{_ANALYSED_EDGE}/review")
    assert review.status_code == 200, f"STAGE review: {review.text}"
    body = review.json()
    findings = body.get("findings") or []
    assert findings, "STAGE review: no findings on the demo edge"
    for f in findings:
        _assert_finding_wellformed(f, "STAGE review")


def test_demo_task_screen_and_draft_roundtrip(tmp_path):
    client = _client(tmp_path)
    task = client.get(f"/api/workstreams/{_WS}/tasks/{_TASK}")
    assert task.status_code == 200, f"STAGE task: {task.text}"

    put = client.put(
        f"/api/workstreams/{_WS}/tasks/{_TASK}/draft",
        json={"content_html": "<p>Demo draft body.</p>"},
    )
    assert put.status_code in (200, 204), f"STAGE draft-save: {put.text}"
    got = client.get(f"/api/workstreams/{_WS}/tasks/{_TASK}/draft").json()
    assert got.get("content_html") == "<p>Demo draft body.</p>", "STAGE draft: did not round-trip"


def test_demo_cross_workstream_climax_renders(tmp_path):
    client = _client(tmp_path)
    detail = client.get(f"/api/cross-links/{_CROSS_EDGE}")
    assert detail.status_code == 200, f"STAGE cross-link: {detail.text}"
    body = detail.json()
    findings = body.get("findings") or []
    assert findings, "STAGE cross-link: the climax has no findings"
    for f in findings:
        _assert_finding_wellformed(f, "STAGE cross-link")
