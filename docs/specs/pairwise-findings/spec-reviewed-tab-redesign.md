# Reviewed Tab Redesign

**Epic:** [Pairwise Findings — Overview](spec.md)

**Ticket:** TBD

Redesigns the Reviewed tab in the open-draft view so it gathers every finding the
drafter has accepted anywhere in the task's neighbourhood — not only from documents
joined directly to her draft — and retires the Related · 1 hop tab, whose peer
context the Pairwise Findings box now covers more completely. Without this, a
finding accepted between RMiT 2025 and the Exposure Draft is accepted and then
invisible when the drafter sits down to write.

## User Story

As Aisyah R., I want the Reviewed tab to hold every linkage I have accepted,
wherever in my task's neighbourhood it came from, so that the decisions I made
surveying the landscape become the brief I draft from.

## Background & Context

**Current state:**

- The open-draft view has three tabs: **Reviewed**, **Related · 1 hop**, and
  **Copilot**. It opens on Reviewed.
- Reviewed lists accepted findings, but only from links touching the task document
  itself. On Open Finance PD 2026 that is one link — the draft against the 2025
  Exposure Draft — and that pair has no findings.
- Related · 1 hop lists findings on links between the task's directly-joined
  documents, without regard to whether they were accepted or dismissed. On the
  Operational Resilience workstream it is empty, because every link there runs from
  the task outward.
- Both lists render in attention order, and each card names the clauses it cites
  and links through to the comparison screen.

**Problem:**

- **Accepted findings disappear.** Once the Pairwise Findings box lets Aisyah
  accept a difference between RMiT 2025 and the Exposure Draft, that acceptance is
  recorded but never shown in the open-draft view, because RMiT is two steps from
  her draft. Accepting something and then losing it is worse than not offering to
  accept it.
- **Reviewed is empty in the demo path.** On a workstream where the drafter's
  document has no findings of its own yet, the tab she lands on is blank even after
  a day of judging findings.
- **Related · 1 hop mixes judged and unjudged.** It shows peer findings regardless
  of whether they were accepted or dismissed, so a finding Aisyah explicitly
  rejected can still sit beside her draft as if it were context she endorsed.
- **Two overlapping tabs.** With the Pairwise Findings box covering the whole
  neighbourhood, Related · 1 hop is a narrower view of the same material, split from
  Reviewed on an axis — how many steps away the documents are — that does not
  matter to a drafter.

## Target User & Persona

- **Who:** Aisyah R., a BNM policy drafter, writing the Open Finance Policy Document
  2026 in the drafting workspace.
- **Context:** She has spent the morning in the Pairwise Findings box judging 130
  findings, accepting the ones that should shape her drafting. She now clicks **Open
  draft** and expects those accepted findings beside her as she writes her
  incident-notification clause.
- **Current workaround:** She keeps the comparison screens open in other browser
  tabs and switches between them, or re-reads the source documents while drafting.

## Goals

- Show every accepted finding from the task's neighbourhood in the Reviewed tab,
  matching the Pairwise Findings box's reach exactly.
- Show only accepted findings — never pending, never dismissed.
- Keep each card citing the clauses it relies on, and keep the click-through to the
  full quoted comparison.
- Retire the Related · 1 hop tab without leaving the tab strip broken or a
  placeholder in its slot.
- Keep the drafter's decisions reversible from the tab, so a change of mind while
  drafting does not require going back to the task page.

## Non-Goals

- **No Recommendations tab.** The third slot stays empty in this story; its
  contents are a separate specification.
- **No new findings.** The tab reflects decisions already made; it never introduces
  a finding the drafter has not accepted.
- **No accepting from the Reviewed tab.** Pending findings are judged in the
  Pairwise Findings box or on the comparison screen. The tab holds what was
  accepted, and lets an acceptance be withdrawn.
- **No change to the Copilot tab.**
- **No change to the editor itself.**

## User Workflow

1. **Arriving from the task page.** Aisyah has accepted 18 findings in the Pairwise
   Findings box, including 6 from RMiT 2025 and 5 from the HKMA Open API Framework.
   She clicks **Open draft**.
2. **Landing on Reviewed.** The workspace opens on the Reviewed tab, which shows 18
   accepted findings. The tab strip now reads Reviewed and Copilot; Related · 1 hop
   is gone.
3. **Reading in attention order.** The list runs differences first, then silences,
   then goes-beyond, then alignments — the same order as the task page.
4. **Seeing where each came from.** Each card names its two documents, so she can
   tell the RMiT difference from the HKMA one at a glance, and shows the clause
   numbers it cites.
5. **Drafting against a decision.** She clicks the accepted RMiT
   incident-notification difference. The comparison opens with RMiT 10.32 and
   Exposure Draft 1.4(a) quoted, and she writes her clause with both in view.
6. **Changing her mind.** One accepted alignment turns out not to matter. She
   withdraws the acceptance from its card; it leaves the Reviewed list and returns
   to pending in the Pairwise Findings box.
7. **Continuing to write.** The tab's count drops to 17 and she carries on.

## Acceptance Criteria

### Scenario: Accepted findings from two steps away appear

```gherkin
Given I have accepted 6 findings between RMiT 2025 and the 2025 Exposure Draft
  And RMiT 2025 is two steps from my working draft
When I open the draft and read the Reviewed tab
Then all 6 of those accepted findings are listed
```

### Scenario: The tab gathers acceptances from across the whole neighbourhood

```gherkin
Given I have accepted 6 findings from RMiT 2025, 5 from the HKMA Open API Framework and 7 from BIS Papers 168
When I open the draft and read the Reviewed tab
Then the tab reports 18 accepted findings
  And each card names the two documents its finding relates
```

### Scenario: Pending and dismissed findings are excluded

```gherkin
Given the neighbourhood holds 130 findings
  And I have accepted 18 and dismissed 12, leaving 100 pending
When I open the draft and read the Reviewed tab
Then only the 18 accepted findings are listed
  And no dismissed finding appears
  And no pending finding appears
```

### Scenario: The list runs in attention order

```gherkin
Given I have accepted findings labelled differs-on, silent-on, goes-beyond and aligns-with
When I read the Reviewed tab
Then the findings run in the order conflicts-with, differs-on, silent-on, goes-beyond, aligns-with
  And that matches the order used on the task page
```

### Scenario: Each card cites its clauses

```gherkin
Given I have accepted the difference between RMiT 10.32 and Exposure Draft 1.4(a) on incident notification
When I read its card in the Reviewed tab
Then the card names both clause numbers
  And it shows the finding's summary
```

### Scenario: Opening a card shows the clauses word for word

```gherkin
Given the Reviewed tab lists my accepted RMiT incident-notification difference
When I click that card
Then the clause comparison opens with that finding selected
  And RMiT 10.32 and Exposure Draft 1.4(a) are quoted word for word
```

### Scenario: A finding with no supporting clause on one side

```gherkin
Given I have accepted a silent-on finding where the Exposure Draft has no corresponding clause
When I read its card in the Reviewed tab
Then the card tells me no matching clause was found on that side
  And no clause number is invented for it
```

### Scenario: Withdrawing an acceptance from the tab

```gherkin
Given the Reviewed tab lists 18 accepted findings
When I withdraw my acceptance of one alignment
Then it leaves the Reviewed tab
  And the tab reports 17 accepted findings
  And that finding is pending again in the Pairwise findings box
```

### Scenario: The Related · 1 hop tab is gone

```gherkin
Given I open the draft for the Open Finance PD 2026 task
When I read the tab strip
Then I see a Reviewed tab and a Copilot tab
  And no Related · 1 hop tab is offered
  And no empty placeholder tab occupies its place
```

### Scenario: Peer findings that were only ever shown under Related are now judged

```gherkin
Given a finding between RMiT 2025 and the Exposure Draft was previously visible under Related · 1 hop without being judged
When I open the draft after the redesign
Then that finding appears in the Reviewed tab only if I accepted it
  And if I have not judged it, I find it pending in the Pairwise findings box
```

### Scenario: Nothing accepted yet

```gherkin
Given I have not yet accepted any finding for this task
When I open the draft and read the Reviewed tab
Then it tells me no findings have been accepted yet
  And it points me to the Pairwise findings box on the task page to judge them
```

### Scenario: The tab reflects a decision made moments earlier

```gherkin
Given I accepted a difference in the Pairwise findings box and immediately clicked Open draft
When the Reviewed tab loads
Then that accepted difference is listed
```

### Scenario: A decision made on the comparison screen reaches the tab

```gherkin
Given I accepted a finding while reading the clause comparison
When I open the draft and read the Reviewed tab
Then that finding is listed
```

### Scenario: A blank working draft does not empty the tab

```gherkin
Given I have accepted 18 findings
  And my working draft still has no content
When I open the draft and read the Reviewed tab
Then all 18 accepted findings are listed
```

### Scenario Outline: Every accepted label reaches the tab

```gherkin
Given I have accepted a finding labelled <label>
When I read the Reviewed tab
Then that finding is listed under <label>

Examples:
  | label          |
  | conflicts-with |
  | differs-on     |
  | silent-on      |
  | goes-beyond    |
  | aligns-with    |
```

## Business Rules & Constraints

- **Same reach as the box.** The tab draws on links where at least one end is the
  task document or a document joined directly to it — the identical rule the
  Pairwise Findings box uses. The two surfaces never disagree about which findings
  are in scope.
- **Accepted only.** Pending and dismissed findings never appear. The exclusion is
  applied before the list reaches the drafter, not as something she filters away.
- **Attention order.** `conflicts-with`, `differs-on`, `silent-on`, `goes-beyond`,
  `aligns-with`, matching the task page and the comparison screen.
- **Each card names its pair.** With findings arriving from several documents, a
  card must say which two documents it relates, or the drafter cannot tell an HKMA
  difference from a RMiT one.
- **Clause numbers on the card, quoted clauses on the comparison screen.** Nothing
  on a card can misquote, because no card quotes.
- **No matching clause found.** Where a finding has no supporting clause on one
  side, the card says so. No clause number is ever invented.
- **Withdrawal is available, acceptance is not.** A drafter can undo an acceptance
  from the tab; she cannot accept a pending finding there, because the tab does not
  show pending findings.
- **One decision, everywhere.** Withdrawing an acceptance in the tab returns the
  finding to pending on the task page and the comparison screen.
- **The draft's content is never a gate.** A blank working draft does not empty or
  disable the tab.
- **Two tabs, not a placeholder.** Removing Related leaves Reviewed and Copilot. No
  disabled or coming-soon tab stands in for the future Recommendations tab.

## Success Metrics

- Accepted findings lost between the task page and the open-draft view fall from
  all of them — every finding from a document two steps away — to none.
- On the Open Finance PD 2026 workstream, a drafter who has accepted 18 findings
  sees 18 in the Reviewed tab, where today she would see 0.
- The open-draft view carries two tabs instead of three, removing a tab that showed
  unjudged findings beside the draft.
- A drafter can reach the quoted clauses behind any accepted finding in one click
  from the tab.

## Dependencies

- **The Pairwise Findings box** is what produces the acceptances this tab displays.
  Shipping this story before the box leaves the tab correct but sparsely populated.
- **The clause comparison screen must open on a nominated finding**, shared with
  the box story.
- **The Recommendations specification** claims the vacated third slot. This story
  must leave the tab strip coherent with two tabs until that lands.

## Open Questions

- [x] ~~Should the Reviewed tab match the box's reach, or stay narrower?~~ —
      **Resolved:** match it exactly. Any narrower rule means a finding can be
      accepted and then lost, which is the defect this story exists to fix.
- [x] ~~Should the Related · 1 hop tab survive alongside the redesign?~~ —
      **Resolved:** no. The Pairwise Findings box covers the same peer material more
      completely and with review state attached, and Related showed unjudged findings
      beside the draft as though endorsed.
- [x] ~~Should the vacated tab slot hold a placeholder for Recommendations?~~ —
      **Resolved:** no. A disabled tab advertises something the drafter cannot use;
      the slot stays empty until the Recommendations specification is built.
- [x] ~~Can a drafter accept a pending finding from the Reviewed tab?~~ —
      **Resolved:** no. Judging happens in the box or on the comparison screen, and
      the tab is the record of what was accepted. Withdrawal is allowed so a change
      of mind mid-draft does not send her back to the task page.
- [ ] Should accepted findings be groupable by document as well as by label in the
      tab? — **Deferred (non-blocking):** attention order is the drafting need, and
      each card names its pair. Revisit if drafters with many accepted findings ask
      to read them document by document.

---

## Functional Requirements

- **Scope parity:** the Reviewed tab must draw on exactly the edge set Story 1's box
  uses — `workstreams.neighbourhood_edges(edges, node_id)`. The two surfaces share
  one helper so they cannot diverge.
- **Accepted-only, server-side:** `review_state == "accepted"` is filtered in the
  engine, not the browser. This is an existing negative constraint from the
  drafting-workspace spec and it stands.
- **Attention order:** cards render in `LABEL_SEVERITY_ORDER` via the existing
  `bySeverity()`. No sinking or state-based sub-ordering — every card in this tab is
  accepted, so `forGroupDisplay` does not apply.
- **Endpoint labelling:** every card shows both endpoints. Cards arrive from several
  document pairs, so the existing `showBothEndpoints` mode of `LinkageRefCard`
  becomes the default here rather than an opt-in.
- **Withdrawal, not acceptance:** the tab offers exactly one state transition,
  `accepted → pending`. It must not offer accept or dismiss, because it does not
  show pending or dismissed findings.
- **Optimistic withdrawal with rollback:** the card leaves the list immediately and
  the tab count decrements; on failure it returns and an inline error appears.
- **No draft gate:** the tab's content must not vary with draft content.
- **Tab strip:** exactly two tabs — Reviewed and Copilot. No third tab, no disabled
  placeholder.
- **Idempotency:** repeated withdrawal of the same finding is a no-op returning the
  same body — guaranteed by `engine.findings.set_review_state`.

### Validation & Business Rules

- A finding with an empty `source_clauses` or `target_clauses` renders "No matching
  clause found" for that side. `LinkageRefCard` already receives
  `source_clause_number: null` in that case and must render the fallback rather than
  an empty slot.
- `sentiment` renders only on `differs-on`, via `labelText()`.
- Withdrawing sends `{"review_state": "pending"}` to the existing per-finding PATCH
  route. Any other value from this surface is a bug.
- A non-task node → `400 NOT_A_TASK` (existing `_task_node` guard).

## Permissions & Security

- **Scope:** internal read API, same trust boundary as the rest of
  `/api/workstreams/*`. No authentication in MVP1 and none added here.
- **Authorization:** none — same as the existing Reviewed tab.
- **Input validation:** `node_id` is resolved against `graph.json` membership before
  any findings path is built, so no path traversal is reachable through it. Existing
  behaviour of the route being modified.
- **Clause numbers only on cards.** Unchanged from today: `_linkage_card` deliberately
  omits clause text, so the tab cannot misquote. Quoted text lives on the comparison
  screen, sourced from the finding's own stored clauses.

## API Design

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/reviewed-linkages`

**Existing route, widened edge scope. Response shape unchanged**, so no consumer
contract breaks — callers simply receive more cards.

The only change: replace the current "every edge incident to the task node" scan
with `workstreams.neighbourhood_edges(...)`. The accepted-only filter, the
`_linkage_card` projection, and the `FindingsNotAnalysedError` tolerance all stay.

**Response (200)** — `open-finance-pd-2026`, after accepting one RMiT difference
and one HKMA alignment:

```json
{
  "findings": [
    {
      "id": "e-rmit_2025--ed_open_finance_2025~7",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "Both require incident notification, but RMiT sets a 1-hour trigger where the ED leaves the threshold to the institution.",
      "edge_id": "e-rmit_2025--ed_open_finance_2025",
      "left": {
        "id": "rmit-2025",
        "title": "RMiT 2025",
        "node_type": "internal-published"
      },
      "right": {
        "id": "ed-open-finance-2025",
        "title": "ED Open Finance 2025",
        "node_type": "internal-published"
      },
      "source_clause_number": "Rmit 2025 10.32",
      "target_clause_number": "ed-open-finance-2025 1.4(a)"
    },
    {
      "id": "e-hkma_open_api_framework--ed_open_finance_2025~3",
      "label": "aligns-with",
      "sentiment": null,
      "summary": "Both require consent to be explicit, informed and revocable by the customer.",
      "edge_id": "e-hkma_open_api_framework--ed_open_finance_2025",
      "left": {
        "id": "hkma-open-api-framework",
        "title": "HKMA Open API Framework",
        "node_type": "peer-regulator"
      },
      "right": {
        "id": "ed-open-finance-2025",
        "title": "ED Open Finance 2025",
        "node_type": "internal-published"
      },
      "source_clause_number": "HKMA Open API 4.1",
      "target_clause_number": "ed-open-finance-2025 2.3"
    }
  ]
}
```

Before this change the same request on the same fixture returns
`{"findings": []}` — the task's only edge has no findings file, so there is nothing
accepted to report.

`review_state` is **not** on these cards and is not needed: every card in the
response is accepted by construction. Story 1 adds `review_state` to `_linkage_card`
for the box's benefit; it rides along harmlessly here.

**Errors:** unchanged.

| Status | Code                   | Condition                                           |
| ------ | ---------------------- | --------------------------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | No `data/workstreams/{workstream_id}/graph.json`    |
| 400    | `NOT_A_TASK`           | The node is absent or its `node_type` is not `task` |

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/related-linkages`

**Deprecated, retained, unchanged.** The frontend stops calling it when the Related
tab is removed. It is not deleted: `engine/tests/test_api_drafting.py` covers it, the
`hops` validation is a documented contract, and keeping it is the rollback seam if
the Related tab has to come back. Add a one-line docstring note that no frontend
surface calls it as of this story.

### `PATCH /api/workstreams/{workstream_id}/edges/{edge_id}/findings/{finding_id}`

**Unchanged — reused for withdrawal.**

**Request:**

```json
{ "review_state": "pending" }
```

**Response (200):**

```json
{
  "finding": {
    "id": "e-hkma_open_api_framework--ed_open_finance_2025~3",
    "label": "aligns-with",
    "sentiment": null,
    "summary": "Both require consent to be explicit, informed and revocable by the customer.",
    "review_state": "pending",
    "source_clauses": [{ "clause_number": "HKMA Open API 4.1", "text": "…" }],
    "target_clauses": [
      { "clause_number": "ed-open-finance-2025 2.3", "text": "…" }
    ]
  },
  "counts": { "total": 47, "accepted": 0, "dismissed": 0 }
}
```

**Errors:**

| Status | Code                   | Condition                                        |
| ------ | ---------------------- | ------------------------------------------------ |
| 400    | `INVALID_REVIEW_STATE` | `review_state` not in pending/accepted/dismissed |
| 400    | `EDGE_NOT_ANALYSED`    | The edge has no findings file                    |
| 404    | `FINDING_NOT_FOUND`    | No finding on that edge carries `finding_id`     |

## UI/Frontend Requirements

### Components

**`DraftingWorkspacePage`** — `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx`

- **Type:** Modify.
- Changes:
  - `type TabKey = "reviewed" | "copilot"` — drop `"related"`.
  - Delete the `related` query (`fetchRelatedLinkages`), `relatedCards`, the
    `related` entry in `tabs`, and the whole `tab === "related"` block.
  - Add a withdrawal mutation calling `setReviewState(workstreamId, edgeId,
findingId, "pending")`, with the edge id taken from the card's `edge_id`.
  - On success invalidate `["reviewed-linkages", workstreamId, nodeId]`,
    `["pairwise-findings", workstreamId, nodeId]`, and
    `["review", workstreamId, edgeId]`.
  - Empty-state copy changes to name the box as the place findings are accepted.

**`LinkageRefCard`** — `frontend/src/features/drafting-workspace/LinkageRefCard.tsx`

- **Type:** Modify.
- Changes:
  - `showBothEndpoints` becomes the effective default for the Reviewed tab — cards
    now arrive from several pairs, so the endpoint pair must always be visible.
  - Add an optional withdrawal control:
    ```typescript
    interface Props {
      card: LinkageCard;
      isActive?: boolean;
      showBothEndpoints?: boolean;
      onSelect?: () => void;
      onWithdraw?: () => void;
      isWithdrawing?: boolean;
      errorMessage?: string;
    }
    ```
  - Render "No matching clause found" where a clause number is `null`.

**`CopilotTab`** — `frontend/src/features/drafting-workspace/CopilotTab.tsx`

- **Type:** Unchanged, but note it receives `reviewedCards` as a prop. That prop now
  carries the wider neighbourhood set, which is the desired behaviour — the Copilot's
  grounding improves for free. No code change; assert it still renders.

### User Interactions

| Action             | Result                                                                                               |
| ------------------ | ---------------------------------------------------------------------------------------------------- |
| Open the draft     | Lands on Reviewed, showing every accepted finding in the neighbourhood                               |
| Click a card       | Opens the comparison screen for that pair with that finding selected (`?finding=` — Story 1's param) |
| Click **Withdraw** | Card leaves the list optimistically, tab count −1, finding returns to pending in the box             |
| Click **Copilot**  | Switches tabs; the Copilot's grounding now includes the wider accepted set                           |

### States

- **Loading:** existing behaviour.
- **Empty:** "No findings accepted yet. Accept linkages in the Pairwise findings box
  on the task page and they appear here." — replaces the current copy, which points
  at "the review screen" only.
- **Withdrawal failed:** the card returns to the list and shows "Could not withdraw
  that decision. Try again."
- **Tab count:** the badge on the Reviewed tab shows the number of accepted findings.

## Architecture Notes

- **New dependencies:** none.
- **Dependencies & integration:** this story consumes what Story 1 produces. It
  depends on Story 1's `neighbourhood_edges` helper existing (Story 1 Task 1) and on
  the review screen's `?finding=` deep link (Story 1 Tasks 3, 8). If built in
  parallel, Story 1 Task 1 must land first.
- **Shared state:** the `review_state` field, written only through the existing
  per-finding PATCH route. Three surfaces read it; none of them owns it.
- **Query invalidation is bidirectional.** Story 1's box invalidates
  `reviewed-linkages`; this tab invalidates `pairwise-findings`. Both must invalidate
  `["review", workstreamId, edgeId]`. Missing any one of the three leaves a surface
  showing a decision the user has already reversed.
- **Why widen the existing route rather than add one:** `reviewed-linkages` already
  has exactly the right contract — task-scoped, accepted-only, `LinkageCard[]`. Only
  its edge scope is wrong. Widening it is a two-line change and keeps one route for
  one concept.

## Exemplar Files

- `engine/api.py:1883` (`get_reviewed_linkages`) — the exact function being
  modified; the change is its edge-scope line.
- `engine/workstreams.py:211` (`edges_between`) — the helper being superseded here,
  and its docstring note about `opres-v2` having no anchor↔anchor edges (which is
  why the Related tab was empty there).
- `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx:94` — the
  `tabs` array to shrink.
- `frontend/src/features/review-linkages/ReviewLinkagesPage.tsx:36` — the
  `setReviewState` mutation shape to copy for withdrawal.
- `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx:147` —
  the `Related · 1 hop` describe block to delete.
- `engine/tests/test_api_drafting.py` — the route's existing tests, to extend.

## Implementation Plan

### Sub-tasks

**Task 1: widen `reviewed-linkages` to the neighbourhood** — _small_

- Files: `engine/api.py`, `engine/tests/test_api_drafting.py`
- Swap the edge scan for `workstreams.neighbourhood_edges(...)`. Keep the
  accepted-only filter and the unanalysed-edge tolerance. Add the deprecation
  docstring note to `get_related_linkages`.
- SEQUENTIAL (depends on Story 1 Task 1 — the helper)

**Task 2: withdrawal control on `LinkageRefCard`** — _small_

- Files: `frontend/src/features/drafting-workspace/LinkageRefCard.tsx`
- Optional `onWithdraw` / `isWithdrawing` / `errorMessage`; both endpoints always
  shown; "No matching clause found" fallback.
- INDEPENDENT

**Task 3: retire the Related tab and wire withdrawal** — _medium_

- Files: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx`,
  `frontend/src/lib/api.ts`
- Two-tab strip, delete the related query and block, add the optimistic withdrawal
  mutation with three-way invalidation, update the empty-state copy. Leave
  `fetchRelatedLinkages` in `api.ts` but unreferenced — deleting it and the route
  together is a separate cleanup, and the rollback seam is worth more than the dead
  export.
- SEQUENTIAL (depends on Task 2)

**Task 4: MSW handlers + component tests** — _medium_

- Files: `frontend/src/test/msw/handlers.ts`,
  `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`
- Widen the `reviewed-linkages` handler to return neighbourhood cards for
  `open-finance-pd-2026`; delete the `Related · 1 hop` describe block; add
  withdrawal tests.
- SEQUENTIAL (depends on Task 3)

**Task 5: E2E spec** — _small_

- Files: `frontend/e2e/reviewed-tab.spec.ts` (new)
- The accept-then-open-draft loop. See Verification.
- SEQUENTIAL (depends on Task 4, and on Story 1 Task 10's box being clickable)

### Negative Constraints

- Do **NOT** delete `GET .../tasks/{node_id}/related-linkages` or its tests. It stays
  as a rollback seam.
- Do **NOT** delete `edges_between` from `engine/workstreams.py` — the deprecated
  route still calls it.
- Do **NOT** add a third tab, a disabled tab, or a "coming soon" placeholder for
  Recommendations.
- Do **NOT** add accept or dismiss controls to this tab. Withdrawal only.
- Do **NOT** filter review state in the browser. The engine filters; the tab renders
  what it is given.
- Do **NOT** modify any fixture under `data/workstreams/`.
- Do **NOT** change `engine/findings.py` or the per-finding PATCH route.
- Do **NOT** touch `CopilotTab.tsx`, `EditorPane.tsx`, or the draft autosave debounce.
- Do **NOT** re-implement the neighbourhood rule — import Story 1's helper.

## Test Scenarios

**Test 1: accepted second-order findings reach the route** _(engine)_

- Setup: copy `data/workstreams` to tmp; `PATCH
.../edges/e-rmit_2025--ed_open_finance_2025/findings/e-rmit_2025--ed_open_finance_2025~7`
  with `{"review_state": "accepted"}`.
- Action: `GET /api/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd/reviewed-linkages`
- Expected: `200`; exactly one card; its `id` is `~7`; its `edge_id` is the RMiT
  edge; `left.id == "rmit-2025"` and `right.id == "ed-open-finance-2025"`.

**Test 2: acceptances aggregate across pairs** _(engine)_

- Setup: accept 6 findings on the RMiT edge, 5 on the HKMA edge, 7 on the BIS edge.
- Action: same request.
- Expected: 18 cards; the `edge_id` distribution is `{rmit: 6, hkma: 5, bis: 7}`.

**Test 3: pending and dismissed are excluded** _(engine)_

- Setup: accept 18, dismiss 12, leave 100 pending.
- Action: same request.
- Expected: exactly 18 cards; no card's id is among the dismissed or pending ids.

**Test 4: before/after widening on the same fixture** _(engine)_

- Setup: accept one finding on the RMiT edge (a second-order edge).
- Action: same request.
- Expected: 1 card. This is the regression guard for the defect — the pre-change
  implementation returns 0 here because the RMiT edge does not touch the task node.

**Test 5: second-order↔second-order acceptances excluded** _(engine)_

- Setup: in the tmp copy only, add edge `e-hkma…--bis_papers_168` with one finding,
  and accept it.
- Action: same request.
- Expected: that finding is absent; the count matches the other accepted findings
  only.

**Test 6: `opres-v2` first-order acceptances still work** _(engine)_

- Setup: workstream `opres-v2`, node `opres-pd-v0-3`; accept one finding on
  `e-opres_v0_3--bcbs_opres_2021`.
- Action: `GET …/reviewed-linkages`
- Expected: 1 card — the pre-existing behaviour is preserved, not just the new
  behaviour added.

**Test 7: draft content does not affect the response** _(engine)_

- Setup: accept 3 findings; `PUT …/draft` with `{"content_html": "<p>1.1 Scope.</p>"}`.
- Action: `GET …/reviewed-linkages` before and after the draft write.
- Expected: both responses identical.

**Test 8: withdrawal removes a card from the route** _(engine)_

- Setup: accept 2 findings on the HKMA edge, then `PATCH` one back to `pending`.
- Action: `GET …/reviewed-linkages`
- Expected: 1 card; the withdrawn finding's id is absent.

**Test 9: route guards** _(engine)_

- Action / Expected:
  - `GET /api/workstreams/nope/tasks/x/reviewed-linkages` → `404`
    `WORKSTREAM_NOT_FOUND`
  - `GET /api/workstreams/open-finance-pd-2026/tasks/rmit-2025/reviewed-linkages` →
    `400` `NOT_A_TASK`

**Test 10: `related-linkages` still behaves** _(engine)_

- Action: `GET …/related-linkages?hops=1` and `?hops=2`.
- Expected: `200` for `hops=1`; `400 HOPS_OUT_OF_RANGE` for `hops=2`. Unchanged —
  the deprecation is documentation only.

**Test 11: the tab strip has two tabs** _(frontend, Vitest + MSW)_

- Action: render `/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd/draft`.
- Expected: `getAllByRole("tab")` has length 2, named `/Reviewed/` and `/Copilot/`;
  `queryByRole("tab", {name: /Related/})` is null; `queryByTestId("related-empty")`
  is null.

**Test 12: the tab lists neighbourhood acceptances in attention order** _(frontend)_

- Setup: MSW returns 18 accepted cards spanning three pairs, deliberately in a
  non-severity order.
- Expected: rendered order is `conflicts-with` → `differs-on` → `silent-on` →
  `goes-beyond` → `aligns-with`; the Reviewed tab badge reads `18`.

**Test 13: each card names both endpoints** _(frontend)_

- Setup: as Test 12.
- Expected: a card sourced from the RMiT edge shows both "RMiT 2025" and "ED Open
  Finance 2025"; a card from the HKMA edge shows "HKMA Open API Framework" and "ED
  Open Finance 2025".

**Test 14: clicking a card deep-links to the comparison** _(frontend)_

- Action: click the card for `e-rmit_2025--ed_open_finance_2025~7`.
- Expected: navigation to
  `/workstreams/open-finance-pd-2026/edges/e-rmit_2025--ed_open_finance_2025/review?finding=e-rmit_2025--ed_open_finance_2025~7`.

**Test 15: withdrawal removes the card and decrements the badge** _(frontend)_

- Setup: 18 accepted cards; MSW `PATCH` returns `200` with `review_state: "pending"`.
- Action: click Withdraw on one card.
- Expected: 17 cards; badge reads `17`; the withdrawn card is absent.

**Test 16: withdrawal failure restores the card** _(frontend)_

- Setup: MSW `PATCH` returns `500`.
- Action: click Withdraw.
- Expected: the card is back in the list; badge reads `18`; "Could not withdraw that
  decision. Try again." shown on the card.

**Test 17: no accept or dismiss controls exist** _(frontend)_

- Setup: as Test 12.
- Expected: no element with accessible name `Accept` or `Dismiss` inside the
  Reviewed panel.

**Test 18: empty state names the box** _(frontend)_

- Setup: MSW returns `{"findings": []}`.
- Expected: the copy mentions the Pairwise findings box and the task page; the badge
  reads `0`.

**Test 19: blank draft does not empty the tab** _(frontend)_

- Setup: MSW draft returns `{"content_html": ""}`; reviewed returns 18 cards.
- Expected: 18 cards render.

**Test 20: "No matching clause found" on a one-sided finding** _(frontend)_

- Setup: an accepted `silent-on` card with `target_clause_number: null`.
- Expected: the card shows "No matching clause found" on the target side; no clause
  number is rendered there.

**Test 21: the Copilot tab still works with the wider set** _(frontend)_

- Action: switch to Copilot, send a message.
- Expected: the existing Copilot behaviour is unchanged; it receives the 18 accepted
  cards without error. (Regression guard on the `reviewedCards` prop widening.)

## Acceptance Criteria

- [ ] `GET .../reviewed-linkages` returns accepted findings from second-order edges;
      the pre-change implementation returns zero for the same setup.
- [ ] Pending and dismissed findings never appear in the response.
- [ ] `opres-v2`'s first-order behaviour is unchanged.
- [ ] The open-draft view has exactly two tabs; no Related tab and no placeholder.
- [ ] Cards render in attention order and name both endpoints.
- [ ] Clicking a card opens the comparison with that finding selected.
- [ ] Withdrawal works, decrements the badge, returns the finding to pending in the
      box, and rolls back on failure.
- [ ] No accept or dismiss control exists in the tab.
- [ ] `GET .../related-linkages` and its tests still pass unchanged.
- [ ] `.venv/bin/python -m pytest engine/tests` is green.
- [ ] `cd frontend && npm run test` is green, and `npx tsc -b` reports no errors.
- [ ] No fixture under `data/workstreams/` is modified.

## Verification

Run the verifier skill to confirm changes are clean.

### Backend API Tests

| File                                           | Covers                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------- |
| `engine/tests/test_api_drafting.py` _(modify)_ | Tests 1–10: widened scope, guards, and the retained `related-linkages` contract |

Use the existing `TestClient` + `shutil.copytree` fixture pattern. Test 4 is the
one that must be written to fail against the current implementation before the
change — it is the regression guard for the whole story.

Run: `.venv/bin/python -m pytest engine/tests -q` (Windows:
`.venv/Scripts/python.exe -m pytest engine/tests`).

### Browser/UI Testing

1. Engine on 8000, app on 5173 with `VITE_API_BASE` set (see Story 1).
2. Open the Open Finance PD 2026 task page. In the Pairwise findings box, accept
   two `differs-on` findings from RMiT 2025 and one `aligns-with` from the HKMA
   framework.
3. Click **Open draft**.
4. Expect: the tab strip shows **Reviewed** and **Copilot** only.
5. Expect: Reviewed holds 3 cards, differences before the alignment, each naming
   its two documents and its clause numbers.
6. Click the RMiT card — expect the comparison screen with that finding selected and
   its clauses highlighted. Press back.
7. Click **Withdraw** on the HKMA alignment — expect 2 cards and a badge of 2.
8. Return to the task page — expect that HKMA finding pending again, floated above
   the judged cards in `aligns-with`.
9. Regression: open `/workstreams/opres-v2/tasks/opres-pd-v0-3/draft` and confirm the
   Reviewed tab still shows its accepted findings and the Copilot tab still responds.

After a local run, `git checkout data/workstreams/open-finance-pd-2026` — accepting
and withdrawing write to a tracked path.

### E2E Tests

| Key Scenario                                                    | Test file                           | Assigned sub-task |
| --------------------------------------------------------------- | ----------------------------------- | ----------------- |
| Accepted findings from two steps away appear                    | `frontend/e2e/reviewed-tab.spec.ts` | Task 5            |
| The tab gathers acceptances from across the whole neighbourhood | `frontend/e2e/reviewed-tab.spec.ts` | Task 5            |
| The Related · 1 hop tab is gone                                 | `frontend/e2e/reviewed-tab.spec.ts` | Task 5            |
| Opening a card shows the clauses word for word                  | `frontend/e2e/reviewed-tab.spec.ts` | Task 5            |
| Withdrawing an acceptance from the tab                          | `frontend/e2e/reviewed-tab.spec.ts` | Task 5            |
| The tab reflects a decision made moments earlier                | `frontend/e2e/reviewed-tab.spec.ts` | Task 5            |

Scenarios covered by the tests above rather than E2E: the pending/dismissed
exclusion and the attention-order guarantee (engine tests 3 and frontend test 12 —
asserting server-side filtering is not an E2E concern), the empty state (frontend
test 18), the one-sided-clause case (frontend test 20), and the blank-draft
invariance (engine test 7). Scenario "Peer findings that were only ever shown under
Related are now judged" is verified by frontend test 11 plus Story 1's box tests —
it asserts an absence, which E2E cannot demonstrate meaningfully.

**Locator strategies:**

- `role="tab"` with accessible names `Reviewed`, `Copilot`; `data-testid="count-reviewed"`
  for the badge
- `aria-label="Reviewed linkages"` — the panel
- `data-testid="linkage-ref-card"` with `data-finding-id` and `data-edge-id`
- Withdrawal by accessible name `Withdraw`
- The E2E begins on the task page and accepts through the box, so it also depends on
  Story 1's locators (`data-testid="finding-card"`, action name `Accept`).

E2E setup per `frontend/e2e/README.md`. The spec header must note that a run writes
review state into `data/workstreams/open-finance-pd-2026` and requires
`git checkout data/workstreams/open-finance-pd-2026` afterwards.
