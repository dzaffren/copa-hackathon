---
name: offline-build-needs-docintel
description: full python -m engine.build needs Azure Document Intelligence for the legacy tech-risk PDFs; the default extractor scrambles them
type: convention
captured: 2026-07-13
source: /build session (#32 source connection engine, Task 2 verification)
---

Running the full `python -m engine.build` OFFLINE (no Azure Document Intelligence
credentials) fails on the legacy technology-risk cluster: the default MarkItDown
extractor scrambles reading order on BNM's multi-column PDFs, so curated-edge
clauses like `BCM 9.17` do not resolve and `graph.build_graph` raises
`GraphBuildError` ("... cites clause 'BCM 9.17' which does not resolve ...").

**Why:** the committed `data/artifacts/*.json` were built WITH Azure Document
Intelligence (`prebuilt-layout`), which reconstructs the column/heading order the
default extractor mangles (see the DOCINTEL notes in `engine/config.py`). Without
DI, those PDFs segment differently and the anchored curated edges dangle. This is
pre-existing and environment-dependent — not a regression from any given change.

**How to apply:** Do NOT read a `GraphBuildError` on a legacy tech-risk clause as
"I broke the build" when running offline. The AI Discussion Paper (`ai-dp-2025`)
plus the AI reference library plus `verdicts.json` DO build fully offline — verify
AI-domain engine work by calling `run_build(...)` into a temp dir with
`documents={"ai-dp-2025": DOCUMENTS["ai-dp-2025"]}`, `curated_edges=[]`,
`reference_documents=REFERENCE_DOCUMENTS`, `connection_fixtures=AI_DP_CONNECTIONS`
— not the whole corpus. Regenerating the FULL committed artifacts needs DI
credentials (`AZURE_DOCINTEL_ENDPOINT` / `AZURE_DOCINTEL_API_KEY`).
