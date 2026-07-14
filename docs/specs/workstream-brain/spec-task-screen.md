# Task Screen with Pairwise Comparison

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)

**Ticket:** TBD

The task screen is the drafter's home for a single working-draft node. Reached by clicking **Open task** on any `task`-type node on the workstream graph, it lays out the source document's metadata, the neighbour anchors declared when the task was created, and a pairwise comparison card showing what the engine has found between the working draft and each neighbour. The drafter uses it to decide which anchor to focus on next and to jump straight into drafting with that context in mind.

## User Story

As Aisyah R., I want to see every neighbour anchor for my task and how each one compares against my current draft, so that I can decide which anchor to focus on next and open the draft with that context in mind.

## Background & Context

**Current state:**

- Drafters carry the list of anchor documents (BCBS mother docs, peer regulators, statutory hooks, industry submissions) in their heads or in a personal spreadsheet.
- Even when they know the anchor list, they have no single place to see which anchors have been compared against their draft and which have not.
- Peer benchmarking notes get redone from scratch every workstream cycle because there is no persistent home for the linkages between a draft and its anchors.

**Problem:**

- Without one screen that inventories every anchor and shows finding-level status against each one, drafters do not know where the gaps in their own review coverage are.
- Findings that already exist for some anchor pairs are invisible from the task's home, forcing the drafter to remember which pairs have been analysed and navigate to each individually.
- Un-analysed pairs risk being forgotten; there is no visible prompt saying "this anchor has never been compared against your draft".

## Target User & Persona

- **Who:** Aisyah R., a BNM policy drafter who owns the Operational Resilience Policy Document working draft (v0.3) and is the primary author responsible for reconciling it against six declared anchor documents.
- **Context:** After adding the OpRes PD task to the workstream graph and declaring its six neighbour anchors, Aisyah returns to this screen every day she picks up drafting — to check which anchors she has already reviewed against, which are still pending, and to decide which finding to open next.
- **Current workaround:** A personal notebook plus mental notes on which peer regulators she has already benchmarked, redone each drafting cycle.

## Goals

- Give the drafter one screen that lists every neighbour anchor declared for the task and the current comparison status against each.
- Make un-analysed pairs visually distinct so the drafter can see coverage gaps at a glance.
- Route the drafter into the review screen (for an analysed pair) or the drafting workspace (to keep writing with context) in one click.
- Keep the verbatim-citation guarantee — no invented clauses appear in any finding shown here.

## Non-Goals

- **No editing of the neighbour list from this screen.** Neighbours are added or removed by editing edges on the workstream graph.
- **No inline draft editing on the task screen.** Draft content is edited on the drafting workspace, reached via **Open draft**.
- **No enforcement of workflow assignment in MVP1.** The **Assign** button opens the workflow picker but does not persist an assignment.

## User Workflow

1. **Starting point — workstream graph.** Aisyah clicks the OpRes PD v0.3 node on the workstream graph, then clicks **Open task** in the node-detail panel.
2. **Task screen loads.** The header shows the breadcrumb back to the workstream graph, the task badge, the document title "Operational Resilience PD — v0.3", and a one-line description noting that six neighbour nodes were defined at creation. Top-right shows **Assign** and **Open draft** actions.
3. **Read the source card.** On the left, Aisyah sees the document name, format, clause count, when it was last edited, herself as owner, Farid M. and Priya S. as reviewers, and an "in progress" status pill.
4. **Scan the neighbour list.** Below the source card, she sees six neighbour rows — BCBS OpRes 2021, FSB 3rd-Party Toolkit, HKMA SPM OR-2, RMiT PD (28 Nov 2025), FSA 2013 §143, and the ABM position paper — each showing its structural edge type and node type.
5. **Read the pairwise comparison card.** On the right, one card per neighbour pair. Four cards show analysed findings with a semantic label and a one-line summary; two cards (FSB and ABM) show a "not analysed" state with an **Analyze linkages** button.
6. **Filter to one neighbour.** She clicks the **HKMA** filter chip to isolate the HKMA card, reads the summary, and clicks its "Open in Review" link to see the full finding detail.
7. **Return and continue.** She clicks the filter chip **All** to bring back every pair, then clicks **Open draft** top-right to switch to the drafting workspace with the same task context loaded.

## Acceptance Criteria

### Scenario: Landing on the task screen renders all three cards populated

```gherkin
Given Aisyah has opened the Operational Resilience workstream
  And she has clicked "Open task" on the OpRes PD v0.3 node
When the task screen loads
Then she sees a header showing the breadcrumb "← Workstream graph / Task", a task badge, the document title "Operational Resilience PD — v0.3", and the one-line description "Working draft of the Policy Document following the 2025 Discussion Paper · 6 neighbour nodes defined at creation"
  And she sees a source card listing the document name "OpRes PD v0.3 working draft", the format ".docx", the clause count "42 clauses", the last-edited timestamp, herself as owner, Farid M. and Priya S. as reviewers, and an "in progress" status pill
  And she sees a neighbour-nodes card listing six rows
  And she sees a pairwise comparison card containing six pair entries — one for each neighbour
  And she sees a footer on the pairwise comparison card that reads "4 of 6 neighbours analysed"
```

### Scenario: Neighbour list shows every declared edge with its structural type

```gherkin
Given the task screen is loaded for the OpRes PD v0.3 task
When Aisyah reads the neighbour-nodes card
Then she sees six rows in the following order

  | Neighbour name              | Structural edge  | Node type              |
  | BCBS OpRes 2021             | contributes-to   | international-standard |
  | FSB 3rd-Party Toolkit       | contributes-to   | international-standard |
  | HKMA SPM OR-2               | contributes-to   | peer-regulator         |
  | RMiT PD (28 Nov 2025)       | parallel-to      | internal-published     |
  | FSA 2013 §143               | references       | act-law                |
  | ABM position paper          | contributes-to   | industry-input         |
```

### Scenario: Analysed pair cards show a semantic label and one-line summary

```gherkin
Given the task screen is loaded for the OpRes PD v0.3 task
  And the pairs against BCBS OpRes 2021, HKMA SPM OR-2, RMiT PD (28 Nov 2025), and FSA 2013 §143 have already been analysed
When Aisyah reads the pairwise comparison card
Then she sees a pair card for each analysed neighbour showing the neighbour name, a semantic label, a one-line summary, and a link labelled "Open in Review"
  And she sees the following pair summaries

  | Neighbour              | Semantic label   | One-line summary                                                                                                             |
  | BCBS OpRes 2021        | aligns-with      | Dependency mapping tracks BCBS Principle 7                                                                                    |
  | HKMA SPM OR-2          | differs-on       | Annual vs biennial scenario testing — draft pins annual cadence; HKMA requires at least biennial                              |
  | RMiT PD (28 Nov 2025)  | conflicts-with   | Anchor to superseded RMiT version — draft anchors to the 1 June 2023 RMiT while the 28 Nov 2025 version supersedes it         |
  | FSA 2013 §143          | aligns-with      | Statutory basis correctly cited — preamble anchors this PD to FSA §143(2)                                                     |
```

### Scenario: Un-analysed pair cards show a "not analysed" state with an Analyze button

```gherkin
Given the task screen is loaded for the OpRes PD v0.3 task
  And the FSB 3rd-Party Toolkit pair has never been analysed
  And the ABM position paper pair has never been analysed
When Aisyah reads the pairwise comparison card
Then she sees a pair card for FSB 3rd-Party Toolkit shown as visually distinct from analysed cards, carrying a "not analysed" badge, the count "0 findings", explanatory text noting no pairwise linkages have been surfaced yet, and an "Analyze linkages" button
  And she sees the same treatment on the pair card for ABM position paper
  And neither card shows a semantic label or a finding summary
```

### Scenario: Clicking a neighbour filter chip narrows the pair list to that neighbour

```gherkin
Given the task screen is loaded with all six pair cards visible
When Aisyah clicks the filter chip "HKMA"
Then she sees only the HKMA SPM OR-2 pair card
  And the other five pair cards are hidden
  And the "HKMA" chip is shown as selected
```

### Scenario: Clicking the All filter chip restores every pair card

```gherkin
Given the task screen is loaded
  And Aisyah has previously clicked the filter chip "FSA" so only the FSA pair card is visible
When she clicks the filter chip "All"
Then she sees all six pair cards
  And the "All" chip is shown as selected
```

### Scenario Outline: Filter chip isolates a single neighbour

```gherkin
Given the task screen is loaded with all six pair cards visible
When Aisyah clicks the filter chip <chip>
Then she sees only the pair card for <neighbour>
  And the remaining five pair cards are hidden

Examples:
  | chip  | neighbour              |
  | BCBS  | BCBS OpRes 2021        |
  | FSB   | FSB 3rd-Party Toolkit  |
  | HKMA  | HKMA SPM OR-2          |
  | RMiT  | RMiT PD (28 Nov 2025)  |
  | FSA   | FSA 2013 §143          |
  | ABM   | ABM position paper     |
```

### Scenario: Analysing an un-analysed pair from the task screen

```gherkin
Given the task screen is loaded
  And the FSB 3rd-Party Toolkit pair card is in a "not analysed" state
When Aisyah clicks "Analyze linkages" on the FSB pair card
Then she sees the card enter an in-progress analysing state
  And once the analysis completes, the card renders the surfaced findings with their semantic labels and one-line summaries
  And the pairwise-comparison footer updates to reflect one additional analysed neighbour
```

### Scenario: Opening the drafting workspace from the top-right action

```gherkin
Given the task screen is loaded for the OpRes PD v0.3 task
When Aisyah clicks "Open draft" in the top-right of the header
Then she is taken to the drafting workspace for this task
```

### Scenario: Opening the workflow picker from the Assign action

```gherkin
Given the task screen is loaded for the OpRes PD v0.3 task
When Aisyah clicks "Assign" in the top-right of the header
Then she sees a workflow picker open next to the button
  And the picker lists Farid M. and Priya S. as available workstream members she can assign the task to
```

### Scenario: Opening the review screen from an analysed pair card

```gherkin
Given the task screen is loaded
  And the HKMA SPM OR-2 pair card shows a "differs-on" finding summary
When Aisyah clicks "Open in Review" on the HKMA pair card
Then she is taken to the review linkages screen for the OpRes PD v0.3 against HKMA SPM OR-2 pair
```

### Scenario: Navigating back to the workstream graph via the breadcrumb

```gherkin
Given the task screen is loaded
When Aisyah clicks the breadcrumb "← Workstream graph"
Then she is taken back to the workstream graph for the Operational Resilience workstream
```

### Scenario: Empty draft shows an empty-state prompt instead of pair cards

```gherkin
Given a task node has been created for a working draft that contains zero clauses
  And Aisyah clicks "Open task" on that node
When the task screen loads
Then she sees the source card showing the draft with a clause count of "0 clauses"
  And she sees the pairwise comparison card rendering an empty-state message explaining that no findings can exist until the draft has content
  And she sees an "Open draft" call-to-action inside the pairwise comparison card
  And no pair cards are shown
```

### Scenario: A finding whose clause cannot be resolved is never rendered with invented text

```gherkin
Given an analysed pair against the RMiT PD (28 Nov 2025) references clause number that cannot be resolved in the parsed clause index
When Aisyah reads the RMiT pair card
Then she does not see any fabricated clause text
  And she sees either the finding omitted from the card or the phrase "No matching clause found" in place of any clause quotation
```

## Business Rules & Constraints

- **Verbatim citations only.** Any clause text shown inside a pair card must come from the parsed clause index for the cited document. If a clause number cannot be resolved, the pair card either omits that finding or shows "No matching clause found" in its place — the tool never invents clause text.
- **A pair card cannot show a summary until the pair has been analysed.** Un-analysed pairs are visually distinct (a dashed-border treatment, a "not analysed" badge, and an "Analyze linkages" call-to-action). They carry no semantic label, no one-line summary, and no clause references.
- **Filter chip semantics.** Selecting a single-neighbour chip hides every other pair card. Selecting "All" restores every pair card. Only one chip is selected at a time.
- **Assign is a display-only workflow picker in MVP1.** Clicking **Assign** opens a dropdown listing available workstream members (Farid M., Priya S.). MVP1 does not enforce that the selection actually reassigns the task; the picker exists to demonstrate the surface area.
- **Open draft always navigates to the drafting workspace for this task.** It never opens a modal or the workstream graph.
- **Neighbour list is read-only on this screen.** The declared neighbours were fixed when the task was added to the graph. To add or remove a neighbour, the drafter must return to the workstream graph and edit the task node's edges there.
- **Empty draft means no findings can exist yet.** When the source draft has zero clauses, the tool refuses to display any pair cards and prompts the user to open the draft. It never fabricates comparison content against an empty draft.
- **Pairwise progress footer.** The footer summarises how many neighbours have been analysed out of the total declared (for example, "4 of 6 neighbours analysed"). This count updates when a previously un-analysed pair completes analysis.

## Success Metrics

- **Every neighbour is accounted for at a glance.** A drafter opening the task screen can name, without scrolling, which anchors have been compared against the draft and which have not.
- **Un-analysed anchors get triaged.** During the hackathon demo, the drafter identifies at least one un-analysed neighbour from the task screen and either opens its analysis or defers it consciously — no pair sits invisibly unaccounted for.
- **Zero fabricated clauses.** Across every pair card rendered during the demo run, every clause quotation traces to a real entry in the clause index. Where no matching clause exists, the card shows "No matching clause found" rather than fabricated text.
- **One-click path into drafting.** From landing on the task screen, the drafter reaches the drafting workspace in one action via **Open draft**.

## Dependencies

- **Workstream graph screen.** The task screen is only reachable by clicking **Open task** on a `task`-type node on the workstream graph. Without the graph, there is no entry point.
- **Neighbour edges declared at task creation.** The six neighbour rows on this screen and the six pair cards on the pairwise comparison card come from the edges declared when the OpRes PD v0.3 task node was added to the workstream graph.
- **Review linkages screen.** Each analysed pair card's "Open in Review" link takes the drafter to the review linkages screen for that specific source-target pair.
- **Drafting workspace.** The **Open draft** action in the header (and the empty-state call-to-action) navigate to the drafting workspace for this task.
- **Widened linkage taxonomy.** Pair cards display the five semantic labels (`aligns-with`, `differs-on`, `conflicts-with`, `silent-on`, `goes-beyond`) plus the optional sentiment tag on `differs-on` — these come from the taxonomy-widening story.
- **Verbatim clause index.** Any clause referenced inside a pair card summary must resolve to a real entry in the parsed clause index for the cited document.

## Open Questions

- [x] ~~Should the task screen allow editing the neighbour list directly?~~ — **Resolved:** No. Neighbours are structural edges declared on the workstream graph; the task screen is read-only for the neighbour list. Editing lives on the graph.
- [x] ~~Does clicking Assign persist a reassignment in MVP1?~~ — **Resolved:** No. MVP1 shows the workflow picker to demonstrate the surface but does not persist a reassignment. Deferred to post-MVP1.
- [ ] Should the "Analyze linkages" click on an un-analysed pair navigate straight to the review screen, or stay on the task screen and render the findings inline? — **Deferred (non-blocking):** For the hackathon build, either behaviour is acceptable as long as the pair card updates to an analysed state after completion. Final choice can be made during the build week without gating the spec.

---

## Technical Design

### Functional Requirements

- Task screen route: `/workstreams/:workstreamId/tasks/:nodeId`. Only reachable when `nodeId` refers to a `task`-type node; other node types return `NOT_A_TASK` and the screen renders a redirect back to the workstream graph.
- Pairwise-comparison card renders one row per neighbour defined at the task's node creation. Neighbour order matches the edge order in `data/workstreams/{workstream_id}/graph.json`.
- Analysed pairs render finding cards; unanalysed pairs render a dashed "not analysed" card with an **Analyze linkages** button.
- Filter chip narrows the visible pair cards to a single neighbour via client-side filtering; no additional API round-trip is made when a chip is clicked.
- Empty-draft state (task has zero clauses parsed) renders an empty-state card with an **Open draft** button; no per-pair cards are rendered even if edges exist.
- **Assign** opens a shadcn `Dialog` with a static list of workstream members (Farid M., Priya S.). Selection does not need to persist in MVP1 — the picker closes on selection or dismissal.
- **Open draft** navigates via React Router to `/workstreams/:workstreamId/tasks/:nodeId/draft`.
- **Open in Review** on an analysed pair navigates to `/workstreams/:workstreamId/edges/:edgeId/review`.

### Permissions & Security

- Internal only, single-user demo. No auth in MVP1.
- No sensitive data leaves the local filesystem; all reads are against JSON under `data/workstreams/`.

### API Design

Extend `engine/api.py` with the following endpoints.

**`GET /api/workstreams/{workstream_id}/tasks/{node_id}`**

Returns the task metadata plus the ordered neighbour list with per-pair analysis status.

```json
{
  "task": {
    "id": "opres-pd-v0-3",
    "title": "OpRes PD — v0.3",
    "description": "Working draft of the Policy Document following the 2025 Discussion Paper",
    "status": "in_progress",
    "owner": { "id": "ar", "name": "Aisyah R." },
    "reviewers": [
      { "id": "fm", "name": "Farid M." },
      { "id": "ps", "name": "Priya S." }
    ],
    "clause_count": 42,
    "last_edited_at": "2026-07-13T14:30:00Z"
  },
  "neighbours": [
    {
      "node_id": "bcbs-opres-2021",
      "title": "BCBS OpRes 2021",
      "node_type": "international-standard",
      "edge_type": "contributes-to",
      "edge_id": "e-opres_v0_3--bcbs_opres_2021",
      "analysed": true,
      "findings_count": 3
    },
    {
      "node_id": "hkma-spm-or2",
      "title": "HKMA SPM OR-2",
      "node_type": "peer-regulator",
      "edge_type": "contributes-to",
      "edge_id": "e-opres_v0_3--hkma_spm_or2",
      "analysed": true,
      "findings_count": 1
    },
    {
      "node_id": "fsb-3rd-party",
      "title": "FSB Third-Party Toolkit",
      "node_type": "international-standard",
      "edge_type": "contributes-to",
      "edge_id": "e-opres_v0_3--fsb_3rd_party",
      "analysed": false,
      "findings_count": 0
    }
  ],
  "draft_empty": false
}
```

**`GET /api/workstreams/{workstream_id}/edges/{edge_id}/findings`**

Returns the `Connection[]` payload defined in the engine-taxonomy story for one analysed pair. Used to hydrate `PairwiseComparisonCard` finding one-liners.

**Error table**

| Status | Code                   | Condition                                                         |
| ------ | ---------------------- | ----------------------------------------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | `workstream_id` has no directory under `data/workstreams/`        |
| 404    | `NODE_NOT_FOUND`       | `node_id` is not present in `graph.json`                          |
| 400    | `NOT_A_TASK`           | `node_id` exists but its `node_type` is not `"task"`              |
| 404    | `EDGE_NOT_FOUND`       | `edge_id` on the findings endpoint is not present in `graph.json` |
| 409    | `DRAFT_EMPTY`          | Client requests findings on a task whose parsed clause count is 0 |
| 500    | `INTERNAL_ERROR`       | Unhandled server error while loading JSON                         |

### Data Model

Reuses `data/workstreams/{workstream_id}/graph.json` and `data/workstreams/{workstream_id}/findings/{edge_id}.json` from the workstream-graph story.

New computed field on task nodes: `draft_empty: bool`. Derived server-side as:

- `True` when no draft file exists under `data/workstreams/{workstream_id}/drafts/{node_id}.docx` (or the equivalent parsed clause file), OR when the parsed clause count for that draft is zero.
- `False` otherwise.

No new persistent field is added to `graph.json`; `draft_empty` is derived at read time so it stays in sync with the actual draft state.

### UI / Frontend Requirements

All components live under `frontend/src/features/task/`.

- `TaskScreenPage.tsx` — page-level route component; owns the TanStack Query for the task payload, renders the shell (breadcrumb, header, top-right toolbar) and composes children.
- `SourceCard.tsx` — shadcn `Card` with document metadata (title, format, clause count, last-edited), owner and reviewer `Avatar`s, status `Badge`.
- `NeighboursCard.tsx` — list of shadcn `Card` rows, colour-coded per `node_type` (international-standard, peer-regulator, internal-published, act-law, industry-input).
- `PairwiseComparisonCard.tsx` — top toolbar with a filter chip row (shadcn `Toggle` group or custom `Badge` variants) and a body that renders one `NeighbourFindingsCard` per neighbour that passes the filter. Also renders the "4 of 6 neighbours analysed" footer.
- `NeighbourFindingsCard.tsx` — for analysed pairs, shows the semantic label pill, the one-line summary, and an `Open in Review` link; for unanalysed pairs, shows a dashed-border empty state with a "not analysed" `Badge` and an **Analyze linkages** button.
- `AssignDialog.tsx` — shadcn `Dialog` with a static list of workstream members (Farid M., Priya S.); no persistence.
- `EmptyDraftCard.tsx` — rendered inside the pairwise section when `draft_empty` is true; includes an **Open draft** button.
- Top-right toolbar in `TaskScreenPage`: **Assign** button (opens `AssignDialog`) and **Open draft** link (React Router `<Link>`).

**Routes**

- `/workstreams/:workstreamId/tasks/:nodeId` — this screen.
- Navigation to `/workstreams/:workstreamId/tasks/:nodeId/draft` on **Open draft**.
- Navigation to `/workstreams/:workstreamId/edges/:edgeId/review` on **Open in Review**.

**State**

- TanStack Query key: `['task', workstreamId, nodeId]`.
- Findings for each analysed pair are fetched via `['findings', workstreamId, edgeId]` and rendered inside `NeighbourFindingsCard`.
- Filter chip state is local React state inside `PairwiseComparisonCard` (no server round-trip).
- The `Analyze linkages` mutation (from the workstream-graph story's `analyze` endpoint) invalidates `['task', workstreamId, nodeId]` on success so the pair card flips from unanalysed to analysed without a full reload.

### Architecture Notes

- Reuses the shadcn primitives already installed in the workstream-graph story: `Card`, `Badge`, `Dialog`, `Button`, `Avatar`, `Separator`.
- No new frontend or backend dependencies.
- Integration point: `engine/api.py`. The new endpoint reads `graph.json` and derives `draft_empty` from `engine/connections.py` (or its equivalent parsed-clause counter).
- Follows the same JSON-file persistence pattern as the rest of the epic — no database.

### Exemplar Files

- `engine/api.py` — FastAPI pattern (route decoration, Pydantic response models, error responses).
- `engine/connections.py` — pattern for reading parsed clause counts.
- `frontend/src/features/workstream-graph/GraphCanvas.tsx` (built in the workstream-graph story) — same visual language and shadcn conventions.
- `docs/poc/workstream-brain/task.html` — reference layout for the three-card grid and the filter chip row.

### Implementation Plan

- **Task 1 — Backend endpoint (small, INDEPENDENT).**
  Add `GET /api/workstreams/{workstream_id}/tasks/{node_id}` to `engine/api.py`. Include the `draft_empty` derivation, ordered neighbours from `graph.json`, and error codes `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`, `NOT_A_TASK`. Ships with unit tests.

- **Task 2 — Page shell (medium, SEQUENTIAL after workstream-graph Task 1).**
  Build `TaskScreenPage.tsx` with the breadcrumb, header, and top-right toolbar. Wire the TanStack Query and render loading/error/empty states.

- **Task 3 — Left column (small, SEQUENTIAL after Task 2).**
  Build `SourceCard.tsx` and `NeighboursCard.tsx`. Node-type colour coding lives in a small shared helper.

- **Task 4 — Pairwise comparison (medium, SEQUENTIAL after Task 2).**
  Build `PairwiseComparisonCard.tsx` (filter chip row, client-side filter, footer count) and `NeighbourFindingsCard.tsx` (analysed and unanalysed states). Includes the E2E flow.

- **Task 5 — Assign dialog (small, SEQUENTIAL after Task 2).**
  Build `AssignDialog.tsx` as a static picker.

- **Task 6 — Empty-draft state (small, INDEPENDENT of Tasks 3–5 once Task 2 is done).**
  Build `EmptyDraftCard.tsx` and branch on `draft_empty` inside `PairwiseComparisonCard`.

### Negative Constraints

- Do NOT allow editing the neighbour list on this screen. Adding or removing anchors lives on the workstream graph via node/edge editing.
- Do NOT run finder→critic inline on this screen. The **Analyze linkages** button delegates to the `analyze` endpoint owned by the workstream-graph story.
- Do NOT persist Assign selections in MVP1. The picker is cosmetic; do not add a `assignee` field to `graph.json`.
- Do NOT fabricate clause text. If a clause number does not resolve in the parsed clause index, omit that finding from the pair card or render "No matching clause found".
- Do NOT introduce a new persistence layer. Reuse `data/workstreams/{workstream_id}/…` JSON files only.

### Test Scenarios

Backend (pytest, `engine/tests/test_api.py`):

- `test_GET_task_returns_opres_pd_v0_3_with_6_neighbours` — happy path, six neighbours in `graph.json` order, `draft_empty=false`.
- `test_GET_task_404_NODE_NOT_FOUND` — request against an unknown node id returns 404 with code `NODE_NOT_FOUND`.
- `test_GET_task_400_NOT_A_TASK_for_bcbs_node` — request against `bcbs-opres-2021` returns 400 with code `NOT_A_TASK`.
- `test_GET_task_404_WORKSTREAM_NOT_FOUND` — request against an unknown workstream returns 404 with code `WORKSTREAM_NOT_FOUND`.
- `test_GET_task_draft_empty_true_when_no_draft_file` — task node exists but has no draft file: response carries `draft_empty=true` and neighbours still populated.
- `test_GET_task_neighbour_order_matches_graph_json` — neighbours in the response preserve the edge order declared in `graph.json`.

Frontend component tests (`npm run test`):

- Filter chip `HKMA` narrows the pairwise card to exactly 1 pair; clicking `All` restores 6.
- Unanalysed pair card renders the dashed treatment plus **Analyze linkages** button; no semantic label is shown.
- Analysed pair card renders the semantic label pill, one-line summary, and `Open in Review` link.
- `Assign` button opens the shadcn `Dialog` and shows both Farid M. and Priya S. options.
- Empty-draft state renders `EmptyDraftCard` with an **Open draft** button and no pair cards, even when the neighbours array is non-empty.
- Breadcrumb click routes to `/workstreams/:workstreamId`.

### Verification

- Backend: `pytest engine/tests/test_api.py::test_GET_task -v`.
- Frontend component: `cd frontend && npm run test`.
- E2E: `frontend/e2e/task-screen.spec.ts` — covers the flow "land on task → filter to HKMA → click Open in Review → return → click Open draft". Owned by Task 4.
- Manual: open `/workstreams/opres-v2/tasks/opres-pd-v0-3` in the running frontend, confirm three-card layout matches `docs/poc/workstream-brain/task.html`.

### Data Examples

**Example 1 — Analysed task, populated draft.**
`GET /api/workstreams/opres-v2/tasks/opres-pd-v0-3` returns `task.clause_count=42`, six neighbours in graph order, four with `analysed=true` (BCBS, HKMA, RMiT, FSA), two with `analysed=false` (FSB, ABM), and `draft_empty=false`.

**Example 2 — Empty draft on a valid task.**
`GET /api/workstreams/opres-v2/tasks/opres-pd-v0-0` returns `task.clause_count=0`, `draft_empty=true`, neighbours populated from `graph.json`. Frontend renders `EmptyDraftCard` and suppresses all pair cards.

**Example 3 — Wrong node type.**
`GET /api/workstreams/opres-v2/tasks/bcbs-opres-2021` returns HTTP 400 with body `{"code": "NOT_A_TASK", "message": "Node bcbs-opres-2021 is of type international-standard, not task"}`. Frontend routes the user back to the workstream graph.

**Example 4 — Missing workstream.**
`GET /api/workstreams/nonexistent-ws/tasks/opres-pd-v0-3` returns HTTP 404 with body `{"code": "WORKSTREAM_NOT_FOUND", "message": "Workstream nonexistent-ws not found"}`.
