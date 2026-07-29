# Analyze Fan-Out Cap — Bound the Model Calls Behind One Click

**Ticket:** —
**Type:** Technical — Performance / Reliability (Tier 1)

Put a hard ceiling on how many model calls a single "Analyze" can trigger, and give the
demo a way to warm the cache beforehand, so the live click is fast and cannot hang on
stage. Today a single analyze fans out to one model call per clause on each of the two
documents, unbounded by document size.

## Motivation

**Current state:** Arm G's Stage 1 extracts topic axes by calling the model once per
anchor (`_extract_axes_for_anchor` in `engine/arm_g.py`, looped over every anchor in
`extract_axes_for_document`), and the analyze route runs it on _both_ endpoint documents.
A pair like Open Finance ED (89 anchors) × HKMA (127 anchors) is ~216 axis calls before
the finder and coverage passes even begin, and the finder/critic hop defaults to the
expensive `claude-opus-4-8` (`FINDER_CRITIC_DEPLOYMENT` in `engine/config.py`). There is
a per-document axis cache with first-run auto-population, so a warm pair is cheap — but
the _cold_ pair on stage is slow, and nothing bounds a pathologically large document from
firing hundreds of calls on one click.

**Desired state:** Axis extraction for a document is bounded by a configurable ceiling.
When a document has more anchors than the ceiling, the engine extracts axes for the
highest-signal anchors up to the ceiling and records, in the trace, that it capped —
rather than silently fanning out without limit. A separate, explicit "warm" operation
extracts and caches the axes for the demo documents ahead of time, so the on-stage click
hits a warm cache and returns fast. The analyze route carries a wall-clock budget; a run
that blows it fails cleanly (and, for the cross-workstream climax, triggers the recorded
fallback) rather than hanging.

**Trigger:** Live analyze is on the hot path now, and the demo is a live click on a
laptop. The axis cache already exists and already mitigates repeat runs — the missing
pieces are a ceiling for the cold/large case and a deliberate pre-demo warm step so the
first click of the day is not the slow one.

## Scope

- **In scope:**
  - A configurable per-document axis-extraction ceiling (one constant in
    `engine/config.py`, overridable by env), applied in `extract_axes_for_document`.
  - When the ceiling caps a document, recording that fact in the run's `trace` (count
    attempted vs. capped) so a capped run is observable, never silent — consistent with
    the honesty rules the rest of the engine follows.
  - A wall-clock budget on the analyze run, surfaced as a clean failure when exceeded
    (the cross-workstream climax reads this as its fallback trigger).
  - A `scripts/warm_demo_cache.py` (or equivalent make/CLI target) that populates the
    axis cache for the demo documents, runnable before the demo.
  - Choosing the "highest-signal anchors" rule deterministically (e.g. by anchor text
    length / density, the same signal Arm G's cap logic already uses) so a capped run is
    reproducible.
- **Out of scope:**
  - Concurrency / parallelising the axis calls (a Tier 2 efficiency item — this spec
    bounds the count, it does not speed up the calls).
  - Changing which model each stage uses, or the finder/critic pipeline itself.
  - Batching axis extraction into fewer calls (Tier 2).
  - Any change to finding shape or the review workflow.

## Goals

- No single analyze can trigger more than `2 × ceiling` axis calls, regardless of
  document size.
- A capped run is visible in the trace — the operator can tell a truncated analysis from
  a complete one.
- After `warm_demo_cache.py` runs, an analyze of the demo pair returns within the analyze
  time budget with no cold axis calls.
- A run that exceeds the wall-clock budget fails with a distinct, catchable signal rather
  than hanging — and the cross-workstream climax converts that signal into its recorded
  fallback.

## Verification

- A test with a document of `ceiling + N` anchors asserts exactly `ceiling` axis calls
  are made and the trace records `attempted > capped`.
- A test asserts a warm cache produces zero fresh axis calls on a second analyze of the
  same pair.
- A test asserts a run stubbed to exceed the budget raises the budget signal, and that
  the analyze route maps it to a clean error (not a hang, not a generic 500).
- A test asserts the highest-signal selection is deterministic — the same document caps
  to the same anchor set across runs.
