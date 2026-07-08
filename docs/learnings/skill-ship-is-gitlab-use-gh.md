---
name: ship-is-gitlab-use-gh
description: The /ship skill is GitLab-oriented; override to gh + "Closes #<n>" for this GitHub repo
type: skill-quality
captured: 2026-07-08
source: /build session (#6 engine, Phase 5 ship)
---

The `/ship` skill is written for GitLab (`glab`, merge requests), but this repo
is on GitHub. Override the skill's tool choice: use the `gh` CLI, open a pull
request (not an MR) against `main`, and put `Closes #<n>` in the PR body.

**Why:** Merging a PR whose body contains `Closes #<n>` auto-closes the issue,
ticks the epic #5 checklist, and moves the board card to Done. Following the
skill's `glab`/MR steps verbatim would either fail (no `glab`/GitLab remote) or
silently break that GitHub automation. The `gh` + `Closes #<n>` rule is also
stated in the repo's CLAUDE.md.

**How to apply:** Whenever `/ship` (or the ship phase of `/build`) runs in this
repo, substitute `gh pr create --base main` for the skill's `glab mr create`
steps, and always include `Closes #<n>` in the PR body. Do not hand-edit issue
state — let the merge do it.

**Skill:** did-workflow:ship
