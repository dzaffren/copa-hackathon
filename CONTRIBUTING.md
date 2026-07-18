# Contributing — Git Strategy

This repository uses a lightweight **GitHub Flow** model: `main` is always
releasable, and all work happens on short-lived branches that merge back through a
pull request. It is deliberately simple — right-sized for a small hackathon team.

> Working with an AI agent (e.g. Claude Code)? The enforceable rules below are
> mirrored in [`CLAUDE.md`](CLAUDE.md), which agents load automatically. Humans
> and agents follow the same strategy.

## Golden rules

1. **Never commit directly to `main`.** Branch, then open a pull request.
2. **Never commit confidential material.** Internal BNM documents live in
   `docs/references/` and are git-ignored. Do not add anything sensitive to a
   tracked path. This repo is **public**.
3. **Keep `main` green.** Only merge work that is complete and reviewed.

## Branching

Branch off the latest `main`:

```bash
git switch main && git pull
git switch -c docs/supervisor-checklist
```

Branch names use `type/short-kebab-description`, where `type` matches the commit
types below:

| Prefix      | Use for                                         | Example                       |
| ----------- | ----------------------------------------------- | ----------------------------- |
| `feat/`     | A new capability (spec, POC page, tool feature) | `feat/graph-engine`           |
| `fix/`      | Correcting something broken or wrong            | `fix/impact-citation`         |
| `docs/`     | Specs, briefs, README, and other documentation  | `docs/reviewer-approval-spec` |
| `chore/`    | Tooling, config, housekeeping                   | `chore/add-gitignore`         |
| `refactor/` | Restructuring without changing behaviour        | `refactor/poc-shared-nav`     |

## Commits — Conventional Commits

Format: `type(optional-scope): summary` in the imperative mood, under ~72 chars.

```
docs(specs): add supervisor submission-check story
feat(poc): add drafting copilot page
fix(poc): correct RMiT clause 17 citation on impact report
```

Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`.

Guidance:

- One logical change per commit; keep them focused and reviewable.
- Explain **why** in the body when the reason isn't obvious from the diff.
- Never mix a confidential document into a commit.

## Pull requests

1. Push your branch and open a PR against `main` (`gh pr create` is fine).
2. **Title** follows the Conventional Commit format.
3. **Description** covers: what changed, why, and how to verify (for a POC page,
   which file to open).
4. **Self-review the diff** and confirm the pre-merge checklist below before
   merging. Review approval is not required on `main`, so you can merge your own
   PR — reviews are welcome but optional.
5. Prefer **squash merge** to keep `main` history linear and readable.
6. Delete the branch after merge.

### Pre-merge checklist

- [ ] No confidential / internal documents added to a tracked path.
- [ ] `git status` shows nothing under `docs/references/` staged.
- [ ] Specs stay internally consistent (personas, clause citations, story index).
- [ ] Commit messages follow Conventional Commits.

## Issue tracking

We use **GitHub Issues + a Project board** as the tracker (no Jira). Everything
lives in this repo.

- **Milestone:** `Workstream Brain MVP1 (Hackathon 3 Aug 2026)` — the delivery deadline.
- **Live epic:** [`docs/specs/workstream-brain/spec.md`](docs/specs/workstream-brain/spec.md)
  lists every story with dependencies. Each story spec's `**Ticket:**` field
  links to its GitHub issue when one exists (`TBD` until it lands on the tracker).
- **Project board:** _Workstream Brain MVP1_ — a Todo / In Progress / Done view
  of those issues (Projects tab → open the board).

| Story                                            | Type        | Build order / depends on      |
| ------------------------------------------------ | ----------- | ----------------------------- |
| Linkage taxonomy widening                        | Technical   | build first — no deps         |
| Anchor segmentation (multi-strategy AnchorIndex) | Technical   | taxonomy                      |
| Retrieval-first pipeline (axes + hybrid)         | Technical   | taxonomy; anchor segmentation |
| Workstream graph screen (hero)                   | User-facing | anchor segmentation           |
| Task screen with pairwise comparison             | User-facing | graph; retrieval pipeline     |
| Review linkages screen                           | User-facing | graph; retrieval pipeline     |
| New workstream form                              | User-facing | graph                         |
| Drafting workspace with 3-tab side panel         | User-facing | review linkages (build last)  |

**Historical:** the Rulebook Radar epic (**#5**, stories #6–#11) and the
Reconciliation Workbench re-platform are retired. Their issues stay on GitHub
for history; their specs live under `docs/specs/rulebook-radar/` and
`docs/specs/reconciliation-workbench/` and are not being worked.

**How the tracking stays current automatically:**

- Put `Closes #6` (or `Fixes #6`) in a PR description. Merging the PR **closes the
  issue**, **ticks the epic checklist**, and the board's default workflows **move
  the card to Done** — no manual dragging.
- Move a card to **In Progress** when you start it; the board reflects live status.

**Working an issue:**

```bash
gh issue list                 # see open tickets
gh issue view 6               # read a ticket (links to its spec)
git switch -c feat/graph-engine   # branch named for the work
# ... commit, push, then in the PR body: "Closes #6"
```

## Repository areas

| Path               | What it holds                                           |
| ------------------ | ------------------------------------------------------- |
| `docs/discovery/`  | Discovery brief (opportunity solution tree, experiment) |
| `docs/poc/`        | Clickable HTML prototype                                |
| `docs/specs/`      | Product requirements (epic + story specs)               |
| `docs/references/` | **Git-ignored** — internal BNM material, local only     |
