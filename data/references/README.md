# External reference corpus (public)

Real, public **external references** for the Reference Radar (#26) — a peer
regulator, a national act, and an international standard whose passages the radar
quotes **verbatim** for the clause a drafter is working on. These are the external
analogue of `data/corpus/` (which holds the internal BNM cluster policies), but they
enter the graph as `kind:"reference"` nodes rather than policy nodes. Each public
reference's verbatim `passage` lives in `engine.config.REFERENCE_DOCUMENTS` (extracted
from the real source below with `markitdown`, checked word-for-word); because external
references are **not** BNM-numbered, the build makes each one a single clause via
`engine.clauses.build_reference_clause` rather than the BNM clause segmenter. The files
in this directory are the provenance that config `passage` was copied from.

> **Not confidential.** MAS TRM, the PDPA, and the Basel principles are all public
> documents. This directory is **tracked** (unlike the git-ignored, confidential
> `docs/references/`). Never place anything sensitive here — the BNM Regulatory
> Handbook stays a node-only placeholder with **no** ingested text (see #26).

Each passage below was extracted from the **real source** with the engine's own
`markitdown` pipeline and checked word-for-word — replacing the earlier illustrative
/ hand-written excerpts in the spec. The verbatim-citation guardrail is only real if
these quotes are real.

| Anchor (`target_clause`) | Reference                                                                       | `source_type`    | Source (public)                                                                                                                                                     | Status                                 |
| ------------------------ | ------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `Basel POR TP-1`         | Principles for Operational Resilience (Basel Committee, 2021) — **Principle 5** | `standard`       | [bis.org/bcbs/publ/d516](https://www.bis.org/bcbs/publ/d516.htm)                                                                                                    | ✅ **Verified verbatim**               |
| `PDPA 129`               | Personal Data Protection Act 2010 (Act 709), **§129 as amended by Act A1727**   | `act`            | [Act A1727 (amendment)](https://www.pdp.gov.my/ppdpv1/wp-content/uploads/2024/11/Act-A1727.pdf) · [Act 709](https://www.pdp.gov.my/ppdpv1/en/akta/pdp-act-2010-en/) | ✅ **Verified verbatim (current law)** |
| `MAS TRM Cloud`          | Technology Risk Management Guidelines (MAS, Singapore, 2021) — **§3.4.2**       | `peer_regulator` | [mas.gov.sg TRM Guidelines](https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines)                                                     | ✅ **Verified verbatim**               |

Node-only references (no source file, never ingested): `bnm-handbook` (restricted,
content-withheld) and `trend-cloud-signals` (labelled preview). See #26.

## Provenance notes

- **Basel POR** — third-party dependency management is **Principle 5** (not Principle
  6; Principle 6 is response & recovery). Quoted verbatim from d516 (2021).
- **PDPA §129** — the spec previously quoted the **pre-2024** text (Minister/Gazette
  whitelist). The **Personal Data Protection (Amendment) Act 2024 (Act A1727)**, §12,
  in force **1 April 2025**, deleted the old subsection (1) and made subsection (2) the
  operative test; "data user" → "data controller" throughout. The passage here is the
  **current** law, reconstructed by applying the gazetted amendment (Act A1727 §12) to
  the verbatim 2010 text — both halves source-verified.
- **MAS TRM** — MAS TRM has **no** dedicated public-cloud pre-approval clause; cloud is
  governed under **§3.4 Management of Third Party Services** (§3.4.1 explicitly frames
  cloud-type services). The anchor quotes **§3.4.2** — assess third-party technology risk
  before contracting — the genuine peer analogue for RMiT 17.1. The spec's earlier "no
  prior approval" excerpt was a paraphrase and has been replaced by this real text.

## MAS TRM Guidelines (2021) — source in place

MAS's website returns a maintenance page to the automated fetcher, so the PDF was placed
manually (the same way the `data/corpus/` PDFs were): `mas-trm-2021.pdf` is here now, the
real **§3.4.2** passage was extracted with `markitdown` and anchored to `MAS TRM Cloud`,
and the spec's earlier paraphrase has been replaced by the verbatim text.
