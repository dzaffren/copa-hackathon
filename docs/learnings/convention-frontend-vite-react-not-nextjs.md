---
name: frontend-vite-react-not-nextjs
description: Workstream-brain frontend is Vite + React 18 + TS + Tailwind + shadcn/ui under frontend/, not the archived Next.js app under archive/web/
type: convention
captured: 2026-07-18
source: workstream-brain epic tech-stack finalisation; supersedes the reconciliation-workbench Next.js decision (11 Jul 2026)
---

The Workstream Brain MVP1 demo frontend is a **Vite + React 18 + TypeScript +
Tailwind + shadcn/ui** SPA planned under `frontend/src/features/{feature}/`,
using **React Router v6** for routing, **TanStack Query** for the FastAPI data
layer, and **react-hook-form + zod** for forms. Every user-facing spec in
`docs/specs/workstream-brain/` (`spec-workstream-graph.md`,
`spec-review-linkages.md`, `spec-task-screen.md`, `spec-drafting-workspace.md`,
`spec-new-workstream.md`) targets this stack and this location.

**Why:** The workstream-brain epic supersedes the earlier Reconciliation
Workbench Next.js re-platform (11 Jul 2026). The Next.js app that lived at
`web/` has been moved to `archive/web/` alongside the retired
reconciliation-workbench specs at `docs/specs/reconciliation-workbench/`. A
future session reading the old "Next.js under `web/`" convention could wrongly
extend the archived app or scaffold the new frontend in the wrong toolchain.

**How to apply:** When building any user-facing workstream-brain story, scaffold
into `frontend/src/features/{feature}/` using the Vite + React + TS toolchain.
Reuse the shadcn primitives across features (Card, Badge, Dialog, Tabs, etc.).
Data goes through `engine/api.py` (FastAPI) via TanStack Query hooks. Do NOT
extend `archive/web/`; do NOT reintroduce Next.js.

See also: [[skill-ship-is-gitlab-use-gh]] for this repo's GitHub PR flow;
[[convention-frontend-nextjs-not-static-html]] (superseded — kept for history).
