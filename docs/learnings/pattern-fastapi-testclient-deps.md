---
name: fastapi-testclient-deps
description: FastAPI TestClient tests need httpx + python-multipart as explicit deps
type: pattern
captured: 2026-07-08
source: /build session (#6 engine, Task 6 read API)
---

Exercising the FastAPI read service (`engine/api.py`) in tests via
`fastapi.testclient.TestClient` requires `httpx` and `python-multipart` as
explicit dependencies in `pyproject.toml` — they are NOT pulled in transitively
by `fastapi` alone.

**Why:** `TestClient` is built on top of `httpx`, and multipart/form upload
endpoints (e.g. `POST /submissions`) need `python-multipart` to parse the
request body. Neither is a hard dependency of `fastapi`, so a fresh
`uv run pytest` fails with a non-obvious import/runtime error until both are
added.

**How to apply:** When adding or running tests that touch `engine/api.py` (or any
FastAPI app in this repo), ensure `httpx` and `python-multipart` are present in
`pyproject.toml` dependencies. If a test errors on `TestClient` import or on a
multipart upload with a cryptic message, this missing-dep is the first thing to
check.
