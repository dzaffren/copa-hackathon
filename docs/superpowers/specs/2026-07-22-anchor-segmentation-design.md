# Anchor segmentation — citable verbatim anchors for non-BNM documents

**Date:** 2026-07-22
**Type:** Technical — Engine
**Status:** Design approved; pending spec review → implementation plan

## Problem

The engine's citation substrate is hard-coded to BNM's clause-numbering house
style. `engine/clauses.py::segment_clauses` anchors on dotted-decimal regexes
(`^\d+(?:\.\d+)+`, lettered sub-items, `S`/`G` markers) and disambiguates via a
hard-coded `POLICY_SHORT_NAMES` map. Documents that do not follow BNM's style
cannot be ingested with citable structure.

This was measured, not assumed. Running the current `segment_clauses` over the
**EU AI Act** (real foreign legislation, 590K chars, extracted via Azure
Document Intelligence — the same path that built the committed artifacts):

- Ground truth in the text: **~34 `Article N` headers + ~312 `(N)` paragraphs** (~346 real units).
- `segment_clauses` produced **20 entries, all garbage** — it misread the
  adoption date "12.7.2024" (12 July 2024) as clause `12.7`, sub-item `.2024`,
  and swept the following `(a)…(g)` in as children. **Zero** real units captured;
  20 confidently-wrong ones emitted.

For a product whose entire promise is verbatim-citation integrity, this is the
worst failure mode: not an empty result, but a plausible-looking hallucinated
structure. A finding could cite "EU AI Act 12.7.2024(c)", which is meaningless.

yenmay's branch (`origin/yenmay/main`) wrote a spec
(`docs/specs/workstream-brain/spec-engine-anchor-segmentation.md`) and a partial
implementation (`engine/anchors.py`) for exactly this: an `AnchorIndex` with a
`SegmenterRegistry` dispatching by `doc_class`. But her three regex strategies
were measured on the same EU AI Act text and all under-deliver:

- `structured-rules` → same 20-garbage date-misparse (same regex logic).
- `semi-structured` → 94 entries with mangled labels (`12.7.2024(EU)`, `1951(EU)(EU)(EU)(EU)`), many hollow.
- `prose` → 1,224 verbatim paragraph chunks, but labelled `chunk#0`, `chunk#1`… — text preserved, **structure lost** (not citable).

So her _architecture_ is sound; her _segmenters_ do not understand non-BNM
legislative structure. This spec adopts the architecture and replaces the weak
segmenters.

## Goal

Ingest structurally-diverse documents (BNM + every `data/references/*.pdf`) into
a single `AnchorIndex` where every anchor is:

1. **verbatim** — `anchor.text` is a literal substring of the source markdown;
2. **citable** — `anchor_label` is a real locator (`"Article 12(3)"`, `"Principle 4"`), never `chunk#N` or a misread date;
3. **high-coverage** — captures ≥ a per-document pinned threshold of the document's real structural units.

The finder→critic loop and API are unchanged; they consume the unified
`AnchorIndex` and never know which segmenter produced an anchor.

## Decisions (from brainstorming)

- **Citation fidelity:** citable structure required (`Article 12(3)`), not a
  safe-prose fallback (`chunk#417`). This is why a real segmenter is needed, not
  just yenmay's prose strategy.
- **Target documents:** all reference PDFs in `data/references/` — EU AI Act,
  NIST AI RMF, OECD principles, PDPA, Basel POR, MAS TRM. These span multiple
  structures, so doc-class routing is required (not one segmenter).
- **Relation to yenmay's work:** adopt her architecture (`AnchorIndex`,
  `SegmenterRegistry`, `verify_substring`, `Anchor`/`AnchorCitation`), fix/replace
  the segmenters. Cherry-pick the skeleton onto `dzaf/main`; do **not** merge her
  branch wholesale (it deletes the current frontend and re-adds retired legacy
  files — `verdicts.py`, `read_model.py`, `submissions.py`).
- **Success bar:** coverage + verbatim + citable label, measured per document
  against hand-authored ground truth (formalizing the EU AI Act test above).
- **Approach:** LLM-assisted boundary detection + deterministic verbatim slicing
  (Approach 2), with BNM retaining its deterministic offline fast-path.
- **Scope split:** this spec is **A** of three. **B** (cross-reference edges) and
  **C** (definition layer) are dependent future specs, recorded below, brainstormed
  after A lands.

## Approach — why LLM boundary detection

Three approaches were considered:

1. **Per-class deterministic regex** — one more regex strategy per structure.
   Rejected: the EU AI Act test proved regex mis-parses (date-as-clause), and
   each reference doc (NIST/OECD/Basel/PDPA) has a different structure — endless
   whack-a-mole, brittle at every edge.
2. **LLM boundary detection + deterministic slicing** (chosen) — the model emits
   `{anchor_label, starts_with, parent}`; code locates `starts_with` in the
   source and slices verbatim; `verify_substring` guards it. One mechanism for
   all diverse structures. The model _understands_ "this is Article 12(3)"
   regardless of format, but **never produces citation text** — code slices.
3. **Hybrid (regex-first, LLM fallback)** — collapses in practice to "BNM =
   deterministic, everything else = LLM", which is what the chosen approach does
   via doc-class routing, without a fragile coverage-threshold trigger.

**This is not new machinery.** It is how `engine/clauses.py` originally worked
before the deterministic rewrite: `build_clause_index` + the `starts_with` anchor
contract + verbatim slicing are **still present** in `clauses.py`. This spec
revives and generalizes that path — the label widens from a BNM clause-number to
any doc-class locator. Precedent and test scaffolding already exist.

The nondeterminism cost is bounded: these docs already depend on Azure DI for
_extraction_, so their builds are not purely offline anyway. BNM stays fully
offline/deterministic on the existing `structured-rules` path.

## Architecture

```
                          ┌─ doc_class = "structured-rules" (BNM)
ingest (DI) → markdown ───┤     → deterministic regex segmenter  [offline, no model, no regression]
                          │
                          └─ doc_class ∈ {legislative, framework, prose} (non-BNM)
                                → LLM boundary detect → code slice → verify_substring
                                                                          ↓
                                                      AnchorIndex (unified) → finder→critic loop (unchanged)
```

- **Two lanes, one index.** BNM on the deterministic lane (no model, no
  regression to committed artifacts/traces). Non-BNM on the LLM-boundary lane.
  Both emit the same `Anchor` shape into one `AnchorIndex`.
- **Isolation property:** the finder→critic loop and API depend only on
  `AnchorIndex`'s interface, never on which segmenter produced an anchor. New
  doc-classes are added behind the registry without touching the loop.

### Adopt / keep / build / discard

- **Adopt (from yenmay):** `AnchorIndex`, `Anchor`/`AnchorCitation` TypedDicts,
  `SegmenterRegistry`, `verify_substring`.
- **Keep (from current `clauses.py`):** the `structured-rules` deterministic
  segmenter (BNM), and the LLM-boundary slicing machinery (`build_clause_index`,
  `_find_anchor_positions`, ambiguity/not-found handling, `dropped-clauses.json`).
- **Build new:** the LLM-boundary segmenter as a registry strategy, its prompt,
  and `doc_class` config tagging for the reference PDFs.
- **Discard (from yenmay):** her `semi-structured` and `prose` regex strategies
  (measured to mis-parse). `prose` may survive only as a last-resort safe fallback.

## Components & data model

### `engine/anchors.py` (adopted, one change)

`Anchor.doc_class` Literal widens from `{structured-rules, semi-structured, prose}`
to `{structured-rules, legislative, framework, prose}`. `Anchor` shape otherwise
kept exactly:

```
Anchor = { anchor_id, anchor_label, text, doc_class, document_id,
           heading_path, page_span, parent_anchor }
AnchorCitation = { anchor_id, anchor_label, text, doc_class }
```

`AnchorIndex` keeps its strict contract: O(1) `get()→None` on miss, `all()` /
`by_document()` in insertion order, duplicate `anchor_id` raises at construction.
This is the anti-hallucination gate — the finder can only cite an `anchor_id`
that exists here.

### Segmenter registry & strategies

| doc_class          | strategy                                           | mechanism                                                                           | applies to                             |
| ------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------- |
| `structured-rules` | deterministic regex (current `segment_clauses`)    | offline, no model                                                                   | all BNM PDs                            |
| `legislative`      | LLM boundary + code slice                          | model emits `{anchor_label, starts_with, parent}`; code slices + `verify_substring` | EU AI Act, PDPA                        |
| `framework`        | same LLM-boundary strategy, different prompt hints | model boundary + code slice                                                         | NIST AI RMF, OECD, Basel POR, MAS TRM  |
| `prose`            | last-resort safe fallback (verbatim chunks)        | deterministic                                                                       | anything with no extractable structure |

`legislative` and `framework` share **one** LLM-boundary implementation — they
differ only in prompt guidance on what a "unit" is. One new segmenter, not four.

`prose` is selected only when a document is **explicitly declared** `doc_class:
"prose"` in the manifest — there is no auto-detection or automatic fallback (see
Out of scope). It exists for documents with no extractable locator structure at
all, where verbatim `chunk#N` anchors (honest but non-citable) are preferable to
forcing a locator the document does not have. None of the six target reference
PDFs are expected to need it; it is a declared escape hatch, not a default.

### LLM-boundary segmenter

Reuses the revived slicing machinery from `clauses.py`. Contract per unit the
model returns:

- `anchor_label`: the citable locator (`"Article 12(3)"`, `"Principle 4"`) —
  becomes the UI-facing citation. Prompt instructs the model to copy the locator
  verbatim from the heading (mitigates label-invention).
- `starts_with`: a verbatim content snippet (no label prefix) used to locate the
  boundary in the source markdown.
- `parent`: the parent locator for hierarchy (`"Article 12"` for `"12(3)"`).

Code then locates `starts_with`, slices verbatim text between consecutive
anchors, and `verify_substring` asserts the slice is a literal substring.
Unresolvable boundaries (not-found / ambiguous / empty) are dropped to
`dropped-clauses.json`, never emitted — the existing review surface.

### `doc_class` config

Each `config.DOCUMENTS` entry gains a `"doc_class"` field — **declared, not
inferred** (this is what prevents the date-misparse: a doc routes to the right
strategy by declaration). BNM entries → `structured-rules`; reference PDFs tagged
per the table.

### Migration seam: `ClauseIndex` → `AnchorIndex`

`connections.py` swaps the type (yenmay already did this mechanically; we
cherry-pick it). The `_cite` / `_validate_candidates` guardrail is identical,
keyed by `anchor_id` instead of `clause_number`. BNM artifacts round-trip: a BNM
clause `"RMiT 10.16"` becomes an `Anchor` with `anchor_id="RMiT 10.16"`,
`doc_class="structured-rules"` — same key, so committed traces and PR #47's
citation-integrity tests still resolve.

## Data flow

Build-time (extends `build.py`'s existing per-document loop, which already has a
`segment_fn` seam):

```
for each document in manifest:
    markdown  = ingest_fn(source_path)            # DI extraction (unchanged)
    segmenter = registry.get(doc["doc_class"])    # NEW: dispatch by declared class
    anchors   = segmenter(document_id, markdown)  # regex OR llm-boundary lane
    verify_substring(a, markdown) for a in anchors   # verbatim gate (ALL lanes)
merge → AnchorIndex → write anchor-index.json
```

**Determinism boundary:** the LLM-boundary lane is nondeterministic per build.
To keep the tracked artifact stable and CI offline, **commit `anchor-index.json`**
(as today with `clause-index.json`); rebuilding a non-BNM doc is a deliberate,
reviewed act (diff entry counts before committing — same discipline as the
existing "don't rebuild without DI" blocker). CI never calls the model; it reads
the committed index. BNM rebuilds stay fully offline/deterministic.

Runtime flow is unchanged: `analyze` → finder→critic → validator → findings. A
non-BNM edge now resolves because its document finally has citable anchors. The
`409 NOT_ANALYSABLE` guard still fires for genuinely unbuilt docs.

## Acceptance harness — the measurable bar

New `test_anchor_coverage.py`, one parametrized case per non-BNM doc, each pinning
three assertions against a small hand-authored ground-truth fixture (the doc's
real top-level locators, extractable from its own table of contents — cheap, not
full text):

| Assertion         | Method                                                                                                                           | Example threshold                       |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **Coverage**      | `#anchors_captured / #ground_truth_units ≥ X%`                                                                                   | EU AI Act ≥ 90% of its Articles present |
| **Verbatim**      | every `anchor.text` is a literal substring of source                                                                             | 100%, no budget                         |
| **Citable label** | every `anchor_label` matches the doc's locator regex, and **zero** match a known-garbage pattern (e.g. a date `\d+\.\d+\.\d{4}`) | 100%                                    |

Thresholds are pinned **per document from measured reality** (like `MAX_HOLLOW`),
not aspirational 100% — a doc that measures 88% is pinned at 88% with a note, so
the test records what IS rather than becoming an untunable test that gets deleted.

## Testing strategy (layered)

1. **Unit** — LLM-boundary segmenter with a _stubbed_ model (injected boundary
   list), asserting slicing + `verify_substring` + drop behavior. No network,
   CI-safe (mirrors how `connections.py` stubs the finder).
2. **Acceptance** — `test_anchor_coverage.py` against committed `anchor-index.json`
   plus ground-truth fixtures. Reads artifacts, no model.
3. **Regression** — existing `test_artifact_integrity.py` (incl. PR #47's
   `test_all_committed_traces_still_resolve`) + `test_taxonomy_traces.py` stay
   green through the `ClauseIndex→AnchorIndex` rename. BNM anchor_ids == old
   clause_numbers, so committed traces resolve unchanged.
4. **One live end-to-end** (manual/marked, like `run_finder_trace.py`) — actually
   build one non-BNM doc via the model and eyeball, to validate the prompt before
   committing its index.

## Risks & mitigations

| Risk                                                                           | Mitigation                                                                                                                                                                                   |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM emits a `starts_with` not in the source (hallucinated boundary)            | `verify_substring` + `_find_anchor_positions` drop it to `dropped-clauses.json`, never cited. Same machinery that handles BNM's long tail.                                                   |
| LLM invents a plausible-but-wrong `anchor_label` (right pattern, wrong number) | Prompt copies the locator verbatim from the heading; harness catches pattern violations; ground-truth fixtures spot-check. **Accepted residual risk** for semantic-but-pattern-valid errors. |
| Nondeterministic rebuild churns the committed index                            | Commit `anchor-index.json`; rebuild is deliberate + reviewed. CI reads committed, never calls model.                                                                                         |
| Coverage threshold set too high → untunable test that gets deleted             | Pin thresholds per document from measured reality, not aspirational 100%.                                                                                                                    |
| `ClauseIndex→AnchorIndex` migration orphans a BNM trace                        | PR #47's `test_all_committed_traces_still_resolve` is the guard; BNM anchor_ids unchanged.                                                                                                   |

## Out of scope (YAGNI)

- Auto-detection of `doc_class` (it is declared per manifest entry).
- Frontend rendering of non-BNM citations (separate FE work).
- Specs B and C below.

## Future specs (recorded for sequencing; not built here)

- **Spec B — Cross-reference edges.** Extract intra-doc `refer to Article X` /
  footnote links as anchor→anchor edges; feed the finder a clause + its
  referents. _Depends on A_ (needs citable anchors to link). The core reasoning
  uplift from the legal-RAG reference article.
- **Spec C — Definition layer.** Extract per-doc defined terms as anchored
  passages; attach to finder context; surface cross-doc term-divergence as a
  `differs-on` source. _Depends on A._

Each gets its own brainstorm after A lands, designed against a real anchor model.

## Reference

- Legal-RAG multi-graph article (motivating B/C):
  https://medium.com/enterprise-rag/legal-document-rag-multi-graph-multi-agent-recursive-retrieval-through-legal-clauses-c90e073e0052
- yenmay's prior spec: `docs/specs/workstream-brain/spec-engine-anchor-segmentation.md` (on `origin/yenmay/main`)
- Empirical segmentation test: this session (EU AI Act via DI, all four segmenters measured).
