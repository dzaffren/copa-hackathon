# Knowledge-Graph + Ontology Pipeline POC — Design

**Status:** Draft, ready for user review
**Date:** 2026-07-12
**Author:** brainstormed with Claude (superpowers:brainstorming)
**Position:** Parallel POC to the existing `engine/` (Rulebook Radar MVP1). Not a replacement, not a PR against the main epic — a separate data-science exploration to see whether an ontology-driven cross-document knowledge graph produces useful findings from the BNM corpus.

---

## 1. Motivation

The existing `engine/` is a domain-specialist regulatory clause pipeline: verbatim clause segmentation + curated seed edges + a two-agent finder/critic loop that discovers _pairwise_ connections between two documents. It nails the verbatim-citation guarantee and is deliberately narrow.

What it cannot answer today (from the drafter interview + AR2025 Ch1B reading):

- "How do all N documents in the corpus relate as a network?" — the engine is pairwise; whole-corpus topology is not surfaced.
- "Which concepts appear across which documents?" — no entity extraction, no concept nodes.
- "How does BNM's OpRes DP relate to BCBS's OpRes Principles?" — no cross-issuer, no BCBS in the corpus, no `Reference` node type.
- "What is each document primarily about?" — no topic modelling, no tf-idf, no concept extraction.

The POC's goal is **not** to replace the engine. It is to **produce a real network graph over the corpus** using a proper data-science pipeline (chunking → NER → entity resolution → graph assembly → analysis → visualisation), grounded in an explicit ontology, so the team can see whether concept-level KG analysis over BNM policy documents produces defensible findings.

The bar is: **feed the PDFs in `data/corpus/` (plus additions) into a pipeline, get out a graph, look at it, and be able to defend every node and edge with verbatim provenance.**

---

## 2. Scope

### In scope

- Standalone POC directory `kg-poc/` parallel to `engine/`. No shared code with `engine/` except patterns.
- Seven-stage pipeline: ingest → chunk → extract → resolve → graph → analyze → visualise.
- MECE-7 ontology (see §4) authored as a first-class artifact.
- Gazetteer-first + GLiNER long-tail hybrid entity extraction.
- NetworkX property graph with two node types (`Document`, `Entity`) and five edge types (`mentions`, `co-occurs`, `cites`, `about`, `same-as`).
- Deterministic, offline-capable pipeline (except for optional Azure Document Intelligence at ingest time).
- Manual quality gates: precision audit, recall audit, entity-resolution audit, graph sanity, cross-issuer sanity.
- Corpus expansion in three tiers (v1 → v2 → v3), each with quality-gate checkpoints.

### Out of scope

- Replacing or modifying the existing `engine/`.
- Any user-facing app / API / frontend. The deliverable is a graph file + a static HTML viz + a markdown analysis report.
- Multi-user, auth, persistence beyond files.
- Fine-tuning any model (GLiNER used zero-shot; no training data assembled).
- Laws, acts, statutory instruments (dropped from the corpus — structural mismatch with clause-numbered regulatory documents).
- Foreign jurisdictions beyond BCBS (no MAS, APRA, OSFI, PRA, EBA).
- SKOS/OWL ontology (deferred — MECE-7 is flat).
- Real-time / streaming pipeline. Batch only.

---

## 3. Corpus (tiered)

Expansion in three tiers, each a checkpoint gated by the quality audit (§8).

### v1 — 7 BNM documents (already in `data/corpus/`)

- Risk Management in Technology (RMiT) PD — `pd-rmit-nov25.pdf`
- Outsourcing PD — `PD_Outsourcing_20191023.pdf`
- Business Continuity Management PD — `PD-BCM.pdf`
- Operational Resilience Discussion Paper — `dp_operationalresilience_Dec2025.pdf`
- Recovery Planning PD — `pd_Recovery Planning.pdf`
- Management of Customer Information & Permitted Disclosures PD — `MCIPD_PD_2025.pdf`
- Open Finance Exposure Draft — `ED_Open_Finance_2025.pdf`

### v2 — + remaining BNM 2025 documents from AR2025 Ch1B

- Capital Adequacy Framework (IRB Approach for Credit Risk) ED
- Capital Adequacy Framework (Counterparty Credit Risk) ED
- Interest Rate Risk in the Banking Book ED
- Financial Institution's Response to Fraud ED
- Climate Risk Management and Scenario Analysis PD
- Personal Financing PD
- Revised Payment Card Requirements

Same issuer (BNM), tests within-issuer breadth.

### v3 — + selected BCBS mother documents

- BCBS Principles for Operational Resilience (March 2021) — mother doc for BNM's OpRes DP
- BCBS Principles for the Sound Management of Operational Risk (revised 2021)
- Basel III: Finalising post-crisis reforms — d424 (December 2017) — mother doc for BNM's Capital Adequacy EDs; source of the "72.5% output floor"
- BCBS High-level Principles for Business Continuity (2006) — mother doc for BNM's BCM PD
- BCBS Principles on Third-Party Risk Management (2024) — maps to Outsourcing + RMiT
- BCBS Principles for the Effective Management and Supervision of Climate-related Financial Risks (2022) — maps to Climate Risk PD

4–6 BCBS documents deliberately chosen to be mother-doc'd to a BNM document already in the corpus, not exhaustive BCBS coverage.

### Deliberately excluded

- **Laws/Acts** (FSA 2013, CCA 2025, Hire-Purchase Amendment 2026). Statutory drafting differs structurally from PD/ED/DP (Parts → Divisions → Sections → subsections; legal jargon; nested cross-references). Would require a `Definition` class and `section-of` edge — not in v1.
- **Foreign non-BCBS jurisdictions** (MAS, APRA, OSFI, PRA, EBA). Terminology drift is significant; would need per-issuer sub-gazetteers. Deferred.

---

## 4. Ontology — MECE-7

Seven concept classes, mutually exclusive by a decision-cascade test, collectively exhaustive against the corpus.

### Class definitions

| #   | Class            | Defining test                                                                                   | Examples                                                                                                           |
| --- | ---------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| 1   | `RegulatoryBody` | Is this an org that **issues rules**?                                                           | BNM, BCBS (the committee), HKMA, MAS, Shariah Advisory Council (BNM)                                               |
| 2   | `Party`          | Is this an actor that is **regulated by, or facilitates regulation, but does not issue rules**? | board, senior management, CRO, Shariah Committee (at a bank), TPSP, cloud service provider, AKPK, ECAI, PSE        |
| 3   | `Reference`      | Is this a **rule/standard already in force elsewhere** that this doc points to?                 | BCBS d424, Basel III, ISO 27001, FSA 2013                                                                          |
| 4   | `Instrument`     | Is this a **regulatory document** issued by a `RegulatoryBody`?                                 | RMiT PD, Outsourcing PD, OpRes DP, Open Finance ED, Supervisory Letter                                             |
| 5   | `Requirement`    | Is this **something that must be done, produced, or met**?                                      | approval, notification, disclosure, RTO, MTPD, output floor, risk weight, Recovery Plan (the artifact required)    |
| 6   | `Topic`          | Is this a **domain of concern** the doc talks about?                                            | operational risk, cyber risk, credit risk, climate risk, cloud, CCRIS, customer information, e-money, open finance |
| 7   | `Process`        | Is this an **activity or event** — something that happens over time?                            | stress testing, business impact analysis, recovery testing, scenario analysis, disruption, incident, resolution    |

### Decision cascade for class assignment

Applied in order; take the first hit:

1. Does it issue rules? → `RegulatoryBody`
2. Is it an actor (person/committee/organisation)? → `Party`
3. Is it a rule from outside this corpus? → `Reference`
4. Is it a regulatory document? → `Instrument`
5. Is it something that must be done/produced/met? → `Requirement`
6. Is it an activity/event? → `Process`
7. Otherwise (a domain/subject) → `Topic`

### Disambiguation of shared surface forms

- `BCBS` (the org) → `RegulatoryBody`; `BCBS d424` (the doc) → `Reference`.
- `Shariah Committee` (at a bank) → `Party`; `Shariah Advisory Council` (at BNM) → `RegulatoryBody`.
- `recovery` (activity) → `Process`; `Recovery Plan` (required artifact) → `Requirement`; `Recovery Planning` (domain / PD subject) → `Topic`.
- `approval` (as a noun / duty) → `Requirement`; `approving` (activity) → `Process`.

### Attributes on nodes (from tier v3 onward)

- `jurisdiction` — `MY` (BNM) or `INT` (BCBS/BIS)
- `issuer` — `BNM`, `BCBS`, `BIS`

Applied to `Document` nodes and to `RegulatoryBody` / `Reference` / `Instrument` entities. Enables queries like "BNM instruments referencing BCBS d424" without introducing new classes.

### `Reference` as a dual-role node

A BCBS document ingested in v3 surfaces in two roles simultaneously:

- As a `Document` node — the pipeline extracted entities from its own text.
- As `Reference` entities — the target of `mentions` edges from BNM docs that name it ("as per BCBS d424 paragraph 20.5").

The two are linked by a `same-as` edge in Stage 5. This enables cross-issuer traversal: BNM clause → BCBS reference → BCBS document → BCBS clause.

### Ontology deliverable

- `kg-poc/ontology/classes.yaml` — the 7 classes + defining tests + examples.
- `kg-poc/ontology/seeds.yaml` — gazetteer seed terms, each with `class`, `canonical`, `aliases`, optional `left_context_forbidden` / `right_context_forbidden`. Authored by hand, versioned in git.

---

## 5. Repository layout

New POC lives **parallel** to `engine/`. No shared code, no shared config, no PRs against the main rulebook-radar epic.

```
kg-poc/
  README.md
  pyproject.toml                   # own venv, own deps
  ontology/
    classes.yaml                   # the 7 classes + defining tests
    seeds.yaml                     # gazetteer seed terms per class
  pipeline/
    __init__.py
    ingest.py                      # PDF → clean markdown
    chunk.py                       # doc → sentence-level chunks
    extract.py                     # gazetteer + GLiNER → typed spans
    resolve.py                     # entity resolution (canonicalisation)
    graph.py                       # assemble NetworkX graph
    analyze.py                     # centrality, communities, per-doc summaries
    run.py                         # argparse driver: python -m kg_poc.run --stage=all
  notebooks/
    01_explore_corpus.ipynb        # token counts, doc lengths
    02_ontology_coverage.ipynb     # spans per class, per doc
    03_graph_analysis.ipynb        # centrality, communities, viz
  data/                            # git-ignored outputs
    text/                          # cleaned markdown per doc
    chunks.jsonl
    spans.jsonl
    entities.jsonl
    mentions.jsonl
    graph.graphml
    graph.json
    graph.html                     # pyvis interactive viz
    analysis.md
    qa/                            # quality-gate outputs
      precision-audit-{date}.md
      recall-audit-{date}.md
      resolution-audit-{date}.md
  tests/
    test_ingest.py
    test_chunk.py
    test_extract.py
    test_resolve.py
    test_graph.py
```

### Reuse discipline

- **Copy, don't import** `engine/ingest.py`'s MarkItDown + Azure Document Intelligence pattern. It's the one thing that already works and rebuilding it would be wasted effort.
- Nothing else is reused. The engine's clause segmenter, curated-edge model, finder/critic loop, and API are irrelevant to the DS pipeline.

### Deps

- `spacy>=3.7` (sentencizer, PhraseMatcher, tokeniser)
- `gliner>=0.2` (zero-shot NER)
- `networkx>=3` (graph)
- `pyvis>=0.3` (interactive HTML viz)
- `matplotlib`, `pandas`, `jupytext` (notebooks)
- `markitdown` + `azure-ai-documentintelligence` (copied from engine)
- `pyyaml`
- `pytest` (unit tests)

Pin GLiNER checkpoint in `pyproject.toml` for reproducibility.

---

## 6. Pipeline stages

Seven stages, each a module you can run in isolation and inspect its output. Every stage writes an artifact to disk. If stage 3 misbehaves, you fix the gazetteer and rerun stage 3 without touching 1–2 or 4–7.

### Stage 1 — Ingest (`ingest.py`)

- Copy engine's pattern: MarkItDown, route PDFs through Azure Document Intelligence when creds are set (BNM/BCBS PDFs are multi-column and reading-order matters).
- Input: `data/corpus/*.pdf`.
- Output: `data/text/{doc_id}.md`.
- Failure: empty conversion → raise `UnreadableDocumentError`, halt the run.
- Manual gate: spot-check every doc's markdown after Stage 1 before running Stage 2.

### Stage 2 — Chunk (`chunk.py`)

- Sentence-level chunks with paragraph context. Not clause segmentation (that's the engine's job) — GLiNER works best on ~1–3 sentences.
- Use spaCy's sentencizer, no LLM.
- Every chunk carries `{doc_id, chunk_id, char_start, char_end, text}` so spans can be traced back byte-for-byte.
- Warn (don't halt) on any chunk >500 chars — probable segmentation miss.
- Output: `data/chunks.jsonl`.

### Stage 3 — Extract (`extract.py`)

Two-pass hybrid, in order:

1. **Gazetteer pass** — spaCy `PhraseMatcher` over `ontology/seeds.yaml`. Every hit gets its class from the seed entry directly. 100% precision on the ~50–100 authored terms. Deterministic.
2. **GLiNER pass** — zero-shot with the 7 class names as labels, on the chunks _after_ removing gazetteer hits (mask them out so GLiNER doesn't re-find them). Adds long-tail coverage. Runs on CPU in minutes for 7 docs; longer for larger corpora.

Class labels passed to GLiNER are descriptive (`"regulatory requirement or duty"` instead of just `"Requirement"`) to help zero-shot precision; class name in output stays canonical.

Output: `data/spans.jsonl` — one line per span:

```jsonc
{
  "doc_id": "rmit-v1-2020",
  "chunk_id": "rmit-v1-2020:0042",
  "char_start": 12038,
  "char_end": 12043,
  "surface": "board",
  "class": "Party",
  "source": "gazetteer",
  "confidence": 1.0,
}
```

Confidence threshold on GLiNER spans: **0.7** (v1 default; tunable). Spans below threshold dumped to `spans_dropped.jsonl` for human review. Never silently kept.

### Stage 4 — Resolve (`resolve.py`)

Three steps, in order:

1. **Normalise** surface — lowercase, strip articles/plurals ("the boards" → "board"). Deterministic.
2. **Class-gated merge** — spans with the same normalised form _and same class_ collapse to one entity. Same string + different class → separate entities (kills BCBS-the-org vs BCBS-the-doc collision).
3. **Alias handling** — from `seeds.yaml`, declared aliases collapse to the canonical entity.

No fuzzy matching in v1. Known long tail of duplicates (e.g. `board` vs `Board of Directors` if the latter isn't declared as an alias) is a known limitation; captured in the resolution audit's "possible under-merge" queue.

Output:

- `data/entities.jsonl` — `{entity_id, class, canonical_label, aliases[], mention_count, docs_appearing_in[]}`.
- `data/mentions.jsonl` — back-index `{entity_id, doc_id, chunk_id, char_start, char_end}`. Every entity traceable to verbatim spans.

### Stage 5 — Graph (`graph.py`)

NetworkX property graph.

**Node types:**

| Type       | Attributes                                                                                         |
| ---------- | -------------------------------------------------------------------------------------------------- |
| `Document` | doc_id, doc_type (PD/ED/DP/BCBS), title, issued_date, jurisdiction, issuer, char_count             |
| `Entity`   | entity_id, class (one of MECE-7), canonical_label, mention_count, jurisdiction (opt), issuer (opt) |

**Edge types:**

| Type        | Direction                            | Weight                                                                                    |
| ----------- | ------------------------------------ | ----------------------------------------------------------------------------------------- |
| `mentions`  | Document → Entity                    | tf-idf (raw count / idf across corpus)                                                    |
| `co-occurs` | Entity ↔ Entity                      | # of chunks where both appear, PMI-normalised                                             |
| `cites`     | Document → Document                  | # of explicit "refer to..." references, resolved through `Reference` entities             |
| `about`     | Document → Entity (Topic-class only) | top-k tf-idf Topic entities per doc; a derived filtered view of `mentions`                |
| `same-as`   | Reference-entity → Document-node     | when a BCBS doc appears both as ingested `Document` and as `Reference` entity in BNM docs |

**Filters at build time:**

- Drop entities with `mention_count < 2` from the graph (kept in `entities.jsonl`). Threshold configurable.
- PMI normalisation on `co-occurs` edges to dampen runaway hub nodes (`board`, `bank`, `BNM`).

Output: `data/graph.graphml` (portable) + `data/graph.json` (readable).

### Stage 6 — Analyze (`analyze.py`)

Standard graph statistics, no ML:

- Node degree, betweenness centrality, PageRank on Entity nodes.
- Louvain community detection — do entities cluster by topic?
- Per-doc summary — top 10 entities by tf-idf; docs most similar by Jaccard on their Entity sets.
- Cross-issuer summary (v3) — which BNM documents cite the most BCBS references; which BCBS documents are cited by the most BNM instruments.

Output: `data/analysis.md` + `data/figures/*.png`.

### Stage 7 — Visualise (notebook)

`pyvis` interactive HTML — Documents as one shape, Entities coloured by class. Filters for edge type and minimum weight. Static matplotlib figures for `analysis.md`.

### Cross-cutting invariants

- **Verbatim provenance.** Every span carries `(doc_id, chunk_id, char_start, char_end)`. Every entity in `entities.jsonl` links to `mentions.jsonl` which points to `chunks.jsonl` which slices verbatim from `data/text/{doc_id}.md`.
- **Determinism.** Stages 1, 2, 4, 5, 6 fully deterministic. Stage 3 gazetteer deterministic; GLiNER deterministic given a fixed model checkpoint + seed.
- **Loud failure.** Empty conversions halt; unresolvable seed entries halt; missing class attribute on a span halts. No silent corruption.

---

## 7. Data flow & artifact contract

The stages hand off through files, not in-memory objects.

```
data/corpus/*.pdf
      │  Stage 1 (ingest.py)
      ▼
data/text/{doc_id}.md
      │  Stage 2 (chunk.py)
      ▼
data/chunks.jsonl
      │  Stage 3 (extract.py) — reads ontology/seeds.yaml
      ▼
data/spans.jsonl (+ spans_dropped.jsonl)
      │  Stage 4 (resolve.py) — reads ontology/seeds.yaml
      ▼
data/entities.jsonl + data/mentions.jsonl
      │  Stage 5 (graph.py)
      ▼
data/graph.graphml + data/graph.json
      │  Stage 6 (analyze.py) + Stage 7 (notebook)
      ▼
data/analysis.md + data/graph.html + data/figures/*.png
```

### Contracts (one line per record, JSONL)

```jsonc
// chunks.jsonl
{"doc_id": "rmit-v1-2020", "chunk_id": "rmit-v1-2020:0042",
 "char_start": 12034, "char_end": 12211,
 "text": "The board shall ensure ..."}

// spans.jsonl
{"doc_id": "rmit-v1-2020", "chunk_id": "rmit-v1-2020:0042",
 "char_start": 12038, "char_end": 12043, "surface": "board",
 "class": "Party", "source": "gazetteer", "confidence": 1.0}

// entities.jsonl
{"entity_id": "party:board", "class": "Party",
 "canonical_label": "board", "aliases": ["the board", "boards"],
 "mention_count": 187, "docs_appearing_in": ["rmit-v1-2020", "PD-BCM", ...]}

// mentions.jsonl (back-index)
{"entity_id": "party:board", "doc_id": "rmit-v1-2020",
 "chunk_id": "rmit-v1-2020:0042", "char_start": 12038, "char_end": 12043}
```

### Reproducibility

Every artifact filename is stable across runs (no timestamps in names; timestamps inside as metadata). Byte-identical rebuild for Stages 1, 2, 4, 5, 6; seed-identical for Stage 3. `git diff` on the artifacts tells you exactly what a code/seed change did.

### Debuggability

Each stage prints a one-line summary:

```
Stage 3: 7 docs → 41,822 chunks → 8,904 spans (5,213 gazetteer, 3,691 gliner)
         class breakdown: Party=1,208 Requirement=1,847 Topic=2,109 ...
Stage 4: 8,904 spans → 892 entities (median mentions=3, max=187 [party:board])
```

### Orchestration

No Airflow / Prefect. A single `python -m kg_poc.run --stage=all` (or `--stage=3`) driven by argparse. Each stage function takes `(input_paths, output_paths, config)` — no globals — so notebooks can call individual stages too.

### Storage & git

- `kg-poc/data/` is git-ignored.
- In git: code, `ontology/classes.yaml`, `ontology/seeds.yaml`, notebooks (jupytext-paired `.py` for readable diffs), a committed `data/analysis.md` snapshot after a good run so reviewers see results without running the pipeline.

---

## 8. Failure modes & quality gates

### Failure modes per stage

- **Stage 1** — empty conversion → raise, halt. Reading-order scrambled → mitigated by Azure Document Intelligence. No creds → warn, run with default extractor, record which extractor was used.
- **Stage 2** — markdown tables/lists confuse the sentencizer → preprocess list labels. Warn on chunk >500 chars.
- **Stage 3** — gazetteer over-match (`board` in `cardboard`) → whole-token matches only + per-term forbidden-context. Class collision (BCBS org vs doc) → seed-time disambiguation rules. GLiNER low precision → threshold 0.7, dropped spans logged.
- **Stage 4** — over-merge (cloud-Topic vs cloud-Party) → class-gated. Under-merge (board vs Board of Directors) → declared aliases only; long tail accepted as v1 limitation.
- **Stage 5** — sparse entities → drop `mention_count < 2`. Runaway hubs → PMI + viz-filter, not drop.

### Quality gates (all five must pass before shipping the graph)

1. **Precision audit.** 100 gazetteer + 100 GLiNER spans hand-labelled. Target gazetteer ≥98%, GLiNER ≥75%. Output `data/qa/precision-audit-{date}.md`.
2. **Recall audit.** 5 clauses per doc with pre-declared must-catch concepts (RTO, MTPD, output floor, TPSP, material outsourcing, board, ...). Target 100% on the must-catch list.
3. **Entity resolution audit.** 50 sampled entities checked for over/under-merge. Top-20 near-string-match "possible under-merge" queue logged.
4. **Graph sanity (scripted).** Every Document node has ≥1 outgoing `mentions` edge. Every Entity has `mention_count ≥ 2`. Every mention in `docs_appearing_in` backed by a `mentions.jsonl` row. Top-10 highest-degree Entities manually inspected.
5. **Cross-issuer sanity (v3 only).** ≥1 `Reference` entity in a BNM doc `same-as` a `Document` node from BCBS. If zero, extraction missed the point.

Fail rule: any target missed → fix seeds/thresholds → rerun affected stages. Ship the graph only when all 5 pass.

### Determinism check

CI runs the full pipeline on the v1 corpus and diffs artifacts against a committed golden. Byte-identical (Stages 1, 2, 4, 5, 6) or seed-identical (Stage 3). Diff → red build → investigate before merge.

### Deliberately not tested

- The ontology being "right." Curation question, not code — captured by the recall audit's must-catch list.
- GLiNER's underlying model quality (third-party dep with its own benchmarks).
- Hold-out evaluation on a labelled test set. This is a POC on 7–40 docs; the corpus IS the eval set.

---

## 9. Testing

### Layer 1 — Unit tests (`pytest`, CI, no corpus, no network)

- `test_ingest.py` — stub MarkItDown, assert empty raises, assert Azure DocIntel path used when creds set.
- `test_chunk.py` — sentence-splitting on hand-crafted markdown with tables, list labels, mid-sentence newlines. Chunk offsets round-trip.
- `test_extract.py` — gazetteer PhraseMatcher on 10-sentence fixture with known terms + FP traps (`board` in `cardboard`). Span offsets exact. GLiNER stubbed with deterministic fake.
- `test_resolve.py` — synthetic spans covering same-string-same-class merge, same-string-different-class separate, alias merge, normalisation edges.
- `test_graph.py` — 5-entity, 3-doc fixture. Edge counts + weights. `mention_count < 2` filter.

All unit tests <5 seconds total.

### Layer 2 — Corpus quality gates

See §8. Manual + scripted, run after each real pipeline run, results in `data/qa/`.

---

## 10. Path to production (context for demo expectations)

The POC as designed is a **batch, notebook-driven, single-machine pipeline that writes files to disk**. Production is a different discipline — this section sets expectations honestly.

### Four transitions

- **A. Notebook / script (POC lives here).** Files on disk; reproducibility a leap of faith.
- **B. Scheduled batch job.** Cron / Actions / Prefect. Config in git, secrets in a vault. Outputs versioned to object store. Data-validation contracts fail the run loudly.
- **C. Served pipeline (what "the platform" needs).** User event triggers extraction on demand. Split ingestion service (writes to KG store) + query service (reads for UI). KG in Neo4j / Memgraph / triplestore. Async job model. Model serving warm at startup.
- **D. Human-in-the-loop production.** Curator UI feeds corrections back into gazetteer. Precision on human-reviewed spans tracked over time. Ontology governed with change review.

### Productionisation checklist for _this_ pipeline

Roughly in order (rough effort estimates):

1. Move artifacts off local disk to blob storage — 1 day.
2. Version every run `{code_sha, gazetteer_sha, gliner_checkpoint, corpus_sha}` — 1 day.
3. Replace file hand-off with a store (Neo4j for KG; Parquet/DuckDB for spans/mentions) — 3 days.
4. Automate the §8 quality gates as fail-the-run data validation — 2 days.
5. Containerise + pin — 1 day.
6. Orchestrator (Prefect / Actions matrix, one job per doc-type) — 3 days.
7. Read APIs (GraphQL / REST / Cypher-proxy) over the KG — 5 days.
8. Idempotent upsert semantics (stable ids from `(doc_id, canonical_label, class, char_offset)`) — 2 days.
9. Observability (per-stage timing, class counts, precision drift alerts) — 3 days.
10. HITL curator UI — a product, not a sprint. ~4–6 weeks.

Steps 1–5 ≈ 1 sprint. Steps 6–9 ≈ 2–3 sprints. Step 10 is a product in itself.

### What the POC deliberately does _not_ do

- No graph database. NetworkX in-memory is fine at 7–40 docs.
- No orchestrator. `argparse` and files.
- No REST API. Notebooks.
- No auth, no multi-user, no HITL UI.
- No model serving. GLiNER runs in-process.
- No CI running the full pipeline on v2 / v3 corpora. Unit tests only, plus the determinism check on the v1 corpus (see §8).

These are the right shape for a POC that has to prove the _pipeline_ works. Every skipped concern is a clean next-step story.

### Demo modes

**Demo A — "Look at the graph" (5 min, policy/business audience).**

- Open the pyvis HTML.
- Filter to `Document ↔ Topic` edges — "here's what each doc is about."
- Click an Entity — "here are the verbatim mentions across the corpus."
- Click a Document — "top-10 topics + cited references."
- v3 highlight: BNM doc `mentions` a BCBS `Reference` `same-as` a BCBS `Document` — mother-doc traversal in one click.
- Message: "This is the network. Now imagine it queryable from a policy drafter's UI."

**Demo B — "Look at the pipeline" (10 min, technical audience).**

- Seven stages, each input + output side-by-side.
- `spans.jsonl` — verbatim provenance per span.
- `analysis.md` — precision audit results (actual measured numbers).
- Live demo: remove a seed, rerun Stage 3, watch a specific edge disappear. Deterministic and inspectable.
- Message: "Real DS pipeline with auditable outputs, not an LLM demo."

**Demo C — "Road to production" (5 min, platform/PM audience).**

- The 10-step checklist, colour-coded (green = next sprint, amber = medium lift, red = product effort).
- One-liner: "The POC proves extraction + ontology. Productionising is well-understood engineering — no research risk left."

Recommended hackathon combo: **A + C** (~10 min). Skip B unless the audience asks.

### Honest limitations to declare upfront

- 7–40 docs, not the full BNM catalogue.
- Extraction precision measured, not perfect — under-merge / low-recall entities are known.
- No live UI — a graph file + static HTML.
- BCBS math/tables not extracted (prose only).
- Ontology is v1, deliberately not exhaustive — captured by the class-decision-cascade doc.

---

## 11. Open questions

- **GLiNER checkpoint choice.** `urchade/gliner_medium-v2.1` is the current safe default. Larger checkpoints raise precision but slow iteration; revisit after v1 audit.
- **Should `docs/references/` be part of the corpus?** The git-ignored internal folder may hold BCBS PDFs the team already has. Per CLAUDE.md this is confidential — the POC must not commit anything under `docs/references/` or its extracts. Ingest locally only.
- **Confidence threshold tuning.** 0.7 is the v1 default; may need per-class thresholds after audit.
- **Recovery-plan-style artifacts vs Requirement class.** Design says "artifact required" → `Requirement`. Confirm on first-audit sample; a `GovernanceArtifact` class may re-emerge if the audit shows drift.

---

## 12. Change log

- 2026-07-12 — first draft written after brainstorming session (Sections 1–10). Corpus tiers finalised; laws dropped from scope; BCBS mother-docs added at v3.
