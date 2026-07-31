# COPA Hackathon — Agent Guide

AI for BNM policy consistency (COPA Hackathon 2026, Must-Win 10). **Project SELARAS**
— **S**emantic **E**ngine for **L**inkage **A**nalysis across **R**egulatory
**A**rtefacts & **S**tandards — is the current product: each policy workstream
(DP / ED / PD under active drafting) is a knowledge graph of documents joined by
structural edges, and AI-found linkages between clause pairs surface as findings the
drafter reviews and accepts before drafting. Findings carry a **five-label semantic
taxonomy** — `aligns-with` / `differs-on` / `conflicts-with` / `silent-on` /
`goes-beyond`.

Working code lives in `engine/` (FastAPI + the finder→critic loop), `frontend/` (the
SELARAS app), plus earlier iterations kept as reference. This is **not** a
docs-only repo.

> **Renamed 30 Jul 2026 — "Workstream Brain" is the old product name.** The current
> product is **Project SELARAS**; use that in prose, UI copy, and new specs. The old
> name survives deliberately in three places, and none of them is a bug to fix:
> directory slugs (`docs/specs/workstream-brain/`, `docs/poc/workstream-brain/`, and
> the `deploy-poc.yml` paths that publish them), superseded specs, and
> `docs/learnings/`. **"Workstream" alone is still live domain vocabulary** —
> `data/workstreams/`, `/api/workstreams/*`, the workstream fixtures — and the rename
> does not touch it.

> **Iteration history — read this before trusting any spec.** Four generations, each
> superseding the last: policy-consistency-ai → rulebook-radar → reconciliation-workbench
> → **workstream-brain, now Project SELARAS (current)**. Older specs and POCs are
> retained as historical record and are explicitly _not_ buildable.
> `Conflict / Duplication / Gap` is **retired**
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
- `frontend/` — **the SELARAS app** (Vite + React 18 + Tailwind + shadcn/ui).
  The only frontend. This is where UI work lands.
- `data/corpus/` — the parsed BNM policy PDFs; `data/workstreams/` — workstream
  fixtures, which the API reads (see the retired-fixtures rule below);
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
> removed when SELARAS became the end state. If a spec or POC references
> them, that spec is describing a repo that no longer exists.

**Docs:** `docs/discovery/` (briefs per iteration), `docs/adr/` (decisions),
`docs/learnings/` (repo conventions — read `INDEX.md` first).

**Confidential:** `docs/references/` — **git-ignored**, internal, local only.
Note this is _not_ `data/references/`, which is public and tracked.

## Retired workstream fixtures (hard rule)

`data/workstreams/` holds four fixtures. Three are **retired** and carry
`"hidden": true` in their `workstream.json`:

| Fixture                | State                                  |
| ---------------------- | -------------------------------------- |
| `open-finance-pd-2026` | **live** — the current demo workstream |
| `opres-v2`             | retired, hidden                        |
| `rmit-v2-2025`         | retired, hidden                        |
| `open-finance-ed`      | retired, hidden                        |

**A retired fixture's data oddities are not bugs. Do not fix them.** They stay on
disk because the engine suite reads several of them by id, and `hidden: true`
keeps them out of the drafter's sidebar. Only `list_workstreams` honours the flag
— every direct-id route still serves a hidden workstream, so existing links and
tests keep working (`engine/workstreams.py`'s `list_workstreams` docstring is the
source of truth).

Concretely, leave these alone: the retired `contributes-to` edge type still stored
in `opres-v2` / `rmit-v2-2025`; `opres-v2`'s second task node (`opres-pd-v0-0`)
and its edges; seeded drafts that predate the deliverable-kind vocabulary and so
carry no `task_type`; the absence of anchor↔anchor edges in `opres-v2`; and the
duplicated `name` between `open-finance-ed` and `open-finance-pd-2026`. Each is
recorded history, and "correcting" one silently changes what a test asserts.

Build and demo against **`open-finance-pd-2026`**. Use a retired fixture only as
a regression check that existing behaviour still holds — never as the shape a new
feature is designed around. `data/corpus/` and `data/artifacts/` are not covered
by this rule.

## Conventions

- Specs are non-technical and grounded in real clauses (RMiT 17.1/17.2,
  Outsourcing 12.1, Operational Resilience 1.1 — note "OpRes 6.11" is a phantom
  clause, not in the parsed corpus).
- **Personas.** Aisyah R. is the policy drafter throughout. The SELARAS
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
- **Read routes are fixture projections; `analyze` and `copilot` are live.** The GET
  routes (graph, node/edge detail, review, findings, cross-links) are projections over
  `data/workstreams/`. But `create_app()` exposes injectable model seams —
  `run_arm_g_fn`, `copilot_reply_fn`, `copilot_stream_fn` — and the `analyze` route
  (`POST .../edges/{edge_id}/analyze`) calls `run_arm_g_fn(src_doc, tgt_doc)`, whose
  default adapter runs the real Arm G pipeline (`engine/arm_g.py`, which calls
  `engine.llm.call_chat`). Since #52 it resolves a document's anchors from the
  **workstream's own** anchors (`engine.ws_anchors.build_index(workstreams_dir,
workstream_id)`, per-node files under `data/workstreams/<ws>/anchors/`), falling back
  to the shared `data/artifacts/anchor-index.json` only for a legacy workstream that
  ships none of its own. `canned_analysis` no longer exists. Tests inject stubs for
  these seams, so CI needs no model or creds — but the running service **does** reach a
  model on `analyze`/`copilot`. The demo strategy is build-and-persist: a workstream's
  anchors, axes, and findings are committed with it so no model call is needed on the
  day. (The `verdicts`/`connections` legacy finder is retained only as a rollback seam.)

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
- **Workstream-brain uses the fixture base, not the specs' shapes** — the
  workstream-brain specs are greenfield-stale; build screens to the committed
  fixtures + `engine/workstreams.py` (`node_type`/`edge_type`, `analysed` derived
  from a findings file). See
  `docs/learnings/convention-workstream-brain-opres-v2-conventions.md` — but note
  two of its claims are now `opres-v2`-only, not general: **the task node is _not_
  always the edge source** (`open-finance-pd-2026` points its edges _into_ the ED
  node, so read both endpoints and never normalise direction), and `opres-v2` is a
  retired fixture, so design against `open-finance-pd-2026` per the retired-fixtures
  rule above.
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

## Frontend conventions (the SELARAS app)

- **The frontend is `frontend/`** — Vite + React 18 + TypeScript + Tailwind + shadcn/ui.
- **Graph library:** `react-force-graph-2d` for all interactive graph canvases.
- **API base:** set `VITE_API_BASE` in `frontend/.env` (defaults to `http://localhost:8000`).
- **State:** TanStack Query for all server state; no Redux/Zustand.
- **Node types (8):** task, internal-published, international-standard, peer-regulator,
  act-law, industry-input, supervisory-letter, others.
- **Edge types (3):** supersedes, references, parallel-to. `contributes-to` was
  retired on 29 Jul 2026 (folded into `references`); `engine.workstreams.EDGE_TYPES`
  refuses it on write, but the retired fixtures (`opres-v2`, `rmit-v2-2025`) still
  store it and the read projections pass it through, so don't "fix" those graphs.
- **Finding labels (5):** aligns-with, differs-on, conflicts-with, silent-on, goes-beyond.
- **Sentiment (3, differs-on only):** tighten, loosen, neutral.
- **CORS:** FastAPI includes CORS middleware allowing origin `http://localhost:5173`.
- **Theme:** single light theme only — no dark mode, no toggle. Off-white
  page background, white cards, a royal-blue primary accent. See
  `frontend/src/index.css`'s `:root` block for the token values.
