# kg-poc — Knowledge-graph + ontology pipeline POC

Parallel POC to `../engine/`. Ingests BNM policy PDFs and produces a
NetworkX knowledge graph grounded in a MECE-7 ontology.

**Design:** `../docs/superpowers/specs/2026-07-12-kg-ontology-pipeline-poc-design.md`

## Quickstart

```bash
cd kg-poc
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
python -m kg_poc.run --stage=all
open data/graph.html
```

## Stages

1. `ingest.py` — PDF → clean markdown (`data/text/`)
2. `chunk.py` — markdown → sentence chunks (`data/chunks.jsonl`)
3. `extract.py` — chunks → typed spans (`data/spans.jsonl`)
4. `resolve.py` — spans → entities + mentions
5. `graph.py` — entities → NetworkX graph
6. `analyze.py` — graph → `analysis.md` + figures
7. `viz.py` — graph → interactive HTML

Run a single stage: `python -m kg_poc.run --stage=3`.
