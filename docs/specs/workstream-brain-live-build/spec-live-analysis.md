# Analyse a Linkage on a Self-Built Workstream

**Ticket:** TBD
**Type:** Technical — Migration (data-source repointing)

Linkage analysis today only works on documents prepared ahead of time by an
offline build step, reading from one shared, pre-built store. A drafter who
builds a workstream inside the app cannot analyse the connections they draw,
because the documents they added are not in that shared store. This work
repoints linkage analysis so it reads from each workstream's own prepared
passages, making "Analyze linkage" work on the documents the drafter built
themselves — the last piece needed for a fully build-it-yourself workstream.

## Motivation

The headline capability of Workstream Brain is surfacing labelled linkages
between two documents, each quoted verbatim. For the COPA Hackathon 2026 demo
(3 Aug 2026), the team is building the demo workstreams live in the app and
removing the outdated pre-seeded examples. If analysis keeps reading from the
shared pre-built store, then everything a drafter adds through the app is
un-analysable, and the demo's climax — a drafter analysing a connection they
drew and seeing findings — cannot happen.

**Current state:** "Analyze linkage" only produces findings for documents that
an offline build step placed in a single, shared pre-built store. It looks each
side of a connection up in that shared store. A document a drafter adds and
breaks into passages inside the app never lands there, so its connections
cannot be analysed. The shared store also covers only a subset of the demo
corpus, so most real BNM documents have nothing to analyse against.

**Desired state:** "Analyze linkage" reads each side of a connection from the
workstream's own prepared passages — the same passages produced when the
drafter broke each document up on adding it. Any connection between two
different documents in the same workstream, each broken into passages, can be
analysed and produces findings, each quoting the exact passages it relies on.
The results are saved with the workstream so they survive to the demo.

**Trigger:** A blocked feature. The "Add a document", "Extract concepts" and
"Connect two documents" stories now let a drafter assemble a real workstream,
but the final step — analysing a connection they built — is still wired to the
old shared store and returns nothing for self-built documents. The pre-seeded
examples that the old wiring depended on are being deleted, so the build-it-
yourself flow must stand entirely on its own.

## Scope

- **In scope:**
  - Repoint linkage analysis so it reads both documents of a connection from
    the workstream's own prepared passages instead of the shared pre-built
    store.
  - Have analysis extract, on its own, whatever concepts it needs for the two
    documents, and reuse any concepts already extracted (by the "Extract
    concepts" story) so it never repeats that work.
  - Preserve the existing rules that a connection with a document missing on one
    side, and a connection whose two sides are the same document, cannot be
    analysed, each with a clear message.
  - Save the resulting findings with the workstream so they persist across
    re-opening.
  - Surface a genuine analysis failure (model or connection problem) and a
    genuine "nothing found" outcome clearly, and in both cases leave the
    connection in a clean, re-analysable state — never half-analysed.

- **Out of scope:**
  - **Cross-workstream analysis.** Analysing a connection whose two documents
    belong to different workstreams (the eventual demo climax) is a separate
    spec and an epic Non-Goal.
  - Changing how a document is broken into passages, or how concepts are
    extracted — both are reused unchanged from their own stories.
  - Changing the five finding labels, the tighten/loosen sentiment rule, or the
    verbatim-citation guarantee.
  - Any re-analysis scheduling, background processing, or automatic re-running
    when a document changes.

## Goals

- A connection between two different self-built documents in one workstream,
  each broken into passages, produces findings on demand — with zero reliance
  on the shared pre-built store or any offline preparation for that workstream.
- 100% of findings quote a real passage from the cited document; no invented
  quotes, preserving the verbatim guarantee.
- Analysis never re-derives concepts that already exist for a document — a
  second analysis touching a document whose concepts were already extracted
  reuses them.
- A failed or empty analysis never leaves a connection half-analysed: it is
  either fully saved with findings or left exactly as re-analysable as before.

## Non-Goals

- Cross-workstream connection and analysis (deferred to a separate spec).
- Re-running analysis automatically, or notifying the drafter when a document's
  passages change after a connection was analysed.
- Any change to the "Extract concepts" button behaviour — it still lets a
  drafter see concepts earlier, but is no longer a prerequisite for analysis.

## Success Criteria

- On a workstream built entirely inside the app, the drafter can select a
  connection between two of their documents, run "Analyze linkage", and see
  findings labelled with the five semantic labels, each quoting the exact
  passages it relies on.
- Re-opening that workstream on a later day shows the same findings, unchanged.
- A connection where one side has no document, and a connection whose two sides
  are the same document, both refuse analysis with a clear message and no
  findings are written.
- When analysis genuinely fails or genuinely finds nothing, the connection is
  reported clearly and remains available to analyse again — it never shows as
  analysed-with-no-results in a way that cannot be retried.

## Acceptance Criteria

> Scenarios are written from the drafter's point of view — what they do and what
> they observe — not from the internals of where passages are read.

### Scenario: Analysing a connection between two self-built documents produces findings

```gherkin
Background:
  Given Aisyah has built her "Operational Resilience" workstream inside the app
    And it holds these documents, each broken into passages:
      | Document                                          | Broken into passages |
      | Operational Resilience PD v0.3 (her focal draft)  | yes                  |
      | BCBS Principles for Operational Resilience 2021   | yes                  |
    And she has drawn a connection between the two documents

Scenario: Findings appear, each quoting exact passages
  Given Aisyah has opened the connection between her Operational Resilience PD
        and the BCBS Principles for Operational Resilience 2021
  When she clicks "Analyze linkage"
  Then she sees a set of findings between the two documents
    And each finding carries exactly one label from aligns-with, differs-on,
        conflicts-with, silent-on, or goes-beyond
    And each finding quotes the exact passages it relies on, with their numbers
    And no finding quotes a passage that is not present in the cited document
```

### Scenario: Analysis works for any two different documents in the workstream

```gherkin
Scenario Outline: Any two distinct, broken-up documents can be analysed
  Given Aisyah has a connection between "<near document>" and "<far document>"
        in the same workstream
    And both documents have been broken into passages
  When she clicks "Analyze linkage"
  Then she sees findings between the two documents
    And every finding quotes real passages from the documents it cites

  Examples:
    | near document                    | far document                                    |
    | Operational Resilience PD v0.3   | BCBS Principles for Operational Resilience 2021 |
    | Operational Resilience PD v0.3   | FSB Cyber Incident Reporting 2023               |
    | Operational Resilience PD v0.3   | HKMA Operational Resilience SPM 2022            |
```

### Scenario: Concepts already extracted are reused, not re-derived

```gherkin
Scenario: A prior "Extract concepts" run is reused by analysis
  Given Aisyah has already run "Extract concepts" on her Operational Resilience
        PD v0.3, so its concepts are shown on the node
    And she has a connection from that document to the BCBS Principles 2021
  When she clicks "Analyze linkage"
  Then she sees findings between the two documents
    And the concepts already shown on her Operational Resilience PD node are
        unchanged
    And the analysis does not repeat the concept-extraction work that was
        already done for that document
```

### Scenario: Analysis extracts what it needs on its own when concepts were never extracted

```gherkin
Scenario: Analysis does not require concepts to be extracted first
  Given Aisyah has a connection between two documents, each broken into passages
    And she has NOT clicked "Extract concepts" on either document
  When she clicks "Analyze linkage"
  Then she sees findings between the two documents
    And she is never told to extract concepts first
```

### Scenario: A second, related analysis reuses concepts derived by the first

```gherkin
Scenario: Concepts derived during one analysis are reused by the next
  Given Aisyah has analysed the connection between her Operational Resilience
        PD v0.3 and the BCBS Principles 2021
    And she also has a connection between her Operational Resilience PD v0.3 and
        the FSB Cyber Incident Reporting 2023
  When she clicks "Analyze linkage" on the second connection
  Then she sees findings between her draft and the FSB document
    And the concepts for her Operational Resilience PD v0.3 are reused rather
        than derived again
```

### Scenario: A connection with a document missing on one side cannot be analysed

```gherkin
Scenario: The far document is missing
  Given Aisyah has a connection from her Operational Resilience PD v0.3 to a
        placeholder node that has no document attached
  When she clicks "Analyze linkage"
  Then she is told the connection cannot be analysed because that side has no
        document
    And no findings are saved for the connection
    And the connection is still shown as not analysed
```

### Scenario: A connection whose two sides are the same document cannot be analysed

```gherkin
Scenario: Both sides resolve to the same document
  Given Aisyah has a connection whose two nodes both point at the same document
  When she clicks "Analyze linkage"
  Then she is told there is nothing to compare because both sides are the same
        document
    And no findings are saved for the connection
    And the connection is still shown as not analysed
```

### Scenario: Analysis genuinely fails and leaves no half-analysed state

```gherkin
Scenario: A model or connection problem during analysis
  Given Aisyah has a valid connection between two different, broken-up documents
    And the analysis service cannot be reached during the run
  When she clicks "Analyze linkage"
  Then she is told the analysis failed and can be tried again
    And no findings are saved for the connection
    And the connection is still shown as not analysed
    And clicking "Analyze linkage" again re-runs the analysis cleanly
```

### Scenario: Analysis genuinely finds nothing and stays re-analysable

```gherkin
Scenario: No linkages found between the two documents
  Given Aisyah has a valid connection between two different, broken-up documents
    And the analysis honestly finds no linkages between them
  When she clicks "Analyze linkage"
  Then she is told no linkages were found
    And no findings are saved for the connection
    And the connection is still shown as not analysed
    And she can click "Analyze linkage" again later
```

### Scenario: Saved findings persist across re-opening the workstream

```gherkin
Scenario: Findings survive to the next day
  Given Aisyah analysed the connection between her Operational Resilience PD
        v0.3 and the BCBS Principles 2021 yesterday and saw findings
  When she re-opens the "Operational Resilience" workstream today
    And opens that same connection
  Then she sees the same findings she saw yesterday, unchanged
    And each finding still quotes the exact passages it relied on
```

## Constraints

- **Backwards compatibility:** The observable behaviour of analysing a
  connection is unchanged — same five labels, same verbatim-quoting findings,
  same refusal messages for missing-document and same-document connections. What
  changes is only where the two documents' passages are read from. Any
  workstream whose findings were already saved keeps showing them unchanged.
- **Downtime:** None. This is preparation-time and demo-time behaviour; there is
  no live service to take down.
- **Compliance:** The verbatim-citation product rule is absolute — every finding
  must quote the exact passages it relies on, and where nothing supports a claim
  the tool must say so rather than invent a quote. This work must preserve that
  guarantee end to end.
- **Rollback:** Reversible. If the repointed analysis misbehaves during
  preparation, reverting to the previous wiring restores the old behaviour;
  findings already saved with a workstream are unaffected either way.

## Dependencies

- **Add a document and break it into passages** — analysis reads each document's
  own passages, which that story produces on adding a document.
- **Connect two existing documents** — analysis runs on a connection, which that
  story lets the drafter draw between any two documents on the canvas.
- **Extract concepts** — analysis reuses concepts this story extracts when they
  already exist, and derives its own when they do not; the two must agree on
  where a document's concepts live so neither repeats the other's work.
- Access to the language model used for concept extraction and linkage analysis
  during preparation and on the demo day.
- Removal of the outdated pre-seeded example workstreams, so the build-it-
  yourself flow is the sole path being demonstrated.

## Open Questions

- [x] ~~Must the drafter extract concepts before analysing?~~ — **Resolved:**
      No. Analysis extracts whatever concepts it needs itself and reuses any that
      already exist, so it never repeats the work and never blocks on the
      "Extract concepts" button.
- [x] ~~What happens to a connection when analysis finds nothing?~~ —
      **Resolved:** The drafter is told no linkages were found, nothing is saved,
      and the connection stays not analysed so it can be run again — a "nothing
      found" outcome must never one-way-flip a connection to analysed-with-no-
      results.
- [x] ~~What happens to a connection when analysis fails partway?~~ —
      **Resolved:** Findings are saved only after a full, successful run, so a
      failure leaves the connection exactly as it was — not analysed, and cleanly
      re-runnable. There is never a half-analysed state.
- [x] ~~Does this cover connections spanning two workstreams?~~ — **Resolved:**
      No. Cross-workstream analysis is an epic Non-Goal and a separate spec; this
      work is same-workstream only.

---

## Technical Goals

- The default `run_arm_g_fn` adapter resolves both edge endpoints' passages from
  the **workstream's own** anchors via `ws_anchors.build_index(workstreams_dir,
workstream_id)`, so `POST /api/workstreams/{ws}/edges/{edge}/analyze` on a
  self-built workstream succeeds with **zero reads** of
  `data/artifacts/anchor-index.json`.
- The axis cache is per-workstream: stage 1 reads/writes
  `data/workstreams/{workstream_id}/axes/axes-{document_id}.json` (via an
  `axes_dir` parameter), so a warm cache from the "Extract concepts" story (or a
  prior analysis) is a **cache hit** — analysis re-calls the model **zero** times
  for anchors whose `text_hash` + `axis_cap` are unchanged.
- The `create_app(..., run_arm_g_fn=fake_fn)` injection seam is unchanged: the
  seam signature stays `(src_doc, tgt_doc) -> {"connections","unsupported",
"trace"}`, so every existing stub in `engine/tests/test_api_analyze_live.py`
  keeps working without edit.
- All five preserved behaviours (missing-doc 409, same-doc 409, 502 on raise,
  `no_linkages_found` with no file written, success → `save_findings`) hold
  exactly as today, verified by the existing suite plus one new adapter test.

## Success Criteria

- With `data/artifacts/anchor-index.json` **absent** but a workstream's own
  `anchors/{node_id}.json` files present, analysing an edge between two distinct
  chunked nodes returns `status: "analysed"` and writes
  `data/workstreams/{ws}/findings/{edge_id}.json` — proving no reliance on the
  shared store.
- A test asserts the default adapter's `AnchorIndex` is built from
  `ws_anchors.build_index(...)` and not from the artifacts file (adapter is
  analysable with the artifacts file removed).
- A cache-reuse test seeds a warm `axes/axes-{document_id}.json` and asserts the
  model extraction call for those anchors is **not** invoked (hit count == anchor
  count, extraction-call count == 0).
- `engine/tests/test_api_analyze_live.py` and `engine/tests/test_arm_g.py` pass
  with no changes to their existing assertions beyond the additions listed under
  Verification.

## Constraints & Risks

- **Backwards compatibility:** Observable behaviour is unchanged — same five
  labels, same `sentiment` rule (`tighten`/`loosen`/`neutral`, `differs-on`
  only), same verbatim citation, same `{code, message}` error bodies, same
  status strings (`analysed` / `no_linkages_found` / the two `NOT_ANALYSABLE`
  409s / `ANALYZE_FAILED` 502). The `run_arm_g_fn` injection seam and its
  `(src_doc, tgt_doc)` signature are unchanged, so all injected stubs keep
  working. Any workstream whose `findings/{edge_id}.json` was already saved keeps
  rendering it — nothing re-runs on read.
- **Downtime:** None. This is preparation-time and demo-time behaviour; there is
  no running service to interrupt.
- **Compliance:** The verbatim-citation product rule is absolute. Arm G already
  reads clause text from the `AnchorIndex` (`_AnchorAsClauseIndex` shim) and
  `connections_to_findings` copies that text into each finding's
  `source_clauses` / `target_clauses` verbatim; this change only swaps **which**
  anchors populate the index (workstream anchors vs. the shared file), so the
  guarantee is preserved end to end.
- **Rollback plan:** Revert the adapter. `_make_default_run_arm_g` currently
  closes over `artifacts_dir` and loads `anchor-index.json`; if the repointed
  adapter misbehaves during preparation, restore that single function (and drop
  the `axes_dir` argument) to return to the shared-store behaviour. Findings
  already saved are unaffected either way.
- **Risks:**
  - _Un-chunked endpoint._ A workstream node with a `document_id` but no
    `anchors/{node_id}.json` produces an empty `by_document(document_id)`, so
    stage 1 yields no axes and the run finds nothing → `no_linkages_found`
    (re-analysable), or the missing `document_id` is caught earlier by the
    existing 409 `NOT_ANALYSABLE` guard. Guarded, not a regression.
  - _`build_index` cost is O(workstream anchor files)._ It unions and dedups
    every anchor file in the workstream per analyze call. Trivial at demo scale
    (single-digit documents, hundreds of anchors); no caching layer added.
  - _Chunked-node identity._ A chunked node's `document_id` equals its node id
    (shared contract). If a graph node's `document_id` does not match the id used
    to write its anchor file, `by_document` returns empty — same
    `no_linkages_found` fallback, surfaced by the empty-findings path.

## Solution Design

Today the analyze route (`engine/api.py::analyze_workstream_edge`, ~1119)
resolves `src_doc` / `tgt_doc` from `graph.json` and calls the injected
`run_arm_g_fn(src_doc, tgt_doc)`. When no stub is injected, `create_app` binds
the default seam via `_make_default_run_arm_g(artifacts_dir)` (~398), whose
closure loads **one shared** `data/artifacts/anchor-index.json` into an
`AnchorIndex` and calls `engine.arm_g.run_arm_g(anchor_index, src_doc, tgt_doc)`.
Self-built documents (whose anchors live per-workstream, written by the
add-node-chunking story) are absent from that shared file, so they resolve to
empty and cannot be analysed.

**Before** (shared-store adapter, `_make_default_run_arm_g(artifacts_dir)`):

```
def _default_run_arm_g(src_doc, tgt_doc):
    raw = json.loads((artifacts_dir / "anchor-index.json").read_text("utf-8"))
    anchor_index = AnchorIndex(raw)
    return _run_arm_g(anchor_index, src_doc, tgt_doc)
```

**After** (workstream-aware adapter — the index and the axis cache are both
per-workstream). Because the seam signature must stay `(src_doc, tgt_doc)`, the
adapter is made **workstream-aware** by binding `workstreams_dir` +
`workstream_id` into its closure. Two equivalent shapes; pick the one that keeps
the route thin:

- _Option A (route-builds-the-adapter):_ the analyze route, when the caller did
  not inject a stub, constructs the adapter per request from `workstreams_dir` +
  the path `workstream_id`, then calls it `(src_doc, tgt_doc)`. `create_app`
  leaves `run_arm_g_fn=None` as the "use the default, workstream-aware adapter"
  sentinel; an injected stub short-circuits this entirely.
- _Option B (workstream-aware factory):_ `_make_default_run_arm_g` takes
  `workstreams_dir` and returns an adapter of signature `(workstream_id, src_doc,
tgt_doc)`; the route passes `workstream_id` through. The injected-stub seam
  stays `(src_doc, tgt_doc)` by having the route detect the default vs. an
  injected stub.

Option A is preferred — it keeps the public seam contract `(src_doc, tgt_doc)`
byte-for-byte and confines the workstream awareness to the route. The adapter
body becomes:

```
def _default_run_arm_g(src_doc, tgt_doc):
    anchor_index = ws_anchors.build_index(workstreams_dir, workstream_id)
    axes_dir = Path(workstreams_dir) / workstream_id / "axes"
    return _run_arm_g(anchor_index, src_doc, tgt_doc, axes_dir=axes_dir)
```

`axes_dir` is threaded through `run_arm_g(..., axes_dir=...)` into both
`extract_axes_for_document(anchor_index, doc, axes_dir=axes_dir)` calls (stage 1,
`engine/arm_g.py` ~945-946). `extract_axes_for_document` (~185) currently reads
the module-level `AXES_DIR = REPO_ROOT / "experiments"` via `_load_axes_cache` /
`_write_axes_cache`; it gains an `axes_dir: Path` parameter (defaulting to
`AXES_DIR` for backwards compatibility) that both cache helpers honour, so the
cache file becomes `axes_dir / f"axes-{document_id}.json"` — i.e.
`data/workstreams/{workstream_id}/axes/axes-{document_id}.json`. The cache-hit
logic (keyed by `text_hash` + `axis_cap`) is untouched, so a cache pre-warmed by
the "Extract concepts" story is reused verbatim.

Everything downstream of stage 1 is unchanged: `connections_to_findings`,
`save_findings`, the empty-findings guard, and the two 409 / one 502 guards in
the route all read exactly as today.

**Shared contract (reproduced verbatim — three sibling specs share it):**

> A module `engine/ws_anchors.py` (created by the "add-node-chunking" story)
> stores per-node anchors at
> `data/workstreams/{workstream_id}/anchors/{node_id}.json` and exposes
> `build_index(workstreams_dir, workstream_id) -> AnchorIndex` (unions all the
> workstream's anchor files, dedup by anchor_id). A chunked node's `document_id`
> equals its node id. The axis cache lives per-workstream at
> `data/workstreams/{workstream_id}/axes/axes-{document_id}.json`;
> `extract_axes_for_document` takes an `axes_dir` parameter. The "extract-
> concepts" story pre-warms this cache; arm_g's stage-1 reuses it on cache hits
> (keyed by text_hash+axis_cap) so analysis never re-derives concepts that
> already exist.

### Changes

- `engine/api.py` — make the default `run_arm_g_fn` path workstream-aware
  (Option A): in `analyze_workstream_edge`, when no stub was injected, build the
  `AnchorIndex` from `ws_anchors.build_index(workstreams_dir, workstream_id)` and
  pass `axes_dir = workstreams_dir / workstream_id / "axes"` into `run_arm_g`;
  stop reading `data/artifacts/anchor-index.json` on this path. Preserve the
  `(src_doc, tgt_doc)` injection seam so `create_app(run_arm_g_fn=fake_fn)` still
  short-circuits. `_make_default_run_arm_g(artifacts_dir)` is either removed or
  retained only as the documented rollback shape.
- `engine/arm_g.py` — `run_arm_g(anchor_index, doc_a, doc_b, signal=...,
axes_dir=AXES_DIR)` threads `axes_dir` into both
  `extract_axes_for_document(...)` calls; `extract_axes_for_document(...,
axes_dir=AXES_DIR)` and its `_load_axes_cache` / `_write_axes_cache` helpers
  take `axes_dir` and build the cache path under it. Default stays `AXES_DIR` so
  callers that don't pass it are unaffected. Six-stage logic unchanged.
- `engine/ws_anchors.py` — consumed as-is via `build_index(workstreams_dir,
workstream_id)`; created by the add-node-chunking story. No edits here beyond
  what that story delivers.

## Architecture Notes

- **New dependencies:** none. `ws_anchors.build_index` and `AnchorIndex` already
  exist (or are delivered by the add-node story); no new packages, no
  `pyproject.toml` / `.github/workflows/test.yml` dep additions.
- **Dependencies & integration:** SEQUENTIAL on the add-node-chunking story for
  `engine/ws_anchors.py` and the per-node anchor files; INTEGRATES with the
  extract-concepts story via the shared per-workstream `axes/` cache directory
  (they must agree the cache lives at
  `data/workstreams/{workstream_id}/axes/axes-{document_id}.json`). No shared
  mutable state beyond that cache dir. The route contract (status strings, error
  codes, findings shape) is unchanged, so the frontend needs no change.

## Exemplar Files

- `engine/api.py::analyze_workstream_edge` (~1119) — the route to edit; keep its
  guard order (missing-doc → same-doc → run → empty-findings → save) intact.
- `engine/api.py::_make_default_run_arm_g` (~398) and `create_app`'s
  `run_arm_g_fn` seam (~420-479) — the adapter/seam pattern to preserve.
- `engine/arm_g.py::run_arm_g` (~920) and `extract_axes_for_document` (~185,
  with `_load_axes_cache` / `_write_axes_cache` ~134-152) — where `axes_dir`
  threads through.
- `engine/anchors.py::AnchorIndex` (~96) — `by_document(document_id)` is what
  stage 1 calls; unknown `document_id` yields an empty list (the graceful
  un-chunked fallback).
- `engine/tests/test_api_analyze_live.py` — THE convention to follow:
  `create_app(workstreams_dir=..., run_arm_g_fn=fake_fn)`, `fake_fn(src, tgt)`
  returning `{"connections","unsupported","trace"}`, and the missing-doc /
  same-doc / 502 / empty-findings cases.
- `engine/workstreams.py::connections_to_findings` (~460), `save_findings`,
  `load_graph` — unchanged, downstream of the seam.

## Implementation Plan

### Sub-tasks

**Task 1: Thread `axes_dir` through the axis-cache path in `engine/arm_g.py`** —
_small_ (<100 LOC)

- Add `axes_dir: Path = AXES_DIR` to `extract_axes_for_document`,
  `_load_axes_cache`, and `_write_axes_cache`; build the cache path as
  `axes_dir / f"axes-{document_id}.json"`. Add `axes_dir: Path = AXES_DIR` to
  `run_arm_g` and pass it into both `extract_axes_for_document(...)` calls.
- Files: `engine/arm_g.py`; `engine/tests/test_arm_g.py` (add an `axes_dir`
  cache-location + cache-reuse test).
- INDEPENDENT — the default `AXES_DIR` keeps every existing caller green, so this
  can land before Task 2.

**Task 2: Make the default `run_arm_g_fn` path workstream-aware in
`engine/api.py`** — _small_ (<100 LOC)

- In `analyze_workstream_edge`, when the caller injected no stub, build the
  `AnchorIndex` via `ws_anchors.build_index(workstreams_dir, workstream_id)` and
  pass `axes_dir = workstreams_dir / workstream_id / "axes"` into `run_arm_g`.
  Preserve the `(src_doc, tgt_doc)` seam so `create_app(run_arm_g_fn=fake_fn)`
  short-circuits. Retire (or downgrade to rollback-only)
  `_make_default_run_arm_g(artifacts_dir)`'s dependence on
  `data/artifacts/anchor-index.json`.
- Files: `engine/api.py`; `engine/tests/test_api_analyze_live.py` (add the
  no-artifacts-file / per-workstream-anchors adapter test).
- SEQUENTIAL — depends on Task 1 (`axes_dir` on `run_arm_g`) and on the
  add-node-chunking story's `engine/ws_anchors.py::build_index`.

### Negative Constraints

- Do NOT change Arm G's six-stage logic (retrieval, finders, suppression,
  coverage, validation, citation rewrite) — only the axis-cache location and the
  index source change.
- Do NOT change the five finding labels or the `differs-on`-only
  `tighten`/`loosen`/`neutral` sentiment rule.
- Do NOT support cross-workstream analysis — out of scope; the route stays
  single-workstream.
- Do NOT read `data/artifacts/anchor-index.json` in the workstream analyze path
  (it may remain only in the documented rollback adapter).
- Do NOT change `connections_to_findings`, `save_findings`, the empty-findings
  guard, or any error code / status string.
- Do NOT edit `engine/ws_anchors.py` beyond what the add-node story delivers.

## Test Scenarios

**Test 1: Success on self-built anchors — findings saved (new)**

- Setup: `create_app(workstreams_dir=tmp, run_arm_g_fn=fake_fn)` where the
  `opres-v2` graph has edge `e-live` from node `opres-pd-v0-3`
  (`document_id: opres-v1-2025-draft`) to `rmit-pd-2025` (`document_id:
rmit-v2-2025`), and `fake_fn(a, b)` asserts `a == "opres-v1-2025-draft"` and
  `b == "rmit-v2-2025"` (source first) and returns `{"connections": [CONN],
"unsupported": [], "trace": {}}`.
- Action: `POST /api/workstreams/opres-v2/edges/e-live/analyze`.
- Expected: `200`, `status == "analysed"`, `findings_count == 1`, and
  `data/workstreams/opres-v2/findings/e-live.json` written. (Mirrors existing
  `test_live_analyze_saves_findings_and_returns_analysed`.)

**Test 2: Default adapter builds from `ws_anchors.build_index`, not the
artifacts file (new)**

- Setup: a tmp workstream `opres-v2` with per-node anchor files present at
  `data/workstreams/opres-v2/anchors/opres-v1-2025-draft.json` and
  `.../rmit-v2-2025.json`, and `data/artifacts/anchor-index.json` **absent**
  (or `artifacts_dir` pointed at an empty tmp dir). Inject a `run_arm_g_fn`
  spy (or let the default build the index and stub `run_arm_g` to assert the
  passed `AnchorIndex` contains the workstream's anchor ids).
- Action: `POST /api/workstreams/opres-v2/edges/e-live/analyze`.
- Expected: `200` `analysed` (or the spy observes an `AnchorIndex` unioned from
  the two per-workstream files) with **no** read of
  `data/artifacts/anchor-index.json` — proving zero reliance on the shared store.

**Test 3: Axis cache reuse — no re-derivation (new, `engine/tests/test_arm_g.py`)**

- Setup: seed `axes_dir/axes-opres-v1-2025-draft.json` with entries whose
  `anchor_id`, `text_hash` (matching current anchor text) and `axis_cap` match
  the anchors; patch `_extract_axes_for_anchor` with a spy that raises if
  called.
- Action: `extract_axes_for_document(anchor_index, "opres-v1-2025-draft",
axes_dir=axes_dir)`.
- Expected: returns the cached axes; the spy is **never** invoked (hits ==
  anchor count, extraction calls == 0); the rewritten cache file lands under
  `axes_dir`, not `REPO_ROOT / "experiments"`.

**Test 4: Missing document on an endpoint → 409, nothing written (preserved)**

- Setup: edge `e-noref` from `opres-pd-v0-3` to node `bcbs` (no `document_id`);
  `run_arm_g_fn` asserts it is never called.
- Action: `POST /api/workstreams/opres-v2/edges/e-noref/analyze`.
- Expected: `409`, body `code == "NOT_ANALYSABLE"`, message
  "Node bcbs has no ingested document to analyse.", no findings file written.
  (Existing `test_edge_with_unmapped_node_is_not_analysable`.)

**Test 5: Both endpoints same document → 409, nothing written (preserved)**

- Setup: edge `e-samedoc` where both `opres-pd-v0-3` and `opres-dp` map to
  `opres-v1-2025-draft`; `run_arm_g_fn` asserts never called.
- Action: `POST /api/workstreams/opres-v2/edges/e-samedoc/analyze`.
- Expected: `409`, `code == "NOT_ANALYSABLE"`, message "Both endpoints resolve
  to the same document (opres-v1-2025-draft); there is nothing to compare.", no
  `findings/e-samedoc.json`. (Existing
  `test_same_document_analyze_returns_409_and_writes_nothing`.)

**Test 6: Analyser raises → 502, no partial write (preserved)**

- Setup: `run_arm_g_fn = boom` where `boom(a, b)` raises `RuntimeError("no
creds")`.
- Action: `POST /api/workstreams/opres-v2/edges/e-live/analyze`.
- Expected: `502`, `code == "ANALYZE_FAILED"`, message "Live analysis failed:
  no creds", and `findings/e-live.json` **not** written. (Existing
  `test_finder_failure_returns_502_and_writes_nothing`.)

**Test 7: No linkages found → `no_linkages_found`, re-analysable (preserved)**

- Setup: `run_arm_g_fn` returns `{"connections": [], "unsupported": [],
"trace": {}}`.
- Action: `POST /api/workstreams/opres-v2/edges/e-live/analyze`.
- Expected: `200`, `status == "no_linkages_found"`, `findings_count == 0`, no
  findings file written (edge stays re-analysable — `analysed` is derived from
  file presence). (Existing `test_empty_findings_are_not_persisted`.)

## Acceptance Criteria

> Business Gherkin scenarios stay in the section above; these are the
> implementation-level completion checks for this technical story.

- [ ] Analysing an edge between two distinct chunked nodes succeeds with
      `data/artifacts/anchor-index.json` absent (Test 2).
- [ ] The default adapter's `AnchorIndex` is built from
      `ws_anchors.build_index(workstreams_dir, workstream_id)` (Test 2).
- [ ] `axes_dir` threads through `run_arm_g` → `extract_axes_for_document` →
      `_load_axes_cache` / `_write_axes_cache`; the cache file lands at
      `data/workstreams/{ws}/axes/axes-{document_id}.json` (Tests 1, 3).
- [ ] A warm axis cache is reused with zero model extraction calls (Test 3).
- [ ] Missing-doc (409), same-doc (409), analyser-raise (502), and
      `no_linkages_found` behaviours are unchanged (Tests 4-7).
- [ ] The `create_app(run_arm_g_fn=fake_fn)` seam and its `(src_doc, tgt_doc)`
      signature are unchanged; all existing stubs pass unedited.
- [ ] The five labels, `differs-on`-only sentiment rule, and verbatim citation
      are preserved.
- [ ] All existing tests still pass.
- [ ] No new type errors beyond the accepted mypy third-party-stub baseline.

## Verification

Run the verifier skill to confirm changes are clean.

### Backend Tests

- `engine/tests/test_api_analyze_live.py` — ADD: (a) an adapter test proving the
  default path builds from `ws_anchors.build_index` with
  `data/artifacts/anchor-index.json` absent → still `analysed` (Test 2); keep
  the existing missing-doc / same-doc / 502 / empty-findings tests green
  unchanged (Tests 4-7).
- `engine/tests/test_arm_g.py` — ADD: (a) an `axes_dir` cache-location test
  asserting the cache file is written under the passed `axes_dir`, and (b) a
  cache-reuse test asserting `_extract_axes_for_anchor` is not called on a warm
  cache (Test 3).
- Run with the main-tree venv (per the run-in-main-worktree learning):
  `.venv/bin/python -m pytest engine/tests/test_api_analyze_live.py
engine/tests/test_arm_g.py`.

### Manual Verification

- [ ] In the app, build a workstream (add two documents so each is chunked),
      draw a connection between them, click "Analyze linkage", and confirm
      findings appear each quoting exact passages — with
      `data/artifacts/anchor-index.json` renamed away to prove no reliance.
- [ ] Confirm `data/workstreams/{ws}/axes/axes-{document_id}.json` is created by
      the run and reused (no re-extraction) on a second analysis touching the
      same document.

### E2E Tests

Playwright exists (`frontend/e2e/`, baseURL `http://localhost:5173`). The
observable "analyze produces findings" flow is user-facing, but it is the tail
of the add-node → connect → analyze chain already exercised by the add-node /
extract E2E specs; a standalone E2E here would duplicate that setup. Map a single
happy-path spec only if the add-node/extract chain does not already cover the
analyze step end to end.

| Scenario                                      | Test file                              | Assigned sub-task |
| --------------------------------------------- | -------------------------------------- | ----------------- |
| Analyse a self-built linkage and see findings | `frontend/e2e/analyze-linkage.spec.ts` | Task 2 (optional) |
