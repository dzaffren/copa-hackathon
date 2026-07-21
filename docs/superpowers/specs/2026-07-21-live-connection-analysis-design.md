# Live Connection Analysis — Design

**Date:** 2026-07-21
**Status:** Approved design → ready for implementation plan
**Scope:** Engine + frontend. Make the "Analyze linkages" button run the _real_
finder→critic loop on edges whose endpoints are ingested documents, instead of
replaying hand-authored canned findings.

## Problem

The demo is pre-baked. The screens (`frontend/`) and the real engine
(`engine.connections.find_connections`) live in two disconnected worlds joined by
a hard-coded string: the `analyze` route replays `workstreams.canned_analysis`,
never calling the finder.

The root cause is a missing seam: **every workstream graph node has
`document_id: None`.** The UI nodes (`bcbs-opres-2021`, `rmit-pd-2025`,
`of-ed-2025`) carry no link to the ingested engine documents
(`opres-v1-2025-draft`, `open-finance-v1-2025-ed`, …). So even though the engine
now has 9 documents / 1,755 real clauses and a working finder→critic loop, the UI
cannot say "analyze _this_ node against _that_ one" — there is nothing to pass.

## The seam

```
Graph node ──(new: document_id)──▶ ClauseIndex ──▶ find_connections() ──▶ adapter ──▶ save_findings ──▶ Review screen (unchanged)
```

Three connected changes:

1. **Node → document_id mapping** in the workstream `graph.json` files.
2. **Live analyze route** that resolves both endpoints' `document_id`s, loads the
   `ClauseIndex`, calls the real `find_connections`, adapts the result, and saves
   it as the edge's findings file.
3. **The button** calls the live route with a real (~30–60s) loading state.

This is low-risk because the `Connection` shape `find_connections` returns already
matches the workstream finding shape almost exactly.

## Node → document_id mapping

Add `document_id` only to nodes with an ingested counterpart:

| node_id             | document_id               |
| ------------------- | ------------------------- |
| `opres-pd-v0-3`     | `opres-v1-2025-draft`     |
| `opres-dp-2025`     | `opres-v1-2025-draft`     |
| `rmit-pd-2025`      | `rmit-v2-2025`            |
| `rmit-pd-2023`      | `rmit-v1-2023`            |
| `rmit-pd-v2`        | `rmit-v2-2025`            |
| `of-ed-2025`        | `open-finance-v1-2025-ed` |
| `bcm-pd-2022`       | `bcm-v1-2022`             |
| `outsourcing-pd-v2` | `outsourcing-v1-2019`     |

Nodes with **no** ingested document (`bcbs-opres-2021`, `fsb-3rd-party`,
`hkma-spm-or2`, `fsa-2013-143`, `abm-position`, `risk-governance-pd-2013`,
`eba-outsourcing-2019`, `mas-outsourcing`, `bcbs-239`, `opres-pd-v0-0`) get no
`document_id` and are honestly non-analysable-live.

### Live-capable edges (both endpoints ingested): 4 of 17

| Workstream        | Edge                        | Note                    |
| ----------------- | --------------------------- | ----------------------- |
| `_cross`          | Open Finance ED ↔ OpRes     | cross-workstream climax |
| `opres-v2`        | OpRes draft ↔ RMiT PD 2025  | version-drift story     |
| `open-finance-ed` | Open Finance ED ↔ RMiT 2023 | new live pair           |
| `open-finance-ed` | Open Finance ED ↔ BCM 2022  | new live pair           |

The other 13 edges have ≥1 endpoint with no ingested source document, or are
self-compare / empty-draft. **Not in scope to fix by ingesting more docs** — a
much larger corpus effort deferred earlier.

## Route

**Decision: replace the canned route**, do not add a parallel one.

`POST /api/workstreams/{workstream_id}/edges/{edge_id}/analyze` becomes live:

1. Load the workstream graph; 404 if workstream/edge missing (unchanged).
2. Resolve `source`/`target` node `document_id`s.
   - If either is absent → `409 not_analysable`, body names the offending node.
     Do **not** write a findings file (edge stays unanalysed, re-analysable).
3. Load the `ClauseIndex` from `data/artifacts/` (the API gains a clause-index
   read for this route only — it previously never read the index).
4. Call `find_connections(task_doc_id, other_doc_id, clause_index, ...)` with the
   **task/source node as `doc_a`** so `silent-on`/`goes-beyond` read in the right
   direction (matches the "task node is edge source" convention).
5. Adapt `result["connections"]` → findings, `save_findings(...)`, return the
   same JSON shape the route returns today (`{id, status:"analysed", findings,
findings_count}`).
6. On a live-call failure (creds/network/model) → `502 analyze_failed` with a
   message; no findings file written; button offers retry.

### Injectable seam for tests

`create_app()` currently takes `analyze_delay`. Replace it with an injectable
`find_connections_fn` (default: the real `engine.connections.find_connections`),
so CI stubs the model exactly as `test_connections.py` already injects
`finder_fn`/`critic_fn`. Remove `analyze_delay` and its `time.sleep` — real
latency replaces the fake delay.

## Adapter

`find_connections` returns `{connections[], unsupported[]}`. A small adapter
(`workstreams.py`):

- Takes `result["connections"]` (supported, verbatim-cited only).
- Per connection adds `id` (stable hash of `summary` + cited clause numbers) and
  `review_state: "pending"` — the only two fields workstream findings have that
  `Connection` lacks.
- Passes through unchanged: `summary`, `label`, `sentiment`, `source_clauses`
  (with verbatim `text`), `target_clauses`, `scope_note`, `supported`.
- **Excludes** `result["unsupported"]` — preserving the "never invent" guarantee.

Fixture findings for the 4 live edges are **overwritten** by a live run: the
curated fixture is the pre-seeded state; a live analyze refreshes it via the
existing `save_findings`.

## Frontend

- Button behavior is per-edge, data-driven:
  - Both nodes have `document_id` → **"⚡ Analyze live"** (enabled).
  - Otherwise → disabled, tooltip: "Live analysis needs both documents ingested —
    {node} isn't in the corpus yet."
- On click → spinner + "Analyzing… the AI is reading both documents"; on success
  the edge flips to analysed and the findings render (Review/Task screens
  unchanged). On `502` → inline error + retry. On `409` → shouldn't occur (button
  disabled) but render the message rather than crash.

## Testing

- **Adapter unit test:** `Connection` → finding shape; `id`/`review_state` added;
  `unsupported` excluded; verbatim text preserved.
- **Route test (stubbed `find_connections_fn`):** live path saves findings, edge
  becomes analysed, returns correct shape. No live model in CI.
- **`not_analysable` test:** edge with a node lacking `document_id` → 409, no file
  written.
- **`analyze_failed` test:** stub raises → 502, no file written.
- **Existing canned-route tests updated:** `test_api_workstreams.py` (8 refs) plus
  single refs in `test_api_review.py`, `test_api_new_workstream.py`,
  `test_api_cross_links.py`, `test_api_drafting.py` — migrate from canned
  expectations to the stubbed live route.
- **Manual live smoke-run** on the `_cross` edge before the demo.

## Non-goals

- Ingesting BCBS/HKMA/FSB/FSA/EBA/MAS reference documents (larger corpus effort).
- Changing the Review/Task/Graph screens' rendering.
- Uploading arbitrary user documents (the separate "first-run journey" idea).
- Removing `canned_analysis` from `workstreams.py` immediately — leave the
  function in place (unused) unless the plan finds it cleanly removable.

## Files touched

- `data/workstreams/*/graph.json` — add `document_id` to mapped nodes.
- `engine/api.py` — rewrite the `analyze` route; swap `analyze_delay` for
  `find_connections_fn`; add clause-index load.
- `engine/workstreams.py` — add the connection→finding adapter.
- `engine/tests/` — new adapter/route tests; migrate canned-route tests.
- `frontend/` — button state + live-call loading/error handling.
