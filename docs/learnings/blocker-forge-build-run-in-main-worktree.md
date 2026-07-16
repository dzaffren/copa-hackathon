---
name: forge-build-run-in-main-worktree
description: run forge builds that need pytest/vitest in the main working tree — .venv and node_modules exist only there, not in isolated worktrees
type: blocker
captured: 2026-07-15
source: /build session for spec-workstream-graph (PR #37)
---

Run forge builds that need `pytest`/`vitest` **in the main working tree**, not
an isolated git worktree. This repo's `.venv` (Python) and
`frontend/node_modules` are git-ignored and exist **only** in the main working
tree.

**Why:** forge `feature-builder` subagents run in fresh, isolated git worktrees,
which start without `.venv` and `node_modules`. So `pytest` and `npm run test`
(Vitest) cannot run there, and provisioning them per-worktree is slow and
offline-fragile (a full `uv sync` / `npm ci`, plus the offline-build caveats).
A build that can't run its own tests can't self-verify.

**How to apply:** for any forge build in this repo that must run tests, execute
the sub-tasks directly in the main working tree on the build branch (as the
workstream-graph build did) instead of spawning worktree-isolated
feature-builders — or provision deps inside the worktree first. Verify with
`.venv/Scripts/python.exe -m pytest engine/tests` and, in `frontend/`,
`npm run test`.

**What was tried:** the default forge Phase 3 model (one `feature-builder` per
sub-task in its own worktree) was rejected up front because a fresh worktree has
neither `.venv` nor `node_modules`; the sub-tasks were run sequentially in the
main tree instead, keeping verification on the real suites. This is distinct
from [[forge-verify-hook-false-fail-pyenv-ruff]], which is about the Stop hook's
cosmetic `LINT FAIL`, not worktree isolation.
