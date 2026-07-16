# Review Linkages — Pairwise Clause Reader with Accept / Dismiss / Comment

**Ticket:** TBD

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)

The review linkages screen is where a drafter reads every AI-found relationship between two documents in her workstream side-by-side with the underlying clauses. Each finding can be accepted, dismissed, or discussed in a comment thread, and new linkages can be surfaced by prompting the finder again or added by hand from parsed clause lists. This is the surface that turns raw pairwise linkage output into a curated set of findings the drafter can trust downstream.

## User Story

As Aisyah R. (an Operational Resilience policy drafter), I want to review every AI-found linkage between my working draft and an anchor document, accept or dismiss each one, and thread comments with reviewers, so that only the linkages I trust carry forward into my drafting.

## Background & Context

**Current state:**

- The workstream graph shows a document-level edge between the OpRes PD v0.3 working draft and the RMiT PD (28 Nov 2025). Clicking the edge and running **Analyze linkages** produces a batch of AI-found findings.
- Today those findings live in an internal trace file; a drafter has no surface to read them clause-by-clause, resolve them, or discuss them with a reviewer.
- Comments on cross-workstream linkages happen out-of-band — chat threads, email, and marginalia in Word.

**Problem:**

- A drafter cannot judge a finding without seeing the exact clause text on both sides. Truncated summaries are not enough to accept or dismiss confidently.
- False positives are inevitable in AI-found linkages. Without an explicit dismiss action, they clutter downstream drafting views and erode trust.
- Reviewer questions on individual findings get lost in Teams threads and never make it back to the drafter as she writes the next version.
- When the AI misses an obvious pair a human eye can catch, the drafter has no way to add it without violating the verbatim-citation rule.

## Target User & Persona

- **Who:** Aisyah R., senior policy drafter for BNM Operational Resilience. Owns the OpRes PD v0.3 working draft; her workstream depends on the RMiT PD as a same-domain anchor.
- **Context:** After running **Analyze linkages** on a workstream-graph edge, she needs to work through the returned findings one at a time before starting the next drafting session on §5 or §7.
- **Current workaround:** Reads finder output in a raw trace file, cross-references clauses in two PDF windows, and tracks accept/dismiss decisions in a personal spreadsheet. Reviewer feedback comes through Teams and rarely re-joins the finding.

## Goals

- Let a drafter read every AI-found linkage against verbatim source and target clause text without leaving the screen.
- Capture an explicit accept, dismiss, or discuss decision on every finding.
- Allow the drafter to expand the finding set — either by prompting the finder again with a focus, or by hand-adding a linkage from parsed clause lists.
- Preserve the verbatim-citation guarantee: no free-text clause references anywhere, even on manually added linkages.
- Persist accepted findings so they flow into the drafting workspace, and keep dismissed findings dismissed everywhere until explicitly reopened.

## Non-Goals

- **Correction store / few-shot re-run on nearby linkages** — accept and dismiss decisions do not yet retrain finder or critic on adjacent pairs. Deferred per epic.
- **Bulk accept / bulk dismiss** — one card at a time is enough for MVP1.
- **Filtering the findings list by semantic label** — the list on any single pair is short enough to scan; a filter widget adds clutter without demo value.
- **Editing accepted findings** — once accepted, a finding is either kept as-is or dismissed and re-created.

## User Workflow

1. **Land on the screen.** Aisyah arrives from the workstream graph's edge detail (clicking **Review** on the OpRes PD ↔ RMiT PD edge) or from a pair card on the task screen. The header shows the pair she is reviewing and running counts of total, accepted, and dismissed findings.
2. **Read the two panes.** The left pane shows the OpRes PD v0.3 working draft clause-by-clause; the centre pane shows the RMiT PD (28 Nov 2025) the same way. Each clause card carries its clause number, short title, and verbatim clause text.
3. **See the first finding pre-selected.** On page load the first finding card is already active. The clauses it cites are highlighted with a coloured left border and scrolled into view on both panes.
4. **Click a different finding.** Aisyah clicks another card in the sidebar. The previous highlight clears; the new card's cited clauses light up and scroll into view. If the target clause was off-screen, the target pane scrolls to reveal it.
5. **Accept a finding.** On the version-drift finding she agrees with, she clicks **Accept**. A persistent "accepted" badge appears on the card, the accept and dismiss buttons disappear, and the card stays in the stack.
6. **Dismiss a false positive.** On the §4.4 ↔ §10.49 card (different subjects) she clicks **Dismiss**. The card greys, drops to the bottom of the stack, and the accept/dismiss row is replaced by a **Reopen** link.
7. **Discuss with a reviewer.** She clicks the comment icon on the goes-beyond finding, reads Priya's earlier reply, types "@Farid what do you think?" and clicks **Post**. Her comment appears at the bottom of the thread with her avatar, name, and a timestamp.
8. **Ask the finder for more.** After scanning the five findings, she clicks **Find more linkages**, chooses the "Governance and accountability" focus area, adds an optional prompt, and clicks **Run**. While the run is in flight the sidebar shows a loading state.
9. **Add one by hand.** She noticed §7.1 relates to RMiT §17.2 (critical technology outsourcing) but the AI missed it. She clicks **Add manually**, picks §7.1 from the source dropdown, §17.2 from the target dropdown, chooses **aligns-with**, writes a one-sentence finding, and clicks **Add**. The new finding appears at the top of the stack, already marked as accepted.
10. **Leave and return later.** When she reopens the screen the next day her accepted findings still carry their badge, her dismissed finding is still dismissed, and her comments are all there.

## Acceptance Criteria

### Scenario: Landing on the OpRes PD ↔ RMiT PD pair renders both panes and the findings sidebar

```gherkin
Given Aisyah has run Analyze linkages on the OpRes PD v0.3 to RMiT PD (28 Nov 2025) edge
  And the run produced five findings
When she opens the review linkages screen for that pair
Then she sees "OpRes PD v0.3 working draft" as the source pane with each of §4.4, §5.3, §6.3, §7.1, and §8.2 rendered as a clause card
  And she sees "RMiT PD (28 Nov 2025)" as the target pane with the front matter, §10.49, §17.1, §17.2, and §21.5 rendered as clause cards
  And each clause card shows its clause number, its short title, and the verbatim clause text
  And she sees five finding cards in the sidebar
  And the header shows "5 findings", "1 accepted", "1 dismissed"
```

### Scenario: First finding is auto-selected on page load

```gherkin
Given the screen has just loaded for the OpRes PD to RMiT PD pair
When Aisyah does nothing
Then the first finding card in the sidebar is marked as the active card
  And OpRes PD §7.1 in the source pane is highlighted with a coloured left border
  And the RMiT PD front matter clause in the target pane is highlighted with a coloured left border
  And both highlighted clauses are scrolled into view in their respective panes
```

### Scenario: Clicking a finding card highlights and scrolls to its cited clauses

```gherkin
Given the version-drift finding is currently the active card
When Aisyah clicks the "Third-party concentration overlaps RMiT §17.1" finding card
Then the version-drift card is no longer marked active
  And the third-party concentration card is marked active
  And OpRes PD §7.1 and RMiT front matter are no longer highlighted
  And OpRes PD §8.2 in the source pane is highlighted
  And RMiT §17.1 in the target pane is highlighted
  And both highlighted clauses are scrolled into view
```

### Scenario Outline: Every finding card highlights the correct pair of clauses

```gherkin
Given the five findings on the OpRes PD to RMiT PD pair are present
When Aisyah clicks the "<finding>" card
Then "<source clause>" is highlighted in the source pane
  And "<target clause>" is highlighted in the target pane
  And the card is marked as the active card

Examples:
  | finding                                       | source clause          | target clause              |
  | Anchor to superseded RMiT version             | OpRes PD §7.1          | RMiT PD front matter       |
  | Third-party concentration overlaps RMiT §17.1 | OpRes PD §8.2          | RMiT PD §17.1              |
  | Scenario testing scope wider than RMiT        | OpRes PD §5.3          | RMiT PD §21.5              |
  | Single accountable officer, absent from RMiT  | OpRes PD §6.3          | (no target clause; silent) |
```

### Scenario: Accepting a finding pins an accepted badge and removes the action buttons

```gherkin
Given the "Anchor to superseded RMiT version" finding is visible with Accept, Dismiss, and Comment buttons
When Aisyah clicks Accept on that card
Then the card gains a persistent "accepted" badge next to its label pill
  And the Accept and Dismiss buttons are no longer shown on that card
  And the card stays in its current position in the sidebar
  And the header count updates to show 2 accepted findings
```

### Scenario: Dismissing a false-positive greys the card and moves it to the bottom

```gherkin
Given the "Scenario testing scope wider than RMiT" finding is open with Accept and Dismiss buttons
When Aisyah clicks Dismiss on that card
Then the card is visually greyed out
  And the card moves to the bottom of the findings sidebar
  And the Accept and Dismiss buttons are replaced by a "Reopen" link on that card
  And the header count updates to show 2 dismissed findings
```

### Scenario: Reopening a dismissed finding restores its accept and dismiss controls

```gherkin
Given the "Board approval cadence — false positive" card is dismissed and shows a "Reopen" link
When Aisyah clicks Reopen on that card
Then the card is no longer visually greyed out
  And the Accept and Dismiss buttons are shown again on that card
  And the "Reopen" link is no longer shown
  And the header count updates to show 0 dismissed findings
```

### Scenario: Opening a comment thread shows existing replies

```gherkin
Given the "Anchor to superseded RMiT version" finding already has two replies from Farid M. and Aisyah R.
When Aisyah clicks the comment icon on that card
Then the thread expands under the card
  And she sees Farid's reply with his initials avatar, his name, and its timestamp
  And she sees her own earlier reply with her initials avatar, her name, and its timestamp
  And she sees a text input inviting a new comment and a Post button
```

### Scenario: Posting a new comment appends it to the thread

```gherkin
Given the comment thread on the "Single accountable officer" finding is open with Priya S.'s existing reply
When Aisyah types "Agree — I'll fold this into §6.3 preamble" into the comment input
  And she clicks Post
Then her new reply is appended below Priya's reply
  And her reply shows her initials avatar, her name, and a fresh timestamp
  And the comment count badge on the card increments from 1 to 2
```

### Scenario: Tagging a colleague in a comment

```gherkin
Given the comment thread on the "Third-party concentration overlaps RMiT §17.1" finding is open
When Aisyah types "@Farid can you double-check the cloud-provider carve-out?"
  And she clicks Post
Then the reply is appended to the thread with "@Farid" rendered as a tag
  And Farid M. is understood to be notified of the mention
```

### Scenario: Opening the Find more linkages modal shows the guided prompt

```gherkin
Given Aisyah is on the review linkages screen for the OpRes PD to RMiT PD pair
When she clicks "Find more linkages"
Then a modal opens titled "Find more linkages"
  And she sees a Focus area dropdown with options: Any (broad sweep), Third-party / outsourcing overlap, Governance and accountability, Testing and validation cadences, Definitions and scope
  And she sees an optional free-text prompt field
  And she sees a Run button and a Cancel button
```

### Scenario: Running Find more shows a loading state on the sidebar

```gherkin
Given the Find more linkages modal is open with focus area "Governance and accountability" selected
When Aisyah clicks Run
Then the modal closes
  And the findings sidebar shows a loading indicator scoped to the current pair
  And Aisyah can still read the source and target clause panes while the run is in flight
```

### Scenario: Opening the Add manually modal shows dropdown pickers for both clauses

```gherkin
Given Aisyah is on the review linkages screen for the OpRes PD to RMiT PD pair
When she clicks "Add manually"
Then a modal opens titled "Add linkage manually"
  And she sees a Source clause dropdown listing every parsed clause of OpRes PD v0.3: §4.4, §5.3, §6.3, §7.1, §8.2
  And she sees a Target clause dropdown listing every parsed clause of RMiT PD (28 Nov 2025): front matter, §10.49, §17.1, §17.2, §21.5
  And she sees a Linkage type dropdown with options: aligns-with, differs-on (neutral), differs-on (tighten), differs-on (loosen), conflicts-with, silent-on, goes-beyond
  And she sees a one-sentence finding text area
  And she sees a notice reminding her that the tool never invents clause references
```

### Scenario: Adding a manual linkage creates an accepted finding at the top of the stack

```gherkin
Given the Add manually modal is open
When Aisyah selects source clause "§7.1 Technology risk anchor"
  And she selects target clause "§17.2 Critical technology outsourcing"
  And she selects linkage type "aligns-with"
  And she writes "OpRes §7.1 relies on RMiT §17.2 to make the outsourcing carve-out enforceable"
  And she clicks Add linkage
Then the modal closes
  And a new finding card appears at the top of the findings sidebar
  And the new card carries an "aligns-with" label pill and a persistent "accepted" badge
  And clicking the new card highlights OpRes PD §7.1 in the source pane and RMiT §17.2 in the target pane
  And the header count updates to show one more total finding and one more accepted finding
```

### Scenario: Verbatim-citation rule blocks free-text clause references on manual add

```gherkin
Given the Add manually modal is open
When Aisyah tries to type "§99 Made-up clause" into the source clause selector
Then the source clause selector does not accept free text
  And only clauses parsed from the OpRes PD v0.3 clause index appear as selectable options
  And she cannot submit the manual add form without selecting a real parsed source clause and a real parsed target clause
```

### Scenario: Target clause off-screen scrolls into view when a card is clicked

```gherkin
Given the target pane has been scrolled so RMiT §21.5 is below the visible area
When Aisyah clicks the "Scenario testing scope wider than RMiT" finding card
Then the target pane automatically scrolls so RMiT §21.5 is brought into view
  And RMiT §21.5 is highlighted with a coloured left border
  And OpRes PD §5.3 in the source pane is highlighted and in view
```

### Scenario: Empty findings state on a freshly analysed pair

```gherkin
Given an edge has just been analysed by the finder and the critic returned zero findings
When Aisyah opens the review linkages screen for that pair
Then the source and target clause panes still render every parsed clause on both sides
  And the findings sidebar shows a "no linkages found on this pair — try Find more" empty-state message
  And the "Find more linkages" and "Add manually" buttons are still available
  And no finding card is marked as active because there are none to select
```

### Scenario: Dismissed findings stay dismissed after leaving and returning

```gherkin
Given Aisyah dismissed the "Board approval cadence — false positive" finding this morning
When she navigates away to the workstream graph
  And she returns to the review linkages screen for the same OpRes PD to RMiT PD pair later in the day
Then the "Board approval cadence — false positive" finding is still visibly dismissed
  And it is still at the bottom of the sidebar
  And it still shows a "Reopen" link instead of Accept and Dismiss buttons
```

### Scenario: Accepted findings persist to the drafting workspace's Reviewed tab

```gherkin
Given Aisyah has accepted the "Anchor to superseded RMiT version" finding on the review screen
When she opens the drafting workspace for the OpRes PD v0.3 task
Then the Reviewed linkages tab of the workspace shows the "Anchor to superseded RMiT version" finding
  And its accepted status is preserved
```

### Scenario: Dismissed findings do not appear in the drafting workspace's Reviewed tab

```gherkin
Given Aisyah has dismissed the "Board approval cadence — false positive" finding on the review screen
When she opens the drafting workspace for the OpRes PD v0.3 task
Then the Reviewed linkages tab does not show the "Board approval cadence — false positive" finding
```

### Scenario: Reaching the review screen from the task screen's pair card

```gherkin
Given Aisyah is on the OpRes PD v0.3 task screen
  And the task screen shows a pair card for OpRes PD v0.3 ↔ RMiT PD (28 Nov 2025)
When she clicks the pair card's Review link
Then she lands on the review linkages screen for that same pair
  And the screen behaves identically to arriving from the workstream graph edge detail
```

### Scenario: differs-on finding carries its sentiment tag

```gherkin
Given the "Scenario testing scope wider than RMiT" finding is a differs-on finding with sentiment "tighten"
When Aisyah views its card in the sidebar
Then she sees a "differs-on" label pill on the card
  And she sees a "tighten" sentiment tag on the same card
  And the finding summary explains that OpRes PD requires broader-scope scenario testing than RMiT
```

### Scenario: goes-beyond finding cites only a source clause

```gherkin
Given the "Single accountable officer — absent from RMiT" finding has OpRes PD §6.3 as source and no matching target clause
When Aisyah clicks that finding card
Then OpRes PD §6.3 is highlighted and scrolled into view in the source pane
  And no clause is highlighted in the target pane
  And the card's clause reference line reads "§6.3 ↔ (silent)"
```

## Business Rules & Constraints

- **Verbatim citations only, everywhere.** Every clause quoted in the two panes or referenced in a finding card must come from the parsed clause index for the cited document. On the Add manually modal, both source and target clause pickers are dropdowns of parsed clauses. Free text is refused. If a clause the drafter wants is not in the parsed index, she cannot add the linkage — the tool will not invent a clause reference.
- **Findings persist across screens.** Accepted findings appear on the drafting workspace's Reviewed linkages tab. Dismissed findings stay dismissed everywhere until explicitly reopened from the review screen.
- **Manual adds are accepted by default.** A drafter adding a linkage by hand has, by definition, already vetted it. The new card carries an "accepted" badge from the moment it is created; no separate accept step is needed.
- **Dismissed findings remain visible but greyed.** The card is moved to the bottom of the stack and dimmed. It is never deleted or hidden — the drafter must be able to reopen a dismissed finding at any time.
- **One active card at a time.** Only one finding card can be the currently selected one. Selecting a new card clears any previous highlight on both panes before applying the new one.
- **Dismissed cards are not selectable.** Clicking a greyed-out dismissed card does not make it active and does not change clause highlighting.
- **Semantic labels drive the label pill; sentiment is a separate tag.** A card carries exactly one of aligns-with, differs-on, conflicts-with, silent-on, or goes-beyond as its label pill. A sentiment tag (tighten, loosen, neutral) is only shown if the label is differs-on. No sentiment tag appears on any other label.
- **@tagging is limited to workstream colleagues in demo scope.** The demo covers Aisyah R., Farid M., and Priya S. Tagging any other name renders as plain text.
- **Header counts stay consistent.** The header running counts of total, accepted, and dismissed findings update immediately whenever a card is accepted, dismissed, reopened, or added.

## Success Metrics

- On the OpRes PD ↔ RMiT PD pair, Aisyah can accept, dismiss, comment, and manually add findings on the pre-seeded five findings without leaving the screen, in under three minutes end-to-end.
- Every clause reference shown on the screen — in a clause card, a finding summary, or a manually added linkage — is traceable to a real entry in the parsed clause index. Zero fabricated clause references appear.
- Accepted findings from the review screen appear unchanged on the drafting workspace's Reviewed tab; dismissed findings do not.
- Judges and product reviewers can, unaided, walk from the workstream graph through the review screen to the drafting workspace and see the accepted findings arrive on the Reviewed tab.

## Dependencies

- **Workstream graph edge detail.** The review screen is opened from the **Review** button on an analysed edge. The graph is responsible for triggering **Analyze linkages** and passing the resulting finding set into this screen.
- **Task screen pair card.** The review screen is also reachable from a pair card on the task screen; the two entry points land on the same screen with the same state.
- **Parsed clause index for both source and target documents.** Both panes render clauses from a pre-parsed clause index. The manual-add dropdowns are populated from the same index. Any document that has not been parsed cannot be used on this screen.
- **Widened linkage taxonomy.** The five semantic labels (aligns-with, differs-on, conflicts-with, silent-on, goes-beyond) and the three differs-on sentiment tags (tighten, loosen, neutral) are established by the engine taxonomy story and consumed here.
- **Drafting workspace's Reviewed tab.** Accepted findings from this screen surface there; dismissed findings do not.
- **Persistence of accept, dismiss, and comment decisions.** Decisions made here must survive navigation away and back, and must remain consistent with the drafting workspace's view.

## Open Questions

- [ ] Whether the manual-add clause pickers should default-filter to clauses containing overlapping concepts, or list every parsed clause. **Deferred (non-blocking):** default to every clause for MVP1; refine once a real drafter uses it.
- [ ] Whether the loading state during Find more should show partial results as the finder emits them, or wait for the critic to finish scoping. **Deferred (non-blocking):** wait-until-done is acceptable for MVP1 demo.

---

## Functional Requirements

- Route: `/workstreams/:workstreamId/edges/:edgeId/review`. Requires the edge to be analysed; otherwise render an empty state prompting the user to click **Analyze linkages** on the workstream graph.
- Each finding on load carries a `review_state: "pending" | "accepted" | "dismissed"` field. New findings default to `pending`. Manually added findings default to `accepted`.
- Accept / dismiss / reopen mutate the finding's `review_state` and persist to `data/workstreams/{workstream_id}/findings/{edge_id}.json`.
- Comment threads persist as an array on each finding. Each comment: `{id, author_id, author_name, text, created_at}`. `@tags` in text are stored verbatim; a simple regex extracts `@name` mentions for a future notification path (not built in MVP1).
- **Find more linkages** invokes the finder→critic with a scoped prompt (focus area + optional free text). Appended findings are marked `source: "find-more"`.
- **Add manually** creates a finding with `source: "manual"` and defaults to `review_state: "accepted"`. Source and target clauses must be picked from dropdowns populated from the parsed `ClauseIndex` — free text is forbidden.
- Cross-screen persistence: findings marked `accepted` on this screen appear in the drafting workspace's **Reviewed** tab.

## Permissions & Security

- Internal only, no auth in MVP1.
- Input validation on comment POST: `text` max 2000 chars; strip HTML tags.

## API Design (extend `engine/api.py`)

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}/review`

Returns the edge, both sides' parsed clauses, and every finding on the edge.

```json
{
  "edge": {
    "id": "e-opres--rmit",
    "source_node": {
      "id": "opres-pd-v0-3",
      "title": "OpRes PD v0.3",
      "kind": "task"
    },
    "target_node": {
      "id": "rmit-pd-2025",
      "title": "RMiT PD (28 Nov 2025)",
      "kind": "internal-published"
    }
  },
  "source_clauses": [
    {
      "number": "4.4",
      "title": "Dependency mapping",
      "text": "A financial institution shall map dependencies for each critical business service..."
    },
    {
      "number": "5.3",
      "title": "Scenario testing scope",
      "text": "Scenario testing shall cover severe-but-plausible disruptions across all critical business services..."
    },
    {
      "number": "6.3",
      "title": "Single accountable officer",
      "text": "The board shall designate a single accountable officer for operational resilience..."
    },
    {
      "number": "7.1",
      "title": "Technology risk anchor",
      "text": "Financial institutions shall comply with the Policy Document on Risk Management in Technology issued on 1 June 2023..."
    },
    {
      "number": "8.2",
      "title": "Third-party concentration",
      "text": "A financial institution shall limit third-party concentration risk on critical business services..."
    }
  ],
  "target_clauses": [
    {
      "number": "front-matter",
      "title": "Supersession notice",
      "text": "This Policy Document supersedes the version issued on 28 November 2025..."
    },
    {
      "number": "10.49",
      "title": "Cyber incident notification",
      "text": "A financial institution shall notify the Bank of any cyber incident within twenty-four hours..."
    },
    {
      "number": "17.1",
      "title": "Third-party technology risk",
      "text": "A financial institution shall identify, assess and manage risks arising from the use of third-party technology service providers..."
    },
    {
      "number": "17.2",
      "title": "Critical technology outsourcing",
      "text": "A financial institution shall obtain prior written approval from the Bank before outsourcing any critical technology function..."
    },
    {
      "number": "21.5",
      "title": "Scenario testing",
      "text": "A financial institution shall carry out scenario-based testing of its technology risk management framework at least annually..."
    }
  ],
  "findings": [
    {
      "id": "f-opres--rmit-1",
      "label": "conflicts-with",
      "sentiment": null,
      "summary": "Anchor to superseded RMiT version",
      "scope_note": null,
      "source_clauses": [
        {
          "clause_number": "7.1",
          "text": "Financial institutions shall comply with the Policy Document on Risk Management in Technology issued on 1 June 2023..."
        }
      ],
      "target_clauses": [
        {
          "clause_number": "front-matter",
          "text": "This Policy Document supersedes the version issued on 28 November 2025..."
        }
      ],
      "review_state": "pending",
      "source": "finder-critic",
      "comments": []
    }
  ]
}
```

### `PATCH /api/workstreams/{workstream_id}/findings/{finding_id}`

Body: `{"review_state": "accepted" | "dismissed" | "pending"}`. Idempotent — sending the same state twice is a no-op.

### `POST /api/workstreams/{workstream_id}/findings/{finding_id}/comments`

Body: `{"text": "Agree — the 2023 version is fully superseded. Should we also update every RMiT reference in the Open Finance ED?"}`. Returns the appended comment with server-generated `id` and `created_at`.

### `POST /api/workstreams/{workstream_id}/edges/{edge_id}/find-more`

Body:

```json
{
  "focus_area": "Governance and accountability",
  "prompt": "Focus on board-level oversight duties and dual-role accountable officers."
}
```

Allowed `focus_area` values: `"Any"`, `"Third-party / outsourcing overlap"`, `"Governance and accountability"`, `"Testing and validation cadences"`, `"Definitions and scope"`. Response: appended findings with `source: "find-more"`, each freshly `review_state: "pending"`.

### `POST /api/workstreams/{workstream_id}/edges/{edge_id}/findings`

Manual add. Body:

```json
{
  "label": "aligns-with",
  "sentiment": null,
  "summary": "OpRes §7.1 relies on RMiT §17.2 to make the outsourcing carve-out enforceable",
  "source_clause_number": "7.1",
  "target_clause_number": "17.2"
}
```

Server validates that both clause numbers exist in `ClauseIndex` for their respective documents. On success, the returned finding is `review_state: "accepted"`, `source: "manual"`.

### Error table

| Status | Code                   | Condition                                                  |
| ------ | ---------------------- | ---------------------------------------------------------- |
| 404    | `EDGE_NOT_FOUND`       | `edge_id` missing                                          |
| 400    | `EDGE_NOT_ANALYSED`    | `GET /review` on an unanalysed edge (no findings file yet) |
| 400    | `INVALID_REVIEW_STATE` | `PATCH` with an unknown state                              |
| 400    | `INVALID_LABEL`        | Manual add with label outside the 5-label set              |
| 400    | `INVALID_SENTIMENT`    | Sentiment supplied on a non-`differs-on` label             |
| 400    | `CLAUSE_NOT_INDEXED`   | Manual add cites a clause not in `ClauseIndex`             |
| 400    | `TEXT_TOO_LONG`        | Comment text > 2000 chars                                  |
| 404    | `FINDING_NOT_FOUND`    | `finding_id` missing                                       |

## Data Model

`data/workstreams/{workstream_id}/findings/{edge_id}.json`:

```json
{
  "edge_id": "e-opres--rmit",
  "generated_at": "2026-07-11T04:20:15Z",
  "trace_ref": "connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json",
  "findings": [
    {
      "id": "f-opres--rmit-1",
      "label": "conflicts-with",
      "sentiment": null,
      "summary": "Anchor to superseded RMiT version",
      "scope_note": null,
      "source_clauses": [
        {
          "clause_number": "7.1",
          "text": "Financial institutions shall comply with the Policy Document on Risk Management in Technology issued on 1 June 2023..."
        }
      ],
      "target_clauses": [
        {
          "clause_number": "front-matter",
          "text": "This Policy Document supersedes the version issued on 28 November 2025..."
        }
      ],
      "review_state": "pending",
      "source": "finder-critic",
      "comments": []
    },
    {
      "id": "f-opres--rmit-2",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "OpRes PD requires scenario testing across every critical business service; RMiT §21.5 only requires annual testing of the technology risk framework",
      "scope_note": "Scope divergence: business-service breadth vs technology-framework depth",
      "source_clauses": [
        {
          "clause_number": "5.3",
          "text": "Scenario testing shall cover severe-but-plausible disruptions across all critical business services..."
        }
      ],
      "target_clauses": [
        {
          "clause_number": "21.5",
          "text": "A financial institution shall carry out scenario-based testing of its technology risk management framework at least annually..."
        }
      ],
      "review_state": "pending",
      "source": "finder-critic",
      "comments": []
    },
    {
      "id": "f-opres--rmit-3",
      "label": "goes-beyond",
      "sentiment": null,
      "summary": "Single accountable officer for operational resilience — absent from RMiT",
      "scope_note": null,
      "source_clauses": [
        {
          "clause_number": "6.3",
          "text": "The board shall designate a single accountable officer for operational resilience..."
        }
      ],
      "target_clauses": [],
      "review_state": "pending",
      "source": "finder-critic",
      "comments": [
        {
          "id": "c-2026-07-12-001",
          "author_id": "ps",
          "author_name": "Priya S.",
          "text": "Should this officer also cover cyber incident escalation under RMiT §10.49?",
          "created_at": "2026-07-12T02:15:00Z"
        }
      ]
    }
  ]
}
```

Comment shape:

```json
{
  "id": "c-2026-07-13-001",
  "author_id": "fm",
  "author_name": "Farid M.",
  "text": "Agree — the 2023 version is fully superseded. Should we also update every RMiT reference in the Open Finance ED?",
  "created_at": "2026-07-12T09:15:00Z"
}
```

## UI / Frontend Requirements

Components under `frontend/src/features/review-linkages/`:

- `ReviewLinkagesPage.tsx` — page route wired to `/workstreams/:workstreamId/edges/:edgeId/review`. Owns the active-finding state and orchestrates the three-column layout: source pane, target pane, findings sidebar.
- `ClausePane.tsx` — vertical scrollable pane rendering clause cards, each with clause-number title + verbatim text. Highlighted-clause behaviour: when a finding is active, cards whose numbers are in the finding's source/target clause list get `bg-indigo-50 border-l-4 border-indigo-500` styling and scroll into view.
- `FindingCard.tsx` — shadcn `Card` with semantic-label `Badge` (colour-coded per label), sentiment sub-badge for `differs-on`, summary, `Accept` / `Dismiss` buttons, `Comment` button with count.
- `CommentThread.tsx` — inline expansion, list of comments with `Avatar` + name + timestamp, text input + Post button.
- `FindMoreDialog.tsx` — shadcn `Dialog`, focus-area `Select` (5 options), textarea for optional prompt, Submit button.
- `AddManuallyDialog.tsx` — shadcn `Dialog`, source-clause `Select` (options from parsed `ClauseIndex`), target-clause `Select`, label `Select`, sentiment `Select` (shown only when label = `differs-on`), summary `Input`.

State:

- TanStack Query key: `['review', workstreamId, edgeId]`.
- Active-finding state is local; clicking a card sets it and triggers scroll to the highlighted clauses.
- Mutations (`accept`, `dismiss`, `reopen`, `comment`, `find-more`, `manual-add`) invalidate the review query on success.

Styling:

- Label colour map (Tailwind): `aligns-with` → emerald, `differs-on` → indigo, `conflicts-with` → red, `silent-on` → sky, `goes-beyond` → sky.
- Sentiment sub-badge colour: neutral gray for `neutral`, indigo up-arrow for `tighten`, amber down-arrow for `loosen`.

## Architecture Notes

- Reuses shadcn primitives from the workstream-graph story: `Card`, `Badge`, `Dialog`, `Button`, `Input`, `Select`, `Textarea`, `Avatar`, `Separator`, `ScrollArea`.
- New dep on `scroll-into-view-if-needed` (small utility, ~4kb) for smooth scroll-to-clause behaviour. Optional — can use native `element.scrollIntoView({behavior: 'smooth', block: 'center'})`.
- Integration point: `engine/api.py`. New helper module `engine/findings.py` owns read/write of the per-edge findings file.

## Exemplar Files

- `engine/api.py` — FastAPI route pattern; error-response shape.
- `engine/clauses.py` — `ClauseIndex.get(number)` and `ClauseIndex.entries_for_document(doc_id)` used by manual-add validation and by the review GET's clause payload.
- `engine/connections.py` — finder→critic entry point reused by `POST /find-more`.
- `docs/poc/workstream-brain/review.html` — visual reference for pane layout, highlight styling, and card affordances.

## Implementation Plan

- **Task 1 — Backend endpoints (medium, INDEPENDENT of frontend):** FastAPI routes `GET /review`, `PATCH /findings/{id}` (review-state), `POST /findings/{id}/comments`, `POST /edges/{id}/find-more`, `POST /edges/{id}/findings` (manual add). Wire all error codes from the table. Return payloads shaped exactly per the API section.
- **Task 2 — Persistence helper (small, SEQUENTIAL after Task 1):** persist `review_state` + comments to `data/workstreams/{workstream_id}/findings/{edge_id}.json`; write helper in `engine/findings.py` with `load(edge_id)`, `save(edge_id, payload)`, `append_comment(finding_id, comment)`, `set_review_state(finding_id, state)`.
- **Task 3 — Page + clause panes (medium, SEQUENTIAL after workstream-graph Task 1):** build `ReviewLinkagesPage` + `ClausePane` (two instances, source + target) with scroll-into-view and highlight styling. Wire TanStack Query to `GET /review`.
- **Task 4 — Finding card + accept/dismiss/reopen (medium, SEQUENTIAL after Task 3):** build `FindingCard`; wire `PATCH` mutations; enforce dismissed-cards-move-to-bottom sort; wire header counts.
- **Task 5 — Comment thread (small, SEQUENTIAL after Task 4):** build `CommentThread` with avatar + timestamp; wire `POST` comment; render `@tag` matches with a badge span.
- **Task 6 — Find more dialog (small, SEQUENTIAL after Task 4):** build `FindMoreDialog` with focus-area `Select`; wire `POST /find-more`; sidebar loading state.
- **Task 7 — Add manually dialog (medium, SEQUENTIAL after Task 4):** build `AddManuallyDialog` with `ClauseIndex`-populated dropdowns; enforce `CLAUSE_NOT_INDEXED` on server; hide sentiment `Select` unless label is `differs-on`.

## Negative Constraints

- Do NOT allow free-text clause references in manual-add. Only dropdown values from `ClauseIndex`.
- Do NOT fabricate clause text anywhere. All clause text on this screen comes from `ClauseIndex.get(number).text` or from the finding's stored `ClauseCitation.text`.
- Do NOT delete findings. Dismiss is a state, not a deletion.
- Do NOT filter findings by label in MVP1 (list is short enough to scan).
- Do NOT bulk-accept or bulk-dismiss in MVP1.

## Test Scenarios (implementation-level)

Backend:

- `test_GET_review_returns_source_target_clauses_and_findings`
- `test_GET_review_400_EDGE_NOT_ANALYSED_when_no_findings_file`
- `test_GET_review_404_EDGE_NOT_FOUND_when_edge_id_unknown`
- `test_PATCH_review_state_persists_to_disk`
- `test_PATCH_review_state_400_INVALID_REVIEW_STATE_on_bad_value`
- `test_PATCH_review_state_is_idempotent`
- `test_POST_comment_appends_and_returns_new_comment`
- `test_POST_comment_400_TEXT_TOO_LONG_at_2001_chars`
- `test_POST_comment_strips_html_tags`
- `test_POST_manual_finding_rejects_unindexed_source_clause_400_CLAUSE_NOT_INDEXED`
- `test_POST_manual_finding_rejects_free_text_bypass_400_CLAUSE_NOT_INDEXED`
- `test_POST_manual_finding_accepts_with_valid_clauses_and_defaults_to_accepted`
- `test_POST_manual_finding_rejects_sentiment_on_non_differs_on_400_INVALID_SENTIMENT`
- `test_POST_manual_finding_400_INVALID_LABEL_on_unknown_label`
- `test_POST_find_more_appends_findings_with_source_find_more`
- `test_dismissed_finding_appears_in_drafting_reviewed_tab_as_absent` (integration with drafting story)

Frontend component tests:

- Clicking a finding card scrolls both panes to the cited clauses and highlights them.
- Dismiss moves a card to the bottom of the stack and shows Reopen.
- Reopen restores Accept/Dismiss controls.
- `AddManuallyDialog` submit is disabled when source or target clause is not selected.
- `AddManuallyDialog` hides the sentiment `Select` unless label is `differs-on`.
- `goes-beyond` finding with no target clause displays "§6.3 ↔ (silent)" and highlights only the source pane.

## Verification

- Backend: `pytest engine/tests/test_api.py::test_review -v`.
- Frontend: `npm run test` from `frontend`.
- E2E: `frontend/e2e/review-linkages.spec.ts` — "land on review of OpRes×RMiT edge, click first finding, accept it, add a comment, dismiss another, reopen it, add manual finding". Assign to Tasks 4/5/6/7.
