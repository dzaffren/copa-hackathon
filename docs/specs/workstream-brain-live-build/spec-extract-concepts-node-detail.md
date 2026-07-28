# Extract Concepts and View Node Detail

**Ticket:** TBD

When a drafter opens a document's detail panel, they see a consistent, ordered
view of that document: the documents it connects to, a trail of what has
happened to it, its regulatory profile, and its topics. This story adds an
"Extract concepts" action that derives the document's topics on demand and shows
them as pills, so the drafter can understand at a glance what any document in the
workstream is about before connecting or analysing it.

## User Story

As Aisyah, a policy drafter building a workstream, I want to open a document and
extract its concepts on demand so that I can see what topics it covers and read a
clear record of what has been done to it, without leaving the page or guessing at
its contents.

## Background & Context

**Current state:**

- Opening a document's detail panel shows its first-order neighbours (the
  documents it directly connects to), and that is effectively all it shows.
- The recent-activity trail exists as a section but is empty — nothing populates
  it, so the drafter cannot see that a document was created or broken into
  passages.
- There is no way to see a document's topics inside the app; concepts are never
  derived on demand for a document the drafter added.
- There is no regulatory-profile summary on a document at all.

**Problem:**

- A drafter cannot tell what a freshly added document covers without reading it in
  full, which defeats the purpose of a build-it-yourself workstream.
- With an empty activity trail, the drafter has no confirmation that a document
  was successfully added and broken into passages.
- Without a visible topic summary, deciding which documents are worth connecting
  and analysing is slower and more error-prone.

## Target User & Persona

- **Who:** Aisyah R., the policy drafter, working on the Operational Resilience
  policy-document workstream for the COPA Hackathon 2026 demo.
- **Context:** She has just added a source document (for example, "BCBS
  Principles for Operational Resilience 2021") to her workstream and wants to
  understand it before connecting and analysing it.
- **Current workaround:** She opens the source PDF outside the tool and reads it
  herself to work out what it covers.

## Goals

- Show a document's detail panel with four sections in a fixed order: neighbours,
  recent activity, metadata, and concepts.
- Populate the recent-activity trail with the real events that happen to a
  document through the build flow: "node created", "chunking completed", and
  later "axes extracted".
- Let the drafter extract a document's concepts on demand with a single action,
  waiting while it runs, and see the resulting topic pills when it finishes.
- Show a fixed regulatory-profile "Metadata" section as a placeholder so the
  layout is correct ahead of a later story that fills it in.
- Make concepts, once extracted, persist so re-opening the document later still
  shows them.

## Non-Goals

- **Filling in the metadata fields.** The Metadata section is a deliberate
  placeholder; every field shows "N/A" for now and is not derived from the
  document in this story.
- **Background extraction.** Extraction runs only when the drafter clicks the
  button and completes before returning; there is no queue and no work that
  continues after the drafter navigates away.
- **Editing concepts.** The drafter cannot rename, add, or remove concept pills
  by hand in this story.
- **Analysis of the document's linkages**, which is a separate story.

## User Workflow

1. **Open a document** — Aisyah clicks a document node on the canvas and its
   detail panel opens, showing four sections in order: its neighbours, its recent
   activity, its metadata, and its concepts.
2. **Read the trail** — She sees the recent-activity trail already lists "node
   created" and "chunking completed", confirming the document was added and
   broken into passages. The Concepts section is empty because concepts have not
   been extracted yet.
3. **Extract concepts** — She clicks "Extract concepts". The button shows a
   pending state and she waits while the extraction runs; on a large document this
   can take from a few seconds up to a couple of minutes.
4. **See the result** — When it finishes, concept pills appear in the Concepts
   section (for example, "operational resilience testing frequency"), and "axes
   extracted" joins the recent-activity trail.
5. **Completion** — She can re-open the document at any time and still see the
   same concepts and the full activity trail; clicking "Extract concepts" again
   returns quickly with the same pills.

## Acceptance Criteria

### Scenario: Opening a document shows the four sections in order

```gherkin
Given Aisyah has added the "BCBS Principles for Operational Resilience 2021" document to her workstream
When she opens that document's detail panel
Then she sees four sections in this order: neighbours, recent activity, metadata, and concepts
  And the neighbours section lists the "Operational Resilience PD v0.3" focal working draft it connects to
  And the recent-activity trail lists "node created" and "chunking completed"
  And the metadata section is shown
  And the concepts section is empty because concepts have not been extracted yet
```

### Scenario: Extracting concepts for the first time

```gherkin
Given Aisyah has opened the "BCBS Principles for Operational Resilience 2021" document
  And its concepts have not been extracted yet
When she clicks "Extract concepts"
Then the "Extract concepts" button shows a pending state while the extraction runs
  And she waits on the page until it finishes
```

### Scenario: Concept pills appear when extraction finishes

```gherkin
Given Aisyah has clicked "Extract concepts" on the "BCBS Principles for Operational Resilience 2021" document
When the extraction finishes
Then the concepts section shows topic pills including "operational resilience testing frequency", "third-party dependency management", and "scenario testing cadence"
  And "axes extracted" is added to the recent-activity trail
  And the "Extract concepts" button returns from its pending state
```

### Scenario: Metadata section always shows the placeholder profile

```gherkin
Given Aisyah has opened any document in her workstream
When she reads the metadata section
Then she sees these fields, each showing "N/A": policy owner, applicability, empowerment framework, requirement, issuance date, effective date, keywords, legal basis, and ISMP classification
  And this is true whether or not concepts have been extracted
```

### Scenario: Extraction fails and the drafter is told clearly

```gherkin
Given Aisyah has opened the "BCBS Principles for Operational Resilience 2021" document
  And its concepts have not been extracted yet
When she clicks "Extract concepts"
  And the extraction cannot complete because the concept-extraction service is unavailable
Then she sees a clear message that extraction failed
  And no concept pills are shown
  And no "axes extracted" entry is added to the recent-activity trail
  And she is offered the option to retry
```

### Scenario: Retrying after a failed extraction succeeds

```gherkin
Given Aisyah's earlier attempt to extract concepts for the "BCBS Principles for Operational Resilience 2021" document failed
  And the concept-extraction service is available again
When she clicks "Extract concepts" to retry
Then the extraction runs and finishes
  And the concept pills appear in the concepts section
  And "axes extracted" is added to the recent-activity trail
```

### Scenario: A second extraction is fast and yields the same concepts

```gherkin
Given Aisyah has already extracted concepts for the "BCBS Principles for Operational Resilience 2021" document
  And the document's passages have not changed since
When she clicks "Extract concepts" again
Then it returns quickly without redoing the extraction from scratch
  And the concepts section shows the same topic pills as before
  And the recent-activity trail is unchanged
```

### Scenario: Concepts persist when the document is re-opened later

```gherkin
Given Aisyah extracted concepts for the "BCBS Principles for Operational Resilience 2021" document earlier
When she closes the detail panel and re-opens the same document later
Then the concepts section still shows the same topic pills
  And the recent-activity trail still lists "node created", "chunking completed", and "axes extracted"
```

### Scenario: A prepared workstream keeps its concepts for the demo

```gherkin
Given Aisyah extracted concepts for the "Operational Resilience Policy 2024" document while preparing the demo workstream ahead of time
When she re-opens that workstream and that document during the demo
Then the concepts section shows the same topic pills that were extracted during preparation
  And no re-extraction is needed to see them
```

## Business Rules & Constraints

- **Section order is fixed.** A document's detail panel always shows neighbours,
  then recent activity, then metadata, then concepts — in that order.
- **The activity trail records real build events.** The trail shows "node
  created" and "chunking completed" for every document, and gains "axes
  extracted" once concepts have been successfully extracted; entries are never
  fabricated for events that did not happen.
- **Extraction requires passages.** Concept extraction runs over the document's
  passages, which always exist by the time a document node exists (a document is
  broken into passages when it is added).
- **Extraction is synchronous.** The drafter waits on the page while extraction
  runs; there is no background processing and nothing continues after the drafter
  navigates away.
- **No partial results on failure.** If extraction fails, no concept pills are
  shown and no "axes extracted" entry is added; the drafter sees a clear failure
  message and can retry.
- **Reuse over rework.** Re-clicking "Extract concepts" after a successful
  extraction reuses the concepts already derived and returns quickly with the
  same pills; new work happens only if the document's passages changed.
- **Metadata is a placeholder.** The Metadata section always lists the same nine
  regulatory-profile fields — policy owner, applicability, empowerment framework,
  requirement, issuance date, effective date, keywords, legal basis, and ISMP
  classification — each showing "N/A" for now; it is not derived from the
  document in this story.
- **Concepts and metadata are distinct.** Concepts are the document's extracted
  topic phrases; metadata is the (currently empty) regulatory profile. They are
  separate sections and are not confused with one another.
- **Durability.** Once extracted, a document's concepts are stored with the
  workstream so they survive to the demo and are shown on re-opening without
  re-extraction.

## Success Metrics

- A drafter can extract a document's concepts and see topic pills within a single
  wait, without leaving the page — seconds for a small document, up to a couple of
  minutes for a large one.
- 100% of opened documents show the four sections in the fixed order, with a
  populated activity trail for every build event that occurred.
- A workstream prepared before the demo shows its previously extracted concepts
  intact on re-opening, with no re-extraction required.
- A repeated extraction on an unchanged document returns noticeably faster than
  the first and yields identical concepts.

## Dependencies

- A document must already have been added and broken into passages (the "Add a
  document and break it into passages" story) before its concepts can be
  extracted.
- Access to the concept-extraction service (the language model used for
  extraction) during preparation and demo.
- Durable storage of concepts with the workstream, shared with the wider epic's
  durability rule, so extracted concepts persist to the demo.

## Open Questions

- [x] ~~Should the Metadata fields be derived from the document now?~~ —
      **Resolved:** No. Metadata is a deliberate placeholder showing "N/A" for all
      nine fields so the layout is correct; deriving it is a later story.
- [x] ~~Should extraction run in the background so the drafter can keep working?~~
      — **Resolved:** No. Extraction is synchronous and the drafter waits on the
      page; this keeps the flow simple for the hackathon with no background
      machinery.
- [x] ~~Should re-clicking "Extract concepts" always redo the work?~~ —
      **Resolved:** No. Concepts already derived are reused, so a second extraction
      on an unchanged document returns quickly with the same pills; new work happens
      only if the passages changed.
- [x] ~~What does the drafter see if extraction fails partway?~~ — **Resolved:**
      A clear failure message and a retry option; no partial or garbled concepts and
      no "axes extracted" entry are shown.

---

## Functional Requirements

- **Section order (fixed):** The node-detail payload and the panel that renders it
  must present exactly four sections in this order: (1) `first_order_neighbours`,
  (2) `recent_activity`, (3) `metadata`, (4) `concepts`. This order is a contract —
  a test asserts the payload key order and the panel's rendered section order.
- **`concepts` → `metadata` rename (contract change):** Today's node-detail
  `concepts` block surfaces the nine-field regulatory profile from
  `engine/concepts.py` (`concepts.load_concepts`). That block **moves** to a new
  `metadata` key. The `concepts` key is **repurposed** to carry the extracted
  **axes** (topic pills), not the nine regulatory fields. The two are distinct
  sections and are never conflated.
- **Metadata is a placeholder (always nine fields, all N/A):** The `metadata` block
  always lists the nine `CONCEPT_FIELDS` from `engine/concepts.py` — `policy_owner`,
  `applicability`, `empowerment_framework`, `requirement`, `issuance_date`,
  `effective_date`, `keywords`, `legal_basis`, `ismp_classification` — each `null`
  on the wire and rendered as "N/A" in the panel. This story does **not** derive any
  metadata value; the field set of `engine/concepts.py` is unchanged.
- **Extract concepts (synchronous):** `POST /api/workstreams/{workstream_id}/nodes/{node_id}/extract-concepts`
  runs the extraction inline and blocks until it completes or fails; there is no
  queue, no background worker, and nothing continues after the response returns. On
  a large document a single call may take from a few seconds up to a couple of
  minutes.
- **Extraction mechanism:** The route builds the workstream anchor index via
  `ws_anchors.build_index(workstreams_dir, workstream_id)`, then calls
  `arm_g.extract_axes_for_document(index, document_id=node_id, axes_dir=<workstream axes dir>)`
  (a chunked node's `document_id` equals its node id). It collects the **deduped
  union** of axes across all of the node's anchors, persists them via the axes
  cache, and appends an `"axes extracted"` entry to the node's `recent_activity` in
  `graph.json`.
- **Reuse over rework (cache hit):** `extract_axes_for_document` already caches
  per-anchor, keyed on `text_hash` + `axis_cap` (see `engine/arm_g.py`). A second
  extraction on a node whose anchors have not changed is a cache hit for every
  anchor: no model call runs, the same axes are returned, and — because the union is
  unchanged and an `"axes extracted"` entry already exists — the `recent_activity`
  trail is not double-appended. This is the mechanism behind "second extraction is
  fast and unchanged".
- **Atomicity (no partial on failure):** The axes cache write, the concepts pill
  store, and the `"axes extracted"` activity append happen **only after** a fully
  successful extraction. If extraction raises, none of the three side effects occur:
  no pills, no activity entry, no partial cache surfaced to the reader.
- **Idempotency:** Repeated successful calls on unchanged anchors yield the same
  axes and add no duplicate `"axes extracted"` entry.

### Validation & Business Rules

- **Node must be segmented.** Extraction requires the node's anchors to exist
  (`ws_anchors.build_index` yields at least one anchor for `node_id`). A real
  document node is always chunked when it is added, so this is a guard, not an
  expected path: an unchunked node → **409 `NOT_SEGMENTED`**.
- **Extraction failure is atomic.** If `extract_axes_for_document` raises
  (`LLMResponseError` or any extraction-service failure) → **502
  `EXTRACTION_FAILED`**, with no `"axes extracted"` activity entry and no partial
  pills written.
- **Unknown workstream / node.** Missing workstream → **404 `WORKSTREAM_NOT_FOUND`**;
  missing node → **404 `NODE_NOT_FOUND`**.
- **Concepts absent is not an error.** A node whose axes cache is absent returns a
  `concepts` block with `status: "not_extracted"` and an empty `axes` list; the
  panel shows an empty Concepts section, not an error.

## Permissions & Security

- **Scope:** Internal demo API (`/api/workstreams/*`), same surface as every other
  Workstream Brain route; no per-user authorization in MVP1.
- **Authorization:** None beyond the existing CORS allow-list (`http://localhost:5173`).
- **Input validation:** `workstream_id` and `node_id` are path segments resolved
  against `data/workstreams/`; no request body is required for `extract-concepts`
  (an empty `POST`). The route never reaches a live model when tests inject a fake
  extractor.

## API Design

### `GET /api/workstreams/{workstream_id}/nodes/{node_id}`

Enriched to carry the four ordered blocks. `metadata` is the (renamed) nine-field
profile — every field `null` for now; `concepts` carries extracted axes.

**Response (200) — a chunked document with concepts already extracted:**

```json
{
  "id": "bcbs-opres-2021",
  "node_type": "international-standard",
  "title": "BCBS Principles for Operational Resilience 2021",
  "issuer": "BCBS",
  "short_type": "Standard",
  "description": "Basel Committee principles for operational resilience.",
  "source_url": "https://www.bis.org/bcbs/publ/d516.htm",
  "first_order_neighbours": [
    {
      "id": "opres-pd-v0-3",
      "node_type": "task",
      "title": "Operational Resilience PD v0.3"
    }
  ],
  "recent_activity": [
    { "event": "node created", "at": "2026-07-20T09:00:00Z" },
    { "event": "chunking completed", "at": "2026-07-20T09:01:12Z" },
    { "event": "axes extracted", "at": "2026-07-20T09:03:44Z" }
  ],
  "metadata": {
    "policy_owner": null,
    "applicability": null,
    "empowerment_framework": null,
    "requirement": null,
    "issuance_date": null,
    "effective_date": null,
    "keywords": null,
    "legal_basis": null,
    "ismp_classification": null
  },
  "concepts": {
    "status": "extracted",
    "axes": [
      "operational resilience testing frequency",
      "third-party dependency management",
      "scenario testing cadence"
    ]
  }
}
```

**Response (200) — a chunked document whose concepts have not been extracted:**

```json
{
  "id": "bcbs-opres-2021",
  "recent_activity": [
    { "event": "node created", "at": "2026-07-20T09:00:00Z" },
    { "event": "chunking completed", "at": "2026-07-20T09:01:12Z" }
  ],
  "metadata": {
    "policy_owner": null,
    "applicability": null,
    "empowerment_framework": null,
    "requirement": null,
    "issuance_date": null,
    "effective_date": null,
    "keywords": null,
    "legal_basis": null,
    "ismp_classification": null
  },
  "concepts": { "status": "not_extracted", "axes": [] }
}
```

(Non-block fields — `node_type`, `title`, `first_order_neighbours`, etc. — omitted
from the second example for brevity; they are unchanged.)

### `POST /api/workstreams/{workstream_id}/nodes/{node_id}/extract-concepts`

**Request:** empty body (no payload required).

**Response (200):**

```json
{
  "node_id": "bcbs-opres-2021",
  "concepts": {
    "status": "extracted",
    "axes": [
      "operational resilience testing frequency",
      "third-party dependency management",
      "scenario testing cadence"
    ]
  },
  "recent_activity": [
    { "event": "node created", "at": "2026-07-20T09:00:00Z" },
    { "event": "chunking completed", "at": "2026-07-20T09:01:12Z" },
    { "event": "axes extracted", "at": "2026-07-20T09:03:44Z" }
  ]
}
```

On a cache hit (unchanged anchors) the response is identical to the prior success
and no new `"axes extracted"` entry is appended.

**Errors:**

| Status | Code                   | Condition                                                                                                                           |
| ------ | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | No workstream with `workstream_id` under `data/workstreams/`.                                                                       |
| 404    | `NODE_NOT_FOUND`       | No node with `node_id` in the workstream graph.                                                                                     |
| 409    | `NOT_SEGMENTED`        | The node has no anchors yet (`ws_anchors.build_index` yields none for `node_id`) — it was never chunked.                            |
| 502    | `EXTRACTION_FAILED`    | `extract_axes_for_document` raised (extraction service unavailable / unparseable reply). No axes stored, no activity entry written. |

## Data Model & Migrations

### Per-workstream axes cache (new location)

**File:** `data/workstreams/{workstream_id}/axes/axes-{document_id}.json`
(`document_id` equals the chunked node id). This is the axis cache **relocated** from
`engine/arm_g.py`'s `AXES_DIR = REPO_ROOT/"experiments"` — the shape is unchanged
from `arm_g`.

| Field                 | Type     | Description                                                       |
| --------------------- | -------- | ----------------------------------------------------------------- |
| `document_id`         | string   | The node id whose anchors were extracted.                         |
| `model`               | string   | Deployment used (`EXTRACTION_DEPLOYMENT`).                        |
| `anchors`             | array    | One entry per anchor.                                             |
| `anchors[].anchor_id` | string   | Anchor identifier within the node.                                |
| `anchors[].text_hash` | string   | SHA256 (first 16 hex) of the anchor text — cache key.             |
| `anchors[].axis_cap`  | int      | Axis cap for this anchor's length — second half of the cache key. |
| `anchors[].axes`      | string[] | The extracted axes for that anchor.                               |

**Example (`data/workstreams/opres-v2/axes/axes-bcbs-opres-2021.json`):**

```json
{
  "document_id": "bcbs-opres-2021",
  "model": "gpt-4o-mini",
  "anchors": [
    {
      "anchor_id": "bcbs-opres-2021::p3",
      "text_hash": "9f2c1a0b3d4e5f6a",
      "axis_cap": 5,
      "axes": [
        "operational resilience testing frequency",
        "scenario testing cadence"
      ]
    },
    {
      "anchor_id": "bcbs-opres-2021::p7",
      "text_hash": "1b2c3d4e5f6a7b8c",
      "axis_cap": 6,
      "axes": ["third-party dependency management", "scenario testing cadence"]
    }
  ]
}
```

The node-detail `concepts.axes` list is the **deduped union** across `anchors[].axes`
— from the example above: `["operational resilience testing frequency", "scenario
testing cadence", "third-party dependency management"]`.

### Recent activity (existing location)

`recent_activity` lives **on the node object in `graph.json`**
(`data/workstreams/{workstream_id}/graph.json`), an append-only list. The
`extract-concepts` route appends `{"event": "axes extracted", "at": "<ISO-8601>"}`
after a successful extraction. Sibling stories append `"node created"` and
`"chunking completed"`.

### Migration notes

- The fixture `recent_activity` entries carry the older `{kind, author, at, summary}`
  shape (see `data/workstreams/opres-v2/graph.json`). New build-event entries use the
  `{event, at}` shape; the panel renders both (an entry with `event` shows the event
  label; an entry with `kind` keeps the author/summary rendering).
- No data backfill is required; nodes without an axes cache simply return
  `status: "not_extracted"`.

## UI/Frontend Requirements

### Components

**NodeDetailPanel** — `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`

- **Type:** Modify existing.
- **Purpose:** Render the four sections in the fixed order — First-order
  neighbours, Recent activity, **Metadata** (the nine named fields, each "N/A"),
  **Concepts** (extracted axes as pills) — and add an "Extract concepts" button.
- **Changes:**
  - Move the current nine-field regulatory disclosure to a **Metadata** section that
    always renders all nine labelled fields showing "N/A" (values are `null`).
  - Repurpose the **Concepts** section to render `concepts.axes` as pills. When
    `status === "not_extracted"` (empty axes), show an empty state and the "Extract
    concepts" button.
  - Remove the "Second-order neighbours" placeholder section from the four-section
    order (metadata takes its slot); if retained it must not break the fixed order.
- **Props:** unchanged (`workstreamId`, `nodeId`, `onSelectNode`, `onClose`).

### User Interactions

- Click a document node on the canvas → panel opens showing the four ordered
  sections.
- Click "Extract concepts" → `api.extractConcepts(workstreamId, nodeId)` fires; the
  panel refetches node detail on success (TanStack Query `invalidateQueries` on
  `["node", workstreamId, nodeId]`).
- Click a concept pill → no action in this story (pills are read-only).

### States (Extract concepts button)

- **Idle:** button reads "Extract concepts", enabled, when `concepts.status ===
"not_extracted"`.
- **Pending:** button reads "Extracting…" with a spinner, disabled, while the
  synchronous call is in flight.
- **Error:** on failure, show a clear inline failure message ("Concept extraction
  failed") and a retry affordance (the button returns to an enabled "Extract
  concepts" / "Retry"); no pills, no activity change.
- **Done:** on success, pills appear in the Concepts section and "axes extracted"
  appears in Recent activity; the button no longer shows (concepts are present).

### Type & API-client changes

- `frontend/src/lib/types.ts`:
  - Add `NodeMetadata` (the nine fields, each `string | string[] | null`) and set
    `NodeDetail.metadata: NodeMetadata`.
  - Add `NodeConcepts = { status: "extracted"; axes: string[] } | { status:
"not_extracted"; axes: [] }` and set `NodeDetail.concepts: NodeConcepts`.
  - Add `ExtractConceptsResponse = { node_id: string; concepts: NodeConcepts;
recent_activity: RecentActivity[] }`.
- `frontend/src/lib/api.ts`: add
  `extractConcepts(workstreamId: string, nodeId: string): Promise<ExtractConceptsResponse>`
  posting to `.../nodes/${nodeId}/extract-concepts`.

## Architecture Notes

- **New dependencies:** none (reuses `engine/arm_g.py`, `engine/concepts.py`, and the
  sibling story's `engine/ws_anchors.py`).
- **Shared contract (verbatim — three sibling specs share this):**

  > A module `engine/ws_anchors.py` (created by the sibling "add-node-chunking"
  > story) stores per-node anchors at
  > `data/workstreams/{workstream_id}/anchors/{node_id}.json` and exposes
  > `build_index(workstreams_dir, workstream_id) -> AnchorIndex` (unions all the
  > workstream's anchor files). A chunked node's `document_id` equals its node id.
  > The axis cache RELOCATES from `engine/arm_g.py`'s `AXES_DIR =
REPO_ROOT/"experiments"` to per-workstream
  > `data/workstreams/{workstream_id}/axes/axes-{document_id}.json`;
  > `extract_axes_for_document` gains an `axes_dir` parameter (default preserves old
  > path for back-compat) so this story can point it at the workstream's axes dir.

- **Contract changes this story introduces:**
  - **Axis-cache relocation:** `extract_axes_for_document` (and its
    `_load_axes_cache` / `_write_axes_cache` helpers) gain an `axes_dir` parameter
    defaulting to `AXES_DIR` (back-compat for `scripts/run_finder_trace.py` and the
    Arm G experiment). This story passes
    `workstreams_dir/{workstream_id}/axes`.
  - **`concepts` → `metadata` rename in the node-detail payload:** the block that
    was `concepts` (nine regulatory fields) is now `metadata`; the new `concepts`
    block carries axes. Downstream consumers of the old `concepts` shape
    (`CrossProfile.concepts` in `frontend/src/lib/types.ts`) read the **cross-links**
    routes, not this node-detail route, so they are unaffected; only
    `fetchNodeDetail` / `NodeDetailPanel` consume the renamed shape.
- **Dependencies & integration:** SEQUENTIAL on the sibling "add-node-chunking"
  story for `engine/ws_anchors.py`. The `axes_dir` parameterisation (Task 1) is a
  prerequisite for the route (Task 2), which is a prerequisite for the panel (Task 3).

## Exemplar Files

- `engine/api.py` `get_workstream_node_detail` (~955) — the route to restructure
  (four ordered blocks; `_ws_error` helper at ~302) and the sibling of the new POST
  route.
- `engine/arm_g.py` `extract_axes_for_document` (~185), `_load_axes_cache` /
  `_write_axes_cache` (~134), `AXES_DIR` (~67) — the extractor and cache to
  parameterise with `axes_dir`.
- `engine/concepts.py` — `CONCEPT_FIELDS` (the nine metadata fields; do not change
  the set).
- `engine/tests/test_arm_g.py` (`test_axis_cache_hit_skips_extraction`,
  `test_axis_cache_invalidated_on_cap_change`) — how to `monkeypatch` `AXES_DIR` and
  stub `call_chat` so no live model runs.
- `engine/tests/test_api_node_metadata.py` — TestClient + `shutil.copytree` fixture
  pattern for node-detail assertions.
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx` — the panel to modify.
- `frontend/src/lib/types.ts` / `frontend/src/lib/api.ts` — the `NodeDetail` type and
  the client-function pattern (`fetchNodeDetail`, `analyzeEdge`).
- `frontend/e2e/workstream-graph.spec.ts` — the Playwright pattern (baseURL
  `http://localhost:5173`, role-based locators).

## Implementation Plan

### Sub-tasks

**Task 1: Relocate + parameterise the axis cache in `engine/arm_g.py`** — _small_ (<100 LOC)

- Add an `axes_dir: Path = AXES_DIR` parameter to `extract_axes_for_document`,
  `_load_axes_cache`, and `_write_axes_cache`; default preserves the old path for
  `scripts/run_finder_trace.py` and the Arm G experiment.
- Files: `engine/arm_g.py`, `engine/tests/test_arm_g.py` (add a test that passing
  `axes_dir` writes/reads under that dir; existing default-path tests stay green).
- INDEPENDENT.

**Task 2: `extract-concepts` route + node-detail payload restructure in `engine/api.py`** — _medium_ (100–300 LOC)

- Restructure `get_workstream_node_detail`: emit `first_order_neighbours`,
  `recent_activity`, `metadata` (nine `CONCEPT_FIELDS`, all `null`), `concepts`
  (deduped-union axes from the workstream axes cache, or `{status: "not_extracted",
axes: []}`) in that key order.
- Add `POST .../nodes/{node_id}/extract-concepts`: build index via
  `ws_anchors.build_index`, guard `NOT_SEGMENTED`, call
  `arm_g.extract_axes_for_document(index, document_id=node_id,
axes_dir=workstreams_dir/workstream_id/"axes")`, dedupe-union axes, on success
  append `{"event":"axes extracted","at":...}` to the node in `graph.json` and return
  `{node_id, concepts, recent_activity}`. Wrap failures as `502 EXTRACTION_FAILED`
  (no side effects); `404` guards via `_ws_error`.
- Files: `engine/api.py`, `engine/tests/test_api_extract_concepts.py` (new),
  additions to `engine/tests/test_api_node_metadata.py`.
- SEQUENTIAL (depends on Task 1 and on `engine/ws_anchors.py` from the sibling story).

**Task 3: Four-section render + Extract-concepts button + types/api** — _medium_ (100–300 LOC)

- `frontend/src/lib/types.ts`: `NodeMetadata`, `NodeConcepts`,
  `ExtractConceptsResponse`; update `NodeDetail`.
- `frontend/src/lib/api.ts`: `extractConcepts(workstreamId, nodeId)`.
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`: render four sections
  in order; Metadata (nine N/A fields); Concepts (axes pills / empty + button);
  button idle/pending/error/done states; invalidate the node query on success.
- Files: the three above, `frontend/e2e/extract-concepts.spec.ts` (new).
- SEQUENTIAL (depends on Task 2).

### Negative Constraints

- Do NOT populate any of the nine metadata fields — they are `null`/"N/A"
  placeholders in this story.
- Do NOT change `engine/concepts.py`'s `CONCEPT_FIELDS` set or its save/load.
- Do NOT make extraction background/async — it is synchronous and blocks until done.
- Do NOT re-derive axes when the per-anchor cache is warm (rely on
  `extract_axes_for_document`'s `text_hash` + `axis_cap` cache).
- Do NOT double-append `"axes extracted"` on a cache-hit re-run.
- Do NOT write axes, pills, or the activity entry on a failed extraction (atomic).
- Do NOT touch the cross-links routes or `CrossProfile.concepts` shape.

## Test Scenarios

> Tests inject a fake extractor exactly as `engine/tests/test_arm_g.py` does
> (`monkeypatch.setattr(arm_g, "call_chat", fake_call_chat)` and a fake
> `ws_anchors.build_index`), so no live model is reached.

**Test 1: Extract concepts succeeds (first extraction)**

- Setup: workstream `opres-v2`, node `bcbs-opres-2021` with two stub anchors; fake
  extractor returns axes `["operational resilience testing frequency", "scenario
testing cadence"]` and `["third-party dependency management", "scenario testing
cadence"]`.
- Action: `POST /api/workstreams/opres-v2/nodes/bcbs-opres-2021/extract-concepts`.
- Expected: 200; `concepts.status == "extracted"`; `concepts.axes` is the deduped
  union `["operational resilience testing frequency", "scenario testing cadence",
"third-party dependency management"]`; `recent_activity` ends with
  `{"event": "axes extracted", ...}`; the axes cache file exists under
  `.../opres-v2/axes/axes-bcbs-opres-2021.json`.

**Test 2: Second extraction is a cache hit (fast, unchanged)**

- Setup: run Test 1's success, then replace `call_chat` with a `boom` that raises if
  called (mirrors `test_axis_cache_hit_skips_extraction`).
- Action: `POST .../extract-concepts` again with unchanged anchors.
- Expected: 200; `call_chat` never invoked; `concepts.axes` identical to Test 1;
  `recent_activity` has exactly one `"axes extracted"` entry (no duplicate).

**Test 3: Extraction failure is atomic**

- Setup: node with anchors; fake extractor raises `LLMResponseError`.
- Action: `POST .../extract-concepts`.
- Expected: 502 `EXTRACTION_FAILED` with message "Concept extraction failed";
  subsequent `GET .../nodes/{id}` shows `concepts.status == "not_extracted"`, empty
  `axes`, and NO `"axes extracted"` entry in `recent_activity`.

**Test 4: Node not segmented**

- Setup: a node for which `ws_anchors.build_index` yields no anchors.
- Action: `POST .../extract-concepts`.
- Expected: 409 `NOT_SEGMENTED` with message "Node {node_id} has not been segmented
  into passages"; no cache file, no activity entry.

**Test 5: Node-detail shows four blocks in order with metadata all N/A**

- Setup: node `bcbs-opres-2021`, concepts not yet extracted.
- Action: `GET /api/workstreams/opres-v2/nodes/bcbs-opres-2021`.
- Expected: 200; response keys include `first_order_neighbours`, `recent_activity`,
  `metadata`, `concepts` in that order; `metadata` has all nine `CONCEPT_FIELDS`
  keys, each `null`; `concepts == {"status": "not_extracted", "axes": []}`.

**Test 6: Unknown workstream / node**

- Action: `POST /api/workstreams/nope/nodes/x/extract-concepts` and
  `POST /api/workstreams/opres-v2/nodes/nope/extract-concepts`.
- Expected: 404 `WORKSTREAM_NOT_FOUND` and 404 `NODE_NOT_FOUND` respectively.

**Test 7: `axes_dir` parameter round-trips (arm_g)**

- Setup: `AnchorIndex` with one anchor; stub `call_chat`; pass a `tmp_path` as
  `axes_dir`.
- Action: `extract_axes_for_document(index, "doc-a", axes_dir=tmp_path)`.
- Expected: cache written to `tmp_path/axes-doc-a.json`, NOT under the default
  `AXES_DIR`; a second call from that `axes_dir` is a cache hit.

## Verification

Run the verifier skill to confirm changes are clean.

### Backend API Tests

- `engine/tests/test_api_extract_concepts.py` (new) — Tests 1–4, 6 above, using the
  `TestClient` + `shutil.copytree` fixture from `test_api_node_metadata.py`, a stub
  `ws_anchors.build_index`, and a fake `call_chat` (per `test_arm_g.py`).
- `engine/tests/test_api_node_metadata.py` (additions) — Test 5: four ordered blocks;
  `metadata` all-`null` nine fields; `concepts` `not_extracted` shape.
- `engine/tests/test_arm_g.py` (additions) — Test 7: `axes_dir` parameter round-trip
  without regressing the default-path tests.

### Browser/UI Testing

- URL: `http://localhost:5173/workstreams/opres-v2` (engine on `http://localhost:8000`).
- Steps:
  1. Click the "BCBS OpRes 2021" node → panel opens showing First-order neighbours,
     Recent activity, Metadata, Concepts in that order. Expected: Metadata lists the
     nine fields all "N/A"; Concepts is empty with an "Extract concepts" button.
  2. Click "Extract concepts" → button shows "Extracting…" (disabled). Expected:
     spinner while the call runs.
  3. On success → concept pills appear (e.g. "operational resilience testing
     frequency"); "axes extracted" appears in Recent activity.
  4. Re-open the same node later → pills persist; no re-extraction.

### E2E Tests

| Key Scenario                                 | Test file                               | Assigned sub-task |
| -------------------------------------------- | --------------------------------------- | ----------------- |
| Open a document, extract concepts, see pills | `frontend/e2e/extract-concepts.spec.ts` | Task 3            |

**Locator strategies:** node buttons by role/name (e.g. `getByRole("button", {
name: "BCBS OpRes 2021" })`); the action button by `getByRole("button", { name:
/extract concepts/i })`; concept pills by `data-testid="concept-pill"`; section
headings by `getByRole("heading", { name: /metadata/i })` etc. to assert order.
The Playwright suite (`frontend/playwright.config.ts`, baseURL
`http://localhost:5173`) already exists — add the one new spec.
