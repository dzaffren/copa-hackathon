# Rulebook Radar — Overview

> **⚠️ SUPERSEDED (11 Jul 2026, then again 18 Jul 2026).** This two-persona
> (drafter + supervisor), RMiT-cluster design is the historical record of the
> 9–10 Jul era. It was first superseded by
> [`../reconciliation-workbench/spec.md`](../reconciliation-workbench/spec.md)
> on 11 Jul 2026, and the current live epic is
> **[`../workstream-brain/spec.md`](../workstream-brain/spec.md)** (18 Jul 2026
> pivot to cross-workstream drafting). Retained for history; do not build from
> this file. The Next.js prototype under `web/` that backed the
> reconciliation-workbench design has been moved to `archive/web/`.

**Discovery Brief:** docs/discovery/policy-consistency-ai/brief.md

## Summary

Rulebook Radar maps a cluster of Bank Negara Malaysia's published policy documents
**together with their external reference universe** — peer central banks' equivalent
policies, national acts (such as the Personal Data Protection Act), and international
standards — as one connected knowledge graph. Its primary job for a policy drafter is
the **Reference Radar**: for the clause being drafted, surface — quoted verbatim — what
peer regulators, acts, and standards say on that exact topic, so the drafter can ground
the draft in the external references that shape it. Keeping the rulebook internally
consistent (flagging a Conflict, Duplication, or Gap across BNM's own policies) becomes a
secondary "good to know" layer for the drafter, and remains the engine behind the
supervisor's checklist. The same knowledge graph serves a supervisor, who uploads a
bank's application and receives a cited checklist of every requirement it must meet across
the linked policies, with the missing items flagged. The tool is built entirely on
published documents and demonstrated on the technology-risk cluster for the COPA Hackathon
2026 (3 August 2026).

## Background & Context

**Current state:**

- When a drafter revises a policy such as Risk Management in Technology (RMiT), the heavy
  lifting is researching what **external references** say on the topic — other central
  banks' equivalent technology-risk policies, international bodies, government acts (for
  example the Personal Data Protection Act), the regulatory handbook, and technology
  trends. This research directly shapes the draft, and today it is scattered, manual work.
- The connections between BNM's own policies — which rules overlap, depend on, or
  reference each other — live in the heads of experienced policy staff, not in any shared
  map. A drafter checking a revision for internal overlaps recalls which other policies
  might be affected and reads each one.
- When a supervisor assesses a bank's application (for example, a cloud outsourcing
  arrangement), they must remember and assemble every relevant requirement scattered
  across multiple policies, then check the submission against each by hand.
- Why a clause changed — and which discussion papers or decisions drove it — is hard to
  reconstruct months later.

**Problem:**

- The drafter's primary pain is **external-reference research**: finding what peers,
  acts, and standards say on the exact topic being drafted is slow, scattered, and manual,
  yet it is what most directly shapes the wording. _(Validated 9 July 2026 in the first
  direct drafter interview, an RMiT drafter.)_
- Internal cross-policy consistency is a real but **secondary** concern for the drafter:
  overlaps are appreciated context that rarely change the draft, and internal conflicts are
  not a top worry. It stays valuable as a "good to know" layer and as the engine that
  assembles the supervisor's requirement set.
- For supervision, the dangerous failure is a _missed_ requirement — a required control the
  assessor forgot to check for, letting a compliance gap slip through.
- Both tasks depend on individual expertise that is hard to scale, hand over, or
  reconstruct months later.

This directly targets **BP2026 Must-Win 10** (AI roadmap for supervision), whose Key
Result 3 is ">15% efficiency across 10 supervisory processes from staff usage of AI
tools." It also supports **MW9** (process efficiency) and **MW6** (a coherent,
non-contradictory rulebook), and the broader SET2027 goals of a Trusted Institution /
Credible Regulator and Engaged Employees.

## Goals

- Give a drafter, for the clause being drafted, a **Reference Radar** of what peer
  regulators, national acts, and international standards say on that exact topic — each
  reference quoted verbatim with a plain-language "why this reference matters."
- Keep internal rulebook consistency as a **secondary, cited layer** for the drafter
  (reference gaps first, peer support next, internal overlaps last), and as the engine that
  assembles the supervisor's requirement set.
- Ensure every reference, finding, checklist line, and copilot answer quotes the exact
  clause or passage it relies on, so a human can verify it in seconds and never has to
  trust an unsupported claim.
- Let a supervisor upload a bank submission and get a complete, cited checklist of what
  every relevant policy requires — with the missing items flagged — without having to know
  which policies apply.
- Close both loops: let the drafter _act_ on findings (fix and submit for approval) and the
  supervisor _decide_ (approve or return to the bank), not merely diagnose.
- Demonstrate a measurable efficiency gain and fewer missed issues on a real cluster of BNM
  policies by the hackathon.

## Non-Goals

- **Cross-cluster mapping.** MVP1 covers a single cluster (technology-risk). The graph
  shows one greyed, clearly-labelled "preview" node representing a ripple reaching another
  cluster, but full cross-cluster analysis is a future phase.
- **The whole rulebook.** The demo is scoped to a cluster of 5–10 related policies plus a
  small external reference set for one topic — not every BNM policy and not every source the
  drafter named.
- **Regulatory handbook content.** The regulatory handbook is confidential (the same class
  as internal committee minutes) and is **deferred from MVP1**: it appears at most as a
  locked placeholder node or a clearly-labelled mock document, never with real content in a
  tracked path.
- **Multi-draft workspace and a separate reviewer persona.** MVP1 has exactly one editable
  draft; every other BNM policy is read-only published context. The dedicated reviewer role
  and multi-draft, role-based workspace are **deferred to a future phase** (see the deferred
  reviewer story). Manager approval is retained as the drafter's closing action.
- **A committed near-real-time trend / news layer.** Technology-trend and news signals are
  RMiT-specific evidence so far; they ship as a labelled **preview** and join the MVP only if
  other policy drafters confirm the same near-real-time need.
- **Silent AI edits.** The copilot never finalises policy text on its own; every change is
  proposed for a human to accept or reject.
- **Replacing human judgement.** The tool surfaces and cites references and findings;
  drafters, managers, and supervisors make every decision.

## Story Index

Epic tracking issue: [#5](https://github.com/dzaffren/copa-hackathon/issues/5).

| Ticket                                                          | Story                                                 | Spec                                                             | Type        | Status                      | Dependencies                       |
| --------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------- | ----------- | --------------------------- | ---------------------------------- |
| [#6](https://github.com/dzaffren/copa-hackathon/issues/6)       | Policy ingestion & rulebook knowledge-graph engine    | [spec-knowledge-graph-engine.md](spec-knowledge-graph-engine.md) | Technical   | Not Started                 | —                                  |
| [#7](https://github.com/dzaffren/copa-hackathon/issues/7)       | Single-draft rulebook workspace                       | [spec-drafter-workspace.md](spec-drafter-workspace.md)           | User-facing | Not Started                 | #6 Engine                          |
| [#26](https://github.com/dzaffren/copa-hackathon/issues/26)     | Reference Radar (external references for the drafter) | [spec-reference-radar.md](spec-reference-radar.md)               | User-facing | Not Started                 | #6 Engine; #7 Workspace            |
| [#8](https://github.com/dzaffren/copa-hackathon/issues/8)       | Draft alignment (references-first)                    | [spec-ripple-impact-report.md](spec-ripple-impact-report.md)     | User-facing | Not Started                 | #6 Engine; #7 Workspace; #26 Radar |
| [#9](https://github.com/dzaffren/copa-hackathon/issues/9)       | Drafting copilot with live write-back                 | [spec-drafting-copilot.md](spec-drafting-copilot.md)             | User-facing | Not Started                 | #6 Engine; #8 Alignment; #26 Radar |
| [#10](https://github.com/dzaffren/copa-hackathon/issues/10)     | Supervisor submission completeness & compliance check | [spec-supervisor-check.md](spec-supervisor-check.md)             | User-facing | Not Started                 | #6 Engine                          |
| ~~[#11](https://github.com/dzaffren/copa-hackathon/issues/11)~~ | ~~Reviewer & approval workflow~~                      | [spec-reviewer-approval.md](spec-reviewer-approval.md)           | User-facing | **Deferred (future phase)** | —                                  |

> **Story map note (9 Jul 2026 pivot).** The drafter side was re-issued around the
> Reference Radar as the primary value. #7 narrowed to a single editable draft; **#26
> Reference Radar** is new; **#8** was reframed from "ripple / impact report" to **"Draft
> alignment"** (references-first) and now folds in the manager-approval closing step; #9
> was re-grounded on reference retrieval and grounded web search. #6 (engine) and #10
> (supervisor) are unchanged — the engine's clause segmentation and linking applies to
> external reference documents too, which are ingested through the same pipeline and
> modelled as graph nodes. **#11 (reviewer & approval) is deferred**: MVP1 has no separate
> reviewer persona, and approval is folded into #8. The `spec-ripple-impact-report.md`
> filename is retained for ticket-#8 stability even though the story is now "Draft
> alignment."

## Shared Business Rules

- **Verbatim-citation guardrail (hard rule).** Every reference shown, finding, checklist
  line, and copilot answer must quote the exact clause or passage text it is based on, with
  its clause / paragraph number and source. If no supporting clause or passage exists, the
  tool must say so explicitly (for example, "No matching clause found") rather than assert an
  unsupported claim. This is the anti-hallucination measure and applies to every story,
  including external references.
- **Reference-first ordering for the drafter.** For the drafter the flag hierarchy is
  inverted from the original design: **external references / equivalents first**, internal
  overlaps second, internal conflicts last. For the **supervisor**, gaps (missing
  requirements) remain the headline. Both draw on the same graph.
- **External references are first-class graph nodes.** Peer central banks' equivalent
  policies, national acts (for example the Personal Data Protection Act), and
  international-standard papers are public documents ingested through the same pipeline as
  BNM policies and modelled as nodes that connect to the specific policy clauses they inform
  — same graph, new node types. The **regulatory handbook** is confidential and deferred: it
  appears at most as a locked placeholder or clearly-labelled mock, never with real content.
  **Technology-trend / news** nodes appear only as a labelled preview until validated with
  more drafters.
- **AI proposes, human commits.** The tool may suggest, redraft, classify, and flag, but it
  never finalises policy text or makes an approval / return decision on its own. A human
  always accepts, rejects, or decides.
- **A single editable draft (MVP1).** The workspace centres on exactly one in-progress
  editable draft — RMiT v2 in the demo — the only editable node in the graph. Every other
  BNM policy appears as **published** (in force or superseded), read-only context; overlaps
  with them are the secondary "good to know" layer. There is no separate reviewer role and no
  second editable draft in MVP1; the drafter's closing action is **submit for manager
  approval**.
- **Node status is derived, not invented.** A document is "In progress" exactly when a live
  working draft exists for it; "In force" and "Superseded" come from the published corpus.
- **Grounded web search on an approved allowlist.** Where the copilot searches the web for
  technology trends or news, it queries **only an approved source allowlist** (central banks,
  standard-setters, major wires); every result is cited and archived so a finding stays
  reproducible later. Who owns and edits that allowlist is a build-time decision.
- **One shared state across the drafter's pages.** The Draft alignment report and the
  drafting copilot read and write **one shared finding state**. Accepting a fix on either
  inserts a tracked change into the living draft and marks the matching finding resolved, and
  both views update live — the drafter never has to switch pages to learn the current state.
- **Public vs. sensitive data.** The drafter experience runs entirely on published (public)
  documents — BNM policies and public external references. The supervisor experience ingests
  a bank's submission — sensitive supervised-entity data — which carries heavier
  access-control and data-governance requirements. For the hackathon demo the submission is
  sample data, and the regulatory handbook is a locked placeholder.

## User Journey Map

> Rulebook Radar serves two personas on one shared knowledge graph. The journey below shows
> both, connected by the graph they have in common. The drafter path leads with external
> references (the primary value); the supervisor path is unchanged.

**Drafter path**

1. **Open the single-draft workspace** — Aisyah, a policy drafter, opens Rulebook Radar and
   sees her one editable draft, RMiT v2, at the centre of the technology-risk cluster.
   Every other BNM policy appears as published, read-only context, and the draft's external
   references orbit it as first-class nodes. She clicks a link to understand _why_ a policy
   or reference connects to her clause, and a "Why this changed" trail explains the version
   change. _(Story: Single-draft rulebook workspace)_
2. **Consult the Reference Radar** — For the clause she is drafting (RMiT clause 17.1, cloud
   adoption), the Reference Radar shows what a peer central bank's technology-risk policy,
   the Personal Data Protection Act, and an international standard say on that exact topic —
   each quoted verbatim with a plain-language "why this reference matters." _(Story:
   Reference Radar)_
3. **Check draft alignment** — She opens the Draft alignment report. It lists **reference
   gaps first** (where a peer or an act expects something her draft lacks), **peer support**
   next (where an external reference backs her wording), and **internal overlaps** last (the
   secondary "good to know" layer) — each finding quoting the exact clause it relies on.
   _(Story: Draft alignment)_
4. **Fix it with the copilot** — She opens the drafting copilot, which retrieves from the
   connected reference nodes and runs grounded web search on the approved allowlist, and
   accepts a redraft. The accepted text is written into the living document as a tracked
   change, the matching alignment finding is marked resolved, and both pages sync live.
   _(Story: Drafting copilot with live write-back)_
5. **Submit for approval** — When all findings are resolved, the Draft alignment report
   offers "Submit draft for manager approval." She submits; the approving manager is
   notified. (No separate reviewer step in MVP1.) _(Story: Draft alignment)_

**Supervisor path (same graph, different task — unchanged)**

6. **Upload a submission** — In the supervision workspace, an officer in Jabatan Penyeliaan
   uploads Meridian Bank's cloud outsourcing application. _(Story: Supervisor submission
   completeness & compliance check)_
7. **Get a cited checklist** — The tool reads the submission, classifies it (public cloud ·
   critical system · material outsourcing), and — using the same graph — assembles every
   requirement that applies across RMiT and Outsourcing, marking each Met / Missing /
   Unclear with the exact clause and where in the submission it looked. _(Story: Supervisor
   submission completeness & compliance check)_
8. **Decide** — Because two requirements are missing, approval is blocked. The officer
   clicks "Return to bank," which drafts a return letter auto-populated from the gaps (each
   citing its clause), and sends it. When a clean resubmission meets every requirement, the
   approve path becomes available. _(Story: Supervisor submission completeness & compliance
   check)_

## Success Metrics

- **Time efficiency (MW10 KR3):** a drafter or supervisor completes one real task — a
  drafter's external-reference research and consistency check, or a supervisor's
  submission-completeness check — **at least 15% faster** with Rulebook Radar than without
  it, measured as before/after time-to-complete on the same task across a small set of tasks.
  The drafter baseline explicitly includes **time spent researching external references per
  draft**.
- **Fewer missed issues (completeness / recall):** on a labelled set of known references,
  known conflicts, and known requirements, the tool surfaces a **higher proportion of the
  real items** than an unaided human finds in the same time — with special attention to
  recall for supervision (missing a required control is the dangerous failure) and to not
  missing an obviously-relevant external reference.
- **Zero unsupported claims:** 100% of references, findings, checklist lines, and copilot
  answers quote an existing clause or passage verbatim; any citation that cannot be verified
  against the source document is treated as a defect.
- **No invented equivalence:** every external reference the radar claims is "equivalent" or
  "related" to a BNM clause genuinely addresses that topic — a passage claimed to match that
  actually covers something else is treated as a defect.
- **End-to-end loop completion:** both personas can complete their full loop in the demo —
  drafter (references → align → fix → submit for approval) and supervisor (upload →
  checklist → return or approve).

## Dependencies

- **Locked demo cluster (confirmed):** a 6-document technology-risk cluster — RMiT +
  Outsourcing + Business Continuity Management + Operational Resilience + Recovery Planning +
  Management of Customer Information — plus a greyed AML/CFT cross-cluster preview. All real
  published BNM documents. (No standalone "Cyber Risk" policy — cyber lives inside RMiT — so
  it is not a node.)
- **Published policy documents:** the corpus of current, published BNM policy PDFs for the
  chosen cluster (all public via bnm.gov.my), ingested through the knowledge-graph engine.
- **External reference corpus (new):** a small set of **public** external references for one
  topic (cloud adoption / RMiT 17) — a peer central bank's technology-risk policy, the
  Personal Data Protection Act, and one international-standard / BIS paper — as public PDFs
  ingested through the same pipeline and modelled as graph nodes. The exact set is locked by
  the reference-radar experiment (discovery Experiment 2 / action item 8). The regulatory
  handbook is deferred as a locked placeholder.
- **Sample bank submission:** a representative cloud outsourcing application (sample / mock
  data) for the supervisor demo, plus a second "clean" version so the approve path can be
  shown.
- **Living working-document location:** an agreed place where the one in-progress policy
  draft lives and can be edited with tracked changes (for the drafter write-back loop).
- **Confirmed pain (validation):** the drafter external-reference pain is validated with one
  RMiT drafter (9 Jul 2026); generalisation to other drafters and validation of the
  supervisor pain (Jabatan Penyeliaan) are in progress, plus a baseline time for the
  efficiency measurement.

## Shared Architecture Notes

Cross-story technical shape, added when each drafter story was refined (`/prd-refine`). Full
detail: [`architecture.md`](architecture.md) and the ADRs in [`../../adr/`](../../adr/).

- **Frontend:** a React 18 + TypeScript + Vite + Tailwind SPA in `web/`, reading the engine's
  FastAPI read API. #7 scaffolds it (typed API client, shared types, workflow-state store,
  React Flow graph, mock `DraftDocViewer`, Playwright); #26/#8/#9 build on it.
- **Engine reference-node extension (#6, reopened):** external references are ingested through
  the same pipeline and modelled as new node kinds (`kind:"reference"` + `source_type` /
  `access` / `preview`) with reference↔clause edges — same graph, new node types. The
  regulatory handbook is a restricted, content-withheld node (no text ingested); trends are a
  labelled preview.
- **Drafter workflow state:** findings + tracked changes in browser `localStorage` for the
  MVP1 demo (cross-tab sync via the `storage` event); server-side per document/version for
  production. #8 owns the finding state (`rr.findings.rmit-v2-2026-draft`); #9 reads/updates
  the same key so the counts cannot diverge.
- **Demo stand-ins:** copilot prose from curated fixtures with clauses fetched live; grounded
  web search from an allowlist fixture; write-back a mock tracked change; SharePoint / Microsoft
  Graph is the documented production path.
- **Decisions:** ADR 0001 (workflow state), 0002 (React Flow), 0003 (reference read path),
  0004 (copilot generation), 0005 (write-back). Note: `Operational Resilience 6.11` is a phantom
  clause — the real anchor is `RMiT 10.50 ↔ Operational Resilience 1.1`.

## Rollout Strategy

- **Delivery order:** build the knowledge-graph engine first (everything depends on it),
  then the single-draft workspace, then the Reference Radar (the primary drafter value),
  then the Draft alignment report, then the copilot; the supervisor check can proceed in
  parallel once the engine exists; the reviewer / approval workflow is deferred.
- **Demo scope:** one cluster, two personas, both loops closed end-to-end, with the
  Reference Radar as the headline drafter moment.
- **Roadmap slide:** the "what's next" story bundles the cross-cluster "preview" node, the
  deferred reviewer / multi-draft workspace, and the fuller external universe (the regulatory
  handbook and a committed trend / news layer) — MVP1 proves the pattern on one cluster and
  one topic's references; expansion is the next phase.

## Open Questions

> Resolve before or during implementation. Non-blocking questions may be deferred with
> rationale.

- [x] ~~Should the drafter flag conflicts, or references and overlaps?~~ — **Resolved
      (9 Jul 2026 pivot):** for the drafter the hierarchy inverts — **references / equivalents
      first, internal overlaps second, conflicts last**. For the supervisor, gaps (missing
      requirements) remain the headline.
- [x] ~~Does the copilot write back to the live document, or only suggest text?~~ —
      **Resolved:** it writes the accepted redraft into the living document as a tracked
      change (AI proposes, human commits), and shares finding state with the alignment report.
- [x] ~~Should the drafter be able to reach "submit" by dismissing findings, not only fixing
      them?~~ — **Resolved:** yes, a finding may be dismissed rather than fixed, but a
      dismissal must record a reason for the audit trail; a dismissed finding counts as
      resolved for the purpose of submitting.
- [x] ~~Should MVP1 keep the separate reviewer persona and multi-draft workspace?~~ —
      **Resolved (9 Jul 2026 pivot):** no. MVP1 has a single editable draft and no separate
      reviewer role; the drafter's closing action is submit for manager approval (folded into
      the Draft alignment story). The reviewer / multi-draft workspace is deferred to a future
      phase.
- [ ] **Has the reference-radar assumption been validated (cross-jurisdiction equivalence)?**
      — **Status:** the riskiest new assumption — that an LLM can find genuinely equivalent
      passages in a peer regulator's differently-structured policy and in acts without forcing
      false equivalences — is tested by discovery Experiment 2 (action item 8), **not yet
      run**. ← Validate before committing external-source content; the graph/clause mechanics
      are already green for internal pairs.
- [ ] **Which external sources make the demo cut for the tech-risk cluster?** — **Status:**
      awaiting Experiment 2; candidate names (a peer central bank's tech-risk guidelines, the
      Personal Data Protection Act, an international operational-resilience standard) are
      unverified until sourced. ← Blocks final content, not the architecture.
- [ ] **Does the technology-trend / news layer join MVP1 or stay a preview?** — **Status:**
      the near-real-time trend / news need is RMiT-specific evidence so far; it joins the MVP
      only if other policy drafters confirm the same workflow (discovery action item 7). Until
      then it is a labelled preview. Non-blocking.
- [ ] **How is the ">15% efficiency" baseline captured for the demo?** — **Status:** awaiting
      a measured baseline time from drafter / supervision contacts, now including time spent
      researching external references per draft (discovery action item 5). ← Needed for the
      Impact pitch; does not block build.
- [ ] **What is the exact final cluster (which 5–10 policies)?** — **Status:** largely settled
      (the 6-document technology-risk cluster is in use); confirm the final set (discovery
      action item 2). ← Blocks final content, not the architecture.
- [ ] **Is the supervisor pain validated with Jabatan Penyeliaan?** — **Status:** open
      (discovery action item 4); the supervisor use case proceeds on its previously-scoped
      assumption for the demo. Non-blocking for build.
- [ ] **What governance applies to the uploaded bank submission in a real deployment?** —
      **Deferred (non-blocking):** the demo uses sample data; real access-control and
      data-governance design is a post-hackathon concern, but must be named explicitly in the
      pitch.
