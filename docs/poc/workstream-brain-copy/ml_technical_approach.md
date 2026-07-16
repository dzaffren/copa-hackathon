# ML/Technical Approach

## Table 1 — Core Issue → ML/Technical Approach

| # | Core Issue | Why It's Hard | Technique | Type |
|---|---|---|---|---|
| 1 | Scale — can't compare every clause to every other clause | O(n²) comparisons across a growing multi-cluster corpus | Bi-encoder embeddings + FAISS/pgvector dense retrieval (top-k candidates) | ML |
| 2 | Zero-tolerance hallucination — must quote exact clause or say "no match" | LLMs generate plausible-but-fabricated citations | Extractive selection (pick from retrieved spans, never free-generate) + faithfulness/groundedness verifier | ML + rules |
| 3 | Nuanced relationships — aligns / differs-↑ / differs-↓ / conflicts / silent / goes-beyond | Binary "similar/not similar" is too coarse | Natural Language Inference (NLI) classifier fine-tuned on clause pairs | ML |
| 4 | Domain specificity — "shall" ≠ "may", RTO/MTPD/TPSP are load-bearing | General-purpose models miss regulatory register | Domain-adaptive pretraining on BNM/BCBS/peer-regulator corpus | ML |
| 5 | Tighten vs. loosen severity — "annually" vs "biennial" | Requires understanding obligation strength + quantities, not just topic similarity | Deontic modal extraction + normalized quantity extraction + deterministic comparator | ML (extraction) + rules (compare) |
| 6 | Defensibility / explainability | Policymakers won't trust unexplainable output | Extractive spans + verbatim quoting + confidence scores surfaced in UI | ML + product |
| 7 | Version drift (e.g. RMiT 2023 vs 2025) | Looks like an ML problem but isn't | NER/relation extraction for citations → deterministic graph lookup | Rules (no LLM needed) |
| 8 | Cold start — near-zero labeled "conflict" data | Can't fine-tune without training data | Active learning from Accept/Dismiss actions in the review UI | ML (data flywheel) |
| 9 | Coverage gaps (supervisor checklist) | Proving a requirement is absent, not just present | Same retrieve→NLI spine, run per-requirement; no match above threshold = gap | ML |
| 10 | Undiscovered cross-workstream links | Drafters don't manually connect every relevant doc | Graph embeddings / GNN link-prediction over the knowledge graph | ML |

## Table 2 — Techniques → Where They Plug Into the Pipeline

| Pipeline Stage | Technique | Solves Issue # | Notes |
|---|---|---|---|
| 1. Ingestion | Layout-aware parsing (LayoutLMv3, Donut, Azure Doc Intelligence) | 4, 6 | Produces canonical clause IDs — precondition for verbatim citation |
| 2. Candidate generation | Bi-encoder + FAISS/pgvector (dense retrieval) | 1 | This is the "finder" — cheap, high recall |
| 3. Reranking | Cross-encoder on top-k shortlist | 1, 6 | Precision pass before anything hits an LLM/NLI model |
| 4. Relationship typing | NLI (DeBERTa-v3-style, fine-tuned) | 3 | entailment→aligns, contradiction→conflicts, neutral→goes-beyond/silent |
| 5. Severity comparison | Deontic strength + quantity extraction + comparator | 5 | The genuinely novel piece — explainable, not black-box |
| 6. Grounding check | Extractive-only generation + SummaC/QAGS-style faithfulness verifier or refutation-prompted LLM judge | 2, 6 | Architecturally prevents fabricated citations |
| 7. Reference resolution | NER + relation extraction + graph lookup | 7 | Deterministic — explicitly not ML-heavy |
| 8. Feedback loop | Active learning from Accept/Dismiss | 8, 3, 5 | Turns the review UI into a training-data engine over time |
| 9. Gap detection | Retrieve→NLI spine, inverted (absence = gap) | 9 | Reuses stage 2–4 machinery, different framing |
| 10. Discovery | Graph link-prediction (Node2Vec/GNN) | 10 | Powers the currently-stubbed "second-order neighbours" |

## Table 3 — If You Only Pitch Three Things

| Innovation | The Claim | Why Judges Care |
|---|---|---|
| Extractive + faithfulness-verified findings | "The system is architecturally incapable of citing a clause that doesn't exist" | Directly answers the #1 adoption blocker for AI in regulation — not just a UI promise, a structural guarantee |
| Deontic/quantitative tighten-loosen comparator | Explains why one clause is stricter than another, not just that they differ | Domain-specific, explainable, hard to fake with a generic LLM demo |
| Accept/Dismiss active-learning flywheel | Every reviewer action becomes training signal; precision compounds per institution | Turns a UI feature you already built into a genuine data moat |
