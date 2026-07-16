---
name: engine-deps-live-in-two-places
description: A new engine dependency must be added to BOTH pyproject.toml and the CI workflow's explicit pip list
type: pattern
captured: 2026-07-16
source: /build session (drafting workspace, PR #40 — bleach)
---

Adding a runtime dependency to `engine/` requires editing **two** files:

1. `pyproject.toml` → `dependencies`
2. `.github/workflows/test.yml` → the engine job's `pip install` list

The CI job does **not** install from `pyproject.toml`. It installs an explicit,
hand-maintained package list, because `pip install -e .` does not resolve
cleanly in this repo (the comment in the workflow says so).

**Why:** the failure mode is nastier than a normal missing dep, because it is
invisible locally. The dev venv already has the package — you just installed it
to make your tests pass — so the full suite is green on your machine and stays
green no matter how many times you re-run it. CI is the only place the gap
exists. PR #40 added `bleach` to `pyproject.toml`, ran 197 passing tests
locally, and CI failed collection on _every_ test that imports `engine.api` with
`ModuleNotFoundError: No module named 'bleach'` — including pre-existing suites
that had nothing to do with the change, which makes the diff look far more
broken than it is.

This is the same shape as [FastAPI TestClient deps](pattern-fastapi-testclient-deps.md)
— a dependency that has to be declared somewhere non-obvious — but a different
root cause. That learning is about `fastapi` not pulling `httpx`/`python-multipart`
transitively into `pyproject.toml`. This one is about `pyproject.toml` not
reaching CI at all.

**How to apply:** after `uv pip install <pkg>` for engine work, immediately add
it to both files. To check before pushing, diff the two lists:

```bash
sed -n '/^dependencies = \[/,/^\]/p' pyproject.toml
sed -n '/pip install \\/,/markitdown/p' .github/workflows/test.yml
```

If CI reports `ModuleNotFoundError` on a module that imports fine locally — and
especially if it fails tests your diff never touched — check the workflow list
first. Do not start debugging the tests.
