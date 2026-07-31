# Pairwise Findings Box

**Epic:** [Pairwise Findings — Overview](spec.md)

**Ticket:** TBD

Replaces the task page's "Pairwise comparison" box with **Pairwise findings** — a
review surface that draws semantic linkages from the whole neighbourhood around the
task rather than only from documents joined directly to it, and shows them from the
moment the workstream has been analysed rather than waiting for the drafter to
write clauses. Findings are grouped by semantic label with honest counts, filtered
by any combination of documents, and accepted or dismissed without leaving the
page.

## User Story

As Aisyah R., I want to see and judge every semantic linkage around my task from
the moment I open it — before I have written a single clause — so that I understand
the landscape I am drafting into and can record my position on each difference
while it is in front of me.

## Background & Context

**Current state:**

- The box is titled "Pairwise comparison · draft vs neighbours" and described as
  "Finder→critic linkages between the working draft and each neighbour node."
- When the working draft is blank, the box replaces its whole content with a
  message saying no findings can exist until the draft has content, and hides the
  document filter.
- The box shows one card per document joined directly to the task. Each card shows
  one headline finding, a count, and a link into the comparison screen.
- The document filter is single-select: choosing one document replaces the
  selection.
- Accepting or dismissing a finding is only possible on the comparison screen.
- A footer reports how many of the directly-joined documents have been analysed.

**Problem:**

- **Aisyah's first act is blocked.** Understanding what RMiT, the HKMA framework
  and BIS Papers 168 already say about the Exposure Draft is the work she does
  _before_ writing. The box refuses to show it until after.
- **130 existing findings are unreachable.** On Open Finance PD 2026, the Exposure
  Draft has 51 findings against RMiT 2025, 47 against the HKMA Open API Framework
  and 32 against BIS Papers 168. The task page shows none of them, because none of
  those pairs involves the task document.
- **One headline buries fifty.** A pair with 51 findings contributes one visible
  line. If that headline is an alignment, a difference on incident-reporting
  timelines is invisible.
- **Every judgement costs a round trip.** Accepting one finding means navigating to
  the comparison screen and back, losing her position in the list.
- **The filter forces repeated passes.** Comparing the two peer regulators side by
  side means selecting one, reading, then selecting the other.

## Target User & Persona

- **Who:** Aisyah R., a BNM policy drafter who owns the Open Finance Policy
  Document 2026 working draft and must reconcile it against the 2025 Exposure
  Draft, RMiT 2025, the HKMA Open API Framework, BIS Papers 168 and the ABS-MAS API
  Playbook.
- **Context:** She opens the task on 30 July with an empty working draft, intending
  to spend the day understanding what the surrounding documents already say before
  drafting anything. She returns to this box each day to check what she has judged
  and what is still pending.
- **Current workaround:** She reads the Exposure Draft and each peer document
  manually, keeping notes on differences in a personal spreadsheet, and repeats the
  exercise each drafting cycle because nothing persists.

## Goals

- Populate the box whenever findings exist in the task's neighbourhood, regardless
  of the working draft's content.
- Draw on findings from links where either end is the task document or a document
  joined directly to it.
- Group findings by semantic label in attention order, with a truthful total and
  pending count per group.
- Let the drafter accept or dismiss any finding from its card, and reach the full
  clause comparison in one click with that finding selected.
- Keep acted-on findings visible but out of the way, so pending work stays at the
  top of each group.
- Keep never-analysed pairs visible so coverage gaps are not silently hidden.
- Allow any combination of documents to be selected in the filter at once.

## Non-Goals

- **No bulk accept or dismiss.** Each finding is judged on its own card.
- **No change to how findings are produced.** This story changes which existing
  findings are surfaced and how they are reviewed.
- **No editing of the neighbourhood.** Documents and the links between them are
  managed on the workstream graph.
- **No links between two documents that are both two steps from the task.** A
  linkage between the HKMA framework and BIS Papers 168 does not appear.
- **No search across finding text.** Narrowing is by document and by label only.
- **No changes to the open-draft view.** The Reviewed tab is the second story.

## User Workflow

1. **Opening the task.** Aisyah clicks the Open Finance PD 2026 document on the
   workstream graph, then **Open task**. Her working draft is blank.
2. **Reading the box.** On the right, the box is headed **Pairwise findings**, with
   the description "Semantic linkages (differs-on, conflicts-with, silent-on,
   aligns-with, goes-beyond) between nodes". It is populated — no empty-draft
   message appears.
3. **Reading the shape of the work.** Five label groups in attention order tell her
   there are no conflicts, 30 differences, 11 silences, 14 places one document goes
   beyond the other, and 75 alignments.
4. **Noticing what has not been looked at.** A strip above the groups says two
   pairs have never been analysed — the ABS-MAS API Playbook against the Exposure
   Draft, and her own draft against the Exposure Draft. She analyses the ABS-MAS
   pair.
5. **Narrowing to the peer regulators.** She selects the HKMA chip and the RMiT
   chip together. The groups narrow to those two documents' findings, keeping the
   same label structure and updating each count.
6. **Judging from the card.** A difference summary reads that RMiT sets a one-hour
   incident notification trigger where the Exposure Draft leaves the threshold to
   the institution. She clicks **Review**.
7. **Reading the clauses.** The comparison screen opens on that pair with this
   finding selected, RMiT 10.32 and Exposure Draft 1.4(a) quoted word for word.
   She accepts it there and returns to the task page.
8. **Seeing her decision land.** The card is muted, marked accepted, and has sunk
   below the pending differences in its group. The group still reads 30, now with
   29 pending.
9. **Working through the rest.** She accepts and dismisses alignments straight from
   their cards without opening the comparison. Each acted-on card sinks, so the
   pending ones stay at the top.
10. **Correcting a misclick.** She dismisses one card by accident, clicks **Undo**
    on it, and it returns to pending at the top of its group.
11. **Finishing.** With every group's pending count at zero, she clicks **Open
    draft** to start writing.

## Acceptance Criteria

### Scenario: The box is populated when the working draft is blank

```gherkin
Given I own the Open Finance PD 2026 task
  And my working draft has no content
  And the workstream holds 130 findings across three analysed document pairs
When I open the task page
Then the Pairwise findings box lists findings
  And no message tells me findings require draft content
  And the document filter is available
```

### Scenario: The box is titled and described in the new vocabulary

```gherkin
Given I am on the Open Finance PD 2026 task page
When I read the Pairwise findings box heading
Then it is titled "Pairwise findings"
  And it is described as "Semantic linkages (differs-on, conflicts-with, silent-on, aligns-with, goes-beyond) between nodes"
```

### Scenario: Findings from documents two steps away are included

```gherkin
Given my Open Finance PD 2026 draft is joined only to the 2025 Exposure Draft
  And the Exposure Draft is joined to RMiT 2025, the HKMA Open API Framework and BIS Papers 168
When I open the task page
Then I see the 51 findings between RMiT 2025 and the Exposure Draft
  And I see the 47 findings between the HKMA Open API Framework and the Exposure Draft
  And I see the 32 findings between BIS Papers 168 and the Exposure Draft
```

### Scenario: Findings between two documents that are both two steps away are excluded

```gherkin
Given the HKMA Open API Framework and BIS Papers 168 are each two steps from my draft
  And a linkage exists between those two documents
When I open the task page
Then no finding from that linkage appears in the Pairwise findings box
```

### Scenario: Findings are grouped by label in attention order with counts

```gherkin
Given the neighbourhood holds 0 conflicts, 30 differences, 11 silences, 14 goes-beyond findings and 75 alignments
When I open the Pairwise findings box
Then I see five label groups in the order conflicts-with, differs-on, silent-on, goes-beyond, aligns-with
  And each group shows its total and how many are still pending
  And every finding in every group is shown without a "show more" control
```

### Scenario: An empty label group shows its zero rather than vanishing

```gherkin
Given the neighbourhood holds no conflicts-with findings
When I open the Pairwise findings box
Then the conflicts-with group is shown with a count of zero
  And it tells me none were found
```

### Scenario: A card shows the summary and three stacked actions

```gherkin
Given a difference exists between RMiT 2025 and the Exposure Draft on incident notification timing
When I read its card in the Pairwise findings box
Then I see its label, the two documents it relates, and its one-line summary
  And I see Review, Accept and Dismiss actions on the card
  And no clause text is quoted on the card
```

### Scenario: Accepting from the card sinks it within its own group

```gherkin
Given the differs-on group holds 30 findings, all pending
When I accept the RMiT incident-notification difference from its card
Then the group still reports 30 findings
  And it reports 29 pending
  And the accepted card is shown as accepted, below every pending card in the differs-on group
  And the accepted card stays inside the differs-on group rather than moving elsewhere
```

### Scenario: Dismissing from the card sinks it within its own group

```gherkin
Given the aligns-with group holds 75 findings, all pending
When I dismiss one alignment from its card
Then the group still reports 75 findings
  And it reports 74 pending
  And the dismissed card is shown as dismissed, below every pending card in the aligns-with group
```

### Scenario: Undoing a decision returns the finding to pending

```gherkin
Given I have just dismissed an alignment by mistake
When I click Undo on that card
Then the finding is pending again
  And its card returns above the acted-on cards in the aligns-with group
  And the group's pending count returns to 75
```

### Scenario: Review opens the comparison on the chosen finding

```gherkin
Given the differs-on group holds 30 findings from several document pairs
When I click Review on the RMiT incident-notification difference
Then the clause comparison for RMiT 2025 and the Exposure Draft opens
  And that difference is the selected finding
  And RMiT 10.32 and Exposure Draft 1.4(a) are quoted word for word
```

### Scenario: A decision made on the comparison screen shows on the task page

```gherkin
Given I clicked Review on the RMiT incident-notification difference
  And I accepted it on the comparison screen
When I return to the task page
Then that card is shown as accepted
  And it sits below the pending cards in the differs-on group
```

### Scenario: Selecting several documents in the filter at once

```gherkin
Given the box holds findings from RMiT 2025, the HKMA Open API Framework and BIS Papers 168
When I select the RMiT chip and the HKMA chip together
Then I see findings from RMiT 2025 and the HKMA Open API Framework
  And I see no findings from BIS Papers 168
  And each label group's counts describe only the filtered findings
```

### Scenario: Deselecting one of several selected documents

```gherkin
Given I have selected the RMiT chip and the HKMA chip
When I deselect the RMiT chip
Then I see only findings from the HKMA Open API Framework
  And the HKMA chip stays selected
```

### Scenario: Clearing the filter

```gherkin
Given I have selected the RMiT chip and the HKMA chip
When I select All
Then no individual document chip is selected
  And every finding in the neighbourhood is shown again
```

### Scenario: Filtering to a document whose findings are all acted on

```gherkin
Given I have accepted every one of the 32 findings from BIS Papers 168
When I select only the BIS Papers 168 chip
Then each label group reports zero pending
  And the accepted cards are still shown
```

### Scenario: Never-analysed pairs appear in the coverage strip

```gherkin
Given the ABS-MAS API Playbook has never been compared against the Exposure Draft
  And my working draft has never been compared against the Exposure Draft
When I open the Pairwise findings box
Then a strip above the label groups tells me two pairs have not been analysed
  And it names the ABS-MAS API Playbook against the Exposure Draft
  And it names my draft against the Exposure Draft
  And each has its own action to analyse it
```

### Scenario: Analysing a pair from the coverage strip

```gherkin
Given the coverage strip offers to analyse the ABS-MAS API Playbook against the Exposure Draft
When I run that analysis and it finds linkages
Then those findings join the label groups in the right groups
  And each affected group's total and pending count rise accordingly
  And that pair leaves the coverage strip
```

### Scenario: Analysing a pair that yields no linkages

```gherkin
Given the coverage strip offers to analyse my draft against the Exposure Draft
  And my working draft is blank
When I run that analysis and it finds nothing
Then I am told no matching clause was found for that pair
  And the label groups are unchanged
```

### Scenario: An analysis that cannot complete

```gherkin
Given the coverage strip offers to analyse the ABS-MAS API Playbook against the Exposure Draft
When the analysis cannot be completed
Then I am told the analysis failed and can retry
  And the pair stays in the coverage strip
  And no partial findings are added to any group
```

### Scenario: The coverage strip disappears when every pair is analysed

```gherkin
Given every pair in the neighbourhood has been analysed
When I open the Pairwise findings box
Then no coverage strip is shown
  And the label groups start at the top of the box
```

### Scenario: A task whose neighbourhood has no findings at all

```gherkin
Given my task is joined to one document and that pair has never been analysed
  And no other pair in the neighbourhood has been analysed
When I open the task page
Then the Pairwise findings box tells me no linkages have been surfaced yet
  And the coverage strip lists that pair with an action to analyse it
  And no message blames my draft for being empty
```

### Scenario: A task with no declared neighbours

```gherkin
Given I have just created a task and declared no other documents
When I open the task page
Then the Pairwise findings box tells me the task has no neighbouring documents yet
  And it points me to the workstream graph to add them
```

### Scenario Outline: A tighten or loosen direction shows only on a difference

```gherkin
Given a finding carries the label <label>
When I read its card in the Pairwise findings box
Then the direction shown is <shown>

Examples:
  | label          | shown                    |
  | differs-on     | tighten or loosen        |
  | conflicts-with | no direction             |
  | silent-on      | no direction             |
  | goes-beyond    | no direction             |
  | aligns-with    | no direction             |
```

### Scenario: The header metrics describe the neighbourhood

```gherkin
Given the neighbourhood holds 130 findings across three analysed pairs and two unanalysed pairs
When I read the metric tiles at the top of the task page
Then the findings total counts every finding in the neighbourhood
  And the analysed count describes pairs in the neighbourhood, not only documents joined to my draft
```

## Business Rules & Constraints

- **Neighbourhood rule.** A finding qualifies when at least one end of its link is
  the task document or a document joined directly to the task. On Open Finance PD
  2026 that admits five pairs: draft↔Exposure Draft, and the Exposure Draft against
  each of RMiT 2025, the HKMA Open API Framework, BIS Papers 168 and the ABS-MAS
  API Playbook.
- **The draft's content is never a gate.** No control is disabled and no content
  hidden because the working draft is blank.
- **Group order is fixed.** `conflicts-with`, `differs-on`, `silent-on`,
  `goes-beyond`, `aligns-with` — always, filtered or not.
- **Every card renders.** No group truncates, samples or hides findings behind a
  "show more". A group reporting 75 shows 75 cards.
- **Two counts per group.** The total never changes as findings are judged; the
  pending count falls. A group reading "30 · 12 pending" means 18 have been judged.
- **Acted-on cards sink within their own group.** An accepted `differs-on` finding
  goes to the bottom of `differs-on`, never to a separate section and never to
  another label's group.
- **Ordering within a group.** Pending findings first in their existing order, then
  acted-on findings. Accepted and dismissed cards are visually distinguishable from
  each other.
- **Every decision is reversible.** Accepted and dismissed cards offer an undo that
  returns the finding to pending.
- **One decision, everywhere.** A finding accepted on the card, on the comparison
  screen, or in the review queue reads as accepted in all three.
- **Filter is multi-select.** Chips toggle independently; any combination is valid.
  With none selected, everything shows. Counts always describe the visible set.
- **Filter chips cover the neighbourhood.** Every document contributing a finding
  gets a chip, including documents two steps from the draft.
- **Cards carry no clause text.** The card shows the summary and clause numbers;
  the quoted clauses live on the comparison screen, so nothing on a card can
  misquote.
- **Review carries the finding.** Clicking Review opens the comparison for that
  pair with that finding selected, not the pair's first finding.
- **No matching clause found.** Where a finding has no supporting clause on one
  side, the surface says so rather than paraphrasing.

## Success Metrics

- On the Open Finance PD 2026 workstream with a blank working draft, findings shown
  on the task page rise from 0 to 130.
- Findings reachable without leaving the task page rise from 1 headline per
  directly-joined document to every finding in the neighbourhood.
- Judging a finding requires zero navigations away from the task page, down from
  one round trip per finding.
- A drafter can state her pending workload for each of the five labels from the top
  of the box without scrolling or counting.
- Coverage gaps stay visible: every never-analysed pair in the neighbourhood is
  named on the page, so no pair is silently omitted.

## Dependencies

- **Findings must already exist for a pair to contribute.** Pairs never analysed
  appear in the coverage strip instead. The demo workstreams ship with their
  findings produced, so nothing needs analysing during a demo.
- **The clause comparison screen must open on a nominated finding**, rather than
  always selecting the pair's first finding.
- **The Reviewed tab redesign** consumes what this story accepts. Until it lands, a
  finding accepted from a document two steps away will not appear in the open-draft
  view.

## Open Questions

- [x] ~~Should the box reach beyond documents joined directly to the task?~~ —
      **Resolved:** yes, to links where either end is the task or a directly-joined
      document. Links between two documents that are both two steps away are
      excluded as noise.
- [x] ~~Should any findings be collapsed by default given 75 alignments?~~ —
      **Resolved:** no. All cards render; the multi-select filter is the tool for
      narrowing, and hiding cards would undercut the honest-counts rule.
- [x] ~~What does a card show?~~ — **Resolved:** the summary, its label, the two
      documents, and Review / Accept / Dismiss. Clause text stays on the comparison
      screen.
- [x] ~~Where do acted-on cards go?~~ — **Resolved:** to the bottom of their own
      label group, muted, with undo. The group total stays truthful and pending work
      stays at the top.
- [x] ~~Can several documents be filtered at once?~~ — **Resolved:** yes.
      Comparing two peer regulators together is a real need that single-select
      forces into two passes.
- [x] ~~Where does the analyse action live once cards are grouped by label?~~ —
      **Resolved:** a coverage strip above the groups, which disappears when every
      pair is analysed.
- [ ] Should the box remember a drafter's filter selection between visits to the
      task page? — **Deferred (non-blocking):** the box is usable either way, and
      the demo path selects filters fresh each time. Revisit if drafters report
      re-selecting the same documents daily.
- [ ] Should a "hide judged findings" control be offered once a drafter has worked
      through most of a group? — **Deferred (non-blocking):** sinking acted-on cards
      already keeps pending work at the top. Add only if long groups prove hard to
      work through in practice.

---

## Functional Requirements

- **Neighbourhood scope:** the box must render findings from every edge returned by
  `workstreams.neighbourhood_edges(edges, node_id)` — the task's own edges plus
  every edge incident to a first-order neighbour. Edges with both endpoints
  second-order must be excluded.
- **Edge direction agnostic:** the box must not assume the task node is the edge
  source. `open-finance-pd-2026` stores edges pointing into the ED node, the
  reverse of `opres-v2`.
- **No draft gate:** the response must not vary with draft content, and the
  frontend must not read `draft_empty` to decide what to render.
- **Grouping:** exactly five groups, always all five present, in
  `LABEL_SEVERITY_ORDER` (`conflicts-with`, `differs-on`, `silent-on`,
  `goes-beyond`, `aligns-with`). A group with zero findings renders its header with
  a zero count and an empty note.
- **Counts:** each group shows `total` (never changes as findings are judged) and
  `pending` (falls as they are). Both are computed over the **currently filtered**
  set.
- **No truncation:** every card in every group renders. No `slice`, no windowing,
  no "show more".
- **Within-group order:** pending findings first, in server order; then accepted
  and dismissed. Stable sort, so findings sharing a state keep server order.
- **Atomicity:** a review-state write touches exactly one finding in one edge's
  findings file. `engine.findings.set_review_state` already reads-modifies-writes
  the whole list, which is the atomic unit; no change needed.
- **Idempotency:** `PATCH` of the same `review_state` twice is a no-op returning
  the same body — already guaranteed by `set_review_state`.
- **Optimistic UI with rollback:** accept/dismiss/undo updates the card
  immediately, then reconciles. On failure the card reverts to its prior state and
  an inline error appears.

### Validation & Business Rules

- `review_state` must be one of `pending` / `accepted` / `dismissed`; anything else
  → `400 INVALID_REVIEW_STATE`. Existing behaviour, unchanged.
- A node that is not `node_type: "task"` → `400 NOT_A_TASK`. Existing behaviour of
  `_task_node`, reused.
- A missing workstream → `404 WORKSTREAM_NOT_FOUND`; a missing node → `404
NODE_NOT_FOUND`.
- An edge with no findings file is **unanalysed**, not "analysed with zero
  findings" — it contributes to `unanalysed_pairs`, never to a label group.
- `sentiment` renders only when `label === "differs-on"`, via the existing
  `labelText()`. Any sentiment on another label is ignored at render time (the
  engine already guards this in `engine/tests/test_taxonomy_traces.py`).
- A finding whose `source_clauses` or `target_clauses` is empty renders "No
  matching clause found" for that side. Never fabricate a clause number.

## Permissions & Security

- **Scope:** internal read API, same trust boundary as every other
  `/api/workstreams/*` route. No authentication exists in MVP1 and none is added
  here.
- **Authorization:** none. Any caller who can reach the engine can read and write
  review state, matching the existing review screen.
- **Input validation:** `workstream_id`, `node_id` and `edge_id` are path segments
  used to build filesystem paths under `workstreams_dir`. The existing routes
  already resolve them against `graph.json` membership before touching disk — the
  new route must do the same (a `node_id` not in the graph 404s before any path is
  constructed), so no traversal via `../` is reachable.
- **No clause text on the new route's cards** — only clause numbers. Reduces the
  blast radius of the verbatim guarantee to the review route, which quotes from the
  finding's own stored text.

## API Design

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/pairwise-findings`

New route. Projects every finding in the task's neighbourhood, plus the coverage
list of never-analysed pairs, plus the filter's document list. Replaces the task
screen's per-neighbour `GET .../edges/{edge_id}/findings` fan-out with one call.

**Response (200)** — abridged from `open-finance-pd-2026`, task node
`open-finance-pd-2026-pd`:

```json
{
  "findings": [
    {
      "id": "e-rmit_2025--ed_open_finance_2025~7",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "Both require incident notification, but RMiT sets a 1-hour trigger where the ED leaves the threshold to the institution.",
      "review_state": "pending",
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
      "id": "e-rmit_2025--ed_open_finance_2025~0",
      "label": "aligns-with",
      "sentiment": null,
      "summary": "Both set the scope for managing technology and cyber risk, scaled to the institution's size and operations.",
      "review_state": "accepted",
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
      "source_clause_number": "Rmit 2025 1.2",
      "target_clause_number": "ed-open-finance-2025 1.4(a)(b)(c)(d)(e)(f)"
    }
  ],
  "nodes": [
    {
      "id": "ed-open-finance-2025",
      "title": "ED Open Finance 2025",
      "node_type": "internal-published",
      "findings_count": 0
    },
    {
      "id": "rmit-2025",
      "title": "RMiT 2025",
      "node_type": "internal-published",
      "findings_count": 51
    },
    {
      "id": "hkma-open-api-framework",
      "title": "HKMA Open API Framework",
      "node_type": "peer-regulator",
      "findings_count": 47
    },
    {
      "id": "bis-papers-168",
      "title": "BIS Papers 168",
      "node_type": "international-standard",
      "findings_count": 32
    },
    {
      "id": "abs-mas-api-playbook",
      "title": "ABS-MAS API Playbook",
      "node_type": "international-standard",
      "findings_count": 0
    }
  ],
  "unanalysed_pairs": [
    {
      "edge_id": "e-open_finance_pd_2026_pd--ed_open_finance_2025",
      "edge_type": "references",
      "left": {
        "id": "open-finance-pd-2026-pd",
        "title": "Open Finance PD · 2026 (PD)",
        "node_type": "task"
      },
      "right": {
        "id": "ed-open-finance-2025",
        "title": "ED Open Finance 2025",
        "node_type": "internal-published"
      }
    },
    {
      "edge_id": "e-abs_mas_api_playbook--ed_open_finance_2025",
      "edge_type": "references",
      "left": {
        "id": "abs-mas-api-playbook",
        "title": "ABS-MAS API Playbook",
        "node_type": "international-standard"
      },
      "right": {
        "id": "ed-open-finance-2025",
        "title": "ED Open Finance 2025",
        "node_type": "internal-published"
      }
    }
  ],
  "counts": {
    "total": 130,
    "by_label": {
      "conflicts-with": { "total": 0, "pending": 0 },
      "differs-on": { "total": 30, "pending": 29 },
      "silent-on": { "total": 11, "pending": 11 },
      "goes-beyond": { "total": 14, "pending": 14 },
      "aligns-with": { "total": 75, "pending": 74 }
    },
    "analysed_pairs": 3,
    "total_pairs": 5
  }
}
```

Notes on the shape:

- `findings[]` is `_linkage_card` plus `review_state`. Server order is graph edge
  order then within-file order; all grouping, sinking and filtering is done in the
  browser, so a review-state change needs no refetch to reorder.
- `nodes[]` is the filter's chip list — every node in the neighbourhood other than
  the task itself, in graph order, with its finding count across all its
  neighbourhood edges. A node with `findings_count: 0` still gets a chip (its
  pair is unanalysed).
- `unanalysed_pairs[]` is every neighbourhood edge with no findings file, and is
  `[]` when coverage is complete.
- `counts.by_label` covers **all five labels always**, including zeros, so the
  frontend never has to synthesise a missing group.

**Errors:**

| Status | Code                   | Condition                                         |
| ------ | ---------------------- | ------------------------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | No `data/workstreams/{workstream_id}/graph.json`  |
| 404    | `NODE_NOT_FOUND`       | `node_id` is not a node in that graph             |
| 400    | `NOT_A_TASK`           | The node exists but its `node_type` is not `task` |
| 500    | `INTERNAL_ERROR`       | A findings file is unreadable or malformed        |

### `PATCH /api/workstreams/{workstream_id}/edges/{edge_id}/findings/{finding_id}`

**Unchanged — reused as-is.** The box's Accept / Dismiss / Undo call the existing
route. Documented here only to pin the contract the new frontend depends on.

**Request:**

```json
{ "review_state": "accepted" }
```

**Response (200):**

```json
{
  "finding": {
    "id": "e-rmit_2025--ed_open_finance_2025~7",
    "label": "differs-on",
    "sentiment": "tighten",
    "summary": "Both require incident notification, but RMiT sets a 1-hour trigger where the ED leaves the threshold to the institution.",
    "review_state": "accepted",
    "source_clauses": [{ "clause_number": "Rmit 2025 10.32", "text": "…" }],
    "target_clauses": [
      { "clause_number": "ed-open-finance-2025 1.4(a)", "text": "…" }
    ]
  },
  "counts": { "total": 51, "accepted": 1, "dismissed": 0 }
}
```

Undo sends `{"review_state": "pending"}` to the same route.

**Errors:**

| Status | Code                   | Condition                                        |
| ------ | ---------------------- | ------------------------------------------------ |
| 400    | `INVALID_REVIEW_STATE` | `review_state` not in pending/accepted/dismissed |
| 400    | `EDGE_NOT_ANALYSED`    | The edge has no findings file                    |
| 404    | `FINDING_NOT_FOUND`    | No finding on that edge carries `finding_id`     |
| 404    | `WORKSTREAM_NOT_FOUND` | Unknown workstream                               |

### `POST /api/workstreams/{workstream_id}/edges/{edge_id}/analyze`

**Unchanged — reused as-is** by the coverage strip. Returns
`{"status": "analysed", findings, findings_count}` on success, or
`{"status": "no_linkages_found", "findings": [], "findings_count": 0}` when the
run produced nothing (no findings file is written, so the pair stays in
`unanalysed_pairs` and stays re-analysable). Failures surface as `502
ANALYZE_FAILED`, `409 NOT_ANALYSABLE` (an endpoint has no ingested document, or
both endpoints resolve to the same document).

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}/review?finding_id={id}`

**Existing route, one additive optional query param.** The comparison screen needs
to open on a nominated finding rather than the first selectable one.

Server change is deliberately minimal: validate that `finding_id` (when present)
exists on the edge, and echo it back as `active_finding_id` so the frontend has an
authoritative value to seed selection with. Clause panes are unchanged — they
already carry every clause cited by any finding on the edge.

**Response (200)** adds one field:

```json
{
  "edge": {
    "id": "e-rmit_2025--ed_open_finance_2025",
    "edge_type": "parallel-to",
    "source_node": {},
    "target_node": {}
  },
  "active_finding_id": "e-rmit_2025--ed_open_finance_2025~7",
  "source_clauses": [],
  "target_clauses": [],
  "findings": [],
  "counts": { "total": 51, "accepted": 1, "dismissed": 0 }
}
```

`active_finding_id` is `null` when the param is absent — the screen then keeps its
current behaviour of selecting the first non-dismissed finding.

**Errors:** existing set, plus:

| Status | Code                | Condition                                             |
| ------ | ------------------- | ----------------------------------------------------- |
| 404    | `FINDING_NOT_FOUND` | `finding_id` given but no finding on that edge has it |

## UI/Frontend Requirements

### Components

**`PairwiseFindingsCard`** — `frontend/src/features/task/PairwiseFindingsCard.tsx`

- **Type:** New file, replacing `PairwiseComparisonCard.tsx` (deleted).
- **Purpose:** the whole box — header, coverage strip, multi-select filter, five
  label groups.
- **Props:**
  ```typescript
  interface Props {
    workstreamId: string;
    nodeId: string;
  }
  ```
  Note it no longer takes `neighbours` or `draftEmpty`: it owns its own query, and
  draft state is irrelevant to it.

**`FindingGroup`** — `frontend/src/features/task/FindingGroup.tsx`

- **Type:** New.
- **Purpose:** one label group — header with label pill, total and pending count,
  then its ordered cards, then an empty note when the group has none.
- **Props:**
  ```typescript
  interface Props {
    label: SemanticLabel;
    findings: PairwiseFinding[]; // already filtered and sorted by the parent
    workstreamId: string;
    onReview: (finding: PairwiseFinding) => void;
    onSetState: (finding: PairwiseFinding, state: ReviewState) => void;
    isPending: (findingId: string) => boolean;
  }
  ```

**`PairwiseFindingCard`** — `frontend/src/features/task/PairwiseFindingCard.tsx`

- **Type:** New.
- **Purpose:** one finding — label pill (with sentiment arrow on `differs-on`
  only), the two document names, clause numbers, the summary, and the vertical
  action column.
- **Layout:** summary block on the left, actions stacked vertically on the right —
  Review, Accept, Dismiss top to bottom. Once acted on, the column collapses to a
  single Undo control and the card is muted with an accepted/dismissed marker.
- **Props:**
  ```typescript
  interface Props {
    finding: PairwiseFinding;
    onReview: () => void;
    onSetState: (state: ReviewState) => void;
    isPending: boolean;
    errorMessage?: string;
  }
  ```

**`CoverageStrip`** — `frontend/src/features/task/CoverageStrip.tsx`

- **Type:** New.
- **Purpose:** the never-analysed pairs row above the groups, one Analyze control
  per pair. Renders nothing when `pairs` is empty.
- **Props:**
  ```typescript
  interface Props {
    workstreamId: string;
    pairs: UnanalysedPair[];
    onAnalysed: (edgeId: string) => void;
  }
  ```
- Reuses `useAnalyzeEdge` and `AnalyzeProgressBar` — the same hook and progress
  bar the graph screen's `EdgeDetailPanel` uses. Per-pair pending/error state, so
  one failing pair does not block another.

**`NodeFilterChips`** — `frontend/src/features/task/NodeFilterChips.tsx`

- **Type:** New (generalises the `FilterChip` currently inside
  `PairwiseComparisonCard.tsx`).
- **Purpose:** multi-select document filter. Chips toggle independently; `All`
  clears the set.
- **Props:**
  ```typescript
  interface Props {
    nodes: PairwiseFilterNode[];
    selected: Set<string>;
    onToggle: (nodeId: string) => void;
    onClear: () => void;
  }
  ```
- **Accessibility:** each chip is a `button` with `aria-pressed` reflecting
  selection (already the pattern in the current `FilterChip`), inside a
  `role="group"` labelled "Filter by node". Multi-select needs no new ARIA — a
  toggle-button group is already correct.

**Deleted:** `frontend/src/features/task/NeighbourFindingsCard.tsx` and
`frontend/src/features/task/EmptyDraftCard.tsx`. Both exist only to serve the
per-neighbour card and the draft-empty gate, and both are dead once the box is
finding-grouped. `EmptyDraftCard` has no other importer.

### Sorting and filtering (client-side)

Add to `frontend/src/lib/labels.ts`:

```typescript
/** Review-state rank within a label group: pending floats, judged sinks.
 *  Accepted and dismissed share a rank — they sink together, in server order. */
export function reviewStateRank(state: ReviewState): number {
  return state === "pending" ? 0 : 1;
}

/** One label group's findings in display order: pending first, then judged,
 *  each block preserving server order (Array.prototype.sort is stable). */
export function forGroupDisplay<T extends { review_state: ReviewState }>(
  items: readonly T[],
): T[] {
  return [...items].sort(
    (a, b) => reviewStateRank(a.review_state) - reviewStateRank(b.review_state),
  );
}
```

Grouping is a `Map<SemanticLabel, PairwiseFinding[]>` seeded from `LABEL_SEVERITY_ORDER`
so all five keys exist regardless of content. `bySeverity` is **not** used inside a
group — every finding in a group shares its label — but `LABEL_SEVERITY_ORDER`
drives the group order.

Filtering: a finding is visible when `selected.size === 0`, or when either
`finding.left.id` or `finding.right.id` is in `selected`. Counts are computed after
filtering, so a group header always describes what is on screen.

### User Interactions

| Action                        | Result                                                                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Click **Accept**              | Card optimistically marks accepted, sinks within its group, group pending count −1                                          |
| Click **Dismiss**             | Same, marked dismissed                                                                                                      |
| Click **Undo** on judged card | Returns to pending, floats back above the judged block, pending count +1                                                    |
| Click **Review**              | Navigates to `/workstreams/{ws}/edges/{edgeId}/review?finding={findingId}`                                                  |
| Toggle a node chip            | Adds/removes from the selected set; groups and counts recompute                                                             |
| Click **All**                 | Clears the set; everything visible again                                                                                    |
| Click **Analyze** on a pair   | Runs analysis; on success invalidates the pairwise query so new findings land in their groups and the pair leaves the strip |

### States

- **Loading:** a spinner with "Loading findings…" inside the card, matching the
  task page's existing `role="status"` loader.
- **Empty — no findings anywhere, but pairs exist:** "No linkages have been
  surfaced yet." plus the coverage strip listing those pairs. Must **not** mention
  the draft.
- **Empty — no neighbours at all:** "This task has no neighbouring documents yet."
  with a link to the workstream graph. Distinguished from the above by
  `nodes.length === 0`.
- **Group empty:** header with its zero count and "None found." — the group is
  never hidden.
- **Analysis pending:** per-pair spinner plus `AnalyzeProgressBar`; other pairs
  stay interactive.
- **Analysis found nothing:** inline "No matching clause found — no linkages
  surfaced for this pair." The pair remains in the strip.
- **Analysis failed:** inline "Analysis failed. Check the engine has model
  credentials, then retry." Pair stays, no partial findings.
- **Review-state write failed:** the card reverts and shows "Could not save that
  decision. Try again."

### Header metric tiles

`TaskScreenPage`'s three tiles currently derive from `neighbours` (first-order,
edges out of the task only). Two of the three are wrong once the box covers the
neighbourhood, and the first needs relabelling rather than repointing:

| Tile                                         | Source                                          | `open-finance-pd-2026` | `opres-v2` |
| -------------------------------------------- | ----------------------------------------------- | ---------------------- | ---------- |
| **Documents** (relabelled from "Neighbours") | `nodes.length`                                  | 5                      | 9          |
| **Analysed**                                 | `counts.analysed_pairs` of `counts.total_pairs` | 3 of 5                 | 4 of 10    |
| **Findings**                                 | `counts.total`                                  | 130                    | 6          |

Today those read 1 / 0 / 0 and 7 / 4 / 6 respectively.

**Why "Documents" and not "Neighbours".** The neighbourhood is wider than the
first-order neighbour list, so `nodes.length` (9 on `opres-v2`) would contradict
`NeighboursCard`'s 7 rows and the header byline's "7 neighbour nodes" if both were
called "neighbours". They measure different things and must be labelled
differently: the tile counts documents the box can show findings for; the card
lists documents joined directly to the task. `NeighboursCard` and the byline keep
reading `neighbours` from `GET .../tasks/{node_id}` and are unchanged.

## Architecture Notes

- **New dependencies:** none.
- **Dependencies & integration:** the box becomes the task page's only findings
  consumer — `TaskScreenPage` stops passing `neighbours` and `draft_empty` into it.
  `NeighboursCard` (left column) keeps reading `neighbours` from `GET
.../tasks/{node_id}` and is unchanged, so that route's response shape must not be
  narrowed.
- **Query keys:** `["pairwise-findings", workstreamId, nodeId]` for the new route.
  A review-state write invalidates it, and also
  `["reviewed-linkages", workstreamId, nodeId]` and `["review", workstreamId, edgeId]`
  so Story 2's tab and the comparison screen never show stale state.
- **Why one route rather than reusing `related-linkages`:** `related-linkages`
  returns anchor↔anchor edges only (it excludes every edge touching the task) and
  applies no review-state projection. Widening it would break its `hops`
  contract and its existing tests. A new route with a superset scope is cleaner
  than overloading it, and leaves the old route available as a rollback seam.

## Exemplar Files

- `engine/api.py:1883` (`get_reviewed_linkages`) — the pattern for a task-scoped
  route that walks edges, loads findings per edge, tolerates
  `FindingsNotAnalysedError`, and projects via `_linkage_card`. The new route is
  this shape with a different edge scope and no review-state filter.
- `engine/api.py:1917` (`get_related_linkages`) — how `neighbour_ids` /
  `edges_between` are called, and the `_task_node` guard pattern.
- `engine/workstreams.py:194` (`neighbour_ids`) and `:211` (`edges_between`) — the
  helpers `neighbourhood_edges` sits beside, and the docstring style to match.
- `frontend/src/features/review-linkages/ReviewLinkagesPage.tsx` — the
  accept/dismiss mutation wired to `setReviewState`, and `forDisplay`'s
  sink-the-dismissed sort, which `forGroupDisplay` generalises.
- `frontend/src/features/task/PairwiseComparisonCard.tsx` — the `FilterChip`
  markup and `aria-pressed` pattern to carry into `NodeFilterChips`.
- `frontend/src/features/task/NeighbourFindingsCard.tsx` — `useAnalyzeEdge` +
  `AnalyzeProgressBar` wiring to carry into `CoverageStrip`.
- `engine/tests/test_api_workstreams.py` — TestClient + `shutil.copytree` fixture
  pattern for engine route tests.
- `frontend/src/features/task/TaskScreenPage.test.tsx` — Vitest + MSW pattern,
  `data-testid` conventions, and the helpers to update.

## Implementation Plan

### Sub-tasks

**Task 1: `neighbourhood_edges` helper + unit tests** — _small_

- Files: `engine/workstreams.py`, `engine/tests/test_workstreams_neighbourhood.py`
  (new)
- Add the helper described in the epic's Shared Architecture Notes. Cover: the
  `open-finance-pd-2026` five-edge case, the `opres-v2` task-outward case, a
  synthetic graph with a second-order↔second-order edge that must be excluded, an
  isolated node (→ `[]`), and edge-direction independence.
- INDEPENDENT

**Task 2: `GET .../tasks/{node_id}/pairwise-findings` route** — _medium_

- Files: `engine/api.py`, `engine/tests/test_api_pairwise_findings.py` (new)
- Add `review_state` to `_linkage_card`. Build `findings`, `nodes`,
  `unanalysed_pairs`, `counts` exactly as specified. Reuse `_task_node`,
  `findings.load`, and the `FindingsNotAnalysedError` tolerance.
- SEQUENTIAL (depends on Task 1)

**Task 3: `finding_id` query param on the review route** — _small_

- Files: `engine/api.py`, `engine/tests/test_api_review.py`
- Optional param, validated against the edge's findings, echoed as
  `active_finding_id`; `null` when absent; `404 FINDING_NOT_FOUND` when unknown.
- INDEPENDENT

**Task 4: frontend types, API client, and label helpers** — _small_

- Files: `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`,
  `frontend/src/lib/labels.ts`, `frontend/src/lib/labels.test.ts`
- Add `PairwiseFinding`, `PairwiseFilterNode`, `UnanalysedPair`,
  `PairwiseFindingsResponse`; add `fetchPairwiseFindings`; extend `fetchReview`
  with an optional `findingId`; add `reviewStateRank` / `forGroupDisplay` with unit
  tests (including sort stability).
- SEQUENTIAL (depends on Task 2 for the response shape)

**Task 5: `NodeFilterChips` + `CoverageStrip`** — _small_

- Files: `frontend/src/features/task/NodeFilterChips.tsx`,
  `frontend/src/features/task/CoverageStrip.tsx`
- Multi-select chips with `aria-pressed`; per-pair analyse with its own
  pending/error state via `useAnalyzeEdge`.
- SEQUENTIAL (depends on Task 4)

**Task 6: `PairwiseFindingCard` + `FindingGroup`** — _medium_

- Files: `frontend/src/features/task/PairwiseFindingCard.tsx`,
  `frontend/src/features/task/FindingGroup.tsx`
- Summary-only card with the vertical action column; muted judged state with Undo;
  group header with total and pending; "None found." for an empty group.
- SEQUENTIAL (depends on Task 4)

**Task 7: `PairwiseFindingsCard` container + `TaskScreenPage` rewire** — _medium_

- Files: `frontend/src/features/task/PairwiseFindingsCard.tsx`,
  `frontend/src/features/task/TaskScreenPage.tsx`; delete
  `frontend/src/features/task/PairwiseComparisonCard.tsx`,
  `frontend/src/features/task/NeighbourFindingsCard.tsx`,
  `frontend/src/features/task/EmptyDraftCard.tsx`
- Own the query, grouping, filtering, and the optimistic review mutation with
  rollback and cross-query invalidation. Repoint the three metric tiles. Stop
  threading `neighbours` / `draft_empty` into the box.
- SEQUENTIAL (depends on Tasks 5, 6)

**Task 8: comparison screen opens on the nominated finding** — _small_

- Files: `frontend/src/features/review-linkages/ReviewLinkagesPage.tsx`,
  `frontend/src/features/review-linkages/ReviewLinkagesPage.test.tsx`
- Read `?finding=` from the URL, seed `activeId` from it, keep the
  first-non-dismissed fallback when absent or unknown.
- SEQUENTIAL (depends on Tasks 3, 4)

**Task 9: MSW handlers + component tests** — _medium_

- Files: `frontend/src/test/msw/handlers.ts`,
  `frontend/src/features/task/TaskScreenPage.test.tsx`
- Add a `pairwise-findings` handler for both `open-finance-pd-2026` and
  `opres-v2`. Rewrite the task-screen tests against the new structure.
- Specifically removed or rewritten in `TaskScreenPage.test.tsx`:
  - the `pairCard()` helper (`data-neighbour` no longer exists — cards are per
    finding, keyed by `data-finding-id`);
  - the "4 of 7 neighbours analysed" footer assertion (the footer is replaced by
    per-group counts);
  - `describe("TaskScreenPage — empty draft")`'s "renders the empty-draft card and
    no pair cards" — inverted into Test 28's assertion that the box renders its
    groups on an empty draft;
  - "presents the empty draft as the starting state, not an error" — its
    `empty-draft-card` lookup becomes an assertion that the box is populated and
    no `alert` role is present.
- `EMPTY_URL` / `FRESH_URL` (the `opres-pd-v0-0` and freshly-scaffolded task
  fixtures) stay useful — they now prove the box works with no draft rather than
  that it hides itself.
- SEQUENTIAL (depends on Task 7)

**Task 10: E2E spec** — _small_

- Files: `frontend/e2e/pairwise-findings.spec.ts` (new)
- The demo path on `open-finance-pd-2026`. See Verification.
- SEQUENTIAL (depends on Task 9)

### Negative Constraints

- Do **NOT** modify any fixture under `data/workstreams/` — not `graph.json`, not
  a findings file, not an anchors or axes file. Every scenario in this spec is
  satisfiable against the committed fixtures.
- Do **NOT** rebuild `data/artifacts/` (see the `engine.build` narrowing blocker in
  `CLAUDE.md`). Nothing in this story reads the clause index.
- Do **NOT** delete or narrow `GET .../tasks/{node_id}/related-linkages`. Story 2
  stops calling it; it stays as a rollback seam with its tests green.
- Do **NOT** remove `draft_empty` from `GET .../tasks/{node_id}`, and do not remove
  `neighbours` — `NeighboursCard` and existing engine tests depend on the latter.
- Do **NOT** change `engine/findings.py`. Its id derivation (`{edge_id}~{i}`, `~`
  chosen deliberately for URL-safety) and read-default behaviour are exactly what
  this story needs.
- Do **NOT** change `engine/connections.py`, `engine/arm_g.py`, or anything about
  how findings are produced. This story only projects and reviews existing
  findings.
- Do **NOT** reorder findings server-side. Grouping and sinking are view concerns,
  per the existing convention in `ReviewLinkagesPage`.
- Do **NOT** normalise edge direction to put the task first. Two fixtures use
  opposite conventions and `left`/`right` must stay `source`/`target`.
- Do **NOT** introduce a state library. TanStack Query plus local `useState`, per
  the frontend conventions.
- Do **NOT** add a "show more" / windowing control to any group.

## Test Scenarios

**Test 1: the route surfaces second-order findings** _(engine)_

- Setup: copy `data/workstreams` to tmp; workstream `open-finance-pd-2026`, node
  `open-finance-pd-2026-pd`.
- Action: `GET /api/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd/pairwise-findings`
- Expected: `200`; `counts.total == 130`; `len(body["findings"]) == 130`; the set of
  `edge_id`s is exactly `{e-rmit_2025--ed_open_finance_2025,
e-hkma_open_api_framework--ed_open_finance_2025,
e-bis_papers_168--ed_open_finance_2025}`.

**Test 2: label counts match the fixture exactly** _(engine)_

- Setup: as Test 1.
- Action: same request.
- Expected: `counts.by_label` == `{"conflicts-with": {"total": 0, "pending": 0},
"differs-on": {"total": 30, "pending": 30}, "silent-on": {"total": 11, "pending":
11}, "goes-beyond": {"total": 14, "pending": 14}, "aligns-with": {"total": 75,
"pending": 75}}` — all five keys present, `conflicts-with` present at zero.

**Test 3: second-order↔second-order edges are excluded** _(engine)_

- Setup: copy the fixture, then append to the tmp copy's `graph.json` an edge
  `e-hkma_open_api_framework--bis_papers_168` and a findings file for it with one
  `conflicts-with` finding. (Tmp copy only — the tracked fixture is untouched.)
- Action: same request.
- Expected: `counts.total` stays `130`; `counts.by_label["conflicts-with"]["total"]
== 0`; no finding carries that `edge_id`.

**Test 4: unanalysed pairs are listed, analysed ones are not** _(engine)_

- Setup: as Test 1.
- Action: same request.
- Expected: `[p["edge_id"] for p in body["unanalysed_pairs"]]` ==
  `["e-open_finance_pd_2026_pd--ed_open_finance_2025",
"e-abs_mas_api_playbook--ed_open_finance_2025"]`; `counts.analysed_pairs == 3`;
  `counts.total_pairs == 5`.

**Test 5: filter node list covers the neighbourhood** _(engine)_

- Setup: as Test 1.
- Action: same request.
- Expected: `[n["id"] for n in body["nodes"]]` contains `ed-open-finance-2025`,
  `rmit-2025`, `hkma-open-api-framework`, `bis-papers-168`,
  `abs-mas-api-playbook`; does **not** contain `open-finance-pd-2026-pd`;
  `findings_count` is `51` for `rmit-2025` and `0` for `abs-mas-api-playbook`.

**Test 6: review state rides on the card** _(engine)_

- Setup: as Test 1, then `PATCH
/api/workstreams/open-finance-pd-2026/edges/e-rmit_2025--ed_open_finance_2025/findings/e-rmit_2025--ed_open_finance_2025~0`
  with `{"review_state": "accepted"}`.
- Action: `GET …/pairwise-findings`
- Expected: that finding's `review_state == "accepted"`;
  `counts.by_label["aligns-with"]` == `{"total": 75, "pending": 74}`;
  `counts.total` still `130`.

**Test 7: draft content does not affect the response** _(engine)_

- Setup: as Test 1 — `open-finance-pd-2026` has no `drafts/` directory, so the
  draft is empty.
- Action: `GET …/pairwise-findings`, then `PUT …/tasks/{node}/draft` with
  `{"content_html": "<p>1.1 Scope.</p>"}`, then `GET …/pairwise-findings` again.
- Expected: both responses are byte-identical.

**Test 8: task-outward fixture still works** _(engine)_

- Setup: workstream `opres-v2`, node `opres-pd-v0-3` (8 edges out of the task, 4
  analysed).
- Action: `GET …/pairwise-findings`
- Expected: `200`; `counts.total == 6` (3 + 1 + 1 + 1 across the four analysed
  edges); `counts.analysed_pairs == 4`; `counts.total_pairs == 10`;
  `len(body["nodes"]) == 9`.
- The scope is wider than the task's own edges, and the extra two edges are the
  point of the test: `e-opres_v0_0--bcbs_opres_2021` and
  `e-opres_v0_0--hkma_spm_or2` qualify because their targets are first-order
  neighbours of `opres-pd-v0-3`, even though their source is the _other_ task node
  `opres-pd-v0-0`. `e-opres_v0_3--opres_dp_2025` and the incoming
  `e-iais_draft_…--opres_dp_2025` also qualify.
- Consequence to assert deliberately: `nodes` contains `opres-pd-v0-0` — a second
  task node is a legitimate neighbourhood document here, and it gets a filter chip
  like any other. Only the _viewed_ task node is excluded from `nodes`.

**Test 9: route guards** _(engine)_

- Action / Expected:
  - `GET /api/workstreams/nope/tasks/x/pairwise-findings` → `404`,
    `{"code": "WORKSTREAM_NOT_FOUND"}`
  - `GET /api/workstreams/open-finance-pd-2026/tasks/nope/pairwise-findings` →
    `404`, `{"code": "NODE_NOT_FOUND"}`
  - `GET /api/workstreams/open-finance-pd-2026/tasks/rmit-2025/pairwise-findings`
    → `400`, `{"code": "NOT_A_TASK"}`

**Test 10: review route honours `finding_id`** _(engine)_

- Setup: workstream `open-finance-pd-2026`, edge
  `e-rmit_2025--ed_open_finance_2025`.
- Action: `GET …/edges/e-rmit_2025--ed_open_finance_2025/review?finding_id=e-rmit_2025--ed_open_finance_2025~7`
- Expected: `200`; `active_finding_id ==
"e-rmit_2025--ed_open_finance_2025~7"`; `findings` and clause panes unchanged from
  the no-param response.

**Test 11: review route rejects an unknown `finding_id`** _(engine)_

- Action: same route with `?finding_id=e-rmit_2025--ed_open_finance_2025~9999`
- Expected: `404`, `{"code": "FINDING_NOT_FOUND"}`.

**Test 12: review route without the param is unchanged** _(engine)_

- Action: `GET …/review` with no query string.
- Expected: `active_finding_id is None`; every other field identical to the
  pre-change response (regression guard on `test_api_review.py`).

**Test 13: idempotent accept** _(engine)_

- Setup: finding `e-rmit_2025--ed_open_finance_2025~7` already `accepted`.
- Action: `PATCH` the same finding with `{"review_state": "accepted"}` again.
- Expected: `200`, same body, `counts.accepted` unchanged, findings file content
  identical.

**Test 14: groups render all five labels including the empty one** _(frontend,
Vitest + MSW)_

- Setup: MSW returns the `open-finance-pd-2026` payload.
- Action: render `/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd`.
- Expected: five group headers in DOM order `conflicts-with`, `differs-on`,
  `silent-on`, `goes-beyond`, `aligns-with`; the `conflicts-with` group shows `0`
  and "None found."; `getAllByTestId("finding-card")` has length `130` (proving no
  truncation).

**Test 15: accept sinks the card within its group** _(frontend)_

- Setup: as Test 14.
- Action: click Accept on the first `differs-on` card.
- Expected: the `differs-on` header reads total `30`, pending `29`; that card now
  carries `data-review-state="accepted"`; its index within
  `[...differsGroup.querySelectorAll('[data-testid=finding-card]')]` is greater
  than every pending sibling's; it is still inside the `differs-on` group element.

**Test 16: undo restores pending and position** _(frontend)_

- Setup: as Test 15, after the accept.
- Action: click Undo on that card.
- Expected: header pending returns to `30`; the card's
  `data-review-state="pending"`; it precedes any judged sibling.

**Test 17: multi-select filter** _(frontend)_

- Setup: as Test 14.
- Action: click the `RMiT 2025` chip, then the `HKMA Open API Framework` chip.
- Expected: both chips `aria-pressed="true"`; visible cards' `edge_id`s are only
  the RMiT and HKMA edges (98 cards); `differs-on` header total reads `22` (7 RMiT
  - 15 HKMA); no BIS card present.

**Test 18: deselect one of two** _(frontend)_

- Setup: as Test 17.
- Action: click the `RMiT 2025` chip again.
- Expected: `RMiT` chip `aria-pressed="false"`, `HKMA` still `true`; 47 cards
  visible; `differs-on` total reads `15`.

**Test 19: All clears the filter** _(frontend)_

- Setup: as Test 17.
- Action: click `All`.
- Expected: no node chip `aria-pressed="true"`; 130 cards visible; `differs-on`
  total back to `30`.

**Test 20: coverage strip lists and clears** _(frontend)_

- Setup: as Test 14; MSW `POST .../edges/e-abs_mas_api_playbook--ed_open_finance_2025/analyze`
  returns `{"status": "analysed", "findings_count": 4}` and the refetched
  `pairwise-findings` payload drops that pair and adds 4 `differs-on` findings.
- Action: assert the strip names both unanalysed pairs; click Analyze on the
  ABS-MAS pair.
- Expected: the strip then lists one pair; `differs-on` header total reads `34`.

**Test 21: analysis that finds nothing keeps the pair** _(frontend)_

- Setup: MSW analyze returns `{"status": "no_linkages_found", "findings": [],
"findings_count": 0}`.
- Action: click Analyze on the draft↔ED pair.
- Expected: "No matching clause found" appears inline; that pair is still in the
  strip; all group counts unchanged.

**Test 22: analysis failure is recoverable** _(frontend)_

- Setup: MSW analyze returns `502 {"code": "ANALYZE_FAILED"}`.
- Action: click Analyze.
- Expected: "Analysis failed. Check the engine has model credentials, then retry."
  inline; pair remains; the Analyze control is enabled again; no card added to any
  group.

**Test 23: review-state write failure rolls back** _(frontend)_

- Setup: MSW `PATCH .../findings/:findingId` returns `500`.
- Action: click Accept on a `differs-on` card.
- Expected: the card returns to `data-review-state="pending"`; group pending count
  returns to `30`; "Could not save that decision. Try again." shown on the card.

**Test 24: Review navigates with the finding in the URL** _(frontend)_

- Setup: as Test 14.
- Action: click Review on the card whose id is
  `e-rmit_2025--ed_open_finance_2025~7`.
- Expected: location is
  `/workstreams/open-finance-pd-2026/edges/e-rmit_2025--ed_open_finance_2025/review?finding=e-rmit_2025--ed_open_finance_2025~7`.

**Test 25: comparison screen selects the nominated finding** _(frontend)_

- Setup: render that URL directly; MSW review handler echoes `active_finding_id`.
- Expected: the card for `~7` is the active one; the clause panes highlight
  `Rmit 2025 10.32` and `ed-open-finance-2025 1.4(a)` rather than the first
  finding's clauses.

**Test 26: sentiment renders only on `differs-on`** _(frontend)_

- Setup: MSW payload with one finding per label, each carrying
  `sentiment: "tighten"`.
- Expected: the `differs-on` card shows the tighten arrow; the other four show no
  arrow.

**Test 27: no clause on one side** _(frontend)_

- Setup: a `silent-on` finding with `target_clause_number: null`.
- Expected: the card shows "No matching clause found" for the target side; no
  clause number is rendered there.

**Test 28: empty and no-neighbour states** _(frontend)_

- Setup A: payload with `findings: []`, `nodes` non-empty, `unanalysed_pairs`
  non-empty.
- Expected A: "No linkages have been surfaced yet."; the strip is present; the word
  "draft" does not appear in the box.
- Setup B: payload with `findings: []`, `nodes: []`, `unanalysed_pairs: []`.
- Expected B: "This task has no neighbouring documents yet." plus a link to the
  workstream graph.

**Test 29: metric tiles read the neighbourhood** _(frontend)_

- Setup: as Test 14.
- Expected: the tiles read Documents `5`, Analysed `3` of `5`, Findings `130`. The
  first tile is labelled "Documents", not "Neighbours".
- Also assert on `opres-v2`: Documents `9`, Analysed `4` of `10`, Findings `6`,
  while `NeighboursCard` still shows `7` rows — the two numbers differ legitimately
  and neither is a bug.

**Test 30: `opres-v2` task screen does not regress** _(frontend)_

- Setup: MSW `opres-v2` payload; render
  `/workstreams/opres-v2/tasks/opres-pd-v0-3`.
- Expected: the source card and the seven-row `NeighboursCard` are unchanged; the
  box renders its groups; no `empty-draft-card` testid exists anywhere in the DOM.

## Acceptance Criteria

- [ ] `GET .../tasks/{node_id}/pairwise-findings` returns 130 findings for
      `open-finance-pd-2026`, with all five label groups present in `counts.by_label`.
- [ ] Second-order↔second-order edges are excluded, proven by a test that adds one.
- [ ] The response is identical whether or not the working draft has content.
- [ ] `GET .../edges/{edge_id}/review?finding_id=…` echoes `active_finding_id`, and
      is unchanged without the param.
- [ ] The box renders every card — 130 on the demo fixture — with no truncation
      control.
- [ ] Accept, Dismiss and Undo work from the card, sink within the label group, and
      keep group totals stable while pending counts move.
- [ ] The node filter is multi-select, and counts describe the filtered set.
- [ ] The coverage strip lists both unanalysed pairs and clears one on success.
- [ ] Review lands on the comparison screen with the clicked finding selected.
- [ ] `PairwiseComparisonCard.tsx`, `NeighbourFindingsCard.tsx` and
      `EmptyDraftCard.tsx` are deleted and nothing imports them.
- [ ] `.venv/bin/python -m pytest engine/tests` is green.
- [ ] `cd frontend && npm run test` is green, and `npx tsc -b` reports no errors.
- [ ] No fixture under `data/workstreams/` is modified (`git status` clean there).

## Verification

Run the verifier skill to confirm changes are clean.

### Backend API Tests

| File                                             | Covers                                                      |
| ------------------------------------------------ | ----------------------------------------------------------- |
| `engine/tests/test_workstreams_neighbourhood.py` | Tests 1–3's helper: hop rule, direction, exclusion, isolate |
| `engine/tests/test_api_pairwise_findings.py`     | Tests 1–9, 13: the new route end to end                     |
| `engine/tests/test_api_review.py` _(modify)_     | Tests 10–12: `finding_id` param and its regression guard    |

Follow the `TestClient` + `shutil.copytree(REPO_ROOT / "data" / "workstreams")`
fixture pattern from `engine/tests/test_api_workstreams.py`. Tests must inject no
model seams — this story adds no route that reaches a model.

Run: `.venv/bin/python -m pytest engine/tests -q` (Windows:
`.venv/Scripts/python.exe -m pytest engine/tests`). Ignore the forge
`stop-verify` LINT FAIL — it is the known pyenv/ruff false-fail in `CLAUDE.md`.

### Browser/UI Testing

1. Start the engine: `uvicorn engine.api:app --port 8000` (repo root).
2. Start the app: `cd frontend && npm run dev`, with `VITE_API_BASE=http://localhost:8000`.
3. Open `http://localhost:5173/workstreams/open-finance-pd-2026`, click the
   **Open Finance PD · 2026 (PD)** node, then **Open task**.
4. Expect: the box titled **Pairwise findings** with the new description; metric
   tiles reading Documents 5, Analysed 3 of 5, Findings 130; no empty-draft message
   even though the draft is blank.
5. Expect: five group headers, `conflicts-with` at 0 with "None found.",
   `aligns-with` at 75 with 75 cards present (scroll to confirm none are hidden).
6. Expect: a coverage strip naming the ABS-MAS↔ED and draft↔ED pairs.
7. Click the **RMiT 2025** and **HKMA Open API Framework** chips together — expect
   both highlighted and BIS cards gone.
8. Click **Accept** on a `differs-on` card — expect it to mute and sink below the
   pending cards in that group, header pending 30 → 29, total still 30.
9. Click **Undo** on it — expect it back at the top of the pending block, pending
   29 → 30.
10. Click **Review** on a RMiT card — expect the comparison screen with that
    finding selected and its two clauses highlighted. Press back — expect the box
    with the same filter still applied.
11. Regression: open `/workstreams/opres-v2/tasks/opres-pd-v0-3` and confirm the
    left column's seven neighbour rows are unchanged.

After a local run that clicked Analyze or Accept, `git checkout data/workstreams`
— those actions write to tracked fixture paths.

### E2E Tests

| Key Scenario                                                 | Test file                                | Assigned sub-task |
| ------------------------------------------------------------ | ---------------------------------------- | ----------------- |
| The box is populated when the working draft is blank         | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Findings from documents two steps away are included          | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Findings are grouped by label in attention order with counts | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| An empty label group shows its zero rather than vanishing    | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Accepting from the card sinks it within its own group        | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Undoing a decision returns the finding to pending            | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Review opens the comparison on the chosen finding            | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Selecting several documents in the filter at once            | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |
| Never-analysed pairs appear in the coverage strip            | `frontend/e2e/pairwise-findings.spec.ts` | Task 10           |

Scenarios not mapped to E2E and covered by the tests above instead: the
route-guard cases and the two draft-content-invariance cases (engine tests 7, 9 —
no UI path), and the analysis failure / no-linkage cases (frontend tests 21–22 —
they need an induced backend failure, which MSW can do and a live E2E cannot
reliably).

**Locator strategies:**

- `data-testid="pairwise-card"` — the box (name retained so existing selectors keep
  working)
- `data-testid="finding-group"` with `data-label="differs-on"` — one label group
- `data-testid="finding-card"` with `data-finding-id`, `data-edge-id`,
  `data-review-state` — one finding card
- `data-testid="coverage-strip"`, `data-testid="coverage-pair"` with
  `data-edge-id`
- `role="group"` + `aria-label="Filter by node"`; chips are `button` with
  `aria-pressed`
- Card actions by accessible name: `Review`, `Accept`, `Dismiss`, `Undo`
- Group counts: `data-testid="group-total"` and `data-testid="group-pending"`
  within a group

E2E setup mirrors `frontend/e2e/README.md`: engine on 8000, `VITE_API_BASE` set,
Playwright starts Vite. The spec must reset state it mutates — note in the file
header that a run writes review state into `data/workstreams/open-finance-pd-2026`
and requires `git checkout data/workstreams/open-finance-pd-2026` afterwards, the
same convention `add-edge.spec.ts` uses.
