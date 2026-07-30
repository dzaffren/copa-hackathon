# Post-Hackathon Roadmap — Tier 2 (not built before 5 Aug)

**Ticket:** —
**Type:** Roadmap — prose, not an implementation spec

The three items below are real engineering work the demo does _not_ need, captured for
repo credibility and post-hackathon planning. They are deliberately prose, not buildable
specs: each becomes its own spec → plan → build cycle after the demo. See
[`spec-demo-hardening.md`](spec-demo-hardening.md) for the Tier 1 work that does ship.

## 1. Documentation reconciliation

The single highest-credibility, lowest-effort item — and the one most likely to mislead a
reviewer reading the repo cold. `CLAUDE.md` still states, as a hard rule, that "the API
is a fixture projection, not a model client" and that "`create_app()` takes no model
seam, so the service _cannot_ reach a model." The code contradicts both: `create_app()`
in `engine/api.py` exposes `run_arm_g_fn`, `copilot_reply_fn`, and `copilot_stream_fn`,
and the analyze route runs a live Arm G pipeline. The knowledge-graph review of this repo
surfaced exactly this as its sharpest unresolved contradiction.

The work: rewrite the stale `CLAUDE.md` sections to describe the live-model reality
(injectable seams, live analyze, live copilot with a citation guardrail), and prune or
clearly date-stamp the four superseded product generations still in-tree so a newcomer
builds the right mental model. A one-paragraph slice — correcting just the "no model
seam" claim — is cheap enough to pull into Tier 1 if the week allows; the full
reconciliation is a post-demo pass.

**Why not now:** It touches no runtime behaviour and cannot break the demo, so it yields
to the four specs that can.

## 2. Persistence path — files/localStorage → server-side state

The engine stores everything as JSON on disk (workstreams are directories, findings /
drafts / review-state are files) and the frontend keeps workflow state in browser
`localStorage` (ADR 0001 records this as a deliberate demo choice: "localStorage (demo) →
server-side (prod)"). That is right for a hackathon and wrong for a product: the
maker-checker "audit trail" is a JSON file with no real identity, there is no concurrency
control, and nothing is multi-user.

The work, post-demo: introduce a server-side store behind the same route contracts (the
API shapes do not need to change), give the review/approval trail real actor identity,
and add optimistic-concurrency handling so two reviewers cannot silently clobber each
other. The file store stays as the local/dev seam. This is a genuine design effort — it
gets its own spec, and it is where the "digital twin of expert judgement" pitch has to
become durable.

**Why not now:** Multi-user durability is not demonstrated on stage; a single presenter
on one laptop is served fine by files.

## 3. LLM cost / efficiency design

The Tier 1 fan-out cap ([`spec-engine-analyze-fanout-cap.md`](spec-engine-analyze-fanout-cap.md))
is a blunt instrument: it bounds the _count_ of axis-extraction calls, it does not make
them cheaper or faster. The efficiency work proper is: batch axis extraction into far
fewer calls (many anchors per prompt instead of one call per anchor), run the independent
calls concurrently rather than in a serial loop, and route each stage to a right-sized
model rather than defaulting the finder/critic hop to the expensive `claude-opus-4-8`
(`FINDER_CRITIC_DEPLOYMENT`). Together these change analyze from "bounded but serial and
opus-heavy" to "cheap and quick," which is what makes live analysis viable at more than
demo scale.

**Why not now:** The cap plus a warm cache is enough to make the demo click fast and
safe; the real cost curve only matters once the product runs beyond a rehearsed pair.
