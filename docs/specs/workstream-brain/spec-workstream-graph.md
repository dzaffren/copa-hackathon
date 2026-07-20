# Workstream Graph Screen

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)

**Ticket:** TBD

The workstream graph is the drafter's home screen. It shows every document their
workstream depends on as a node on a canvas, with structural edges connecting
them. Clicking any node opens a detail panel with neighbours, activity, and an
action to open the underlying task or source. Clicking any edge opens an edge
detail panel that either invites the user to analyse the pair or lists the
findings already discovered. A collapsible sidebar lists every workstream the
user belongs to. This is the hero screen — the drafter enters here, adds new
anchors here, and navigates from here into every other screen in the product.

## User Story

As Aisyah R., a policy drafter in the Prudential Policy Department who owns the
Operational Resilience Policy Document v0.3, I want to see every document my
workstream depends on and how they connect on a single canvas, so that I can
navigate to any anchor, task, or finding without hunting through email,
SharePoint folders, or my own memory.

## Background & Context

**Current state:**

- Drafters keep a mental list of the international standards, peer-regulator
  publications, statutes, and industry submissions that anchor their working
  draft. That list lives in the drafter's head, or a personal spreadsheet.
- To find how a peer regulator handled a topic Aisyah is drafting, she opens
  SharePoint, searches for a peer document, opens it, and reads.
- To remember which BCBS principle her draft is adapting, she opens the BCBS
  PDF and Ctrl-Fs.

**Problem:**

- The workstream has no single home. Anchors live scattered across shared
  drives, email attachments, and personal notes.
- When a drafter rotates out, their mental map of "which docs matter and how
  they relate" leaves with them.
- Adding a newly-published peer anchor (e.g. HKMA SPM OR-2 landing mid-cycle)
  has no lightweight capture path — it becomes a folder in SharePoint that no
  one else sees.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, Prudential Policy Department, BNM. Owns
  the Operational Resilience PD v0.3. Reviews the Outsourcing PD v2 draft.
- **Context:** Aisyah opens the tool at the start of the drafting day, at
  hand-off moments between clauses, and whenever a new peer or international
  publication lands that she needs to consider. She wants to orient herself in
  under thirty seconds.
- **Current workaround:** A personal spreadsheet listing anchor documents with
  links to SharePoint copies. No visibility into relationships between anchors,
  and no shared version with reviewers.

## Goals

- Give the drafter a single canvas that answers "what does this workstream
  depend on, and how do those things connect?"
- Make adding a new anchor a thirty-second capture — pick a source, pick a
  type, declare at least one relationship, done.
- Serve as the launch pad into every other screen: the task screen for editable
  drafts, the review screen for findings, and the new-workstream form.

## Non-Goals

- Editing the draft directly on this screen. Task nodes navigate to the task
  screen; the drafting workspace opens from there.
- Showing semantic linkage labels (aligns-with, differs-on, conflicts-with,
  silent-on, goes-beyond) on graph edges. Semantic labels live on findings
  inside the edge detail panel, only after the pair has been analysed.
- Extracting or displaying concept content. The Concepts disclosure inside the
  node detail panel shows placeholder content only; the extraction pipeline is
  out of scope for this epic.
- Building the institution map. The sidebar link renders and navigates, but the
  destination screen is a separate epic.
- Second-order neighbours in the node detail panel — the section renders with
  a "N/A in demo" placeholder.

## User Workflow

1. **Landing** — Aisyah opens the tool and lands on her Operational Resilience
   workstream. The canvas shows her working draft in the centre and six anchor
   documents arranged around it. The left sidebar lists the three workstreams
   she belongs to.
2. **Orient** — She reads the coloured legend, recognises the peer-regulator
   node for HKMA SPM OR-2, the international-standard node for BCBS OpRes
   Principles 2021, and the internal-published node for RMiT PD 28 Nov 2025.
3. **Inspect a node** — She clicks her PD v0.3 node. A detail panel opens on
   the right with type badge, title, description, a list of first-order
   neighbours as coloured chips, recent activity, a collapsed Concepts
   disclosure, and an **Open task** button.
4. **Inspect an edge** — She clicks the edge between her PD and HKMA SPM OR-2.
   The panel switches to edge detail, shows a "not analysed" status badge, and
   presents an **Analyze linkages** call-to-action with no summary content.
5. **Add a new anchor** — A colleague forwards her the FSB Third-Party Toolkit
   PDF. She clicks **+ Add node**, uploads the PDF, picks
   `international-standard`, declares one edge (`contributes-to` from FSB to
   her PD), and clicks **Add to graph**. The new node appears on canvas
   connected to her PD.
6. **Navigate onward** — Back on the PD node, she clicks **Open task**. She
   leaves the graph screen for the task screen. Alternatively, she clicks a
   first-order neighbour chip and the panel refocuses on that neighbour.
7. **Move between workstreams** — From the sidebar, she clicks the Outsourcing
   v2 workstream and lands on its graph. She collapses the sidebar to a
   thin rail to reclaim canvas space, then expands it again.

## Acceptance Criteria

### Scenario: Aisyah opens her pre-seeded workstream

```gherkin
Given Aisyah R. is signed in
  And her Operational Resilience v0.3 workstream is pre-seeded with the following documents
    | Node title                        | Node type              | Structural edge to PD v0.3 |
    | Operational Resilience PD v0.3    | task                   | (this is the source node)  |
    | BCBS OpRes Principles 2021        | international-standard | contributes-to             |
    | HKMA SPM OR-2                     | peer-regulator         | contributes-to             |
    | FSB Third-Party Toolkit           | international-standard | contributes-to             |
    | RMiT PD 28 Nov 2025               | internal-published     | parallel-to                |
    | Financial Services Act 2013 §143  | act-law                | references                 |
    | ABM Position Paper on Op Res      | industry-input         | contributes-to             |
  And she belongs to three workstreams: Operational Resilience v0.3, Outsourcing v2, RMiT v2 (delivered)
When she opens the tool and lands on the Operational Resilience workstream
Then she sees a canvas with 7 nodes coloured by their type per the legend
  And she sees 6 structural edges connecting the 6 anchors to the PD v0.3 node
  And she sees no semantic labels on any edge
  And she sees a left sidebar listing all 3 workstreams with role badges (own, review, delivered)
  And she sees a `+ New workstream` action and an `Institution map` link in the sidebar
```

### Scenario: Aisyah clicks the task node and sees its detail panel

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
When she clicks the Operational Resilience PD v0.3 node
Then a NODE DETAIL panel opens on the right
  And the header shows a `task` type badge, a sub-badge with issuer and short type, the title "Operational Resilience PD v0.3", and a one-line description
  And she sees a First-order neighbours section with 6 clickable chips, each coloured by the neighbour's node type
  And she sees a Second-order neighbours section with the placeholder "N/A in demo"
  And she sees a Recent activity list with edit and comment entries showing author and timestamp
  And she sees a Concepts disclosure collapsed by default
  And she sees an **Open task** action button at the bottom of the panel
```

### Scenario: Aisyah clicks a resource node and sees its detail panel

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
When she clicks the BCBS OpRes Principles 2021 node
Then a NODE DETAIL panel opens on the right
  And the header shows an `international-standard` type badge, a sub-badge, the title, and a one-line description
  And the First-order neighbours section lists the PD v0.3 node as a chip
  And the action button at the bottom reads **Open source** (not **Open task**)
```

### Scenario: Aisyah clicks a first-order neighbour chip to switch focus

```gherkin
Given the NODE DETAIL panel is showing the Operational Resilience PD v0.3 node
When Aisyah clicks the HKMA SPM OR-2 chip in the First-order neighbours section
Then the panel refocuses on the HKMA SPM OR-2 node
  And the panel header, description, neighbours, activity, and action button all update to reflect HKMA SPM OR-2
  And the action button reads **Open source**
```

### Scenario: Aisyah clicks an unanalysed edge

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
  And the edge between the PD v0.3 node and the HKMA SPM OR-2 node has never been analysed
When she clicks that edge
Then an EDGE DETAIL panel opens on the right
  And the header shows a `contributes-to` structural edge badge
  And the header shows a status badge reading "not analysed"
  And the header shows a pair title in the form "Operational Resilience PD v0.3 ↔ HKMA SPM OR-2"
  And she sees an **Analyze linkages** call-to-action
  And she sees no finding cards, no summary, and no clause content
```

### Scenario: Aisyah clicks an already-analysed edge

```gherkin
Given the edge between the PD v0.3 node and the BCBS OpRes Principles 2021 node has already been analysed
  And the analysis produced the following findings
    | Semantic label   | One-line summary                                                       |
    | aligns-with      | We adopt BCBS Principle 3 on governance verbatim                       |
    | differs-on       | We set scenario-testing cadence at 6 months; BCBS says "regular"       |
    | silent-on        | BCBS covers third-party concentration; our PD does not yet             |
When Aisyah clicks that edge
Then an EDGE DETAIL panel opens on the right
  And the header status badge reads "3 linkage(s)"
  And she sees 3 finding cards
  And each finding card shows a semantic label pill and its one-line summary
  And each finding card has a **Review** button that navigates to the review linkages screen for that pair
  And she sees no **Analyze linkages** call-to-action (the pair has already been analysed)
```

### Scenario: Aisyah adds a new anchor with one edge to her PD

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
When she clicks **+ Add node**
  And she uploads a PDF titled "BCBS OpRes 2021 Companion Guide"
  And she picks the node type `international-standard`
  And she adds one edge with target "Operational Resilience PD v0.3" and edge type `contributes-to`
  And she clicks **Add to graph**
Then the modal closes
  And the new node appears on the canvas coloured as an international-standard
  And a new `contributes-to` structural edge appears between the new node and the PD v0.3 node
  And the detail panel resets to empty
```

### Scenario: Aisyah tries to add a node without declaring an edge

```gherkin
Given Aisyah has opened the add-node modal
  And she has uploaded a source and picked a node type
  And the Edges section has zero rows
When she attempts to complete the add
Then the **Add to graph** action does not complete
  And she sees a message that at least one edge to an existing node is required
  And the modal remains open
```

### Scenario: Aisyah adds multiple edges to a new node

```gherkin
Given Aisyah has opened the add-node modal
  And she has uploaded a source and picked node type `peer-regulator`
When she adds a first edge with target "Operational Resilience PD v0.3" and edge type `contributes-to`
  And she adds a second edge with target "RMiT PD 28 Nov 2025" and edge type `parallel-to`
  And she clicks **Add to graph**
Then the new node appears on the canvas
  And two structural edges appear from the new node — one `contributes-to` the PD v0.3, one `parallel-to` the RMiT PD
```

### Scenario: Aisyah removes an edge row before submitting

```gherkin
Given Aisyah has opened the add-node modal
  And she has added two edge rows
When she clicks the delete X on the second edge row
Then the second edge row is removed
  And only the first edge row remains
  And **Add to graph** remains available because at least one edge is still declared
```

### Scenario: Aisyah adds a linkage between two existing nodes from the node detail panel

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
  And the NODE DETAIL panel is showing the HKMA SPM OR-2 node
When she clicks the **+ Add linkage** button in the node detail panel
Then an ADD LINKAGE dialog opens
  And the dialog header reads "Add linkage from HKMA SPM OR-2"
  And she sees a `Target node` select populated with every other node on the workstream except HKMA SPM OR-2
  And she sees an `Edge type` select populated with the four structural types (`supersedes`, `references`, `contributes-to`, `parallel-to`)
When she picks target "BCBS OpRes Principles 2021" and edge type `contributes-to`
  And she clicks **Add linkage**
Then the dialog closes
  And a new `contributes-to` structural edge appears on the canvas between HKMA SPM OR-2 and BCBS OpRes Principles 2021
  And the edge status is "not analysed"
  And the NODE DETAIL panel refreshes to include BCBS OpRes Principles 2021 in the First-order neighbours section
```

### Scenario: Aisyah cannot create a self-edge

```gherkin
Given the ADD LINKAGE dialog is open with source "HKMA SPM OR-2"
When Aisyah opens the `Target node` select
Then HKMA SPM OR-2 is not present in the list of target options
  And she cannot pick her own node as the target
```

### Scenario: Aisyah cannot duplicate an existing linkage

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
  And a `contributes-to` edge already exists between HKMA SPM OR-2 and the Operational Resilience PD v0.3 node
When Aisyah opens the ADD LINKAGE dialog from HKMA SPM OR-2
  And she picks target "Operational Resilience PD v0.3" and edge type `contributes-to`
  And she clicks **Add linkage**
Then the tool rejects the submission with a "linkage already exists" message
  And no duplicate edge appears on the canvas
```

### Scenario Outline: Aisyah zooms the canvas

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph at the default zoom level
When she clicks the <control> control
Then the canvas <effect>

Examples:
  | control    | effect                                                        |
  | zoom in    | scales up so nodes appear larger and the canvas shows less    |
  | zoom out   | scales down so nodes appear smaller and the canvas shows more |
  | reset zoom | returns to the default zoom level and default centre          |
```

### Scenario: Aisyah collapses the sidebar

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
  And the sidebar is expanded, listing three workstream names with role badges
When she clicks the collapse control
Then the sidebar collapses to an icon-only rail
  And the workstream names, `+ New workstream` label, and `Institution map` label are hidden
  And workstream, add, and institution icons remain visible and clickable
```

### Scenario: Aisyah expands the sidebar back

```gherkin
Given the sidebar is collapsed to an icon-only rail
When Aisyah clicks the expand control
Then the sidebar expands to full width
  And all three workstream names, role badges, `+ New workstream` label, and `Institution map` label are shown
```

### Scenario: Aisyah opens the new-workstream screen from the sidebar

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
When she clicks `+ New workstream` in the sidebar
Then she navigates to the new-workstream screen
```

### Scenario: Aisyah clicks the Institution map link

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
When she clicks the `Institution map` link at the bottom of the sidebar
Then she navigates to the institution map screen
```

### Scenario: Aisyah opens the task screen from a task node

```gherkin
Given the NODE DETAIL panel is showing the Operational Resilience PD v0.3 node
When Aisyah clicks the **Open task** action button
Then she navigates to the task screen for the Operational Resilience PD v0.3 task
```

### Scenario: Aisyah opens the source of a resource node

```gherkin
Given the NODE DETAIL panel is showing the BCBS OpRes Principles 2021 node
When Aisyah clicks the **Open source** action button
Then she is taken to the source document (attached file or external URL) for BCBS OpRes Principles 2021
```

### Scenario: Aisyah switches to a different workstream from the sidebar

```gherkin
Given Aisyah is on the Operational Resilience v0.3 workstream graph
When she clicks the Outsourcing v2 workstream in the sidebar
Then she navigates to the Outsourcing v2 workstream graph
  And the canvas re-renders with the Outsourcing v2 nodes and edges
  And her sidebar remains visible with Outsourcing v2 highlighted as the active workstream
```

### Scenario: Aisyah runs analysis on an unanalysed edge

```gherkin
Given the EDGE DETAIL panel is showing an unanalysed edge between the PD v0.3 node and the HKMA SPM OR-2 node
When Aisyah clicks **Analyze linkages**
Then the tool runs the linkage analysis for that pair
  And once analysis completes, the panel updates in place
  And the status badge changes from "not analysed" to a linkage count (e.g. "5 linkage(s)")
  And a list of finding cards appears, each with a semantic label pill, a one-line summary, and a **Review** button
  And the **Analyze linkages** call-to-action is no longer shown
```

## Business Rules & Constraints

- **One document, one node.** No clause-level nodes appear on the graph.
  Clause content surfaces only inside finding cards behind the edge detail
  panel.
- **Seven flat node types.** Every node is exactly one of: `task`,
  `internal-published`, `international-standard`, `peer-regulator`, `act-law`,
  `industry-input`, `others`. Type is picked once at add-time and cannot change.
- **Four structural edge types.** Every graph edge is exactly one of:
  `supersedes`, `references`, `contributes-to`, `parallel-to`.
- **Every new node requires at least one edge.** The add-node modal does not
  allow completion until at least one edge to an existing node is declared.
- **Structural edges on the graph, semantic labels on findings.** Semantic
  labels (aligns-with, differs-on, conflicts-with, silent-on, goes-beyond)
  never appear on graph edges. They only appear on finding cards inside the
  edge detail panel, and only after the pair has been analysed.
- **Task nodes open the task screen; resource nodes open the source.** The
  action button on a `task` node reads **Open task**; on the six resource
  types it reads **Open source**.
- **Verbatim citations only.** Any clause text that surfaces (e.g. inside
  finding cards on an analysed edge) must be quoted from the parsed clause
  index. If no clause supports a claim, the tool says "No matching clause
  found" — it never invents one.
- **Unanalysed edges show no summary.** The edge detail panel shows the
  **Analyze linkages** call-to-action and nothing else when the pair has never
  been analysed. Summary content only appears after analysis completes.
- **Second-order neighbours are deferred.** The node detail panel renders the
  section with a "N/A in demo" placeholder until v2 corpus expansion.
- **Concepts disclosure is a placeholder.** The disclosure renders collapsed
  and its expanded content is a stub — the extraction pipeline is not built
  in this epic.

## Success Metrics

- **Aisyah reaches any anchor in three clicks or fewer** from landing on the
  workstream graph, without opening SharePoint or email.
- **A newly-published peer anchor is captured in under thirty seconds** —
  upload, pick type, declare one edge, add.
- **Zero fabricated clause references** appear on any edge detail finding
  card during the hackathon demo.
- **Every workstream member on the hackathon demo drives the full flow
  (landing → inspect node → inspect edge → add anchor → open task) without
  documentation** in under three minutes.

## Dependencies

- **Linkage taxonomy widening in the engine** — the semantic labels shown on
  finding cards inside the edge detail panel depend on the engine producing
  the five-label taxonomy.
- **Pre-seeded Operational Resilience v0.3 workstream** — the demo relies on
  seven pre-seeded nodes (PD v0.3, BCBS OpRes Principles 2021, HKMA SPM OR-2,
  FSB Third-Party Toolkit, RMiT PD 28 Nov 2025, FSA 2013 §143, ABM position
  paper) and six pre-seeded structural edges.
- **Retired experiment trace** — clicking **Analyze linkages** on the demo
  pair replays the retired trace rather than making a live model call.
- **Task screen, review linkages screen, new-workstream screen, institution
  map** — the graph is the launch pad; the action buttons and sidebar links
  navigate to these screens. Their content is scoped in their own stories.

## Open Questions

- [x] ~~Should semantic labels ever appear on the graph edges?~~
      **Resolved:** No. Structural edges on the graph, semantic labels on findings.
      Putting semantic labels on graph edges implies findings exist where none have
      been generated. Confirmed in the epic overview's shared business rules.
- [x] ~~Should the action button on a task node read "Edit in workspace"?~~
      **Resolved:** No. It reads **Open task** and navigates to the task screen.
      The drafting workspace opens from the task screen, not directly from the
      graph.
- [ ] Second-order neighbours in the node detail panel —
      **Deferred (non-blocking):** section renders with "N/A in demo" placeholder;
      enable after v2 corpus expansion. Does not block MVP1 demo.
- [ ] Concepts disclosure content —
      **Deferred (non-blocking):** section renders collapsed with placeholder
      content; the extraction pipeline is a separate deliverable outside this
      epic. Does not block MVP1 demo.

---

## Functional Requirements

- **Add-node modal requires at least one complete edge row.** The `Add to graph`
  submit button is disabled until the modal state contains at least one edge
  row where both `target_node_id` and `edge_type` are set. Removing rows below
  one disables the button again.
- **Node action button varies by node type.** If the loaded node's `type` is
  `task`, the detail panel renders an `Open task` button whose click navigates
  to `/workstreams/:workstreamId/tasks/:nodeId`. For any of the six resource
  types (`internal-published`, `international-standard`, `peer-regulator`,
  `act-law`, `industry-input`, `others`), it renders `Open source` whose click
  opens the node's attached file URL or external source URL in a new tab.
- **Edge detail panel branches on `analysed` flag.** When `analysed = false`,
  render the `Analyze linkages` call-to-action and no finding cards. When
  `analysed = true`, render a finding-count badge and one finding card per
  entry in the `findings` array.
- **Analyze linkages replays the retired trace for the demo pair.** For the
  edge whose two endpoints match the OpRes v0.3 draft and the Open Finance
  2025 Exposure Draft (in either direction), the analyze endpoint reads
  `data/artifacts/connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json`,
  waits an artificial 800ms, and returns the trace's findings. For any other
  pair, the endpoint calls the live finder-critic loop.
- **Second-order neighbours panel renders static placeholder.** The section
  always renders the text `N/A in demo` with no traversal call.
- **Concepts disclosure renders collapsed placeholder.** Expanding it shows a
  short placeholder paragraph, not extracted content.
- **Zoom is clamped between 0.5 and 2.5.** Zoom-in multiplies current scale by
  1.25; zoom-out multiplies by 0.8; reset returns to 1.0. Pan/drag is not
  supported.

## Permissions & Security

- **Scope:** internal-only, single-user demo. This story ships to the hackathon
  environment.
- **Authentication:** none in MVP1. All new endpoints under `/api/workstreams/**`
  are open on localhost.
- **Input validation:**
  - `node_type` must be one of the seven flat types.
  - `edge_type` must be one of the four structural types.
  - Uploaded attachments in the add-node flow are validated by the existing
    submission-ingest MIME allowlist (PDF, DOCX) — attachments outside this
    set are rejected before persistence.
- **File storage:** all workstream data persists under
  `data/workstreams/{workstream_id}/`. This directory is git-ignored to keep
  BNM internal document metadata out of the public repo.

## API Design (extend `engine/api.py`)

All new routes are added to the existing FastAPI app in
`engine/api.py` via `create_app`.
Persistence lives under `data/workstreams/`.

### `GET /api/workstreams`

Lists all workstreams for the sidebar.

**Response 200:**

```json
{
  "workstreams": [
    {
      "id": "opres-2026",
      "name": "Operational Resilience v0.3",
      "deliverable_type": "Policy Document",
      "role": "own"
    },
    {
      "id": "outsourcing-v2",
      "name": "Outsourcing v2",
      "deliverable_type": "Policy Document",
      "role": "review"
    },
    {
      "id": "rmit-v2-2025",
      "name": "RMiT v2 (delivered 28 Nov 2025)",
      "deliverable_type": "Policy Document",
      "role": "delivered"
    }
  ]
}
```

### `GET /api/workstreams/{workstream_id}/graph`

Returns nodes, edges, and per-edge analysed flags for canvas render.

**Response 200 for `opres-2026`:**

```json
{
  "workstream_id": "opres-2026",
  "nodes": [
    {
      "id": "opres-pd-v0-3",
      "type": "task",
      "title": "Operational Resilience PD v0.3",
      "issuer": "BNM",
      "short_type": "PD (draft)"
    },
    {
      "id": "bcbs-opres-2021",
      "type": "international-standard",
      "title": "BCBS OpRes Principles 2021",
      "issuer": "BCBS",
      "short_type": "Principles"
    },
    {
      "id": "hkma-spm-or-2",
      "type": "peer-regulator",
      "title": "HKMA SPM OR-2",
      "issuer": "HKMA",
      "short_type": "SPM"
    },
    {
      "id": "fsb-third-party-toolkit",
      "type": "international-standard",
      "title": "FSB Third-Party Toolkit",
      "issuer": "FSB",
      "short_type": "Toolkit"
    },
    {
      "id": "rmit-pd-2025-11-28",
      "type": "internal-published",
      "title": "RMiT PD 28 Nov 2025",
      "issuer": "BNM",
      "short_type": "PD (in force)"
    },
    {
      "id": "fsa-2013-s143",
      "type": "act-law",
      "title": "Financial Services Act 2013 §143",
      "issuer": "Parliament",
      "short_type": "Act"
    },
    {
      "id": "abm-position-opres",
      "type": "industry-input",
      "title": "ABM Position Paper on Op Res",
      "issuer": "ABM",
      "short_type": "Position paper"
    }
  ],
  "edges": [
    {
      "id": "e-bcbs--opres",
      "source": "bcbs-opres-2021",
      "target": "opres-pd-v0-3",
      "type": "contributes-to",
      "analysed": true,
      "finding_count": 3
    },
    {
      "id": "e-hkma--opres",
      "source": "hkma-spm-or-2",
      "target": "opres-pd-v0-3",
      "type": "contributes-to",
      "analysed": false,
      "finding_count": 0
    },
    {
      "id": "e-fsb--opres",
      "source": "fsb-third-party-toolkit",
      "target": "opres-pd-v0-3",
      "type": "contributes-to",
      "analysed": false,
      "finding_count": 0
    },
    {
      "id": "e-rmit--opres",
      "source": "rmit-pd-2025-11-28",
      "target": "opres-pd-v0-3",
      "type": "parallel-to",
      "analysed": false,
      "finding_count": 0
    },
    {
      "id": "e-fsa--opres",
      "source": "fsa-2013-s143",
      "target": "opres-pd-v0-3",
      "type": "references",
      "analysed": false,
      "finding_count": 0
    },
    {
      "id": "e-abm--opres",
      "source": "abm-position-opres",
      "target": "opres-pd-v0-3",
      "type": "contributes-to",
      "analysed": false,
      "finding_count": 0
    }
  ]
}
```

### `GET /api/workstreams/{workstream_id}/nodes/{node_id}`

Full node detail for the node detail panel.

**Response 200 for `opres-pd-v0-3`:**

```json
{
  "id": "opres-pd-v0-3",
  "type": "task",
  "title": "Operational Resilience PD v0.3",
  "issuer": "BNM",
  "short_type": "Policy Document (working draft)",
  "description": "BNM Prudential Policy Department working draft of the Operational Resilience Policy Document, v0.3 (17 Jun 2026).",
  "source_url": null,
  "first_order_neighbours": [
    {
      "id": "bcbs-opres-2021",
      "type": "international-standard",
      "title": "BCBS OpRes Principles 2021"
    },
    {
      "id": "hkma-spm-or-2",
      "type": "peer-regulator",
      "title": "HKMA SPM OR-2"
    },
    {
      "id": "fsb-third-party-toolkit",
      "type": "international-standard",
      "title": "FSB Third-Party Toolkit"
    },
    {
      "id": "rmit-pd-2025-11-28",
      "type": "internal-published",
      "title": "RMiT PD 28 Nov 2025"
    },
    {
      "id": "fsa-2013-s143",
      "type": "act-law",
      "title": "Financial Services Act 2013 §143"
    },
    {
      "id": "abm-position-opres",
      "type": "industry-input",
      "title": "ABM Position Paper on Op Res"
    }
  ],
  "second_order_neighbours": {
    "status": "placeholder",
    "message": "N/A in demo"
  },
  "recent_activity": [
    {
      "kind": "edit",
      "author": "Aisyah R.",
      "at": "2026-07-11T09:20:00+08:00",
      "summary": "Revised §5.3 scenario testing cadence"
    },
    {
      "kind": "comment",
      "author": "Farid M.",
      "at": "2026-07-10T16:42:00+08:00",
      "summary": "Suggested tightening §6.3 accountable officer language"
    }
  ],
  "concepts": {
    "status": "placeholder",
    "message": "Concept extraction not enabled in MVP1"
  }
}
```

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}`

Edge detail. Reads the on-disk `findings/{edge_id}.json` if present.

**Response 200 — unanalysed edge (`e-hkma--opres`):**

```json
{
  "id": "e-hkma--opres",
  "source": {
    "id": "hkma-spm-or-2",
    "title": "HKMA SPM OR-2",
    "type": "peer-regulator"
  },
  "target": {
    "id": "opres-pd-v0-3",
    "title": "Operational Resilience PD v0.3",
    "type": "task"
  },
  "edge_type": "contributes-to",
  "status": "not_analysed",
  "findings": []
}
```

**Response 200 — analysed edge (`e-bcbs--opres`):**

```json
{
  "id": "e-bcbs--opres",
  "source": {
    "id": "bcbs-opres-2021",
    "title": "BCBS OpRes Principles 2021",
    "type": "international-standard"
  },
  "target": {
    "id": "opres-pd-v0-3",
    "title": "Operational Resilience PD v0.3",
    "type": "task"
  },
  "edge_type": "contributes-to",
  "status": "analysed",
  "findings": [
    {
      "id": "f-1",
      "label": "aligns-with",
      "sentiment": null,
      "summary": "OpRes PD §4.4 operationalises BCBS Principle 7 on managing third-party dependencies without narrowing or widening it."
    },
    {
      "id": "f-2",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "OpRes PD §5.3 sets scenario-testing cadence at annually; BCBS Principle 5 states 'regular' without a fixed cadence."
    },
    {
      "id": "f-3",
      "label": "silent-on",
      "sentiment": null,
      "summary": "BCBS Principle 6 covers third-party concentration risk; OpRes PD v0.3 does not yet address concentration."
    }
  ]
}
```

### `POST /api/workstreams/{workstream_id}/nodes`

Creates a node. Body must include `edges` with at least one entry (server-side
enforcement of the same rule the modal enforces client-side).

**Request:**

```json
{
  "node_type": "international-standard",
  "title": "BCBS OpRes 2021 Companion Guide",
  "description": "BCBS supplementary companion to the 2021 Operational Resilience Principles",
  "source_url": null,
  "attachment_submission_id": "sub-9c1e",
  "edges": [
    { "target_node_id": "opres-pd-v0-3", "edge_type": "contributes-to" }
  ]
}
```

**Response 201:**

```json
{
  "id": "bcbs-companion-2021",
  "type": "international-standard",
  "title": "BCBS OpRes 2021 Companion Guide",
  "created_edges": [
    {
      "id": "e-bcbs-companion--opres",
      "source": "bcbs-companion-2021",
      "target": "opres-pd-v0-3",
      "type": "contributes-to",
      "analysed": false
    }
  ]
}
```

**Response 400 — empty edges list:**

```json
{
  "error": "EDGE_REQUIRED",
  "message": "At least one edge to an existing node is required to add a new node."
}
```

### `POST /api/workstreams/{workstream_id}/edges/{edge_id}/analyze`

Kicks off finder→critic on the pair.

**Request:** empty body.

**Response 200 for the demo pair (`opres-pd-v0-3` × `open-finance-ed-2025`) after 800ms:**

```json
{
  "id": "e-opres--openfinance",
  "status": "analysed",
  "findings": [
    {
      "id": "f-1",
      "label": "aligns-with",
      "sentiment": null,
      "summary": "Both drafts adopt BCBS Principle 3 on governance verbatim."
    },
    {
      "id": "f-2",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "OpRes PD §5.3 fixes scenario-testing cadence at annual; Open Finance ED §7.1 requires 'periodic' testing without cadence."
    },
    {
      "id": "f-3",
      "label": "conflicts-with",
      "sentiment": null,
      "summary": "OpRes PD §7.1 cites RMiT PD dated 1 June 2023, superseded by the 28 November 2025 reissue referenced by Open Finance ED."
    }
  ]
}
```

### `POST /api/workstreams/{workstream_id}/edges`

Creates a new structural edge between two existing nodes. Used by the "Add
linkage" affordance in the node detail panel — no file upload, no node
creation, just a new edge.

**Request:**

```json
{
  "source_node_id": "hkma-spm-or-2",
  "target_node_id": "bcbs-opres-2021",
  "edge_type": "contributes-to"
}
```

**Response 201:**

```json
{
  "id": "e-hkma--bcbs",
  "source": "hkma-spm-or-2",
  "target": "bcbs-opres-2021",
  "type": "contributes-to",
  "analysed": false,
  "finding_count": 0
}
```

**Response 400 — self-edge:**

```json
{
  "error": "SELF_EDGE_FORBIDDEN",
  "message": "source_node_id and target_node_id must differ."
}
```

**Response 409 — duplicate edge:**

```json
{
  "error": "EDGE_ALREADY_EXISTS",
  "message": "An edge of type 'contributes-to' already exists between 'hkma-spm-or-2' and 'bcbs-opres-2021'."
}
```

### Error table

| Status | Code                   | Condition                                                            |
| ------ | ---------------------- | -------------------------------------------------------------------- |
| 400    | `EDGE_REQUIRED`        | Node create body has zero edges                                      |
| 400    | `INVALID_NODE_TYPE`    | `node_type` not in the 7-flat set                                    |
| 400    | `INVALID_EDGE_TYPE`    | Any edge row's `edge_type` not in the 4-structural set               |
| 400    | `SELF_EDGE_FORBIDDEN`  | `POST /edges` with `source_node_id == target_node_id`                |
| 404    | `WORKSTREAM_NOT_FOUND` | `workstream_id` missing under `data/workstreams/`                    |
| 404    | `NODE_NOT_FOUND`       | `node_id` (source or target) not in the workstream's `graph.json`    |
| 404    | `EDGE_NOT_FOUND`       | `edge_id` not in the workstream's `graph.json`                       |
| 409    | `NODE_ORPHAN`          | Attempt to persist a node whose edges list is empty after validation |
| 409    | `EDGE_ALREADY_EXISTS`  | `POST /edges` with (source, target, edge_type) already present       |

## Data Model

Persistence root: `data/workstreams/`
(git-ignored).

### `data/workstreams/{workstream_id}/workstream.json`

```json
{
  "id": "opres-2026",
  "name": "Operational Resilience v0.3",
  "description": "BNM Prudential Policy Department Operational Resilience Policy Document, v0.3 (target ED Q4 2026).",
  "deliverable_type": "Policy Document",
  "target_publication": "2026-11-30",
  "owner": "Aisyah R.",
  "reviewers": ["Farid M."],
  "access": ["Aisyah R.", "Farid M."]
}
```

### `data/workstreams/{workstream_id}/graph.json`

```json
{
  "nodes": [
    {
      "id": "opres-pd-v0-3",
      "type": "task",
      "title": "Operational Resilience PD v0.3",
      "issuer": "BNM",
      "short_type": "Policy Document (working draft)",
      "description": "BNM Prudential Policy Department working draft of the Operational Resilience Policy Document, v0.3 (17 Jun 2026).",
      "source_url": null,
      "attachment_submission_id": null,
      "created_at": "2026-05-14T09:00:00+08:00"
    }
  ],
  "edges": [
    {
      "id": "e-bcbs--opres",
      "source": "bcbs-opres-2021",
      "target": "opres-pd-v0-3",
      "type": "contributes-to",
      "analysed": true,
      "created_at": "2026-05-14T09:00:00+08:00"
    }
  ]
}
```

### `data/workstreams/{workstream_id}/findings/{edge_id}.json`

The `Connection[]` array as produced by
`engine/connections.py`. Schema and
label vocabulary are owned by
[`spec-engine-taxonomy.md`](spec-engine-taxonomy.md).

## UI / Frontend Requirements

Components live under
`frontend/src/features/workstream-graph/`.

### Components

- `frontend/src/features/workstream-graph/WorkstreamGraphPage.tsx` — the page
  route `/workstreams/:workstreamId`. Owns TanStack Query for the graph, the
  right-panel state machine (idle / node-selected / edge-selected), and the
  Add-node dialog open state.
- `frontend/src/features/workstream-graph/GraphCanvas.tsx` — SVG-based canvas.
  Renders nodes as coloured circles keyed by node type, edges as lines keyed
  by structural type (line style only — no textual labels). Owns node/edge
  click handlers and zoom controls. Applies zoom via inline `transform:
scale(...)` on the SVG root.
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx` — shadcn `Card`
  header with `Badge` for node type and sub-type badge; description; chip row
  of first-order neighbours (each a shadcn `Badge` variant coloured by type);
  static "N/A in demo" second-order block; recent-activity list; `Collapsible`
  for the concepts placeholder; a bottom action `Button` reading `Open task`
  or `Open source` conditional on node type; and a `+ Add linkage`
  secondary `Button` that opens `AddLinkageDialog` pre-populated with the
  current node as source.
- `frontend/src/features/workstream-graph/AddLinkageDialog.tsx` — shadcn
  `Dialog` hosting a react-hook-form + zod form. Two fields: `Select` for
  `target_node_id` (options = every node in the workstream _except_ the
  source, sorted by title) and `Select` for `edge_type` (4 structural
  types). Submit `Button` reads `Add linkage` and is disabled until both
  selects have a value. On submit, POSTs `/api/workstreams/{ws}/edges` and
  invalidates the graph query on success. On 400 `SELF_EDGE_FORBIDDEN` or
  409 `EDGE_ALREADY_EXISTS`, renders an inline error message in the dialog
  without closing it.
- `frontend/src/features/workstream-graph/EdgeDetailPanel.tsx` — shadcn `Card`
  header with pair title and a status `Badge`. If `status = not_analysed`,
  renders a single `Button` reading `Analyze linkages`. If `status =
analysed`, renders one `Card` per finding with a semantic-label `Badge`, the
  one-line summary, and a `Review` button that navigates to
  `/workstreams/:workstreamId/edges/:edgeId/review`.
- `frontend/src/features/workstream-graph/AddNodeDialog.tsx` — shadcn `Dialog`
  hosting a react-hook-form + zod form. Fields: `Select` for `node_type` (7
  options), `Input` for title, `Textarea` for description, `Input` for source
  URL, file input for attachment. Below, an editable list of edge rows; each
  row is a `Select` for target node id + a `Select` for edge type + a delete
  X `Button`. The submit `Button` (`Add to graph`) is disabled while the edge
  rows list has zero complete rows.
- `frontend/src/features/workstream-graph/Sidebar.tsx` — shadcn `Sheet` on
  mobile, collapsible rail on desktop. Lists workstreams with role badges
  (`own`, `review`, `delivered`), a `+ New workstream` link, and an
  `Institution map` link. Owns collapsed/expanded state.

### Routes

- `/workstreams/:workstreamId` — this screen.
- `/workstreams/:workstreamId/tasks/:nodeId` — task screen (other story).
- `/workstreams/:workstreamId/edges/:edgeId/review` — review linkages screen
  (other story).
- `/workstreams/new` — new-workstream form (other story).
- `/institution-map` — placeholder route link (deferred epic).

### TanStack Query keys

- `['workstreams']` — the sidebar list.
- `['workstream', workstreamId, 'graph']` — canvas graph payload.
- `['node', workstreamId, nodeId]` — node detail panel.
- `['edge', workstreamId, edgeId]` — edge detail panel.

**Invalidation rules:**

- On successful `POST /api/workstreams/{workstream_id}/nodes`, invalidate
  `['workstream', workstreamId, 'graph']` so the canvas re-fetches and the
  new node appears.
- On successful `POST /api/workstreams/{workstream_id}/edges`, invalidate
  `['workstream', workstreamId, 'graph']` and `['node', workstreamId, sourceNodeId]`
  so the canvas re-renders with the new edge and the source node's
  first-order-neighbours list refreshes.
- On successful `POST /api/workstreams/{workstream_id}/edges/{edge_id}/analyze`,
  invalidate `['edge', workstreamId, edgeId]` so `EdgeDetailPanel` re-renders
  with the finding cards.

### Zoom controls

- `scale` state on `GraphCanvas`, initial value `1.0`, clamped `[0.5, 2.5]`.
- Zoom-in button: `scale = min(2.5, scale * 1.25)`.
- Zoom-out button: `scale = max(0.5, scale * 0.8)`.
- Reset button: `scale = 1.0`.
- Applied via inline `style={{ transform: 'scale(${scale})', transformOrigin:
'center center' }}` on the outer SVG group.

## Architecture Notes

- **New frontend dependencies:** `react`, `react-dom`, `react-router-dom`,
  `@tanstack/react-query`, `react-hook-form`, `zod`, `@hookform/resolvers`,
  `tailwindcss`, `class-variance-authority`, `clsx`, `tailwind-merge`,
  `lucide-react`. shadcn/ui initialised with `npx shadcn@latest init`;
  components added: `button`, `card`, `dialog`, `form`, `input`, `select`,
  `badge`, `sheet`, `collapsible`, `separator`, `tooltip`, `scroll-area`.
- **New backend dependencies:** none. Reuses the existing FastAPI app in
  `engine/api.py`, `engine.connections.find_connections`, and
  `engine.submissions.ingest_submission` (for attachments in the add-node
  flow).
- **Integration point:** all new endpoints are registered on the same `FastAPI`
  instance created by `engine.api.create_app`. Route decorators are added
  inside the factory so tests can construct the app against a `tmp_path`-based
  `data/workstreams/` root.
- **Persistence:** filesystem JSON, no database. Each workstream is a folder
  under `data/workstreams/{workstream_id}/` containing `workstream.json`,
  `graph.json`, and `findings/{edge_id}.json` per analysed edge.

## Exemplar Files

- `engine/api.py` — pattern for adding
  FastAPI routes, uniform error body via `_error`, injectable-dependencies
  factory `create_app`.
- `engine/connections.py` — the
  callable `find_connections` invoked by the `analyze` endpoint for
  non-demo pairs.
- `engine/submissions.py` — attachment
  ingest for the add-node flow (PDF/DOCX MIME allowlist reused).
- `docs/poc/workstream-brain/workstream.html`
  — reference layout, colour legend, and label copy.

## Implementation Plan

### Task 1 — Scaffold the `frontend/` app (INDEPENDENT, medium)

Files to create:

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tailwind.config.ts`
- `frontend/postcss.config.js`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/index.css`
- `frontend/src/lib/queryClient.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/components/ui/*` (from
  shadcn init: `button.tsx`, `card.tsx`, `dialog.tsx`, `form.tsx`, `input.tsx`,
  `select.tsx`, `badge.tsx`, `sheet.tsx`, `collapsible.tsx`, `separator.tsx`,
  `tooltip.tsx`, `scroll-area.tsx`).
- `frontend/src/features/workstream-graph/Sidebar.tsx`
  (the shared sidebar shell across screens).

Deliverable: `npm run dev` in `frontend/` starts a Vite server that renders an
empty `App` with the shared `Sidebar` visible. React Router is configured with
the routes listed above; every route except `/workstreams/:workstreamId` is a
stub.

### Task 2 — Seed the demo workstream on disk (SEQUENTIAL after Task 1, small)

Files to create:

- `data/workstreams/opres-2026/workstream.json`
- `data/workstreams/opres-2026/graph.json`
  (7 nodes, 6 edges, per the response example in "API Design").
- `data/workstreams/opres-2026/findings/e-bcbs--opres.json`
  (the three findings from the analysed-edge response example above).
- `data/workstreams/outsourcing-v2/workstream.json`
  and `graph.json` (a minimal seed so the sidebar switch is demoable).
- `data/workstreams/rmit-v2-2025/workstream.json`
  and `graph.json` (delivered — for sidebar completeness).

Verification: `ls data/workstreams/opres-2026/findings/` shows one file;
`jq '.nodes | length' data/workstreams/opres-2026/graph.json` prints `7`.

### Task 3 — Add FastAPI endpoints (INDEPENDENT of Task 1, SEQUENTIAL after Task 2, medium)

Files to modify:

- `engine/api.py` — register the seven
  new routes on `create_app` (five `GET` routes, `POST /nodes`,
  `POST /edges`, `POST /edges/{id}/analyze`). Add a `workstreams_root: Path`
  argument to the factory (default `REPO_ROOT / "data" / "workstreams"`) so
  tests point it at `tmp_path`.

Files to create:

- `engine/workstreams.py` — helpers
  for reading/writing `workstream.json`, `graph.json`, and
  `findings/{edge_id}.json`. Node-type and edge-type validation lives here,
  plus `add_edge(...)` helper that enforces the self-edge and
  duplicate-edge invariants.
- `engine/tests/test_api_workstreams.py`
  — unit tests for the seven new routes (see "Test Scenarios" below).

Verification: `pytest engine/tests/test_api_workstreams.py -v` all green.

### Task 4 — Build the workstream graph page (SEQUENTIAL after Tasks 1 and 3, medium)

Files to create:

- `frontend/src/features/workstream-graph/WorkstreamGraphPage.tsx`
- `frontend/src/features/workstream-graph/GraphCanvas.tsx`
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`
- `frontend/src/features/workstream-graph/EdgeDetailPanel.tsx`
- `frontend/src/features/workstream-graph/types.ts`
- `frontend/src/features/workstream-graph/legend.ts`
  (colour/short-label maps for node types and edge types).
- `frontend/e2e/workstream-graph.spec.ts`
  (Playwright happy-path E2E — see Verification).

Verification: `npm run dev`; open `/workstreams/opres-2026`; assert canvas
shows 7 nodes and 6 edges; click BCBS node → `Open source` visible; click
`e-bcbs--opres` edge → 3 finding cards.

### Task 5 — Wire the Add-node dialog (SEQUENTIAL after Task 4, small)

Files to create:

- `frontend/src/features/workstream-graph/AddNodeDialog.tsx`
- `frontend/src/features/workstream-graph/addNodeSchema.ts`
  (zod schema; `edges` refined to `min(1)`).

Files to modify:

- `WorkstreamGraphPage.tsx` — open the dialog from `+ Add node`, invalidate
  the graph query on success.

Verification: submit disabled with zero edge rows; submit re-enabled after
adding one complete row; new node appears on canvas after save.

### Task 6 — Wire the Add-linkage dialog on the node detail panel (SEQUENTIAL after Task 4, small)

Files to create:

- `frontend/src/features/workstream-graph/AddLinkageDialog.tsx`
- `frontend/src/features/workstream-graph/addLinkageSchema.ts`
  (zod schema; `target_node_id` and `edge_type` both required; refine that
  `target_node_id !== source_node_id`).

Files to modify:

- `NodeDetailPanel.tsx` — add a `+ Add linkage` secondary button next to the
  `Open task` / `Open source` primary action; open `AddLinkageDialog`
  pre-populated with the current node as source.
- `WorkstreamGraphPage.tsx` — mount `AddLinkageDialog`; on success, invalidate
  both `['workstream', workstreamId, 'graph']` and
  `['node', workstreamId, sourceNodeId]` so the canvas re-renders and the
  neighbours chip row refreshes.

Verification: from any node's detail panel, clicking `+ Add linkage` opens
the dialog with the source pre-populated; the target select omits the source
node; submitting a valid pair produces a new edge on the canvas; submitting
a duplicate (source, target, edge_type) triple renders an inline error
inside the dialog and does not create a duplicate edge.

### Task 7 — Wire zoom controls (SEQUENTIAL after Task 4, small)

Files to modify:

- `GraphCanvas.tsx` — add the three `Button` controls, clamp logic, and inline
  `transform: scale(...)` on the SVG group.

Verification: zoom-in/out/reset all visibly change canvas scale; scale never
exits `[0.5, 2.5]`.

### Task 8 — Wire sidebar collapse and `+ New workstream` link (SEQUENTIAL after Task 4, small)

Files to modify:

- `Sidebar.tsx` — collapse toggle button and reduced-rail rendering; wire
  `+ New workstream` to navigate to `/workstreams/new`; wire `Institution map`
  to `/institution-map`.

Verification: sidebar collapses to icon-only rail and back; both links
navigate to their placeholder routes.

## Negative Constraints

- **Do NOT show semantic labels on graph edges.** Semantic labels (`aligns-with`,
  `differs-on`, `conflicts-with`, `silent-on`, `goes-beyond`) appear only
  inside `EdgeDetailPanel` finding cards, and only after the pair is analysed.
- **Do NOT modify `engine/connections.py` internals in this story.** The
  taxonomy widening is owned by
  [`spec-engine-taxonomy.md`](spec-engine-taxonomy.md); this story consumes
  its output only.
- **Do NOT wire the concepts panel to any extraction pipeline.** Ontology
  extraction is out of MVP1 scope; the `Collapsible` renders placeholder text.
- **Do NOT implement pan or drag on the SVG canvas.** MVP1 supports zoom only.
- **Do NOT persist workstream files outside `data/workstreams/`.** Sensitive
  BNM document metadata must remain under the git-ignored root.
- **Do NOT implement authentication or role-checking on the workstream
  endpoints in MVP1.** Reuse the existing submission role-gate for attachment
  ingest only.

## Test Scenarios

Backend (pytest, `engine/tests/test_api_workstreams.py`):

- `test_GET_workstreams_lists_three_seeded_workstreams` — response body
  contains `opres-2026`, `outsourcing-v2`, `rmit-v2-2025`.
- `test_GET_graph_returns_seeded_opres_workstream` — 7 nodes, 6 edges, one
  edge (`e-bcbs--opres`) has `analysed=true`.
- `test_GET_node_detail_returns_first_order_neighbours_for_task_node` — PD
  node has 6 neighbours in the response.
- `test_GET_edge_detail_returns_not_analysed_when_findings_file_absent` —
  `e-hkma--opres` returns `status: not_analysed`, `findings: []`.
- `test_GET_edge_detail_returns_analysed_with_findings_when_file_present` —
  `e-bcbs--opres` returns three findings and `status: analysed`.
- `test_POST_node_rejects_empty_edges_400_EDGE_REQUIRED` — request body with
  `edges: []` returns 400 `EDGE_REQUIRED` and does not touch `graph.json`.
- `test_POST_node_rejects_invalid_node_type_400_INVALID_NODE_TYPE` — request
  body with `node_type: "cluster"` returns 400 `INVALID_NODE_TYPE`.
- `test_POST_node_rejects_invalid_edge_type_400_INVALID_EDGE_TYPE` — edge row
  with `edge_type: "differs-on"` returns 400 `INVALID_EDGE_TYPE`.
- `test_POST_node_writes_graph_and_returns_created_edges` — new node and
  its edges are persisted to `graph.json`.
- `test_POST_missing_workstream_returns_404_WORKSTREAM_NOT_FOUND`.
- `test_POST_edge_analyze_replays_retired_trace_for_opres_openfinance_pair` —
  the endpoint returns the retired trace's findings; no network call is made
  (assert via a stub `finder_fn` that raises if called).
- `test_POST_edge_analyze_writes_findings_file_and_flips_edge_analysed_flag`.
- `test_POST_edge_creates_new_structural_edge_between_existing_nodes` — a
  well-formed body persists the new edge to `graph.json` with
  `analysed: false` and returns 201.
- `test_POST_edge_rejects_self_edge_400_SELF_EDGE_FORBIDDEN` — request with
  `source_node_id == target_node_id` returns 400 and does not touch
  `graph.json`.
- `test_POST_edge_rejects_duplicate_edge_409_EDGE_ALREADY_EXISTS` — creating
  an edge whose (source, target, edge_type) triple already exists in
  `graph.json` returns 409 and does not persist a duplicate.
- `test_POST_edge_rejects_unknown_source_or_target_404_NODE_NOT_FOUND`.
- `test_POST_edge_rejects_invalid_edge_type_400_INVALID_EDGE_TYPE`.

Frontend (Vitest component tests, files colocated under
`frontend/src/features/workstream-graph/`):

- `AddNodeDialog.test.tsx: submit button disabled when edge rows empty`.
- `AddNodeDialog.test.tsx: submit button re-enables after adding one complete row`.
- `AddNodeDialog.test.tsx: removing rows below one disables submit again`.
- `AddLinkageDialog.test.tsx: submit disabled until both selects have a value`.
- `AddLinkageDialog.test.tsx: target select omits the source node from its options`.
- `AddLinkageDialog.test.tsx: 409 EDGE_ALREADY_EXISTS renders inline error without closing`.
- `GraphCanvas.test.tsx: clicking a node dispatches showNode(nodeId)`.
- `NodeDetailPanel.test.tsx: re-renders with clicked node's data when nodeId changes`.
- `NodeDetailPanel.test.tsx: action button reads Open task for task node`.
- `NodeDetailPanel.test.tsx: action button reads Open source for BCBS node`.
- `NodeDetailPanel.test.tsx: + Add linkage button opens AddLinkageDialog with source pre-populated`.
- `EdgeDetailPanel.test.tsx: unanalysed edge shows Analyze linkages button and no finding cards`.
- `EdgeDetailPanel.test.tsx: analysed edge shows finding cards and no Analyze button`.
- `GraphCanvas.test.tsx: zoom-in clamps at 2.5 after repeated clicks`.
- `GraphCanvas.test.tsx: zoom-out clamps at 0.5 after repeated clicks`.
- `Sidebar.test.tsx: collapse toggle hides workstream names and reveals rail`.

### Scenario-to-test mapping

| Key Scenario (business)                                                     | Test location                                                                                                                                                                                                              |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Aisyah opens her pre-seeded workstream                                      | E2E `workstream-graph.spec.ts` + backend `test_GET_graph_returns_seeded_opres_workstream`                                                                                                                                  |
| Aisyah clicks the task node and sees its detail panel                       | `NodeDetailPanel.test.tsx: action button reads Open task` + E2E                                                                                                                                                            |
| Aisyah clicks a resource node and sees its detail panel                     | `NodeDetailPanel.test.tsx: action button reads Open source`                                                                                                                                                                |
| Aisyah clicks a first-order neighbour chip to switch focus                  | `NodeDetailPanel.test.tsx: re-renders with clicked node's data`                                                                                                                                                            |
| Aisyah clicks an unanalysed edge                                            | `EdgeDetailPanel.test.tsx: unanalysed edge shows Analyze linkages` + backend `test_GET_edge_detail_returns_not_analysed`                                                                                                   |
| Aisyah clicks an already-analysed edge                                      | `EdgeDetailPanel.test.tsx: analysed edge shows finding cards` + backend `test_GET_edge_detail_returns_analysed_with_findings` + E2E                                                                                        |
| Aisyah adds a new anchor with one edge to her PD                            | `AddNodeDialog.test.tsx: submit button re-enables` + backend `test_POST_node_writes_graph_and_returns_created_edges` + E2E                                                                                                 |
| Aisyah tries to add a node without declaring an edge                        | `AddNodeDialog.test.tsx: submit disabled when edge rows empty` + backend `test_POST_node_rejects_empty_edges_400_EDGE_REQUIRED`                                                                                            |
| Aisyah adds multiple edges to a new node                                    | `AddNodeDialog.test.tsx: multi-edge` (component) + backend `test_POST_node_writes_graph`                                                                                                                                   |
| Aisyah removes an edge row before submitting                                | `AddNodeDialog.test.tsx: removing rows below one disables submit again`                                                                                                                                                    |
| Aisyah adds a linkage between two existing nodes from the node detail panel | `NodeDetailPanel.test.tsx: + Add linkage button opens dialog` + `AddLinkageDialog.test.tsx: submit disabled until both selects have a value` + backend `test_POST_edge_creates_new_structural_edge_between_existing_nodes` |
| Aisyah cannot create a self-edge                                            | `AddLinkageDialog.test.tsx: target select omits the source node` + backend `test_POST_edge_rejects_self_edge_400_SELF_EDGE_FORBIDDEN`                                                                                      |
| Aisyah cannot duplicate an existing linkage                                 | `AddLinkageDialog.test.tsx: 409 EDGE_ALREADY_EXISTS renders inline error without closing` + backend `test_POST_edge_rejects_duplicate_edge_409_EDGE_ALREADY_EXISTS`                                                        |
| Aisyah zooms the canvas (in/out/reset)                                      | `GraphCanvas.test.tsx: zoom-in clamps` + `zoom-out clamps`                                                                                                                                                                 |
| Aisyah collapses the sidebar                                                | `Sidebar.test.tsx: collapse toggle`                                                                                                                                                                                        |
| Aisyah expands the sidebar back                                             | `Sidebar.test.tsx: collapse toggle` (round-trip)                                                                                                                                                                           |
| Aisyah opens the new-workstream screen from the sidebar                     | `Sidebar.test.tsx: + New workstream navigates`                                                                                                                                                                             |
| Aisyah clicks the Institution map link                                      | `Sidebar.test.tsx: institution map navigates`                                                                                                                                                                              |
| Aisyah opens the task screen from a task node                               | E2E `workstream-graph.spec.ts`                                                                                                                                                                                             |
| Aisyah opens the source of a resource node                                  | `NodeDetailPanel.test.tsx: Open source`                                                                                                                                                                                    |
| Aisyah switches to a different workstream from the sidebar                  | `Sidebar.test.tsx: workstream item navigates` + backend `test_GET_workstreams_lists_three`                                                                                                                                 |
| Aisyah runs analysis on an unanalysed edge                                  | Backend `test_POST_edge_analyze_replays_retired_trace_for_opres_openfinance_pair` + backend `test_POST_edge_analyze_writes_findings_file_and_flips_edge_analysed_flag` + E2E                                               |

## Verification

- **Backend:** `pytest engine/tests/test_api_workstreams.py -v` from repo root.
- **Frontend components:** `npm run test` (Vitest) from `frontend/`.
- **E2E:** Playwright — one happy-path spec at
  `frontend/e2e/workstream-graph.spec.ts`
  covering: land on `/workstreams/opres-2026` → assert 7 nodes visible → click
  BCBS node → assert `Open source` visible → click `e-bcbs--opres` edge →
  assert 3 finding cards visible → click `+ Add node` → assert dialog opens
  and `Add to graph` is disabled. Assigned to Task 4.
