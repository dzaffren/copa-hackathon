# Arm G — Coverage-aware composite finding flow

**Ticket:** TBD
**Type:** Technical — Evaluation tooling
**Epic:** [Experiment — Retrieval-strategy ablation](experiment-retrieval-ablation.md)

Adds a new arm to the retrieval-ablation experiment that derives findings differently depending on the kind of relationship being asserted: "both sides speak to a topic" findings come from focused pairwise comparison, while "only one side covers a topic" findings come from a whole-document pass that can actually confirm an absence. This fixes the experiment's most misleading signal — the coverage findings — so the team can trust the evidence when picking which analyze pipeline to ship.

## Motivation

The retrieval-ablation experiment exists to choose the smallest analyze pipeline that lands the pitch's cross-jurisdiction narrative. But the experiment's output files misrepresent the quality of two of the five finding labels, so the decision would be made on bad evidence.

Findings carry one of five labels. Three of them — "aligns with", "differs on", "conflicts with" — describe two clauses that are _both present_ and relate to each other. Two of them — "silent on" and "goes beyond" — are **coverage** labels: they assert that a topic is present on exactly one side. "Silent on" means our document does not cover something the other document does; "goes beyond" is the mirror.

**Current state.** Every arm in the experiment compares documents anchor-by-anchor, handing the analyst exactly two passages at a time. This works for the three same-topic labels — you can judge whether two passages agree or differ by reading just those two. It fails for the coverage labels for two reasons:

1. **Absence cannot be judged from a single pair.** A coverage claim is about a whole document ("the other side covers this _nowhere_"). When the analyst only ever sees one passage from each side, it will declare the other side "silent" on a topic even when that topic is thoroughly addressed in a different part of that same document — it simply never saw the other part.
2. **The pass/fail flag is being misread as a quality signal.** A finding is currently flagged "supported" purely when every clause it quotes can be found verbatim in the source — an anti-fabrication check, never a measure of whether the finding is a _good_ one. Because the anchor-by-anchor setup forces every finding to quote a passage from both sides, genuine one-sided coverage findings get distorted: "silent on" collapses into "differs on, more permissive", "goes beyond" collapses into "differs on, stricter", or the passage quoted from the empty side is simply irrelevant.

The result: the two coverage labels look like weak or mislabelled versions of "differs on", and the experiment cannot honestly report how well any arm surfaces coverage gaps.

**Desired state.** A new arm ("Arm G") produces same-topic findings and coverage findings through two different, purpose-fit passes, so that:

- Coverage findings genuinely reflect one-sided coverage, confirmed against the whole of the other document.
- Coverage findings do not merely repeat topics already reported as same-topic findings.
- Coverage finding summaries are specific and useful to a policy drafter — they name the shared topic, say what the covering side requires, and say precisely what the other side leaves unaddressed.
- The experiment gains a trustworthy read on coverage quality that it can weigh when choosing the shipping pipeline.

**Trigger.** While generating findings for the experiment, the team observed that the "supported" flag does not measure output quality for the coverage labels, and that anchor-by-anchor comparison structurally cannot establish a whole-document absence. The pitch depends on cross-jurisdiction coverage gaps landing cleanly, so this must be fixed before the ablation's decision is trusted.

## Scope

- **In scope:**
  - A new composite arm ("Arm G") in the retrieval-ablation experiment that derives same-topic findings via focused pairwise comparison and coverage findings via a whole-document pass.
  - A sequential rule ("suppression list") that stops the coverage pass from re-reporting a topic already found as a same-topic finding.
  - An enhanced instruction set for the coverage pass so "silent on" / "goes beyond" summaries are meaningful and do not collapse into "differs on".
  - Scaling the number of topic descriptors extracted per passage by the length of that passage, so dense passages are not artificially capped.
  - A per-finding coverage-quality note recorded in the experiment output.
  - Validation runs on all three demo pairs, including the different-purpose stress pair.

- **Out of scope:**
  - Any change to the behaviour of the existing arms (the whole-document arm, the two keyword arms, the two semantic arms). They must produce the same output as before.
  - Promoting this flow into the live analyze pipeline or exposing it through the product. That is a deliberate follow-on once Arm G is validated.
  - Changing the five-label taxonomy, the sentiment rule, or the verbatim-citation guarantee.
  - Building or curating the cross-jurisdiction glossary. It may be plugged in later but is not required here.

## Goals

- Produce coverage findings ("silent on" / "goes beyond") on the demo pairs that a human judge marks as genuine at least 7 out of 10 times.
- Ensure zero coverage findings duplicate a topic already reported as a same-topic finding on the same pair.
- Preserve both pitch-critical findings on their pairs (the mandatory-vs-voluntary divergence on the regulator pair; the payment-initiation write-access divergence on the working-paper pair).
- Surface at least one genuine coverage finding that the older arms collapsed or mislabelled.
- On the different-purpose stress pair, keep the count of coverage findings bounded — no flood of spurious one-sided gaps.

## Non-Goals

- Guaranteeing that same-topic findings improve over the existing semantic/keyword arms. Same-topic quality is assumed to hold because that pass reuses the established comparison approach; it is not separately re-measured in this task.
- Reaching a final decision on which pipeline to ship. Arm G adds evidence to the existing decision rule; it does not replace it.
- Handling document pairs beyond the three demo pairs.

## Success Criteria

- On the two similar-purpose demo pairs, the coverage findings pass the human-judged genuineness bar (≥ 7 of 10 sampled are real one-sided gaps, not disguised "differs on" or irrelevant-passage noise).
- No coverage finding on any validated pair repeats a topic that was already reported as a same-topic finding for that pair.
- Both pitch-critical findings still appear on their respective pairs after the change.
- At least one coverage finding surfaces on a demo pair that the previous anchor-by-anchor arms got wrong (collapsed into "differs on" or missed).
- On the different-purpose stress pair, coverage findings remain few and defensible rather than flooding — demonstrating the whole-document confirmation and suppression rule prevent noise between documents written for unrelated purposes.
- The existing arms produce byte-for-byte the same findings they did before Arm G was added.

## Acceptance Criteria

> Operational scenarios describing the observable behaviour of the experiment when Arm G is run. "The analysis" refers to the experiment's finding-generation for a document pair.

### Scenario: Coverage finding confirmed against the whole of the other document

```gherkin
Given the Open Finance response is being compared against the HKMA Open API framework
  And the Open Finance response requires a specific consent-revocation cadence
  And no part of the HKMA framework addresses that revocation cadence
When Arm G runs the analysis on this pair
Then a "goes beyond" finding is produced for the consent-revocation cadence
  And the finding quotes the Open Finance passage that sets the cadence
  And the finding states that the HKMA framework does not address it
  And the finding is confirmed against the entire HKMA framework, not just one nearby passage
```

### Scenario: A topic present elsewhere in the other document is not reported as a gap

```gherkin
Given the Open Finance response is being compared against the HKMA framework
  And the Open Finance response covers customer authentication in one passage
  And the HKMA framework also covers customer authentication, but in a differently-worded passage
When Arm G runs the analysis on this pair
Then no "silent on" or "goes beyond" finding is produced claiming either side omits customer authentication
  And customer authentication is instead reported as a same-topic finding if the two positions relate
```

### Scenario: Coverage pass does not repeat a same-topic finding

```gherkin
Given the analysis has already found that both documents address data-access consent as a same-topic finding
When Arm G runs its coverage pass on the same pair
Then data-access consent does not also appear as a "silent on" or "goes beyond" finding
  And the coverage findings cover only topics not already reported as same-topic
```

### Scenario: Coverage summaries are specific, not collapsed into a difference

```gherkin
Given Arm G produces a "silent on" finding on a demo pair
When a policy drafter reads the finding summary
Then the summary names the shared topic both documents sit under
  And the summary states what the covering document requires
  And the summary states precisely what our document leaves unaddressed
  And the summary does not describe the two sides as merely taking different positions on the same rule
```

### Scenario: Dense passages yield more topic descriptors than short ones

```gherkin
Given one passage is a long clause covering eight distinct sub-topics
  And another passage is a single short sentence
When topic descriptors are extracted for each passage
Then the long passage yields more descriptors than the short one
  And the long passage is not capped at the small fixed number used previously
```

### Scenario: Pitch-critical findings survive the change

```gherkin
Given Arm G runs the analysis on the HKMA pair and on the BIS working-paper pair
When the findings are reviewed
Then the mandatory-versus-voluntary divergence still appears on the HKMA pair
  And the payment-initiation write-access divergence still appears on the BIS working-paper pair
```

### Scenario: Different-purpose pair does not flood with spurious gaps

```gherkin
Given the Open Finance response is being compared against the tech-risk management document, which was written for a different purpose
When Arm G runs the analysis on this pair
Then the number of coverage findings remains small and defensible
  And each coverage finding names a genuinely shared topic where one side stops short
  And unrelated subject matter from either document does not produce coverage findings
```

### Scenario: Existing arms are unchanged

```gherkin
Given the existing arms are run on the same pairs as before Arm G was added
When their findings are compared against the previously recorded findings
Then each existing arm produces the same findings it produced before
```

## Constraints

- **Backwards compatibility:** Must maintain. Existing arms and their recorded outputs must not change.
- **Compliance:** Every finding must continue to quote the exact clause it relies on, with its clause number; where no clause supports a claim, the finding must say so rather than invent one. The five-label taxonomy and the sentiment-only-on-"differs on" rule are unchanged.
- **Rollback:** Fully reversible — Arm G is additive experiment tooling; removing it leaves the rest of the experiment intact.
- **Downtime:** N/A — offline experiment tooling, not a running service.

## Dependencies

- The topic-descriptor cache used by the semantic and keyword arms (Arm G's same-topic stage reuses it and benefits from the larger per-passage descriptor counts).
- A working text-embedding endpoint for the semantic variant of Arm G's same-topic stage; the keyword variant needs no embedding endpoint and can run in its absence.
- The existing anchor-level index of the three demo documents (Open Finance response, HKMA framework, BIS working paper) plus the tech-risk document for the stress pair.

## Open Questions

- [x] ~~How should the coverage pass avoid double-counting what the same-topic pass already found?~~ — **Resolved:** Sequential suppression list. The same-topic stage runs first; the topics it matched are handed to the coverage pass as "already covered on both sides — do not report as gaps."
- [x] ~~How is Arm G judged successful?~~ — **Resolved:** Coverage findings must be genuine (≥ 7 of 10 human-judged) and non-redundant with same-topic findings; both pitch-critical findings must survive; and at least one genuine coverage finding the old arms got wrong must surface. Same-topic parity is assumed, not separately measured.
- [x] ~~Which pairs must be validated?~~ — **Resolved:** All three — the HKMA pair and the BIS working-paper pair (pitch-critical coverage), and the tech-risk pair (different-purpose stress test that the coverage output does not flood).
- [x] ~~Should this change the live product now?~~ — **Resolved:** No. Experiment-only. Promotion to the live analyze pipeline is a deliberate follow-on after Arm G validates.
- [ ] Does restricting the same-topic pass to the three same-topic labels ever suppress a legitimate finding the unrestricted comparison would have caught? — **Deferred (non-blocking):** Same-topic parity is assumed for this task; if a regression is noticed during human judgment it will be raised then, but it does not block delivering Arm G.

---

## Solution Design

Arm G is a **composite arm**: it runs a same-topic stage (reusing an existing retrieval arm) and then a coverage stage (a whole-document pass), and merges their outputs through the existing citation validator. It lives entirely in `scripts/experiments/retrieval_ablation.py` plus a one-function change in `scripts/experiments/extract_axes.py`. The five-label taxonomy, the verbatim-citation validator (`_validate_candidates`), and the `_AnchorAsClauseIndex` shim are reused unchanged.

The coverage labels are directional (per `engine/connections.py` direction convention: document A is "we/ours", document B is "they/theirs" — `goes-beyond` = A covers, B absent; `silent-on` = A absent, B covers). Because the coverage stage is a **whole-document** pass, the finder sees every anchor of both documents in one prompt and can emit both directions in a single call — no second retrieval direction is needed, and it can verify that a topic is absent across the _entire_ other document rather than just a nearby passage.

### Data flow — sequence of events for one `(arm=G, pair)` run

The following is the end-to-end sequence `run_arm_g(anchor_index, doc_a, doc_b, signal)` executes. Data shapes are given at each hand-off.

```
STAGE 0 — Axis extraction (precondition, run once via extract_axes.py)
  For each document: each anchor -> LLM -> N topic axes (N now scales with anchor length).
  Cached to experiments/axes-{document_id}.json:
    { "document_id": "...", "anchors": [ {"anchor_id","text_hash","axes":[str,...]}, ... ] }

STAGE 1 — Same-topic retrieval  (deterministic, no LLM)
  axes_a = _load_axes(doc_a)          # {anchor_id: [axis, ...]}
  axes_b = _load_axes(doc_b)
  candidates = retrieve_cosine_only(axes_a, axes_b)   if signal == "cosine"
             = retrieve_bm25_only(axes_a, axes_b)     if signal == "bm25"
  # candidates: list of pair dicts, each:
  #   {source_anchor_id, target_anchor_id, matched_axis_source,
  #    matched_axis_target, similarity|bm25_score, signal}

STAGE 2 — Same-topic finder + critic  (LLM, per pair; mirrors run_arm_c loop)
  for pair in candidates:
      f = _finder_per_pair(anchor_index, pair, labels="same-topic")   # 3 labels only
      c = _critic_per_pair(anchor_index, pair, f)
      same_topic_candidates += c
  # each surviving candidate: {summary, label in {aligns-with,differs-on,conflicts-with},
  #                            sentiment?, source_clauses:[anchor_id], target_clauses:[anchor_id],
  #                            scope_note?}

STAGE 3 — Suppression list build  (deterministic, no LLM)
  suppression = {
    "topics":  sorted set of matched_axis_source + matched_axis_target
               over every candidate that produced a surviving same-topic finding,
    "pairs":   sorted set of (source_anchor_id, target_anchor_id) that produced one
  }
  # This is the "already covered on both sides" set handed to the coverage stage.

STAGE 4 — Coverage whole-doc pass  (LLM, one finder call, optional one critic call)
  user = _format_doc_block(anchor_index, doc_a) + _format_doc_block(anchor_index, doc_b)
       + "TOPICS ALREADY COVERED ON BOTH SIDES (do NOT report as gaps): {suppression.topics}"
  coverage_raw   = call_chat(COVERAGE_FINDER_SYSTEM_PROMPT, user)     # silent-on / goes-beyond only
  coverage_final = _critic_coverage_whole_doc(...)                    # optional; same 2-label restriction
  # each coverage candidate is single-sided:
  #   goes-beyond -> source_clauses:[A anchor], target_clauses:[]   (B may be cited as context)
  #   silent-on   -> source_clauses:[],        target_clauses:[B anchor]

STAGE 5 — Merge + validate  (deterministic, no LLM)
  merged = same_topic_candidates + coverage_final
  supported, unsupported, validation = _validate_candidates(merged, _AnchorAsClauseIndex(anchor_index))
  # _validate_candidates already treats an empty clause list as "all resolved",
  # so a single-sided coverage finding stays supported=True honestly.

STAGE 6 — Write  (run_one, extended)
  findings.json  = {connections: supported, unsupported}
  trace.json     += {suppression, coverage_finder_output, coverage_critic_output,
                     retrieval_candidates: <stage-1 candidates>}
  metadata.json  += {coverage_finding_count, same_topic_finding_count,
                     coverage_quality_notes: [...]}   # see Test Scenarios / metric below
```

**Why the ordering is strict (SEQUENTIAL within the arm).** Stage 3 depends on Stage 2's _surviving_ findings (post-critic), and Stage 4 depends on Stage 3's suppression list. Stages 1, 3, 5 are pure Python; Stages 2 and 4 are the only LLM spend.

### Changes

- `scripts/experiments/extract_axes.py` — replace the fixed cap `axes = axes[:5]` (currently ~lines 111–112) with a length-scaled cap `cap = min(12, max(5, ceil(len(anchor["text"]) / 400)))`, truncate to `cap`, and pass the computed `N` into the user prompt so the model targets the right count. Update the "1-5" wording in `_AXIS_SYSTEM_PROMPT` and the module docstring to "1-N". `text_hash` already drives cache invalidation, so re-running re-extracts.
- `scripts/experiments/retrieval_ablation.py`:
  - Add `COVERAGE_FINDER_SYSTEM_PROMPT` (and `COVERAGE_CRITIC_SYSTEM_PROMPT`) as module-level constants **local to the runner** — do NOT edit `engine.connections`. They restrict output to `silent-on` / `goes-beyond`, embed the COVERAGE-SUMMARY RULE (name the shared topic; state what the covering side requires; state precisely what the other side does not address; NOT a disagreement, NOT a stricter version of the same rule), and reuse the verbatim CITATION RULE + JSON-array contract from `FINDER_SYSTEM_PROMPT`.
  - Add a `labels` parameter (or a same-topic prompt variant) to `_finder_per_pair` / `_critic_per_pair` so the same-topic stage emits only the three same-topic labels and skips one-sided pairs.
  - Add `_build_suppression(same_topic_candidates) -> {"topics": [...], "pairs": [...]}`.
  - Add `_finder_coverage_whole_doc(anchor_index, doc_a, doc_b, suppression)` and `_critic_coverage_whole_doc(...)`, modelled on `_finder_whole_doc` / `_critic_whole_doc` (both use `_format_doc_block`, `max_tokens=16384`).
  - Add `run_arm_g(anchor_index, doc_a, doc_b, signal="cosine")` implementing Stages 1–5 and returning the standard result dict (`retrieval_candidates` = Stage-1 candidates; coverage raw + suppression stashed for the trace).
  - Register `"G": run_arm_g` in `ARM_RUNNERS`; thread an optional `--signal cosine|bm25` CLI arg through `main` / `run_one` into `run_arm_g` (default `cosine`).
  - Extend `run_one` to write the extra trace/metadata fields (suppression, coverage outputs, coverage-quality notes).
  - Fix the stale `arms = ["B","C","D"]` default in `main` for `--arm all` so it includes E/F/G.

## Architecture Notes

- **New dependencies:** none. Cosine path uses the existing Bedrock embedding call (`_embed_batch`); BM25 path uses the already-listed `rank-bm25`. No new `pyproject.toml` or CI-workflow deps, so the "engine deps live in two places" learning does not apply here.
- **Dependencies & integration:** `run_arm_g` composes existing pieces — `retrieve_cosine_only` / `retrieve_bm25_only`, `_finder_per_pair` / `_critic_per_pair`, `_format_doc_block`, `_validate_candidates`, `_AnchorAsClauseIndex`, `_load_axes`. The only shared surface touched is `_finder_per_pair` / `_critic_per_pair` gaining an optional `labels` argument — it must default to current behaviour so Arms C/D/E/F are byte-for-byte unchanged.

## Exemplar Files

- `scripts/experiments/retrieval_ablation.py` `run_arm_c` (~lines 645–690) — the same-topic stage loop mirrors this exactly (retrieve → per-pair finder+critic → validate).
- `scripts/experiments/retrieval_ablation.py` `_finder_whole_doc` / `_critic_whole_doc` (~lines 531–564) — the coverage whole-doc pass follows this prompt-assembly and `call_chat` pattern.
- `engine/connections.py` `_TAXONOMY_PROMPT_BLOCK` / `FINDER_SYSTEM_PROMPT` (~lines 325–367) — the label definitions and citation/JSON contract the coverage prompt copies and narrows.

## Implementation Plan

### Sub-tasks

**Task 1: Scale the per-anchor axis cap** — _small_

- Files: `scripts/experiments/extract_axes.py`
- INDEPENDENT

**Task 2: Coverage-stage prompts + same-topic label restriction** — _small_

- Add `COVERAGE_FINDER_SYSTEM_PROMPT` / `COVERAGE_CRITIC_SYSTEM_PROMPT`; add optional `labels` arg to `_finder_per_pair` / `_critic_per_pair` (default preserves current behaviour).
- Files: `scripts/experiments/retrieval_ablation.py`
- INDEPENDENT

**Task 3: Suppression builder + coverage whole-doc functions** — _medium_

- Add `_build_suppression`, `_finder_coverage_whole_doc`, `_critic_coverage_whole_doc`.
- Files: `scripts/experiments/retrieval_ablation.py`
- SEQUENTIAL (depends on Task 2)

**Task 4: `run_arm_g` composite + CLI + trace/metadata wiring** — _medium_

- Add `run_arm_g`, register in `ARM_RUNNERS`, thread `--signal`, extend `run_one` writes, fix `--arm all` default list.
- Files: `scripts/experiments/retrieval_ablation.py`
- SEQUENTIAL (depends on Tasks 2 and 3)

**Task 5: Coverage-quality metric note** — _small_

- Per coverage finding, record in metadata whether it is single-sided and whether its matched topic is absent from the suppression list.
- Files: `scripts/experiments/retrieval_ablation.py`
- SEQUENTIAL (depends on Task 4)

### Negative Constraints

- Do NOT modify `engine/connections.py`, `engine/anchors.py`, or `engine/tests/test_taxonomy_traces.py`. Promotion to the engine is a separate follow-on.
- Do NOT change `run_arm_b/c/d/e/f`, `retrieve_cosine_only`, `retrieve_bm25_only`, `_bm25_retrieve_per_anchor`, or `retrieve_hybrid` behaviour. The optional `labels` arg on `_finder_per_pair`/`_critic_per_pair` MUST default to current behaviour.
- Do NOT build or wire the glossary; the coverage stage does not use it.
- Do NOT rebuild `data/artifacts/anchor-index.json` (the "engine.build silently narrows artifacts" blocker).

## Test Scenarios

**Test 1: Existing arms unchanged**

- Setup: recorded `experiments/retrieval-ablation/C/hkma-ed/findings.json` from before the change.
- Action: run `python scripts/experiments/retrieval_ablation.py --arm C --pair hkma-ed`.
- Expected: `connections` / `unsupported` shape and `_finder_per_pair` call arguments identical to before (default `labels`), no diff attributable to the new arg.

**Test 2: Axis cap scales with length**

- Setup: one anchor with `len(text) > 2000`, one with `len(text) < 200`.
- Action: run `extract_axes.py` for their document.
- Expected: long anchor's `axes` length > short anchor's; long anchor may exceed 5 (up to cap 12); short anchor still ≥ 1.

**Test 3: Coverage finding is single-sided and validates supported**

- Setup: an Arm G run on `hkma-ed`.
- Action: inspect `findings.json` coverage entries.
- Expected: every `goes-beyond` has non-empty `source_clauses` and empty (or context-only) `target_clauses`; every `silent-on` the mirror; each carries `supported: true`; `sentiment` is null (sentiment only on `differs-on`).

**Test 4: Suppression prevents duplication**

- Setup: Arm G run where same-topic stage produced a `differs-on` on topic "data-access consent" (topic in `suppression.topics`).
- Action: inspect coverage findings.
- Expected: no `silent-on`/`goes-beyond` finding whose matched topic is in `suppression.topics`; metadata coverage-quality note flags any that slip through as `redundant: true`.

**Test 5: Whole-doc absence (B4 case)**

- Setup: a topic present in a _non-adjacent_ anchor of document B (low retrieval similarity to the A anchor).
- Action: run Arm G; check no `silent-on`/`goes-beyond` claims B omits that topic.
- Expected: because the coverage finder sees all of B via `_format_doc_block`, it does not report a gap the whole document actually covers.

**Test 6: Missing embeddings endpoint degrades gracefully**

- Setup: no Bedrock creds configured.
- Action: run `--arm G --pair hkma-ed --signal bm25`.
- Expected: same-topic stage uses BM25 (no embedding call), coverage stage runs, findings written; `--signal cosine` under no creds fails only at the embedding call with the existing error, not silently.

## Acceptance Criteria

- [ ] `--arm G --pair {hkma-ed,bis-ed,rmit-ed}` each write `findings.json`, `trace.json`, `metadata.json` under `experiments/retrieval-ablation/G/{pair}/`.
- [ ] Coverage findings are single-sided and `supported: true`; sentiment null on both coverage labels.
- [ ] No coverage finding's matched topic appears in the run's suppression list.
- [ ] Both pitch-critical findings appear (HKMA mandatoriness `differs-on/tighten`; BIS payment-initiation divergence).
- [ ] `rmit-ed` coverage-finding count stays bounded (no flood) and each names a genuinely shared topic.
- [ ] Arms B/C/D/E/F outputs are unchanged (Test 1).
- [ ] Existing engine tests still pass; no new type/lint issues in the two touched scripts.

## Verification

Run the verifier skill after implementation. Then, from the main working tree (per the "run forge builds in the main tree" learning):

```bash
# regenerate axes with the scaled cap
python scripts/experiments/extract_axes.py --docs bnm-open-finance-ed-2025 hkma-open-api-framework-2018 bis-pap168-open-finance bnm-rmit-nov25
# run Arm G on all three validation pairs
python scripts/experiments/retrieval_ablation.py --arm G --pair hkma-ed
python scripts/experiments/retrieval_ablation.py --arm G --pair bis-ed
python scripts/experiments/retrieval_ablation.py --arm G --pair rmit-ed
# no-embeddings fallback
python scripts/experiments/retrieval_ablation.py --arm G --pair hkma-ed --signal bm25
```

### Backend Tests

- Existing engine suite must stay green: `.venv/bin/python -m pytest engine/tests` (in particular `engine/tests/test_taxonomy_traces.py`, which is untouched and must still pass since the taxonomy is unchanged).
- The experiment scripts have no dedicated unit-test suite today; verification is via the runs above plus the human-judgment pass defined in the parent experiment spec.

### Manual Verification

- [ ] Inspect `experiments/retrieval-ablation/G/hkma-ed/trace.json`: confirm `suppression`, `coverage_finder_output`, and `retrieval_candidates` are all present.
- [ ] Human-judge 10 coverage findings per similar-purpose pair (hkma-ed, bis-ed) → ≥ 7/10 genuine.
- [ ] Confirm at least one coverage finding that Arm C/E collapsed into `differs-on` is now a clean `silent-on`/`goes-beyond`.
- [ ] Diff an existing arm's re-run against its prior `findings.json` to confirm no regression (Test 1).
