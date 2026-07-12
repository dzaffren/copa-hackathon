# Frontend Re-platform — Next.js + React (design)

**Date:** 2026-07-12
**Status:** Design — awaiting approval before spec edits
**Affects:** the 5 UI story specs in `docs/specs/reconciliation-workbench/`, `CLAUDE.md`,
`scripts/export_poc_snapshot.py`, deploy config. **Does not affect** the engine
(`spec-source-connection-engine.md`, `engine/`).

## Summary

Re-platform the Reconciliation Workbench **demo frontend** from six self-contained static
HTML pages (`docs/poc/drafter-knowledge-graph/*.html`) to a **Next.js + React + Tailwind +
shadcn/ui** application in a new top-level `web/` directory, deployable to **Vercel**. This
is a frontend re-platforming for a richer, componentised hackathon demo — **not** a product
change. Every business rule, acceptance scenario, verbatim-citation guarantee, and honesty
label in the five UI story specs is preserved exactly as approved. The Python engine stays
read-only and untouched.

## Motivation

- **Richer demo (3 Aug 2026).** The hackathon demo needs more polish and interactivity than
  hand-written vanilla JS across six duplicated HTML files comfortably delivers.
- **Deployable to a real host.** Target Vercel (not only a static GitHub Pages dump), which
  gives per-PR preview URLs and a live-capable path to the engine.
- **Side benefit — dev velocity.** Components + one shared store remove the markup and
  `localStorage`-plumbing duplication currently copy-pasted across the six pages.

## Decisions (locked with the user)

| #   | Decision             | Choice                                                                                        |
| --- | -------------------- | --------------------------------------------------------------------------------------------- |
| 1   | Driver               | Richer hackathon demo; possibly deploy to Vercel                                              |
| 2   | Framework            | **Next.js + React** (App Router)                                                              |
| 3   | Shared finding state | **Zustand + `persist`** (localStorage)                                                        |
| 4   | Data source          | **Bundled JSON snapshot**, swappable to live FastAPI via env var                              |
| 5   | Testing              | Vitest/RTL as the gate; 2–3 Playwright hero flows **optional/non-blocking**; pytest unchanged |
| 6   | Old HTML POC         | **Keep as UX reference**; revisit removal after parity                                        |
| 7   | Convention           | Update `CLAUDE.md` + capture a learning so the framework isn't later flagged as a mistake     |

## Architecture

```
engine/  (unchanged — read-only FastAPI, no write routes)
   │  python -m engine.build → data/artifacts/{clause-index,graph,verdicts}.json
   │  scripts/export_poc_snapshot.py → web/public/data/*.json   (retargeted; skips access:"restricted")
   ▼
web/  (new Next.js app → Vercel)
   ├─ app/
   │   ├─ page.tsx                  upload + scripted analyse sequence
   │   ├─ workspace/page.tsx        54-paragraph canvas + connection rail
   │   ├─ connections/[id]/page.tsx reconciliation view
   │   ├─ insights/page.tsx         cross-source insights + decision trail
   │   ├─ assistant/page.tsx        grounded redraft + (mock) Word write-back
   │   └─ monitor/page.tsx          prepared drift events
   ├─ components/   Tailwind + shadcn/ui (VerdictBadge, QuoteBlock, ConnectionRail, …)
   ├─ lib/data.ts   single read seam: bundled snapshot (default) | NEXT_PUBLIC_API_BASE live engine
   └─ lib/store.ts  Zustand + persist — the one shared finding state
```

- **`web/` is a sibling of `engine/`** — keeps npm/Node tooling cleanly separated from the
  Python engine and its `pyproject.toml`/`uv` toolchain. First `package.json` in the repo.
- **UI kit:** Tailwind + **shadcn/ui** (supported by the `ui-ux-pro-max` skill and the
  shadcn MCP) for demo polish without hand-rolling components.

## Data flow — `lib/data.ts` (the read seam)

Mirrors today's `RR_API_BASE` switch, one level up:

- **Default (demo, zero-backend):** reads the exported JSON snapshot bundled at
  `web/public/data/` (`paragraphs.json`, `connections/{n}.json`, `insights.json`,
  `drift.json`). Deploys anywhere static; demo cannot fail on a network call.
- **Live (opt-in):** if `NEXT_PUBLIC_API_BASE` is set, reads from the live FastAPI engine —
  enabling the "analyse any paragraph live" wow-moment (`POST …/analyse`).
- The exporter (`scripts/export_poc_snapshot.py`) is retargeted from
  `docs/poc/drafter-knowledge-graph/data/` to `web/public/data/` and **still skips any
  `access:"restricted"` node** (confidentiality guard preserved). It runs in CI before the
  Vercel build so the bundled snapshot is fresh.

## Shared finding state — `lib/store.ts` (Zustand + persist)

One store, persisted to `localStorage`, replacing the hand-written `state.js` module and the
`rr_*` getters/setters. Reactive across components/routes automatically; cross-tab sync via
the storage event is retained by Zustand's `persist`. **No backend writes** — the engine
stays read-only; all drafter actions are client-side, exactly as the approved specs require.

The `rr_*` key → store-slice mapping (ownership carries over 1:1 from the specs' spine table):

| Spec                  | Was (`rr_*` key)                          | Store slice                      | Owner writes / others read                    |
| --------------------- | ----------------------------------------- | -------------------------------- | --------------------------------------------- |
| Upload & workspace    | `rr_user_srcs`, `rr_resolved_blocked`     | `sources`, `blocked`             | owner                                         |
| Reconciliation        | `rr_verdicts`, `rr_pulled`                | `verdicts`, `trail`              | owner; trail read by insights + assistant     |
| Cross-source insights | `rr_watch`, `rr_setaside`                 | `watch`, `setAside`              | owner; **reads** `trail` (display-only)       |
| Grounded redraft      | `rr_draft`, `rr_resolved`, `rr_submitted` | `draft`, `resolved`, `submitted` | owner; **reads** `verdicts`/`trail`           |
| Drift monitor         | `rr_drift_seen`                           | `driftSeen`                      | owner; hand-off only, writes no verdict/trail |

The `state.js` method contract each spec references is rewritten as a `useStore` hook
contract with the **same method names**, so Functional Requirements and Test Scenarios stay
readable:

```ts
// lib/store.ts (contract)
useStore.commitAct(connId, { verdict, note_type, why }); // writes verdicts + appends trail
useStore.dismiss(connId, reason); // verdicts {status:"dismissed"}
useStore.isResolved(connId); // committed act OR dismissal
useStore.trail(); // selector over the trail slice
useStore.addSource(para, { title, source_type });
useStore.supplyBlocked(connId);
useStore.accept(findingId, para, wording); // mock tracked change into draft + resolve
useStore.watch(insight) / setAside(insightId);
useStore.submit(); // gate on all findings resolved
useStore.reset(); // fresh upload clears the store
```

## Impact on the five UI specs

Each spec's **"Shared Technical Spine"** / technical sections are edited to:

- Replace "static Tailwind HTML, no build step" with the Next.js + shadcn/ui stack.
- Replace the `state.js` + `rr_*` `localStorage` contract with the Zustand store slices and
  the `useStore` hook contract above (same method names).
- Replace `RR_API_BASE` with `lib/data.ts` + `NEXT_PUBLIC_API_BASE`.
- Repoint file paths from `docs/poc/drafter-knowledge-graph/*.html` to `web/app/**` +
  `web/components/**`.
- Update Verification: Vitest/RTL component + store tests as the gate; optional Playwright
  hero flows; pytest unchanged for the exporter.

**All business content — user stories, acceptance criteria, business rules, success metrics
— stays byte-for-byte unchanged.** The engine spec is not touched.

## Testing

- **Vitest + React Testing Library (the gate):** store slices and the guarantee-bearing
  components — verdict→act derivation (`actFor`), justification/dismissal gates, verified vs
  illustrative vs pending-extraction rendering, "No matching clause found" states, running
  counts and idempotency.
- **Playwright (optional, non-blocking):** 2–3 hero flows — upload→workspace→reconcile;
  insight→carry→assistant→accept→submit; a drift item→reconcile hand-off. Flagged so a red
  E2E never derails the demo.
- **pytest (unchanged):** engine + `export_poc_snapshot.py` (shape parity, restricted-node
  skip, verification markers preserved).

## Deploy

- **Vercel** becomes primary (per "possibly Vercel"): zero-config Next.js deploy, per-PR
  previews. The exporter runs in CI before build so the bundled snapshot ships fresh.
- Existing `.github/workflows/deploy-poc.yml` (GitHub Pages of the old HTML) is retained
  until `web/` reaches parity, then retired or repurposed. `confidentiality-guard.yml` is
  unchanged and still guards `data/references/`.

## Repo changes

- **New:** `web/` Next.js app (first `package.json` — introduces npm/Node alongside Python).
- **Modified:** `scripts/export_poc_snapshot.py` → writes `web/public/data/`.
- **Modified:** `CLAUDE.md` — the "self-contained HTML using Tailwind via CDN — no build
  step" convention is replaced by the Next.js stack; a `docs/learnings/` entry captures the
  pivot so a future session doesn't flag the framework as a mistake.
- **Modified:** the five UI story specs (spine/technical sections only, per above).
- **Kept:** `docs/poc/drafter-knowledge-graph/*.html` as the UX reference the `web/` build
  follows; removal revisited after parity.

## Non-goals

- **No product/scope change.** No new persona, verdict, or feature; the acting loop and
  honesty labels are exactly as specified.
- **No backend writes / no database / no auth.** The engine stays read-only; drafter state
  is client-side (persisted locally). Serverless KV/DB persistence and multi-user auth are a
  roadmap item, explicitly out of scope for MVP1.
- **No engine changes** beyond the exporter's output path.
- **No live Microsoft Graph write-back.** Still a mock tracked change in the demo, with live
  Graph documented as the production path (unchanged from the grounded-redraft spec).

## Risks & mitigations

- **Convention reversal.** Overrides an explicit `CLAUDE.md` rule → mitigated by updating
  `CLAUDE.md` + a learning entry in the same change.
- **Two UX sources of truth** (old HTML + new `web/`) during the build → mitigated by
  treating the HTML as read-only reference and the specs as authoritative; parity checklist
  before any removal.
- **Demo depends on a build now** (vs. open-an-HTML-file) → mitigated by the bundled
  snapshot (no backend at demo time) and Vercel preview URLs; the old HTML remains a
  fallback until parity.
- **First npm toolchain in a Python repo** → mitigated by isolating everything under `web/`.

## Open questions

- [x] ~~Design-doc location?~~ — **Resolved:** kept here in
      `docs/specs/reconciliation-workbench/`, beside the specs it affects (repo convention is
      `docs/specs/`, not the `docs/superpowers/specs/` default).
- [ ] Retire `deploy-poc.yml` (GitHub Pages) once Vercel is live, or keep both? — Deferred;
      settle at parity.
- [x] ~~Where does shared state live?~~ — Zustand + persist (localStorage); no backend.
- [x] ~~Snapshot vs live engine?~~ — Bundled snapshot default; `NEXT_PUBLIC_API_BASE` flips
      to live.
