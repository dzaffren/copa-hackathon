# Experiment — Retrieval-strategy ablation on cross-jurisdiction pairs

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)
**Type:** Experiment — Engine evaluation
**Status:** Not started (spec approved 2026-07-21)

## Purpose

Decide between three implementation options for the cross-jurisdiction analyze flow — anchor-swap only, cosine-only retrieval, or full hybrid retrieval — by measuring output quality on the two demo-critical cross-jurisdiction pairs. The experiment produces the evidence needed to pick the smallest option that lands the pitch's cross-jurisdiction narrative on stage.

## Background: why Arm A (current ClauseIndex baseline) is dropped

Before designing the arms, the natural instinct is to include the current staging engine as a floor comparator (Arm A). Analysis shows this is not a fair test — it would produce a definitional non-run, not a meaningful data point. Recording the analysis here so we don't relitigate it or return to it under time pressure.

**What the current engine can do:** dzaf's `engine/api.py` analyze route calls `find_connections(doc_a_id, doc_b_id, clause_index)` in `engine/connections.py`. The `ClauseIndex` is built by `engine.clauses.segment_clauses` — a strict, network-free, regex-driven line classifier specifically calibrated for BNM's PD template. It classifies each markdown line by regex as one of: numbered clause (`^\s*(\d+\.\d+(?:\(\w+\))*)\s+`), sub-item (`^\s*\(([a-z]+|[ivx]+)\)\s+`), appendix (`^\s*Appendix\s+\d+`), or a bare-integer section heading (constrained to be the monotonic successor of the previous heading so footnotes like `44 This is also applicable` are rejected). It also uses `S` / `G` markers as structural boundary hints.

**What that means for non-BNM documents.** The parser was written for the BNM PD template — the regex encodes assumptions specific to that structure. Applied to HKMA's Open API Framework 2018:

- HKMA numbered principles appear inside bold heading formatting (`## 8.1 The HKMA...`) — not as bare `8.1` at line start.
- Suffixes like `58(REST)` don't match the sub-item regex's `(a|b|c|...|i|ii|iii|...)` alphabetical / roman-numeral constraint.
- The framework has **no `S` / `G` markers** — the parser reads that absence as "no clause boundary here" and treats the whole document as one un-anchored blob.

Applied to BIS Working Paper 168:

- Numbering is `1. Introduction`, `2. Background` — single-digit followed by period, not `N.M`.
- Or prefix-form like `Section 3.1` — the regex expects the number at line start with no leading word.
- Footnote numbers throughout the running text — exactly the pattern the monotonic-successor check exists to reject.
- No `S` / `G` markers.

**Empirical check:** the current `data/artifacts/clause-index.json` contains 1,755 clauses across 9 documents. Every single document is a BNM PD (RMiT, BCM, Recovery Planning, Customer Info, Outsourcing, Open Finance ED, OpRes DP, AI DP). Zero non-BNM documents. This isn't accidental — the parser hasn't been fed non-BNM docs because it fundamentally cannot parse them.

**Could the regex be loosened to accept non-BNM shapes?** Yes, but doing so is a real engineering mistake in two directions:

1. **False positives on BNM docs.** The strict regex exists because BNM PDs are dense with in-text references to other clause numbers ("as required under paragraph 10.4…"). Loosening the regex to accept HKMA-style numbering would cause the parser to hallucinate clause boundaries mid-paragraph on BNM docs, breaking every calibrated test in `engine/tests/test_clauses.py` and corrupting known-good ingestion.

2. **Structurally-wrong "clauses" on non-BNM docs.** Even if we got the regex to fire on HKMA lines, the resulting "clauses" would encode false parent/child relationships. `HKMA OpenAPI 11.2` in the source PDF is a _sub-heading of a section on API function categories_ — not a sub-clause of `HKMA OpenAPI 11`. Treating it as the latter (which the clause parser's structural inference would do) fabricates a hierarchy the source doesn't have. Yenmay's `semi-structured` segmenter avoids this by walking the heading tree explicitly.

**Position stated cleanly:** dzaf's `segment_clauses` is a well-designed, specialised parser for the BNM PD template. It is not broken; it is scope-limited by design. AnchorIndex with its three segmenter strategies (`structured-rules`, `semi-structured`, `prose`) is a scope expansion, not a correction. The old regex parser is preserved verbatim as the `structured-rules` strategy in `engine/anchors.py`.

**Consequence for this experiment.** Running the current engine (ClauseIndex + `find_connections`) on BIS Pap 168 × ED or HKMA 2018 × ED would produce empty output: the ClauseIndex has no entries for BIS or HKMA, so the finder receives empty B-side context and returns nothing. That is a definitional non-run, not experimental evidence. We drop the baseline arm and open the experiment at the AnchorIndex level.

## Hypothesis

The cross-jurisdiction pairs benefit progressively from three enhancements — anchor IDs, semantic retrieval, and hybrid retrieval with glossary aliases. We hypothesise:

- **AnchorIndex alone (Arm B)** produces high-recall / high-yield findings on both pairs by giving the finder clean anchor IDs to cite, but may miss subtle same-axis-different-vocabulary pairs.
- **Cosine-only retrieval (Arm C)** improves recall on same-axis-different-vocabulary pairs (e.g. "conforming loan" ≡ "Level C loan") over Arm B, at the cost of one axis-extraction call per anchor (cached).
- **Full hybrid retrieval (Arm D)** further improves recall via BM25 keyword matching (catches jargon-heavy pairs cosine misses) and glossary alias expansion (catches known cross-jurisdiction equivalences).

If B suffices, Options 1 ships. If D dominates, Option 2 justifies the build cost. If C ≈ D, Option 1.5 is the honest choice.

## Test pairs

Both are demo-critical cross-jurisdiction pairs the pitch depends on landing:

- **BIS Working Paper 168 × BNM Open Finance ED 2025** — 60 anchors + 127 anchors. BIS document is a working paper (semi-structured segmentation). Yenmay's pre-experiment run produced 16 supported findings, 0 unsupported. The pitch-critical finding is the payment-initiation `differs-on / neutral` — BIS notes write-access globally, BNM's ED is read-only.
- **HKMA Open API Framework 2018 × BNM Open Finance ED 2025** — 89 anchors + 127 anchors. HKMA is heading-driven (semi-structured). Pre-experiment run produced 24 supported findings, 0 unsupported. The pitch-critical finding is the `differs-on / tighten` on mandatoriness — BNM binding vs HKMA voluntary.

## Arms

Five arms measured on both pairs. Arms C and D require a real embedding endpoint (Azure OpenAI or local sentence-transformers); Arms B/E/F need neither and can run against just the anchor index + hand-authored glossary. **Execution note (21 Jul 2026):** Arms E and F were added mid-experiment when we discovered the environment had no embeddings endpoint configured. Rather than substitute or fake the cosine signal, we split the retrieval hypothesis into "keyword-only" (E/F) and "keyword + semantic" (C/D) so each arm tests one signal cleanly. Decision on C/D deferred until an embeddings endpoint is available; E/F land in the meantime and may prove sufficient to pick the shipping option.

### Arm B — AnchorIndex + whole-doc pairwise (Option 1)

```
AnchorIndex → finder(anchors_a_all, anchors_b_all)
            → critic(finder_output, anchors_a_all, anchors_b_all)
            → validate(critic_output, AnchorIndex)
            → connections + unsupported
```

Isolates the value of AnchorIndex alone. Same finder → critic → validate loop the current engine uses, but the finder sees clean anchor IDs (`Open Finance ED 11.5`, `HKMA OpenAPI 8.2`) and full anchor text for both documents in one prompt.

Cost per pair: 2 large LLM calls.

### Arm C — Cosine-only retrieval + per-pair finder (Option 1.5)

```
Axes extracted per anchor (1-5 phrases in canonical regulatory language, cached to disk)
Axes embedded via text-embedding-3-small (cached alongside axes JSON)
For each anchor on side A:
  candidate_pairs += top-K by cosine similarity over embedded axes against side B
De-duplicate to unique (source_anchor_id, target_anchor_id) pairs
For each candidate pair:
  finder(pair)  → per-pair judgment call
  critic(finder_output, pair)
  validate(critic_output, AnchorIndex)
```

Isolates the value of _any_ retrieval step. Uses purely semantic similarity (dense-vector cosine) — no keyword signal, no glossary.

Cost per pair: 1 axis extraction call per anchor (cached across runs), N candidate-pair finder+critic calls where N is bounded by top-K per source anchor.

Parameters:

- Top-K per source axis: 3
- Similarity floor: 0.55
- Embedding model: OpenAI `text-embedding-3-small`

### Arm D — Hybrid BM25 + cosine + glossary + per-pair finder (Option 2)

```
Axes extracted per anchor (same as Arm C, cache shared)
For each anchor on side A:
  expanded_queries = axes + glossary_aliases(axes)
  bm25_hits = BM25 over side B's axes for expanded_queries
  cosine_hits = cosine over side B's axis embeddings for expanded_queries
  candidate_pairs += reciprocal_rank_fusion(bm25_hits, cosine_hits, top-K, floor)
De-duplicate to unique (source_anchor_id, target_anchor_id) pairs, keep best fusion score + earliest matching axis
For each candidate pair:
  finder(pair)
  critic(finder_output, pair)
  validate(critic_output, AnchorIndex)
```

Adds keyword and alias signals over Arm C. Reciprocal-rank-fusion combines BM25 rank + cosine rank into a single score per pair. Glossary expansion catches known cross-jurisdiction equivalences that neither BM25 nor cosine alone would surface.

Cost per pair: same axis extraction (cache reused), N candidate-pair finder+critic calls. BM25 and cosine are deterministic and cheap.

Parameters:

- BM25: `rank-bm25` with default parameters, tokenisation via whitespace + lowercase.
- Cosine: same as Arm C.
- RRF constant `k`: 60 (industry default per Cormack et al. 2009).
- Top-K per source axis after fusion: 3
- Similarity floor after fusion: 0.5 (rank-based; not directly comparable to Arm C's cosine floor)
- Glossary: `data/glossary.json`, hand-authored, ~20 entries covering known cross-jurisdiction aliases for the demo corpus. Includes entries relevant to open-finance (KYC ↔ CDD, PISP ↔ payment initiation ↔ write access, TSP ↔ third-party provider, mandated FSP ↔ ASPSP, etc.).

### Arm E — BM25-only retrieval + per-pair finder (no cosine, no glossary)

```
Axes extracted per anchor (reuses the Arm C/D cache)
For each anchor on side A:
  For each axis on side A:
    bm25_hits = BM25 over side B's axes for that axis (raw, no expansion)
  candidate_pairs += top-K per (source anchor, source axis) by BM25 score
De-duplicate to unique (source_anchor_id, target_anchor_id) pairs, keep best BM25 score
For each candidate pair:
  finder(pair)
  critic(finder_output, pair)
  validate(critic_output, AnchorIndex)
```

Isolates the value of keyword-overlap retrieval alone. No embedding step, no glossary expansion. This is the cheapest retrieval arm to run — BM25 is pure Python, no LLM cost beyond axis extraction (cached).

Cost per pair: axis extraction (cached), N candidate-pair finder+critic calls where N is bounded by top-K per source axis.

Parameters:

- BM25: `rank-bm25` with default parameters, tokenisation via whitespace + lowercase.
- Top-K per source anchor after fusion of its axes' hits: 3
- BM25 score floor: none (top-K per anchor caps volume already; a floor may re-introduce zero-signal blind spots)

**Interpretation guide:**

- If E ≥ B on precision and demo-critical findings, keyword retrieval alone was enough to beat whole-doc prompting. Cosine may still add value but the base retrieval story ships without it.
- If E ≪ B, keyword-only retrieval isn't enough to make per-pair prompting worthwhile — the finder needs cross-document context (from Arm B) or semantic signal (from Arms C/D).

### Arm F — BM25 + glossary + per-pair finder (no cosine)

```
Axes extracted per anchor (reuses the Arm C/D cache)
Glossary loaded from data/glossary.json
For each anchor on side A:
  For each axis on side A:
    expanded_query = " ".join(axis + glossary_aliases(axis))
    bm25_hits = BM25 over side B's axes for expanded_query
  candidate_pairs += top-K per (source anchor, source axis) by BM25 score
De-duplicate to unique (source_anchor_id, target_anchor_id) pairs
For each candidate pair:
  finder(pair)
  critic(finder_output, pair)
  validate(critic_output, AnchorIndex)
```

Isolates the incremental value of glossary alias expansion over Arm E's plain BM25. If F > E on demo-critical findings, the glossary earns its keep as a source of cross-jurisdiction recall even in a keyword-only retrieval setup — which is exactly the argument the retrieval-pipeline spec makes for the hybrid approach.

Cost per pair: same as Arm E (axis extraction cached, N finder+critic calls). BM25 + glossary expansion adds no LLM cost.

Parameters:

- BM25: same as Arm E.
- Glossary: `data/glossary.json` (same file Arm D would use).
- Top-K per source anchor after fusion of its axes' hits: 3

## Metrics

Six metrics per arm × pair. Recorded to a single spreadsheet at `experiments/retrieval-ablation-results.csv` for the final judgment pass.

| Metric                            | How measured                                                                                                                                                                                                                                | Why it matters                                                                                                           |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Supported count**               | `len(findings)` from the emitted results file                                                                                                                                                                                               | Raw output volume                                                                                                        |
| **Unsupported ratio**             | `len(unsupported) / (len(supported) + len(unsupported))`                                                                                                                                                                                    | Citation hygiene — proxy for LLM confusion. Lower is better.                                                             |
| **Label diversity**               | Count of distinct labels in the five-value set (`aligns-with`, `differs-on`, `conflicts-with`, `silent-on`, `goes-beyond`) that appear in `findings`. Range 1-5.                                                                            | Are we surfacing the full taxonomy or collapsing everything into `aligns-with`?                                          |
| **Demo-critical finding present** | Binary. Read the summary of every `findings` entry. Answer `yes` if any finding matches the pitch-critical topic for that pair (BIS × ED: payment-initiation write-access divergence; HKMA × ED: mandatory-vs-voluntary regime divergence). | The pitch-relevant findings the arm must produce.                                                                        |
| **Human-judged precision @ 10**   | Random sample of 10 supported findings per arm × pair. Human reads each and marks "genuine linkage" or "false positive." Precision = genuine / 10.                                                                                          | The actual value the drafter gets. Sanity check that high supported-count isn't inflated with weak or spurious findings. |
| **Wall-clock latency**            | Seconds from `analyze` start to findings written to disk                                                                                                                                                                                    | Demo-critical — 30s is fine, 3min is not. Affects whether the arm can run live on stage or must be pre-computed.         |

Cost (in dollars, based on the run's token counts) is tracked in the spreadsheet but not weighted in the decision — the demo's total LLM budget is small enough that any of the arms is affordable.

## Decision rule

Rank the five arms by the following priority chain. Choose the highest-ranked arm that clears the bar, where "clears" means "meets the minimum" not "wins by the largest margin."

1. **Demo-critical finding present** — arms that surface the pitch-critical finding cleanly rank above arms that don't. Binary priority — an arm that fails here is out of the running regardless of other metrics.
2. **Human-judged precision @ 10 ≥ 0.7** — an arm that produces findings that aren't at least 70% genuine on manual inspection is unshippable regardless of volume.
3. **Label diversity ≥ 3** — an arm that collapses everything into one or two labels isn't showing the taxonomy that the pitch depends on. Below 3, the tool looks like keyword matching.
4. **Wall-clock latency ≤ 120s** — an arm that takes longer than two minutes can't run live on stage during the demo without awkward silence. Above 120s, it becomes pre-computed only.

Ties on the priority chain break to **simplicity of build effort**. Arm B is trivial; Arm E is a day (BM25 + axis extraction); Arm F is Arm E plus glossary wiring (~2 hours on top); Arms C and D each add embeddings infrastructure and a day of work. If two arms tie on all priority checks, ship the simpler one.

**Decision matrix (updated to include Arms E and F):**

- If **Arm B clears all bars** on both pairs: ship Option 1 (AnchorIndex swap only). Skip the retrieval pipeline build. The pitch story becomes "AnchorIndex alone was sufficient."
- If **Arm B misses one or more bars but Arm E clears all bars**: ship a keyword-only retrieval pipeline. Build cost ~1 day. This is a stripped-down Option 1.5 — real retrieval, no embedding infrastructure. Well-suited to a corpus with jargon-heavy anchors (regulatory language).
- If **Arm E misses bars but Arm F clears them**: ship BM25 + glossary. Same build cost as E plus a small glossary loader. The glossary earned its keep.
- If **Arms E and F both miss bars**: run Arms C and D (need embeddings endpoint or sentence-transformers). The keyword-only retrieval isn't sufficient — semantic similarity is required.
- If **Arm C or D clears all bars** where E and F did not: ship Option 1.5 or Option 2 with real embeddings.
- If **all five arms miss bars:** flag as a hackathon-blocker. The retrieval pipeline as designed isn't enough for cross-jurisdiction; step back and reconsider the demo shape.

**Sequencing note.** Arms B, E, and F are all runnable today (no embedding infrastructure needed). Run those three first, apply the decision matrix. Only escalate to Arms C and D if the first three don't yield a clear winner.

## Execution

### Runner script

`scripts/experiments/retrieval_ablation.py` — self-contained, doesn't touch anything on the staging tree beyond writing results to `experiments/` (gitignored). CLI shape:

```bash
python scripts/experiments/retrieval_ablation.py --arm B --pair bis-ed
python scripts/experiments/retrieval_ablation.py --arm C --pair hkma-ed
python scripts/experiments/retrieval_ablation.py --arm all --pair all
```

Writes per-run:

- `experiments/retrieval-ablation/{arm}/{pair}/findings.json` — the supported + unsupported findings, same shape as production
- `experiments/retrieval-ablation/{arm}/{pair}/trace.json` — full audit trail including finder / critic outputs, retrieval candidate list (arms C, D), axis cache reference
- `experiments/retrieval-ablation/{arm}/{pair}/metadata.json` — wall-clock, token counts, LLM cost estimate, random seed

Also writes an aggregate spreadsheet `experiments/retrieval-ablation-results.csv` after all six runs, one row per (arm, pair), columns for every metric above except human-judged precision (which is filled in by hand afterwards).

### Order of execution

- **Ordering rule.** Randomize arm-per-pair order to control for LLM non-determinism from run sequencing.
- **Temperature.** All arms run at `temperature=0`.
- **Axis extraction cache.** One axis pass over each of the 3 documents (BIS Pap 168, HKMA OpenAPI, Open Finance ED) at the start. Cached at `experiments/axes-{document_id}.json`. Arms C and D share this cache.
- **Failure handling.** Any arm that fails (LLM timeout, empty finder output, unresolvable citation) records the failure in metadata and continues to the next arm. Doesn't abort the whole experiment.

### Budget

- Axis extraction (one-time): 276 anchors total (127 + 89 + 60) × 1 small LLM call each ≈ $0.20.
- Arm B: 2 large LLM calls per pair × 2 pairs = 4 calls ≈ $2.
- Arm C: ~30 candidate pairs per pair × 2 pairs × 2 LLM calls per pair = ~120 small calls ≈ $2.
- Arm D: similar to Arm C, +/- ~15% depending on how many pairs the fusion surfaces ≈ $2.
- **Total: ~$6-7 in tokens, ~2-3 hours wall-clock, ~40 minutes human judgment at the end.**

### Human judgment pass

After all six runs complete, the aggregate spreadsheet has 5 of the 6 metric columns filled. The human-judged precision column requires ~40 minutes of drafter time:

- For each arm × pair (6 cells), randomly select 10 supported findings.
- Read each finding's summary + cited anchor text on both sides.
- Mark "genuine linkage" (the two anchors really do speak to a shared axis or coverage asymmetry that matches the label) or "false positive" (the finding is confused, wrong-label, or the two anchors don't actually relate).
- Compute precision = genuine / 10 per cell.

## Dependencies

- **Existing:** `engine/anchors.py`, `data/artifacts/anchor-index.json` (with ED, HKMA 2018, BIS Pap 168 all indexed at anchor-level), `engine/connections.py` `find_connections` (as the AnchorIndex-compatible variant — needs a small refactor for Arm B and per-pair invocation for Arms C, D).
- **New dependencies (in `pyproject.toml`):** `rank-bm25`, `numpy` (already listed), `openai` (already listed for embeddings).
- **New file:** `data/glossary.json` — curated for the open-finance demo corpus, ~20 entries. Owned by a subject-matter expert if possible; drafter-authored as a fallback. Only used by Arm D.

## Deliverables

- Runner script `scripts/experiments/retrieval_ablation.py`
- Axis extraction cache under `experiments/axes-{document_id}.json` (reusable for later work)
- Six results directories under `experiments/retrieval-ablation/{arm}/{pair}/`
- Aggregate spreadsheet `experiments/retrieval-ablation-results.csv`
- Written recommendation (this file, updated with results section) naming which option to ship

## Open questions to resolve during execution

- [ ] Does Arm B's finder handle 216 anchors (127 + 89) in one prompt without truncating or missing pairs? If yes, cosine/hybrid retrieval may add less than expected.
- [ ] Does the glossary meaningfully improve Arm D over Arm C, or is the open-finance corpus too heavily BNM-vs-BNM-adjacent for cross-vocabulary aliases to fire? Only 6-10 of the ~20 glossary entries are likely to actually be relevant to this specific demo pair — future work will reveal whether the glossary earns its keep on other domains.
- [ ] Is human-judged precision on Arm B's 24 HKMA×ED findings materially different from Arm D's? The pre-experiment run produced 24 findings under similar-to-Arm-B conditions; if precision was already high, the retrieval enhancements may show diminishing returns.
