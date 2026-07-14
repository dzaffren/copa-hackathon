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

## Sibling: `../engine/` data flow

`../engine/` is a different shape of pipeline — clause-level, LLM-in-the-loop,
no entity graph. Recorded here for contrast.

### What it produces

PDFs → **verbatim-cited cross-doc clause linkages**. Two big stages:

1. **Build** (`engine/build.py` → `engine/clauses.py`): PDFs → a `ClauseIndex`.
   Deterministic, no LLM at query time.
2. **Query** (`engine/connections.py`): pick two docs → LLM finder/critic
   proposes candidate linkages → deterministic validator gates every citation
   against the `ClauseIndex` → verbatim quotes attached.

The "no hallucination" guarantee lives in the boundary between those stages.

### Stages, with a worked example (OpRes × Open Finance)

**1 · Ingest** (build time). PDF → raw markdown per doc:

```
S 4.3
In the context of preserving continuity of critical operations,
a financial institution shall ensure...
```

**2 · Segment** (build time, deterministic). `segment_clauses()` scans line
by line with regexes (`_NUMBERED_CLAUSE_RE`, `_SUBITEM_RE`,
`_SECTION_HEADING_RE`), finds every clause boundary, slices the markdown
byte-for-byte between boundaries. Output — one `ClauseEntry` per clause:

```python
{
  "clause_number": "Operational Resilience 4.3",
  "text": "In the context of preserving continuity of critical operations, ...",
  "policy_id": "opres",
  "document_id": "opres-v1-2025-draft",
  "parent": None,
  "children": ["Operational Resilience 4.3(a)", ...],
}
```

`text` is a literal substring of the source markdown — that is what "verbatim
by construction" means. No LLM writes clause text.

**3 · Assemble `ClauseIndex`** (build time). `merge_clause_indexes()` combines
all documents' entries into a single dict keyed by canonical clause number,
persisted under `data/artifacts/`. `clause_index.get("Operational Resilience 4.3")`
returns the entry above; an unknown number returns `None`. This lookup is the
guardrail.

**4 · `find_connections(doc_a, doc_b, clause_index)`** — query time.

_4a · Finder LLM_ (`_finder_turn`). Prompt = both docs' full clause text (from
`clause_index.entries_for_document`) + `FINDER_SYSTEM_PROMPT`. Returns raw
candidate dicts:

```json
[
  {
    "summary": "Both require business continuity plans...",
    "source_clauses": ["Open Finance 7.6(b)"],
    "target_clauses": ["Operational Resilience 4.3"],
    "scope_note": null
  },
  {
    "summary": "Both cover incident escalation to the board.",
    "source_clauses": ["Open Finance 8.2"],
    "target_clauses": ["Operational Resilience 999.99"]
  }
]
```

The LLM is told _"only cite clause numbers from the provided lists"_ but it
can and does slip up.

_4b · Critic LLM_ (`_critic_turn`). Same doc context + finder candidates +
`CRITIC_SYSTEM_PROMPT`. Refutes weak ones, adds `scope_note`, surfaces
missed connections. Same output shape.

_4c · Deterministic validator_ (`_validate_candidates`). For every candidate,
walk each cited clause number and call `clause_index.get(number)`:

- Candidate 1: both cited numbers resolve → **supported**. `_cite()` fetches
  each cited clause's verbatim `text` from the index _by number_ and attaches
  it. The LLM's _summary_ is kept; the _quoted clause text_ is not.
- Candidate 2: `"Operational Resilience 999.99"` returns `None` →
  **unsupported**. Emitted as `{"summary": ..., "message": "No matching
clause found", "supported": false}`. Never promoted to a low-confidence
  connection.

**5 · Trace + return**. Writes
`data/artifacts/connection-trace-{doc_a}__{doc_b}.json` (model id, timestamp,
raw finder + critic outputs, per-citation validation). Returns
`{"connections": [...supported...], "unsupported": [...]}`.

### The guardrail in one sentence

The LLM proposes _"clause A relates to clause B"_; the code then fetches
A's and B's text from a deterministic index by number and stamps them onto
the output — so the connection carries the model's judgement but the
corpus's words.

### Contrast with this POC

|                 | `engine/`                                    | `kg-poc/`                      |
| --------------- | -------------------------------------------- | ------------------------------ |
| Unit            | Clause                                       | Entity mention                 |
| Primary object  | `ClauseIndex` + linkage list                 | NetworkX graph                 |
| LLM role        | Finder + critic at query time                | None (GLiNER + spaCy at build) |
| Output moment   | "OF 7.6(b) ↔ OpRes 4.3, here are the quotes" | "topic:cloud has degree 56"    |
| Verbatim quotes | Yes (by-key fetch from index)                | N/A                            |
