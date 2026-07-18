# Learnings Index

Per-repo learnings captured by the `/learn` skill. Each entry points to a
file in this directory. The active ruleset is synced into the repo's
`CLAUDE.md` under `## Learnings`.

- [mypy third-party stub baseline](convention-mypy-third-party-stub-baseline.md) — the 4 mypy stub warnings in engine/ are accepted baseline, not a regression
- [FastAPI TestClient deps](pattern-fastapi-testclient-deps.md) — TestClient tests need httpx + python-multipart as explicit deps
- [/ship is GitLab, use gh](skill-ship-is-gitlab-use-gh.md) — override /ship's glab with gh + "Closes #<n>" on this GitHub repo
- [Frontend is Vite + React under `frontend/`](convention-frontend-vite-react-not-nextjs.md) — workstream-brain uses Vite + React + TS + Tailwind + shadcn; the archived Next.js `web/` is not part of MVP1
- [~~Frontend is Next.js, not static HTML~~](convention-frontend-nextjs-not-static-html.md) — **superseded 18 Jul 2026**; kept for history
- [Offline build needs Document Intelligence](convention-offline-build-needs-docintel.md) — full `python -m engine.build` needs Azure DI for the legacy tech-risk PDFs; the AI DP + refs + verdicts build offline
- [Engine artifact writes must be UTF-8](pattern-engine-artifact-writes-utf8.md) — pass `encoding="utf-8"`; the AI DP's Unicode glyphs crash cp1252 on Windows
- [Forge verify hook false-fails (pyenv/ruff)](blocker-forge-verify-hook-false-fail-pyenv-ruff.md) — cosmetic Stop-hook `LINT FAIL`; verify with venv pytest, don't disable hooks or install ruff
