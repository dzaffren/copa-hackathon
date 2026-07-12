# Snapshot data (`web/public/data/`)

The Next.js app reads these JSON files at demo time when `NEXT_PUBLIC_API_BASE`
is unset (the default) — so the deployed demo needs no backend. See
`web/lib/data.ts`.

**Provenance / honesty labelling.** These files are the **curated prepared
analysis** the demo uses (per the epic: upload + extraction are real; the source
set and the analysis are prepared). Paragraph _text_ and source _quotes_ are
verbatim; quotes are marked `verified`, `illustrative`, or `pending_extraction`
and the UI renders that marker faithfully.

**Regeneration.** Once the engine story emits real DP artifacts
(`data/artifacts/verdicts.json` + reference nodes), run:

```
python -m scripts.export_poc_snapshot
```

to regenerate `paragraphs.json` + `connections/*.json` from the build artifacts.
Until then, these are hand-authored from the showcase connections specified in
`docs/specs/reconciliation-workbench/`.
