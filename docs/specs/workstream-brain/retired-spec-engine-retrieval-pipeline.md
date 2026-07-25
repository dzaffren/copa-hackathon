# Retrieval-first pipeline — axis extraction + hybrid retrieval before finder/critic

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)
**Ticket:** TBD
**Type:** Technical — Engine
**Parent:** [spec.md](spec.md)
**Execution:** SEQUENTIAL — depends on [spec-engine-taxonomy.md](spec-engine-taxonomy.md) (five-label taxonomy) and [spec-engine-anchor-segmentation.md](spec-engine-anchor-segmentation.md) (`AnchorIndex` shape).

## Motivation

Today the finder/critic loop is handed two whole documents' worth of anchor text and asked to both (i) find candidate pairs and (ii) label them. On the BNM cluster this works because the documents are short and internally consistent. On the widened cross-jurisdiction corpus (BNM × UK BoE × HKMA × SG MAS × BCBS mother-docs) it will not: the finder has to hold hundreds of anchors in its head at once, and pairs that speak to the same axis but use disjoint terminology (Malaysia's "conforming loans" vs England's "Level C loans") are exactly the pairs it will miss.

The fix is to invert the flow. Instead of "read both docs, propose pairs," we ask each anchor "what is this anchor _about_?" — extracting short **axis phrases** in canonical regulatory language, not the source's jurisdiction-specific wording. Then deterministic hybrid retrieval (BM25 + cosine over axis embeddings, expanded through a small glossary) proposes candidate anchor pairs _before_ any LLM sees a comparison. The finder/critic loop then judges one pair at a time, which is a much smaller ask.

Two parts of the multi-agent pattern from the Legal Document RAG article on Medium map directly: pre-computed enrichment (their `references` edges, our per-anchor axes) plus a retrieval-driven candidate generation step (their hybrid search, ours). We deliberately do NOT adopt free-form agent conversation — the pipeline stays deterministic-orchestrator + role-specialised LLM stages, which is what regulatory tech needs for auditability.

**Current state:** `engine/connections.py::find_connections` calls `finder_fn(doc_a_text, doc_b_text)` then `critic_fn(finder_output, doc_a_text, doc_b_text)`. Both stages see full-document context. There is no per-anchor enrichment, no retrieval, no glossary. On the retired BNM trace this produces twelve supported linkages; on cross-jurisdiction docs early experiments in the discovery brief suggest recall will drop sharply because "same axis, different words" pairs go unproposed.

**Desired state:** the engine runs a five-stage pipeline before emitting findings:

- **Stage A (LLM):** per-anchor **axis extraction** — one LLM call per anchor produces 1-5 short topic phrases in canonical regulatory language. Cached to `data/artifacts/axes-{document_id}.json` so re-runs are cheap.
- **Stage B (deterministic):** **hybrid retrieval** — for each anchor on side A, retrieve top-K anchors on side B using BM25 over axis text ∪ cosine over axis embeddings ∪ glossary alias expansion. Emits a candidate pair list.
- **Stage C (LLM):** **finder** — same finder function as today, but called _per candidate pair_, not per document. Prompt shrinks from "find pairs" to "label this pair or reject it."
- **Stage D (LLM, stretch):** **coverage-asymmetry prover** — for anchors on side A whose Stage-B retrieval found no B-side match, run a broader search across all of B and emit a verified `silent-on` / `goes-beyond` candidate for the critic. **Deferred as stretch for MVP1** — Stages A+B+C ship first; D lands if time allows before 2026-07-31.
- **Stage E (deterministic):** **citation validator** — unchanged. `AnchorIndex.get(anchor_id)` resolves every citation; unresolved goes to `unsupported`.

**Trigger:** the workstream-brain demo commits to at least one cross-jurisdiction pair analysed end-to-end (SG MAS 637 × UK BoE Chapter 3). Without retrieval-first, the finder cannot reliably propose the "same axis, different terminology" pairs that make the cross-jurisdiction story land on stage.

## Scope

- **In scope:**
  - Stage A: axis extraction module `engine/axes.py`, one LLM call per anchor, cached JSON output.
  - Stage B: hybrid retriever module `engine/retrieval.py` — BM25 (rank-bm25) + cosine over axis embeddings (numpy) + glossary expansion (`data/glossary.json`).
  - Stage C: refactor `find_connections` so the finder/critic is invoked per candidate pair, not per document pair.
  - Curated `data/glossary.json` with ~20 hand-authored cross-jurisdiction alias entries (conforming loan ↔ Level C loan, LCR ↔ liquidity coverage ratio ↔ MAS Notice 649 liquidity requirement, KYC ↔ CDD, etc.).
  - Trace format extension: `axis_extraction`, `retrieval_candidates`, and `coverage_asymmetry_checks` (empty list until Stage D ships) added to `connection-trace-{pair}.json`.
  - Retired-trace replay: the twelve supported linkages must survive under the new pipeline. Since the trace is replayed rather than re-derived, this means the pipeline can accept a "prerecorded candidate pair list" mode that bypasses Stages A+B.
- **Out of scope (deferred stretch):**
  - **Stage D — coverage-asymmetry prover.** MVP1 emits `silent-on`/`goes-beyond` only when the finder/critic _itself_ produces them from Stage-B candidates. The dedicated broad-search verification agent is deferred to a second PR if 2026-07-25 arrives with Stages A+B+C stable.
  - Fine-tuning or retraining any model.
  - Live web retrieval / grounded search on an allowlist — the Rulebook Radar spec includes this as a future direction; the workstream-brain engine stays offline-corpus-only for MVP1.
  - Re-embedding on every rebuild. Axis embeddings are cached; rebuild only re-embeds anchors whose text (or axes) changed.
  - UI changes. Downstream screens keep rendering the `Connection` shape unchanged (the taxonomy + anchor-segmentation stories own citation shape).

## Technical Goals

- Every anchor in `AnchorIndex` has 1-5 extracted axes cached to disk after one build.
- Stage-B retrieval on the SG MAS 637 × UK BoE Chapter 3 pair proposes at least 3× more candidate pairs than raw pairwise prompting would (measured against a hand-labelled 10-pair benchmark).
- The retired BNM taxonomy trace (twelve linkages, `opres × open-finance`) replays end-to-end under the new pipeline in "prerecorded" mode without a live LLM call.
- The pipeline is deterministic given the same axes cache, glossary, and retrieval parameters — same inputs bit-for-bit produce the same candidate set. The demo backstop trace remains replayable.
- One cross-jurisdiction demo pair (SG MAS 637 × UK BoE Chapter 3) produces ≥ 5 supported findings across at least three of the five semantic labels.

## Success Criteria

- `python -m engine.build_axes --document all` writes `data/artifacts/axes-{document_id}.json` for every document in the manifest, one file per document. Each file lists every anchor's `anchor_id` + `axes: list[str]`.
- `python -m engine.find_connections --pair mas-637-2024-07 boe-ch3-sacr` runs the full pipeline (A→B→C→E) and writes `data/artifacts/connection-trace-mas-637-2024-07__boe-ch3-sacr.json` with ≥ 5 supported findings.
- Test suite passes: unit tests for axes.py, retrieval.py, and the refactored `find_connections`.
- Retired-trace replay test: `pytest engine/tests/test_connections.py::test_retired_trace_replay` produces identical output to the pre-refactor version.

## Constraints & Risks

- **Backwards compatibility:** `find_connections` public signature grows one optional parameter (`prerecorded_candidates`); default behaviour when omitted is the new pipeline. Callers that supply the parameter bypass Stages A+B and go straight to per-pair finder/critic — this is the replay path.
- **Downtime:** N/A.
- **Rollback plan:** the pipeline is behind the `find_connections` entry point. If Stage-B retrieval produces poor candidates on cross-jurisdiction pairs during build week, the demo can fall back to the retired BNM trace only (already a supported replay path). Cross-jurisdiction demo pair is scoped as one exhibit, not the entire demo spine.
- **Risks:**
  - _Axis extraction quality on prose docs._ Federal-Register-style prose may produce vague axes ("regulatory requirements", "banking rules") that retrieve too broadly. Mitigation: the axis extraction prompt is explicit about specificity, and there is a max-K + similarity floor at retrieval time. Qualitative review during build.
  - _Glossary coverage._ 20 hand-authored aliases will not cover every jurisdictional mismatch. Mitigation: Stage-B top-K is generous (K=5, floor=0.55) so recall-over-precision at retrieval; the finder/critic rejects false positives cheaply. Glossary is a demo prop, not a scale solution — say so in the pitch.
  - _Cost._ Axis extraction is O(anchors) LLM calls — potentially ~500 calls on the full MVP1 corpus. Mitigation: cache aggressively per document; only re-extract when anchor text or the extraction prompt changes. Budget: ~$5 at Azure OpenAI GPT-4o rates for a full build; acceptable.
  - _Determinism vs. LLM temperature._ Axis extraction with `temperature=0` is stable enough for practical purposes but not bit-identical across runs. Mitigation: cache the _output_, not the invocation. Once axes are extracted and committed, they don't change until the anchor text changes.

## Solution Design

Five stages wired together by a new orchestrator `engine/pipeline.py`. Every LLM stage is an injectable seam so tests stub without network access.

### Stage A — Axis Extraction (`engine/axes.py`)

**Contract:**

```python
def extract_axes(anchor: Anchor, axis_fn: AxisFn = default_axis_fn) -> list[str]: ...
```

**Prompt (system):**

> You are an expert regulatory-policy analyst. Given one clause or passage from a policy document, list 1-5 short "axes" that describe _what topics this passage speaks to_. Each axis is a short noun phrase in canonical regulatory language, deliberately abstracted away from the specific terminology this document happens to use. The goal is that a semantically-equivalent passage in a different jurisdiction, using different terminology, would produce overlapping axes.
>
> Rules:
>
> - Axes must be topics (nouns), never positions (do NOT include "requires X annually" — instead say "scenario testing cadence").
> - Prefer generic regulatory language ("residential mortgage risk-weight tier") over jurisdiction-specific labels ("conforming loan classification").
> - Return a JSON list of strings. No commentary.

**Output cache (`data/artifacts/axes-{document_id}.json`):**

```json
{
  "document_id": "mas-637-2024-07",
  "generated_at": "2026-07-20T14:32:00Z",
  "model": "gpt-4o-2024-08-06",
  "anchors": [
    {
      "anchor_id": "MAS 637 §7.3.15",
      "axes": [
        "residential mortgage risk-weight tier",
        "loan-to-value bucketing",
        "prime mortgage regulatory classification"
      ]
    }
  ]
}
```

Re-extraction triggers only when the anchor's `text` field changes (compare SHA256 of `text` against the cache entry's `text_hash`).

### Stage B — Hybrid Retrieval (`engine/retrieval.py`)

**Contract:**

```python
def retrieve_candidates(
    doc_a_axes: dict[str, list[str]],   # anchor_id -> axes
    doc_b_axes: dict[str, list[str]],
    glossary: Glossary,
    top_k: int = 5,
    similarity_floor: float = 0.55,
) -> list[CandidatePair]: ...
```

**Where `CandidatePair` is:**

```python
class CandidatePair(TypedDict):
    source_anchor_id: str
    target_anchor_id: str
    matched_axis_source: str
    matched_axis_target: str
    similarity: float           # cosine
    bm25_rank: Optional[int]    # None if only vector search retrieved it
    glossary_expansion: Optional[str]  # the alias that surfaced this pair, if any
```

**Algorithm (no LLM):**

1. For each axis on side A, look up glossary aliases. Union: `expanded_queries = {axis} ∪ glossary[axis]`.
2. BM25 rank every side-B axis against `expanded_queries` (tokenised via simple whitespace + lowercase).
3. Cosine-similarity every side-B axis against `expanded_queries` using embeddings computed from OpenAI `text-embedding-3-small` (cached alongside axes JSON).
4. Reciprocal-rank fusion: combine BM25 rank + cosine rank into a single score. Take top-K per source axis with score ≥ floor.
5. Deduplicate to anchor pairs — many axes on the same source anchor can retrieve the same target anchor; emit one `CandidatePair` per unique (source_anchor, target_anchor) with the best (axis, similarity) recorded.

**Determinism:** given the same axes JSON, glossary, and floor, the output is bit-identical.

### Stage C — Finder/Critic Per Pair (`engine/connections.py` refactor)

The current `find_connections(document_a_text, document_b_text, ...)` becomes:

```python
def find_connections(
    document_a_id: str,
    document_b_id: str,
    anchor_index: AnchorIndex,
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    glossary: Glossary,
    finder_fn: FinderFn = default_finder_fn,
    critic_fn: CriticFn = default_critic_fn,
    axis_fn: AxisFn = default_axis_fn,
    prerecorded_candidates: Optional[list[CandidatePair]] = None,
    trace_path: Optional[Path] = None,
) -> FindConnectionsResult:
    candidates = prerecorded_candidates or retrieve_candidates(axes_a, axes_b, glossary)
    supported, unsupported = [], []
    for pair in candidates:
        candidate = finder_fn(anchor_index.get(pair.source_anchor_id), anchor_index.get(pair.target_anchor_id), pair.matched_axis_source)
        candidate = critic_fn(candidate, ...)
        record = _validate_candidate(candidate, anchor_index)
        (supported if record["supported"] else unsupported).append(record)
    _write_trace(...)
    return {"connections": supported, "unsupported": unsupported}
```

The finder/critic prompts are updated to take _one pair at a time_ with the matched axis as context. Prompt shrinks from "find pairs" to "label this pair or reject it."

**Prerecorded-candidate mode:** when `prerecorded_candidates` is supplied, Stages A+B are bypassed. This is how the retired BNM trace replays: the trace file contains a list of the twelve pairs it originally produced, and the pipeline re-runs finder/critic against them under the new taxonomy. The taxonomy backfill script from [spec-engine-taxonomy.md](spec-engine-taxonomy.md) produces this shape.

### Stage D — Coverage-Asymmetry Prover (deferred stretch, out of MVP1 scope)

Design captured here for the follow-up PR. Not implemented in MVP1.

For each anchor on side A whose Stage-B retrieval produced zero candidates above the floor: run a broader retrieval across _all_ of side B (K=20, floor=0.35), and pass the top hits to a dedicated `coverage_fn(anchor_a, top_hits_b)` LLM stage that verifies "is A really silent on this topic that B addresses?" If verified, emit as a `silent-on` (or `goes-beyond` when flipped) candidate. If not, drop.

Scoped to a second PR because: (i) it's the highest-effort/lowest-demo-value piece — most `silent-on`/`goes-beyond` will emerge from Stage-C already; (ii) it needs its own prompt, its own tests, and its own trace-format extension; (iii) 2026-08-03 deadline argues for shipping A+B+C stable rather than A+B+C+D fragile.

### Stage E — Citation Validator (unchanged)

`_validate_candidate` still resolves every `anchor_id` in the candidate against `AnchorIndex`. Verbatim text still comes from the index. This is the same anti-hallucination guardrail as before.

### Changes

- `engine/axes.py` — NEW. `extract_axes`, `AxisFn` seam, `build_axes_for_document`, cache read/write. ~200 LOC.
- `engine/retrieval.py` — NEW. `retrieve_candidates`, `Glossary`, BM25 + cosine + RRF fusion. ~250 LOC.
- `engine/pipeline.py` — NEW. Orchestrator: reads manifest, dispatches segmentation → axis extraction → retrieval → find_connections per pair. ~150 LOC.
- `engine/connections.py` — refactor `find_connections` to take axes + glossary or prerecorded candidates. Update finder/critic prompts to per-pair shape. Keep the `label` + `sentiment` + verbatim-citation invariants from the taxonomy spec.
- `data/glossary.json` — NEW. Hand-authored, ~20 entries.
- `data/artifacts/axes-{document_id}.json` — NEW, one per document.
- `data/artifacts/axis-embeddings-{document_id}.npz` — NEW, one per document. Numpy compressed archive keyed by `anchor_id`.
- `data/artifacts/connection-trace-mas-637-2024-07__boe-ch3-sacr.json` — NEW, the cross-jurisdiction demo trace.
- `engine/build.py` — extended: `python -m engine.build --with-axes` runs Stage A after segmentation.
- `engine/tests/test_axes.py` — NEW.
- `engine/tests/test_retrieval.py` — NEW.
- `engine/tests/test_pipeline.py` — NEW.
- `engine/tests/test_connections.py` — update tests for per-pair finder/critic; add prerecorded-candidate replay test.

### Data Model — Trace Extension

The existing `connection-trace-{pair}.json` gains three top-level fields:

```json
{
  "pair": "mas-637-2024-07__boe-ch3-sacr",
  "generated_at": "...",
  "model": "...",
  "axis_extraction": {
    "source_document_id": "mas-637-2024-07",
    "target_document_id": "boe-ch3-sacr",
    "axes_source_path": "data/artifacts/axes-mas-637-2024-07.json",
    "axes_target_path": "data/artifacts/axes-boe-ch3-sacr.json"
  },
  "retrieval_candidates": [
    {
      "source_anchor_id": "MAS 637 §7.3.15",
      "target_anchor_id": "BoE Ch3 §4.2",
      "matched_axis_source": "residential mortgage risk-weight tier",
      "matched_axis_target": "credit risk weighting for residential exposures",
      "similarity": 0.87,
      "bm25_rank": 2,
      "glossary_expansion": null
    }
  ],
  "coverage_asymmetry_checks": [],
  "finder_output": [...],
  "critic_output": [...],
  "validation": [...]
}
```

### Glossary Format (`data/glossary.json`)

```json
{
  "generated_at": "2026-07-20",
  "curated_by": "hackathon-team",
  "entries": [
    {
      "canonical": "residential mortgage risk-weight tier",
      "aliases": [
        "conforming loan classification",
        "Level C loan",
        "prime mortgage tier",
        "eligible residential exposure"
      ],
      "jurisdictions_using_aliases": ["MY", "UK", "US", "SG"],
      "notes": "MY conforming loans map to England's Level C loans on the risk-weight schedule."
    },
    {
      "canonical": "liquidity coverage ratio",
      "aliases": [
        "LCR",
        "MAS Notice 649 liquidity requirement",
        "PRA liquidity buffer"
      ],
      "jurisdictions_using_aliases": ["INTL", "SG", "UK"]
    }
  ]
}
```

Full MVP1 file has ~20 entries. Owner curates during Task 5.

## Architecture Notes

- **New dependencies:** `rank-bm25` (pure-Python BM25 implementation, ~5 KB, MIT-licensed). Numpy is already a transitive dep. OpenAI embeddings use the existing `openai` / `azure-ai-inference` client — no new SDK.
- **Dependencies & integration:** requires `AnchorIndex` from [spec-engine-anchor-segmentation.md](spec-engine-anchor-segmentation.md) and the widened `Connection` schema from [spec-engine-taxonomy.md](spec-engine-taxonomy.md). The retired-trace replay path (introduced by the taxonomy spec's backfill) becomes the prerecorded-candidate mode of the new pipeline — the two designs compose cleanly.
- **Trace-file compatibility:** existing traces without the three new fields load fine (fields are optional at read time). Only newly-generated traces carry them.

## Exemplar Files

- `engine/connections.py:1-869` — the current finder/critic seams and trace writer. The refactor preserves the seam pattern and the injectable `finder_fn`/`critic_fn` contract; only the _granularity_ of invocation (per pair, not per doc) changes.
- The Medium article on Legal Document RAG (multi-agent recursive retrieval) — the enrichment-then-retrieval pattern our Stages A+B implement. Cite in the architecture doc, not in the spec body.
- The n8n graph agents transcript at `docs/interviews/graph-agents-neo4j-n8n-transcript.md` — the axis-as-search-query pattern (extract "what a chunk is about," then hybrid-search).

## Implementation Plan

### Sub-tasks

**Task 1: `engine/axes.py` — axis extraction module.** — _medium_ (100–300 LOC)

- Files: `engine/axes.py`, `engine/tests/test_axes.py`.
- INDEPENDENT (once [spec-engine-anchor-segmentation.md](spec-engine-anchor-segmentation.md) has landed and `Anchor` exists).
- Notes: `AxisFn` type alias with real default calling Azure OpenAI GPT-4o, `temperature=0`. The prompt is the one described in Solution Design. Output validation: raises `LLMResponseError` if the model returns non-JSON, empty list, or > 5 axes. Cache read/write with SHA256 of anchor text as invalidation key. Tests stub the LLM with hand-written axis lists.

**Task 2: `engine/retrieval.py` — hybrid retriever.** — _medium_ (100–300 LOC)

- Files: `engine/retrieval.py`, `engine/tests/test_retrieval.py`.
- SEQUENTIAL — depends on Task 1 (uses `AxisFn` output shape).
- Notes: BM25 via `rank-bm25`, cosine via numpy dot products on unit-normalised vectors, reciprocal-rank fusion. `Glossary` loads from `data/glossary.json` with a `expand(axis) -> set[str]` API. Deterministic given fixed inputs. Tests exercise: pure BM25 hit, pure cosine hit, RRF-only hit (neither ranks alone but combined score passes floor), glossary-only hit (query expansion surfaces a pair that neither raw BM25 nor cosine would).

**Task 3: `engine/pipeline.py` — orchestrator.** — _small_ (< 100 LOC)

- Files: `engine/pipeline.py`.
- SEQUENTIAL — depends on Tasks 1, 2.
- Notes: reads the manifest, walks a list of document pairs to analyse, dispatches segmentation (already done by anchor-segmentation story) → axis extraction (Task 1, cached) → retrieval (Task 2) → `find_connections` (Task 4). CLI entry: `python -m engine.pipeline --pair {doc_a_id} {doc_b_id}`.

**Task 4: Refactor `engine/connections.py::find_connections` to per-pair.** — _medium_ (100–300 LOC)

- Files: `engine/connections.py`, `engine/tests/test_connections.py`.
- SEQUENTIAL — depends on Tasks 1, 2 for input shapes.
- Notes: new signature (see Solution Design). Finder/critic prompts rewritten per-pair (the pair + matched axis go in the prompt; the finder judges/labels or rejects). The `prerecorded_candidates` bypass path preserves the retired-trace replay. Trace writer extended with the three new top-level fields. Test the prerecorded replay path against the retired trace explicitly.

**Task 5: `data/glossary.json` — curated cross-jurisdiction aliases.** — _small_ (< 50 LOC, but slow — needs human judgement)

- Files: `data/glossary.json`.
- INDEPENDENT.
- Notes: ~20 hand-authored entries covering the demo pair's likely terminology mismatches. Prioritise the SG MAS 637 × UK BoE Ch 3 axes: risk weights, LTV buckets, KYC/CDD, LCR/NSFR, capital tiers, credit-risk-mitigation (CRM), securitisation, ECAI mappings. Include the "conforming loan ↔ Level C loan" entry explicitly — it's a story hook.

**Task 6: Extended `engine/build.py` and CLI.** — _small_ (< 100 LOC)

- Files: `engine/build.py`.
- SEQUENTIAL — depends on Tasks 1-4.
- Notes: `python -m engine.build --with-axes` runs anchor segmentation, then Stage A (axis extraction) for every `in_mvp1: true` document, writes per-document axes + embeddings caches. `python -m engine.pipeline --pair A B` runs Stages A(cached)+B+C+E on one pair. Sensible defaults; explicit CLI for the demo runbook.

**Task 7: Cross-jurisdiction demo trace + smoke test.** — _small_ (< 50 LOC)

- Files: `data/artifacts/connection-trace-mas-637-2024-07__boe-ch3-sacr.json`, `engine/tests/test_pipeline.py`.
- SEQUENTIAL — depends on Tasks 1-6.
- Notes: produce the actual demo trace by running the full pipeline once with live LLM calls; commit the resulting JSON so the demo replays deterministically. Add a smoke test that loads it and asserts ≥ 5 supported findings across ≥ 3 semantic labels.

### Negative Constraints

- Do NOT implement Stage D (coverage-asymmetry prover) in MVP1. Design captured; second PR.
- Do NOT change the `AnchorIndex` shape — that's owned by the anchor-segmentation spec.
- Do NOT change the five-label taxonomy or the sentiment rules — owned by the taxonomy spec.
- Do NOT introduce free-form multi-agent conversation (AutoGen/CrewAI-style). Orchestrator stays deterministic; every LLM stage is single-purpose with structured input/output.
- Do NOT skip caching. Axis extraction cost is real; every LLM call must go through the cache-read-first path.
- Do NOT touch `_cite` or the citation-validator's clause-resolution branch. Verbatim guarantee comes from `AnchorIndex`, not the model.
- Do NOT ingest new documents beyond the manifest — the anchor-segmentation story owns corpus scope.

## Test Scenarios

**Test 1: `test_axis_extraction_produces_canonical_language`**

- Setup: hand-crafted anchor text "conforming residential mortgage loans as defined under BNM Policy Document on Housing Credit shall carry a risk weight of 35%..."
- Action: `extract_axes` with a stubbed `axis_fn` returning `["residential mortgage risk-weight tier", "prime mortgage regulatory classification"]`.
- Expected: returns exactly the two axes; cache write includes SHA256 of the source text.

**Test 2: `test_axis_extraction_cache_hit`**

- Setup: axes JSON already exists on disk with matching `text_hash`.
- Action: call `extract_axes` for the same anchor.
- Expected: returns cached axes without invoking `axis_fn`. Assert `axis_fn` call count is zero.

**Test 3: `test_axis_extraction_cache_miss_on_text_change`**

- Setup: axes JSON exists but the anchor's `text` has changed (SHA256 differs).
- Action: call `extract_axes`.
- Expected: `axis_fn` invoked once; cache overwritten with new axes and new hash.

**Test 4: `test_retrieval_pure_bm25_hit`**

- Setup: source anchor with axis `"scenario testing cadence"`; target anchors including one with axis `"scenario testing frequency requirement"` (BM25 overlap on "scenario testing").
- Action: `retrieve_candidates` with vectors zeroed so only BM25 contributes.
- Expected: the overlapping pair returned with `bm25_rank == 1` and `glossary_expansion == None`.

**Test 5: `test_retrieval_pure_cosine_hit`**

- Setup: source axis `"cyber-hygiene expectations"`; target axis `"information-security controls"` — no BM25 overlap but hand-crafted embeddings that are 0.9 cosine-similar.
- Action: `retrieve_candidates` with BM25 disabled.
- Expected: pair returned with `similarity ≥ 0.55`.

**Test 6: `test_retrieval_glossary_expansion_hit`**

- Setup: source axis `"conforming loan classification"`; target axis `"Level C loan"`. Glossary maps them to the same canonical entry. Raw BM25 and cosine both below floor.
- Action: `retrieve_candidates` with glossary loaded.
- Expected: pair returned with `glossary_expansion == "residential mortgage risk-weight tier"`.

**Test 7: `test_retrieval_deterministic`**

- Setup: fixed axes JSON, fixed glossary, fixed floor.
- Action: call `retrieve_candidates` twice.
- Expected: bit-identical output both times (assert JSON dumps are equal).

**Test 8: `test_find_connections_per_pair_invocation`**

- Setup: `retrieve_candidates` returns 3 candidate pairs; stub `finder_fn` to always return a labelled candidate.
- Action: call `find_connections` with the 3 pairs.
- Expected: `finder_fn` invoked exactly 3 times (once per pair); 3 supported findings emitted; trace file contains 3 entries.

**Test 9: `test_find_connections_prerecorded_bypass_stages_ab`**

- Setup: pass `prerecorded_candidates` explicitly.
- Action: call `find_connections`.
- Expected: `retrieve_candidates` never called; finder/critic invoked per prerecorded pair; result shape matches the direct-retrieval path.

**Test 10: `test_retired_bnm_trace_replays_end_to_end`**

- Setup: the retired taxonomy trace, migrated to prerecorded-candidate shape by the taxonomy spec's backfill.
- Action: run `find_connections` in prerecorded mode against it with stubbed finder/critic returning the trace's original labels.
- Expected: all 12 supported linkages survive; 0 unsupported introduced.

**Test 11: `test_cross_jurisdiction_smoke`**

- Setup: load `data/artifacts/connection-trace-mas-637-2024-07__boe-ch3-sacr.json` produced by Task 7.
- Action: assert trace shape.
- Expected: ≥ 5 supported findings; ≥ 3 distinct `label` values represented; every citation resolves in the current `AnchorIndex`.

## Acceptance Criteria

- [ ] `engine/axes.py` extracts and caches per-anchor axes, invalidating on text hash change.
- [ ] `engine/retrieval.py` implements BM25 + cosine + RRF + glossary expansion, deterministic given fixed inputs.
- [ ] `data/glossary.json` contains ≥ 20 entries with cross-jurisdiction aliases, including "residential mortgage risk-weight tier" mapping conforming ↔ Level C.
- [ ] `find_connections` invokes finder/critic per candidate pair, not per document; the prerecorded-candidate mode bypasses Stages A+B.
- [ ] `data/artifacts/connection-trace-mas-637-2024-07__boe-ch3-sacr.json` exists, has ≥ 5 supported findings across ≥ 3 label values.
- [ ] Retired taxonomy trace replays via prerecorded-candidate mode with all 12 linkages preserved.
- [ ] All new tests pass; all existing tests still pass after `find_connections` signature change.
- [ ] `mypy` clean beyond the third-party stub baseline.

## Verification

Backend-only story — no browser or UI testing.

### Backend Tests

Run:

```
.venv/Scripts/python.exe -m pytest engine/tests/ -v
```

- New: `test_axes.py::*` (Tests 1-3), `test_retrieval.py::*` (Tests 4-7), `test_pipeline.py::*` (Tests 8-11).
- Existing: `test_connections.py::*` all pass after per-pair refactor. Specifically `test_direction_flip_swaps_silent_and_goesbeyond` and `test_retired_trace_backfill` continue to pass.

### Manual Verification

- [ ] Open `data/artifacts/axes-mas-637-2024-07.json`. Pick 5 anchors at random. Confirm axes are in canonical regulatory language, not source-specific terminology. If > 1 of 5 look source-specific, tune the extraction prompt and re-run for that document only.
- [ ] Open `data/artifacts/connection-trace-mas-637-2024-07__boe-ch3-sacr.json`. Find one `differs-on` finding. Confirm the paired anchors genuinely speak to the same axis, and that the sentiment (`tighten`/`loosen`/`neutral`) is correct.
- [ ] Confirm the "conforming loan ↔ Level C loan" glossary entry surfaces a supported finding in the cross-jurisdiction trace. If not, the demo hook needs a different exhibit — file a note for the pitch team.

## Open Questions

- [x] ~~Should we implement Stage D (coverage-asymmetry prover) in MVP1?~~ — **Resolved:** no. Stretch for a follow-up PR. `silent-on`/`goes-beyond` still emerge from Stage C on Stage-B candidates in MVP1; the dedicated prover adds recall but is not a demo-blocker.
- [x] ~~Should the pipeline use free-form multi-agent (AutoGen/CrewAI) or fixed orchestration?~~ — **Resolved:** fixed. Regulatory tech needs auditability; agent-negotiation is not compatible with the verbatim-citation guarantee.
- [x] ~~Should glossary expansion apply at extraction time or at retrieval time?~~ — **Resolved:** retrieval time. Extraction time would pollute the axis cache with alias noise; retrieval-time expansion keeps axes clean and lets the glossary evolve without invalidating the cache.
- [ ] Whether to include an LLM-based candidate-shortlisting stage between Stages B and C — **Deferred (non-blocking):** could improve precision by reranking Stage-B candidates before the finder sees them. Not needed if Stage-B top-K + finder rejection produces acceptable precision on the demo pair. Revisit if false-positive rate is > 30% on manual review.
- [ ] Whether to fall back to a smaller embedding model to reduce cost — **Deferred (non-blocking):** `text-embedding-3-small` is the current default; `text-embedding-3-large` was considered but not chosen. Cost is not the bottleneck at MVP1 corpus size.
