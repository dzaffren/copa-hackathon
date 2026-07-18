# Workstream Brain — Agent Guide

AI for BNM cross-workstream policy drafting (COPA Hackathon 2026, Must-Win 10).
A knowledge-graph tool that maps every document a policy workstream depends on
(BNM peers, BCBS mother-docs, national acts, industry input) and surfaces
five-label semantic linkages — `aligns-with` / `differs-on` / `conflicts-with` /
`silent-on` / `goes-beyond` — between clause pairs. Each finding cites the
exact clause it relies on. Cross-jurisdiction pairs run through an axis-first
retrieval pipeline so "same axis, different terminology" pairs (Malaysia's
conforming loans ≡ England's Level C loans) are discoverable.

**Live epic:** [`docs/specs/workstream-brain/spec.md`](docs/specs/workstream-brain/spec.md).
**Retired predecessors:** the Rulebook Radar epic
([`docs/specs/rulebook-radar/`](docs/specs/rulebook-radar/), superseded 11 Jul 2026)
and the Reconciliation Workbench re-platform ([`docs/specs/reconciliation-workbench/`](docs/specs/reconciliation-workbench/),
superseded by workstream-brain). Legacy code that backed those epics — the Next.js
`web/` frontend and the `kg-poc` prototype — lives under [`archive/`](archive/) and is
not part of the MVP1 build.

## Git strategy (follow exactly)

Full guideline: [`CONTRIBUTING.md`](CONTRIBUTING.md). Enforceable rules:

- **Never commit to `main` directly.** Branch, then open a PR. Model is GitHub Flow.
- Branch names: `type/short-kebab` (`feat/`, `fix/`, `docs/`, `chore/`, `refactor/`).
- Commits use **Conventional Commits**: `type(scope): imperative summary` (≤72 chars).
  Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`.
- One logical change per commit; explain **why** in the body when non-obvious.
- Prefer **squash merge**; delete the branch after merge.
- **Only commit or push when the user explicitly asks.**

## Issue tracking

Tracker is **GitHub Issues + a Project board** (no Jira). Use the `gh` CLI.

- Workstream Brain MVP1 stories live under `docs/specs/workstream-brain/`; each
  spec's `**Ticket:**` field links to its issue when one exists. Story tickets
  are marked `TBD` in the spec table until they land on the tracker.
- Milestone: `Workstream Brain MVP1 (Hackathon 3 Aug 2026)`.
- Build order / deps (see the epic's Rollout Strategy):
  1. **engine taxonomy widening** → 2. **anchor segmentation** → 3. **retrieval
     pipeline** → 4. user-facing screens (workstream graph, task, review linkages,
     new workstream) → 5. drafting workspace (last).
- Read a ticket before working it: `gh issue view <n>` (links to its spec).
- **Put `Closes #<n>` in the PR body** — merging auto-closes the issue, ticks the
  epic checklist, and moves the board card to Done. Don't hand-edit issue state.
- Historical: Rulebook Radar epic **#5** (stories #6–#11) is retired; its issues
  stay on GitHub for history but are not being worked.

## Confidentiality (hard rule)

This repo is **public**. `docs/references/` holds internal BNM documents and is
git-ignored — **never** add, commit, or push anything sensitive to a tracked path.
Before any commit, verify nothing under `docs/references/` is staged.

## Product rule — verbatim citation

Every finding, checklist line, and copilot answer must **quote the exact clause**
it relies on, with its clause number. If no clause supports a claim, state "No
matching clause found" — never invent one. Preserve this in any spec or POC edit.

## Repository layout

- `docs/discovery/workstream-brain-mvp1/` — discovery brief for the live epic
- `docs/poc/workstream-brain/` — clickable HTML prototype (read-only UX reference)
- `docs/specs/workstream-brain/` — **live epic**: overview + engine specs
  (taxonomy, anchor segmentation, retrieval pipeline) + user-facing story specs
- `docs/specs/rulebook-radar/`, `docs/specs/reconciliation-workbench/` — retired
  predecessor specs; kept for historical reference, not built from
- `docs/references/` — **git-ignored**, internal BNM material, local only
- `engine/` — FastAPI backend + knowledge-graph engine (`engine/api.py` is the
  frontend seam)
- `data/corpus/` — public source PDFs, keyed by `data/corpus/manifest.json`
- `data/artifacts/` — build outputs (anchor index, connection traces, axes caches)
- `archive/` — retired code (`web/` Next.js frontend, `kg-poc` prototype); not
  built or referenced by the live epic

## Tech stack (MVP1)

- **Backend:** Python 3.12 + FastAPI, entrypoint `engine/api.py`; runs offline
  in demo mode by replaying `data/artifacts/connection-trace-*.json`, with live
  Azure OpenAI + Azure Document Intelligence seams for full builds.
- **Frontend:** **Vite + React 18 + TypeScript + Tailwind + shadcn/ui**, planned
  under `frontend/src/features/{feature}/` per the workstream-brain user-facing
  specs. Routing via React Router v6; data via TanStack Query; forms via
  react-hook-form + zod. The `frontend/` directory does not exist yet — it is
  created by the user-facing story builds.
- **Retired:** the Next.js app under `archive/web/` and the `kg-poc` prototype
  under `archive/kg-poc/` are not part of MVP1 and should not be extended.

## Conventions

- **Personas (workstream-brain MVP1):** Aisyah R. drafts and owns the workstream;
  Farid M. and Priya S. review findings. No separate "approving manager"
  persona — the drafter's closing action is to submit for reviewer sign-off.
- **Semantic labels on findings only:** graph edges are structural (`supersedes`
  / `references` / `contributes-to` / `parallel-to`), declared at
  node-creation time. Semantic labels (`aligns-with` / `differs-on` /
  `conflicts-with` / `silent-on` / `goes-beyond`) live on _findings_ — never
  render them on the graph edges themselves.
- **Sentiment is `differs-on`-only:** `tighten` / `loosen` / `neutral` attaches
  exclusively to `differs-on` findings; other labels carry no sentiment.
- **MVP1 scope:** UK + HK + SG + BCBS mother-docs (CRE, OPE, BCP) alongside the
  BNM cluster. NZ, EU, US, ID stay archived in `data/corpus/temp/` until v2. One
  cross-jurisdiction demo pair (SG MAS 637 × UK BoE Chapter 3) runs the full
  finder→critic loop; other jurisdictions are retrievable but not
  full-analysed.

## Learnings

- **mypy third-party stub baseline** — the 4 mypy warnings in `engine/`
  (`markitdown` + `azure.ai.inference` missing stubs) are an accepted baseline;
  don't chase them or add `# type: ignore`. See
  `docs/learnings/convention-mypy-third-party-stub-baseline.md`.
- **FastAPI TestClient deps** — tests using `fastapi.testclient.TestClient` need
  `httpx` and `python-multipart` as explicit `pyproject.toml` deps (not pulled in
  by `fastapi` alone). See `docs/learnings/pattern-fastapi-testclient-deps.md`.
- **/ship is GitLab — use gh** — the `/ship` skill targets GitLab; on this GitHub
  repo override to `gh pr create --base main` with `Closes #<n>` in the PR body.
  See `docs/learnings/skill-ship-is-gitlab-use-gh.md`.
- **Frontend is Vite + React under `frontend/`, not the archived `web/`** — the
  workstream-brain epic uses Vite + React 18 + TypeScript + Tailwind + shadcn/ui
  planned under `frontend/src/features/{feature}/`. The Next.js app under
  `archive/web/` is retired reconciliation-workbench code; do not extend it. See
  `docs/learnings/convention-frontend-vite-react-not-nextjs.md`.
- **Offline build needs Azure Document Intelligence** — a full `python -m engine.build`
  fails offline on the legacy tech-risk PDFs (`BCM 9.17` won't resolve → `GraphBuildError`)
  because the default extractor scrambles multi-column PDFs; the committed artifacts were
  DI-built. The AI DP + references + `verdicts.json` DO build offline — don't read that
  `GraphBuildError` as a regression. See
  `docs/learnings/convention-offline-build-needs-docintel.md`.
- **Engine artifact writes must be UTF-8** — pass `encoding="utf-8"` to any `write_text`
  of document/markdown text in `engine/`; the AI DP's Unicode glyphs (U+2212) crash the
  cp1252 platform default on Windows. See
  `docs/learnings/pattern-engine-artifact-writes-utf8.md`.
- **Forge verify hook false-fails here** — the forge `stop-verify` Stop hook reports
  `LINT FAIL: No global/local python version…` because `.python-version` pins an
  uninstalled `3.13` and `ruff` isn't installed; it's cosmetic (pytest via `.venv` is
  green). Verify with `.venv/Scripts/python.exe -m pytest engine/tests`; don't disable
  all hooks (kills secret-scan) or install ruff to appease it. See
  `docs/learnings/blocker-forge-verify-hook-false-fail-pyenv-ruff.md`.
