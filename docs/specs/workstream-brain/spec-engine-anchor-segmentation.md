# Anchor segmentation — replace regex ClauseIndex with a multi-strategy AnchorIndex

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)
**Ticket:** TBD
**Type:** Technical — Engine
**Parent:** [spec.md](spec.md)
**Execution:** SEQUENTIAL — depends on [spec-engine-taxonomy.md](spec-engine-taxonomy.md) (label taxonomy must land first so this story can carry `label`/`sentiment` through the widened citation shape).

## Motivation

The workstream corpus for the hackathon demo now includes cross-jurisdiction Basel III credit-risk documents (`data/corpus/temp/`) from UK, HK, SG plus BCBS mother-docs from bis.org. The engine's current `ClauseIndex` was built for BNM's clause-numbered PDs (`RMiT 17.1`, `Outsourcing 12.1`) and its anchor-slice parser assumes every document has a consistent "`{n}.{m}` heading + verbatim opening phrase" shape. That assumption breaks on the new corpus: EBA-style article pages, MAS Notice 637 (paragraph-numbered but structured differently), Bank of England chapters (heading-driven prose), HKMA gazetted rules, and BCBS papers (numbered principles + running prose) all violate the regex assumption in different ways.

Without a widened anchor model, the finder→critic loop cannot cite anything on these documents — every candidate becomes `unsupported` with "No matching clause found," which fails the verbatim-citation guarantee downstream screens depend on.

**Current state:** `engine/clauses.py` (`class ClauseIndex`, line 610) is keyed by canonical clause numbers of the form `"{PolicyShortName} {number}"` (e.g. `"RMiT 17.1"`). The parser at `engine/clauses.py:1-609` uses an LLM to find clause _boundaries_ and slices verbatim text between anchors. `POLICY_SHORT_NAMES` (lines 27-58) hard-codes the seven BNM-style document classes it knows about. The `Connection` TypedDict in `engine/connections.py:60-77` cites `source_clauses` / `target_clauses` typed as `list[ClauseCitation]` with a `clause_number` field.

**Desired state:** the engine has an `AnchorIndex` that supersedes `ClauseIndex`, keyed by a stable `anchor_id` string that is always a verbatim substring of the source document's markdown. Three segmentation strategies dispatch by declared `doc_class`. Every citation stored on a `Connection` or `UnsupportedConnection` uses the widened `AnchorCitation` shape (`anchor_id`, `anchor_label`, `text`, `doc_class`). All existing BNM demo artefacts (`data/artifacts/clause-index.json`, all three `connection-trace-*.json` files) round-trip through the new index without content loss. The retired taxonomy trace still replays.

**Trigger:** the workstream-brain epic's cross-jurisdiction demo commits to at least one non-BNM pair analysed end-to-end (SG MAS 637 × UK BoE Chapter 3). Without anchor segmentation, that pair cannot be ingested; without ingestion, the retrieval-pipeline story ([spec-engine-retrieval-pipeline.md](spec-engine-retrieval-pipeline.md)) has no input to run axis extraction over.

## Scope

- **In scope:**
  - Introduce `engine/anchors.py` with `AnchorIndex`, `AnchorCitation`, `Anchor`, and a `SegmenterRegistry` that dispatches by `doc_class`.
  - Implement three segmentation strategies: `structured-rules` (regex, current behaviour preserved), `semi-structured` (markdown-heading walk), `prose` (semantic paragraph chunking anchored by page + nearest heading).
  - Detect `doc_class` at ingest time — declared per corpus entry, not inferred. Config lives alongside the corpus manifest.
  - Ingest UK Bank of England Chapter 3, HKMA CA-G-1 + gazetted rules, SG MAS Notice 637 (latest effective date), and three BCBS papers (CRE, OPE, BCP — see Dependencies) as segmented anchor sets.
  - Widen `Connection` / `UnsupportedConnection` in `engine/connections.py` to cite `source_anchors` / `target_anchors` (renamed from `source_clauses` / `target_clauses`).
  - Preserve every existing BNM clause as a legal `Anchor` under `doc_class: "structured-rules"` — no BNM regression.
  - Preserve the retired taxonomy trace (twelve linkages) end-to-end under the widened schema.
- **Out of scope:**
  - Retrieval, axis extraction, or any change to the finder→critic loop's _logic_. Only the citation shape changes here. Retrieval-first pipeline is [spec-engine-retrieval-pipeline.md](spec-engine-retrieval-pipeline.md).
  - Automated `doc_class` inference. Class is declared in the corpus manifest by whoever adds the document; no LLM detector.
  - Ingesting NZ, EU, US, ID from `data/corpus/temp/`. MVP1 demo is UK + HK + SG + BCBS; the other jurisdictions stay archived until v2.
  - UI changes. Downstream screens still render "cite: `{label}` — `{text}`"; the shape they read from the API just replaces `clause_number` with `anchor_label`.
  - Superseding the `POLICY_SHORT_NAMES` mapping — it becomes one entry per document class rather than the sole source of truth, but existing BNM entries stay put.

## Technical Goals

- Every document in the workstream-brain demo corpus (BNM cluster + UK BoE Ch 3 + HKMA CA-G-1 + HKMA gazetted rules + SG MAS 637 + three BCBS papers) is segmented into `Anchor` records with verbatim `text` fields, retrievable by `anchor_id` in O(1).
- Zero anchor `text` field is produced by an LLM — every `text` is a literal substring of the source markdown, code-verified at build time.
- The retired taxonomy trace (`data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json`) still replays with all twelve linkages resolvable under the widened `source_anchors`/`target_anchors` schema.
- `AnchorIndex.get(anchor_id)` returns an `Anchor` or `None` — the same contract `ClauseIndex.get()` provides today. The citation validator in `_validate_candidates` needs only a symbol-rename change to use it.

## Success Criteria

- `python -m engine.build` on the widened corpus produces `data/artifacts/anchor-index.json` containing ≥ 400 anchors across ≥ 10 documents spanning ≥ 4 jurisdictions (BNM, UK, HK, SG) plus BCBS.
- Every anchor's `text` field verifies as a substring of its source markdown when the build script runs the assertion pass.
- Running the existing pytest suite (`engine/tests/`) shows no regressions once the `source_clauses` → `source_anchors` rename is complete. The retired-trace replay test in `test_connections.py` passes against the widened schema.
- A manual sample of 20 anchors picked at random across all three `doc_class` values reads as a self-contained, meaningful passage (i.e. the segmenter did not chop mid-sentence in a way that destroys meaning). This is the qualitative acceptance step.

## Constraints & Risks

- **Backwards compatibility:** Not preserved at the API contract level (`source_clauses` → `source_anchors` is a breaking rename). BUT no live consumer exists yet — every downstream screen in the workstream-brain epic ships against this new shape. The retired taxonomy trace is migrated by the same backfill script that renamed its label field.
- **Downtime:** N/A — no production system.
- **Rollback plan:** the story lands behind a feature-branch PR; if segmentation quality on the new corpus is unacceptable during build week, revert the PR and demo only the BNM cluster + one cross-jurisdiction _sample_ pair whose anchors were hand-curated. The taxonomy work in the parent spec is independent and stays landed.
- **Risks:**
  - _Segmenter over-chunks prose docs._ The Federal Register / BoE Chapter 3 flowing prose can produce anchors so short they are useless as citations. Mitigation: minimum anchor length threshold (≥ 200 chars) and merge-adjacent rule in the prose segmenter; qualitative sample check before demo.
  - _MAS Notice 637 has multiple effective dates in the corpus._ Only the latest (`effective 1 July 2024 (updated).pdf`) enters MVP1; earlier versions live in the corpus manifest as `archived: true` and are not ingested.
  - _BCBS papers are large (100+ pages) and semi-structured._ Semi-structured strategy will produce hundreds of anchors per paper; the axis-extraction step in the retrieval spec caches per-anchor axes so re-runs are cheap, but first-run cost is real.

## Solution Design

Three moving parts: a new `engine/anchors.py` module, a per-doc-class segmenter dispatch, and a corpus manifest that declares `doc_class` per document.

### Data Model

**`Anchor` (new TypedDict, `engine/anchors.py`):**

| Field           | Type                                                      | Constraints                                                                 | Description                                                                  |
| --------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `anchor_id`     | `str`                                                     | Required; unique within `AnchorIndex`; stable across rebuilds               | Canonical citation key (e.g. `"MAS 637 §7.3.15"`, `"BoE Ch3 §4.2"`)          |
| `anchor_label`  | `str`                                                     | Required; short human-readable label                                        | UI-render label; often equal to `anchor_id`                                  |
| `text`          | `str`                                                     | Required; ≥ 200 chars; **must be a literal substring of `source_markdown`** | Verbatim passage text                                                        |
| `doc_class`     | `Literal["structured-rules", "semi-structured", "prose"]` | Required                                                                    | Which segmenter produced this anchor                                         |
| `document_id`   | `str`                                                     | Required; matches a key in the corpus manifest                              | The document this anchor belongs to                                          |
| `heading_path`  | `list[str]`                                               | Optional; empty for `structured-rules`                                      | Nearest ancestor headings, most-general first (`["Chapter 3", "Section 4"]`) |
| `page_span`     | `Optional[tuple[int, int]]`                               | Optional; present for `prose` and BCBS PDFs                                 | First and last page numbers the anchor spans                                 |
| `parent_anchor` | `Optional[str]`                                           | Optional                                                                    | `anchor_id` of the enclosing structural unit, if any                         |

**`AnchorCitation` (widened `ClauseCitation`):**

| Field          | Type  | Constraints                          | Description                              |
| -------------- | ----- | ------------------------------------ | ---------------------------------------- |
| `anchor_id`    | `str` | Required; resolves in `AnchorIndex`  | Citation key                             |
| `anchor_label` | `str` | Required                             | UI-render label                          |
| `text`         | `str` | Required; fetched from `AnchorIndex` | Verbatim passage text                    |
| `doc_class`    | `str` | Required                             | Segmenter class (for UI badge/filtering) |

**Widened `Connection` (in `engine/connections.py`):**

`source_clauses: list[ClauseCitation]` → `source_anchors: list[AnchorCitation]`.
`target_clauses: list[ClauseCitation]` → `target_anchors: list[AnchorCitation]`.
`label`, `sentiment`, `summary`, `scope_note`, `supported` — unchanged from the taxonomy spec.

### Corpus Manifest

New file `data/corpus/manifest.json` — the single source of truth for what enters the demo:

```json
{
  "documents": [
    {
      "document_id": "opres-v1-2025-draft",
      "title": "Operational Resilience PD v0.3",
      "jurisdiction": "MY",
      "issuer": "BNM",
      "doc_class": "structured-rules",
      "source_path": "data/corpus/bnm/opres-v0.3.pdf",
      "in_mvp1": true
    },
    {
      "document_id": "boe-ch3-sacr",
      "title": "BoE Chapter 3 – Credit risk – standardised approach",
      "jurisdiction": "UK",
      "issuer": "Bank of England",
      "doc_class": "semi-structured",
      "source_path": "data/corpus/temp/UK/Chapter 3 – Credit risk – standardised approach _ Bank of England.pdf",
      "in_mvp1": true
    },
    {
      "document_id": "mas-637-2024-07",
      "title": "MAS Notice 637 (effective 1 July 2024)",
      "jurisdiction": "SG",
      "issuer": "MAS",
      "doc_class": "semi-structured",
      "source_path": "data/corpus/temp/SG/MAS Notice 637 effective 1 July 2024 (updated).pdf",
      "in_mvp1": true
    },
    {
      "document_id": "hkma-ca-g-1",
      "title": "HKMA CA-G-1 Overview of Capital Adequacy Regime",
      "jurisdiction": "HK",
      "issuer": "HKMA",
      "doc_class": "semi-structured",
      "source_path": "data/corpus/temp/HK/HKMA CA-G-1.pdf",
      "in_mvp1": true
    },
    {
      "document_id": "bcbs-cre",
      "title": "BCBS Calculation of RWA for Credit Risk (CRE)",
      "jurisdiction": "INTL",
      "issuer": "BCBS",
      "doc_class": "semi-structured",
      "source_path": "data/corpus/bcbs/cre.pdf",
      "in_mvp1": true
    }
  ]
}
```

Full manifest lists all MVP1 documents (BNM cluster + 3 UK + 2 HK + 1 SG + 3 BCBS). Documents with `in_mvp1: false` are archived and not ingested.

### Segmenter Dispatch

**`engine/anchors.py::segment(document_id, source_markdown, doc_class) -> list[Anchor]`** dispatches by `doc_class`:

- **`structured-rules`** — delegates to existing `engine/clauses.py::_parse_clauses` (the LLM-boundary + code-slice pipeline), wrapping the resulting `Clause` records as `Anchor` records with `heading_path=[]`, `page_span=None`. `anchor_id` uses the canonical `"{PolicyShortName} {number}"` form. This path is a pass-through — no behaviour change on BNM docs.
- **`semi-structured`** — walks the markdown heading tree (`#`, `##`, `###`, numbered list markers like `4.4`, `(a)`, `(i)`) with a deterministic Python parser (no LLM). Emits one `Anchor` per leaf section. `anchor_id` = `"{ShortName} {heading-number-path}"` (e.g. `"MAS 637 §7.3.15"`, `"BoE Ch3 §4.2"`, `"BCBS CRE 20.3"`). `heading_path` records the enclosing headings.
- **`prose`** — semantic paragraph chunker with three rules: (i) split on double-newline paragraph boundaries; (ii) merge adjacent paragraphs under 200 chars into the next; (iii) split when total chunk > 1500 chars at the nearest sentence boundary. Every emitted anchor is tagged with its `heading_path` (nearest heading above) and `page_span` (from Document Intelligence's page metadata when available; otherwise `None`). `anchor_id` = `"{ShortName} p.{page} \"{first-heading-above}\""`.

All three strategies enforce the invariant: **`anchor.text` is a code-verified literal substring of `source_markdown`**. The build script asserts this after segmentation and raises on any violation.

### Changes

- `engine/anchors.py` — NEW. `Anchor`, `AnchorCitation`, `AnchorIndex`, `segment(...)`, `SegmenterRegistry`. Roughly 400 LOC.
- `engine/clauses.py` — `_parse_clauses` and helpers become the implementation of the `structured-rules` strategy. Keep the file; `AnchorIndex` calls into it. `ClauseIndex` becomes a thin alias `ClauseIndex = AnchorIndex` for one commit to make the rename incremental, then deleted.
- `engine/connections.py` — rename `source_clauses` → `source_anchors`, `target_clauses` → `target_anchors` on `Connection` and `UnsupportedConnection`. `ClauseCitation` → `AnchorCitation` alias, then rename. Update `_validate_candidates` to look up `AnchorIndex.get(anchor_id)` instead of `ClauseIndex.get(clause_number)`. Update `_write_trace` to write the new field names. **Do NOT touch the finder/critic prompts' _logic_** — only the JSON field names inside the prompts change.
- `engine/build.py` — read `data/corpus/manifest.json`, dispatch each `in_mvp1: true` document through the segmenter, assemble one `AnchorIndex`, write `data/artifacts/anchor-index.json` (replacing `clause-index.json`).
- `data/corpus/manifest.json` — NEW. Lists all MVP1 documents.
- `data/corpus/bcbs/` — NEW directory. Contains `cre.pdf`, `ope.pdf`, `bcp.pdf` (see Dependencies).
- `data/corpus/temp/UK/`, `data/corpus/temp/HK/`, `data/corpus/temp/SG/` — existing; referenced from the manifest.
- `data/artifacts/anchor-index.json` — NEW. Replaces `data/artifacts/clause-index.json`.
- `data/artifacts/connection-trace-*.json` — the three existing traces are migrated in-place by the backfill script (rename `source_clauses` → `source_anchors`, no other content changes). The retired-trace already carries verbatim citations that are valid BNM anchor_ids under the new scheme.
- `scripts/backfill_anchor_citations.py` — NEW one-off script. Renames citation fields in the three existing traces. No LLM calls; deterministic JSON transform.
- `engine/tests/test_anchors.py` — NEW test module.
- `engine/tests/test_connections.py` — update every `source_clauses`/`target_clauses` reference to the new names. Add a test that a `structured-rules` anchor and a `semi-structured` anchor both survive citation validation.

## Architecture Notes

- **New dependencies:** none. Markdown-heading walking is stdlib regex; the segmenter is pure Python. Azure Document Intelligence is already used by `engine/ingest.py` for reading-order extraction on multi-column PDFs — no new call sites here.
- **Dependencies & integration:** [spec-engine-taxonomy.md](spec-engine-taxonomy.md) must land first (it widens the `Connection` schema with `label` + `sentiment`). This story widens the _citation_ half of the same schema in a coordinated rename. Every downstream story in the epic consumes `AnchorCitation` instead of `ClauseCitation`.
- **Breaking change acknowledgement:** the API response shape for `POST /connections/find` changes field names. The workstream-brain frontend is not yet built against the old shape (per the epic's rollout — engine widening lands first, screens consume the new shape).

## Exemplar Files

- `engine/clauses.py:1-609` — the current parse-then-slice-verbatim pipeline. The `structured-rules` strategy is this code, wrapped. Preserve the `starts_with` anchor + substring-verify invariant across all three strategies.
- `engine/ingest.py:1-163` — how PDFs already become markdown (MarkItDown or Azure DI). No changes here; the segmenter takes markdown as input.
- `data/artifacts/clause-index.json` — existing JSON shape to preserve at the top level; only the entry shape widens.

## Implementation Plan

### Sub-tasks

**Task 1: Corpus manifest + BCBS asset acquisition.** — _small_ (< 100 LOC)

- Files: `data/corpus/manifest.json`, `data/corpus/bcbs/` (three PDFs downloaded from bis.org).
- INDEPENDENT.
- Notes: manifest lists every MVP1 document with `document_id`, `doc_class`, `source_path`, `in_mvp1`. BCBS PDFs are the standardised approach CRE, operational risk OPE, and BCP — direct downloads from bis.org publications. Store the URLs in a sidecar `sources.md` for reproducibility. Do NOT commit PDFs > 50 MB without checking the `.gitignore` policy — BCBS papers are ~2-5 MB each so fine.

**Task 2: `Anchor` + `AnchorCitation` + `AnchorIndex` core module.** — _medium_ (100–300 LOC)

- Files: `engine/anchors.py`.
- INDEPENDENT.
- Notes: define the TypedDicts, `AnchorIndex` class (mirrors `ClauseIndex` API: `get(anchor_id) -> Optional[Anchor]`, `all() -> list[Anchor]`, `by_document(document_id) -> list[Anchor]`). No segmenter logic yet — that's Task 3-5. Include the substring-verification helper that every strategy will call.

**Task 3: `structured-rules` strategy — wrap existing clause parser.** — _small_ (< 100 LOC)

- Files: `engine/anchors.py`, `engine/clauses.py`.
- SEQUENTIAL — depends on Task 2.
- Notes: extract the current `_parse_clauses` + slice pipeline behind a `SegmenterFn` seam. Wrap its `Clause` output as `Anchor` records (`anchor_id = f"{POLICY_SHORT_NAMES[doc]} {number}"`, `heading_path=[]`, `page_span=None`, `doc_class="structured-rules"`). The BNM corpus goes through this path unchanged. Add regression test that all existing BNM clauses round-trip byte-identical.

**Task 4: `semi-structured` strategy — markdown-heading walker.** — _medium_ (100–300 LOC)

- Files: `engine/anchors.py`, `engine/tests/test_anchors.py`.
- SEQUENTIAL — depends on Task 2.
- Notes: deterministic markdown parser. Detect heading levels from `#`, `##`, `###`; also detect numbered-list-as-heading patterns (`4.4 Title`, `(a)`, `(i)`). Emit one anchor per leaf section (a section with no numbered children). `anchor_id` uses the shortname from the manifest plus the numeric path. Test against a hand-curated MAS 637 excerpt (10 anchors), BoE Chapter 3 excerpt (10 anchors), and BCBS CRE 20 excerpt (10 anchors). NO LLM calls in this strategy.

**Task 5: `prose` strategy — semantic paragraph chunker.** — _medium_ (100–300 LOC)

- Files: `engine/anchors.py`, `engine/tests/test_anchors.py`.
- SEQUENTIAL — depends on Task 2.
- Notes: paragraph-boundary split, min-length merge (200 chars), max-length split (1500 chars at sentence boundary using a simple `.!?` regex — not spaCy). Anchor label includes page number when the source markdown carries page markers (Azure DI emits `<!-- page N -->` breadcrumbs). Test against a Federal Register excerpt as a shape check even though US is not in MVP1 — proves the strategy is future-ready.

**Task 6: Widen `Connection` / `UnsupportedConnection` citation fields.** — _medium_ (100–300 LOC)

- Files: `engine/connections.py`, `engine/tests/test_connections.py`.
- SEQUENTIAL — depends on Task 2 (Anchor* types exist).
- Notes: rename `source_clauses` → `source_anchors`, `target_clauses` → `target_anchors`, `ClauseCitation` → `AnchorCitation` throughout. Update `_validate_candidates` to use `AnchorIndex.get(anchor_id)` instead of `ClauseIndex.get(clause_number)`. Update finder/critic prompt string embedded in `connections.py` so the JSON schema they describe uses `source_anchors`/`target_anchors`. Do NOT change the finder/critic logic. Every existing test in `test_connections.py` gets updated field names; behaviour assertions unchanged.

**Task 7: Build pipeline reads manifest and produces `anchor-index.json`.** — _small_ (< 100 LOC)

- Files: `engine/build.py`, `data/artifacts/anchor-index.json`.
- SEQUENTIAL — depends on Tasks 3-6.
- Notes: `python -m engine.build` reads `data/corpus/manifest.json`, dispatches each `in_mvp1: true` entry through `anchors.segment(...)`, unions the results into one `AnchorIndex`, writes it to `data/artifacts/anchor-index.json`. Delete `clause-index.json` in the same commit. Assert that every emitted anchor's `text` is a substring of the source markdown.

**Task 8: Backfill script for existing traces.** — _small_ (< 50 LOC)

- Files: `scripts/backfill_anchor_citations.py`, three existing `connection-trace-*.json` files.
- SEQUENTIAL — depends on Task 6.
- Notes: pure JSON rename pass. Reads each trace, renames `source_clauses` → `source_anchors` etc., writes back. Zero LLM calls. Idempotent (safe to re-run). Assert every anchor_id resolves in the new `anchor-index.json` before writing.

### Negative Constraints

- Do NOT change the finder/critic prompts' _reasoning instructions_ — only the JSON field name they emit. The taxonomy work in [spec-engine-taxonomy.md](spec-engine-taxonomy.md) owns the label/sentiment vocabulary; this story owns citation shape.
- Do NOT introduce automated `doc_class` inference. The manifest is the source of truth. If a document is added later and its class is wrong, the segmenter output will be poor — that's fine, humans fix the manifest.
- Do NOT ingest NZ / EU / US / ID documents from `data/corpus/temp/`. Those directories stay untouched; the manifest simply omits them.
- Do NOT rewrite `engine/ingest.py`. Segmentation operates on markdown that ingest already produces.
- Do NOT change `_cite` — verbatim text still comes from the index, never from the model. This is the same anti-hallucination guardrail the taxonomy spec preserves.

## Test Scenarios

**Test 1: `test_structured_rules_bnm_round_trip`**

- Setup: run the `structured-rules` strategy on the existing BNM OpRes PD markdown.
- Action: build the resulting `AnchorIndex` and look up 5 known clauses by their canonical anchor_id (e.g. `"Operational Resilience 4.4"`).
- Expected: every lookup returns an `Anchor` whose `text` field byte-matches the existing `Clause.text` in `data/artifacts/clause-index.json`.

**Test 2: `test_semi_structured_mas_637_headings`**

- Setup: hand-curated 3-page markdown excerpt from MAS Notice 637 with three heading levels (Section 7, §7.3, §7.3.15).
- Action: run the `semi-structured` strategy.
- Expected: emits anchors keyed `"MAS 637 §7.3.15"` (leaf), with `heading_path == ["Section 7 Credit Risk", "7.3 Standardised Approach"]`. No anchor emitted for the parent §7.3 (only leaves).

**Test 3: `test_semi_structured_bcbs_cre_numbered_paragraphs`**

- Setup: BCBS CRE 20 excerpt with numbered paragraphs (`20.1`, `20.2`, `20.3(a)`, `20.3(b)`).
- Action: run the `semi-structured` strategy.
- Expected: emits four anchors (`"BCBS CRE 20.1"`, `"BCBS CRE 20.2"`, `"BCBS CRE 20.3(a)"`, `"BCBS CRE 20.3(b)"`), each `text` is a substring of the source.

**Test 4: `test_prose_min_length_merge`**

- Setup: prose markdown with three consecutive paragraphs of lengths 80, 60, 900 chars.
- Action: run the `prose` strategy.
- Expected: two anchors emitted; the 80+60-char paragraphs merge with the 900-char follower, producing one anchor of ~1040 chars and… actually, that violates the max-length rule too. Adjust: emits one anchor combining the 80-char + 60-char + first-N-chars of the 900-char paragraph up to a sentence boundary under 1500 chars, and one anchor for the remainder.

**Test 5: `test_prose_max_length_sentence_split`**

- Setup: prose markdown with a single 2400-char paragraph containing four sentences.
- Action: run the `prose` strategy.
- Expected: emits two anchors, split at the sentence boundary nearest the 1500-char mark. Both anchors have `text` that ends with `.`, `!`, or `?`.

**Test 6: `test_anchor_text_is_substring_of_source`**

- Setup: build the full `AnchorIndex` from the manifest.
- Action: for every anchor, assert `anchor.text in load_source_markdown(anchor.document_id)`.
- Expected: 100% pass — zero anchors whose text is not a literal substring. This is the verbatim guarantee.

**Test 7: `test_retired_trace_survives_field_rename`**

- Setup: the retired taxonomy trace after Tasks 6 + 8 have run.
- Action: load it, iterate every finding.
- Expected: each finding has `source_anchors` and `target_anchors` (not `source_clauses`/`target_clauses`); every `anchor_id` resolves in the new `anchor-index.json`; every `text` matches the anchor's current text.

**Test 8: `test_widened_connection_typeddict`**

- Setup: import `Connection` and `AnchorCitation` from `engine.connections`.
- Action: construct a `Connection` literal with `source_anchors=[AnchorCitation(anchor_id="BoE Ch3 §4.2", ...)]`.
- Expected: constructs successfully; `typing.get_type_hints` shows the new field names.

**Test 9: `test_end_to_end_cross_jurisdiction_pair`**

- Setup: full manifest built, `AnchorIndex` in memory.
- Action: stub `finder_fn` to emit one candidate citing `"MAS 637 §7.3.15"` on side A and `"BoE Ch3 §4.2"` on side B; stub `critic_fn` to pass it through; run `find_connections`.
- Expected: one `Connection` emitted, both anchors resolved with verbatim text pulled from the index. Zero unsupported.

## Acceptance Criteria

- [ ] `engine/anchors.py` exists with `Anchor`, `AnchorCitation`, `AnchorIndex`, and a `segment(document_id, source_markdown, doc_class)` dispatcher covering all three strategies.
- [ ] `data/corpus/manifest.json` lists all MVP1 documents (BNM cluster + UK BoE Ch 3 + HKMA CA-G-1 + HKMA gazetted rules + SG MAS 637 latest + BCBS CRE, OPE, BCP) with `doc_class` declared per entry.
- [ ] `data/corpus/bcbs/` contains three BCBS PDFs downloaded from bis.org, with `sources.md` recording the URLs.
- [ ] `python -m engine.build` produces `data/artifacts/anchor-index.json` with ≥ 400 anchors and zero substring-verification failures.
- [ ] `Connection` / `UnsupportedConnection` cite `source_anchors` / `target_anchors`; `_validate_candidates` looks up anchors via `AnchorIndex.get(anchor_id)`.
- [ ] The three existing `connection-trace-*.json` files carry the new field names and resolve against the new index.
- [ ] Every existing test in `engine/tests/test_connections.py` passes after field-name rename.
- [ ] New tests in `engine/tests/test_anchors.py` pass (Tests 1-9 above).
- [ ] `mypy` clean beyond the accepted third-party stub baseline.

## Verification

Backend-only story — no browser or UI testing.

### Backend Tests

Run:

```
.venv/Scripts/python.exe -m pytest engine/tests/ -v
```

- Existing tests pass with field-name rename.
- New tests `test_anchors.py::*` pass.
- `test_connections.py::test_retired_trace_backfill` continues to pass under the widened schema.

### Manual Verification

- [ ] Randomly sample 20 anchors from `anchor-index.json` across all three `doc_class` values. Read each. Confirm it is a self-contained, meaningful passage (not chopped mid-sentence in a way that destroys meaning). If > 2 of 20 fail, tune the segmenter thresholds before demo.
- [ ] Load the retired taxonomy trace and pick one finding at random. Confirm both `source_anchors[0].text` and `target_anchors[0].text` are verbatim in the source markdown files (byte-diff).
- [ ] Confirm the BCBS PDFs at `data/corpus/bcbs/` are the versions cited in `sources.md` (check download dates or SHA256 against the URLs).

## Open Questions

- [x] ~~Should `doc_class` be inferred automatically or declared?~~ — **Resolved:** declared in the manifest. Auto-inference is a v2 concern; wrong class produces poor anchors that a human then fixes.
- [x] ~~Should the retired BNM trace be re-emitted or field-renamed?~~ — **Resolved:** field-renamed by `scripts/backfill_anchor_citations.py`. Re-emitting would require re-running the finder/critic, which the taxonomy spec explicitly forbids.
- [x] ~~Should NZ / EU / US / ID enter MVP1?~~ — **Resolved:** no. MVP1 demo is UK + HK + SG + BCBS. Other jurisdictions stay in `data/corpus/temp/` archived by manifest omission.
- [ ] Which specific BCBS papers ship in MVP1? — **Deferred (non-blocking):** default set is CRE (credit-risk standardised approach), OPE (operational risk), BCP (Core Principles for Effective Banking Supervision). Owner can swap during Task 1 if the demo pair needs a different mother-doc. Recorded in the manifest.
- [ ] Should HKMA gazetted rules (large PDF, ~200 pages) enter MVP1 or stay archived? — **Deferred (non-blocking):** default is IN. If ingestion cost is a problem during build, drop to `in_mvp1: false` in the manifest; the demo still lands with HKMA CA-G-1 as the HK anchor.
