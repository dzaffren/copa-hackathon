"""The analyze route must hand the finder the DRAFTER's document as document A.

The finder's DIRECTION CONVENTION is fixed: document A is "we/ours". So
`silent-on` ("ours has no provision"), `goes-beyond` ("ours covers it, theirs
does not") and `differs-on`'s tighten/loosen only mean anything if A really is
the drafter's side.

Edge direction cannot decide that. The two live fixtures point OPPOSITE ways:
`opres-v2` runs task → anchor, while `open-finance-pd-2026` points every anchor
INTO the ED node its PD consolidates. The route used to pass `edge["source"]` as
A, which silently inverted all three of those labels on the demo workstream.

`test_api_finder_pipeline.py` already covers the task-as-source shape; this file covers the
anchor-as-source shape and the flip-back of the persisted clause sides.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from engine.api import create_app

CONN = {
    "summary": "Ours requires a breach plan; theirs is silent.",
    "label": "goes-beyond",
    "sentiment": None,
    "source_clauses": [{"clause_number": "ED 11.5", "text": "ours..."}],
    "target_clauses": [{"clause_number": "HKMA 3.1", "text": "theirs..."}],
    "scope_note": None,
    "supported": True,
}


def _ws(tmp_path: Path) -> Path:
    """A workstream shaped like `open-finance-pd-2026`: the anchor is the edge
    SOURCE and the document the drafter owns (the ED) is the edge TARGET."""
    root = tmp_path / "workstreams"
    ws = root / "of-pd"
    (ws / "findings").mkdir(parents=True)
    (ws / "graph.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "of-pd-task",
                        "title": "Open Finance PD",
                        "node_type": "task",
                        "document_id": "of-pd-2026",
                    },
                    {
                        "id": "ed-of-2025",
                        "title": "ED Open Finance 2025",
                        "node_type": "internal-published",
                        "document_id": "ed-of-2025-doc",
                    },
                    {
                        "id": "hkma",
                        "title": "HKMA Open API",
                        "node_type": "peer-regulator",
                        "document_id": "hkma-doc",
                    },
                ],
                "edges": [
                    # The task points into the ED, exactly as the demo fixture does.
                    {
                        "id": "e-task-ed",
                        "source": "of-pd-task",
                        "target": "ed-of-2025",
                        "edge_type": "references",
                    },
                    # The pair under test: anchor → ED. "Ours" is the TARGET here.
                    {
                        "id": "e-hkma-ed",
                        "source": "hkma",
                        "target": "ed-of-2025",
                        "edge_type": "references",
                    },
                ],
            }
        ),
        "utf-8",
    )
    (ws / "workstream.json").write_text(
        json.dumps(
            {"id": "of-pd", "name": "Open Finance PD", "primary_task_id": "of-pd-task"}
        ),
        "utf-8",
    )
    return root


def _client(tmp_path, fn):
    return TestClient(create_app(workstreams_dir=_ws(tmp_path), run_finder_pipeline_fn=fn))


def test_the_drafters_document_is_document_a_even_when_it_is_the_edge_target():
    """The regression this file exists for: `hkma → ed` must be analysed
    ED-first, because the ED is the side the drafter owns."""
    calls = []

    def stub(a, b):
        calls.append((a, b))
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        client = _client(Path(tmp), stub)
        r = client.post("/api/workstreams/of-pd/edges/e-hkma-ed/analyze")
        assert r.status_code == 200
    # NOT ("hkma-doc", "ed-of-2025-doc") — that ordering is what inverted the
    # labels on the demo workstream.
    assert calls == [("ed-of-2025-doc", "hkma-doc")]


def test_the_label_the_finder_chose_is_persisted_unchanged(tmp_path):
    """The flip-back must move only the cited clauses. Rewriting `goes-beyond`
    to `silent-on` here would re-introduce the bug from the other direction."""

    def stub(a, b):
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    client = _client(tmp_path, stub)
    r = client.post("/api/workstreams/of-pd/edges/e-hkma-ed/analyze")
    assert r.status_code == 200
    assert r.json()["findings"][0]["label"] == "goes-beyond"


def test_the_persisted_clause_sides_follow_the_edge_not_the_finder(tmp_path):
    """Findings are stored in EDGE orientation — `source_clauses` belongs to
    `edge["source"]` — because that is what the review panes read. Since the
    finder was called ours-first, its sides must be swapped back on the way in."""

    def stub(a, b):
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    client = _client(tmp_path, stub)
    r = client.post("/api/workstreams/of-pd/edges/e-hkma-ed/analyze")
    assert r.status_code == 200
    finding = r.json()["findings"][0]
    # edge source is `hkma`, so the HKMA clause must be in source_clauses.
    assert [c["clause_number"] for c in finding["source_clauses"]] == ["HKMA 3.1"]
    assert [c["clause_number"] for c in finding["target_clauses"]] == ["ED 11.5"]


def test_a_task_owned_edge_still_reads_task_first(tmp_path):
    """The task node itself is unambiguously "ours" whichever end it sits on."""
    calls = []

    def stub(a, b):
        calls.append((a, b))
        return {"connections": [CONN], "unsupported": [], "trace": {}}

    client = _client(tmp_path, stub)
    r = client.post("/api/workstreams/of-pd/edges/e-task-ed/analyze")
    assert r.status_code == 200
    assert calls == [("of-pd-2026", "ed-of-2025-doc")]
