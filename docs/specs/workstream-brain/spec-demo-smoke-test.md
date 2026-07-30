# Demo Smoke Test — One Script That Proves the Demo Flow

**Ticket:** —
**Type:** Technical — Test coverage / Demo hardening (Tier 1)

A single, fast test that walks the whole demo path — build the workstream, analyse an
edge, review a finding, save a draft, open the cross-workstream climax — against the
seeded fixtures, and fails CI the moment any stage breaks. It is the regression net that
holds the other three Tier 1 specs in place through eight days of change.

## Motivation

**Current state:** The suite is strong at the unit level (382 engine test functions, 17
frontend suites), but the tests exercise routes in isolation with stubbed pipelines.
Nothing asserts that the _sequence_ a presenter clicks through on stage works end to end
against the real fixtures. A change that individually passes every unit test can still
break the demo flow — a fixture drifts, a route's contract shifts, an error code the
frontend keys on changes — and nobody finds out until the room is watching.

**Desired state:** One smoke test drives the demo's exact happy path against the seeded
fixtures and the real (model-stubbed) engine wiring: load the workstream graph → analyse
the demo edge → confirm findings come back with verbatim clause evidence and valid labels
→ read the review pane → save and re-read a draft → open the cross-workstream climax and
confirm a result with `source` set. It runs in CI and locally as a pre-demo check. When
it is green, the presenter can trust the path; when it goes red, it names the stage that
broke.

**Trigger:** Three behaviour-touching specs (the integrity guard, the fan-out cap, the
live-with-recorded climax) land in the same short window, on the hot path, days before a
live demo. That is precisely the situation a flow-level smoke test exists for. Building it
first also forces an executable definition of "the demo works" that the other three specs
verify against.

## Scope

- **In scope:**
  - One test (e.g. `engine/tests/test_demo_smoke.py`) that exercises the full demo
    sequence against the committed workstream fixtures, with model calls stubbed
    deterministically (no live network in CI).
  - Assertions at each stage: the graph loads; analyse returns findings; every finding
    carries a five-label value and verbatim clause text; the review pane serves the same
    clause text; a draft round-trips; the cross-workstream detail returns a result with a
    `source` field.
  - A health-check assertion: `GET /health` reports `ok` against the committed artifacts
    (ties the smoke test to [`spec-engine-artifact-integrity-guard.md`](spec-engine-artifact-integrity-guard.md)).
  - Wiring it into the existing CI job (`.github/workflows/test.yml`) so a red smoke test
    blocks a merge.
  - A one-command local invocation documented in the spec suite, runnable the morning of
    the demo.
- **Out of scope:**
  - A browser / Playwright end-to-end test driving the real UI (valuable, but heavier
    than an eight-day runway wants; a Tier 2 follow-on).
  - Live-model calls in CI — the smoke test stubs models; the live path is exercised by
    hand during rehearsal.
  - Load or performance assertions beyond "completes" — the fan-out cap spec owns timing.
  - Testing every route; this asserts the demo _path_, not full coverage.

## Goals

- A single green/red signal answers "does the demo flow work right now?"
- A red result names the stage that broke (graph load, analyse, review, draft, or
  climax), not just "a test failed."
- The test runs in CI on every push and completes fast enough to run casually before the
  demo (target: seconds, model calls stubbed).
- The other three Tier 1 specs each leave this test green when they land — it is their
  shared acceptance gate.

## Verification

- The test passes against the current committed fixtures and stubbed models.
- Deliberately breaking one stage (e.g. renaming a fixture edge id) turns the test red
  with a message identifying that stage.
- The test is present in the CI workflow and a forced failure blocks the job.
