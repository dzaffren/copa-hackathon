# Learnings Index

Per-repo learnings captured by the `/learn` skill. Each entry points to a
file in this directory. The active ruleset is synced into the repo's
`CLAUDE.md` under `## Learnings`.

- [mypy third-party stub baseline](convention-mypy-third-party-stub-baseline.md) — the 4 mypy stub warnings in engine/ are accepted baseline, not a regression
- [FastAPI TestClient deps](pattern-fastapi-testclient-deps.md) — TestClient tests need httpx + python-multipart as explicit deps
- [/ship is GitLab, use gh](skill-ship-is-gitlab-use-gh.md) — override /ship's glab with gh + "Closes #<n>" on this GitHub repo
- [Vitest/Playwright spec collision](convention-vitest-playwright-spec-collision.md) — scope web/ Vitest test.include to src/** so it skips Playwright *.spec.ts
- [React Flow edge-click chip](pattern-react-flow-edge-click-chip.md) — reliable edge E2E clicks via a testid'd midpoint chip, not a wide hit path
- [Editable draft by id](pattern-editable-draft-by-id.md) — identify the editable draft by EDITABLE_DRAFT_ID, not status; two nodes are "In progress"
