# COPA Hackathon — Agent Guide

AI for BNM policy consistency (COPA Hackathon 2026, Must-Win 10). **Workstream Brain**
is the current product: each policy workstream (DP / ED / PD under active drafting) is
a knowledge graph of documents joined by structural edges, and AI-found linkages between
clause pairs surface as findings the drafter reviews and accepts before drafting.
Findings carry a **five-label semantic taxonomy** — `aligns-with` / `differs-on` /
`conflicts-with` / `silent-on` / `goes-beyond`.

Working code lives in `engine/` (FastAPI + the finder→critic loop), `frontend/` (the
Workstream Brain app), plus earlier iterations kept as reference. This is **not** a
docs-only repo.

> **Iteration history — read this before trusting any spec.** Four generations, each
> superseding the last: policy-consistency-ai → rulebook-radar → reconciliation-workbench
> → **workstream-brain (current)**. Older specs and POCs are retained as historical record
> and are explicitly _not_ buildable. `Conflict / Duplication / Gap` is **retired**
> vocabulary from the rulebook-radar era — `engine/tests/test_taxonomy_traces.py::test_no_retired_vocabulary_as_label`
> asserts it never reappears as a finding `label`.

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

> ⚠️ **This section is stale and needs a decision.** Epic #5 and stories #6–#11 below
> describe the **superseded rulebook-radar** plan and are still open, while actual work
> ships as PRs with no matching issues (#33–#37, workstream-brain). Don't assume an
> issue exists for the work you're doing; confirm with `gh issue list` first.

- Epic **#5** = high-level checklist. Stories **#6–#11**, one per spec in
  `docs/specs/rulebook-radar/`; each spec's `**Ticket:**` field links to its issue.
- Milestone: `Rulebook Radar MVP1 (Hackathon 3 Aug 2026)`.
- Build order / deps: #6 engine (first) → #7 workspace (#6) → #8 ripple (#6,#7)
  → #9 copilot (#6,#8); #10 supervisor (#6, parallel); #11 reviewer (#7,#8).
- Read a ticket before working it: `gh issue view <n>` (links to its spec).
- **Put `Closes #<n>` in the PR body** — merging auto-closes the issue, ticks the
  epic checklist, and moves the board card to Done. Don't hand-edit issue state.

## Confidentiality (hard rule)

This repo is **public**. `docs/references/` holds internal BNM documents and is
git-ignored — **never** add, commit, or push anything sensitive to a tracked path.
Before any commit, verify nothing under `docs/references/` is staged.

## Product rule — verbatim citation

Every finding, checklist line, and copilot answer must **quote the exact clause**
it relies on, with its clause number. If no clause supports a claim, state "No
matching clause found" — never invent one. Preserve this in any spec or POC edit.

## Repository layout

**Live code:**

- `engine/` — FastAPI read service, clause index, finder→critic connection loop.
  Serves two route families (see "Two taxonomies" below).
- `frontend/` — **the Workstream Brain app** (Vite + React 18 + Tailwind + shadcn/ui).
  This is where current UI work lands.
- `data/corpus/` — the parsed BNM policy PDFs; `data/workstreams/` — workstream
  fixtures (`opres-v2`, `outsourcing-v2`, `rmit-v2-2025`); `data/references/` —
  **public** external standards (Basel, MAS TRM, PDPA). Not confidential.
- `kg-poc/` — standalone ontology/NER pipeline experiment (MECE-7 classes).
- `scripts/` — trace runners, snapshot exporter.

**Earlier iterations — read-only reference, do not build from:**

- `web/` — Next.js app from the reconciliation-workbench iteration (superseded).
- `docs/poc/{policy-consistency-ai,drafter-knowledge-graph,workstream-brain}/` —
  three generations of clickable HTML prototypes; the workstream-brain set is the
  UX reference for current work.
- `docs/specs/{rulebook-radar,reconciliation-workbench}/` — superseded epics.
  `docs/specs/workstream-brain/` is current but **greenfield-stale** — see the
  opres-v2 learning below before building from it.

**Docs:** `docs/discovery/` (briefs per iteration), `docs/adr/` (decisions),
`docs/learnings/` (repo conventions — read `INDEX.md` first).

**Confidential:** `docs/references/` — **git-ignored**, internal, local only.
Note this is _not_ `data/references/`, which is public and tracked.

## Conventions

- Specs are non-technical and grounded in real clauses (RMiT 17.1/17.2,
  Outsourcing 12.1, Operational Resilience 1.1 — note "OpRes 6.11" is a phantom
  clause, not in the parsed corpus).
- **Personas.** Aisyah R. is the policy drafter throughout. The Workstream Brain
  demo runs on **OpRes PD v0.3** as the task node (the editable working draft);
  every other document in the workstream is published, read-only context. An
  approving manager gives the final sign-off. There is **no separate reviewer
  persona** — the reviewer / multi-draft model (incl. Farid M.) is deferred.
- **Scope is multi-workstream, not a single cluster.** MVP1 demos at least two real
  BNM workstreams in parallel (Operational Resilience + Open Finance ED response);
  cross-workstream linkage is the demo climax, not a preview. The management-facing
  institution map is deferred to a follow-on epic.
- **The frontend is `frontend/`** — Vite + React 18 + Tailwind + shadcn/ui, with
  TanStack Query against the engine's `/api/workstreams/*` routes. This is where
  Workstream Brain UI work lands (#36, #37). `web/` is the **previous** iteration's
  Next.js app (reconciliation workbench, Zustand + persist, `NEXT_PUBLIC_API_BASE`)
  and is not the active surface — don't add workstream-brain screens there. The
  `docs/poc/workstream-brain/*.html` pages are the read-only UX reference.
- **Two taxonomies live in the engine — don't conflate them.** They are separate
  fields on separate route families:

  | Module                  | Field     | Values                                                                        | Serves                             |
  | ----------------------- | --------- | ----------------------------------------------------------------------------- | ---------------------------------- |
  | `engine/connections.py` | `label`   | `aligns-with` / `differs-on` / `conflicts-with` / `silent-on` / `goes-beyond` | `/api/workstreams/*` → `frontend/` |
  | `engine/verdicts.py`    | `verdict` | `Consensus` / `Conflict` / `Gap` / `Duplicate` / `Partial`                    | legacy routes → `web/`             |

  Both have five values and both contain a "conflict", but they mean different things.
  New workstream-brain work uses `label`. The retired-vocabulary test guards `label`
  only, so `verdicts.py` legitimately still emits `Conflict` as a `verdict`.

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
- **The frontend is a build-step app, and Workstream Brain's is `frontend/`** — the
  11 Jul 2026 re-platform retired "self-contained HTML, no build step"; don't flag a
  framework/`package.json`/build step as a mistake. Current UI work is `frontend/`
  (Vite + React 18), **not** `web/` (the previous iteration's Next.js app). See
  `docs/learnings/convention-frontend-app-is-frontend-dir.md`.
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
- **Workstream-brain uses the opres-v2 base, not the specs' shapes** — the
  workstream-brain specs are greenfield-stale; build screens to the `opres-v2`
  fixtures + `engine/workstreams.py` (`node_type`/`edge_type`, `analysed` derived
  from a findings file, task node is always the edge source). See
  `docs/learnings/convention-workstream-brain-opres-v2-conventions.md`.
- **Run forge builds in the main tree, not a worktree** — `.venv` and
  `frontend/node_modules` exist only in the main working tree, so builds that need
  `pytest`/`vitest` must run there rather than in isolated feature-builder
  worktrees. See `docs/learnings/blocker-forge-build-run-in-main-worktree.md`.
