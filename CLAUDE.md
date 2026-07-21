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

## Issue tracking — none

**This repo does not use an issue tracker.** GitHub Issues was abandoned on
16 Jul 2026; the rulebook-radar epic (#5) and its stories (#6–#11, #26) described a
plan superseded twice over and were closed. Don't open issues, don't look for a
ticket before working, and **don't put `Closes #<n>` in a PR body** — there is
nothing to close. A spec under `docs/specs/workstream-brain/` plus a PR is the whole
process. Specs may still carry a stale `**Ticket:**` field; ignore it.

## Confidentiality (hard rule)

This repo is **public**. `docs/references/` holds internal BNM documents and is
git-ignored — **never** add, commit, or push anything sensitive to a tracked path.
Before any commit, verify nothing under `docs/references/` is staged.

## Product rule — verbatim citation

Every finding, checklist line, and copilot answer must **quote the exact clause**
it relies on, with its clause number. If no clause supports a claim, state "No
matching clause found" — never invent one. Preserve this in any spec or POC edit.

## Repository layout

**Live code — this is the whole product now:**

- `engine/` — FastAPI service serving **only** `/api/workstreams/*`, projections over
  `data/workstreams/`. Also holds `clauses.py` (the clause index / verbatim guarantee)
  and `connections.py` (the five-label finder→critic loop) — the current engine, not
  yet mounted as HTTP routes; exercised by `scripts/run_finder_trace.py` and tests.
- `frontend/` — **the Workstream Brain app** (Vite + React 18 + Tailwind + shadcn/ui).
  The only frontend. This is where UI work lands.
- `data/corpus/` — the parsed BNM policy PDFs; `data/workstreams/` — workstream
  fixtures (`opres-v2`, `outsourcing-v2`, `rmit-v2-2025`), which the API reads;
  `data/references/` — **public** external standards (Basel, MAS TRM, PDPA);
  `data/artifacts/` — built clause index + recorded linkage traces (see the
  narrowing blocker below).
- `kg-poc/` — standalone ontology/NER pipeline spike (MECE-7 classes). Isolated —
  nothing imports it, and its `node_type` vocabulary is unrelated to the engine's.
- `scripts/` — `run_finder_trace.py` (records linkage traces).

**Earlier iterations — read-only reference, do not build from:**

- `docs/poc/{policy-consistency-ai,drafter-knowledge-graph,workstream-brain}/` —
  three generations of clickable HTML prototypes; the workstream-brain set is the
  UX reference for current work.
- `docs/specs/{rulebook-radar,reconciliation-workbench}/` — superseded epics.
  `docs/specs/workstream-brain/` is current but **greenfield-stale** — see the
  opres-v2 learning below before building from it.

> **The legacy code is gone** (16 Jul 2026). `web/` (the reconciliation-workbench
> Next.js app), `engine/{verdicts,submissions,read_model}.py`, the clause/graph/
> paragraph/submission HTTP routes, and `scripts/export_poc_snapshot.py` were all
> removed when Workstream Brain became the end state. If a spec or POC references
> them, that spec is describing a repo that no longer exists.

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
  TanStack Query against the engine's `/api/workstreams/*` routes (`VITE_API_BASE`).
  It is now the only frontend. The `docs/poc/workstream-brain/*.html` pages are the
  read-only UX reference.
- **One taxonomy: the five semantic labels.** Findings carry exactly one `label` —
  `aligns-with` / `differs-on` / `conflicts-with` / `silent-on` / `goes-beyond`
  (`engine/connections.py`), with `sentiment` (`tighten`/`loosen`) valid **only** on
  `differs-on`. `engine/tests/test_taxonomy_traces.py` guards this. The competing
  `verdict` vocabulary (`Consensus`/`Conflict`/`Gap`/`Duplicate`/`Partial`) went with
  `verdicts.py`, so "conflict" now means exactly one thing.
- **The API is a fixture projection, not a model client.** Every route reads
  `data/workstreams/`; the `analyze` route replays `workstreams.canned_analysis` for
  the demo pair and returns `no_matching_source` otherwise. `create_app()` takes no
  model seam, so the service _cannot_ reach a model — editing `connections.py` will
  not change what the demo renders.

## Learnings

- **mypy third-party stub baseline** — the 4 mypy warnings in `engine/`
  (`markitdown` + `azure.ai.inference` missing stubs) are an accepted baseline;
  don't chase them or add `# type: ignore`. See
  `docs/learnings/convention-mypy-third-party-stub-baseline.md`.
- **FastAPI TestClient deps** — tests using `fastapi.testclient.TestClient` need
  `httpx` and `python-multipart` as explicit `pyproject.toml` deps (not pulled in
  by `fastapi` alone). See `docs/learnings/pattern-fastapi-testclient-deps.md`.
- **Engine deps live in two places** — a new `engine/` dependency must be added to
  **both** `pyproject.toml` and the explicit `pip install` list in
  `.github/workflows/test.yml`; CI does not install from `pyproject.toml`. Miss the
  second and CI fails collection on every `engine.api` importer while your local
  suite stays green (the venv already has it). See
  `docs/learnings/pattern-engine-deps-live-in-two-places.md`.
- **/ship is GitLab — use gh** — the `/ship` skill targets GitLab; on this GitHub repo
  override to `gh pr create --base dzaf/main`. **No `Closes #<n>`** — there is no issue
  tracker. See `docs/learnings/skill-ship-is-gitlab-use-gh.md`.
- **The frontend is a build-step app, and it's `frontend/`** — the 11 Jul 2026
  re-platform retired "self-contained HTML, no build step"; don't flag a
  framework/`package.json`/build step as a mistake. `frontend/` (Vite + React 18) is
  now the only frontend. See
  `docs/learnings/convention-frontend-app-is-frontend-dir.md`.
- **Offline build needs Azure Document Intelligence** — a full `python -m engine.build`
  fails offline on the legacy tech-risk PDFs (`BCM 9.17` won't resolve → `GraphBuildError`)
  because the default extractor scrambles multi-column PDFs; the committed artifacts were
  DI-built. The AI DP + references DO build offline — don't read that `GraphBuildError`
  as a regression. See `docs/learnings/convention-offline-build-needs-docintel.md`.
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
- **`engine.build` silently narrows `data/artifacts/`** — a rebuild without Azure
  Document Intelligence shrinks the clause index instead of failing (#34 took it from
  7 documents to 2 and orphaned two committed traces; the suite stays green because
  the trace tests never re-resolve citations). Don't rebuild without DI; diff the
  entry count before committing; **don't** naive-restore from an old revision — the
  document IDs are disjoint and it breaks the one working trace. Legacy-path only:
  workstream-brain reads `data/workstreams/`, not `data/artifacts/`. See
  `docs/learnings/blocker-engine-build-silently-narrows-artifacts.md`.

## Frontend conventions (Workstream Brain app)

- **The frontend is `frontend/`** — Vite + React 18 + TypeScript + Tailwind + shadcn/ui.
- **Graph library:** `react-force-graph-2d` for all interactive graph canvases.
- **API base:** set `VITE_API_BASE` in `frontend/.env` (defaults to `http://localhost:8000`).
- **State:** TanStack Query for all server state; no Redux/Zustand.
- **Node types (8):** task, internal-published, international-standard, peer-regulator,
  act-law, industry-input, supervisory-letter, others.
- **Edge types (4):** supersedes, references, contributes-to, parallel-to.
- **Finding labels (5):** aligns-with, differs-on, conflicts-with, silent-on, goes-beyond.
- **Sentiment (3, differs-on only):** tighten, loosen, neutral.
- **CORS:** FastAPI includes CORS middleware allowing origin `http://localhost:5173`.
- **Dark mode:** default theme. Deep navy/slate, NOT pure black.
