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

## Issue tracking — none

**This repo does not use an issue tracker.** GitHub Issues was abandoned on
16 Jul 2026: the rulebook-radar epic (#5) and its stories (#6–#11, #26) described a
plan that had been superseded twice, and tracking them was costing more than it gave.
They were closed as superseded. There is no Project board and no milestone.

The process is: **a spec under `docs/specs/workstream-brain/`, a branch, a PR.**

- **Don't** open issues, and **don't** put `Closes #<n>` / `Fixes #<n>` in a PR body —
  there is nothing to close. If a tool or skill asks for a ticket id, there isn't one;
  don't invent one to satisfy it.
- Some older specs still carry a `**Ticket:**` field pointing at a closed issue.
  It's vestigial — ignore it.
- Describe the work in the PR body itself. That is the record.

```bash
git switch -c feat/short-kebab    # branch named for the work
# ... commit, push, then open the PR against dzaf/main:
gh pr create --base dzaf/main
```

## Repository areas

| Path               | What it holds                                           |
| ------------------ | ------------------------------------------------------- |
| `docs/discovery/`  | Discovery brief (opportunity solution tree, experiment) |
| `docs/poc/`        | Clickable HTML prototype                                |
| `docs/specs/`      | Product requirements (epic + story specs)               |
| `docs/references/` | **Git-ignored** — internal BNM material, local only     |
