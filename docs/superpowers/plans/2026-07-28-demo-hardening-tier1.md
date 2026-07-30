# Demo Hardening (Tier 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the four Tier 1 demo-hardening fixes from `docs/specs/workstream-brain/spec-demo-hardening.md` so the COPA Hackathon demo (5 Aug 2026) cannot fail on a thin index, a runaway Analyze click, or a scripted-but-fragile climax — with one end-to-end smoke test holding it all in place.

**Architecture:** All four fixes live in the existing FastAPI engine (`engine/`) and the Vite/React frontend (`frontend/`). No database, no new service. The engine already exposes injectable model seams on `create_app()` (`run_arm_g_fn`, `copilot_reply_fn`, `copilot_stream_fn`); we add a read-only `/health` route, a per-document axis-extraction ceiling, a live-with-recorded-fallback path for the cross-workstream climax, and a smoke test. Every change is test-first.

**Tech Stack:** Python 3.13 / FastAPI / pytest (engine); React 18 + TypeScript + Vite + TanStack Query + Vitest + MSW (frontend). Tests run via `.venv/bin/python -m pytest engine/tests` and `npm test` in `frontend/`.

**Build order (from the overview spec):** Task Group A (smoke test) → B (integrity guard) → C (fan-out cap) → D (climax). The smoke test lands first as the shared acceptance gate; the climax lands last because it is the only audience-visible behaviour change.

**Non-negotiables carried through every task:** verbatim citation (findings/cards quote real clause text, never synthesised); exactly one of the five semantic labels per finding; engine state stays in files.

**One deliberate scope refinement (confirm before Task Group C):** the fan-out spec asks for a "wall-clock budget → clean failure." True _preemption_ of a synchronous model call needs async/timeouts and is Tier 2. This plan delivers the demo-safety the budget was for by other means — the per-document cap plus a pre-demo warm-cache step make the click fast, and the climax falls back on any failure _or empty result_. Budget overrun is detected post-hoc (elapsed check) and recorded, not preempted mid-call. See Task C4.

---

## File Structure

**Task Group A — smoke test**

- Create: `engine/tests/test_demo_smoke.py` — one test walking graph → analyze → review → draft → cross-link against the seeded fixtures with a stubbed pipeline.
- Modify: `.github/workflows/test.yml` — ensure the smoke test runs in CI (it runs automatically under `pytest engine/tests`; add an explicit assertion step only if the workflow filters tests).

**Task Group B — artifact integrity guard**

- Modify: `engine/config.py` — add `DEMO_DOCUMENTS` (the document ids the demo relies on).
- Modify: `engine/api.py` — add `GET /health`; add a typed `DocumentNotIndexedError` raised inside the default Arm G adapter (`_make_default_run_arm_g`) and mapped to `409 INDEX_MISSING_DOCUMENT` in the analyze route.
- Create: `engine/tests/test_api_health.py` — `/health` ok/degraded/fresh-checkout tests + the analyze 409 test.
- Create: `frontend/src/lib/hooks/useHealth.ts` — TanStack Query hook for `/health`.
- Modify: `frontend/src/lib/api.ts` — add `fetchHealth()`.
- Modify: `frontend/src/lib/types.ts` — add `HealthResponse`.
- Create: `frontend/src/components/DegradedIndexBanner.tsx` — the warning banner.
- Modify: `frontend/src/components/AppShell.tsx` — mount the banner above `<Outlet />`.
- Modify: `frontend/src/test/msw/handlers.ts` — default `*/health` handler returning `{status:"ok"}`.
- Create: `frontend/src/components/DegradedIndexBanner.test.tsx` — banner shows on degraded, absent on ok.

**Task Group C — analyze fan-out cap**

- Modify: `engine/config.py` — add `AXIS_ANCHOR_CEILING` and `ANALYZE_BUDGET_SECONDS`.
- Modify: `engine/arm_g.py` — cap `extract_axes_for_document` to the top-`ceiling` highest-signal anchors; record `attempted`/`capped` in the returned axis cache; add a post-hoc elapsed check in `run_arm_g`.
- Create: `scripts/warm_demo_cache.py` — pre-populate the axis cache for the demo documents.
- Modify: `engine/tests/test_arm_g.py` — cap tests (exactly `ceiling` extraction calls; deterministic selection).

**Task Group D — cross-workstream climax**

- Modify: `engine/api.py` — `GET /api/cross-links/{edge_id}` attempts the live pipeline, falls back to the committed `_cross` trace, and stamps `source: "live" | "recorded"`.
- Create: `data/workstreams/_cross/recorded-traces/<demo-edge>.json` — the committed safety-net trace for the demo pair.
- Modify: `engine/tests/test_api_cross_links.py` — live-success, live-raises-fallback, empty-fallback, verbatim + label tests.

---

## Task Group A — Demo Smoke Test (Fix 4)

Build first. It is the executable definition of "the demo works" that B, C, D verify against.

### Task A1: One end-to-end smoke test

**Files:**

- Create: `engine/tests/test_demo_smoke.py`
- Reference (do not modify): `engine/tests/test_api_workstreams.py` (harness), `engine/tests/test_api_arm_g.py` (stub shape)

- [ ] **Step 1: Write the failing smoke test**

Create `engine/tests/test_demo_smoke.py`:

```python
"""Demo-day smoke test: walks the exact path a presenter clicks through — load
the workstream graph, analyse the demo edge, read the review pane, round-trip a
draft, and open the cross-workstream climax — against the seeded fixtures with a
stubbed pipeline. Red here means the demo flow is broken; the failing assertion
names the stage. No network, model, or credentials.
"""

import json
import shutil

from fastapi.testclient import TestClient

from engine.api import create_app
from engine.config import REPO_ROOT

_OPRES = "opres-v2"
_TASK = "opres-pd-v0-3"
_FSB_EDGE = "e-opres_v0_3--fsb_3rd_party"  # the seeded, unanalysed analyze pair

# A single supported connection the stubbed pipeline returns. Shape mirrors
# engine/tests/test_api_arm_g.py::CONN so connections_to_findings maps it.
_STUB_CONN = {
    "summary": "Both require third-party continuity planning.",
    "label": "aligns-with",
    "sentiment": None,
    "source_clauses": [{"clause_number": "Operational Resilience 4.3", "text": "The financial institution must plan for third-party disruption."}],
    "target_clauses": [{"clause_number": "FSB 3.1", "text": "Firms should manage third-party dependencies."}],
    "scope_note": None,
    "supported": True,
}


def _stub_run_arm_g(src_doc, tgt_doc):
    return {"connections": [_STUB_CONN], "unsupported": [], "trace": {}}


def _client(tmp_path):
    dst = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", dst)
    app = create_app(workstreams_dir=dst, run_arm_g_fn=_stub_run_arm_g)
    return TestClient(app)


def test_demo_flow_end_to_end(tmp_path):
    client = _client(tmp_path)

    # STAGE 1 — the graph loads.
    graph = client.get(f"/api/workstreams/{_OPRES}/graph")
    assert graph.status_code == 200, "STAGE graph-load failed"
    assert any(e["id"] == _FSB_EDGE for e in graph.json()["edges"]), "demo edge missing from fixture"

    # STAGE 2 — analyse the demo edge; findings come back labelled + verbatim.
    analyze = client.post(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}/analyze")
    assert analyze.status_code == 200, f"STAGE analyze failed: {analyze.text}"
    findings = analyze.json()["findings"]
    assert findings, "STAGE analyze produced no findings"
    labels = {"aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"}
    for f in findings:
        assert f["label"] in labels, f"STAGE analyze: bad label {f['label']}"
        cited = (f.get("source_clauses") or []) + (f.get("target_clauses") or [])
        assert cited and all(c.get("text") for c in cited), "STAGE analyze: finding cites no verbatim text"

    # STAGE 3 — the review pane serves the same verbatim clause text.
    review = client.get(f"/api/workstreams/{_OPRES}/edges/{_FSB_EDGE}/review")
    assert review.status_code == 200, f"STAGE review failed: {review.text}"

    # STAGE 4 — a draft round-trips.
    put = client.put(
        f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft",
        json={"html": "<p>Demo draft body.</p>"},
    )
    assert put.status_code in (200, 204), f"STAGE draft-save failed: {put.text}"
    got = client.get(f"/api/workstreams/{_OPRES}/tasks/{_TASK}/draft")
    assert got.status_code == 200, "STAGE draft-read failed"
    assert "Demo draft body." in json.dumps(got.json()), "STAGE draft did not round-trip"

    # STAGE 5 — the cross-workstream climax returns a result.
    listing = client.get("/api/cross-links")
    assert listing.status_code == 200, "STAGE cross-link list failed"
    links = listing.json().get("links", [])
    assert links, "STAGE cross-link: no cross-links in fixture"
    edge_id = links[0]["id"]
    detail = client.get(f"/api/cross-links/{edge_id}")
    assert detail.status_code == 200, f"STAGE cross-link detail failed: {detail.text}"
```

- [ ] **Step 2: Run it and read the failures as a to-do list**

Run: `.venv/bin/python -m pytest engine/tests/test_demo_smoke.py -v`
Expected: it may PASS immediately (every route already exists). If a stage fails, the assertion message names the stage — fix the test's fixture assumptions (e.g. the exact draft request/response shape) against the real routes in `engine/api.py`, not the routes themselves. Do NOT change engine behaviour to make the smoke test pass; the smoke test documents current behaviour.

Two known adjustment points:

- The draft PUT body/response: confirm the request key (`html`) and response shape against `@app.put(".../draft")` in `engine/api.py` (~line 1439) and `engine/drafts.py`; adjust Step 1's Stage 4 to match.
- The cross-links list envelope: confirm `/api/cross-links` returns `{"links": [...]}` (see `fetchAllCrossLinks` in `frontend/src/lib/api.ts`); adjust Stage 5 if the key differs.

- [ ] **Step 3: Make the smoke test green against current behaviour**

Adjust only the test to match the real route contracts until it passes.
Run: `.venv/bin/python -m pytest engine/tests/test_demo_smoke.py -v`
Expected: PASS.

- [ ] **Step 4: Prove it catches a broken stage**

Temporarily change `_FSB_EDGE` to `"e-does-not-exist"` and run the test.
Expected: FAIL at `"demo edge missing from fixture"`. Revert the change.

- [ ] **Step 5: Commit**

```bash
git add engine/tests/test_demo_smoke.py
git commit -m "test(engine): add demo-flow smoke test as the Tier 1 acceptance gate"
```

### Task A2: Confirm the smoke test runs in CI

**Files:**

- Reference/Modify: `.github/workflows/test.yml`

- [ ] **Step 1: Check the workflow already collects the new test**

Read `.github/workflows/test.yml`. The engine step runs `pytest engine/tests` (or the whole suite). If it runs the directory, `test_demo_smoke.py` is picked up automatically — no change needed. If it names specific files, add `engine/tests/test_demo_smoke.py`.

- [ ] **Step 2: Verify the full engine suite still passes locally**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS (existing 382 tests + the new smoke test).

- [ ] **Step 3: Commit (only if the workflow changed)**

```bash
git add .github/workflows/test.yml
git commit -m "ci: ensure demo smoke test runs in the engine job"
```

---

## Task Group B — Artifact Integrity Guard (Fix 1)

### Task B1: Declare the demo's expected documents

**Files:**

- Modify: `engine/config.py`

- [ ] **Step 1: Add the constant**

At the end of the Arm G config block in `engine/config.py` (after the deployment
constants near line 835), add:

```python
# The document ids the demo relies on being present in the anchor index.
# `GET /health` reports `degraded` when any of these is missing. Keep this in
# sync with the seeded workstream fixtures under data/workstreams/.
DEMO_DOCUMENTS = [
    "opres-v1-2025-draft",
    "open-finance-v1-2025-ed",
    "rmit-v2-2025",
    "bcbs-opres-2021",
    "fsb-3rd-party",
]
```

Confirm each id against the seeded `data/workstreams/*/graph.json` node
`document_id` values before finalising; adjust the list to the real ids.

- [ ] **Step 2: Commit**

```bash
git add engine/config.py
git commit -m "feat(engine): declare DEMO_DOCUMENTS for the health guard"
```

### Task B2: `GET /health` route

**Files:**

- Modify: `engine/api.py`
- Create: `engine/tests/test_api_health.py`

- [ ] **Step 1: Write the failing health tests**

Create `engine/tests/test_api_health.py`:

```python
"""Tests for GET /health — the artifact integrity guard. A thin or missing
anchor index must report `degraded` and name the missing demo documents; a
fresh checkout with no index must report `degraded` without raising.
"""

import json

from fastapi.testclient import TestClient

from engine.api import create_app


def _client(tmp_path, anchor_docs):
    ws = tmp_path / "workstreams"
    ws.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    if anchor_docs is not None:
        anchors = [
            {"anchor_id": f"{d}::1", "document_id": d, "text": "x", "clause_number": "1"}
            for d in anchor_docs
        ]
        (artifacts / "anchor-index.json").write_text(json.dumps(anchors), "utf-8")
    app = create_app(workstreams_dir=ws, artifacts_dir=artifacts)
    return TestClient(app)


def test_health_degraded_when_index_thin(tmp_path):
    client = _client(tmp_path, anchor_docs=["opres-v1-2025-draft", "rmit-v2-2025"])
    body = client.get("/health").json()
    assert body["status"] == "degraded"
    missing = set(body["demo_documents"]["missing"])
    assert "fsb-3rd-party" in missing
    assert "open-finance-v1-2025-ed" in missing


def test_health_ok_when_all_demo_documents_indexed(tmp_path):
    from engine.config import DEMO_DOCUMENTS

    client = _client(tmp_path, anchor_docs=list(DEMO_DOCUMENTS))
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["demo_documents"]["missing"] == []


def test_health_degraded_on_fresh_checkout_without_raising(tmp_path):
    client = _client(tmp_path, anchor_docs=None)  # no anchor-index.json at all
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "degraded"
    assert body["anchor_index"]["documents"] == 0
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_api_health.py -v`
Expected: FAIL — `/health` returns 404 (route does not exist yet).

- [ ] **Step 3: Add a shared index-documents helper**

In `engine/api.py`, above `def create_app(`, add a helper that reads the anchor
index's distinct document ids without requiring the file to exist:

```python
def _indexed_documents(artifacts_dir: Path) -> Optional[set[str]]:
    """Distinct `document_id`s present in the anchor index, or None when the
    index file is absent (a fresh checkout). None means 'unknown', so callers
    skip membership checks rather than falsely rejecting."""
    path = Path(artifacts_dir) / "anchor-index.json"
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {a["document_id"] for a in raw}
```

- [ ] **Step 4: Add the `/health` route**

Inside `create_app`, alongside the other route definitions (after the CORS block
and the `run_arm_g_fn` default wiring), add:

```python
    @app.get("/health")
    def health() -> Any:
        from engine.config import DEMO_DOCUMENTS

        indexed = _indexed_documents(artifacts_dir)
        anchor_docs = indexed or set()
        try:
            clause_index = load_clause_index(artifacts_dir)
            clause_docs = {e["document_id"] for e in clause_index.all()}
        except Exception:
            clause_docs = set()
        missing = [d for d in DEMO_DOCUMENTS if d not in anchor_docs]
        return {
            "status": "ok" if not missing else "degraded",
            "anchor_index": {"documents": len(anchor_docs)},
            "clause_index": {"documents": len(clause_docs)},
            "demo_documents": {
                "expected": list(DEMO_DOCUMENTS),
                "present": [d for d in DEMO_DOCUMENTS if d in anchor_docs],
                "missing": missing,
            },
        }
```

Confirm `load_clause_index` is already imported in `engine/api.py` (it is used by
the review path); if the `ClauseIndex.all()` accessor differs, adjust
`clause_docs` to the real accessor. If none exists cheaply, set
`clause_docs = set()` and count only the anchor index — the guard's decision is
driven by the anchor index alone.

- [ ] **Step 5: Run to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_api_health.py -v`
Expected: PASS (all three).

- [ ] **Step 6: Run the full engine suite (no regressions)**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add engine/api.py engine/tests/test_api_health.py
git commit -m "feat(engine): add GET /health artifact integrity guard"
```

### Task B3: Distinct 409 when an endpoint document is not indexed

**Files:**

- Modify: `engine/api.py` (the default Arm G adapter + the analyze route)
- Modify: `engine/tests/test_api_health.py`

- [ ] **Step 1: Write the failing test**

Append to `engine/tests/test_api_health.py`:

```python
def test_analyze_returns_409_when_document_not_indexed(tmp_path):
    import shutil
    from engine.config import REPO_ROOT

    ws = tmp_path / "workstreams"
    shutil.copytree(REPO_ROOT / "data" / "workstreams", ws)
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    # Index that deliberately omits the analyze pair's documents.
    (artifacts / "anchor-index.json").write_text(
        json.dumps([{"anchor_id": "x::1", "document_id": "some-other-doc", "text": "x", "clause_number": "1"}]),
        "utf-8",
    )
    app = create_app(workstreams_dir=ws, artifacts_dir=artifacts)  # real default adapter
    client = TestClient(app)
    res = client.post("/api/workstreams/opres-v2/edges/e-opres_v0_3--fsb_3rd_party/analyze")
    assert res.status_code == 409
    body = res.json()
    assert body["code"] == "INDEX_MISSING_DOCUMENT"
    assert "some-other-doc" not in body["message"]  # names the MISSING doc, not the present one
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_api_health.py::test_analyze_returns_409_when_document_not_indexed -v`
Expected: FAIL — currently returns 502 (the adapter raises a generic error) or 200.

- [ ] **Step 3: Add a typed error and raise it in the default adapter**

In `engine/api.py`, add near the top-level helpers:

```python
class DocumentNotIndexedError(Exception):
    """Raised by the default Arm G adapter when a pair's document is absent
    from the anchor index — mapped by the analyze route to 409."""

    def __init__(self, document_id: str) -> None:
        super().__init__(document_id)
        self.document_id = document_id
```

Then, inside `_make_default_run_arm_g`'s `_default_run_arm_g`, after building the
`AnchorIndex`, check membership before running:

```python
    def _default_run_arm_g(src_doc: str, tgt_doc: str) -> dict[str, Any]:
        raw = json.loads(
            (artifacts_dir / "anchor-index.json").read_text(encoding="utf-8")
        )
        anchor_index = AnchorIndex(raw)
        indexed = {a["document_id"] for a in raw}
        for doc in (src_doc, tgt_doc):
            if doc not in indexed:
                raise DocumentNotIndexedError(doc)
        return _run_arm_g(anchor_index, src_doc, tgt_doc)
```

Because this lives inside the _default_ adapter, tests that inject their own
`run_arm_g_fn` (all of `test_api_arm_g.py`) bypass the check entirely — no
regression.

- [ ] **Step 4: Map the error to 409 in the analyze route**

In the analyze route (`analyze_workstream_edge`, ~line 1163), split the `try`
so the typed error becomes a 409 while other failures stay 502:

```python
        try:
            result = run_arm_g_fn(src_doc, tgt_doc)
        except DocumentNotIndexedError as exc:
            return _ws_error(
                409,
                "INDEX_MISSING_DOCUMENT",
                f"Document {exc.document_id} is not in the anchor index; "
                f"rebuild the index (with Azure Document Intelligence) before analysing.",
            )
        except Exception as exc:  # live model / creds / network failure
            return _ws_error(502, "ANALYZE_FAILED", f"Live analysis failed: {exc}")
```

- [ ] **Step 5: Run to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_api_health.py -v`
Expected: PASS (all four).

- [ ] **Step 6: Full suite + commit**

```bash
.venv/bin/python -m pytest engine/tests -q
git add engine/api.py engine/tests/test_api_health.py
git commit -m "feat(engine): return 409 INDEX_MISSING_DOCUMENT for unindexed analyze pairs"
```

### Task B4: Frontend — `fetchHealth`, `useHealth`, banner

**Files:**

- Modify: `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, `frontend/src/test/msw/handlers.ts`, `frontend/src/components/AppShell.tsx`
- Create: `frontend/src/lib/hooks/useHealth.ts`, `frontend/src/components/DegradedIndexBanner.tsx`, `frontend/src/components/DegradedIndexBanner.test.tsx`

- [ ] **Step 1: Add the type**

In `frontend/src/lib/types.ts`, add a new `// --- Health ---` section:

```ts
export interface HealthResponse {
  status: "ok" | "degraded";
  anchor_index: { documents: number };
  clause_index: { documents: number };
  demo_documents: { expected: string[]; present: string[]; missing: string[] };
}
```

- [ ] **Step 2: Add the API call**

In `frontend/src/lib/api.ts`, import `HealthResponse` at the top with the other
type imports, then add (note `/health` is NOT under `/api/`, and `getJson`
returns the body directly):

```ts
export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>(`${API_BASE}/health`);
}
```

- [ ] **Step 3: Add the query hook**

Create `frontend/src/lib/hooks/useHealth.ts`:

```ts
import { useQuery } from "@tanstack/react-query";

import { fetchHealth } from "@/lib/api";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: fetchHealth });
}
```

- [ ] **Step 4: Add the default MSW handler**

In `frontend/src/test/msw/handlers.ts`, add to the `handlers` array (MSW is
configured `onUnhandledRequest: "error"`, so every test that renders the shell
needs this default):

```ts
http.get("*/health", () =>
  HttpResponse.json({
    status: "ok",
    anchor_index: { documents: 5 },
    clause_index: { documents: 5 },
    demo_documents: { expected: [], present: [], missing: [] },
  }),
),
```

- [ ] **Step 5: Write the failing banner test**

Create `frontend/src/components/DegradedIndexBanner.test.tsx`:

```tsx
import { http, HttpResponse } from "msw";
import { screen, waitFor } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { renderApp } from "@/test/utils";
import { server } from "@/test/msw/server";

describe("DegradedIndexBanner", () => {
  it("shows the banner when the index is degraded", async () => {
    server.use(
      http.get("*/health", () =>
        HttpResponse.json({
          status: "degraded",
          anchor_index: { documents: 2 },
          clause_index: { documents: 1 },
          demo_documents: {
            expected: [],
            present: [],
            missing: ["fsb-3rd-party"],
          },
        }),
      ),
    );
    renderApp("/");
    expect(
      await screen.findByTestId("degraded-index-banner"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("degraded-index-banner")).toHaveTextContent(
      "fsb-3rd-party",
    );
  });

  it("renders no banner when the index is ok", async () => {
    renderApp("/"); // default handler returns status: ok
    await waitFor(() =>
      expect(screen.queryByTestId("degraded-index-banner")).toBeNull(),
    );
  });
});
```

- [ ] **Step 6: Run to verify it fails**

Run (from `frontend/`): `npm test -- DegradedIndexBanner`
Expected: FAIL — no `degraded-index-banner` test id (component/mount not built).

- [ ] **Step 7: Build the banner**

Create `frontend/src/components/DegradedIndexBanner.tsx` (mirrors the hand-rolled
`OverlapAlertsCard` notice idiom — `<section>`, `data-testid`, `lucide-react`
icon, rose warning tint):

```tsx
import { TriangleAlert } from "lucide-react";

import { useHealth } from "@/lib/hooks/useHealth";

export function DegradedIndexBanner() {
  const { data } = useHealth();
  if (!data || data.status !== "degraded") return null;
  const missing = data.demo_documents.missing;
  return (
    <section
      data-testid="degraded-index-banner"
      aria-label="Degraded index warning"
      className="flex items-center gap-2 border-b border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-900"
    >
      <TriangleAlert className="h-4 w-4 shrink-0" aria-hidden />
      <span>
        Document index is incomplete — analysis will be partial. Missing:{" "}
        {missing.length ? missing.join(", ") : "unknown"}. Rebuild the index
        before the demo.
      </span>
    </section>
  );
}
```

- [ ] **Step 8: Mount it in the app shell**

In `frontend/src/components/AppShell.tsx`, import the banner and place it inside
the content column, directly above `<Outlet />` (outside any page scroll region):

```tsx
import { DegradedIndexBanner } from "@/components/DegradedIndexBanner";
// ...
<div className="flex min-h-0 min-w-0 flex-1 flex-col">
  <DegradedIndexBanner />
  <Outlet />
</div>;
```

- [ ] **Step 9: Run to verify it passes**

Run (from `frontend/`): `npm test -- DegradedIndexBanner`
Expected: PASS (both cases).

- [ ] **Step 10: Full frontend suite (no regressions from the new default handler)**

Run (from `frontend/`): `npm test`
Expected: PASS. If any test that renders the shell now errors on an unhandled
`/health`, confirm Step 4's default handler is in `handlers.ts`.

- [ ] **Step 11: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/lib/hooks/useHealth.ts \
        frontend/src/components/DegradedIndexBanner.tsx frontend/src/components/DegradedIndexBanner.test.tsx \
        frontend/src/components/AppShell.tsx frontend/src/test/msw/handlers.ts
git commit -m "feat(frontend): show a degraded-index banner driven by GET /health"
```

---

## Task Group C — Analyze Fan-Out Cap (Fix 3)

### Task C1: Config constants

**Files:**

- Modify: `engine/config.py`

- [ ] **Step 1: Add the constants**

After `DEMO_DOCUMENTS` in `engine/config.py`, add:

```python
# Cap on how many anchors one document contributes to Stage-1 axis extraction.
# When a document has more anchors than this, only the highest-signal anchors
# (longest text) are extracted, so one Analyze cannot fan out without bound.
AXIS_ANCHOR_CEILING = int(os.environ.get("ARM_G_AXIS_ANCHOR_CEILING", "60"))

# Post-hoc wall-clock budget (seconds) for one analyze run. Overruns are
# recorded in the trace and, for the cross-workstream climax, trigger the
# recorded fallback. Not a mid-call preemption (that is Tier 2).
ANALYZE_BUDGET_SECONDS = float(os.environ.get("ARM_G_ANALYZE_BUDGET_SECONDS", "45"))
```

- [ ] **Step 2: Commit**

```bash
git add engine/config.py
git commit -m "feat(engine): add AXIS_ANCHOR_CEILING and ANALYZE_BUDGET_SECONDS"
```

### Task C2: Cap axis extraction to the highest-signal anchors

**Files:**

- Modify: `engine/arm_g.py`
- Modify: `engine/tests/test_arm_g.py`

- [ ] **Step 1: Write the failing cap test**

Add to `engine/tests/test_arm_g.py` (match the file's existing anchor/index
helpers — `_anchor`, `_coverage_index` — for building a fake index):

```python
def test_extract_axes_caps_to_ceiling(monkeypatch):
    import engine.arm_g as arm_g
    from engine.anchors import AnchorIndex

    # 70 anchors of varying length in one document; ceiling is lower than that.
    anchors = [
        {"anchor_id": f"d::{i}", "document_id": "d", "text": "word " * (i + 1), "clause_number": str(i)}
        for i in range(70)
    ]
    index = AnchorIndex(anchors)

    monkeypatch.setattr(arm_g, "AXIS_ANCHOR_CEILING", 60)
    monkeypatch.setattr(arm_g, "_load_axes_cache", lambda doc: {"anchors": []})
    monkeypatch.setattr(arm_g, "_write_axes_cache", lambda doc, cache: None)

    calls = []
    monkeypatch.setattr(arm_g, "_extract_axes_for_anchor", lambda a, dep: calls.append(a["anchor_id"]) or ["axis"])

    arm_g.extract_axes_for_document(index, "d")

    assert len(calls) == 60, f"expected 60 extraction calls, got {len(calls)}"
    # Deterministic selection: the 60 longest-text anchors (highest ids here).
    assert set(calls) == {f"d::{i}" for i in range(10, 70)}
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_arm_g.py::test_extract_axes_caps_to_ceiling -v`
Expected: FAIL — currently all 70 anchors are extracted.

- [ ] **Step 3: Apply the cap in `extract_axes_for_document`**

In `engine/arm_g.py`, add `AXIS_ANCHOR_CEILING` to the `engine.config` import,
then change the top of `extract_axes_for_document` (the `anchors = ...` line):

```python
    anchors = anchor_index.by_document(document_id)
    attempted = len(anchors)
    if attempted > AXIS_ANCHOR_CEILING:
        # Highest-signal = longest anchor text. Sort is stable and deterministic
        # (ties broken by anchor_id) so a capped document caps identically each run.
        anchors = sorted(
            anchors, key=lambda a: (-len(a["text"]), a["anchor_id"])
        )[:AXIS_ANCHOR_CEILING]
    cache = _load_axes_cache(document_id)
```

Then, where the cache is written back (near the `cache["anchors"] = new_entries`
line), record the cap so it is observable:

```python
    cache["anchors"] = new_entries
    cache["model"] = deployment
    cache["attempted"] = attempted
    cache["capped"] = attempted - len(anchors)
    _write_axes_cache(document_id, cache)
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_arm_g.py::test_extract_axes_caps_to_ceiling -v`
Expected: PASS.

- [ ] **Step 5: Full engine suite (no regressions)**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add engine/arm_g.py engine/tests/test_arm_g.py
git commit -m "feat(engine): cap Stage-1 axis extraction to the highest-signal anchors"
```

### Task C3: Warm-cache script

**Files:**

- Create: `scripts/warm_demo_cache.py`

- [ ] **Step 1: Write the script**

Create `scripts/warm_demo_cache.py`:

```python
"""Pre-populate the Arm G axis cache for the demo documents, so the first
Analyze click of the demo day hits a warm cache and returns fast.

Run from the repo root:  .venv/bin/python -m scripts.warm_demo_cache
"""

import json
from pathlib import Path

from engine.anchors import AnchorIndex
from engine.arm_g import extract_axes_for_document
from engine.config import DEMO_DOCUMENTS, REPO_ROOT


def main() -> None:
    index_path = REPO_ROOT / "data" / "artifacts" / "anchor-index.json"
    if not index_path.exists():
        raise SystemExit(f"No anchor index at {index_path}; build it (with DI) first.")
    index = AnchorIndex(json.loads(index_path.read_text(encoding="utf-8")))
    indexed = {a["document_id"] for a in index.all()}
    for doc in DEMO_DOCUMENTS:
        if doc not in indexed:
            print(f"skip {doc}: not in anchor index")
            continue
        print(f"warming {doc} ...")
        extract_axes_for_document(index, doc)
    print("done — axis cache warmed for the demo documents.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-run it (offline-safe check)**

Run: `.venv/bin/python -c "import ast; ast.parse(open('scripts/warm_demo_cache.py').read())"`
Expected: no output (parses). A full run needs live model credentials and is a
rehearsal step, not a CI step — do not run it in CI.

- [ ] **Step 3: Commit**

```bash
git add scripts/warm_demo_cache.py
git commit -m "feat(scripts): add warm_demo_cache to pre-warm the demo axis cache"
```

### Task C4: Post-hoc budget signal

**Files:**

- Modify: `engine/arm_g.py`

> **Confirm the scope refinement first (see the plan header).** This step detects
> and records an overrun after the run; it does not preempt a synchronous call.
> The demo-safety comes from C2 (cap) + C3 (warm cache) making the run fast, and
> from Task Group D falling back on failure/empty.

- [ ] **Step 1: Record elapsed time in the trace**

In `engine/arm_g.py`, in `run_arm_g`, wrap the pipeline body with a monotonic
timer and stamp the trace (import `time` and `ANALYZE_BUDGET_SECONDS`):

```python
    started = time.monotonic()
    # ... existing six-stage body, building `trace` ...
    elapsed = time.monotonic() - started
    trace["elapsed_seconds"] = round(elapsed, 2)
    trace["over_budget"] = elapsed > ANALYZE_BUDGET_SECONDS
```

(Place the two trailing lines just before `run_arm_g` returns its result dict, so
`trace` already exists. If `run_arm_g` builds the result in a helper, stamp the
`trace` sub-dict there instead.)

- [ ] **Step 2: Full engine suite**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS (the smoke test's stub returns `trace: {}`, unaffected).

- [ ] **Step 3: Commit**

```bash
git add engine/arm_g.py
git commit -m "feat(engine): record analyze elapsed time and over-budget flag in the trace"
```

---

## Task Group D — Cross-Workstream Climax (Fix 2)

### Task D1: Record the safety-net trace

**Files:**

- Create: `data/workstreams/_cross/recorded-traces/<demo-edge>.json`

- [ ] **Step 1: Identify the demo cross-link edge id**

Run: `.venv/bin/python -c "import json,glob; p=glob.glob('data/workstreams/_cross/graph.json')[0]; g=json.load(open(p)); print([e['id'] for e in g['edges']])"`
Expected: prints the cross-link edge ids. Pick the OpRes × Open Finance ED edge
(the brief's demo-hero linkage) — note its id as `<demo-edge>`.

- [ ] **Step 2: Author the recorded trace from today's fixture findings**

The recorded fallback must reproduce exactly what ships today. Copy the committed
findings the current cross-link detail already serves for `<demo-edge>` into a
trace file shaped like a `run_arm_g` result (`connections`/`unsupported`/`trace`),
so the same `connections_to_findings` mapper produces the same cards:

Run: `.venv/bin/python -c "import json; f=json.load(open('data/workstreams/_cross/findings/<demo-edge>.json')); json.dump({'connections': f, 'unsupported': [], 'trace': {'recorded': True}}, open('data/workstreams/_cross/recorded-traces/<demo-edge>.json','w'), indent=2)"`

(Adjust the source path to where `_cross` findings actually live; confirm with
`ls data/workstreams/_cross`.)

- [ ] **Step 3: Commit**

```bash
git add data/workstreams/_cross/recorded-traces/
git commit -m "chore(data): record the demo cross-link trace as the climax fallback"
```

### Task D2: Live-with-recorded-fallback on the cross-link detail route

**Files:**

- Modify: `engine/api.py` (`get_cross_link_detail`)
- Modify: `engine/tests/test_api_cross_links.py`

- [ ] **Step 1: Write the failing fallback tests**

Add to `engine/tests/test_api_cross_links.py` (reuse the file's existing
`_make_client` / `_links` helpers; inject `run_arm_g_fn`):

```python
def test_cross_link_falls_back_to_recorded_when_live_raises(tmp_path):
    def boom(src, tgt):
        raise RuntimeError("live pipeline down")

    client, _ = _make_client(tmp_path, run_arm_g_fn=boom)
    edge_id = _links(client)[0]["id"]
    res = client.get(f"/api/cross-links/{edge_id}")
    assert res.status_code == 200
    assert res.json()["source"] == "recorded"


def test_cross_link_reports_live_on_success(tmp_path):
    def ok(src, tgt):
        return {
            "connections": [{
                "summary": "Open Finance mandates board oversight; OpRes is silent.",
                "label": "goes-beyond",
                "sentiment": None,
                "source_clauses": [{"clause_number": "Open Finance 7.1", "text": "The board must oversee open finance risk."}],
                "target_clauses": [],
                "scope_note": None,
                "supported": True,
            }],
            "unsupported": [],
            "trace": {},
        }

    client, _ = _make_client(tmp_path, run_arm_g_fn=ok)
    edge_id = _links(client)[0]["id"]
    res = client.get(f"/api/cross-links/{edge_id}")
    assert res.status_code == 200
    assert res.json()["source"] == "live"
```

Confirm `_make_client` in `test_api_cross_links.py` accepts `run_arm_g_fn`; if it
does not, extend it exactly as `test_api_workstreams.py::_make_client` does
(pass the kwarg through to `create_app`).

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest engine/tests/test_api_cross_links.py -k fallback -v`
Expected: FAIL — no `source` field on the response.

- [ ] **Step 3: Add the live-attempt-then-fallback logic**

In `get_cross_link_detail` (`engine/api.py`, ~line 788), after loading the edge
and before assembling the panel, attempt the live pipeline and fall back:

```python
        source = "recorded"
        near_doc = near_node.get("document_id")
        far_doc = far_node.get("document_id")
        recorded_path = (
            workstreams_dir / CROSS_STORE / "recorded-traces" / f"{edge_id}.json"
        )
        if near_doc and far_doc:
            try:
                result = run_arm_g_fn(near_doc, far_doc)
                if result.get("connections"):
                    edge_findings = workstreams.connections_to_findings(result)
                    source = "live"
            except Exception:
                pass  # any failure → recorded fallback below
        if source == "recorded" and recorded_path.exists():
            recorded = json.loads(recorded_path.read_text(encoding="utf-8"))
            edge_findings = workstreams.connections_to_findings(recorded)
```

Then compute `labels`/`counts` from the resulting `edge_findings` (reuse the
existing `_cross_link_findings_summary` / `findings.counts` calls, but source the
findings from the block above rather than only from disk), and add `"source":
source` to the returned dict. Keep the verbatim guarantee intact: cards render
`edge_findings`' own stored clause text on both paths.

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/python -m pytest engine/tests/test_api_cross_links.py -v`
Expected: PASS (new + existing cross-link tests).

- [ ] **Step 5: Add the verbatim + label guard test**

Append to `engine/tests/test_api_cross_links.py`:

```python
def test_cross_link_cards_are_verbatim_and_labels_valid(tmp_path):
    client, _ = _make_client(tmp_path)  # default: recorded path
    edge_id = _links(client)[0]["id"]
    body = client.get(f"/api/cross-links/{edge_id}").json()
    labels = {"aligns-with", "differs-on", "conflicts-with", "silent-on", "goes-beyond"}
    for f in body["findings"]:
        assert f["label"] in labels
        for side in ("source_clauses", "target_clauses"):
            for c in f.get(side) or []:
                assert c.get("text"), "clause card has no verbatim text"
```

- [ ] **Step 6: Run it, then the full suite**

Run: `.venv/bin/python -m pytest engine/tests/test_api_cross_links.py -v`
Expected: PASS.
Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS.

- [ ] **Step 7: Update the smoke test to assert `source`**

In `engine/tests/test_demo_smoke.py` Stage 5, add after fetching `detail`:

```python
    assert detail.json()["source"] in ("live", "recorded"), "STAGE cross-link: no source field"
```

Run: `.venv/bin/python -m pytest engine/tests/test_demo_smoke.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add engine/api.py engine/tests/test_api_cross_links.py engine/tests/test_demo_smoke.py
git commit -m "feat(engine): cross-link climax attempts live analysis, falls back to recorded"
```

### Task D3: Surface `source` in the frontend (optional, low-risk)

**Files:**

- Modify: `frontend/src/lib/types.ts` (add `source?: "live" | "recorded"` to the cross-link detail type)

- [ ] **Step 1: Extend the type only**

Add `source?: "live" | "recorded";` to the `CrossLinkDetail` interface in
`frontend/src/lib/types.ts`. No UI change is required for the demo — the field is
observable in the network response. A visible "live/recorded" badge is a nice-to-
have, not in scope.

- [ ] **Step 2: Frontend suite + commit**

```bash
cd frontend && npm test -- --run && cd ..
git add frontend/src/lib/types.ts
git commit -m "chore(frontend): type the cross-link source field"
```

---

## Final Verification

- [ ] **Full engine suite green**

Run: `.venv/bin/python -m pytest engine/tests -q`
Expected: PASS — original tests + smoke + health + cap + cross-link fallback.

- [ ] **Full frontend suite green**

Run (from `frontend/`): `npm test -- --run`
Expected: PASS.

- [ ] **Smoke test is the last thing you run before the demo**

Run: `.venv/bin/python -m pytest engine/tests/test_demo_smoke.py -v`
Expected: PASS. A red result names the broken stage.

- [ ] **Warm the cache during rehearsal (needs live creds — not CI)**

Run: `.venv/bin/python -m scripts.warm_demo_cache`
Expected: "done — axis cache warmed for the demo documents."
