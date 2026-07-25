# Arm G Finding Pipeline in the Engine

**Ticket:** TBD
**Type:** Technical — Performance / Architecture

Moves the Arm G composite finding pipeline from the experiment scripts into the production engine module, replacing the current anchor-by-anchor approach with a six-stage flow that correctly separates "both sides speak to this topic" findings from "only one side covers this" findings. This story is the core of the Arm G promotion — it makes the pipeline available as a reusable engine capability that the route-wiring story (Story 3) connects to the analyze endpoint.

## Motivation

**Current state:** The production engine runs every analysis step through a single, uniform approach — axis extraction, per-pair judgment, and whole-document coverage reasoning all use the same heavyweight reasoning step, regardless of whether the task actually needs that level of power. Coverage findings ("silent on" and "goes beyond") are unreliable because the engine can only ever see two passages at a time; it cannot confirm that a topic is truly absent from an entire document when it never looks at the whole document. The result is coverage labels that are often mislabelled disagreements — drafters see a "silent on" that is really a "differs on", and the signal erodes trust.

**Desired state:** The engine has a fully operational six-stage pipeline that: uses a small model for extraction, a mid-tier model for per-pair judgment, and the large model only for the one step that genuinely requires whole-document reasoning. Same-topic findings and coverage findings are derived by separate, purpose-fit passes. The coverage pass sees the entire content of both documents simultaneously, so it can honestly confirm that a topic is absent rather than guessing from a nearby passage. Topics already resolved by the same-topic pass are suppressed from the coverage pass, preventing duplicates. All findings are validated against the anchor index before being returned, ensuring no clause text is ever invented.

**Trigger:** The Arm G experiment validated this pipeline design across three real document pairs (Open Finance ED against HKMA, BIS working paper, and RMiT). The coverage findings it produced were genuinely one-sided and specific, unlike the mislabelled findings the current engine produces. The experiment also demonstrated a large reduction in model cost and wall-clock time. Promotion to the engine is now the next step.

## Scope

- **In scope:**
  - The complete six-stage Arm G pipeline as a new engine capability: axis extraction with per-anchor caching, same-topic retrieval, batched same-topic finding, suppression list construction, whole-document coverage finding, and merge-and-validate.
  - Porting the experiment-validated coverage finder instruction set into the engine, including the three-part coverage-summary rule and the "both sides take a position = not a coverage finding" guardrail.
  - Reusing the existing citation validator and taxonomy enforcement from the current engine without modification.
  - Reusing the existing anchor index as the source of verbatim clause text.
  - The axis cache: cached to disk, keyed by anchor text and extraction cap; cap scales with anchor length; shared across all runs on the same documents.
  - The three model tiers (small, mid-tier, large) from Story 1 are used at the correct stage. The pipeline does not configure these tiers — it consumes them as provided by Story 1.

- **Out of scope:**
  - Wiring the pipeline onto the analyze route (Story 3).
  - Changing the existing single-pass analyze behavior — the new pipeline is dormant until Story 3 activates it.
  - Any frontend or drafter-facing changes.
  - Changing the five-label taxonomy, the sentiment rule, or the verbatim-citation guarantee.
  - A cost-reporting or model-usage dashboard.
  - The critic pass — removed by design in Arm G; not included at any stage.

## Goals

- Deliver a self-contained pipeline that a route wiring story can invoke with a document pair and receive a complete, validated finding list in return.
- Ensure that same-topic findings carry only the three agreement-type labels, and coverage findings carry only the two coverage labels — with no overlap between the two sets for the same run.
- Maintain the verbatim-citation guarantee that already exists in the current engine: every finding shown to a drafter quotes an exact clause by its clause number; any finding whose clause cannot be verified is moved to unsupported and never presented as a real finding.
- Keep the taxonomy enforcement rules and the citation validator operating exactly as they do today — this pipeline adds a new entry point, it does not change the shared rules.

## Non-Goals

- Activating the new pipeline on any live route. That is Story 3.
- Changing what findings look like to the drafter — the output shape is identical to today.
- Building a cost dashboard or model-usage reporting interface.
- Improving or changing the existing single-pass analyze path.

## Success Criteria

- A call to the new pipeline for a document pair returns a finding list where: every same-topic finding carries aligns-with, differs-on, or conflicts-with; every coverage finding carries silent-on or goes-beyond; and no topic appears in both groups for the same run.
- Every coverage finding in the output cites clause numbers on exactly one side (the covering side). The other side's clause list is empty, or at most holds a contextual reference explicitly confirming absence.
- The citation validator passes every returned finding — no clause number in any finding is absent from the anchor index.
- The pitch-critical findings from the Arm G experiment survive: the mandatory-versus-voluntary divergence for the HKMA pair, and the payment-initiation write-access divergence for the BIS working-paper pair.
- The axis cache is populated on first run and reused on subsequent runs for the same documents without re-extracting.

## Acceptance Criteria

### Background

```gherkin
Background:
  Given the engine has a complete anchor index for the Open Finance ED and the HKMA Open API Framework
  And the three model tiers are configured: small for extraction, mid-tier for same-topic judgment, large for coverage finding
  And no axis cache exists for these documents yet
```

### Scenario: Full six-stage pipeline completes and returns findings for a document pair

```gherkin
Given Aisyah's document pair is the Open Finance ED and the HKMA Open API Framework
When the Arm G pipeline runs for this pair
Then the pipeline completes all six stages in order
  And findings are returned as a combined list of same-topic findings and coverage findings
  And every finding carries exactly one of the five allowed labels
  And every finding that cites clauses shows verbatim clause text drawn from the anchor index
```

### Scenario: Axis extraction is cached and reused on the second run

```gherkin
Given the Arm G pipeline has already run once for the Open Finance ED and HKMA Framework pair
  And axis phrases were extracted and saved during that first run
When the pipeline runs again for the same pair
Then the axis extraction stage reads from the saved cache rather than calling the small model again
  And the remaining stages run using the cached axis phrases
```

### Scenario: Axis cache is invalidated when a document's anchor text changes

```gherkin
Given the Open Finance ED has a cached set of axis phrases
When the text of one of its anchors changes — for example, clause 10.5 is revised
Then the axis cache for that anchor is treated as stale
  And the small model is called to re-extract axis phrases for the changed anchor
  And the updated axis phrases are saved back to the cache
```

### Scenario: Dense anchors produce more axis phrases than short ones

```gherkin
Given the Open Finance ED contains a long anchor covering eight distinct sub-topics
  And the same document contains a short single-sentence anchor
When axis phrases are extracted for both anchors
Then the long anchor receives more axis phrases than the short anchor
  And the long anchor is not limited to the same small fixed count as the short anchor
```

### Scenario: Same-topic stage produces only agreement-type findings

```gherkin
Given the same-topic retrieval stage surfaces candidate pairs between the Open Finance ED and the HKMA Framework
  And the batched same-topic finder is called with those candidates
When the same-topic finding results are returned
Then every finding in the same-topic results carries one of: aligns-with, differs-on, or conflicts-with
  And no same-topic finding carries silent-on or goes-beyond
```

### Scenario: Batched same-topic judgment calls use the mid-tier model

```gherkin
Given 60 candidate pairs have been surfaced by the same-topic retrieval stage
When the same-topic finder processes these candidates
Then the candidates are sent in batches rather than one pair per call
  And each batch call uses the mid-tier model, not the large model
  And the result is the same set of same-topic findings as would be produced by individual calls
```

### Scenario: Coverage stage uses only the large model

```gherkin
Given the same-topic stage has completed for the Open Finance ED and HKMA Framework pair
  And a suppression list of already-covered topics has been built
When the coverage finder runs its whole-document pass
Then a single call is made to the large model containing the full content of both documents
  And the suppression list is included so those topics are not re-reported
  And the coverage finder uses the large model, not the mid-tier or small model
```

### Scenario: Coverage findings carry only coverage-type labels

```gherkin
Given the coverage finder has completed its whole-document pass
When the coverage findings are returned
Then every finding carries silent-on or goes-beyond
  And no coverage finding carries aligns-with, differs-on, or conflicts-with
  And no coverage finding carries a sentiment value
```

### Scenario: Coverage findings are structurally single-sided

```gherkin
Given the coverage stage produces a "goes-beyond" finding for the Open Finance ED's consent-revocation cadence requirement
When the finding is examined
Then the covering side's clause list is non-empty and quotes the Open Finance ED clause that sets the cadence
  And the other side's clause list is empty, or at most contains a contextual reference confirming that the HKMA framework does not address the cadence
  And the summary names the shared regulatory topic, states what the Open Finance ED requires, and states precisely what the HKMA framework does not address
```

### Scenario: Suppression prevents a same-topic topic from also appearing as a coverage finding

```gherkin
Given the same-topic stage found a "differs-on" finding on the topic of data-access consent for the Open Finance ED and HKMA Framework pair
When the coverage stage runs for the same pair
Then no silent-on or goes-beyond finding appears in the coverage results whose topic is data-access consent
  And the coverage findings cover only topics not already resolved by the same-topic stage
```

### Scenario: A topic genuinely present elsewhere in the other document is not reported as a gap

```gherkin
Given the Open Finance ED covers customer authentication in one passage
  And the HKMA Framework also covers customer authentication, but in a differently-worded section not adjacent to the ED passage
When the coverage finder runs its whole-document pass
Then no silent-on or goes-beyond finding is produced claiming either document omits customer authentication
  And customer authentication appears instead as a same-topic finding if the two positions relate
```

### Scenario: Merge and validate passes all findings through the citation validator

```gherkin
Given the same-topic stage returned findings quoting clauses from the Open Finance ED and HKMA Framework
  And the coverage stage returned findings quoting clauses from those same documents
When the merge-and-validate stage runs
Then every cited clause number is checked against the anchor index
  And every finding whose clause numbers all resolve is placed in the supported list
  And every finding that cites at least one clause number not in the anchor index is moved to the unsupported list with a note that no matching clause was found
  And no text from any unsupported finding is presented as a real finding
```

### Scenario: A finding with an invented clause number is rejected

```gherkin
Given the coverage finder returns a finding that cites a clause number not present in the anchor index
When the merge-and-validate stage runs
Then that finding is placed in the unsupported list
  And the finding is not included in the supported output
  And the reported reason is that no matching clause was found
```

### Scenario: Single-sided coverage findings pass citation validation without error

```gherkin
Given a valid "silent-on" finding where the covering side cites clause 17.2 of the HKMA Framework and the other side's clause list is empty
When the citation validator checks this finding
Then the finding is marked supported
  And the empty clause list on the silent side does not cause the finding to be rejected
```

### Scenario: No critic is called at any stage

```gherkin
Given the Arm G pipeline runs end-to-end for the Open Finance ED and HKMA Framework pair
When the pipeline completes
Then no critic call is made at any stage — not after the same-topic finder and not after the coverage finder
  And the findings returned are the direct output of each finder, filtered only by the citation validator
```

### Scenario: Pitch-critical findings survive the pipeline

```gherkin
Given the Arm G pipeline runs on the HKMA Framework pair and on the BIS working-paper pair
When the findings are reviewed
Then the mandatory-versus-voluntary divergence on the HKMA pair appears as a same-topic finding
  And the payment-initiation write-access divergence on the BIS working-paper pair appears as a same-topic finding
```

### Scenario Outline: Sentiment rules are unchanged — only differs-on may carry sentiment

```gherkin
Given the pipeline produces a finding with label <label>
When the finding is examined for a sentiment value
Then the sentiment field is <expected_sentiment>

Examples:
  | label          | expected_sentiment                         |
  | aligns-with    | absent                                     |
  | differs-on     | one of tighten, loosen, or neutral         |
  | conflicts-with | absent                                     |
  | silent-on      | absent                                     |
  | goes-beyond    | absent                                     |
```

### Scenario: Different-purpose document pair does not produce a flood of spurious coverage findings

```gherkin
Given the Open Finance ED and the tech-risk management document are analyzed as a pair
  And the two documents were written for different regulatory purposes
When the Arm G pipeline runs for this pair
Then the number of coverage findings is small and each names a topic where one side genuinely has no provision
  And unrelated subject matter from either document does not produce coverage findings
```

## Constraints

- **Backwards compatibility:** Must maintain. The existing single-pass analyze behavior is not changed by this story. The citation validator and taxonomy enforcement rules are reused without modification.
- **Downtime:** Not applicable — the new pipeline is dormant until Story 3 wires it onto the analyze route.
- **Compliance:** Every finding must quote the exact clause it relies on, with its clause number. Where no clause supports a claim, the finding is moved to unsupported and the drafter never sees it as a real finding. The five-label taxonomy and the sentiment-only-on-differs-on rule are unchanged.
- **Rollback:** Fully reversible — the new pipeline is a new engine capability that does not replace the existing path until Story 3 explicitly activates it.

## Dependencies

- **Story 1 (Three-tier model configuration):** The pipeline consumes three named model tiers — small, mid-tier, and large. Story 1 defines those tiers and makes them available. Story 2 cannot be completed without them.
- **Anchor index:** The anchor index for both documents in the pair being analyzed must be present and populated. The pipeline reads anchor text from the index and the citation validator resolves clause numbers against it.
- **Axis cache:** Populated on first run for a document pair. Subsequent runs reuse the cache. If the cache is absent, the small model is called to build it before the rest of the pipeline proceeds.

## Open Questions

- [x] ~~Should a critic pass be included in Arm G?~~ — **Resolved:** No critic at any stage. The finder-only design was validated in the experiment and confirmed as the correct choice.
- [x] ~~Which retrieval method — BM25 or cosine similarity?~~ — **Resolved:** Cosine is the default (semantic similarity over axis embeddings — the validated method). BM25 is retained as an automatic fallback when no embeddings endpoint is configured — pure Python, zero cost, preserves graceful degradation. `run_arm_g` takes a `signal` parameter defaulting to cosine, auto-falling-back to BM25. Hybrid is excluded.
- [x] ~~Should coverage findings be allowed to cite a contextual clause from the other side?~~ — **Resolved:** Yes — the covering side must cite a clause; the other side may optionally cite its nearest clause as context only, to confirm that it does not address the sub-point. This does not make the finding two-sided; the citation validator already handles an empty or context-only clause list on the absent side.
- [ ] Should the axis cache be stored alongside the anchor index in the artifacts directory, or in a separate cache directory? — **Deferred (non-blocking):** Either location works; the pipeline reads from wherever Story 1's configuration directs it. This decision can be made during implementation without blocking the pipeline design.

---

## Solution Design

A new engine module `engine/arm_g.py` implements the six-stage pipeline as a single public entry point `run_arm_g(...)`. It composes existing engine pieces — `AnchorIndex` (`engine/anchors.py`), the citation validator `_validate_candidates` and taxonomy enforcement (`engine/connections.py`), and `call_chat` (`engine/llm.py`) — and ports the experiment-validated prompts and retrieval functions from `scripts/experiments/retrieval_ablation.py`. The existing `find_connections` path is untouched; Arm G is a new, parallel entry point that Story 3 wires onto the analyze route.

**Three-tier model routing** (deployments provided by Story 1):

- `EXTRACTION_DEPLOYMENT` (small) — Stage 1 axis extraction
- `REASONING_DEPLOYMENT` (mid) — Stage 3 batched same-topic finder
- `FINDER_CRITIC_DEPLOYMENT` (large) — Stage 5 whole-doc coverage finder

No critic call at any stage.

### Data flow and per-stage design

```
Stage 1  AXIS EXTRACTION                         [EXTRACTION_DEPLOYMENT]
  in : AnchorIndex.by_document(doc) for both docs
  out: axes-{document_id}.json  { anchor_id, text_hash, axis_cap, axes:[...] }
  cap = min(12, max(5, ceil(len(anchor["text"]) / 400)))
  cache hit iff  text_hash == sha256(text)[:16]  AND  axis_cap == cap

Stage 2  SAME-TOPIC RETRIEVAL                     [no model]
  in : axes_a, axes_b
  out: candidates = retrieve_cosine_only(axes_a, axes_b)   # default
       retrieve_bm25_only(axes_a, axes_b)                  # automatic fallback
  shape per candidate: { source_anchor_id, target_anchor_id,
                         matched_axis_source, matched_axis_target, score }
  NB: cosine is preferred (validated default). If no embeddings endpoint is
      configured, fall back to BM25 automatically — pure Python, zero cost,
      keeps the pipeline runnable without embeddings.

Stage 3  BATCHED SAME-TOPIC FINDER                [REASONING_DEPLOYMENT]
  in : candidates (chunked into batches of 8)
  out: same_topic_raw : list[finding dict]
  - Each batch shows the finder the UNION of all anchors in the batch,
    partitioned by side: A-side anchors and B-side anchors listed separately.
  - A finding may cite ANY A-side anchor against ANY B-side anchor in the batch
    (batch-union membership) — not locked to the retrieved pair.
  - PROMPT SIDE-GUARD: source_clauses must be A-side anchor IDs only,
    target_clauses must be B-side anchor IDs only. Enforced by prompt wording,
    NOT a schema enum.
  - Labels restricted to aligns-with / differs-on / conflicts-with by prompt.
  - Batch failure (unparseable / timeout): retry the whole batch ONCE; on second
    failure skip the batch and log every pair id in it. A skipped batch is a
    recall loss, never a correctness fault.

Stage 4  SUPPRESSION LIST BUILD                   [no model]
  in : candidates, same_topic_raw
  out: suppression = { covered_topics:[...], covered_pairs:["a × b", ...] }
  (ported verbatim from _build_suppression in the experiment runner)

Stage 5  WHOLE-DOC COVERAGE FINDER                [FINDER_CRITIC_DEPLOYMENT]
  in : full anchor list of both docs + suppression
  out: coverage_raw : list[finding dict]  (silent-on / goes-beyond only)
  - 1 call. COVERAGE_FINDER_SYSTEM_PROMPT (ported) with the three-part
    COVERAGE-SUMMARY RULE and "both sides take a position = not coverage" guard.

Stage 6  MERGE + REFORMAT + VALIDATE              [no model]
  in : same_topic_raw + coverage_raw
  step a — reformat: for each cited id that does NOT resolve in the index,
           apply _reformat_citation (deterministic; see below); if it now
           resolves, rewrite the citation AND record the rewrite.
  step b — validate: _validate_candidates splits into connections / unsupported
           (existing engine function, unchanged; empty clause list on one side
           of a coverage finding is already treated as resolved).
  out: findings.json  { connections, unsupported }
       trace.json     (all intermediates + counts + wall_clock + rewrites)
```

### The deterministic citation reformatter

`_reformat_citation(cited: str, document_id: str, index: AnchorIndex) -> tuple[str, str] | None` runs ONLY on citations that fail the exact index lookup. It applies reversible, unambiguous transforms in order and returns `(normalized_id, transform_name)` on success or `None` (→ demote to unsupported):

1. `strip_trailing_punct` — `cited.rstrip(" .:;,")`; re-check index.
2. `restore_prefix` — if the stripped id does not start with the document's prefix, prepend it. The prefix is derived from the index, not hardcoded: `index.by_document(document_id)[0]["anchor_id"].rsplit(" ", 1)[0]` (e.g. `"RMiT"`, `"Open Finance ED"`); re-check index.
3. otherwise return `None`.

**No fuzzy / substring / semantic matching.** A citation that only partially resembles a real anchor (e.g. `"B 7."`, or a BIS chunk fragment like `'"5. Conclusion" chunk#68'`) is NOT rescued — it demotes to unsupported, preserving the verbatim-citation guarantee. This is the accepted limitation: the reformatter recovers punctuation/prefix drift only.

Every successful rewrite is appended to `trace.json → citation_rewrites` as:
`{ "cited_raw": "RMiT 2.2(b):", "cited_normalized": "RMiT 2.2(b)", "transform": "strip_trailing_punct" }`

### Output contract (production)

- `findings.json` = `{ "connections": [...], "unsupported": [...] }` — `unsupported` retained; each `Connection` retains `scope_note`.
- `trace.json` = single audit file: `retrieval_candidates`, `same_topic_finder_output`, `suppression`, `coverage_finder_output` (each coverage entry carries computed `single_sided` and `redundant` booleans), `validation`, `citation_rewrites`, plus `counts` (`supported_count`, `unsupported_count`, `same_topic_finding_count`, `coverage_finding_count`) and `wall_clock_seconds`.
- **No `metadata.json`** — counts and timing are folded into `trace.json`. The experiment-era `coverage_quality_notes` structure is removed; its two booleans move onto each `coverage_finder_output` entry.

### Changes

- `engine/arm_g.py` (new) — `run_arm_g`, `_finder_same_topic_batched`, `_build_suppression`, `_finder_coverage_whole_doc`, `_reformat_citation`, `_is_single_sided`, `_is_redundant`, batch chunking + retry-once logic, trace assembly. Ports prompts and retrieval helpers from the experiment runner.
- `engine/config.py` — consumes `EXTRACTION_DEPLOYMENT` and `REASONING_DEPLOYMENT` added by Story 1 (this story does not add them).
- No change to `engine/connections.py`, `engine/anchors.py`, `engine/api.py`.

## Architecture Notes

- **New dependencies:** none. Cosine (default) uses the existing embedding call (`_embed_batch` in the experiment runner); BM25 (fallback) uses `rank-bm25`, already available to the experiment. An embeddings endpoint is preferred but not required — the pipeline falls back to BM25 when it is absent. No new `pyproject.toml` entry.
- **Dependencies & integration:** consumes Story 1's two new deployment vars; reuses `_validate_candidates`, `AnchorIndex`, `call_chat`. The only shared engine surface touched is _reading_ config — no existing function is modified.
- **Reused unchanged:** the five-label taxonomy enforcement (`_validate_label_and_sentiment`), the citation validator (`_validate_candidates`), and `_AnchorAsClauseIndex`-style shimming for anchor-id resolution.

## Exemplar Files

- `scripts/experiments/retrieval_ablation.py` — `run_arm_g`, `_build_suppression`, `_finder_coverage_whole_doc`, `retrieve_cosine_only`, `retrieve_bm25_only`, `_embed_batch`, `COVERAGE_FINDER_SYSTEM_PROMPT` — the validated experiment implementation this story ports. NB (1) the experiment finder is per-pair; this story replaces that loop with batched (size 8) union-membership calls. (2) Port both `retrieve_cosine_only` (default) and `retrieve_bm25_only` (fallback); `retrieve_hybrid` is NOT ported.
- `engine/connections.py` — `find_connections` (public-entry-point shape to mirror), `_validate_candidates` (reused), `FINDER_SYSTEM_PROMPT` / `_TAXONOMY_PROMPT_BLOCK` (citation + taxonomy contract to copy from).
- `engine/anchors.py` — `AnchorIndex.get` / `.by_document` (anchor-id resolution and per-document listing).

## Implementation Plan

### Sub-tasks

**Task 1: Axis extraction with scaled cap + cache invalidation** — _small_

- Port `extract_axes_for_anchor` / cache logic into `engine/arm_g.py` using `EXTRACTION_DEPLOYMENT`; cap scales with length; cache hit keyed on `text_hash` AND `axis_cap`.
- Files: `engine/arm_g.py`
- SEQUENTIAL (depends on Story 1)

**Task 2: Retrieval + batched same-topic finder (union membership, prompt side-guard, retry-once)** — _medium_

- Port `retrieve_cosine_only` (+ `_embed_batch`) and `retrieve_bm25_only`; select cosine when an embeddings endpoint is configured, else fall back to BM25. Add `_finder_same_topic_batched` (batch size 8, union anchors partitioned by side, labels restricted to the three agreement types, side-guard by prompt); retry-once-then-skip-batch failure handling using `REASONING_DEPLOYMENT`.
- Files: `engine/arm_g.py`
- SEQUENTIAL (depends on Task 1)

**Task 3: Suppression build + whole-doc coverage finder** — _medium_

- Port `_build_suppression` and `_finder_coverage_whole_doc` + `COVERAGE_FINDER_SYSTEM_PROMPT` using `FINDER_CRITIC_DEPLOYMENT`.
- Files: `engine/arm_g.py`
- SEQUENTIAL (depends on Task 2)

**Task 4: Reformatter + merge/validate + trace assembly** — _medium_

- Add `_reformat_citation` (strip-trailing-punct, prefix-restore, no fuzzy); wire the reformat-before-validate step; assemble `findings.json` and the single `trace.json` (intermediates + counts + wall_clock + `citation_rewrites` + per-coverage `single_sided`/`redundant`); no `metadata.json`.
- Files: `engine/arm_g.py`
- SEQUENTIAL (depends on Task 3)

**Task 5: `run_arm_g` orchestration + unit tests** — _medium_

- Wire Stages 1–6 in order; expose `run_arm_g(anchor_index, doc_a, doc_b, signal="cosine")` where `signal` selects the retrieval method and auto-falls-back to BM25 when no embeddings endpoint is configured; returns the same result-dict shape the route will consume; add engine tests.
- Files: `engine/arm_g.py`, `engine/tests/test_arm_g.py`
- SEQUENTIAL (depends on Task 4)

### Negative Constraints

- Do NOT modify `engine/connections.py`, `engine/anchors.py`, `engine/api.py`, or `engine/tests/test_taxonomy_traces.py`.
- Do NOT add a critic call at any stage.
- Do NOT use a schema enum for citation fields — side-guard is by prompt; drift is caught by the reformatter + validator.
- Do NOT add fuzzy/substring/semantic citation matching to the reformatter.
- Do NOT change the five-label taxonomy, the sentiment rule, or the `supported` semantics.
- Do NOT emit a `metadata.json`.
- Do NOT rebuild `data/artifacts/anchor-index.json`.
- Do NOT port `retrieve_hybrid` — only cosine (default) and BM25 (fallback) are part of the production pipeline.

## Test Scenarios

**Test 1: Same-topic labels restricted (batched)**

- Setup: stub `REASONING_DEPLOYMENT` finder to return a batch containing a `silent-on` item.
- Action: run Stage 3 over 16 candidates (2 batches of 8).
- Expected: taxonomy validation rejects the `silent-on` from the same-topic stage; only aligns/differs/conflicts survive to merge.

**Test 2: Batch-union membership**

- Setup: a batch where retrieval paired `ED 10.5 × HKMA 8.2` and separately `ED 11.8 × HKMA 9.3`; stub finder to cite `ED 10.5 × HKMA 9.3`.
- Action: run Stage 3.
- Expected: the cross-pair finding is accepted (both anchors were in the batch union); `source_clauses` holds only A-side ids, `target_clauses` only B-side ids.

**Test 3: Batch failure retry-once-then-skip**

- Setup: stub finder to raise on a batch's first call and succeed on retry.
- Action: run Stage 3.
- Expected: one retry occurs, batch succeeds. Second setup: raise on both calls → batch skipped, all 8 pair ids logged, pipeline continues.

**Test 4: Reformatter recovers punctuation/prefix drift**

- Setup: coverage finding cites `"RMiT 2.2(b):"` and `"2.1"` (bare) where `"RMiT 2.2(b)"` and `"RMiT 2.1"` exist in the index.
- Action: run Stage 6.
- Expected: both rewritten and marked supported; `trace.json → citation_rewrites` contains `{cited_raw:"RMiT 2.2(b):", cited_normalized:"RMiT 2.2(b)", transform:"strip_trailing_punct"}` and the prefix-restore entry for `"2.1"`.

**Test 5: Reformatter refuses unsafe rescue**

- Setup: coverage finding cites `"B 7."` and `'"5. Conclusion" chunk#68'`, neither resolvable by strip/prefix.
- Action: run Stage 6.
- Expected: both demote to `unsupported` with "No matching clause found"; no rewrite recorded; no fuzzy match attempted.

**Test 6: Single-sided coverage finding validates**

- Setup: `silent-on` finding, `source_clauses=[]`, `target_clauses=["HKMA OpenAPI 17.2"]` (resolvable).
- Action: run Stage 6.
- Expected: supported; empty source list does not cause rejection.

**Test 7: Output contract shape**

- Setup: a completed Arm G run.
- Action: inspect written files.
- Expected: `findings.json` has keys `connections` + `unsupported`; each connection retains `scope_note`; `trace.json` carries `counts`, `wall_clock_seconds`, `citation_rewrites`, and per-`coverage_finder_output` `single_sided`/`redundant`; NO `metadata.json` written.

**Test 8: Cache invalidation on cap change**

- Setup: an axis cache entry written with `axis_cap=5`; the anchor text now yields `cap=7`.
- Action: run Stage 1.
- Expected: cache miss → re-extraction → entry rewritten with `axis_cap=7`.

**Test 9: Three-tier routing**

- Setup: distinct stub deployments for extraction / reasoning / finder-critic.
- Action: run all stages.
- Expected: Stage 1 calls the extraction deployment, Stage 3 the reasoning deployment, Stage 5 the finder-critic (large) deployment; no critic deployment call anywhere.

## Verification

Run the verifier skill after implementation. Then, from the main working tree (per the "run forge builds in the main tree" learning):

```bash
.venv/bin/python -m pytest engine/tests/test_arm_g.py engine/tests/test_taxonomy_traces.py -v
```

### Backend Tests

- `engine/tests/test_arm_g.py` (new) — covers Tests 1–9 above with stubbed deployments (no live model calls), mirroring how existing engine tests inject `finder_fn`/`critic_fn` stubs.
- `engine/tests/test_taxonomy_traces.py` — must stay green, unchanged (taxonomy and citation guarantees are reused, not modified).

### Manual Verification

- [ ] Run `run_arm_g` against the Open Finance ED × HKMA pair (live) and confirm: coverage findings are single-sided; pitch-critical mandatoriness divergence appears as a same-topic finding; `trace.json` contains counts, wall_clock, and any citation_rewrites; no `metadata.json` is written.
- [ ] Confirm a same-topic-heavy pair completes with batched calls (roughly ⌈candidates / 8⌉ reasoning-deployment calls + 1 finder-critic call), not one call per candidate.
