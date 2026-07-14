---
status: reference
last_updated: 2026-07-11
---

# Corpus Reality Note — what is real, what is mock, and the demo-scope fork

> Written 11 Jul 2026 during a pre-`/prd` document audit. Purpose: give an
> honest ledger of every document the project uses (real vs. mock/constructed),
> record two data-integrity bugs found, and lay out the effort delta between the
> two candidate demos so `/prd` scope can be chosen with full information. **No
> code was changed to produce this note** — it is ground truth read from
> `data/`, `engine/config.py`, and git.
>
> **UPDATE (later on 11 Jul 2026) — Option B chosen + DP successfully extracted.**
> The user chose **Option B (AI DP)** and clarified the product essence (see
> `brief.md` → "The one pain … broadened"): the hero is **connect scattered
> sources to an open document, then AI extracts guiding principles / judges
> consensus·conflict·gap·duplicate / surfaces unseen insights** — _not_ narrow
> align/deviate reconciliation. Consequently:
>
> - The real DP (`data/corpus/dp_ai_financial_sector.pdf`, Aug 2025) **extracted
>   cleanly** via the engine's own MarkItDown pipeline (79,666 chars, no gibberish)
>   → `data/artifacts/_ingest/dp-ai-financial-sector-2025.md`. Bug-#2 blocker
>   ("AI DP not in corpus") is **cleared**.
> - Its **real** citations were catalogued (not assumed): OECD (×14), BCBS/BCBS
>   239 (×9), FSB (×7), NIST (×6), MAS/FEAT (×5), Basel (×5), PDPA, EU AI Act,
>   plus MOSTI/NAIO (national AI governance). **It does NOT cite RMiT** — the
>   earlier "AI DP ↔ RMiT" hero edge was an assumption and is dropped.
> - The DP is a **discussion paper** (~54 numbered paras, ~1 obligation clause,
>   bibliographic footnotes). Under the _narrow_ reconciliation framing this was a
>   poor fit; under the _broadened_ essence it is an **excellent fit** — its
>   scattered cited sources are exactly the "pull in + link + analyse" story.
> - Effort-delta table below is retained for history but **superseded** by the
>   Option B decision; the DP extraction removed the largest Option B cost.

## Why this matters

The product's entire promise is **verbatim citation from real sources**. So the
one thing we cannot afford is to present a **constructed** document as if it were
a real published one. This note draws that line explicitly.

## The ledger — real vs. mock

### ✅ REAL — public documents, safe to quote verbatim

**BNM policy PDFs** (`data/corpus/`, from bnm.gov.my, tracked in git):

| File                                   | Document                          | Status               |
| -------------------------------------- | --------------------------------- | -------------------- |
| `pd-rmit-nov25.pdf`                    | Risk Management in Technology     | ✅ real (see bug #1) |
| `PD_Outsourcing_20191023.pdf`          | Outsourcing (2019)                | ✅ real published    |
| `PD-BCM.pdf`                           | Business Continuity Mgmt (2022)   | ✅ real published    |
| `dp_operationalresilience_Dec2025.pdf` | Operational Resilience (DP, 2025) | ✅ real (a real DP)  |
| `pd_Recovery Planning.pdf`             | Recovery Planning (2021)          | ✅ real published    |
| `MCIPD_PD_2025.pdf`                    | Customer Info / MCIPD (2025)      | ✅ real published    |

**External reference PDFs** (`data/references/`, public, tracked, verbatim-verified):

| File                                         | Source                              | Used in          |
| -------------------------------------------- | ----------------------------------- | ---------------- |
| `mas-trm-2021.pdf`                           | MAS TRM Guidelines §3.4.2           | Test B (GREEN)   |
| `pdpa-2010-act709.pdf` + `...a1727-2024.pdf` | PDPA §129 (2010 + 2024 amendment)   | Test A (GREEN)   |
| `basel-por-2021.pdf`                         | Basel Principles for Op. Resilience | reference corpus |

All quotes used in the two GREEN experiments came from these real files and were
checked word-for-word.

### ⚠️ MOCK / CONSTRUCTED — must never be presented as real

| Item                                           | What it actually is                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`data/mock/rmit-v2-2026-draft.md`**          | **Hand-authored mock draft** — the demo's "living draft". Clause **17.1 was manually bent to "notify-after"** to manufacture the hero conflict with Outsourcing 12.1. Correctly tagged `source:"draft"` from `MOCK_DIR` in `engine/config.py`, and its provenance note records `generation: llm-expanded from rmit-v1-2020; 17.x hand-authored`. **This is fiction — necessarily so** (you cannot demo editing a real published policy), but the briefs describe it more confidently than "a what-if with one clause bent." |
| `data/artifacts/_ingest/rmit-v2-2026-draft.md` | **Byte-identical copy** of the mock (same MD5) — looks like an extraction, isn't. Harmless (git-ignored build output), but don't mistake it for a real ingest.                                                                                                                                                                                                                                                                                                                                                              |
| `bnm-handbook` node                            | Confidential → **no text ever ingested**; node-only placeholder. ✅ handled correctly.                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `trend-cloud-signals` node                     | Labelled **preview** → no verbatim excerpt. ✅ handled correctly.                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

## Bugs found

### Bug #1 — the "RMiT v1 · 2020" label is factually wrong (data-integrity)

- **Symptom:** the corpus has one RMiT PDF, `pd-rmit-nov25.pdf`, whose own text
  says _"comes into effect on **28 November 2025**."_ But `engine/config.py`
  gives it `document_id: "rmit-v1-2020"`, `version: "v1 · 2020"`,
  `effective_date: "2025-11-28"`. So a **2025 document is labelled as the 2020
  version.** There is **no actual 2020 RMiT PDF** anywhere in the repo.
- **Reality:** BNM's RMiT was first issued ~2020 and **reissued 28 Nov 2025**.
  The team is using the **2025 reissue** to play the role of "the older
  superseded v1" in the demo's version-lineage story — but mislabels it "2020".
- **Impact:** anyone reading the graph sees an "RMiT v1 · 2020" node that does
  not correspond to a real 2020 document. For a product whose credibility rests
  on verbatim accuracy, presenting a mislabelled version to the DG/AG panel is a
  real risk.
- **Why NOT fixed live (11 Jul 2026):** `rmit-v1-2020` is a **`document_id` key**,
  not a display label — it appears 100+ times across `engine/config.py`, four
  test files (`test_api.py`, `test_clauses.py`, `test_graph.py`), the generated
  `data/artifacts/graph.json` + `clause-index.json`, and the specs. Renaming it
  is a code refactor + test update + artifact rebuild — out of scope for a
  discovery cleanup, and doing it mid-stream would risk a red build.
- **Recommended fix (scope into `/prd` or a dedicated task):** either
  **(a)** relabel to the truth — `version: "v1 · 2025 (published, in force)"`,
  `document_id: "rmit-v1-2025"` — and rebuild artifacts + update tests; or
  **(b)** source the **actual** 2020 RMiT PDF if the demo genuinely needs a real
  superseded version. **(a)** is lower effort and honest.

### Bug #2 — the corpus (built) and the briefs (planned) describe different demos

- **Built reality:** the engine, artifacts, and both GREEN experiments are all on
  the **RMiT / technology-risk cluster** (RMiT ↔ Outsourcing/BCM/OpRes/Recovery/
  MCIPD + MAS/PDPA/Basel references).
- **Briefs' plan:** the discovery briefs pivoted the demo to the **AI in the
  Financial Sector Discussion Paper** — which is **not in `data/corpus/` at all**
  (the only DP present is Operational Resilience).
- **Impact:** `/prd` would inherit an AI-DP framing that nothing built supports.
- **Resolution:** this note _is_ the resolution — it surfaces the fork for a
  scope decision (below). No document was quietly changed to hide the gap.

## The demo-scope fork — effort delta

Both candidate demos run the **same Reconciliation view**; they differ only in
_which corpus_ is on stage and _how much prep_ each needs.

| Dimension                    | **Option A — RMiT / tech-risk cluster** (built)                         | **Option B — AI in Financial Sector DP** (briefs' vision)                                   |
| ---------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Corpus status                | ✅ Built, ingested, graph + clause-index generated                      | ❌ Not in corpus; real DP PDF fetched once (custom-font), never extracted                   |
| Experiments                  | ✅ Two GREEN (delta+linkage on PDPA; reconciliation on RMiT 17.1 ↔ MAS) | ❌ Would need re-running on the DP corpus                                                   |
| Verbatim sources ready       | ✅ RMiT, Outsourcing, MAS, PDPA, Basel all real + extracted             | ⚠️ DP + its cited external docs all still to source/extract                                 |
| Reconciliation vehicle       | RMiT 17.1 (mock draft) ↔ MAS/Basel/PDPA — **proven**                    | DP clause ↔ MAS/FSB/IOSCO/PDPA — **unproven**                                               |
| Novelty / "live draft" story | Weaker — RMiT v2 is a hand-authored what-if                             | Stronger — a real, in-progress consultation draft                                           |
| Prep effort to demo-ready    | **Low** — mostly building the reconciliation UI over an existing engine | **High** — extract DP (needs markitdown), source references, re-run experiments, then build |
| Honesty risk                 | Low, if the mock v2 + "2020" label (bug #1) are fixed/labelled          | Low on sources, but time-to-ready is the risk                                               |

**Neither is turnkey**, but the gap is large: Option A is a UI build over a proven
engine; Option B is a corpus-build + re-validation _then_ the UI. For a hackathon
window, Option A is the far lower-risk path to a working MVP; Option B is the
better _story_ if the sourcing/extraction is done early enough to de-risk.

A middle path exists: **Option A as the built demo, with the AI-DP framing kept
as the "what's next / this generalises" roadmap slide** — honest about what's
real today while keeping the more inspiring vision visible.

## Recommendation

1. **Pick the demo corpus** (A / B / middle) — this is the one decision that
   gates `/prd` scope. Recommendation: **Option A (or the middle path)** for a
   time-boxed build; only choose B if the DP extraction + re-experiment can be
   done in the next few days.
2. **Fix bug #1** as a scoped task (relabel `rmit-v1-*` to the truth + rebuild
   artifacts + update tests), before the demo shows a version node to judges.
3. **In every brief and the pitch, label the RMiT v2 draft as a constructed
   what-if** — not "a real draft" — so the verbatim-citation promise stays
   credible (the real quotes are the _references_; the draft is the fiction the
   drafter edits).
4. Then `/prd`, carrying the chosen corpus + the verdict-taxonomy finding (#6).

## Cross-references

- Real-vs-mock manifest of record: `engine/config.py` (`DOCUMENTS`,
  `REFERENCE_DOCUMENTS`) — the build does not infer anything from filenames.
- Human-readable corpus table: `data/corpus/README.md`.
- External-reference provenance: `data/references/README.md`.
- Experiment results (both GREEN): `brief.md` → "Experiment results".
