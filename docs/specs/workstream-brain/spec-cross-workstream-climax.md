# Cross-Workstream Climax — Live-with-Recorded-Fallback

**Ticket:** —
**Type:** Technical — Demo hardening / Product behaviour (Tier 1)

Make the demo's headline moment — a conflict found _across two workstreams drafted in
parallel_ — attempt real analysis on stage, while guaranteeing it never fails in front
of an audience. The relationship is currently a stored fixture edge read back with no
computation; this spec keeps that stored result as a safety net and puts a genuine live
attempt in front of it.

## Motivation

**Current state:** `GET /api/cross-links/{edge_id}` reads the `_cross` fixture store,
finds the pre-authored edge, and assembles its panel — regulatory profiles, shared
attributes, reasons, label rollup, and the verbatim clause evidence from a committed
findings file. Nothing is computed at request time. Single-workstream analyze, by
contrast, was promoted to a live Arm G run (`run_arm_g_fn` on the analyze route). So the
climax is the one place in the demo that is entirely scripted, and it is the moment the
pitch leans on hardest.

**Desired state:** Triggering the cross-workstream analysis attempts the real Arm G
pipeline across the two workstreams' documents — the same pipeline single-workstream
analyze already uses — and, on success, shows a live result carrying the verbatim clause
evidence the pipeline produced. If the live attempt fails, exceeds a time budget, or
returns nothing, the endpoint transparently falls back to the committed `_cross` trace
and serves that instead, with a field in the response recording which path was taken
(`source: "live"` / `"recorded"`). The audience sees a working climax either way; the
operator can tell the two apart; the recorded path is byte-for-byte the demo that ships
today.

**Trigger:** The analyze route already computes a `trace` object per run (it is built
today and then discarded before the response). That makes a recorded fallback cheap:
commit one real trace for the demo pair as the safety net, and reuse the existing
`connections → findings` mapper so the live and recorded paths produce the same shape.
An eight-day runway plus a live-audience risk profile makes "attempt live, fall back to
recorded" the only responsible option — fully-live risks a 502 on stage, fully-scripted
undersells a capability the engine actually has.

## Scope

- **In scope:**
  - A cross-workstream analyze trigger that runs Arm G across the two workstreams'
    endpoint documents, bounded by the fan-out cap and time budget from
    [`spec-engine-analyze-fanout-cap.md`](spec-engine-analyze-fanout-cap.md).
  - A transparent fallback to the committed `_cross` trace on any live failure, timeout,
    or empty result — never an error surfaced to the audience for the demo pair.
  - A `source` field (`live` / `recorded`) on the cross-link detail response so the path
    taken is observable.
  - Committing exactly one real recorded trace for the demo pair (Operational Resilience
    × Open Finance ED, the brief's demo-hero linkage) as the safety net.
  - Preserving the verbatim guarantee on both paths: every clause card's text is the text
    the pipeline (live) or the committed trace (recorded) actually cited — never
    re-synthesised.
- **Out of scope:**
  - Making _every_ cross-link live. Only the demo pair carries a recorded fallback;
    other cross-links may remain fixture-only or return `recorded`.
  - Any change to the five-label taxonomy or to how cross-links are classified.
  - Streaming the live result as it computes.
  - Removing the `_cross` fixture — it becomes the fallback, not dead code.

## Goals

- Triggering the demo climax on stage never shows the audience an error, a spinner that
  never resolves, or an empty panel — the recorded trace guarantees a result.
- When the live pipeline succeeds within budget, the panel shows a genuinely computed
  result, with `source: "live"`.
- The recorded fallback reproduces exactly the cross-link panel that ships today.
- A single clause on one side with nothing to cite on the other still renders correctly
  (a `goes-beyond` / `silent-on` linkage) on both paths — the demo-hero linkage is
  exactly this shape (Open Finance mandates board oversight where OpRes is silent).

## Verification

- A test stubs the live pipeline to raise and asserts the endpoint returns the recorded
  trace with `source: "recorded"` and a 200, not a 502.
- A test stubs the live pipeline to exceed the time budget and asserts the same fallback.
- A test stubs the live pipeline to succeed and asserts `source: "live"` with the stub's
  findings, verbatim.
- A test asserts every clause card on both paths quotes text present in the underlying
  finding record (verbatim guarantee), and that no response ever carries a label outside
  the five-label set.
