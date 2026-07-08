---
name: mypy-third-party-stub-baseline
description: The 4 mypy third-party stub warnings in engine/ are an accepted baseline, not a regression
type: convention
captured: 2026-07-08
source: /build session (#6 engine, Phase 4 verifier output)
---

New `engine/` modules that import `azure.ai.inference` (or `markitdown`) inherit
accepted mypy stub warnings — mirror `engine/clauses.py`'s import pattern rather
than adding suppressions. The four warnings (`markitdown` import-not-found in
`ingest.py`; `azure.ai.inference` import-untyped in `ingest.py`, `clauses.py`,
`connections.py`) are a permanent baseline. A clean run of `uv run mypy engine/`
still reports exactly these four and nothing else.

**Why:** These packages publish no type stubs and the repo has no mypy config to
silence them, so the warnings cannot be eliminated at the call site. Treating
them as failures leads to chasing an unfixable target or littering the code with
ad-hoc `# type: ignore` comments.

**How to apply:** When verifying any new `engine/` module (or reviewing mypy
output during `/build`), confirm the count is still 4 and the sources are the
known ones — that means clean. Do not add `# type: ignore` for these imports;
follow `clauses.py`'s existing bare-import pattern. Only investigate if a NEW
error appears beyond these four.
