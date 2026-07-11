# kg-poc — Knowledge-graph + ontology pipeline POC

Parallel POC to `../engine/`. Ingests BNM policy PDFs and produces a
NetworkX knowledge graph grounded in a MECE-7 ontology.

**Design:** `../docs/superpowers/specs/2026-07-12-kg-ontology-pipeline-poc-design.md`

## Quickstart

```bash
cd kg-poc
uv sync --extra dev
uv run python -m spacy download en_core_web_sm
uv run pytest -v               # full unit suite
uv run python -m pipeline.run --stage=all
open data/graph.html
```

Everything runs via `uv run`, which resolves the project's pinned venv
(`uv.lock`) automatically — no manual `source .venv/bin/activate` needed.

## Stages

1. `ingest.py` — PDF → clean markdown (`data/text/`)
2. `chunk.py` — markdown → sentence chunks (`data/chunks.jsonl`)
3. `extract.py` — chunks → typed spans (`data/spans.jsonl`)
4. `resolve.py` — spans → entities + mentions
5. `graph.py` — entities → NetworkX graph
6. `analyze.py` — graph → `analysis.md` + figures
7. `viz.py` — graph → interactive HTML

Run a single stage: `uv run python -m pipeline.run --stage=3`.
