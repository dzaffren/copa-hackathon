# Document → Knowledge-Graph Extraction: Prior Art for Rulebook Radar

**Status:** Research report (deep, multi-source, adversarially verified)
**Date:** 2026-07-08
**Method:** 5-angle fan-out web search → 22 primary/blog sources fetched → 103
falsifiable claims extracted → top 25 verified by 3-vote adversarial panel (a
claim needs 2/3 refutes to be killed) → 23 confirmed, 2 killed → synthesised.
104 agents total.
**Scope:** How doc→KG extraction is done, with emphasis on regulatory/legal/
financial-compliance corpora that demand verbatim citation and anti-hallucination
guarantees — positioned against the [knowledge-graph engine
spec](../../specs/rulebook-radar/spec-knowledge-graph-engine.md). Companion to
that spec's "Prior Art" and "graphify Reuse Evaluation" sections; this is the
deeper, fully-cited version.

---

## Bottom line

Prior art **strongly validates two** of Rulebook Radar's three core choices,
**challenges the third's precedent** (not its soundness), and **reveals one gap**
worth an explicit design decision.

1. **Clause as the atomic unit + typed inter-clause edges — VALIDATED** by
   dedicated legal/compliance KG research, and a **genuine departure** from every
   mainstream doc→KG system (all chunk generically).
2. **Avoiding LLM-generated payload text (anti-hallucination goal) — VALIDATED**:
   multiple legal-KG teams deliberately reject generative LLMs for legally
   consequential extraction; measured LLM extraction accuracy (~91%) is
   categorically below a deterministic verbatim guarantee.
3. **The specific mechanism** (LLM emits boundaries/numbers only → code slices the
   verbatim substring → finder→critic→code-verifier drops unresolvable citations)
   — **well-motivated but largely unprecedented.** No surveyed system implements
   it. Prior art validates the _goal_ more than the _mechanism_. This is a
   defensible novelty claim, not a gap.
4. **The gap:** cross-reference resolution is an unsolved, hard problem
   (best Recall@10 = 55–59% on the CRAwLeR benchmark). This bears directly on the
   finder→critic→verifier loop, and "drop unresolvable citation vs. flag for human
   review" is an unmade design decision for a supervisor workflow.

---

## 1. Canonical doc→KG / GraphRAG systems

All four mainstream systems share two properties that Rulebook Radar deliberately
inverts: they **chunk generically** and they **let the LLM author the payload
text**.

| System                              | Chunk unit                                                                      | Extraction                                                                                                                   | Provenance model                                                                                          | Retrieval                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Microsoft GraphRAG**              | fixed **TextUnit, default 1200 tokens** (token/sentence only; no clause option) | LLM extracts entities+relationships+claims; LLM re-summarises merged descriptions; LLM **pre-generates community summaries** | TextUnit "breadcrumbs" back to source; payload is model-generated                                         | **global** = map-reduce over LLM community summaries; **local** = retrieves raw source chunks |
| **LightRAG**                        | Fix / Recursive / Vector / **Paragraph** (all generic)                          | dedicated EXTRACT LLM role → JSON entity-relation                                                                            | chunk-linked                                                                                              | dual-level local/global; no community reports (cheaper)                                       |
| **Neo4j LLM Graph Builder**         | chunk nodes (embedded, kNN-linked)                                              | `llm-graph-transformer` (LangChain) → Node/Relationship objects, general-purpose LLMs                                        | **two-layer graph**: lexical (docs+chunks) + entity graph; entities "connected to the originating Chunks" | GraphRAG + vector + Text2Cypher                                                               |
| **LlamaIndex Property Graph Index** | per-chunk (`kg_extractors` run "on each chunk")                                 | LLM-extracted entities/relations as node metadata                                                                            | source chunk inserted as node via `HAS_SOURCE`; `include_text=True` returns verbatim chunk                | sub-retrievers (vector, LLM-synonym, Cypher)                                                  |

**Verified findings (all high-confidence unless noted):**

- **Generic chunking, never legal-clause.** _(GraphRAG 3-0, LightRAG 3-0,
  LlamaIndex 3-0.)_ GraphRAG's 1200-token TextUnit is the clearest counterexample
  to clause-level chunking. Boundary-adherence in GraphRAG means _document_
  boundaries, not semantic clauses.
- **Full payload delegated to the LLM.** _(GraphRAG 3-0, LightRAG 3-0, Neo4j 3-0,
  LlamaIndex 3-0.)_ Every system's node/edge text is model-generated — the direct
  opposite of boundary-only-then-code-slice.
- **Provenance = reference-to-chunk breadcrumb, not verbatim-clause guarantee.**
  _(GraphRAG 3-0; global-vs-local 2-1.)_ The closest analogs to keyed-source
  retrieval are **LlamaIndex `include_text=True`** (default `False`) and
  **GraphRAG local search** (retrieves raw chunks) — both return raw _chunks_, not
  verbatim _clauses_, and neither guarantees the payload wasn't model-authored.

> **Caveat (from the verifier panel):** do not overstate GraphRAG as purely
> summary-based — global search is map-reduce over LLM summaries, but local search
> _does_ retrieve raw source chunks. The 2-1 vote on the provenance claim reflects
> exactly this global/local nuance.

Sources: [GraphRAG paper (arXiv 2404.16130)](https://arxiv.org/abs/2404.16130),
[GraphRAG docs](https://microsoft.github.io/graphrag/),
[LightRAG](https://github.com/HKUDS/LightRAG),
[Neo4j LLM Graph Builder](https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/),
[LlamaIndex LPG guide](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/).

## 2. Legal / regulatory-specific KG work

This is where Rulebook Radar's clause-centric design finds its real peers — none
of the generic GraphRAG systems, but a cluster of 2024–2026 legal-KG papers.

- **COMPACT (EACL 2026)** — _validates the clause-graph substrate._ Models
  contract compliance by "constructing structured clause graphs," extracting
  "deontic-temporal entities from clauses" and building "typed relationship graphs
  capturing definitional dependencies, exception hierarchies, and temporal
  sequences" — explicitly "rather than treating clauses in isolation." _(2-1; the
  dissent was over a sibling ACE-accuracy claim, not the clause-graph claim.)_
  **Scope caveat:** COMPACT operates over commercial contracts with LLM-extracted
  entities — it validates the typed-clause-graph idea but **not** verbatim
  code-slicing. [aclanthology.org/2026.eacl-long.377](https://aclanthology.org/2026.eacl-long.377/)
- **GraphCompliance (arXiv 2510.26309, WWW 2026 under review)** — _offers a
  technique Rulebook Radar is missing._ Two aligned graphs: a **policy graph** that
  "encodes normative structure and cross-references" + a **context graph** of
  subject-action-object triples. Its grounding mechanism is **graph alignment**:
  anchoring an LLM-judge in the structured graphs "reduce[s] the burden of
  regulatory interpretation… enabling a focus on the core reasoning step" (+4.1–7.2
  pp micro-F1 over LLM-only and RAG baselines). _(3-0.)_ **Caveat:** the paper's own
  framing is "grounding for reasoning," not "anti-hallucination" — treat that framing
  as a mild editorial extrapolation. Still a preprint. [arXiv 2510.26309](https://arxiv.org/abs/2510.26309)
- **Hairurahman et al. (Artificial Intelligence and Law, Springer, 2026)** —
  _validates the anti-hallucination goal, but not code-slicing._ States plainly:
  "Generative LLMs are vulnerable to hallucinations, plausible but factually
  unsupported outputs, which are unacceptable when extracting legally consequential
  facts." Their answer is a **hybrid: rule-based extraction for structured sections
  (precision + full auditability) + fine-tuned local BERT for narratives.** _(3-0.)_
  **Important:** a claim that this paper enforces verbatim token-offset provenance
  with zero generative summarisation was **REFUTED 0-3** — it is a rule+BERT hybrid,
  **not** a verbatim-slice system. Do not cite it as validating code-slicing
  specifically; cite it for the _reject-generative-LLM_ stance.
  [Springer 10.1007/s10506-026-09507-8](https://link.springer.com/article/10.1007/s10506-026-09507-8)
- **JKEM / CLKG (Li et al., Information 2024, 15(11):666)** — _quantifies why LLM
  extraction ≠ a guarantee._ A knowledge-enhanced prefix-tuned LLM legal-KG
  extractor reaches "90.92%" extraction accuracy — i.e. ~9% can be wrong. Atomic
  unit is the RDF-style triple over a rigid 9-entity/2-relation schema (3480
  triples). _(3-0.)_ **Caveat:** 90.92% is a test-set metric, so "~9% wrong" is a
  simplification of population error, but the direction is sound; "RDF-style" is an
  inference (full text was fetch-blocked). [MDPI 15/11/666](https://www.mdpi.com/2078-2489/15/11/666)
- **CO2 (Co-Compliance Officer, IEEE 2025)** — _an alternative pattern._
  Ontology-driven LLM extraction: LLMs + a legal-document ontology extract
  subject-relation-object triplets, enhanced with legal NER tags and dependency
  parsers. LLM-generated triplets constrained by an ontology, rather than
  code-sliced spans. _(3-0, medium confidence — IEEE Xplore bot-blocked, corroborated
  via Scholar fragments.)_ [IEEE 11271718](https://ieeexplore.ieee.org/abstract/document/11271718/)
- **CRAwLeR (Jałocha & Michelsen, arXiv 2606.21676, June 2026)** — _the gap._
  Cross-reference-aware legal retrieval benchmark: "the benchmarks are hard but not
  solved: best Recall@10 reaches 55% on CRAwLeR-DK and 59% on CRAwLeR-PL." _(3-0.)_
  **Nuance:** authors attribute much of the gap to the query-generation LLM rather
  than the retriever, so "at retrieval time" slightly oversimplifies — but
  "cross-reference resolution is hard/unsolved" is the authors' own framing.
  [arXiv 2606.21676](https://arxiv.org/abs/2606.21676)

**Central-bank / BIS:** [BIS Project Gaia](https://www.bis.org/about/bisih/topics/suptech_regtech/gaia.htm)
is the closest _intent_ peer (a central-bank tool extracting structured, auditable
facts from regulatory disclosures at scale). No BNM-specific or other central-bank
_knowledge-graph_ effort was confirmed — the BNM-specific prior-art question stays
open (see Open Questions).

## 3. Techniques for guaranteeing verbatim quotation / preventing hallucinated citations

The single most useful section for what Rulebook Radar is **missing**. These
surfaced on the anti-hallucination angle and are **not yet reflected in the engine
spec**:

- **`verbatim-rag` (KRLabsOrg)** — an open-source RAG system whose explicit design
  goal is to return **only spans that literally appear in the retrieved source**,
  preventing the generation model from paraphrasing or fabricating. This is the
  **closest external analog to Rulebook Radar's code-slice guarantee** and the best
  starting point for anyone questioning whether the approach is sane.
  [github.com/KRLabsOrg/verbatim-rag](https://github.com/KRLabsOrg/verbatim-rag)
- **Anthropic Citations API** — a production feature that returns cited spans
  resolved back to exact source locations, so the model's claims are tied to source
  passages rather than free-generated. Directly relevant since the engine already
  runs on Claude (Azure Foundry). Worth evaluating as a **belt-and-suspenders** layer
  on the finder/critic output — though note it cites _retrieved passages_, so it
  complements rather than replaces the clause-index keyed lookup.
  [claude.com/blog/introducing-citations-api](https://claude.com/blog/introducing-citations-api)
- **ALCE (arXiv 2305.14627)** — "Enabling LLMs to Generate Text with Citations": the
  standard **attribution/grounding evaluation** framework (citation recall +
  precision). Answers the open question of _how to prove_ the verbatim-citation
  guarantee holds, not just assert it.
  [arXiv 2305.14627](https://arxiv.org/abs/2305.14627)
- **EMNLP 2025 Industry track citation-grounding work** and a
  [practitioner citation-grounding writeup](https://neelmishra.github.io/blog/mlops/rag/citation-grounding.html)
  round out the applied techniques. [aclanthology.org/2025.emnlp-industry.54](https://aclanthology.org/2025.emnlp-industry.54/)

**Takeaway:** Rulebook Radar's extraction-time guarantee (code slices verbatim) is
stronger than any of these at _ingestion_, but it has **no attribution-evaluation
methodology** and **no grounding layer on the reasoning/answer step**. `verbatim-rag`
and the Citations API are candidate patterns for the copilot (#9) answer path;
ALCE is the candidate evaluation harness.

## 4. Clause/section chunking vs fixed-size — why the departure is right

- Legal-RAG practitioner guidance converges on **structure-aware / clause-level
  chunking** for reference documents, because fixed-size windows sever
  cross-references and split requirements mid-clause.
  ([edtek.ai](https://edtek.ai/kb/chunking-strategies-legal-reference-documents/),
  [ipchimp.co.uk](https://ipchimp.co.uk/2024/02/16/rag-for-legal-documents/))
- Academic chunking studies ([arXiv 2402.05131](https://arxiv.org/abs/2402.05131),
  [Springer IR 10.1007/s10791-025-09638-7](https://link.springer.com/article/10.1007/s10791-025-09638-7))
  confirm chunk-boundary choice materially affects retrieval faithfulness — and that
  semantic/structural boundaries beat fixed windows for structured documents.
- Yet **every canonical GraphRAG system ships only generic chunkers** (§1). So the
  clause-as-chunk decision is simultaneously (a) endorsed by legal-domain best
  practice and (b) absent from the mainstream tooling — i.e. correctly identified as
  something the engine had to build itself.

## What Rulebook Radar should consider adding

Ranked by leverage for the hackathon and beyond:

1. **An attribution-evaluation harness (ALCE-style).** Turn the verbatim guarantee
   from an asserted invariant into a _measured_ one: citation-resolution rate,
   hallucinated-citation rate (should be 0 by construction — prove it), verbatim
   fidelity. Cheap to add, strong pitch-defence for "is this real AI?".
2. **Decide drop-vs-flag for unresolvable citations.** CRAwLeR shows cross-reference
   resolution is unsolved (55–59% Recall@10). The current loop **drops** any
   connection citing an unresolvable clause — maximising precision. For a
   **supervisor** workflow, a _missed_ requirement is the dangerous error, so
   consider **flag-for-human-review** as an alternative to silent drop for
   near-miss citations. This is a genuine, unmade design decision.
3. **Graph-alignment grounding for the reasoning step (GraphCompliance pattern).**
   The engine grounds _extraction_; it does not yet ground the finder/critic
   _reasoning_ in a structured graph beyond passing clause text. Anchoring the
   critic in the typed edge graph (overlaps/references/depends-on) is a documented
   +4–7 pp technique.
4. **A grounding layer on the copilot answer path (verbatim-rag / Citations API).**
   The clause index guarantees ingestion fidelity; #9's free-text answers need the
   same discipline at generation time.

## Honest caveats (from the verifier panel)

- **Two claims were killed.** (a) "Multi-clause reasoning… 34–57% base accuracy on
  ACE, +22–43 pp from graph training" — refuted 1-2 (numbers not reliably sourced).
  (b) "Hairurahman et al. enforce verbatim token-offset provenance with zero
  generative summarisation" — refuted 0-3 (it's a rule+BERT hybrid). Neither is used
  as support above.
- **Recency risk.** COMPACT (EACL 2026), GraphCompliance (Oct 2025 preprint, not yet
  peer-reviewed), Hairurahman (Apr 2026), CRAwLeR (Jun 2026) are all very recent;
  figures/framing may shift.
- **Two fetch-blocked sources** (MDPI 403, IEEE 418) were corroborated via Scholar/
  CrossRef, lowering CO2 to medium confidence and making "RDF-style" an inference.
- **No system implements Rulebook Radar's exact mechanism.** The design is
  well-motivated by the anti-hallucination literature but largely unprecedented —
  prior art validates the _goal_ more than the specific _mechanism_.

## Open questions this research did not close

1. Does any system implement the exact "LLM emits boundaries/IDs only, code slices
   verbatim substring" pattern, or a _formally verifiable_ verbatim-quotation
   guarantee (constrained decoding to source spans, span-copy pointer networks)?
   Appears under-explored — worth a dedicated search.
2. Is drop-vs-flag-for-review the right default for unresolvable citations in a
   supervisor/drafter workflow, given the CRAwLeR recall ceiling?
3. Any BNM / central-bank / BIS-specific KG effort beyond Project Gaia that this
   sweep missed?
4. What attribution/grounding evaluation methodology should prove the
   verbatim-citation guarantee holds (automated citation-resolution checks, human
   attribution audits, faithfulness metrics)?

---

### Sources (22 fetched; primary unless noted)

GraphRAG [paper](https://arxiv.org/abs/2404.16130) ·
[docs](https://microsoft.github.io/graphrag/) ·
[LightRAG](https://github.com/HKUDS/LightRAG) ·
[Neo4j LLM Graph Builder](https://neo4j.com/labs/genai-ecosystem/llm-graph-builder/) ·
[LlamaIndex LPG](https://developers.llamaindex.ai/python/framework/module_guides/indexing/lpg_index_guide/) ·
[COMPACT (EACL 2026)](https://aclanthology.org/2026.eacl-long.377/) ·
[GraphCompliance (arXiv 2510.26309)](https://arxiv.org/abs/2510.26309) ·
[JKEM/CLKG (MDPI)](https://www.mdpi.com/2078-2489/15/11/666) ·
[Hairurahman et al. (Springer)](https://link.springer.com/article/10.1007/s10506-026-09507-8) ·
[CRAwLeR (arXiv 2606.21676)](https://arxiv.org/abs/2606.21676) ·
[CO2 (IEEE)](https://ieeexplore.ieee.org/abstract/document/11271718/) ·
[verbatim-rag](https://github.com/KRLabsOrg/verbatim-rag) ·
[ALCE (arXiv 2305.14627)](https://arxiv.org/abs/2305.14627) ·
[Anthropic Citations API](https://claude.com/blog/introducing-citations-api) ·
[EMNLP 2025 citation grounding](https://aclanthology.org/2025.emnlp-industry.54/) ·
[citation-grounding blog](https://neelmishra.github.io/blog/mlops/rag/citation-grounding.html) ·
[legal chunking (edtek)](https://edtek.ai/kb/chunking-strategies-legal-reference-documents/) ·
[legal RAG (ipchimp)](https://ipchimp.co.uk/2024/02/16/rag-for-legal-documents/) ·
[chunking study (arXiv 2402.05131)](https://arxiv.org/abs/2402.05131) ·
[chunking (Springer IR)](https://link.springer.com/article/10.1007/s10791-025-09638-7) ·
[RegTech (arXiv 2606.00898)](https://arxiv.org/abs/2606.00898) ·
[BIS Project Gaia](https://www.bis.org/about/bisih/topics/suptech_regtech/gaia.htm)
