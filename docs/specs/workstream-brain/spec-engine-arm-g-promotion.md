# Arm G Engine Promotion — Overview

**Ticket:** TBD
**Type:** Technical Epic
**Experiment spec:** [Arm G — Coverage-aware composite finding flow](experiment-arm-g-coverage-flow.md)

Promotes the Arm G finding pipeline from an offline experiment into the live analyze engine, replacing the current single-pass pairwise approach with a smarter two-stage flow that correctly separates "both sides speak to this topic" findings from "only one side covers this" findings. At the same time, routes each processing step to the right-sized model — small and fast for extraction, mid-tier for judgment, large only for the one step that genuinely needs it — so the pipeline runs faster and costs a fraction of what it does today.

## Background & Context

**Current state:**

- The live analyze engine compares documents anchor-by-anchor, handing the same large model every pair — whether the task is extracting a topic phrase, judging whether two short clauses relate, or scanning an entire document to verify that a topic is genuinely absent.
- Every step — axis extraction, per-pair judgment, whole-document coverage reasoning — uses the most powerful (and most expensive) model available, even when the task requires only simple extraction with no reasoning.
- The coverage labels ("silent on" and "goes beyond") are structurally unreliable: they claim a topic is absent from an entire document, but the engine only ever sees two anchors at a time, so it cannot actually verify absence. A topic present in an unrelated part of the document gets reported as a gap.
- The Arm G experiment (validated across three document pairs — Open Finance ED × HKMA, × BIS Working Paper, × RMiT) proved that splitting same-topic and coverage finding derivation into two separate passes, with appropriate model assignment, fixes all three problems.

**Problem:**

- Policy drafters receive coverage findings that look like mislabelled disagreements — "silent on" collapses into "differs on, more permissive" — which wastes review time and erodes trust in the tool.
- Running the most expensive model for every step, including trivial extraction tasks, makes each analysis run slow and costly. The BIS × ED pair took 25 minutes per run.
- There is no way to scale to larger document corpora without reducing cost per call.

## Pipeline — How Arm G Works

The diagram below shows the full flow from raw documents to finished findings. Each box shows what happens; the first bracket shows which model tier handles the step, and the `CODE:` line names the responsible Python file and function. After promotion, the entire pipeline lives in one new module — `engine/arm_g.py` — orchestrated by `run_arm_g(...)`; it reuses `engine/anchors.py` (anchor lookup), `engine/connections.py` (`_validate_candidates`, taxonomy enforcement), and `engine/llm.py` (`call_chat`) without modifying them.

```
  READS FROM                                                WRITES TO
  ──────────                                                ─────────

┌─────────────────────────────────────────────────────────────────────────┐
│  INPUT                                                                  │
│  anchor-index.json  ─────────────────────────────────────────────────► │
│  (one entry per anchor in both documents; verbatim text + anchor ID)    │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1 — AXIS EXTRACTION                            [Small model]     │
│  CODE:  engine/arm_g.py  ·  _extract_axes_for_document()                │
│                                                                         │
│  READS:  anchor-index.json  (anchor text for each document)             │
│                                                                         │
│  For each anchor in both documents:                                     │
│  → Extract 1-N short topic phrases in plain regulatory language.        │
│  → Example: "Open Finance ED 10.5" → ["consent validity period",        │
│    "recurring access limit", "time-bound data access"]                  │
│                                                                         │
│  Re-runs only if anchor text or extraction cap changes.                 │
│  Shared across all subsequent runs on the same documents.               │
│                                                                         │
│  WRITES: axes-{document-id}.json  (one file per document)               │
│          { anchor_id, text_hash, axis_cap, axes: [phrase, …] }          │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
              axes-{doc-a}.json + axes-{doc-b}.json
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2 — SAME-TOPIC RETRIEVAL                       [No model]        │
│  CODE:  engine/arm_g.py  ·  retrieve_cosine_only() [default] /         │
│         retrieve_bm25_only() [fallback if no embeddings endpoint]      │
│                                                                         │
│  READS:  axes-{doc-a}.json, axes-{doc-b}.json                           │
│                                                                         │
│  Scores every A-side phrase against every B-side phrase using           │
│  meaning-based similarity (cosine, default) or keyword matching          │
│  (BM25, automatic fallback when no embeddings endpoint is configured).  │
│  Surfaces pairs scoring above threshold — up to 60 candidates.          │
│  Example: 42 candidate pairs from 127 × 89 anchors.                    │
│  Pure computation — no model call.                                      │
│                                                                         │
│  WRITES: retrieval-candidates.json  (in-memory; written to trace)       │
│          [ { source_anchor_id, target_anchor_id,                        │
│              matched_axis_source, matched_axis_target, score } ]        │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
              retrieval-candidates.json (up to 60 pairs)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 3 — BATCHED SAME-TOPIC FINDER                  [Mid model]       │
│  CODE:  engine/arm_g.py  ·  _finder_same_topic_batched()               │
│                                                                         │
│  READS:  retrieval-candidates.json, anchor-index.json                   │
│                                                                         │
│  Sends 8-10 candidate pairs per call to the mid-tier model.             │
│  For each pair: does anchor A genuinely relate to anchor B?             │
│  If yes → aligns-with / differs-on / conflicts-with + verbatim text.    │
│  If no  → emit nothing.                                                 │
│  60 pairs → ~7 batched calls instead of 60 individual calls.            │
│  Coverage labels forbidden here — handled in Stage 5.                  │
│                                                                         │
│  WRITES: same-topic-findings.json  (in-memory; written to trace)        │
│          [ { summary, label, sentiment?, source_clauses,                │
│              target_clauses, scope_note? } ]                            │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
              same-topic-findings.json
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 4 — SUPPRESSION LIST BUILD                     [No model]        │
│  CODE:  engine/arm_g.py  ·  _build_suppression()                       │
│                                                                         │
│  READS:  retrieval-candidates.json, same-topic-findings.json            │
│                                                                         │
│  Collects every topic matched in Stage 3.                               │
│  Example: "consent management" found as differs-on → added to list.     │
│  The coverage stage will not re-report these as gaps.                   │
│  Pure computation — no model call.                                      │
│                                                                         │
│  WRITES: suppression.json  (in-memory; written to trace)                │
│          { covered_topics: [phrase, …],                                 │
│            covered_pairs:  ["anchor-a × anchor-b", …] }                │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
              suppression.json
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 5 — WHOLE-DOCUMENT COVERAGE FINDER             [Large model]     │
│  CODE:  engine/arm_g.py  ·  _finder_coverage_whole_doc()              │
│                                                                         │
│  READS:  anchor-index.json (ALL anchors of both documents),             │
│          suppression.json                                               │
│                                                                         │
│  Sends the entire content of both documents in one call.                │
│  The model sees every anchor at once — the only way to honestly         │
│  confirm "topic X is absent from document B entirely."                  │
│  Suppression list injected: "do not report these topics as gaps."       │
│  Produces only silent-on and goes-beyond findings.                      │
│  1 call per analysis run regardless of document size.                   │
│                                                                         │
│  WRITES: coverage-findings.json  (in-memory; written to trace)          │
│          [ { summary, label, source_clauses, target_clauses } ]         │
│          — source_clauses OR target_clauses is empty (single-sided)     │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
              coverage-findings.json
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 6 — MERGE, REFORMAT & VALIDATE                 [No model]        │
│  CODE:  engine/arm_g.py  ·  _reformat_citation() + reuse of            │
│         engine/connections.py · _validate_candidates()                 │
│                                                                         │
│  READS:  same-topic-findings.json, coverage-findings.json,              │
│          anchor-index.json  (for verbatim clause text lookup)           │
│                                                                         │
│  Merges both lists. For any cited anchor ID that does not resolve,      │
│  the deterministic reformatter tries reversible fixes (strip trailing   │
│  punctuation; restore the document prefix) and re-checks. If it now     │
│  resolves, the citation is rewritten AND the rewrite is logged. Any     │
│  finding still citing an unknown anchor → moved to unsupported.         │
│  No fuzzy/substring matching. Pure code.                                │
│                                                                         │
│  WRITES: findings.json                                                  │
│          { connections:  [ supported findings, scope_note kept ],       │
│            unsupported: [ flagged findings ] }                          │
│                                                                         │
│          trace.json  (SINGLE audit file — no metadata.json)             │
│          { retrieval_candidates, same_topic_finder_output,              │
│            suppression,                                                  │
│            coverage_finder_output: [ …, single_sided, redundant ],      │
│            validation,                                                   │
│            citation_rewrites: [ {cited_raw, cited_normalized,           │
│                                  transform} ],                          │
│            counts: { supported, unsupported,                            │
│                      same_topic_finding, coverage_finding },            │
│            wall_clock_seconds }                                         │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT                                                                 │
│                                                                         │
│  findings.json   — supported findings (verbatim-cited, labelled,        │
│                    scope_note retained)                                 │
│                    + unsupported findings (flagged, never fabricated)   │
│  trace.json      — every intermediate output + counts + timing +        │
│                    citation rewrites; the one audit file per run        │
│                                                                         │
│  (no metadata.json — counts and timing live inside trace.json)          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Model tier assignment:**

All stages live in the new module `engine/arm_g.py`, orchestrated by `run_arm_g(...)`. Stage 6 additionally reuses `_validate_candidates` from `engine/connections.py`.

| Stage                 | Task                                 | Model tier   | Code (`engine/arm_g.py` unless noted)                                  | Why                                                                                              |
| --------------------- | ------------------------------------ | ------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1 — Axis extraction   | Extract topic noun phrases           | Small / fast | `_extract_axes_for_document()`                                         | Pure extraction — no reasoning, no judgment, no context needed                                   |
| 2 — Retrieval         | Score topic similarity               | No model     | `retrieve_cosine_only()` (default) / `retrieve_bm25_only()` (fallback) | Cosine over axis embeddings when available; BM25 keyword fallback otherwise — both cheap, no LLM |
| 3 — Same-topic finder | Judge whether two anchors relate     | Mid-tier     | `_finder_same_topic_batched()`                                         | Focused binary judgment on short text — mid-tier handles this well                               |
| 4 — Suppression build | Set arithmetic                       | No model     | `_build_suppression()`                                                 | Pure computation                                                                                 |
| 5 — Coverage finder   | Verify absence across whole document | Large        | `_finder_coverage_whole_doc()`                                         | The only step requiring whole-document reasoning — earns its cost                                |
| 6 — Merge + validate  | Reformat + citation lookup           | No model     | `_reformat_citation()` + `connections._validate_candidates()`          | Deterministic code                                                                               |

## Goals

- Reduce the time a policy drafter waits for an analysis result from the current multiple-minutes to under 90 seconds for typical document pairs.
- Reduce the cost per analysis run by at least 80% relative to the current single-model approach, making the tool affordable to run on every draft revision.
- Deliver coverage findings ("silent on" / "goes beyond") that policy drafters can trust — no more coverage labels that are really mislabelled disagreements.
- Leave the existing five-label taxonomy, verbatim-citation guarantee, and unsupported-finding safety flag unchanged.

## Non-Goals

- Changing what findings look like to the drafter — the output shape is identical to today.
- Building a cost dashboard or model-usage reporting interface.
- Changing the frontend or the review workflow.
- Supporting real-time streaming of findings as they arrive.

## Story Index

| Ticket | Story                                      | Spec                                                                     | Type      | Status      | Dependencies |
| ------ | ------------------------------------------ | ------------------------------------------------------------------------ | --------- | ----------- | ------------ |
| TBD    | Three-tier model configuration             | [spec-engine-arm-g-model-config.md](spec-engine-arm-g-model-config.md)   | Technical | Not Started | —            |
| TBD    | Arm G finding pipeline in the engine       | [spec-engine-arm-g-pipeline.md](spec-engine-arm-g-pipeline.md)           | Technical | Not Started | Story 1      |
| TBD    | Wire Arm G pipeline onto the analyze route | [spec-engine-arm-g-analyze-route.md](spec-engine-arm-g-analyze-route.md) | Technical | Not Started | Story 2      |

## Shared Business Rules

- Every finding, whether from the same-topic stage or the coverage stage, must quote the exact clause it relies on, with its clause number. If no clause supports a claim, it is moved to unsupported and the drafter never sees it as a real finding.
- The five-label taxonomy is unchanged: aligns-with, differs-on, conflicts-with, silent-on, goes-beyond. Sentiment (tighten / loosen / neutral) applies only to differs-on.
- Coverage labels (silent-on, goes-beyond) must not duplicate topics already reported by the same-topic stage. The suppression list enforces this.
- The analysis is always triggered by a human action — the system never auto-analyzes. The drafter initiates; the engine responds.
- No finding text is ever invented or paraphrased — all clause text comes verbatim from the document index.

## User Journey Map

This epic has no end-user-visible UI changes. The journey from the drafter's perspective is identical to today — the improvement is entirely in quality and speed under the hood.

1. **Drafter requests analysis** — Aisyah opens a document pair in Workstream Brain and clicks Analyze. _(Story 3: route wiring)_
2. **Engine runs the Arm G pipeline** — Axis extraction (cached if already done), retrieval, batched same-topic finder, suppression build, whole-document coverage finder, merge and validate. _(Story 2: pipeline)_
3. **Findings appear** — Same output shape as today. Same-topic findings and coverage findings combined in one list, all verbatim-cited. Coverage findings now genuinely one-sided — no more mislabelled disagreements. _(Story 2 + 3)_
4. **Drafter reviews** — Unchanged from today. Accepts, dismisses, or flags for follow-up.

## Success Metrics

- Analysis wall-clock time for a typical 89-anchor × 127-anchor pair drops below 90 seconds end-to-end.
- Cost per analysis run drops by at least 80% compared to the current single-model approach, as measured by token spend across the three models per run.
- Zero coverage findings in the output that cite clauses from both sides simultaneously (i.e. all coverage findings are structurally single-sided).
- No regression on same-topic findings — the pitch-critical findings (HKMA mandatoriness divergence, BIS payment-initiation gap) still appear.

## Dependencies

- The axis cache for the documents being analyzed must be populated before the first run. Subsequent runs reuse the cache until anchor text changes.
- Three model deployments must be available in the environment: one small/fast model for extraction, one mid-tier model for per-pair judgment, one large model for whole-document coverage reasoning.
- An embeddings endpoint is preferred (enables cosine retrieval, the validated default). It is **not** a hard dependency — if no endpoint is configured, the pipeline automatically falls back to BM25 keyword retrieval, which needs nothing beyond the axis phrases.
- The existing anchor index must contain entries for both documents in the pair being analyzed.

## Rollout Strategy

Stories must be delivered in order: configuration first, then the pipeline logic, then the route wiring. Each story is independently releasable in the sense that it does not break the existing behavior — the new pipeline is only activated when wired onto the route in Story 3.

## Open Questions

- [x] ~~Should the critic pass be included in Arm G?~~ — **Resolved:** No critic in Arm G. The finder-only design was validated in the experiment and the user confirmed this is the correct choice.
- [x] ~~Which retrieval method — cosine or BM25?~~ — **Resolved:** Cosine is the default (semantic similarity over axis embeddings — the method validated in the experiment). BM25 is retained as an automatic fallback when no embeddings endpoint is configured — it is pure Python, costs nothing, and preserves graceful degradation so analysis can still run without embeddings. The pipeline selects cosine when the endpoint is present, BM25 otherwise.
- [x] ~~Should coverage findings be allowed to cite a context clause from the other side?~~ — **Resolved:** Yes — the covering side must cite a clause; the other side may optionally cite its nearest clause as context, described as not reaching the sub-point.
- [ ] Should the axis cache be stored alongside the anchor index in the artifacts directory, or in a separate cache directory? — **Deferred (non-blocking):** Either works; the pipeline reads from wherever it is configured to look. Decision can be made during Story 1 implementation.
