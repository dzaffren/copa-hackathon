---
name: ship-is-gitlab-use-gh
description: The /ship skill is GitLab-oriented; override to `gh pr create --base dzaf/main`, and never add "Closes #<n>" (no issue tracker)
type: skill-quality
captured: 2026-07-08
updated: 2026-07-16
source: /build session (#6 engine, Phase 5 ship); corrected after GitHub Issues was abandoned and dzaf/main became the base
---

The `/ship` skill is written for GitLab (`glab`, merge requests), but this repo is on
GitHub. Override the skill's tool choice: use the `gh` CLI and open a pull request
(not an MR) against **`dzaf/main`**.

**Do NOT put `Closes #<n>` in the PR body.** This repo has no issue tracker — GitHub
Issues was abandoned on 16 Jul 2026 and the rulebook-radar epic (#5) plus its stories
(#6–#11, #26) were closed as superseded. There is nothing for a `Closes` line to close,
and inventing an issue number to satisfy the skill is worse than omitting it.

**Base is `dzaf/main`, not `main`.** Workstream-brain work integrates on `dzaf/main`
(that is where #36 and #37 merged); `main` lags behind and is treated as the release
branch — the Pages demo deploys from it. `--base main` would target a branch that does
not have the current app.

**Why:** Following the skill's `glab`/MR steps verbatim would either fail (no
`glab`, no GitLab remote) or, in the `Closes #<n>` case, add a line referencing issues
that no longer exist. The original version of this learning mandated exactly that —
it was written on 8 Jul when the epic was live, and went stale silently.

**How to apply:** Whenever `/ship` (or the ship phase of `/build`) runs here,
substitute `gh pr create --base dzaf/main` for the skill's `glab mr create` steps, and
omit any issue-closing line. Note `/build` also expects an approved spec and will halt
without one — see [[convention-frontend-app-is-frontend-dir]] for where the code it
builds actually lives.

**Skill:** did-workflow:ship
