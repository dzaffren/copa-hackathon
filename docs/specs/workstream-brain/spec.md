# Workstream Brain MVP1 — Overview

**Discovery Brief:** `docs/discovery/workstream-brain-mvp1/brief.md`

## Summary

Workstream Brain is the second POC delivered for the COPA Hackathon 2026, targeting the "cross-workstream drift is invisible" opportunity retired in the parent discovery brief. Each policy workstream (Discussion Paper, Exposure Draft, Policy Document under active drafting) becomes a knowledge graph of documents connected by structural edges. AI-found linkages between clause pairs surface as findings the drafter reviews and accepts before drafting. This epic covers the drafter-facing MVP1 scope: five drafter/workstream screens plus a widened engine. The management-facing institution map is deferred to a follow-on epic.

## Background & Context

**Current state:**

- The Rulebook Radar engine supports pairwise linkage discovery between two clause-indexed documents, with a verbatim citation guarantee.
- A parent discovery experiment retired the "can the engine find cross-workstream linkages between concurrent BNM workstreams" assumption — 12 supported linkages found on the OpRes DP × Open Finance ED pair, zero unsupported.
- A clickable HTML prototype exists at `docs/poc/workstream-brain/` covering six screens (workstream graph, task, review linkages, drafting workspace, institution map, new workstream).

**Problem:**

- Senior policymakers carry cross-workstream linkages in their heads. When they rotate, retire, or take leave, institutional memory goes with them.
- Peer-benchmarking and BCBS-anchor mapping is manual, gets stale, and is redone from scratch every workstream cycle.
- Drafters switch windows constantly to remember which BCBS clauses and peer positions they were adapting from — the pairwise-compare-then-merge workflow has no tool support today.
- The Rulebook Radar engine's linkage taxonomy (Conflict / Duplication / Gap) is too narrow to describe the full range of cross-doc relationships a workstream member cares about.

## Goals

- Give a drafter one tool that holds every doc their workstream depends on and shows how they relate.
- Make AI-found linkages between draft clauses and anchor clauses actionable — accept, dismiss, comment, resolve.
- Carry accepted linkages into the drafting surface so context does not get lost between review and writing.
- Keep the verbatim-citation guarantee end-to-end: the tool never invents a clause reference.

## Non-Goals

- **Institution map (management-facing zoom-out view)** is out of scope for this epic. Delivered later as a follow-on epic once the FSC/FPWG agenda-builder design is settled.
- **Ontology-based concept extraction pipeline** is not built here. The workstream graph and task pairwise comparison use only the existing finder→critic pairwise loop. Concept nodes appear only in the institution map (deferred).
- **Real Microsoft Word / PowerPoint / Excel embed** in the drafting workspace. The workspace uses a styled document surface, not a live Office embed.
- **Correction store as few-shot examples fed back into finder/critic prompts.** Reviewers can accept, dismiss, and comment on findings, but corrections do not yet retrain nearby linkage analysis. Deferred.
- **Live network calls to Azure AI Foundry during the demo.** The demo replays the retired-experiment trace on `Analyze linkages` clicks; live LLM calls stay behind the same seam for later.

## Story Index

| Ticket | Story                                               | Spec                                                                     | Type        | Status      | Dependencies                  |
| ------ | --------------------------------------------------- | ------------------------------------------------------------------------ | ----------- | ----------- | ----------------------------- |
| TBD    | Linkage taxonomy widening in the engine             | [spec-engine-taxonomy.md](spec-engine-taxonomy.md)                       | Technical   | Not Started | —                             |
| TBD    | Anchor segmentation (multi-strategy `AnchorIndex`)  | [spec-engine-anchor-segmentation.md](spec-engine-anchor-segmentation.md) | Technical   | Not Started | Taxonomy                      |
| TBD    | Retrieval-first pipeline (axis extraction + hybrid) | [spec-engine-retrieval-pipeline.md](spec-engine-retrieval-pipeline.md)   | Technical   | Not Started | Taxonomy; Anchor segmentation |
| TBD    | Workstream graph screen (hero)                      | [spec-workstream-graph.md](spec-workstream-graph.md)                     | User-facing | Not Started | Anchor segmentation           |
| TBD    | Task screen with pairwise comparison                | [spec-task-screen.md](spec-task-screen.md)                               | User-facing | Not Started | Graph; Retrieval pipeline     |
| TBD    | Review linkages screen                              | [spec-review-linkages.md](spec-review-linkages.md)                       | User-facing | Not Started | Graph; Retrieval pipeline     |
| TBD    | Drafting workspace with 3-tab side panel            | [spec-drafting-workspace.md](spec-drafting-workspace.md)                 | User-facing | Not Started | Review                        |
| TBD    | New workstream form                                 | [spec-new-workstream.md](spec-new-workstream.md)                         | User-facing | Not Started | Graph                         |

## Shared Business Rules

- **Verbatim citations only.** Every clause or passage quotation shown to a user must come from the `AnchorIndex` for the cited document. If an `anchor_id` cannot be resolved to a real anchor, the tool displays "No matching clause found" rather than inventing content. (Anchors are structured-rules clauses on BNM/HKMA gazetted rules, heading-based sections on MAS Notice 637 / BoE chapters / BCBS papers, and prose paragraphs on Federal-Register-style documents — see [spec-engine-anchor-segmentation.md](spec-engine-anchor-segmentation.md).)
- **Cross-jurisdiction pairs go through the retrieval-first pipeline.** Pairwise comparison uses axis extraction + hybrid retrieval + glossary expansion _before_ the finder/critic sees a candidate pair (see [spec-engine-retrieval-pipeline.md](spec-engine-retrieval-pipeline.md)). The pipeline is deterministic-orchestrator + role-specialised LLM stages; no free-form multi-agent conversation.
- **One document, one node.** No clause-level nodes exist on any graph. Clauses surface only inside finding cards.
- **Seven node types, flat.** `task` is the only editable node type. The other six (`internal-published`, `international-standard`, `peer-regulator`, `act-law`, `industry-input`, `others`) are read-only anchors. Node type is chosen once at add-time.
- **Four structural edge types.** Every graph edge is exactly one of: `supersedes` (newer version replaces older version of same source), `references` (one doc cites the other as authoritative), `contributes-to` (anchor feeds into a drafting task), `parallel-to` (two live docs on adjacent domains). Edges are declared at node-creation time.
- **Every new node must connect.** Adding a node requires declaring at least one edge to an existing node. Orphan nodes are not allowed.
- **Structural edges live on the graph; semantic labels live on findings.** A graph edge is not a finding. Findings appear only after the user clicks **Analyze linkages** on an edge, and each finding carries one of five semantic labels (`aligns-with`, `differs-on`, `conflicts-with`, `silent-on`, `goes-beyond`). Never render semantic labels on the graph itself.
- **Sentiment tag applies only to `differs-on`.** A `differs-on` finding may carry an optional `tighten`, `loosen`, or `neutral` sentiment. Other labels have no sentiment.
- **Task nodes edit through the task screen, not directly.** Clicking a task node's action button opens the task screen; clicking the task screen's "Open draft" opens the drafting workspace.
- **Findings persist across screens.** A finding accepted on the review screen appears in the drafting workspace's Reviewed tab. A finding dismissed on the review screen stays dismissed everywhere until reopened.

## User Journey Map

A composite drafter's day, showing how the stories connect:

1. **Sign in and open a workstream.** Aisyah opens the Operational Resilience workstream from the sidebar. She lands on the workstream graph, which shows her PD working draft in the centre and six anchor documents around it. _(Story: workstream graph)_
2. **Add a new anchor.** She uploads the just-published HKMA Supervisory Policy Manual OR-2 as a `peer-regulator` node, declaring a `contributes-to` edge from the SPM to her PD draft. The new node appears on the graph immediately. _(Story: workstream graph)_
3. **Kick off a review of the new anchor.** She clicks the new HKMA node, then clicks the `contributes-to` edge in the edge-detail panel. The edge status shows "not analysed" with an **Analyze linkages** button. She clicks it. _(Story: workstream graph)_
4. **Review the linkages the engine found.** She lands on the review screen. Five finding cards appear on the right, each with a semantic label. Clicking a card highlights the relevant clauses in the two-pane clause reader. She accepts three cards, dismisses one as a false positive, and tags Farid on the fifth with a question. _(Story: review linkages)_
5. **Open the task for the PD draft.** From the workstream graph, she clicks the OpRes PD v0.3 node, then clicks **Open task** in the node-detail panel. The task screen shows every neighbour and every already-analysed linkage between her draft and each neighbour. _(Story: task screen)_
6. **Open the draft.** From the task screen top-right, she clicks **Open draft**. The drafting workspace opens with the document surface on the right and three tabs on the left: her reviewed linkages, related linkages one hop away from her task, and a Copilot chat. _(Story: drafting workspace)_
7. **Draft against context.** As she writes §5.3, she keeps the Reviewed tab open to see the `differs-on tighten` finding on scenario cadence. She switches to Copilot to ask for a draft preamble that cites BCBS Principle 7 without overclaiming BNM adoption. _(Story: drafting workspace)_
8. **Set up a new workstream when the Chair announces one.** Later that week, the DG announces a Climate Risk PD v2. Aisyah opens the sidebar and clicks **+ New workstream**. She fills in the name, deliverable type, target quarter, owner, and reviewers, then lands on an empty workstream graph. _(Story: new workstream)_

## Success Metrics

- **Demo lands on stage.** The 6-step walkthrough (parent brief) executes end-to-end on hackathon day without an engineer intervening.
- **All findings shown are verbatim.** Zero fabricated clause references appear anywhere in the shipped POC. Every clause quotation is traceable to a real entry in the clause index.
- **User can drive the full drafter flow in under 10 minutes** without documentation, on the pre-seeded Operational Resilience workstream.
- **Judges score the tool on Problem Relevance and MVP Quality first.** MW6 (coherent rulebook), MW9 (resource discipline), MW10 (AI for supervision) alignment is the pitch spine, not a checkbox.

## Dependencies

- **Existing knowledge-graph engine.** The pairwise linkage discovery loop and the clause index are already built and validated on the parent brief's experiment. The taxonomy-widening story extends the label vocabulary; the anchor-segmentation story widens what can be cited; the retrieval-pipeline story replaces raw pairwise prompting with axis-first retrieval. Every user-facing story consumes them.
- **Retired experiment trace (`data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json`).** Used as the demo backstop when `Analyze linkages` is clicked on the OpRes × Open Finance pair. Replays under the new pipeline via prerecorded-candidate mode.
- **Cross-jurisdiction demo corpus.** UK Bank of England Chapter 3 (credit-risk standardised approach), HKMA CA-G-1 + gazetted rules, Singapore MAS Notice 637 (effective 1 July 2024), and three BCBS mother-docs from bis.org (CRE, OPE, BCP). Ingested through `data/corpus/manifest.json` per [spec-engine-anchor-segmentation.md](spec-engine-anchor-segmentation.md).
- **Cross-jurisdiction glossary (`data/glossary.json`).** ~20 hand-authored alias entries covering the demo pair's likely terminology mismatches (conforming loan ↔ Level C loan, KYC ↔ CDD, LCR ↔ MAS Notice 649 liquidity requirement, etc.). Owned by [spec-engine-retrieval-pipeline.md](spec-engine-retrieval-pipeline.md).
- **Clickable POC (`docs/poc/workstream-brain/`).** Six HTML screens covering the full flow. The build reuses the POC's visual language and interaction patterns; production builds do not reuse the raw HTML.
- **CLAUDE.md conventions.** Verbatim-citation product rule, personas (Aisyah R. drafts and owns; Farid M. reviews; Priya S. reviews), git strategy, no direct commits to main.

## Rollout Strategy

Build in dependency order:

1. **Engine taxonomy widening first** — everything else consumes the new semantic labels.
2. **Workstream graph in parallel with review linkages** — the graph feeds edges into review; review displays findings the graph opens.
3. **Task screen and new workstream in parallel** — both depend on the graph but not each other.
4. **Drafting workspace last** — depends on review having produced accepted findings.

Ship each story behind its own PR closing its own GitHub issue. Squash-merge to main. Hackathon deadline is 2026-08-03; MVP1 must be demoable by 2026-07-31 to leave a buffer for rehearsal.

## Open Questions

Non-blocking, do not gate implementation start:

- [ ] **Manual-add linkage UX detail on review screen.** The screen currently offers a clause-picker dropdown for both source and target clauses (never free text — the verbatim-citation rule forbids invented clauses). Deferred: whether the picker should default-filter to clauses containing overlapping concepts, or show every parsed clause. Non-blocking: default to every clause; refine after first drafter uses it.
- [ ] **Copilot intent-preset behavioural mapping.** MVP1 ships the seven intent presets (DP / PD / ED / FAQ / Engagement Deck / Feedback Template / Peer Benchmarking) as a dropdown that does not alter Copilot behaviour. Deferred: how each preset actually conditions the underlying prompt. Non-blocking for MVP1 demo.
- [ ] **Second-order neighbours in the node-detail panel.** The panel currently shows a "N/A in demo" placeholder for second-order neighbours. Deferred: whether to enable this for MVP1 or after v2 corpus expansion. Non-blocking; leave as N/A for now.
- [ ] **Drafting Copilot "Related · 1 hop" traversal depth.** MVP1 fixes at 1 hop from the task's neighbours. Deferred: whether to expose a "2 hop" toggle. Non-blocking for MVP1.

Blocking, must be resolved before institution-map epic starts (not this one):

- [ ] **Institution-map redesign as FSC/FPWG agenda builder.** The screen was scoped away from this epic. Design in progress with product; will land in a follow-on epic.
