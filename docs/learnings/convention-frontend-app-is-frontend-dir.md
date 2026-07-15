---
name: frontend-app-is-frontend-dir
description: Workstream Brain's UI is frontend/ (Vite + React 18); web/ is the previous iteration's Next.js app — and a build step is intentional, not drift
type: convention
captured: 2026-07-11
updated: 2026-07-16
source: frontend re-platform brainstorm (Reconciliation Workbench); corrected after the workstream-brain build (#36, #37)
---

Two separate facts, both load-bearing:

**1. A build step is intentional.** The 11 Jul 2026 re-platform retired the earlier
convention that "POC pages are self-contained HTML using Tailwind via CDN — no build
step." The repo has a `package.json`, an npm/Node toolchain, and a build step
alongside the Python `engine/`. That is deliberate. Do not "fix" the framework away.

**2. The active app is `frontend/`, not `web/`.** There are two React apps:

| Dir         | Stack                                          | Iteration                             | Status                  |
| ----------- | ---------------------------------------------- | ------------------------------------- | ----------------------- |
| `frontend/` | Vite 5, React 18, TanStack Query, react-router | **Workstream Brain (current)**        | **Active** — build here |
| `web/`      | Next.js 16, React 19, Zustand + persist        | Reconciliation Workbench (superseded) | Reference only          |

`frontend/` talks to the engine's `/api/workstreams/*` routes. `web/` reads the legacy
routes (or a bundled snapshot at `web/public/data/` via `NEXT_PUBLIC_API_BASE`).

**Why:** This learning originally said the demo frontend "is a Next.js app under
`web/`" — true on 11 Jul, wrong the moment workstream-brain shipped its screens into
`frontend/` (#36 Task Screen, #37 workstream graph hero, both 15 Jul). Because the
learnings index is read at the start of `/forge:build`, the stale pointer was actively
feeding the wrong directory to every feature-builder subagent — a silent failure that
repeats every run. The name is now iteration-neutral so a future pivot updates the
table rather than leaving a lie in the title.

**How to apply:** Put Workstream Brain UI in `frontend/`. Do not add workstream-brain
screens to `web/`, and do not treat `web/`'s Zustand/persist pattern as the house
convention — `frontend/` uses TanStack Query against live engine routes. The
`docs/poc/workstream-brain/*.html` pages are the read-only UX reference for current
work; `docs/poc/drafter-knowledge-graph/*.html` belongs to the superseded iteration.
See [[convention-workstream-brain-opres-v2-conventions]] for the data shapes
`frontend/` must follow, and [[blocker-forge-build-run-in-main-worktree]] —
`frontend/node_modules` exists only in the main working tree. See
[[skill-ship-is-gitlab-use-gh]] for the PR flow.
