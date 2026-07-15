# Learnings Index

Per-repo learnings captured by the `/learn` skill. Each entry points to a
file in this directory. The active ruleset is synced into the repo's
`CLAUDE.md` under `## Learnings`.

- [mypy third-party stub baseline](convention-mypy-third-party-stub-baseline.md) — the 4 mypy stub warnings in engine/ are accepted baseline, not a regression
- [FastAPI TestClient deps](pattern-fastapi-testclient-deps.md) — TestClient tests need httpx + python-multipart as explicit deps
- [/ship is GitLab, use gh](skill-ship-is-gitlab-use-gh.md) — override /ship's glab with gh + "Closes #<n>" on this GitHub repo
- [Frontend is Next.js, not static HTML](convention-frontend-nextjs-not-static-html.md) — the demo frontend is a Next.js app under web/; don't flag the build step as a mistake
- [Offline build needs Document Intelligence](convention-offline-build-needs-docintel.md) — full `python -m engine.build` needs Azure DI for the legacy tech-risk PDFs; the AI DP + refs + verdicts build offline
- [Engine artifact writes must be UTF-8](pattern-engine-artifact-writes-utf8.md) — pass `encoding="utf-8"`; the AI DP's Unicode glyphs crash cp1252 on Windows
- [Forge verify hook false-fails (pyenv/ruff)](blocker-forge-verify-hook-false-fail-pyenv-ruff.md) — cosmetic Stop-hook `LINT FAIL`; verify with venv pytest, don't disable hooks or install ruff
- [Workstream-brain opres-v2 conventions](convention-workstream-brain-opres-v2-conventions.md) — build workstream-brain screens to the opres-v2 base (node_type/edge_type, derived analysed, task-as-edge-source), not the stale specs
- [Run forge builds in the main worktree](blocker-forge-build-run-in-main-worktree.md) — .venv + node_modules live only in the main tree; run test-requiring builds there, not in isolated worktrees
