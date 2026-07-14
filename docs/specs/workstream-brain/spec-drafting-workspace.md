# Drafting Workspace with Three-Tab Side Panel

**Ticket:** TBD

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)

The drafting workspace is where a drafter writes the working policy document with all the context they built up during review sitting next to their editor. A styled document surface takes the right side of the screen; a three-tab side panel on the left holds accepted linkages, related linkages between neighbour documents, and a Drafting Copilot chat. This story ensures the drafter never has to leave the workspace to remember what they agreed with, what peers have already said, or what a preamble should look like.

## User Story

As Aisyah R. (senior policy drafter), I want to draft my Policy Document with the reviewed linkages and related-workstream context right next to my editor, and have a Copilot I can ask for a draft skeleton or preamble, so that I don't lose my place switching between windows.

## Background & Context

**Current state:**

- Aisyah has finished reviewing the OpRes PD v0.3 against its anchors on the review linkages screen. She accepted four findings and dismissed the rest.
- She has opened the OpRes PD v0.3 task from the workstream graph and clicked **Open draft** in the task screen's top-right.
- Today, without this tool, she would draft in Word with a stack of open browser tabs holding BCBS, HKMA, FSB, and RMiT — trying to remember which clause she promised herself she would tighten, and which peer clause she was adapting from.

**Problem:**

- Context built up during review evaporates when the drafter opens their document. The finding she accepted about single accountable officer expansion (§6.3) has to be re-remembered.
- Related peer positions that have already been agreed between anchor documents themselves (e.g. HKMA aligning with BCBS) are invisible to the drafter unless she goes and reads each anchor.
- There is no assistant that can produce a first-draft preamble grounded in the accepted linkages and the workstream's citation discipline.

## Target User & Persona

- **Who:** Aisyah R., senior policy drafter, owner of the Operational Resilience workstream. Also drafts RMiT v2 in parallel.
- **Context:** Mid-workstream, after review is complete. She is writing §5.3 (scenario testing cadence) and §6.3 (accountable officer) of the OpRes PD v0.3.
- **Current workaround:** Word document plus five open browser tabs plus a printed spreadsheet of manually tracked peer positions plus post-it notes on the desk.

## Goals

- Put every accepted linkage from review on the same screen as the editor, so nothing gets lost in transit.
- Surface related linkages between neighbour documents themselves (1 hop from the task) as a lightweight peer-context feed.
- Give the drafter a Copilot they can ask for a preamble, section skeleton, or FAQ answer that respects verbatim citation.
- Preserve the drafter's sense of place — one screen, no window switching.

## Non-Goals

- Real Microsoft Word, PowerPoint, or Excel embed. The editor is a styled document surface only.
- Functional Copilot backend in MVP1. The demo runs on a pre-scripted Copilot conversation.
- Editing history or version control on the working draft.
- Intent preset dropdown behaviour. The seven presets render as a signal of surface area; they do not condition Copilot prompts in MVP1.
- Cross-cluster ripple analysis (deferred; the task's neighbours are the outer edge of MVP1 traversal).

## User Workflow

1. **Land on the workspace.** Aisyah clicks **Open draft** on the OpRes PD v0.3 task screen. The drafting workspace opens with the document surface on the right, the three-tab side panel on the left, and the Reviewed tab active by default.
2. **See the reviewed linkages pinned.** The Reviewed tab shows four cards — one per accepted finding from the review screen. Each card names the semantic label, sentiment (if the label is `differs-on`), a one-line summary, and the cited-clause reference.
3. **Read inline callouts against the draft.** As she scans the document surface, small callouts appear alongside the referenced clauses in the draft, colour-coded by semantic label so she can see at a glance which clauses have accepted context attached.
4. **Peek at related peer positions.** She switches to the Related · 1 hop tab and reads five cards showing linkages between her task's neighbour documents themselves — for example, HKMA aligning with BCBS Principle 6. A short banner explains that these are pre-existing agreements between neighbours, useful when her draft is silent on a concept but the neighbours have already formed a position.
5. **Ask the Copilot for a preamble.** She switches to the Copilot tab, picks "PD — Policy Document" from the intent dropdown, and asks the Copilot to draft the §6.3 preamble that flags the accountable-officer expansion. The Copilot returns an inline draft snippet with **Insert into draft** and **Regenerate** buttons.
6. **Insert the snippet.** She clicks **Insert into draft**. The snippet appears in the editor and is visually marked as generated (indigo left-border) so it is clear which text is her authoring and which came from the Copilot.
7. **Keep drafting.** She continues writing, referring back to the Reviewed tab as she works through §5.3. The auto-save indicator refreshes periodically ("Auto-saved 12s ago") so she is not worried about losing work.
8. **Return to the graph.** When she is ready to check her workstream at a glance, she clicks the breadcrumb "← Workstream graph" and returns to the workstream view.

## Acceptance Criteria

### Scenario: Landing on the drafting workspace for the OpRes PD v0.3 task

```gherkin
Given Aisyah has accepted 4 findings on the review linkages screen for the OpRes PD v0.3 task
  And Aisyah has clicked "Open draft" from the OpRes PD v0.3 task screen
When the drafting workspace opens
Then Aisyah sees the OpRes PD v0.3 working draft in the document surface on the right
  And Aisyah sees a three-tab side panel on the left with tabs labelled "Reviewed", "Related · 1 hop", and "Copilot"
  And the "Reviewed" tab is active by default
  And the "Reviewed" tab shows a count badge of 4
  And Aisyah sees the auto-save indicator "Auto-saved 12s ago" near the editor
```

### Scenario: Reviewed tab shows all accepted linkages from the review screen

```gherkin
Given the drafting workspace is open for the OpRes PD v0.3 task
  And Aisyah accepted the following findings on the review linkages screen:
    | semantic label   | sentiment | summary                                                          | cited clause                 |
    | conflicts-with   |           | Update RMiT version anchor                                       | §7.1 references 1 Jun 2023   |
    | differs-on       | tighten   | Annual vs biennial scenario testing                              | §5.3 ↔ HKMA §5.2             |
    | aligns-with      |           | Dependency mapping tracks BCBS Principle 7                       | §4.4 ↔ BCBS Principle 7      |
    | goes-beyond      |           | Single accountable officer                                       | §6.3 ↔ RMiT silent           |
When Aisyah views the "Reviewed" tab
Then Aisyah sees 4 cards, one per accepted finding
  And each card shows the semantic label as a pill
  And the "differs-on" card also shows a "tighten" sentiment indicator
  And each card shows the one-line summary and the cited-clause reference
```

### Scenario: Dismissed findings do not appear in the Reviewed tab

```gherkin
Given Aisyah dismissed 2 findings and accepted 4 findings on the review linkages screen
When Aisyah opens the drafting workspace
  And Aisyah views the "Reviewed" tab
Then Aisyah sees only the 4 accepted findings
  And Aisyah does not see the 2 dismissed findings
  And the tab count badge shows 4
```

### Scenario: Inline finding callouts are colour-coded per semantic label in the editor

```gherkin
Given the drafting workspace is open with 4 accepted findings on the OpRes PD v0.3 draft
When Aisyah scrolls through the document surface
Then Aisyah sees a callout next to §7.1 marked in the "conflicts-with" colour
  And Aisyah sees a callout next to §5.3 marked in the "differs-on" colour
  And Aisyah sees a callout next to §4.4 marked in the "aligns-with" colour
  And Aisyah sees a callout next to §6.3 marked in the "goes-beyond" colour
```

### Scenario Outline: Semantic label colour coding on inline callouts

```gherkin
Given the drafting workspace is showing an inline finding callout
When the callout represents a <label> finding
Then Aisyah sees the callout in the <colour> palette

Examples:
  | label          | colour  |
  | conflicts-with | red     |
  | differs-on     | indigo  |
  | aligns-with    | emerald |
  | goes-beyond    | sky     |
```

### Scenario: Highlighting a card in the Reviewed tab

```gherkin
Given the "Reviewed" tab shows 4 accepted-finding cards
When Aisyah clicks the card for "Single accountable officer (§6.3 ↔ RMiT silent)"
Then Aisyah sees the clicked card visually highlighted as active
  And other cards return to their default appearance
```

### Scenario: Related · 1 hop tab shows linkages between neighbour nodes

```gherkin
Given the drafting workspace is open for the OpRes PD v0.3 task
  And the task's neighbour anchors are BCBS OpRes 2021, HKMA SPM OR-2, FSB Toolkit, RMiT 2023, FSA §143, and ABM Industry Feedback
  And linkages already exist between neighbours as follows:
    | source | target | semantic label | summary                                             |
    | HKMA   | BCBS   | aligns-with    | HKMA implements BCBS OpRes Principle 6 verbatim     |
    | FSB    | BCBS   | aligns-with    | FSB toolkit references BCBS OpRes 2021 explicitly   |
    | RMiT   | FSA    | aligns-with    | RMiT anchors to FSA §143 statutory basis            |
    | HKMA   | FSB    | differs-on     | HKMA scoping narrower than FSB toolkit              |
    | ABM    | RMiT   | goes-beyond    | Industry asked for self-attestation on top of RMiT  |
When Aisyah switches to the "Related · 1 hop" tab
Then Aisyah sees an intro banner explaining that these are linkages between her task's neighbour documents, useful when her draft is silent on a concept
  And Aisyah sees 5 linkage cards
  And each card shows the source anchor pill, a "↔" separator, the target anchor pill, the semantic label pill, and the one-line summary
  And the tab count badge shows 5
```

### Scenario: Copilot tab default state

```gherkin
Given the drafting workspace is open for the OpRes PD v0.3 task
When Aisyah switches to the "Copilot" tab
Then Aisyah sees an intent preset dropdown with 7 options: "PD — Policy Document", "DP — Discussion Paper", "ED — Exposure Draft", "FAQ", "Engagement Deck", "Feedback Template for Industry", and "Peer Benchmarking"
  And Aisyah sees a chat history area seeded with a Copilot welcome message
  And Aisyah sees a sample exchange demonstrating an accepted-linkage-aware answer
  And Aisyah sees a text input at the bottom of the tab
  And Aisyah sees a "Send" button next to the input
```

### Scenario: Copilot generates a draft snippet with Insert and Regenerate actions

```gherkin
Given the "Copilot" tab is active with the "PD — Policy Document" intent preset selected
  And the Copilot welcome message reads "Hi Aisyah — I've loaded 4 accepted linkages and the OpRes DP feedback register. Want me to draft the §6.3 preamble that flags the accountable-officer expansion (goes-beyond RMiT)?"
When Aisyah types "Yes — keep it neutral for the transposition of BCBS Principle 7, and cross-reference RMiT §17.1"
  And Aisyah clicks "Send"
Then Aisyah sees her message right-aligned in indigo
  And Aisyah sees a Copilot response left-aligned in grey
  And the response contains a draft §6.3 preamble as an inline snippet
  And the snippet shows an "Insert into draft" button and a "Regenerate" button
  And any clause text quoted in the snippet is verbatim from the parsed clause index
```

### Scenario: Inserting a Copilot draft snippet into the editor

```gherkin
Given the Copilot has produced a draft §6.3 preamble snippet with an "Insert into draft" button
When Aisyah clicks "Insert into draft"
Then Aisyah sees the snippet appear in the editor
  And the inserted text is visually marked with an indigo left-border to distinguish it from user-authored text
```

### Scenario: Regenerating a Copilot draft snippet

```gherkin
Given the Copilot has produced a draft §6.3 preamble snippet with a "Regenerate" button
When Aisyah clicks "Regenerate"
Then Aisyah sees a fresh Copilot response in the chat history
  And the fresh response contains a new draft snippet with its own "Insert into draft" and "Regenerate" buttons
```

### Scenario: Intent preset dropdown is cosmetic in MVP1

```gherkin
Given the "Copilot" tab is active with the "PD — Policy Document" intent preset selected
  And a chat history exists between Aisyah and the Copilot
When Aisyah changes the intent preset to "FAQ"
Then Aisyah sees the dropdown reflect the new selection
  And the existing chat history is unchanged
  And subsequent Copilot behaviour is not required to differ from the previous preset
```

### Scenario: Editor toolbar is present but non-functional

```gherkin
Given the drafting workspace is open
When Aisyah looks at the editor toolbar
Then Aisyah sees buttons for bold, italic, underline, heading, and list
  And clicking any of these buttons is not required to alter the draft text in MVP1
```

### Scenario: Verbatim citation guarantee on Copilot output

```gherkin
Given the Copilot has produced a draft snippet that references RMiT §17.1
When Aisyah reads the quoted clause text in the snippet
Then the quoted text matches the parsed RMiT §17.1 clause verbatim
  And if the Copilot cannot find a matching clause, the snippet displays "No matching clause found" instead of an invented quotation
```

### Scenario: Auto-save indicator refreshes periodically

```gherkin
Given the drafting workspace has been open for at least one minute
When Aisyah looks at the auto-save indicator near the editor
Then Aisyah sees a timestamp such as "Auto-saved 12s ago"
  And the timestamp updates periodically to reflect the elapsed time
```

### Scenario: Returning to the workstream graph

```gherkin
Given the drafting workspace is open for the OpRes PD v0.3 task
When Aisyah clicks the breadcrumb "← Workstream graph"
Then Aisyah returns to the Operational Resilience workstream graph
  And the OpRes PD v0.3 draft state is preserved for the next visit
```

### Scenario: Tab count badges reflect current content

```gherkin
Given Aisyah has 4 accepted findings and 5 related-neighbour linkages for the OpRes PD v0.3 task
When Aisyah views the three-tab side panel
Then the "Reviewed" tab shows a count badge of 4
  And the "Related · 1 hop" tab shows a count badge of 5
  And the "Copilot" tab does not show a count badge
```

## Business Rules & Constraints

- **Reviewed tab is fed only by accepted findings.** Findings dismissed on the review screen do not appear in the Reviewed tab. A finding that is later re-opened on the review screen reappears here.
- **Related · 1 hop is bounded at exactly 1 hop from the task.** Linkages shown in this tab are between the task's neighbour documents themselves — never against the working draft. Second-hop and cross-cluster traversal are out of scope for MVP1.
- **Copilot intent preset dropdown is cosmetic in MVP1.** The seven options render as a signal of the surface area the tool will eventually cover, but changing the selection does not alter Copilot behaviour in the shipped MVP1 demo.
- **Generated text is visually distinguished from authored text.** Any snippet inserted from the Copilot carries a visible indigo left-border so the drafter and any downstream reviewer can tell at a glance which parts of the draft came from the Copilot.
- **Verbatim citation applies to Copilot output.** Any clause text the Copilot quotes in a chat response or an inserted snippet must be verbatim from the parsed clause index. If the Copilot cannot resolve a clause number to a real clause, it displays "No matching clause found" rather than inventing one.
- **The editor is a styled document surface, not a real Office embed.** The toolbar (bold, italic, underline, heading, list) is present as a visual signal only; toolbar buttons are not required to function in MVP1.
- **Auto-save is cosmetic.** The "Auto-saved 12s ago" indicator refreshes on a timer to communicate confidence; there is no real document versioning or persistence guarantee in MVP1.
- **Inline finding callouts colour-code by semantic label.** Red for `conflicts-with`, indigo for `differs-on`, emerald for `aligns-with`, sky for `goes-beyond`. `silent-on` findings do not surface as inline callouts because they have no draft clause to anchor to.
- **The workspace is reached only through the task screen.** The only entry point in MVP1 is the "Open draft" action on the OpRes PD v0.3 task screen. Direct URLs and other entry points are out of scope for MVP1.

## Success Metrics

- **Zero window-switching during the drafting step of the hackathon demo.** Aisyah's demo persona can complete the §6.3 preamble task using only the workspace — no external tabs opened.
- **All Copilot-quoted clauses are verbatim.** A demo-day audit of every clause quotation shown in the Copilot chat returns zero fabricated clause references.
- **Reviewed tab fidelity.** Every finding accepted on the review screen for the OpRes PD v0.3 task appears in the Reviewed tab on first workspace load; no dismissed findings appear.
- **Copilot snippet insertion works on stage.** The demo-day Copilot script produces at least one inline snippet that inserts into the editor on click and is visually distinguishable from the surrounding user-authored text.

## Dependencies

- **Review linkages story.** The Reviewed tab depends on the review screen having produced accepted findings for the OpRes PD v0.3 task and persisted them for the workspace to read.
- **Task screen story.** The workspace is reached by clicking "Open draft" from the OpRes PD v0.3 task screen. The task's neighbour list also seeds the Related · 1 hop tab.
- **Workstream graph story.** The task's neighbour relationships originate on the workstream graph and are inherited by the workspace's Related · 1 hop tab.
- **Engine taxonomy widening story.** Every semantic label pill and colour-coded callout in this workspace relies on the widened five-label taxonomy (`aligns-with`, `differs-on`, `conflicts-with`, `silent-on`, `goes-beyond`) with the `differs-on` sentiment tags (`tighten`, `loosen`, `neutral`).
- **Pre-seeded Operational Resilience workstream demo data.** The OpRes PD v0.3 draft text, the four accepted findings, and the five related-neighbour linkages are demo-day fixtures that must be present before the workspace can render.

## Open Questions

- [ ] **Auto-scroll from Reviewed card click to referenced clause in the editor.** MVP1 highlights the clicked card but does not commit to scrolling the editor to the referenced clause. Deferred (non-blocking): treat as a nice-to-have polish item after the demo lands.
- [ ] **Copilot intent-preset behavioural mapping.** MVP1 ships the seven intent presets as a cosmetic dropdown. Deferred (non-blocking): how each preset conditions the underlying prompt is a post-MVP1 design question captured in the epic overview.
- [ ] **Related · 1 hop traversal depth toggle.** MVP1 fixes at 1 hop. Deferred (non-blocking): a "2 hop" toggle is a post-MVP1 enhancement.
- [ ] **Cursor-position insertion vs end-of-draft insertion for Copilot snippets.** MVP1 may insert at end-of-draft rather than at cursor position. Deferred (non-blocking): refine after first drafter uses it on stage.

---

## Functional Requirements

- **Route.** `/workstreams/:workstreamId/tasks/:nodeId/draft` under React Router v6 in `frontend/src/app/routes.tsx`. Example concrete URL: `/workstreams/operational-resilience/tasks/opres-pd-v0-3/draft`.
- **Left panel default tab.** `reviewed`. Tab order: `reviewed` → `related` → `copilot`. Tab state lives in local component state on `SidePanelTabs`; switching tabs does not unmount the editor pane.
- **Reviewed tab source.** Pulls findings across all edges incident to the task node where `review_state == "accepted"`. Server-side aggregation across all findings files associated with edges that touch `nodeId`.
- **Related · 1 hop tab source.** Pulls findings on edges between the task's neighbour nodes themselves (excluding edges that touch the task). Requires 1-hop graph traversal server-side: enumerate `neighbours(task)`, then enumerate edges whose both endpoints are in `neighbours(task)`, then return findings on those edges.
- **Copilot tab behaviour.** Renders a fake chat history seeded from a scripted conversation, plus a live input. When the user hits Send, the frontend calls `POST /api/workstreams/{ws}/tasks/{node_id}/copilot` with the current `intent` preset and `message`; the server returns a scripted reply drawn from a hard-coded map keyed on `intent`. No live LLM call. The user's typed message is echoed back in the chat history right-aligned; the scripted reply appears left-aligned.
- **Editor.** `contentEditable` div styled as a Word-like page (serif face, page-width max, drop shadow). Toolbar buttons (Bold / Italic / Underline / Heading / List) hook to `document.execCommand` for MVP1 — deprecated but adequate for demo purposes.
- **Auto-save indicator.** Updates every 12s via `setInterval` in a `useEffect` on `EditorPane`. Copy: `"Auto-saved {N}s ago"` where `N` counts up from 0 and resets on every successful PUT to the draft endpoint.
- **Inline finding callouts.** Coloured left-border divs anchored to clauses in the draft. Colour map matches the review-linkages spec: emerald for `aligns-with`, indigo for `differs-on`, red for `conflicts-with`, sky for `goes-beyond`. `silent-on` findings render no inline callout.
- **Intent preset.** Stored in local component state on `CopilotTab`. Passed to `POST /copilot` on Send. Changing the preset resets the local `messages` array so the chat visibly restarts.
- **Breadcrumb.** `"← Workstream graph"` links back to `/workstreams/:workstreamId`.

## Permissions & Security

- Internal only, no auth in MVP1. Requests are unauthenticated on the local demo host.
- Input sanitization on `contentEditable` before persisting: strip `<script>` tags, inline event handlers (`on*` attributes), and `javascript:` URLs. Frontend uses `dompurify`; backend re-runs `bleach` on receipt so no client can bypass sanitization by hitting the API directly.

## API Design (extend `engine/api.py`)

All endpoints are additions to the existing FastAPI app in `engine/api.py`. Responses are `application/json`.

### GET `/api/workstreams/{workstream_id}/tasks/{node_id}/reviewed-linkages`

Returns accepted findings across all edges incident to the task node.

Response:

```json
{
  "findings": [
    {
      "id": "f-opres-rmit-1",
      "label": "conflicts-with",
      "sentiment": null,
      "summary": "Anchor to superseded RMiT version",
      "neighbour": {
        "node_id": "rmit-pd-2025",
        "title": "RMiT PD (28 Nov 2025)"
      },
      "source_clause_number": "7.1",
      "target_clause_number": "front-matter"
    },
    {
      "id": "f-opres-hkma-1",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "Annual vs biennial scenario testing",
      "neighbour": { "node_id": "hkma-spm-or2", "title": "HKMA SPM OR-2" },
      "source_clause_number": "5.3",
      "target_clause_number": "5.2"
    },
    {
      "id": "f-opres-rmit-2",
      "label": "goes-beyond",
      "sentiment": null,
      "summary": "Single accountable officer expansion",
      "neighbour": {
        "node_id": "rmit-pd-2025",
        "title": "RMiT PD (28 Nov 2025)"
      },
      "source_clause_number": "6.3",
      "target_clause_number": null
    }
  ]
}
```

### GET `/api/workstreams/{workstream_id}/tasks/{node_id}/related-linkages?hops=1`

Returns findings on edges between the task's neighbours (excluding edges touching the task).

Response:

```json
{
  "findings": [
    {
      "id": "f-bcbs-hkma-1",
      "label": "aligns-with",
      "sentiment": null,
      "summary": "HKMA implements BCBS OpRes Principle 6 verbatim",
      "left": { "node_id": "bcbs-opres-2021", "title": "BCBS Op. Res. 2021" },
      "right": { "node_id": "hkma-spm-or2", "title": "HKMA SPM OR-2" }
    },
    {
      "id": "f-fsb-bcbs-1",
      "label": "aligns-with",
      "sentiment": null,
      "summary": "FSB toolkit references BCBS OpRes 2021 explicitly",
      "left": { "node_id": "fsb-toolkit-2020", "title": "FSB Toolkit 2020" },
      "right": { "node_id": "bcbs-opres-2021", "title": "BCBS Op. Res. 2021" }
    },
    {
      "id": "f-hkma-fsb-1",
      "label": "differs-on",
      "sentiment": "neutral",
      "summary": "HKMA scoping narrower than FSB toolkit",
      "left": { "node_id": "hkma-spm-or2", "title": "HKMA SPM OR-2" },
      "right": { "node_id": "fsb-toolkit-2020", "title": "FSB Toolkit 2020" }
    }
  ]
}
```

### GET `/api/workstreams/{workstream_id}/tasks/{node_id}/draft`

Returns the current draft HTML.

Response:

```json
{
  "node_id": "opres-pd-v0-3",
  "content_html": "<h1>Operational Resilience</h1><p><strong>1.1</strong> This policy document sets out the requirements for licensed banks to build operational resilience...</p><p><strong>5.3</strong> Scenario testing shall be conducted at least annually...</p><p><strong>6.3</strong> The financial institution shall designate a single accountable officer...</p>",
  "last_saved_at": "2026-07-13T14:30:00Z"
}
```

### PUT `/api/workstreams/{workstream_id}/tasks/{node_id}/draft`

Body:

```json
{ "content_html": "<h1>Operational Resilience</h1><p>...</p>" }
```

Sanitizes with `bleach` (allowlist: `h1`, `h2`, `h3`, `p`, `strong`, `em`, `u`, `ul`, `ol`, `li`, `div`, `span`), then writes to `data/workstreams/{workstream_id}/drafts/{node_id}.json`. Returns the same shape as GET.

### POST `/api/workstreams/{workstream_id}/tasks/{node_id}/copilot`

Body:

```json
{
  "intent": "PD",
  "message": "Yes — keep it neutral for the transposition of BCBS Principle 7, and cross-reference RMiT §17.1"
}
```

`intent` must be one of: `PD`, `DP`, `ED`, `FAQ`, `Engagement Deck`, `Feedback Template for Industry`, `Peer Benchmarking`.

Response:

```json
{
  "reply": {
    "role": "copilot",
    "text": "Here is a neutral §6.3 preamble grounded in RMiT §17.1 and BCBS Principle 7...",
    "snippet_html": "<div class='copilot-snippet'><p><strong>6.3 Accountable officer.</strong> The financial institution shall designate a single accountable officer for operational resilience, reporting directly to the CEO...</p></div>"
  }
}
```

No LLM call. The server looks up `intent` in `COPILOT_SCRIPTS` (see Data Model) and returns the next scripted reply.

### Error table

| Status | Code                   | Condition                                                                    |
| ------ | ---------------------- | ---------------------------------------------------------------------------- |
| 404    | `TASK_NOT_FOUND`       | `node_id` does not resolve to a task-typed node in the workstream            |
| 400    | `HOPS_OUT_OF_RANGE`    | `hops` query param is anything other than `1`                                |
| 400    | `INVALID_INTENT`       | `intent` is not one of the 7 allowed presets                                 |
| 413    | `DRAFT_TOO_LARGE`      | `content_html` exceeds 200 KB after sanitization                             |
| 400    | `INVALID_HTML`         | Sanitizer rejected the input entirely (empty result or all content stripped) |
| 404    | `WORKSTREAM_NOT_FOUND` | `workstream_id` is not present under `data/workstreams/`                     |

## Data Model

### Draft state

`data/workstreams/{workstream_id}/drafts/{node_id}.json`:

```json
{
  "node_id": "opres-pd-v0-3",
  "content_html": "<h1>Operational Resilience</h1><p><strong>1.1</strong> This policy document sets out the requirements for licensed banks to build operational resilience.</p><p><strong>5.3</strong> Scenario testing shall be conducted at least annually.</p><p><strong>6.3</strong> The financial institution shall designate a single accountable officer.</p>",
  "last_saved_at": "2026-07-13T14:30:00Z"
}
```

### Copilot script map

Server-side constant at `engine/copilot_scripts.py`:

```python
COPILOT_SCRIPTS: dict[str, list[dict]] = {
    "PD": [
        {
            "role": "copilot",
            "text": (
                "Hi Aisyah — I've loaded 4 accepted linkages and the OpRes DP feedback "
                "register. Want me to draft the §6.3 preamble that flags the "
                "accountable-officer expansion (goes-beyond RMiT)?"
            ),
        },
        {
            "role": "copilot",
            "text": "Here is a neutral §6.3 preamble grounded in RMiT §17.1 and BCBS Principle 7.",
            "snippet_html": (
                "<div class='copilot-snippet'>"
                "<p><strong>6.3 Accountable officer.</strong> The financial institution "
                "shall designate a single accountable officer for operational resilience, "
                "reporting directly to the CEO. This requirement extends the technology-risk "
                "accountability framework set out in RMiT §17.1 to the full operational "
                "resilience domain, and is consistent with the governance expectation in "
                "BCBS Principle 7.</p>"
                "</div>"
            ),
        },
    ],
    "DP": [
        {
            "role": "copilot",
            "text": (
                "Discussion Paper mode. I can draft the question set for §5.3 "
                "(scenario testing cadence) framed against the HKMA biennial baseline. "
                "Ready when you are."
            ),
        },
    ],
    "ED": [
        {
            "role": "copilot",
            "text": (
                "Exposure Draft mode. I'll keep the tone consultative and cite the "
                "differs-on tighten finding on §5.3 so respondents see the rationale."
            ),
        },
    ],
    "FAQ": [
        {
            "role": "copilot",
            "text": (
                "FAQ mode. Suggested question: 'Does §6.3 replace or supplement the "
                "RMiT technology-risk accountable officer?' — answer verbatim from "
                "RMiT §17.1."
            ),
        },
    ],
    "Engagement Deck": [
        {"role": "copilot", "text": "Engagement deck mode. Want a 3-slide skeleton for the ABM briefing?"},
    ],
    "Feedback Template for Industry": [
        {"role": "copilot", "text": "Feedback template mode. I can prep the response grid keyed on §5.3 and §6.3."},
    ],
    "Peer Benchmarking": [
        {
            "role": "copilot",
            "text": (
                "Peer benchmarking mode. Loaded HKMA SPM OR-2, MAS TRM, and APRA CPS 230 "
                "on the scenario-testing cadence question."
            ),
        },
    ],
}
```

## UI / Frontend Requirements

Components live under `frontend/src/features/drafting-workspace/`:

- `DraftingWorkspacePage.tsx` — page route. 12-column CSS grid: 5 cols left (`SidePanelTabs`), 7 cols right (`EditorPane`). Renders breadcrumb, auto-save indicator, and workstream/task title header.
- `SidePanelTabs.tsx` — shadcn `Tabs` with 3 tab triggers: `Reviewed`, `Related · 1 hop`, `Copilot`. Count badges on the first two.
- `ReviewedTab.tsx` — list of `LinkageRefCard` components fed from the `reviewed-linkages` query.
- `RelatedTab.tsx` — banner explainer ("These are linkages between your task's neighbour documents, useful when your draft is silent on a concept") + list of neighbour-pair `LinkageRefCard`s fed from the `related-linkages` query.
- `CopilotTab.tsx` — intent preset shadcn `Select` (7 options), scrollable message list using `ScrollArea`, sticky `Input` + Send `Button` at the bottom.
- `LinkageRefCard.tsx` — shadcn `Card` with a label `Badge` (colour by semantic label), optional sentiment `Badge`, one-line summary, and neighbour reference.
- `EditorPane.tsx` — `contentEditable` div wrapped in a page-like frame. Fake toolbar as a `Button` group above. Auto-save indicator uses `useEffect` + `setInterval(12_000)` to increment the "N seconds ago" counter; the PUT is triggered via a debounced `useMutation`.

### State

- **TanStack Query keys:**
  - `['reviewed-linkages', workstreamId, nodeId]` → GET reviewed-linkages
  - `['related-linkages', workstreamId, nodeId]` → GET related-linkages
  - `['draft', workstreamId, nodeId]` → GET draft
- **Copilot messages:** local component state (`useState<Message[]>`) inside `CopilotTab`. Resets on intent-preset change and on tab switch (component unmounts when the tab is not active).
- **Draft auto-save:** debounced `useMutation` with 2000 ms trailing delay. On success, resets the "seconds ago" counter to 0.

### Styling

- Semantic label colour map identical to `spec-review-linkages.md`:
  - `aligns-with` → emerald
  - `differs-on` → indigo
  - `conflicts-with` → red
  - `goes-beyond` → sky
  - `silent-on` → slate
- Editor typography: `font-family: Georgia, 'Times New Roman', serif;` inside the editor surface; UI chrome stays in the app sans-serif.
- Inline callout divs anchored beside referenced clauses with a 4px coloured left border matching label colour, and a small pill showing the neighbour anchor short-name.
- Copilot-inserted snippet: indigo 4px left border with a small "Copilot" tag pill in the top-right corner.

## Architecture Notes

- Reuses shadcn primitives already in the frontend: `Tabs`, `Card`, `Badge`, `Button`, `Select`, `Separator`, `ScrollArea`, `Input`.
- **New dependency (frontend):** `dompurify` for sanitizing `contentEditable` HTML before PUT.
- **New dependency (backend):** `bleach` for server-side HTML sanitization on the PUT draft endpoint. Added to `pyproject.toml`.
- **Integration points:**
  - `engine/api.py` — add the four new endpoints alongside existing routes.
  - `engine/copilot_scripts.py` — new file, module-level `COPILOT_SCRIPTS` constant.
  - `engine/traversal.py` — new helper module (if not already present) with `neighbours(node_id)` and `edges_between(node_ids)` functions used by the related-linkages endpoint.
- Reuses the findings JSON shape defined in `spec-review-linkages.md` — same file layout, same fields.

## Exemplar Files

- `engine/api.py` — existing FastAPI route pattern to mirror for the four new endpoints.
- `docs/specs/workstream-brain/spec-review-linkages.md` — findings JSON format reference.
- `docs/poc/workstream-brain/drafting.html` — visual reference for the 12-col grid, callout styling, and Copilot chat layout.

## Implementation Plan

- **Task 1 (small, INDEPENDENT):** Scaffold `engine/copilot_scripts.py` with the 7-preset scripted conversation map. Content drawn from the POC drafting page. Ships behind the API endpoint added in Task 2.
- **Task 2 (medium, INDEPENDENT of frontend):** FastAPI endpoints for `reviewed-linkages`, `related-linkages` (with `hops=1` gate), draft `GET`/`PUT`, and `copilot` `POST`. Add `bleach` to `pyproject.toml`. Include all error codes from the error table.
- **Task 3 (medium, SEQUENTIAL after review-linkages story Task 2):** Reviewed-linkages endpoint filters `findings.json` files by `review_state == "accepted"` across incident edges. Uses graph traversal helper in `engine/traversal.py` (new file) exposing `neighbours(node_id)` and `edges_between(node_ids)`.
- **Task 4 (medium, SEQUENTIAL after workstream-graph Task 1):** Scaffold `DraftingWorkspacePage` with 12-col grid, breadcrumb link back to workstream graph, and auto-save indicator wired to the 12s `setInterval`. Route registration in `frontend/src/app/routes.tsx`.
- **Task 5 (medium, SEQUENTIAL after Task 4):** Build `SidePanelTabs` with `Reviewed` and `Related · 1 hop` tabs and `LinkageRefCard`. Wire TanStack Query hooks.
- **Task 6 (medium, SEQUENTIAL after Task 4):** Build `CopilotTab` with intent preset dropdown, scripted-reply POST wiring, and echoed user messages.
- **Task 7 (small, SEQUENTIAL after Task 4):** `EditorPane` `contentEditable` div with fake toolbar, `document.execCommand` hooks, `dompurify` sanitizer, and 12s auto-save loop.
- **Task 8 (small, SEQUENTIAL after Task 5 and Task 7):** Inline finding callouts anchored beside referenced clauses in the editor, colour-coded by semantic label.

## Negative Constraints

- Do **not** call a real LLM for Copilot in MVP1. Scripted responses only.
- Do **not** embed Microsoft Office or a real document editor. `contentEditable` div only.
- Do **not** persist Copilot chat history across sessions in MVP1.
- Do **not** let the intent preset condition Copilot behaviour beyond keying into the scripted map.
- Do **not** support 2-hop or greater traversal in the Related tab. Fixed at 1 hop; return `HOPS_OUT_OF_RANGE` for any other value.
- Do **not** filter findings on the Reviewed tab client-side — they are pre-filtered to accepted on the server.
- Do **not** commit any real BNM policy text under `data/workstreams/` that came from `docs/references/`. Draft fixtures are synthesised paraphrases only.

## Test Scenarios (implementation-level)

Backend (pytest under `engine/tests/`):

- `test_GET_reviewed_linkages_returns_only_accepted_findings_across_incident_edges`
- `test_GET_reviewed_linkages_404_TASK_NOT_FOUND_when_node_is_not_a_task`
- `test_GET_related_linkages_hops_1_excludes_edges_touching_task`
- `test_GET_related_linkages_hops_2_returns_400_HOPS_OUT_OF_RANGE`
- `test_PUT_draft_sanitizes_script_tags`
- `test_PUT_draft_strips_inline_event_handlers`
- `test_PUT_draft_413_when_content_over_200kb`
- `test_PUT_draft_400_INVALID_HTML_when_sanitizer_returns_empty`
- `test_POST_copilot_returns_scripted_reply_for_PD_intent`
- `test_POST_copilot_400_INVALID_INTENT_when_intent_not_in_seven_presets`
- `test_GET_draft_returns_last_saved_content_and_timestamp`

Frontend (vitest + React Testing Library under `frontend/src/features/drafting-workspace/__tests__/`):

- Switching tabs preserves editor content (editor pane must not unmount on tab switch).
- Intent preset change resets Copilot messages to the seeded conversation for the new preset.
- Auto-save mutation fires 2 seconds after the last keystroke stops (debounce test).
- Copilot Send call includes the currently selected intent in the request body.
- `LinkageRefCard` renders the sentiment badge only for `differs-on` findings.

## Verification

- **Backend:** `pytest engine/tests/test_api.py -k drafting -v`.
- **Frontend unit:** `cd frontend && npm run test`.
- **E2E:** `frontend/e2e/drafting-workspace.spec.ts` — script: "land on OpRes PD v0.3 draft, assert 4 reviewed linkages visible, switch to Related · 1 hop and assert 5 cards, switch to Copilot, pick PD intent, type a message, assert scripted reply appears with Insert into draft button". Assigned to Task 5's exit criteria.
