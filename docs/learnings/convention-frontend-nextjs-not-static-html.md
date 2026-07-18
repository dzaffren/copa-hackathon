---
name: frontend-nextjs-not-static-html
description: SUPERSEDED (18 Jul 2026). Historical record of the Reconciliation Workbench Next.js re-platform. Live convention is `convention-frontend-vite-react-not-nextjs.md`.
type: convention
captured: 2026-07-11
superseded: 2026-07-18
source: frontend re-platform brainstorm (Reconciliation Workbench)
---

> **SUPERSEDED (18 Jul 2026).** Reconciliation Workbench was retired in favour
> of the Workstream Brain epic; its Next.js app was moved to `archive/web/`.
> The current frontend convention is Vite + React 18 + TS + Tailwind + shadcn
> under `frontend/` — see [[convention-frontend-vite-react-not-nextjs]]. Text
> below is kept as history; do NOT apply it to new work.

The Reconciliation Workbench demo frontend is a **Next.js + React + Tailwind +
shadcn/ui** application under `web/` (deployed to Vercel), using **Zustand +
persist** for the shared finding state and a bundled JSON snapshot at
`web/public/data/` that `NEXT_PUBLIC_API_BASE` can swap for the live FastAPI
engine. This **supersedes** the earlier convention that "POC pages are
self-contained HTML using Tailwind via CDN — no build step."

**Why:** The 11 Jul 2026 re-platform (design:
`docs/specs/reconciliation-workbench/frontend-nextjs-migration-design.md`) moved
the demo to a framework for a richer hackathon surface and a Vercel deploy. The
repo therefore now has a `package.json`, an npm/Node toolchain, and a build step
alongside the Python `engine/` — all of which are intentional, not drift. A
future session reading the old convention could wrongly "fix" the framework away.

**How to apply:** Treat `web/` (Next.js, npm, build step) as the intended demo
frontend. The Python engine stays read-only and untouched; all drafter state is
client-side (Zustand + localStorage), so do NOT add engine write routes or a
database. The old `docs/poc/drafter-knowledge-graph/*.html` pages are kept as the
read-only UX reference the `web/` build follows — do not extend them as the live
demo. See [[skill-ship-is-gitlab-use-gh]] for this repo's GitHub PR flow.
