# Reconciliation Workbench — Overview

**Discovery Brief:** docs/discovery/reconciliation-workbench/brief.md
(grounded by docs/discovery/drafter-knowledge-graph/brief.md — the interview evidence)

> **⚠️ SUPERSEDED (18 Jul 2026).** This reconciliation-workbench epic (single
> policy document as the drafter's home surface, Next.js frontend under `web/`)
> is retired in favour of **[`../workstream-brain/spec.md`](../workstream-brain/spec.md)**,
> which reframes the tool around the _workstream_ as the unit of work and adds
> cross-jurisdiction retrieval. The Next.js app under `web/` has been moved to
> `archive/web/`; the current frontend stack is Vite + React + TS + Tailwind +
> shadcn under `frontend/` (see
> `docs/learnings/convention-frontend-vite-react-not-nextjs.md`). Retained for
> history; do not build from this file.
>
> _Historical note:_ this epic itself superseded `docs/specs/rulebook-radar/`
> (the 9–10 Jul two-persona, RMiT-cluster era) on 11 Jul 2026. The chain of
> pivots is rulebook-radar → reconciliation-workbench → workstream-brain.

## Summary

The Reconciliation Workbench is a policy drafter's home surface: they open an
in-progress policy document, and the tool automatically pulls in the scattered sources
that bear on it — the ones the document already **cites** (peer regulators, international
standards, acts) and the relevant ones it did **not** cite — links each source to the
paragraph it touches, and uses AI to judge every connection (consensus, conflict, gap, or
duplicate), always quoting the exact clause it relies on. The drafter reconciles each
connection (pull a principle in, anchor to an existing rule, note a gap, or flag a
conflict), and — where a fix is needed — a grounded redraft assistant proposes wording
backed by a verbatim source clause that she accepts back into her Microsoft Word draft as a
tracked change. Every accepted change is captured
as a defensible, verbatim-cited decision trail. It is demonstrated for the COPA Hackathon
2026 (3 August 2026) on one real vehicle — Bank Negara Malaysia's _Discussion Paper on AI
in the Malaysian Financial Sector_ (August 2025).

## Background & Context

**Current state:**

- A policymaker drafting or enhancing a policy document does due diligence by scouring
  scattered sources — international standards (BCBS, FSB, OECD, NIST), peer regulators
  (MAS, OSFI, APRA), national acts (the Personal Data Protection Act, the Financial
  Services Act), Bank Negara Malaysia's own policies, and current happenings — to
  strengthen the draft. Each source lives somewhere different, and today the drafter
  hunts through all of them by hand.
- Verbatim benchmarking — _"did we follow the international benchmark exactly, or did we
  deviate, and why?"_ — was named the **primary assessment lens** by a prudential
  drafter and corroborated across three departments (RMiT, FS/CLS, PFP/capital).
- When an external standard changes, no one announces it: _"BCBS never declares what
  changed — the drafter has to spot the deltas manually."_
- Why a clause follows or departs from a benchmark lives in people's heads. Months later
  it is hard to reconstruct — yet the International Monetary Fund's assessment (FSAP)
  checks exactly how closely Bank Negara Malaysia follows international standards and
  whether each deviation is warranted.

**Problem:**

- The research is slow, scattered, and manual, yet it is what most directly shapes the
  wording of a policy.
- Because the reconciliation lives only in memory, the institution carries no defensible,
  clause-by-clause record of why the rulebook says what it says — the exact record the
  IMF assessment expects.
- Reading sources one at a time, a drafter misses cross-source implications and silent
  gaps that only surface when many sources are read together.

This directly targets **BP2026 Must-Win 10** (AI roadmap): **KR2** — _"1 business process
re-engineering initiative per sector using AI"_ — is a binary fit (this is that initiative
for policy drafting), and **KR3** — _">15% efficiency … from staff usage of AI tools"_ —
supplies the metric. It supports **MW6** (a coherent, benchmarked rulebook) and the
**Trusted Institution / Credible Regulator** strategic outcome, evidenced by the IMF FSAP.
(The earlier MW9 anchor is dropped: BP2026 defines MW9's "non-IT" as improvements that do
**not** require building software; this tool is software.)

## Goals

- Let a drafter open an in-progress document and have the tool pull in and **link** the
  sources that bear on it — both the ones it cites and relevant ones it did not — to the
  specific paragraphs they touch.
- For every connection, show the AI's **verdict** (consensus / conflict / gap /
  duplicate / partial) and a plain-language read of how it affects the paragraph, always
  quoting the exact source passage verbatim.
- Let the drafter **act** on each connection — pull a principle in, anchor to an existing
  rule, note a gap, flag a conflict, or note what to reconcile — and, where a fix is needed,
  accept a source-grounded suggestion from the grounded redraft assistant that writes back
  into her Microsoft Word draft as a tracked change.
- Accumulate every accepted reconciliation into a **defensible decision trail** — a
  verbatim-cited, IMF-ready record of why each clause aligns with or deviates from its
  benchmark.
- Surface **cross-source insights** a human reading source-by-source would likely miss.
- Demonstrate the **proactive Monitor** as prepared drift events (a PDPA §129 amendment and
  a Basel output-floor change): when a watched source changes, push the drafter which draft
  clauses are now out of sync.
- Show a measurable efficiency gain (≥15% less reconciliation time) and zero unsupported
  claims on the demo vehicle by the hackathon.

## Non-Goals

- **A continuously-running source watcher.** The Monitor is demonstrated over **one
  prepared source-change event** (a single BCBS delta), not a live service that polls the
  internet. Continuous watching is the roadmap north star.
- **Live web retrieval of every cited source at demo time.** In the demo, the vehicle
  document's citations are catalogued and the source set is curated and clearly labelled;
  live parse-and-fetch is a documented production path, proven only in part (parsing is
  green; live fetch is a build risk).
- **Two corpora.** MVP1 runs one vehicle (the AI Discussion Paper) plus **one
  illustrative Basel row** carrying the IMF story — not a full second capital-rules
  corpus.
- **The supervisor persona.** Checking a bank's submission for missing requirements is a
  validated adjacent product, ranked "what's next," and is deferred to a roadmap slide. It
  shares the same engine and can return cheaply.
- **Confidential sources with real content.** The regulatory handbook and any internal
  "own past positions" that are sensitive appear at most as a locked placeholder or a
  clearly-labelled mock — never with real content in a tracked path.
- **Silent AI edits.** The grounded redraft assistant never finalises policy text or a
  verdict on its own; every change and every verdict is proposed for a human to accept,
  reject, or override.
- **Rebuilding Word or a general copilot.** Drafting, formatting, collaboration, and
  ungrounded free-text generation stay in Microsoft Word (on SharePoint) and M365 Copilot.
  We do not rebuild the editor or compete as a general writer.
- **Replacing human judgement.** The tool surfaces, links, quotes, and proposes; the
  drafter decides.

## Story Index

Epic tracking issue: TBD (GitHub Issues + Project board — see `CLAUDE.md`).

| Ticket | Story                                                | Spec                                                                     | Type        | Status      | Dependencies              |
| ------ | ---------------------------------------------------- | ------------------------------------------------------------------------ | ----------- | ----------- | ------------------------- |
| TBD    | Two-branch source connection engine                  | [spec-source-connection-engine.md](spec-source-connection-engine.md)     | Technical   | Not Started | —                         |
| TBD    | Upload & reconciliation workspace                    | [spec-upload-and-workspace.md](spec-upload-and-workspace.md)             | User-facing | Not Started | Engine                    |
| TBD    | Connection reconciliation & decision trail           | [spec-connection-reconciliation.md](spec-connection-reconciliation.md)   | User-facing | Not Started | Engine; Workspace         |
| TBD    | Cross-source insights ("what you might have missed") | [spec-cross-source-insights.md](spec-cross-source-insights.md)           | User-facing | Not Started | Engine; Workspace         |
| TBD    | Grounded redraft assistant & Word write-back         | [spec-grounded-redraft-assistant.md](spec-grounded-redraft-assistant.md) | User-facing | Not Started | Workspace; Reconciliation |
| TBD    | Source drift monitor (prepared drift events)         | [spec-source-drift-monitor.md](spec-source-drift-monitor.md)             | User-facing | Not Started | Engine; Reconciliation    |

## Shared Business Rules

- **Microsoft writes; we cite (positioning rule).** Drafting happens in Microsoft Word on
  SharePoint, alongside M365 Copilot. Our tool is the **source-intelligence layer**: a
  companion web app that reads the Word draft and writes accepted, source-grounded
  suggestions back as tracked changes via Microsoft Graph. Our grounded redraft assistant
  only proposes wording it can back with a verbatim source clause; a request it cannot
  ground is declined with "No matching clause found," never answered with uncited prose.
- **Evidence-and-justification guardrail (hard rule).** Every AI judgement, verdict,
  insight, assistant answer, and decision-trail entry must carry **both** (a) the exact
  clause or passage it is based on, quoted verbatim with its clause/paragraph number and
  source (the _evidence_), **and** (b) a plain-language rationale for the call (the
  _justification_ / "why this call"). If no supporting passage exists, the tool must say so
  explicitly — for example, _"No matching clause found"_ — and never assert an unsupported
  claim. Evidence without justification, or a claim without evidence, is a defect. This is
  the anti-hallucination measure and applies to every story.
- **Explicit "No source found" state.** A paragraph that has been **analysed** but has no
  source bearing on it shows an explicit _"No matching source found"_ — visibly distinct
  from a paragraph that is simply **"not yet analysed."** The empty-but-analysed state is
  an honest result, not a blank.
- **Verbatim-integrity marking.** Every displayed quote is marked either **✓ verified**
  (checked word-for-word against the source document) or **◦ illustrative** (not yet
  verified). Illustrative quotes are visibly distinct and may never be presented as
  verified.
- **Two branches, clearly labelled.** Connections come from two branches: sources the
  document **cites** (which the tool parses out and retrieves → consensus / duplicate),
  and relevant sources it did **not** cite, matched by topic against a curated source
  library (→ gap / conflict / partial / missed). The demo labels which parts are real
  (upload + extraction) versus prepared (curated source set + pre-prepared analysis).
- **Five verdicts; AI proposes, human confirms.** Each connection carries one verdict —
  **Consensus, Conflict, Gap, Duplicate,** or **Partial** (the source agrees in part and
  diverges in part — also the home for industry feedback marked "partial"). The AI proposes
  the verdict with its evidence and justification; the drafter can confirm or override it.
  Where a connection reads as both a Gap and a deliberate deviation, the drafter's
  confirmation settles the call — the system never trusts its own verdict blindly.
  **"Deviates"** is a documented nuance recorded on a Gap (a deliberate, justified
  departure from a benchmark), not a sixth verdict.
- **The act adapts to the verdict.** Consensus → pull in as a cited guiding principle;
  Duplicate → anchor to the existing rule as a cross-reference; Gap → note as an open gap
  to address; Conflict → flag for resolution before the Exposure Draft; Partial → note what
  to reconcile (which part to keep, which to resolve). A drafter cannot "adopt a conflict as
  a principle."
- **Deviations and partials require a recorded justification.** Overriding a Gap to a
  deliberate **Deviates**, or acting on a **Partial**, requires the drafter to record a
  "why this call" note **before** the decision can be saved — this is what makes the trail
  IMF-defensible.
- **Source types are first-class.** Every source is one of: international standard /
  principle, peer regulator, act / law, internal BNM policy, or **industry feedback**
  (bottom-up — what the regulated industry says back on a published paper). Industry
  feedback is analysed on the same engine as any top-down source, categorised agree /
  partial / disagree.
- **AI proposes, human commits.** The tool may suggest, redraft, classify, judge, and
  flag, but it never finalises policy text or a verdict on its own. A human always accepts,
  rejects, or overrides.
- **A single draft (MVP1).** The tool centres on exactly one in-progress document — the AI
  Discussion Paper in the demo — which the drafter edits in Microsoft Word on SharePoint.
  Every other document is read-only source context. The draft is honestly labelled as a
  constructed what-if where its text has been shaped for the demo; the real, verifiable
  content is the _sources_.
- **The drafter can add or supply sources.** The drafter is the expert: they can add a
  source the curated library missed, and supply a source the tool identified but could not
  retrieve (for example, a peer regulator's site that blocks automated access) — after
  which it is quoted and analysed like any other.
- **One shared state across the drafter's pages.** The workspace, reconciliation view,
  insights/trail, and grounded redraft assistant read and write **one shared finding
  state**. Acting on a connection or accepting a source-grounded suggestion updates the
  draft and the trail, and every view reflects it live — the drafter never switches pages to
  learn the current state.
- **Dismissal records a reason.** A connection may be dismissed as "not relevant" instead
  of acted on, but the dismissal records why (kept in the trail so a reviewer sees what was
  considered and set aside).
- **Public vs. sensitive data.** The drafter experience runs entirely on published
  documents — BNM policies and public external references. Confidential sources are
  deferred (locked placeholder / labelled mock, never in a tracked path).

## User Journey Map

> One persona — a policy drafter (Aisyah R.) — on one shared knowledge graph. The journey
> runs from opening a document to a defensible, submitted draft.

1. **Upload the open document** — Aisyah opens the Reconciliation Workbench and uploads
   the AI Discussion Paper she is enhancing. The tool extracts its paragraphs, parses the
   sources it cites, retrieves them, and matches its topics against the curated library to
   surface relevant sources it did _not_ cite. An honest analyse sequence shows each step;
   one source (MAS) can't be auto-retrieved and is flagged for her to supply. _(Story:
   Upload & reconciliation workspace)_
2. **Explore the connected sources** — In the workspace her document is the canvas. She
   selects paragraph 3.5 (fair usage & bias) and the right rail shows every source
   connected to it — OECD, NIST, the Fair Treatment of Financial Consumers policy —
   each with its source type, verdict, and a verbatim quote. _(Story: Upload &
   reconciliation workspace)_
3. **Reconcile a connection** — She opens the OECD connection: verdict **Consensus**, the
   verbatim OECD passage, and the AI's read of how it affects 3.5. She confirms the
   verdict and pulls it in as a guiding principle; it enters her decision trail. For the
   PDPA §129 connection on paragraph 4.6, the verdict is **Conflict**, so she flags it for
   resolution before the Exposure Draft. _(Story: Connection reconciliation & decision
   trail)_
4. **See what she might have missed** — She opens the insights view. The AI has reasoned
   _across_ her connected sources and surfaces cross-source implications and silent gaps —
   e.g. that her bias stance (3.5) and data stance (4.6) point to a single missing control,
   and that no paragraph addresses model-concentration risk. Each names the sources it
   reasoned across. _(Story: Cross-source insights)_
5. **Fix it with a source-grounded suggestion** — On a flagged paragraph she asks the
   grounded redraft assistant for a fix. It proposes wording backed by a verbatim source
   clause (something a general copilot can't do) and — when she accepts — writes the text
   back into her Microsoft Word draft on SharePoint as a tracked change via Microsoft Graph.
   The matching finding is marked resolved and the trail records the _decision_, not just the
   reference. _(Story: Grounded redraft assistant & Word write-back)_
6. **Get alerted to drift** — A drift item appears: a watched benchmark (BCBS) has
   changed, and the tool lists which of her draft clauses are now out of sync, each with
   the exact changed passage. She opens one straight into the reconciliation view. _(Story:
   Source drift monitor)_
7. **Submit a defensible draft** — With findings resolved and a verbatim-cited trail
   behind every decision, she submits the draft for manager approval. _(Story: Grounded
   redraft assistant & Word write-back)_

## Success Metrics

- **Time efficiency (MW10 KR3):** a drafter reconciles a real draft against its sources
  **at least 15% faster** with the Workbench than without, measured as before/after
  time-to-complete on the same set of clauses (find the relevant sources, pull the exact
  passages, decide align/deviate and note why). A small hand-timed sample or a credible
  drafter estimate is acceptable evidence, labelled as such.
- **Evidential completeness:** a higher share of reconciled clauses end with a verbatim,
  verifiable justification than a from-memory baseline.
- **Zero unsupported claims:** 100% of connections, verdicts, insights, and assistant
  suggestions quote an existing passage verbatim; any citation that cannot be verified
  against its source is treated as a defect.
- **No invented equivalence:** every connection the tool claims genuinely addresses the
  paragraph's topic; a passage claimed to relate that actually covers something else is a
  defect.
- **Fewer missed connections (recall):** on a labelled set of known relevant sources, the
  tool surfaces a higher proportion of the real items than an unaided drafter finds in the
  same time.
- **Source-grounded over general drafting:** our assistant's suggestions are each backed by
  a verbatim source clause (or declined with "No matching clause found") — the measurable
  distinction from Microsoft Copilot, which writes fluent but uncited text.
- **End-to-end loop completion:** the drafter can complete the full loop in the demo —
  upload → connect → reconcile → insights → grounded fix written back to Word → drift alert
  → submit.

## Dependencies

- **Demo vehicle (confirmed):** BNM's _Discussion Paper on AI in the Malaysian Financial
  Sector_ (Aug 2025) — a real, live, in-progress, citation-heavy draft. It extracts
  cleanly (≈73,601 characters, 54 numbered paragraphs) via MarkItDown (naive extraction
  produces gibberish because of the PDF's custom-font encoding).
- **Curated source library (branch ②):** a preloaded set of **public** references matched
  to the vehicle's topics — OECD AI Principles, NIST AI Risk Management Framework, BCBS
  239, EU AI Act (Regulation 2024/1689), the Personal Data Protection Act 2010 (as amended
  2024), and the Fair Treatment of Financial Consumers policy — plus sample industry
  feedback. Maintaining this library is an ongoing operational task.
- **Illustrative Basel row:** the two owed verbatim citations — the **Basel III 72.5%
  output floor** (BCBS d424 / Basel Framework RBC20) and **Canada's OSFI output-floor
  freeze** — carry the IMF deviation-justification story. Both are public but **not yet
  local**; they must be sourced and extracted, or shown as a labelled "pending extraction"
  placeholder — never an approximated quote.
- **Prepared drift event:** one dated source change (a BCBS delta, or the PDPA §129
  2010→2024 amendment already in the corpus) with a hand-verified list of the draft clauses
  it affects, for the Monitor demonstration.
- **Living working-document location:** an agreed place where the one in-progress draft
  lives and can be edited with tracked changes (browser state for the demo; a
  document-management path such as SharePoint / Microsoft Graph is the production route).
- **Confirmed validation:** connection-finding is proven green (blind tests: internal
  RMiT↔Outsourcing links; RMiT 17.1 ↔ MAS TRM §3.4.2 reconciliation; PDPA §129 delta +
  clause linkage; DP citation parsing). Still needed from real people: the proactive-drift
  preference (is the Monitor wanted?), and the ≥15% baseline timing.

## Rollout Strategy

- **Delivery order:** build the two-branch connection engine first (everything depends on
  it), then the upload & workspace, then connection reconciliation & the decision trail,
  then cross-source insights, then the grounded redraft assistant & Word write-back; the
  drift monitor rides the same engine and lands once reconciliation exists.
- **Demo scope:** one vehicle document, one curated source set, both the connect and
  analyse branches, the full reconcile-and-fix loop, two prepared drift events (PDPA §129 and
  the Basel output floor), and one illustrative Basel reconciliation row.
- **Honesty labelling (non-negotiable):** the demo shows real upload + real extraction,
  clearly labelled where the source set is curated and where the analysis is pre-prepared;
  the draft is labelled a constructed what-if; the Word write-back is a mock tracked change
  with the live Microsoft Graph integration labelled as the production path; each Monitor
  drift item is labelled a prepared, dated event, not a live watcher.
- **Roadmap slide:** the continuously-running Monitor, the supervisor persona, live
  parse-and-fetch of cited sources, the branch-② topic→source retrieval at scale, the live
  Microsoft Graph write-back to Word/SharePoint (and a native Word task-pane add-in), the
  confidential regulatory handbook, and full cross-jurisdiction breadth — MVP1 proves the
  pattern on one vehicle; expansion is the next phase.

## Open Questions

> Resolve before or during implementation. Non-blocking questions may be deferred with
> rationale.

- [x] ~~Which verdict vocabulary is canonical?~~ — **Resolved:** **Consensus / Conflict /
      Gap / Duplicate / Partial** (five verdicts). "Partial" homes a source that agrees in
      part and diverges in part (and industry feedback marked "partial"). "Deviates" is a
      documented nuance recorded on a Gap, not a verdict. The Gap-vs-Deviates ambiguity is
      handled by **AI proposes the verdict, the drafter confirms or overrides it.** An
      analysed paragraph with no bearing source shows a distinct "No matching source found"
      state.
- [x] ~~Does MVP1 include the "acting layer," or is it a reference explorer only? And should
      we build our own editor/copilot?~~ — **Resolved:** include the acting layer, but
      **don't rebuild Word or a copilot.** Drafting stays in Microsoft Word on SharePoint
      (with M365 Copilot); our tool is the source-intelligence layer — a companion web app
      whose **grounded redraft assistant** proposes verbatim-cited wording and writes accepted
      suggestions back into the Word draft as tracked changes via Microsoft Graph. This closes
      the POC's critical gaps and delivers "drafting → execution" without competing with
      Microsoft on ground it owns. Positioning: "Microsoft writes; we cite."
- [x] ~~Is the Monitor built or roadmap-only?~~ — **Resolved:** built as a story,
      demonstrated over **two prepared drift events** (PDPA §129, proven green; and a Basel
      output-floor change, the IMF-story headline) — pushed to the drafter but labelled
      prepared, not a running watcher. Delta + linkage tested green; the continuously-running
      service, and the same machinery pointed inward to auto-detect draft edits, are the
      roadmap north star. In MVP1 a draft edit is re-checked by the drafter triggering
      "Analyse this paragraph," not automatically.
- [x] ~~One demo corpus or two?~~ — **Resolved:** one vehicle (AI Discussion Paper) plus
      **one illustrative Basel row** for the IMF story. Not a second capital-rules corpus.
- [x] ~~Keep the supervisor persona in MVP1?~~ — **Resolved:** deferred to a roadmap slide;
      it shares the engine and can return cheaply.
- [ ] **How "live" must the Monitor look in the demo, and where exactly is the
      real-vs-prepared line drawn and labelled?** — **Status:** a single prepared drift
      event is honest and low-risk; settle the exact framing during implementation.
      Non-blocking.
- [ ] **What counts as a "material" source change worth queuing?** — **Status:** the
      Monitor's value depends on filtering noise from substance; the threshold definition
      is deferred and will be informed by the drafter-validation conversation. Non-blocking.
- [x] ~~Can the two owed Basel/OSFI citations be sourced and verified verbatim before the
      demo?~~ — **Resolved:** sourcing and extracting BCBS d424 / RBC20 (output floor) and
      the OSFI freeze is a build task and will be attempted; but the demo is **guaranteed** to
      ship either the verbatim-verified quote or a labelled **"pending extraction"**
      placeholder — never an approximated quote. This keeps the IMF beat without gating the
      demo on the sourcing.
- [x] ~~Should the demo analyse only the three showcase paragraphs (3.5, 3.11, 4.6)?~~ —
      **Resolved:** no. MVP1 fully analyses **8–10 paragraphs** of the vehicle document for
      visible depth (answering the earlier "doesn't feel like a ~40-clause document"
      critique); the remaining paragraphs are selectable and show "not yet analysed" with the
      analyse-this-paragraph trigger. 3.5 / 3.11 / 4.6 remain the worked showcase examples
      throughout the specs.
- [ ] **Is the proactive drift queue actually wanted (vs. on-demand)?** — **Status:**
      awaiting a drafter conversation (4-question script ready). If drafters prefer their
      own cadence, the Monitor drops to a labelled roadmap phase and MVP1 is the reactive
      workbench. ← Validates the Monitor's boldness, not the build.
- [ ] **How is the ≥15% efficiency baseline captured?** — **Status:** awaiting a measured
      or credibly-estimated baseline for the reconciliation task. ← Needed for the Impact
      pitch; does not block build.
- [x] ~~Does the decision trail need to capture _rejected_ references~~ ("we considered
      MAS's approach and chose not to follow it because…")? — **Resolved:** MVP1's trail
      records only the references that **shaped the final text** (accepted principles,
      cross-references, gaps, and flagged conflicts). Dismissed connections still keep their
      reason in the audit log (a shared rule), but a dedicated "rejected references" view is
      **deferred to the roadmap**. The IMF deviation-justification story is carried by the
      recorded "why this call" note on each accepted deviation, not by a separate
      rejected-set view.
- [x] ~~Is "Deviates" a fifth verdict?~~ — **Resolved:** no. The canonical verdict set stays
      **Consensus / Conflict / Gap / Duplicate**. "Deviates" is a **documented nuance** the
      drafter records — a flag plus a "why this call" justification — when a Gap is in fact a
      deliberate, justified deviation from an international benchmark. No fifth badge is built.
