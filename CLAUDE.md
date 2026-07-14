# Rulebook Radar — Agent Guide

AI for BNM policy consistency (COPA Hackathon 2026, Must-Win 10). A knowledge-graph
tool that flags Conflict / Duplication / Gap findings when a policy changes
(drafter) and checks a bank submission for missing requirements (supervisor).
Docs-only repo today: discovery brief, a clickable HTML POC, and PRD specs.

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

- `docs/discovery/` — discovery brief (opportunity solution tree, LLM experiment)
- `docs/poc/policy-consistency-ai/` — clickable prototype; open `index.html`
- `docs/specs/rulebook-radar/` — epic overview (`spec.md`) + 6 story specs
- `docs/references/` — **git-ignored**, internal, local only

## Conventions

- Specs are non-technical and grounded in real clauses (RMiT 17.1/17.2,
  Outsourcing 12.1, Operational Resilience 1.1 — note "OpRes 6.11" is a phantom
  clause, not in the parsed corpus). Keep personas consistent (single-draft MVP1, per
  the 9 Jul 2026 pivot): Aisyah R. drafts **RMiT v2** — the sole editable draft;
  every other BNM policy is published, read-only context; an approving manager gives
  the final sign-off. There is **no separate reviewer persona** in MVP1 — the
  reviewer / multi-draft model (incl. Farid M.) is deferred to a future phase.
- Drafter value leads with the **Reference Radar** (external references — peer
  regulators, acts like PDPA, standards — cited verbatim); internal Conflict /
  Duplication / Gap consistency is the secondary "good to know" layer and the
  supervisor-checklist engine.
- The demo frontend is a **Next.js + React + Tailwind + shadcn/ui** app under `web/`
  (deployed to Vercel), with **Zustand + persist** for the shared finding state and a
  bundled JSON snapshot (`web/public/data/`) that `NEXT_PUBLIC_API_BASE` can swap for the
  live FastAPI engine. This **supersedes** the earlier "self-contained HTML, no build step"
  convention (11 Jul 2026 re-platform — see
  `docs/specs/reconciliation-workbench/frontend-nextjs-migration-design.md`). The old
  `docs/poc/drafter-knowledge-graph/*.html` pages are kept as the read-only UX reference.
- MVP1 scope is a single cluster (technology-risk); cross-cluster ripple is a
  labelled "what's next" preview, not built.

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
- **Frontend is Next.js under `web/`, not static HTML** — the 11 Jul 2026 re-platform
  replaced the "self-contained HTML, no build step" convention with a Next.js + React app.
  Don't flag the framework/`package.json`/build step as a mistake. See
  `docs/learnings/convention-frontend-nextjs-not-static-html.md`.
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
