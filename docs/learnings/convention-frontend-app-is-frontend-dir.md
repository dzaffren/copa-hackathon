---
name: frontend-app-is-frontend-dir
description: frontend/ (Vite + React 18) is the only frontend; a build step is intentional, not drift
type: convention
captured: 2026-07-11
updated: 2026-07-16
source: frontend re-platform brainstorm (Reconciliation Workbench); corrected after the workstream-brain build (#36, #37); simplified after the legacy removal
---

Two separate facts, both load-bearing:

**1. A build step is intentional.** The 11 Jul 2026 re-platform retired the earlier
convention that "POC pages are self-contained HTML using Tailwind via CDN — no build
step." The repo has a `package.json`, an npm/Node toolchain, and a build step
alongside the Python `engine/`. That is deliberate. Do not "fix" the framework away.

**2. `frontend/` is the app** — Vite 5, React 18, TanStack Query, react-router,
Tailwind v3, shadcn/ui. It calls the engine's `/api/workstreams/*` routes, based at
`VITE_API_BASE`. It is now the **only** frontend.

**Why this learning still exists after the cleanup:** it originally said the demo
frontend "is a Next.js app under `web/`" — true on 11 Jul, wrong the moment
workstream-brain shipped its screens into `frontend/` (#36 Task Screen, #37 workstream
graph hero, both 15 Jul). Because the learnings index is read at the start of
`/forge:build`, that stale pointer was actively feeding the wrong directory to every
feature-builder subagent — a silent failure that repeated every run. `web/` was deleted
outright on 16 Jul, so the ambiguity is now gone at the source. The lesson worth
keeping is the failure mode: **a learning that names a directory goes stale silently,
and the index makes it authoritative.** Prefer naming the invariant over the artifact.

**How to apply:** Put UI in `frontend/`. The `docs/poc/workstream-brain/*.html` pages
are the read-only UX reference; `docs/poc/{policy-consistency-ai,drafter-knowledge-graph}/`
belong to superseded iterations. If you find a spec referencing `web/`,
`NEXT_PUBLIC_API_BASE`, or Zustand, it predates 16 Jul 2026 and describes a repo that
no longer exists. See [[convention-workstream-brain-opres-v2-conventions]] for the data
shapes `frontend/` must follow, and [[blocker-forge-build-run-in-main-worktree]] —
`frontend/node_modules` exists only in the main working tree. See
[[skill-ship-is-gitlab-use-gh]] for the PR flow.
