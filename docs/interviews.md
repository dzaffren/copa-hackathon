# BNM Policy Drafter — User Journey Notes

Source: interview with a BNM policy drafter, organised from raw meeting notes.

Abbreviations used throughout:

- **PFP** — Prudential and Financial Policy department
- **PPD** — Payments Policy department
- **PD** — Policy Document
- **ED** — Exposure Draft
- **BCBS** — Basel Committee on Banking Supervision
- **FSA 2013** — Financial Services Act 2013
- **RSU** — Risk Supervision Unit

## 1. Starting a policy assessment

The drafter almost never starts from a blank page. First step is understanding **what they're improving on**, not treating it as a new regulation.

- Go through the requirements and ask: what's implemented in Malaysia today? Are these standalone policies, or do they interplay with existing ones?
- Identify areas that pose challenges, along several dimensions:
  - **Operational cost** — credit policies often need system enhancement.
  - **Capital cost** — how much capital banks must hold (quantifiable).
  - **Interplay with internal standards** — does the new requirement fit how internal processes already work?
  - **System capability** — e.g. can CCRIS handle it?

## 2. Enhancement vs new — verbatim benchmarking is the main assessment point

If the doc is enhancing an existing document, the core question is:
**What are the new requirements added on top, and did BNM deviate from or follow the international benchmark _bulat-bulat_ (i.e. blindly / exactly)?**

Verbatim benchmarking is the _primary_ assessment lens.

- **BCM policy** → refer to mother doc (Operational Resilience draft). Ensure core BCBS principles are captured. Mother doc is very principle-based.
- **Outsourcing** → same pattern.
- **Capital rules** → try to `bulat-bulat` follow BCBS.

**Regulatory posture — important nuance:**

- BNM is **not** regulated to comply with BCBS. Malaysia follows anyway, and won't be penalised if it doesn't.
- However, **other jurisdictions that ARE under BCBS would be penalised** for non-compliance.
- **IMF validation assessment** still checks how closely BNM follows, in which areas it deviates, and whether the deviation is warranted.

## 3. Mother documents & document hierarchy

- **Operational Resilience** is the mother doc → applies to RMiT etc.
- Board / senior management responsibilities need to be **delineated** (e.g. maximum tolerable downtime).
- **BCM policy** governs roles of the board.
- **Basel III** → tells banks how much capital to hold; now in its 3rd iteration.
  - Sub-modules: credit risk, operational risk, market risk.
  - **Counterparty risk framework** was subsumed into credit risk as a standalone module (previously treated as too simple — e.g. exposure to clearing houses like Bursa).

## 4. Technical vs principle-based

- **Principle-based** (Operational Resilience, BCM): high-level, board responsibilities, avoids point-in-time requirements.
- **Technical** (Basel / capital): try to bulat-bulat follow.

## 5. Credit risk specifics

Two ways to calculate credit risk:

- **Standardised Approach (SA)**
- **IRB (Internal Ratings-Based)**

Key mechanics:

- Risk weight depends on counterparty (e.g. sovereign AAA = 0% risk weight).
- **ECAI** = External Credit Assessment Institution (e.g. Moody's).
- Exposure types: bank-to-bank loans, bank-to-corporate loans.
- **PSE** = Public Sector Entity (e.g. EPF — serves a social agenda, own organization).
- **National discretions** exist in footnotes — currently only **MAS and HKMA** exercise them.
- Latest credit risk doc: **June 2024**.

## 6. Jurisdictional benchmarking

Jurisdictions BNM benchmarks against, with regulator, notes, and whether AI can help ingest their documents:

- **Malaysia** — BNM. FSA 2013 empowers issuing regulatory requirements. (source jurisdiction)
- **Hong Kong** — HKMA. Financial requirements built into legislation ("HK capital rules"). _Manual._
- **EU** — EBA plus national regulators. _Manual._
- **US** — Fed Reserve plus state. Reserve committee; different states have different requirements. _Manual._
- **UK** — PRA, FCA, BoE. Post-Brexit — check alignment to EBA. Credit risk via BoE (SACR, UK PRA). _AI-usable._
- **Canada** — OSFI. Basel-based, but paused output floor and gives ~2 years' notice. _AI-usable._
- **Australia** — APRA. _AI-usable._
- **Singapore** — MAS. _AI-usable._
- **Indonesia** — _AI-usable._
- **New Zealand** — RBNZ. _AI-usable._

Structural questions to answer per jurisdiction:

- Is the requirement **legislated**?
- Is there a **mother document**?
- **Precedence** — how does it rank?
- **Who is the standard-setting party** (e.g. EU or HK have distinct arrangements)?

**Coordination note:** if one person is doing benchmarking, need to **label** which jurisdiction each finding comes from.

**Citations pending — need verbatim quote:**

- Basel III **72.5% output floor** — need to quote exact paragraph from BCBS d424 ("Basel III: Finalising post-crisis reforms," Dec 2017) or Basel Framework chapter RBC20. Likely available in `docs/references/`.
- **Canada's 60% freeze** — need to quote exact OSFI announcement (likely the June 2023 press release on Domestic Stability Buffer + Basel III output floor pause).

## 7. How BNM knows BCBS has changed

- **BCBS never declares what changed.** Drafter has to spot deltas manually.
- PFP tracks BCBS; PPD tracks a different standard-setting body (e-money — pioneer for e-wallet, ever-changing).

## 8. Policy drafting lifecycle

The flow: **Discussion Paper → Exposure Draft (ED) → Feedback → Policy Document (PD).**

- **Discussion paper** — get industry to read and give feedback; multiple iterations refine the doc.
- **Consultation papers / discussion papers** signal purpose and intent.
- **Annex 1 of the PD** lists these.
- **Gestation time**: ED → feedback → dept publishes → takes a whole year. **~2 years total** to form a PD.

Feedback categorisation:

- Agreeable / partially agreeable / disagree
- Capital = more **quantitative** feedback
- BCM = more **qualitative** feedback
- Goal: a system to submit feedback to the ED consultation platform.

## 9. Cross-department coordination

- Feedback is worked through **FPWG** and **MC**.
- Reach out to owning depts (e.g. outsourcing) to get their feedback on overlapping sections.
- Tag comment boxes for teams whose policies may overlap: **FS, RSU (Risk Supervision Unit), IFD** — seek their input.
- Previous BCM docs / **supervisory letters still stand** and must be read in reference.
  - Decisions like: "can this be subsumed under the PD?" → if yes, do it.
  - Otherwise: "read in conjunction with X."
- Contested points hashed out at **FPWG**.

## 10. Keeping policy current with tech change

The core problem: **policy drafting is slow (~2 years); tech moves faster.**

- Governance forums for regular check-ins: **CRO / CCO / CEO / CTO forums**.
- Policies are kept **high-level on purpose** — avoids locking in point-in-time requirements.
- **New product filing**: before a bank issues to mass market, they file all info to BNM. (Or they launch to public and file to BNM.)
- **PPD** (payments) explicitly says their landscape is changing — they don't want to be included in rigid PDs. E-money is ever-changing → PPD issues **supervisory letters** instead.
- Principle: **try one-size-fits-all first; if TKDE (tak boleh / don't have), find other ways.**

## 11. Doc timeline governance

- **RSU, PPD, PD** — same nominal timeline, but more frequent check-ins.

## Still open

- Basel output floor + OSFI freeze — pull verbatim citations from the local PDFs in `docs/references/` when available.