# Demo Hardening Suite — COPA Hackathon (demo 3 Aug 2026)

> **STATUS (29 Jul 2026): largely SUPERSEDED by upstream #52/#53.** This suite was
> written against a pre-#52 reality where "live Analyze" returned nothing because the
> global anchor index and the workstream graphs used disjoint document-id namespaces.
> Upstream #52 ("build a workstream from scratch") resolved that with **per-workstream
> anchors** (`engine/ws_anchors.py`) and build-and-persist findings, so:
>
> - **Obsolete:** the artifact-integrity guard (`spec-engine-artifact-integrity-guard.md`)
>   and the analyze fan-out cap (`spec-engine-analyze-fanout-cap.md`) — they harden the
>   shared-index live path the demo no longer uses.
> - **Still relevant:** `spec-cross-workstream-climax.md` — the cross-workstream climax
>   is the one piece #52 explicitly **deferred** (its Non-Goals) and for which no
>   upstream spec exists. See `docs/specs/workstream-brain/REVIEW-2026-07-29.md` for the
>   current state and the real pending work.
>   Demo date corrected from 5 Aug to **3 Aug** (per the upstream epic).

**Ticket:** —
**Type:** Overview — sequencing for a set of technical specs (mostly superseded)

This is the umbrella spec for firming up Workstream Brain ahead of the COPA
Hackathon demo on **5 August 2026** (written 28 July — an eight-day, single-builder
runway). It names the work, splits it into what must ship before the demo and what
stays a credible roadmap, and fixes the build order. Each Tier 1 item has its own
buildable spec; Tier 2 is captured as roadmap prose in
[`roadmap-post-hackathon.md`](roadmap-post-hackathon.md).

## Why this exists

A gap review of the live engine and frontend found the product is _further along than
its own documentation admits_ — the analyze → review → draft flow and the copilot are
wired end to end against live models (`create_app()` in `engine/api.py` exposes
`run_arm_g_fn`, `copilot_reply_fn`, `copilot_stream_fn`; the frontend has a client
function and hook for every route). The risks are not "unbuilt features." They are:

1. **The data-artifact supply chain the live path silently depends on.** The analyze
   route reads whatever happens to be in `data/artifacts/anchor-index.json` and never
   protests when that index is thin or absent — this very working session opened with
   the entire `data/artifacts/` directory staged for deletion, and a documented learning
   records an offline rebuild shrinking it from 7 documents to 2 without failing.
2. **Unbounded LLM fan-out on a single "Analyze" click.** Axis extraction makes one
   model call per clause, on both documents (`engine/arm_g.py`), with the expensive
   `claude-opus-4-8` on the finder/critic hop — a large policy document can hang the
   button on stage.
3. **The demo climax is scripted, not computed.** The cross-workstream relationship —
   the headline moment — is a stored edge in the `_cross` fixture, read back with no
   live analysis and no fallback story.

None of these break a rehearsed run on a warm laptop. All three are exactly what fails
under demo-day conditions: a fresh checkout, a cold cache, a nervous live click.

## Tier 1 — must ship before 5 Aug

Small, independent, each buildable in one sitting. No Tier 1 spec depends on another
landing first.

| #   | Spec                                                                                 | One-line intent                                                                                                                                             |
| --- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | [`spec-engine-artifact-integrity-guard.md`](spec-engine-artifact-integrity-guard.md) | Fail loud — in the UI and at a new `/health` route — when the clause/anchor index is thin or missing, instead of quietly analysing fewer documents.         |
| 2   | [`spec-cross-workstream-climax.md`](spec-cross-workstream-climax.md)                 | Make the cross-workstream climax **live-with-recorded-fallback**: attempt the real pipeline, transparently replay a committed trace if it fails or is slow. |
| 3   | [`spec-engine-analyze-fanout-cap.md`](spec-engine-analyze-fanout-cap.md)             | Put a hard ceiling on axis-extraction calls per analyze, plus a "warm the cache" step, so the live click is bounded and fast.                               |
| 4   | [`spec-demo-smoke-test.md`](spec-demo-smoke-test.md)                                 | One script that runs the full demo flow against the seeded fixtures and fails CI if any stage breaks — the regression net for specs 1–3.                    |

**Build order:** 4 first (the smoke test defines "the demo flow works" and catches the
other three regressing), then 1, then 3, then 2. Spec 2 is last because it is the only
one that changes product behaviour the audience sees; it should land against an already-
green smoke test.

## Tier 2 — roadmap, not built before the demo

Captured as prose for repo credibility and post-hackathon planning, in
[`roadmap-post-hackathon.md`](roadmap-post-hackathon.md):

- **Doc reconciliation** — `CLAUDE.md` still asserts "the API is a fixture projection,
  not a model client" and "`create_app()` takes no model seam"; the code contradicts
  both. Cheap and high-credibility; a one-paragraph slice may be pulled into Tier 1 if
  time allows, but it is not demo-blocking.
- **Persistence path** — JSON-files-and-localStorage → server-side state with real
  identity and concurrency control.
- **LLM cost / efficiency design** — batching, concurrency, and per-run ceilings beyond
  the blunt cap in spec 3.

## Non-negotiables carried by every spec below

- **Verbatim citation.** Every finding, cross-link card, and copilot answer quotes the
  exact clause it relies on, with its clause number, or states "No matching clause
  found." No spec here weakens that guarantee.
- **One taxonomy.** Findings carry exactly one of the five semantic labels; `sentiment`
  is valid only on `differs-on`. No spec reintroduces the retired
  `Conflict / Duplication / Gap` vocabulary as a label.
- **The engine stores state as files.** No spec below introduces a database; that is a
  Tier 2 conversation.
