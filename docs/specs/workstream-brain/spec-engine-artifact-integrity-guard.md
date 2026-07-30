# Artifact Integrity Guard — Fail Loud on a Thin or Missing Index

**Ticket:** —
**Type:** Technical — Reliability / Demo hardening (Tier 1)

Give the engine a way to notice, and refuse to hide, when the clause and anchor
indexes it depends on are incomplete. Today the live analyze path reads whatever is in
`data/artifacts/`, analyses only the documents that happen to be indexed, and reports
success — so a fresh checkout or a bad rebuild degrades the demo silently instead of
failing where someone can see it.

## Motivation

**Current state:** `POST /api/workstreams/{ws}/edges/{edge_id}/analyze` loads
`data/artifacts/anchor-index.json` and runs Arm G against it. If that file is missing,
the route raises and returns a 502. But the more dangerous case is a _present but thin_
index — a documented learning records an offline rebuild silently shrinking the index
from 7 documents to 2, and this session opened with the whole `data/artifacts/`
directory staged for deletion. When the index is thin, analyze does not fail: it simply
finds fewer linkages, and neither the drafter nor the operator has any signal that the
result is incomplete. There is no `/health` route and no startup check.

**Desired state:** The engine can state, on demand, whether its artifacts are demo-ready
— how many documents the anchor index covers, how many the clause index covers, and
whether the set the demo relies on is present. A new read-only `GET /health` route
returns that summary with an overall `ok` / `degraded` status. The analyze route, when
it declines because an endpoint's document is not in the index, returns a distinct,
human-readable error naming the missing document rather than a generic 502. The frontend
surfaces a `degraded` health state as a visible banner so nobody demos on a broken index
without knowing.

**Trigger:** The eight-day demo runway means the machine that runs the demo may not be
the machine the artifacts were built on. Azure Document Intelligence is required to build
the full index (another documented learning); a well-meaning offline rebuild is the most
likely way the demo breaks, and it breaks quietly. This guard converts a silent
degradation into a loud, early, obvious one.

## Scope

- **In scope:**
  - A new `GET /health` route returning `{status, anchor_index: {documents, ...},
clause_index: {documents, ...}, demo_documents: {expected, present, missing}}`.
    `status` is `ok` when every expected demo document is indexed, `degraded` otherwise.
  - The list of expected demo documents lives in one named constant (e.g. in
    `engine/config.py`), not scattered — it is the source of truth for "what the demo
    needs indexed."
  - Tightening the analyze route's not-analysable path so a missing-from-index document
    returns a `409 INDEX_MISSING_DOCUMENT` naming the document id, distinct from the
    existing `NOT_ANALYSABLE` (no ingested document) and the `502 ANALYZE_FAILED` (live
    model / creds failure).
  - A frontend banner, driven by `GET /health`, shown only when `status` is `degraded`,
    listing the missing documents.
- **Out of scope:**
  - Rebuilding the index, or any change to how the index is built (that stays a
    DI-dependent offline step).
  - Any change to the shape of a successful analyze response.
  - Persisting or historising health over time; this is a point-in-time check.
  - Authentication on `/health`.

## Goals

- On a checkout whose `data/artifacts/` is missing or thin, `GET /health` returns
  `degraded` and names every missing demo document.
- A drafter who opens the app against a degraded index sees a banner before they click
  Analyze, not a confusing empty result after.
- The three failure modes on the analyze route — no ingested document, document not in
  index, and live-model failure — are three distinct error codes, each naming what went
  wrong.
- `GET /health` is safe to call on a fresh checkout with no build having run: it reports
  `degraded`, it does not raise.

## Verification

- A test points `artifacts_dir` at a tmp dir containing a two-document index and asserts
  `GET /health` returns `degraded` with the demo documents that are absent listed under
  `missing`.
- A test with the full committed index asserts `status: ok` and an empty `missing`.
- A test asserts analyzing an edge whose endpoint document is absent from the index
  returns `409 INDEX_MISSING_DOCUMENT` naming that document, not a 502.
- A frontend test asserts the banner renders on `degraded` and is absent on `ok`.
