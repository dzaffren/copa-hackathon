---
name: engine-artifact-writes-utf8
description: engine artifact writes must pass encoding="utf-8"; the AI DP's Unicode glyphs crash cp1252 on Windows
type: pattern
captured: 2026-07-13
source: /build session (#32 source connection engine, Task 1)
---

Any `Path.write_text(...)` that persists ingested document / markdown text in
`engine/` must pass `encoding="utf-8"` explicitly. The vehicle AI Discussion
Paper's extracted markdown contains non-cp1252 glyphs (e.g. the Unicode minus
U+2212), so a platform-default `write_text` crashes with
`UnicodeEncodeError: 'charmap' codec can't encode character '−'` on Windows
(cp1252).

**Why:** `Path.write_text` uses the platform default encoding when none is given
— cp1252 on Windows — which cannot encode the DP's Unicode characters. JSON
artifacts happen to be safe (`json.dumps` defaults to `ensure_ascii=True`, so the
output is pure ASCII), but any raw-markdown writer — e.g. the ingest debug dump in
`engine/build.py` — writes text verbatim and MUST be UTF-8. Fixed there this
session.

**How to apply:** When adding any `write_text` / `open(...).write` of document or
markdown text in the engine, pass `encoding="utf-8"`. Watch for this specifically
on the vehicle-document build path (`normalise_glyphs` documents) and any new
artifact writer; a JSON writer is only safe while it keeps `ensure_ascii=True`.
