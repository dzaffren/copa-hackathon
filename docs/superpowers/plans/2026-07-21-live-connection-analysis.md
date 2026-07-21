# Live Connection Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the "Analyze linkages" button run the real finder→critic loop on edges whose endpoints are ingested documents, replacing hand-authored canned findings.

**Architecture:** Add `document_id` to workstream graph nodes; rewrite the `analyze` route to resolve both endpoints' documents, call `engine.connections.find_connections`, adapt the result into the workstream-finding shape, and save it. The frontend enables the button only for edges where both endpoints map to ingested docs.

**Tech Stack:** Python 3.12+, FastAPI, pytest (engine); Vite + React 18 + TanStack Query + Vitest (frontend).

## Global Constraints

- **Never invent clauses:** only `result["connections"]` (supported, verbatim-cited) become findings; `result["unsupported"]` is excluded. (CLAUDE.md verbatim-citation rule.)
- **One taxonomy:** findings carry exactly one `label` of `aligns-with`/`differs-on`/`conflicts-with`/`silent-on`/`goes-beyond`; `sentiment` only on `differs-on`. `find_connections` already enforces this — do not re-validate.
- **Engine deps live in two places:** any new `engine/` dependency goes in BOTH `pyproject.toml` and `.github/workflows/test.yml`. (No new deps expected in this plan.)
- **Artifact writes UTF-8:** `save_findings` already writes UTF-8; do not change.
- **No live model in CI:** every route/adapter test injects a stub `find_connections_fn`; the real model is exercised only by the manual smoke-run (Task 7).
- **Verify with:** `.venv/bin/python -m pytest engine/tests` (engine), `npm run test` in `frontend/` (frontend). Ignore the pre-existing `kg-poc/` collection errors — out of scope.
- **Git:** branch off `dzaf/main`; Conventional Commits; commit per task; do not push unless asked.

---

### Task 1: Map graph nodes to document_ids

**Files:**

- Modify: `data/workstreams/opres-v2/graph.json`
- Modify: `data/workstreams/open-finance-ed/graph.json`
- Modify: `data/workstreams/rmit-v2-2025/graph.json`
- Modify: `data/workstreams/outsourcing-v2/graph.json`
- Modify: `data/workstreams/_cross/graph.json`
- Test: `engine/tests/test_workstream_document_ids.py` (create)

**Interfaces:**

- Produces: graph nodes gain an optional `"document_id"` string field. Consumed by Task 3 (route) and Task 6 (frontend enable/disable).

Add `"document_id"` to exactly these nodes (leave all other nodes untouched — no field):

| file            | node id             | document_id               |
| --------------- | ------------------- | ------------------------- |
| opres-v2        | `opres-pd-v0-3`     | `opres-v1-2025-draft`     |
| opres-v2        | `opres-dp-2025`     | `opres-v1-2025-draft`     |
| opres-v2        | `rmit-pd-2025`      | `rmit-v2-2025`            |
| open-finance-ed | `of-ed-2025`        | `open-finance-v1-2025-ed` |
| open-finance-ed | `rmit-pd-2023`      | `rmit-v1-2023`            |
| open-finance-ed | `bcm-pd-2022`       | `bcm-v1-2022`             |
| rmit-v2-2025    | `rmit-pd-v2`        | `rmit-v2-2025`            |
| outsourcing-v2  | `outsourcing-pd-v2` | `outsourcing-v1-2019`     |
| _cross          | `of-ed-2025`        | `open-finance-v1-2025-ed` |
| _cross          | `opres-dp-2025`     | `opres-v1-2025-draft`     |

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_workstream_document_ids.py
"""Every document_id declared on a workstream graph node must be a real
ingested document (present in the clause index), so the live analyze route
never resolves a node to a document with zero clauses."""
import json
from pathlib import Path

from engine.clauses import load_clause_index
from engine.config import REPO_ROOT

WORKSTREAMS = REPO_ROOT / "data" / "workstreams"
ARTIFACTS = REPO_ROOT / "data" / "artifacts"

EXPECTED = {
    ("opres-v2", "opres-pd-v0-3"): "opres-v1-2025-draft",
    ("opres-v2", "opres-dp-2025"): "opres-v1-2025-draft",
    ("opres-v2", "rmit-pd-2025"): "rmit-v2-2025",
    ("open-finance-ed", "of-ed-2025"): "open-finance-v1-2025-ed",
    ("open-finance-ed", "rmit-pd-2023"): "rmit-v1-2023",
    ("open-finance-ed", "bcm-pd-2022"): "bcm-v1-2022",
    ("rmit-v2-2025", "rmit-pd-v2"): "rmit-v2-2025",
    ("outsourcing-v2", "outsourcing-pd-v2"): "outsourcing-v1-2019",
    ("_cross", "of-ed-2025"): "open-finance-v1-2025-ed",
    ("_cross", "opres-dp-2025"): "opres-v1-2025-draft",
}


def _node(ws: str, node_id: str) -> dict:
    graph = json.loads((WORKSTREAMS / ws / "graph.json").read_text("utf-8"))
    return next(n for n in graph["nodes"] if n["id"] == node_id)


def test_declared_document_ids_match_expected():
    for (ws, node_id), doc_id in EXPECTED.items():
        assert _node(ws, node_id).get("document_id") == doc_id, (ws, node_id)


def test_declared_document_ids_are_ingested():
    index = load_clause_index(ARTIFACTS)
    for (ws, node_id), doc_id in EXPECTED.items():
        assert index.entries_for_document(doc_id), f"{doc_id} has no clauses"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_workstream_document_ids.py -v`
Expected: FAIL — nodes have no `document_id` key (returns `None`).

- [ ] **Step 3: Add `document_id` to the 10 nodes**

Edit each `graph.json`: on each node listed in the table above, add a `"document_id"` key with the mapped value. Example, in `data/workstreams/opres-v2/graph.json` the `opres-pd-v0-3` node object gains:

```json
"document_id": "opres-v1-2025-draft",
```

Do NOT add the field to any node not in the table.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_workstream_document_ids.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add data/workstreams/*/graph.json engine/tests/test_workstream_document_ids.py
git commit -m "feat(workstream-brain): map graph nodes to ingested document_ids"
```

---

### Task 2: Connection→finding adapter

**Files:**

- Modify: `engine/workstreams.py` (add `connections_to_findings`)
- Test: `engine/tests/test_connections_to_findings.py` (create)

**Interfaces:**

- Consumes: a `find_connections` result dict `{"connections": list[dict], "unsupported": list[dict]}`. Each connection dict has keys `summary`, `label`, `sentiment`, `source_clauses` (list of `{clause_number, text}`), `target_clauses`, `scope_note`, `supported`.
- Produces: `connections_to_findings(result: dict) -> list[dict]`. Each finding = the connection dict plus `"id": str` (stable, from summary + cited clause numbers) and `"review_state": "pending"`. `unsupported` is dropped.

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_connections_to_findings.py
from engine.workstreams import connections_to_findings

CONN = {
    "summary": "Both require BCP.",
    "label": "aligns-with",
    "sentiment": None,
    "source_clauses": [{"clause_number": "Operational Resilience 4.3", "text": "..."}],
    "target_clauses": [{"clause_number": "Open Finance 7.6(b)", "text": "..."}],
    "scope_note": None,
    "supported": True,
}


def test_adds_id_and_pending_review_state():
    out = connections_to_findings({"connections": [CONN], "unsupported": []})
    assert len(out) == 1
    f = out[0]
    assert f["review_state"] == "pending"
    assert isinstance(f["id"], str) and f["id"]
    assert f["summary"] == CONN["summary"]
    assert f["source_clauses"] == CONN["source_clauses"]


def test_id_is_stable_for_same_connection():
    a = connections_to_findings({"connections": [CONN], "unsupported": []})[0]
    b = connections_to_findings({"connections": [CONN], "unsupported": []})[0]
    assert a["id"] == b["id"]


def test_excludes_unsupported():
    result = {"connections": [], "unsupported": [{"summary": "dropped"}]}
    assert connections_to_findings(result) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_connections_to_findings.py -v`
Expected: FAIL — `ImportError: cannot import name 'connections_to_findings'`.

- [ ] **Step 3: Implement the adapter**

Add to `engine/workstreams.py` (near `canned_analysis`):

```python
import hashlib


def connections_to_findings(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapt an `engine.connections.find_connections` result into the
    workstream findings shape the Review/Task screens read.

    Only supported connections (`result["connections"]`) become findings —
    `result["unsupported"]` is dropped, preserving the never-invent guarantee.
    Each finding is the connection dict plus a stable `id` (hash of summary +
    cited clause numbers, so re-running yields the same id) and
    `review_state: "pending"`.
    """
    findings: list[dict[str, Any]] = []
    for conn in result.get("connections", []):
        cited = [
            c.get("clause_number", "")
            for side in ("source_clauses", "target_clauses")
            for c in conn.get(side) or []
        ]
        seed = conn.get("summary", "") + "|" + "|".join(cited)
        finding = dict(conn)
        finding["id"] = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
        finding["review_state"] = "pending"
        findings.append(finding)
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_connections_to_findings.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/workstreams.py engine/tests/test_connections_to_findings.py
git commit -m "feat(engine): add connection→finding adapter for live analysis"
```

---

### Task 3: Rewrite the analyze route to call the live finder

**Files:**

- Modify: `engine/api.py` (`create_app` signature + the `analyze` route + imports)
- Test: `engine/tests/test_api_analyze_live.py` (create)

**Interfaces:**

- Consumes: `connections_to_findings` (Task 2); node `document_id` (Task 1); `engine.clauses.load_clause_index(artifacts_dir) -> ClauseIndex` with `.entries_for_document(doc_id) -> list`; `engine.config.REPO_ROOT`.
- Produces: `create_app(workstreams_dir=..., artifacts_dir=..., find_connections_fn=...)`. `find_connections_fn` signature: `(doc_a_id: str, doc_b_id: str, clause_index) -> {"connections": [...], "unsupported": [...]}`. Route returns `200 {id, status:"analysed", findings, findings_count}`, `409 {code:"NOT_ANALYSABLE", message, field}`, or `502 {code:"ANALYZE_FAILED", message}`.

- [ ] **Step 1: Write the failing test**

```python
# engine/tests/test_api_analyze_live.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_api_analyze_live.py -v`
Expected: FAIL — `create_app` has no `find_connections_fn` kwarg.

- [ ] **Step 3: Update `create_app` signature and imports**

In `engine/api.py`, add imports near the top:

```python
from engine.clauses import load_clause_index
from engine.connections import find_connections as _default_find_connections
from engine.config import REPO_ROOT
```

Change the signature (drop `analyze_delay`, add the two new params):

```python
def create_app(
    workstreams_dir: Union[str, Path] = WORKSTREAMS_DIR,
    artifacts_dir: Union[str, Path] = REPO_ROOT / "data" / "artifacts",
    find_connections_fn=_default_find_connections,
) -> FastAPI:
```

Update the docstring: remove the `analyze_delay` paragraph; add that `artifacts_dir` is where the clause index is read for live analysis and `find_connections_fn` is injectable so tests stub the model.

- [ ] **Step 4: Replace the analyze route body**

Replace the entire `analyze_workstream_edge` function body (currently lines ~511–550, the canned version) with:

```python
    @app.post("/api/workstreams/{workstream_id}/edges/{edge_id}/analyze")
    def analyze_workstream_edge(workstream_id: str, edge_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        edge = next(
            (e for e in ws_graph.get("edges", []) if e["id"] == edge_id), None
        )
        if edge is None:
            return _ws_error(
                404,
                "EDGE_NOT_FOUND",
                f"Edge {edge_id} not found in workstream {workstream_id}",
            )
        by_id = {n["id"]: n for n in ws_graph.get("nodes", [])}
        src_doc = by_id.get(edge["source"], {}).get("document_id")
        tgt_doc = by_id.get(edge["target"], {}).get("document_id")
        # The source (task) node is doc_a ("ours") so silent-on / goes-beyond
        # read in the drafter's direction (task node is always the edge source).
        if not src_doc:
            return _ws_error(
                409, "NOT_ANALYSABLE",
                f"Node {edge['source']} has no ingested document to analyse.",
                field="source",
            )
        if not tgt_doc:
            return _ws_error(
                409, "NOT_ANALYSABLE",
                f"Node {edge['target']} has no ingested document to analyse.",
                field="target",
            )
        clause_index = load_clause_index(artifacts_dir)
        try:
            result = find_connections_fn(src_doc, tgt_doc, clause_index)
        except Exception as exc:  # live model / creds / network failure
            return _ws_error(
                502, "ANALYZE_FAILED",
                f"Live analysis failed: {exc}",
            )
        findings = workstreams.connections_to_findings(result)
        workstreams.save_findings(workstreams_dir, workstream_id, edge_id, findings)
        return {
            "id": edge_id,
            "status": "analysed",
            "findings": findings,
            "findings_count": len(findings),
        }
```

`_ws_error` currently has signature `(status_code, code, message)` and returns `{code, message}` — it does NOT accept `field`. Update it to `def _ws_error(status_code, code, message, field=None)` and, when `field is not None`, include `"field": field` in the JSON body (leave existing 2-arg callers unaffected). Also remove the now-dead `import time` (line ~27) — it is used ONLY by the `time.sleep(analyze_delay)` line you are deleting (verified: no other `time.` reference in the file).

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_api_analyze_live.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit**

```bash
git add engine/api.py engine/tests/test_api_analyze_live.py
git commit -m "feat(engine): analyze route runs the live finder on ingested edges"
```

---

### Task 4: Migrate existing canned-route tests

**Files:**

- Modify: `engine/tests/test_api_workstreams.py`
- Modify: `engine/tests/test_api_review.py`
- Modify: `engine/tests/test_api_new_workstream.py`
- Modify: `engine/tests/test_api_cross_links.py`
- Modify: `engine/tests/test_api_drafting.py`

**Interfaces:**

- Consumes: `create_app(find_connections_fn=...)` from Task 3.

- [ ] **Step 1: Find every failing reference**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: FAILs in the 5 files above — any test passing `analyze_delay=` to `create_app`, or asserting the canned `no_matching_source` / canned demo findings.

- [ ] **Step 2: Update each failure**

For each failing test:

- Replace `create_app(..., analyze_delay=0)` with `create_app(...)` (drop the kwarg).
- Any test that POSTed `/analyze` and expected canned findings: pass a stub, e.g. `create_app(workstreams_dir=..., find_connections_fn=lambda a, b, idx: {"connections": [], "unsupported": []})`, and assert on the stubbed result (empty findings → `findings_count == 0`, `status == "analysed"`). A test that specifically asserted `no_matching_source` for an off-pair edge should be deleted or rewritten to the `409 NOT_ANALYSABLE` path (unmapped node).
- Tests that never touch `/analyze` but pass `analyze_delay`: just drop the kwarg.

- [ ] **Step 3: Run the full suite**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS (all engine tests; `kg-poc/` errors are out of scope and not collected under `engine/tests`).

- [ ] **Step 4: Commit**

```bash
git add engine/tests/
git commit -m "test(engine): migrate analyze-route tests to the live finder seam"
```

---

### Task 5: Expose `analysable` on the edge detail route

**Files:**

- Modify: `engine/api.py` (`get_workstream_edge_detail`)
- Modify: `frontend/src/lib/types.ts` (`EdgeDetail`, `EdgeEndpoint`)
- Test: `engine/tests/test_api_analyze_live.py` (add one test)

**Interfaces:**

- Produces: `GET /api/workstreams/{ws}/edges/{id}` response gains `"analysable": bool` (true iff both endpoint nodes have a `document_id`) and each endpoint gains `"document_id": str | None`. Consumed by Task 6.

- [ ] **Step 1: Write the failing test**

Add to `engine/tests/test_api_analyze_live.py`:

```python
def test_edge_detail_reports_analysable(tmp_path):
    client = _client(tmp_path, lambda a, b, idx: {"connections": [], "unsupported": []})
    live = client.get("/api/workstreams/opres-v2/edges/e-live").json()
    assert live["analysable"] is True
    assert live["source"]["document_id"] == "opres-v1-2025-draft"
    noref = client.get("/api/workstreams/opres-v2/edges/e-noref").json()
    assert noref["analysable"] is False
    assert noref["target"]["document_id"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_api_analyze_live.py::test_edge_detail_reports_analysable -v`
Expected: FAIL — `KeyError: 'analysable'`.

- [ ] **Step 3: Update the edge detail route**

In `get_workstream_edge_detail`, include `document_id` in each endpoint dict and add the top-level flag. The `source`/`target` dicts each gain:

```python
"document_id": src.get("document_id"),
```

```python
"document_id": tgt.get("document_id"),
```

And add to the returned dict:

```python
"analysable": bool(src.get("document_id") and tgt.get("document_id")),
```

- [ ] **Step 4: Update the frontend type**

In `frontend/src/lib/types.ts`, add `document_id: string | null;` to `EdgeEndpoint` and `analysable: boolean;` to `EdgeDetail`.

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_api_analyze_live.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/api.py engine/tests/test_api_analyze_live.py frontend/src/lib/types.ts
git commit -m "feat(engine): expose analysable flag + document_id on edge detail"
```

---

### Task 6: Frontend — gate the button on `analysable` and handle live latency/errors

**Files:**

- Modify: `frontend/src/features/workstream-graph/EdgeDetailPanel.tsx`
- Test: `frontend/src/features/workstream-graph/EdgeDetailPanel.test.tsx`

**Interfaces:**

- Consumes: `EdgeDetail.analysable` and `EdgeDetail.source/target.document_id` (Task 5); `analyzeEdge` (unchanged) which may now reject with a 409/502 HttpError.

- [ ] **Step 1: Write the failing test**

Add to `EdgeDetailPanel.test.tsx` (follow the file's existing mock/render setup):

```tsx
it("disables Analyze when the edge is not analysable", async () => {
  // Mock fetchEdgeDetail to return an unanalysed, NOT-analysable edge.
  // (Use the file's existing mocking approach for @/lib/api.)
  renderPanel({
    status: "not_analysed",
    analysable: false,
    source: {
      id: "opres",
      title: "OpRes",
      node_type: "task",
      document_id: "opres-v1-2025-draft",
    },
    target: {
      id: "bcbs",
      title: "BCBS",
      node_type: "international-standard",
      document_id: null,
    },
    findings: [],
  });
  const btn = await screen.findByRole("button", { name: /analyze linkages/i });
  expect(btn).toBeDisabled();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- EdgeDetailPanel`
Expected: FAIL — button is not disabled (no `analysable` gating yet).

- [ ] **Step 3: Implement gating + error state**

In `EdgeDetailPanel.tsx`:

- After `const analysed = edge.status === "analysed";` add:
  ```tsx
  const analysable = edge.analysable;
  ```
- On the Analyze `<Button>`, change `disabled={analyze.isPending}` to `disabled={analyze.isPending || !analysable}` and, when `!analysable`, render a hint under it:
  ```tsx
  {
    !analysable && (
      <p className="text-xs text-muted-foreground">
        Live analysis needs both documents ingested — this pair isn’t in the
        corpus yet.
      </p>
    );
  }
  ```
- Change the spinner copy from `Analyzing…` to `Analyzing… the AI is reading both documents` (real ~30–60s call).
- Add an error surface after the button, driven by the mutation:

  ```tsx
  {
    analyze.isError && (
      <p className="text-xs text-red-600">
        Analysis failed. Check the engine has model credentials, then retry.
      </p>
    );
  }
  ```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- EdgeDetailPanel`
Expected: PASS (new test + existing ones).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/workstream-graph/EdgeDetailPanel.tsx frontend/src/features/workstream-graph/EdgeDetailPanel.test.tsx
git commit -m "feat(frontend): gate live analyze on analysable + show latency/errors"
```

---

### Task 7: Manual live smoke-run + full verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full engine suite**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: all pass.

- [ ] **Step 2: Run the frontend suite**

Run: `cd frontend && npm run test`
Expected: all pass.

- [ ] **Step 3: Live smoke-run against a real edge (needs Azure creds in `.env`)**

Start the engine: `.venv/bin/python -m uvicorn engine.api:create_app --factory --port 8000`
Then: `curl -s -X POST http://localhost:8000/api/workstreams/_cross/edges/x-open_finance_ed--opres_dp_2025/analyze | python3 -m json.tool | head -30`
Expected: `status: "analysed"`, `findings_count > 0`, each finding has `label` in the five-label set, `review_state: "pending"`, and `source_clauses[].text` present. Takes ~30–60s (real model call).

- [ ] **Step 4: Confirm the edge renders in the app**

With engine + `npm run dev` running (Vite proxy from earlier), open the OpRes workstream → cross-link into Open Finance → click Analyze → confirm findings render in Review.

- [ ] **Step 5: Report results** — do not commit anything in this task; it is verification only.

```

```
