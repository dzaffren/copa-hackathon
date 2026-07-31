# Pairwise Findings — Overview

## Summary

Today the box on the task page that shows semantic linkages only works once the
drafter has already written clauses into their working draft, and it only looks at
documents joined directly to the task. This epic turns it into **Pairwise
Findings** — a review surface that draws on the whole neighbourhood around the
task, groups every finding by its semantic label, and lets Aisyah R. accept or
dismiss each one from that single box. Everything she accepts then feeds a
redesigned Reviewed tab in the open-draft view, so decisions made while surveying
the landscape are waiting for her when she starts writing.

## Background & Context

**Current state:**

- The box on the task page is titled "Pairwise comparison · draft vs neighbours"
  and described as "Finder→critic linkages between the working draft and each
  neighbour node."
- When the working draft has no content, the box shows an empty state that says
  no findings can exist until the draft has content, and hides the neighbour
  filter entirely.
- The box shows one card per neighbour document. Each card shows a single headline
  finding and a link into the comparison screen; accepting or dismissing is only
  possible after leaving the task page.
- Only documents joined directly to the task are considered. On the Open Finance
  PD 2026 workstream, that is one document — the Open Finance Exposure Draft.
- The open-draft view carries three tabs: Reviewed, Related · 1 hop, and Copilot.
  Reviewed lists accepted findings, but only from documents joined directly to the
  task.

**Problem:**

- **The box is empty exactly when it is most useful.** Aisyah's first act on a new
  policy document is to understand the landscape she is drafting into. The current
  design refuses to show her anything until she has already written clauses,
  inverting the order of the real work.
- **Findings that already exist are unreachable.** On the Open Finance PD 2026
  workstream, 130 findings have been produced across three document pairs — 51
  between RMiT 2025 and the Exposure Draft, 47 between the HKMA Open API Framework
  and the Exposure Draft, and 32 between BIS Papers 168 and the Exposure Draft.
  None of them appear on the task page, because none of those pairs involves the
  task document itself.
- **One headline per document hides the rest.** A document pair with 51 findings
  contributes one visible line, so a difference on incident-reporting timelines
  sits behind a card whose headline happens to be an alignment.
- **Reviewing costs a round trip.** To accept or dismiss anything, Aisyah leaves
  the task page for the comparison screen and comes back, losing her place in the
  list.
- **Accepted decisions do not all arrive downstream.** The Reviewed tab reads only
  the documents joined directly to the task, so a finding accepted between RMiT
  2025 and the Exposure Draft would be accepted and then invisible.

## Goals

- Show semantic linkages on the task page from the moment the workstream has been
  analysed, with no dependence on the working draft having content.
- Draw findings from the task's wider neighbourhood, so what the drafter's anchor
  documents already say about each other is visible.
- Group findings by semantic label with honest per-label counts, so the drafter
  can see her workload per label and act on differences before alignments.
- Let the drafter accept or dismiss any finding without leaving the task page, and
  reach the full clause-level comparison in one click when she wants it.
- Make every accepted finding — wherever in the neighbourhood it came from —
  appear in the Reviewed tab when she opens the draft.
- Keep the verbatim-citation guarantee: every finding names the clauses it relies
  on, and no clause is ever invented.

## Non-Goals

- **No Recommendations tab.** The open-draft view's third tab is being replaced by
  a Recommendations tab, which is specified separately. This epic retires the
  Related · 1 hop tab and leaves its slot ready.
- **No new analysis capability.** This epic changes which existing findings are
  surfaced and how they are reviewed. It does not change how findings are produced
  or what the engine looks for.
- **No editing of the neighbourhood from this box.** Documents and the links
  between them are still added and removed on the workstream graph.
- **No bulk accept or dismiss.** Each finding is judged individually; a
  select-all action is deferred.
- **No cross-workstream findings.** The box covers the neighbourhood inside one
  workstream. Cross-workstream linkage keeps its own surface.

## Story Index

| Ticket | Story                 | Spec                                                           | Type        | Status      | Dependencies |
| ------ | --------------------- | -------------------------------------------------------------- | ----------- | ----------- | ------------ |
| TBD    | Pairwise Findings box | [spec-pairwise-findings-box.md](spec-pairwise-findings-box.md) | User-facing | Not Started | —            |
| TBD    | Reviewed tab redesign | [spec-reviewed-tab-redesign.md](spec-reviewed-tab-redesign.md) | User-facing | Not Started | Story 1      |

Story 1 replaces the box on the task page: what it draws on, how it is titled and
described, how findings are grouped and filtered, and the accept / dismiss /
review actions on each card. Story 2 redesigns the Reviewed tab in the open-draft
view so it gathers every accepted finding from across the same neighbourhood, and
retires the Related · 1 hop tab.

Story 2 depends on Story 1 only for the accepting behaviour that fills it. Story 1
ships value alone — a drafter can survey and triage the landscape even before the
Reviewed tab widens — and Story 2 closes the loop.

## Shared Business Rules

- **Neighbourhood scope.** A finding belongs on the task's surfaces when it sits on
  a link where at least one end is the task document itself or a document joined
  directly to it. Links between two documents that are both two steps away are out
  of scope. On the Open Finance PD 2026 workstream this brings in the Exposure
  Draft's linkages with RMiT 2025, the HKMA Open API Framework, BIS Papers 168 and
  the ABS-MAS API Playbook, and excludes any HKMA-to-BIS linkage.
- **The draft's content is never a gate.** Neither the box nor the Reviewed tab
  hides content, disables a control, or shows an empty-draft message on account of
  the working draft being blank.
- **Five labels, one vocabulary.** Every finding carries exactly one of
  `conflicts-with`, `differs-on`, `silent-on`, `goes-beyond`, `aligns-with`. A
  tighten or loosen direction is shown only on `differs-on`.
- **Attention order.** Wherever findings are grouped or listed, the order is
  `conflicts-with`, `differs-on`, `silent-on`, `goes-beyond`, `aligns-with` — most
  to least urgent. This holds on the task page, the Reviewed tab and the
  comparison screen alike.
- **Three review states.** A finding is pending, accepted or dismissed. Accepting
  or dismissing is reversible from wherever it was done.
- **One shared decision.** A finding accepted on the task page is accepted
  everywhere — the comparison screen and the Reviewed tab show the same state, and
  a finding dismissed on the comparison screen is dismissed on the task page.
- **Verbatim citation.** Every finding names the source and target clause numbers
  it relies on, and the comparison screen shows those clauses word for word. When
  no clause supports a claim, the surface says "No matching clause found" rather
  than paraphrasing.
- **Counts are honest.** No surface reports a number it has silently trimmed. A
  group labelled 30 contains 30 findings, and a bounded view says what it left
  out.

## User Journey Map

1. **Opening a task with nothing written yet.** Aisyah opens the Open Finance PD
   2026 task on 30 July. Her working draft is blank — she has not typed a clause.
   The Pairwise Findings box is already populated with 130 findings drawn from the
   Exposure Draft's linkages with RMiT 2025, the HKMA Open API Framework and BIS
   Papers 168. _(Story: Pairwise Findings box)_
2. **Reading the shape of the work.** The box tells her there are no conflicts, 30
   differences, 11 places where one document is silent, 14 where one goes beyond
   the other, and 75 alignments. She now knows the landscape has no
   contradictions to resolve but 30 differences to form a position on. _(Story:
   Pairwise Findings box)_
3. **Noticing a coverage gap.** Above the groups, a strip tells her two pairs have
   never been analysed — the ABS-MAS API Playbook against the Exposure Draft, and
   her own draft against the Exposure Draft. She analyses the ABS-MAS pair so the
   Singapore comparison is on the table. _(Story: Pairwise Findings box)_
4. **Narrowing to the peer regulators.** She selects the HKMA and RMiT filter
   chips together, and the groups narrow to the findings from those two documents
   while keeping the same label structure. _(Story: Pairwise Findings box)_
5. **Judging findings one at a time.** She reads a difference summary about
   incident-notification timing, clicks Review, and lands on the clause comparison
   with RMiT 10.32 and Exposure Draft 1.4(a) quoted side by side and that finding
   already selected. She accepts it and returns to the box, where the card is now
   muted and has sunk to the bottom of its group. _(Story: Pairwise Findings box)_
6. **Triaging the alignments quickly.** For most of the 75 alignments she accepts
   or dismisses straight from the card without opening the comparison, and each
   acted-on card sinks so the pending ones stay at the top of their group.
   _(Story: Pairwise Findings box)_
7. **Opening the draft to write.** She clicks Open draft. The Reviewed tab holds
   every finding she accepted — including the RMiT and HKMA ones, which are two
   steps from her document — grouped in the same attention order, each naming its
   clauses. _(Story: Reviewed tab redesign)_
8. **Drafting against her own decisions.** She writes her incident-notification
   clause with the accepted RMiT difference open beside her, clicking a card to
   read the clause it cites. The decisions she made surveying the landscape are
   now the brief she drafts from. _(Story: Reviewed tab redesign)_

## Success Metrics

- A drafter opening a task with a blank working draft sees every finding in the
  task's neighbourhood, where today she sees none — measured on the Open Finance
  PD 2026 workstream as 130 findings shown versus 0.
- Findings reachable from the task page rise from one headline per directly-joined
  document to every finding in the neighbourhood — on Open Finance PD 2026, from 1
  to 130.
- Accepting or dismissing a finding requires no navigation away from the task
  page, reducing the round trips to review a document pair from one per finding to
  zero.
- Every finding accepted anywhere in the task's neighbourhood appears in the
  Reviewed tab, with no accepted finding lost — the current design loses all
  accepted findings from documents that are two steps away.
- A drafter can state her workload per label from the top of the box without
  scrolling or counting, because each group carries its own total and its pending
  count.

## Dependencies

- **A workstream must have been analysed for its findings to appear.** The box
  surfaces findings that already exist; pairs never analysed appear in the
  coverage strip instead. The demo workstreams ship with their findings already
  produced, so nothing needs analysing on the day.
- **The clause comparison screen** is where Review lands, and it must be able to
  open on a nominated finding rather than always on the first one.
- **The Recommendations tab specification** owns the third slot in the open-draft
  view. This epic retires Related · 1 hop and must not leave the tab strip
  broken while that specification is outstanding.

## Rollout Strategy

- **Story 1 first**, because it is the surface the demo opens on and because it
  produces the accepted findings Story 2 displays.
- **Story 2 immediately after.** The gap between them is a state where a drafter
  can accept a finding from two steps away and not see it in the Reviewed tab, so
  the two should land in the same release even though they are separate stories.
- **The Related · 1 hop tab is removed in Story 2**, leaving Reviewed and Copilot
  in place. The third slot stays empty until the Recommendations specification is
  built, rather than shipping a placeholder tab.

## Open Questions

- [x] ~~How far should the box reach into the graph?~~ — **Resolved:** a finding
      qualifies when at least one end of its link is the task document or a
      document joined directly to it. Links between two documents that are both two
      steps away are excluded, because a finding relating neither to the draft nor
      to any document the drafter declared is noise.
- [x] ~~With 130 findings, should the box hide any behind a "show more" control?~~
      — **Resolved:** no. Every card renders, grouped by label with counts. Hiding
      cards by default would trade honesty for brevity, and the multi-select node
      filter is the tool for narrowing.
- [x] ~~What happens to a card once it is accepted or dismissed?~~ — **Resolved:**
      it stays visible, muted, and sinks to the bottom of its own label group with
      an undo action. Pending findings therefore stay at the top of each group and
      the group's total stays truthful.
- [x] ~~Where does the action to analyse a never-analysed pair live once the box
      groups by label instead of by document?~~ — **Resolved:** in a coverage strip
      above the label groups, listing each unanalysed pair with its own analyse
      action. The strip disappears when coverage is complete.
- [x] ~~Can more than one document be selected in the filter?~~ — **Resolved:**
      yes, the filter is multi-select. Comparing the two peer regulators together
      is a real drafting need, and a single-select filter forces two passes.
- [x] ~~Does the Reviewed tab redesign belong in this epic or the Recommendations
      specification?~~ — **Resolved:** this epic. Accepting a finding that then
      fails to appear is a broken promise, so the tab that receives accepted
      findings ships with the box that accepts them. The Recommendations tab is a
      separate concern and stays in its own specification.
- [x] ~~What replaces the Related · 1 hop tab?~~ — **Resolved:** nothing, in this
      epic. Its peer-context content is now reachable from the Pairwise Findings
      box, which covers the same neighbourhood more completely. The Recommendations
      specification claims the slot.

---

## Dependencies & Integration

- **Affected features:** the Task Screen (`frontend/src/features/task/`), the
  Drafting Workspace (`frontend/src/features/drafting-workspace/`), the Review
  Linkages screen (`frontend/src/features/review-linkages/`, which gains
  deep-link-to-finding), and the engine's workstream task routes
  (`engine/api.py`).
- **Shared state:** `review_state` on a finding, persisted per-edge under
  `data/workstreams/<ws>/findings/<edge_id>.json` by `engine/findings.py`. All
  three surfaces (task box, review screen, Reviewed tab) read and write the same
  field via `PATCH .../edges/{edge_id}/findings/{finding_id}` — that route is
  unchanged by this epic and remains the single write path.
- **Breaking changes:**
  - `GET /api/workstreams/{ws}/tasks/{node_id}/related-linkages` becomes unused
    once Story 2 lands. It is **retained** (deprecated, not deleted) so the
    retired `opres-v2`/`rmit-v2-2025` fixtures and its existing tests keep
    passing; the frontend simply stops calling it.
  - `GET .../reviewed-linkages` widens its edge scope. Response shape is
    unchanged (`{findings: LinkageCard[]}`), so no consumer contract breaks —
    existing callers just receive more cards.
  - `draft_empty` on `GET .../tasks/{node_id}` becomes unused by the task screen
    but stays in the response; `engine/tests/test_api_workstreams.py` asserts it
    and the field is cheap.
- **Migration path:** none required. Both stories are read-projection changes
  plus frontend work; no fixture rewrite, no data backfill. `review_state` is
  already derived-on-read with a `pending` default (`engine/findings.py`), so
  findings files that have never been reviewed need no migration.

## Shared Architecture Notes

**One neighbourhood helper, two consumers.** Both stories need the identical edge
set. Add a single helper to `engine/workstreams.py` and call it from both routes
so the two surfaces can never disagree:

```python
def neighbourhood_edges(
    edges: list[dict[str, Any]], node_id: str
) -> list[dict[str, Any]]:
    """Edges where at least one endpoint is `node_id` or a direct neighbour of it.

    The task's own edges plus every edge incident to a first-order neighbour, in
    graph order. Excludes edges whose BOTH endpoints are second-order — a linkage
    between two documents that are each two hops from the draft relates neither to
    the draft nor to anything the drafter declared.
    """
```

Set algebra, given `N1 = {node_id} | neighbour_ids(edges, node_id)`: keep edge `e`
when `e.source in N1 or e.target in N1`. Note this is a _superset_ of both
existing helpers — `edges_between(..., exclude_node=...)` (the Related tab's
anchor↔anchor edges) and the task route's `source == node_id` scan.

Worked example on `data/workstreams/open-finance-pd-2026/graph.json`, where
`node_id = open-finance-pd-2026-pd`:

| Edge                                              | Endpoints in N1?         | Kept |
| ------------------------------------------------- | ------------------------ | ---- |
| `e-open_finance_pd_2026_pd--ed_open_finance_2025` | both (task, 1st-order)   | yes  |
| `e-hkma_open_api_framework--ed_open_finance_2025` | target is 1st-order      | yes  |
| `e-bis_papers_168--ed_open_finance_2025`          | target is 1st-order      | yes  |
| `e-rmit_2025--ed_open_finance_2025`               | target is 1st-order      | yes  |
| `e-abs_mas_api_playbook--ed_open_finance_2025`    | target is 1st-order      | yes  |
| _(hypothetical)_ `e-hkma…--bis_papers_168`        | neither (both 2nd-order) | no   |

N1 here is `{open-finance-pd-2026-pd, ed-open-finance-2025}` — the task node has
exactly one edge. All five real edges qualify; three carry findings (51 + 47 + 32
= 130), two have no findings file at all.

**Direction is not normalised.** `open-finance-pd-2026` stores its edges pointing
_into_ the ED node (`hkma-open-api-framework -> ed-open-finance-2025`), the
opposite of `opres-v2`'s task-outward convention. `neighbourhood_edges` must
therefore check both endpoints, and no surface may assume the task is the edge
source. `_linkage_card`'s existing `left`/`right` = `edge.source`/`edge.target`
projection already handles this correctly — do not "fix" it to put the task first.

**Findings-file presence is the analysed signal.** Unchanged from today: an edge
with no `findings/<edge_id>.json` has never been analysed
(`FindingsNotAnalysedError`), which is a different condition from an analysed edge
with zero findings. The analyze route deliberately refuses to write an empty file
to keep that distinction one-way-safe. The coverage strip is built from exactly
this signal.

**Review state travels with the card.** `_linkage_card` currently omits
`review_state`, because both its consumers filtered by it server-side. Story 1
needs it on the card to render accepted/dismissed styling and sinking, so the
projection gains `review_state` — additive, and Story 2's stricter
accepted-only filter still runs server-side.

**No new packages.** Both stories use what is already in `frontend/package.json`
(React 18, TanStack Query, Tailwind, lucide-react) and the engine's existing
FastAPI + stdlib surface.

## Shared Test Fixtures

- `data/workstreams/open-finance-pd-2026/` is the primary fixture for both
  stories — it is the only one whose task node's findings all live on
  second-order edges, so it is the only fixture that proves the neighbourhood
  rule. 130 findings: 30 `differs-on`, 11 `silent-on`, 14 `goes-beyond`, 75
  `aligns-with`, **0 `conflicts-with`** (so the empty-group case is covered by
  the real fixture, not a synthetic one).
- `data/workstreams/opres-v2/` is the regression fixture: task-outward edges, no
  anchor↔anchor edges, seven neighbours, four analysed. Both stories must keep
  its existing behaviour intact.
- Neither fixture is modified by either story. **No fixture edits, no findings
  rewrites** — if a scenario seems to need one, it is testing the wrong thing.
