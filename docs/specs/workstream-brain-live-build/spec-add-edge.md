# Connect Two Existing Documents

**Ticket:** TBD

This feature lets a policy drafter draw a connection between two documents that
are already on a workstream's canvas, without having to add a new document to do
it. From any node's detail panel the drafter uses "Add edge" to connect the node
they are viewing to another existing document in the same workstream, choosing
one of the four connection types. This unblocks building out a workstream's web
of relationships after documents are already in place, rather than only at the
moment each document is first added.

## User Story

As Aisyah, a policy drafter building a workstream, I want to connect two
documents that are already on my canvas so that I can record how they relate to
one another even after they were added, and set up those pairs for later linkage
analysis.

## Background & Context

**Current state:**

- Documents are added to a workstream one at a time, and each new document must
  be connected to at least one document already on the canvas at the moment it is
  added.
- That "connect while adding" step is the only way a connection is ever created.
- Once a document is on the canvas, there is no way to add a new connection from
  it to another document that is also already there.

**Problem:**

- A drafter often realises two documents relate only after both are on the
  canvas — for example, after adding an international standard and, later, a
  peer-regulator chapter that references it.
- With no way to connect existing documents, the drafter's only workaround is to
  remove and re-add a document just to declare the connection, which is
  destructive and loses the document's prepared passages and concepts.
- Because linkage analysis runs on a connection between two documents, missing
  connections mean pairs the drafter knows are related can never be analysed.

## Target User & Persona

- **Who:** Aisyah R., the policy drafter assembling a policy workstream in the
  Workstream Brain app.
- **Context:** She is mid-build, viewing a document's detail panel on the canvas,
  and recognises that this document relates to another document already in the
  same workstream.
- **Current workaround:** None that is safe — the only option today is removing
  and re-adding a document to re-declare its connections, discarding the work
  already done on it.

## Goals

- Let the drafter start a connection from the node whose detail panel they are
  viewing, using an "Add edge" action.
- Let the drafter choose the other document from those already in the same
  workstream and pick one of the four connection types.
- Show the new connection on the canvas immediately, without running analysis.
- Prevent invalid connections — a document connected to itself, or a connection
  that already exists — with a clear message.

## Non-Goals

- **Running analysis.** Adding a connection only draws the link; finding and
  presenting labelled linkages between the two documents is a separate story.
- **Cross-workstream connections.** A connection can only join two documents in
  the same workstream; connecting documents across two workstreams is out of
  scope for this epic.
- **Editing or removing an existing connection**, or changing its type after it
  is drawn.
- **Connecting to a document not yet on the canvas** — that remains the job of
  the "add a document" flow.

## User Workflow

1. **Viewing a document** — Aisyah has a workstream open with several documents
   on the canvas and clicks a node to open its detail panel; she sees an "Add
   edge" action on the panel.
2. **Starting a connection** — She clicks "Add edge". She is asked to pick the
   other document to connect to, choosing from the other documents already in
   this workstream, and to pick a connection type: supersedes, references,
   contributes-to, or parallel-to.
3. **Confirming** — She confirms the connection.
4. **Seeing the result** — The connection appears on the canvas immediately as a
   link of the chosen type between the two documents, and the detail panel
   reflects the new neighbour. No analysis runs.

## Acceptance Criteria

### Scenario: Connect the viewed document to another existing document

```gherkin
Given I have a workstream open with the documents
  | Document                                              |
  | Operational Resilience PD (working draft)             |
  | BCBS Principles for Operational Resilience 2021       |
  | Bank of England Operational Resilience — Chapter 3    |
  And I am viewing the detail panel for "BCBS Principles for Operational Resilience 2021"
When I choose "Add edge"
  And I select "Bank of England Operational Resilience — Chapter 3" as the other document
  And I choose the connection type "references"
  And I confirm the connection
Then a "references" connection appears on the canvas from "BCBS Principles for Operational Resilience 2021" to "Bank of England Operational Resilience — Chapter 3"
  And the detail panel shows "Bank of England Operational Resilience — Chapter 3" as a neighbour
  And no analysis is run for the new connection
```

### Scenario: Connect an industry-input document to the focal working draft

```gherkin
Given I have a workstream open with the documents
  | Document                                              |
  | Operational Resilience PD (working draft)             |
  | Industry roundtable submission on operational risk    |
  And I am viewing the detail panel for "Industry roundtable submission on operational risk"
When I choose "Add edge"
  And I select "Operational Resilience PD (working draft)" as the other document
  And I choose the connection type "contributes-to"
  And I confirm the connection
Then a "contributes-to" connection appears on the canvas from "Industry roundtable submission on operational risk" to "Operational Resilience PD (working draft)"
  And no analysis is run for the new connection
```

### Scenario Outline: Any of the four connection types can be chosen

```gherkin
Given I have a workstream open with the documents "BCBS Principles for Operational Resilience 2021" and "Bank of England Operational Resilience — Chapter 3"
  And I am viewing the detail panel for "BCBS Principles for Operational Resilience 2021"
When I choose "Add edge"
  And I select "Bank of England Operational Resilience — Chapter 3" as the other document
  And I choose the connection type "<connection type>"
  And I confirm the connection
Then a "<connection type>" connection appears on the canvas from "BCBS Principles for Operational Resilience 2021" to "Bank of England Operational Resilience — Chapter 3"

Examples:
  | connection type |
  | supersedes      |
  | references      |
  | contributes-to  |
  | parallel-to     |
```

### Scenario: Connecting a document to itself is blocked

```gherkin
Given I have a workstream open with the documents "BCBS Principles for Operational Resilience 2021" and "Bank of England Operational Resilience — Chapter 3"
  And I am viewing the detail panel for "BCBS Principles for Operational Resilience 2021"
When I choose "Add edge"
Then "BCBS Principles for Operational Resilience 2021" is not offered as a document I can connect to
  And if I attempt to connect it to itself I am told a document cannot be connected to itself
  And no connection is created
```

### Scenario: Nothing to connect to when the workstream has only the viewed document

```gherkin
Given I have a workstream open whose only document is "Operational Resilience PD (working draft)"
  And I am viewing the detail panel for "Operational Resilience PD (working draft)"
When I choose "Add edge"
Then I am told there are no other documents in this workstream to connect to
  And no connection is created
```

### Scenario: The same connection already exists between the two documents

```gherkin
Given I have a workstream open with the documents "BCBS Principles for Operational Resilience 2021" and "Bank of England Operational Resilience — Chapter 3"
  And a "references" connection already runs from "BCBS Principles for Operational Resilience 2021" to "Bank of England Operational Resilience — Chapter 3"
  And I am viewing the detail panel for "BCBS Principles for Operational Resilience 2021"
When I choose "Add edge"
  And I select "Bank of England Operational Resilience — Chapter 3" as the other document
  And I choose the connection type "references"
  And I confirm the connection
Then I am told this connection already exists between the two documents
  And no duplicate connection is created
  And the existing connection remains on the canvas unchanged
```

### Scenario: A different connection type between the same two documents is allowed

```gherkin
Given I have a workstream open with the documents "BCBS Principles for Operational Resilience 2021" and "Bank of England Operational Resilience — Chapter 3"
  And a "references" connection already runs from "BCBS Principles for Operational Resilience 2021" to "Bank of England Operational Resilience — Chapter 3"
  And I am viewing the detail panel for "BCBS Principles for Operational Resilience 2021"
When I choose "Add edge"
  And I select "Bank of England Operational Resilience — Chapter 3" as the other document
  And I choose the connection type "parallel-to"
  And I confirm the connection
Then a "parallel-to" connection appears on the canvas between the two documents alongside the existing "references" connection
```

### Scenario: A newly added connection is still present after re-opening the workstream

```gherkin
Given I have a workstream open with the documents "BCBS Principles for Operational Resilience 2021" and "Bank of England Operational Resilience — Chapter 3"
  And I added a "references" connection between them from the detail panel
When I leave the workstream and open it again later
Then the "references" connection between the two documents is still on the canvas
```

## Business Rules & Constraints

- A connection is one of exactly four types: supersedes, references,
  contributes-to, or parallel-to. No other type can be chosen.
- The connection is drawn from the document whose detail panel the drafter is
  viewing, to the other document they select.
- The other document must be an existing document in the same workstream; a
  document from a different workstream can never be selected.
- A document cannot be connected to itself; the viewed document is not offered as
  a choice, and any attempt is refused with a clear message.
- If the same connection — the same two documents joined by the same type in the
  same direction — already exists, no duplicate is created and the drafter is
  told it already exists. A connection of a _different_ type between the same two
  documents is allowed and is added alongside the existing one.
- If the workstream contains no other documents, the drafter is told there is
  nothing to connect to and no connection is created.
- Adding a connection never runs analysis; it only draws the link.
- A connection added this way is saved with the workstream so it survives closing
  and re-opening the workstream, consistent with the epic's durable-results rule.

## Success Metrics

- A drafter can connect two documents already on the canvas without removing or
  re-adding either document.
- Connections created this way persist so that a workstream prepared before the
  demo shows every hand-drawn connection intact on the day.
- No duplicate connection (same pair, same type, same direction) is ever created
  through this action.

## Dependencies

- A workstream exists with a focal working-draft node, and at least two documents
  are on the canvas for there to be two documents to connect (the focal node plus
  one added document is enough).
- The four connection types already exist in the product and are reused unchanged.

## Open Questions

- [x] ~~What happens when the drafter tries to create a connection that already
      exists?~~ — **Resolved:** The connection is not duplicated; the drafter is
      told it already exists. A connection of a different type between the same
      two documents is still permitted and is added alongside the existing one.
- [x] ~~Can the drafter connect a document to one in another workstream?~~ —
      **Resolved:** No. Connections join two documents in the same workstream
      only; cross-workstream connection is out of scope for this epic.
- [x] ~~Does adding a connection trigger analysis?~~ — **Resolved:** No. Adding a
      connection only draws the link; analysing it is a separate story.

---

# Technical Design

> Sections below are the implementation-facing enrichment of the business spec
> above. The business content (User Story, Acceptance Criteria, Business Rules)
> is authoritative and is not restated here.

## Functional Requirements

- **New standalone create-edge route.** Add `POST /api/workstreams/{workstream_id}/edges`
  to `engine/api.py`. It creates ONE edge between two nodes that already exist in
  the workstream's `graph.json`. This is a new route: today the only edge creation
  is bundled inside `add_node` (POST `/nodes`), and that bundled behaviour must stay
  unchanged.
- **Reuse persistence helpers.** The route must read via
  `workstreams.load_graph(workstreams_dir, workstream_id)`, append the edge record
  to `graph["edges"]`, and persist via
  `workstreams.save_graph(workstreams_dir, workstream_id, ws_graph)` — the same
  read/append/write shape `create_workstream_node` uses. All writes are UTF-8 (per
  the module docstring).
- **Edge id.** The edge id must be produced by
  `workstreams.make_edge_id(source_id, target_id)` (yielding the on-disk
  `e-{source}--{target}` style with hyphens inside each endpoint turned to
  underscores), so hand-drawn edges are indistinguishable on disk from seeded ones.
- **Edge record shape.** The appended record must match the seeded/`add_node`
  shape exactly: `{"id", "source", "target", "edge_type"}`. No `analysed` /
  `findings_count` key is stored — analysed state stays DERIVED from the presence
  of a findings file (see `workstreams.edge_is_analysed`).
- **Direction convention (must preserve "task is source").** The edge is conceptually
  drawn FROM the viewed node TO the selected node. However, to stay consistent with
  the Task Screen (which lists a task node's OUTGOING edges only) and with
  `add_node`'s seeded convention, the route must decide `source`/`target` as follows:
  if exactly one endpoint is a `task`-type node, the **task node is always the
  `source`** and the other node is the `target` — regardless of which one the drafter
  was viewing. Otherwise (neither endpoint is a task, or — not reachable here — both
  are), the viewed node is the `source` and the selected node is the `target`. This
  mirrors the `node_type_by_id.get(target) == "task"` branch in `add_node`.
- **No analysis on creation.** Creating an edge must NOT run linkage analysis, must
  NOT write a findings file, and must NOT call the finder/critic seam. The new edge
  is returned (and rendered) as unanalysed.
- **Atomicity.** All validation runs before any write. On any rejected request the
  route returns the error and leaves `graph.json` byte-for-byte unchanged (no
  partial append). A single successful request appends exactly one edge and writes
  `graph.json` once.
- **Response.** On success the route returns `201` with the created edge record plus
  `"analysed": false`, matching the `{**edge, "analysed": False}` shape
  `create_workstream_node` returns in its `created_edges`.

### Validation & Business Rules

Validation order in the route (first failure wins), with the concrete outcome:

1. **Workstream exists** — `load_graph` returns `None` → `404 WORKSTREAM_NOT_FOUND`.
2. **Body is an object with the three required string fields** —
   `source_node_id`, `target_node_id`, `edge_type` all present and non-empty →
   else `400 EDGE_REQUIRED`.
3. **Edge type is one of the four** — `edge_type` must be in
   `workstreams.EDGE_TYPES` (`supersedes` / `references` / `contributes-to` /
   `parallel-to`) → else `400 INVALID_EDGE_TYPE`.
4. **Self-loop blocked** — `source_node_id == target_node_id` →
   `400 SELF_LOOP`. (The frontend also omits the viewed node from the target
   picker, so this is a defence-in-depth guard.)
5. **Both nodes exist in THIS workstream's graph** — each id must be present in
   `{n["id"] for n in ws_graph["nodes"]}` → else `404 NODE_NOT_FOUND`. This is the
   only same-workstream check needed: cross-workstream ids simply are not in this
   graph and fail here.
6. **Duplicate refused** — after resolving direction (task-is-source), if an edge
   with the same `(source, target, edge_type)` triple already exists in
   `graph["edges"]`, refuse with `409 DUPLICATE_EDGE`. A _different_ `edge_type`
   between the same ordered pair is allowed and is appended alongside; a same-pair
   same-type edge in the _opposite_ direction is a different `(source, target)`
   ordering and is likewise allowed (it produces a different `make_edge_id`).

## Permissions & Security

- **Scope:** Public workstream API (`/api/workstreams/*`), consistent with every
  other Workstream Brain route. No auth layer exists in the engine; do not add one.
- **Authorization:** None beyond the existing routes. The fixture store is the only
  state.
- **Input validation:**
  - `edge_type` must be a member of `workstreams.EDGE_TYPES` — never trust the
    client string.
  - `source_node_id` and `target_node_id` must each resolve to an existing node id
    in _this_ workstream's `graph.json`; unknown or cross-workstream ids are
    rejected with `404 NODE_NOT_FOUND`, so the route cannot fabricate a dangling
    edge to a node that isn't on the canvas.
  - Request body must be a JSON object; a non-object body is rejected with
    `400 EDGE_REQUIRED` (mirrors the `create_workstream_node` guard).

## API Design

### `POST /api/workstreams/{workstream_id}/edges`

Creates one edge between two existing nodes in the workstream.

**Request:**

```json
{
  "source_node_id": "bcbs-principles-operational-resilience-2021",
  "target_node_id": "bank-of-england-operational-resilience-chapter-3",
  "edge_type": "references"
}
```

**Response (201):**

```json
{
  "id": "e-bcbs_principles_operational_resilience_2021--bank_of_england_operational_resilience_chapter_3",
  "source": "bcbs-principles-operational-resilience-2021",
  "target": "bank-of-england-operational-resilience-chapter-3",
  "edge_type": "references",
  "analysed": false
}
```

**Example — task endpoint forces task-as-source.** Request drawn FROM an
industry-input node TO the working draft:

```json
{
  "source_node_id": "industry-roundtable-submission-operational-risk",
  "target_node_id": "opres-pd-v0-3",
  "edge_type": "contributes-to"
}
```

Because `opres-pd-v0-3` is the `task` node, the persisted record swaps direction so
the task is the source (keeping the edge on the Task Screen's outgoing list):

```json
{
  "id": "e-opres_pd_v0_3--industry_roundtable_submission_operational_risk",
  "source": "opres-pd-v0-3",
  "target": "industry-roundtable-submission-operational-risk",
  "edge_type": "contributes-to",
  "analysed": false
}
```

**Errors:**

| Status | Code                   | Message                                                                 | Condition                                                                   |
| ------ | ---------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | `Workstream {workstream_id} not found`                                  | No `graph.json` for the workstream                                          |
| 400    | `EDGE_REQUIRED`        | `source_node_id, target_node_id and edge_type are required.`            | Body not an object, or any of the three fields missing/empty                |
| 400    | `INVALID_EDGE_TYPE`    | `edge_type must be one of the four structural types, got {edge_type!r}` | `edge_type` not in `EDGE_TYPES`                                             |
| 400    | `SELF_LOOP`            | `A document cannot be connected to itself.`                             | `source_node_id == target_node_id`                                          |
| 404    | `NODE_NOT_FOUND`       | `Node {node_id} not found in workstream {workstream_id}`                | Either endpoint id is absent from this workstream's graph                   |
| 409    | `DUPLICATE_EDGE`       | `A {edge_type} connection already exists between these two documents.`  | An edge with the same resolved `(source, target, edge_type)` already exists |

Error bodies follow the existing `_ws_error` convention: `{"code", "message"}` (with
an optional `field`). `NODE_NOT_FOUND` substitutes the offending `node_id` into the
message so the client can tell which endpoint was unknown.

> **Empty-workstream case (`NO_OTHER_NODES`) is a frontend concern, not a route
> error.** The route always operates on a named target, so "no other nodes to
> connect to" cannot reach it. The dialog handles the empty case client-side (see
> UI/Frontend Requirements) rather than sending a request that would fail.

## UI/Frontend Requirements

### Components

**`NodeDetailPanel`** — `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`

- **Type:** Modify existing.
- **Purpose:** Add an "Add edge" action to the panel footer (the same
  `border-t border-border/60 p-4` footer that today holds "Open task" / "Open
  source"). Clicking it opens the new `AddEdgeDialog`, pre-scoped to the viewed
  node as the connection's origin.
- **New props / state:** Needs the workstream's node list to populate the target
  picker. Two options, pick the one that matches the call site: (a) accept an added
  `nodes: GraphNode[]` prop passed down from the graph page (which already holds the
  graph query), consistent with how `AddNodeDialog` receives `nodes`; or (b) the
  panel opens the dialog and the dialog itself derives candidates. Prefer (a) — pass
  `nodes` in — to avoid a second graph fetch. Add local `const [addEdgeOpen,
setAddEdgeOpen] = useState(false)`.
- **Action button:** Render an "Add edge" `Button` (variant `outline`, `Plus` icon
  from `lucide-react`) in the footer, alongside the existing type-keyed CTA. It is
  present for every node type (task and non-task alike).

**`AddEdgeDialog`** — `frontend/src/features/workstream-graph/AddEdgeDialog.tsx`

- **Type:** New. Mirror `AddNodeDialog.tsx` structure (shadcn `Dialog` +
  `DialogContent` with the `glass` class, controlled `useState`, a single target
  `<select>` and a single edge-type `<select>`, a `useMutation` that invalidates the
  graph query on success). It is a _small_ subset of `AddNodeDialog` — one target,
  one type, no title/URL/attachment fields.
- **Props:**
  ```typescript
  interface AddEdgeDialogProps {
    workstreamId: string;
    /** The node whose panel opened this dialog — the connection's origin. */
    sourceNode: { id: string; title: string };
    /** All nodes in the workstream; the picker excludes `sourceNode.id`. */
    nodes: GraphNode[];
    open: boolean;
    onOpenChange: (open: boolean) => void;
  }
  ```
- **Behaviour:**
  - Target `<select>` lists `nodes.filter((n) => n.id !== sourceNode.id)` by
    `title` — the viewed node is never offered (enforces the self-loop rule at the
    UI, matching the "not offered as a choice" acceptance criterion).
  - Edge-type `<select>` offers the four types, reusing the
    `EDGE_TYPE_OPTIONS` constant pattern from `AddNodeDialog`.
  - Confirm button ("Add connection") stays disabled until a target and a type are
    both chosen, and while the mutation is pending.
  - On success: `queryClient.invalidateQueries({ queryKey: ["workstream",
workstreamId, "graph"] })` (same key `AddNodeDialog` invalidates), then reset
    and close so the new link appears on the canvas immediately.
  - The mutation calls the new `createEdge(workstreamId, body)` in `api.ts`.

### `api.ts` / `types.ts`

- **`frontend/src/lib/api.ts`** — add:
  ```typescript
  export function createEdge(
    workstreamId: string,
    body: CreateEdgeRequest,
  ): Promise<CreateEdgeResponse> {
    return postJson<CreateEdgeResponse>(
      `${API_BASE}/api/workstreams/${workstreamId}/edges`,
      body,
    );
  }
  ```
- **`frontend/src/lib/types.ts`** — add:
  ```typescript
  export interface CreateEdgeRequest {
    source_node_id: string;
    target_node_id: string;
    edge_type: EdgeType;
  }
  export interface CreateEdgeResponse {
    id: string;
    source: string;
    target: string;
    edge_type: EdgeType;
    analysed: boolean;
  }
  ```

### User Interactions

- Click "Add edge" in the node detail panel footer → the `AddEdgeDialog` opens with
  the viewed document fixed as the origin.
- Pick a target document + a connection type, click "Add connection" → the dialog
  closes, the graph query refetches, and the new link renders on the canvas; the
  panel's first-order neighbours now include the connected node.
- If the workstream has only the viewed node, the dialog shows the empty state and
  offers no confirm (no request is sent).

### States

- **Loading:** While the create mutation is pending, the confirm button shows
  "Adding connection…" and is disabled (mirrors `AddNodeDialog`'s pending label).
- **Empty:** When `nodes.filter((n) => n.id !== sourceNode.id).length === 0`, the
  dialog body shows "There are no other documents in this workstream to connect to."
  and hides/disables the confirm button — no request is issued (the `NO_OTHER_NODES`
  case is handled entirely client-side).
- **Error:** On a `409 DUPLICATE_EDGE` (or any non-2xx), surface the server
  `message` inline in the dialog (e.g. "A references connection already exists
  between these two documents.") and keep the dialog open so the drafter can pick a
  different type or target. The graph is not refetched on error.

## Architecture Notes

- **New dependencies:** None. Backend reuses `load_graph`/`save_graph`/`make_edge_id`/
  `EDGE_TYPES`/`_ws_error`; frontend reuses shadcn `Dialog`, TanStack Query, and the
  existing `postJson` client.
- **Dependencies & integration:** The new edge lands in the same `graph.json`
  read by `get_workstream_graph`, `get_workstream_node_detail`, and the Task Screen,
  so a hand-drawn edge shows on the canvas, in the panel's first-order neighbours,
  and (when a task endpoint is involved) on the Task Screen's outgoing list — all via
  the existing derived-`analysed` projection. No shared client state beyond the
  `["workstream", {id}, "graph"]` query key. No breaking changes: `add_node` and its
  POST `/nodes` route are untouched.
- **Persistence:** Legacy-path note — this reads/writes `data/workstreams/`, NOT
  `data/artifacts/`; no `engine.build` rebuild is involved (avoids the artifact-
  narrowing blocker).

## Exemplar Files

- `engine/api.py` — `create_workstream_node` (~1060) is the closest existing
  graph-mutating route: `load_graph` → validate → append → `save_graph` → `201`
  with `{**edge, "analysed": False}`. `get_workstream_node_detail` (~955) and the
  `_ws_error` helper (~302) show the `{code, message}` error contract to copy.
- `engine/workstreams.py` — `make_edge_id` (~376), `load_graph`/`save_graph`
  (~70/76), `EDGE_TYPES` (~43), and the task-is-source branch inside `add_node`
  (~440) that the new direction logic mirrors.
- `frontend/src/features/workstream-graph/AddNodeDialog.tsx` — the modal to mirror
  (target `<select>`, edge-type `<select>`, `useMutation` + `invalidateQueries` on
  the graph key).
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx` — the footer where
  the "Add edge" button lives.
- `frontend/src/lib/api.ts` (`createNode` ~169) and `frontend/src/lib/types.ts`
  (`CreateNodeRequest`/`CreatedEdge` ~254) — the client contract to extend.
- `engine/tests/test_api_workstreams.py` — POST `/nodes` tests (~255) are the test
  pattern for the new route.

## Implementation Plan

### Sub-tasks

**Task 1: Backend create-edge route + validation** — _small_ (<100 LOC)

- Files: `engine/api.py` (new `create_workstream_edge` route), `engine/workstreams.py`
  (optionally a small `validate_edge_create` / `resolve_edge_direction` helper +
  duplicate check, next to `validate_node_create`/`make_edge_id`).
- Adds `POST /api/workstreams/{workstream_id}/edges`: load graph, validate (order
  above), resolve task-is-source direction, refuse duplicates with `409`, append via
  `make_edge_id`, `save_graph`, return `201`.
- INDEPENDENT.

**Task 2: Frontend client contract** — _small_ (<100 LOC)

- Files: `frontend/src/lib/api.ts` (`createEdge`), `frontend/src/lib/types.ts`
  (`CreateEdgeRequest`, `CreateEdgeResponse`).
- INDEPENDENT (contract mirrors Task 1's API design; can be written in parallel).

**Task 3: `AddEdgeDialog` + `NodeDetailPanel` wiring** — _medium_ (100–300 LOC)

- Files: `frontend/src/features/workstream-graph/AddEdgeDialog.tsx` (new),
  `frontend/src/features/workstream-graph/NodeDetailPanel.tsx` (modify — footer
  button + `nodes` prop + open state), and the caller that renders `NodeDetailPanel`
  (pass `nodes` down, e.g. `WorkstreamGraphPage`).
- SEQUENTIAL (depends on Task 2 for `createEdge` / the request+response types).

**Task 4: E2E happy path** — _small_ (<100 LOC)

- Files: `frontend/e2e/add-edge.spec.ts` (new).
- SEQUENTIAL (depends on Tasks 1–3 wired end-to-end and the engine + Vite app
  running).

### Negative Constraints

- Do NOT change `add_node` or the POST `/api/workstreams/{workstream_id}/nodes`
  route — the bundled add-node-and-its-edges behaviour stays exactly as is.
- Do NOT run linkage analysis, write a findings file, or call the finder/critic
  seam on edge creation.
- Do NOT support cross-workstream edges — both endpoints must be in the same
  workstream's graph; out-of-scope endpoints fail as `NODE_NOT_FOUND`.
- Do NOT add an edit/delete-edge route or a way to change an edge's type — out of
  scope for this story.
- Do NOT rebuild `data/artifacts/` (this feature only touches
  `data/workstreams/`).
- Do NOT introduce a new dependency, form library, or state manager.

## Test Scenarios

All against workstream `opres-v2`. Node ids below use the seeded fixture ids
(`opres-pd-v0-3` is the task node; `bcbs-opres-2021` and `fsb-3rd-party` are
anchors) — see `engine/tests/test_api_workstreams.py`.

**Test 1: Happy path — connect two existing anchors (201)**

- Setup: `opres-v2` graph with `bcbs-opres-2021` and `fsb-3rd-party` as anchors and
  no `references` edge between them.
- Action: `POST /api/workstreams/opres-v2/edges` with
  `{"source_node_id": "bcbs-opres-2021", "target_node_id": "fsb-3rd-party",
"edge_type": "references"}`.
- Expected: `201`; body `{"id": "e-bcbs_opres_2021--fsb_3rd_party", "source":
"bcbs-opres-2021", "target": "fsb-3rd-party", "edge_type": "references",
"analysed": false}`; reloading `graph.json` shows the new edge; the edge is NOT
  analysed (no findings file written).

**Test 2: Task-is-source direction preserved (201)**

- Setup: `opres-v2` graph.
- Action: `POST …/edges` with `{"source_node_id": "bcbs-opres-2021",
"target_node_id": "opres-pd-v0-3", "edge_type": "contributes-to"}` (task named as
  the _target_).
- Expected: `201`; persisted record has `source == "opres-pd-v0-3"` and
  `target == "bcbs-opres-2021"` (task swapped to source); the edge appears on the
  Task Screen's outgoing neighbours for `opres-pd-v0-3`.

**Test 3: Self-loop blocked (400 SELF_LOOP)**

- Setup: `opres-v2` graph; count edges before.
- Action: `POST …/edges` with `{"source_node_id": "bcbs-opres-2021",
"target_node_id": "bcbs-opres-2021", "edge_type": "references"}`.
- Expected: `400`, `code == "SELF_LOOP"`, message "A document cannot be connected to
  itself."; `graph.json` edge count unchanged.

**Test 4: Duplicate refused (409 DUPLICATE_EDGE)**

- Setup: create a `references` edge from `bcbs-opres-2021` to `fsb-3rd-party` (Test 1),
  then repeat the identical request.
- Action: second `POST …/edges` with the same triple.
- Expected: `409`, `code == "DUPLICATE_EDGE"`; only one such edge exists in
  `graph.json` (no duplicate appended).

**Test 5: Different type between same pair allowed (201)**

- Setup: a `references` edge from `bcbs-opres-2021` to `fsb-3rd-party` already exists.
- Action: `POST …/edges` with the same pair but `"edge_type": "parallel-to"`.
- Expected: `201`; both the `references` and the `parallel-to` edge now exist between
  the pair in `graph.json`.

**Test 6: Unknown node rejected (404 NODE_NOT_FOUND)**

- Setup: `opres-v2` graph; count edges before.
- Action: `POST …/edges` with `{"source_node_id": "bcbs-opres-2021",
"target_node_id": "ghost-node", "edge_type": "references"}`.
- Expected: `404`, `code == "NODE_NOT_FOUND"`, message names `ghost-node`;
  `graph.json` unchanged. (A cross-workstream id fails identically here.)

**Test 7: Invalid edge type rejected (400 INVALID_EDGE_TYPE)**

- Setup: `opres-v2` graph.
- Action: `POST …/edges` with `"edge_type": "differs-on"` (a finding label, not a
  structural edge type).
- Expected: `400`, `code == "INVALID_EDGE_TYPE"`; `graph.json` unchanged.

**Test 8: Unknown workstream (404 WORKSTREAM_NOT_FOUND)**

- Setup: none.
- Action: `POST /api/workstreams/nope/edges` with a valid body.
- Expected: `404`, `code == "WORKSTREAM_NOT_FOUND"`.

**Test 9: Missing required field (400 EDGE_REQUIRED)**

- Setup: `opres-v2` graph.
- Action: `POST …/edges` with `{"source_node_id": "bcbs-opres-2021", "edge_type":
"references"}` (no `target_node_id`).
- Expected: `400`, `code == "EDGE_REQUIRED"`; `graph.json` unchanged.

## Acceptance Criteria

- [ ] `POST /api/workstreams/{id}/edges` returns the documented responses for all
      Test Scenarios above (201 happy path, task-source swap, and every error code).
- [ ] Self-loop, duplicate (same pair + same type + same direction), unknown-node,
      invalid-type, and unknown-workstream cases are each refused with the exact
      `{code, message}` shown, and `graph.json` is left unchanged on every refusal.
- [ ] A different edge type between the same pair is accepted alongside the existing
      edge.
- [ ] No analysis runs and no findings file is written on edge creation.
- [ ] The `NodeDetailPanel` footer shows an "Add edge" action; the dialog excludes
      the viewed node from the target picker and shows the empty-state message when
      there are no other nodes.
- [ ] On success the graph query invalidates and the new link renders on the canvas.
- [ ] No type errors or lint warnings (frontend `tsc`; backend mypy baseline
      unchanged — do not add `# type: ignore`).

## Verification

Run the verifier skill to confirm changes are clean.

### Backend API Tests

Add to `engine/tests/test_api_workstreams.py` (or a new `engine/tests/test_api_add_edge.py`
following the same `_make_client(tmp_path)` / `_graph_on_disk(dst)` helpers), one test
per Test Scenario above, named in the established style:

- `test_POST_edge_creates_edge_between_two_existing_nodes_201`
- `test_POST_edge_task_endpoint_becomes_source`
- `test_POST_edge_rejects_self_loop_400_SELF_LOOP`
- `test_POST_edge_rejects_duplicate_409_DUPLICATE_EDGE`
- `test_POST_edge_allows_different_type_same_pair_201`
- `test_POST_edge_rejects_unknown_node_404_NODE_NOT_FOUND`
- `test_POST_edge_rejects_invalid_edge_type_400_INVALID_EDGE_TYPE`
- `test_POST_edge_unknown_workstream_404_WORKSTREAM_NOT_FOUND`
- `test_POST_edge_rejects_missing_field_400_EDGE_REQUIRED`

Each refusal test must also assert the on-disk edge count is unchanged, mirroring the
`before = len(_graph_on_disk(dst)["edges"])` pattern used by the POST `/nodes` tests.
Run with `.venv/Scripts/python.exe -m pytest engine/tests` (Windows) or the repo's
venv pytest; the forge verify hook false-fails on pyenv/ruff — ignore that per the
recorded blocker.

### Browser/UI Testing

- URL: `http://localhost:5173/workstreams/opres-v2` (Vite dev server;
  `VITE_API_BASE` → the running engine on `http://localhost:8000`).
- Setup: start the engine and `npm run dev` in `frontend/`.
- Steps:
  1. Click the `BCBS OpRes 2021` node → the detail panel opens. **Expect** an
     "Add edge" action in the panel footer.
  2. Click "Add edge" → a dialog opens. **Expect** the target picker lists the
     other documents but NOT "BCBS OpRes 2021" itself.
  3. Pick another document + connection type "references", click "Add connection".
     **Expect** the dialog closes and a new "references" link renders on the canvas
     between the two nodes; the panel's first-order neighbours now include the
     connected document.
  4. Re-open "Add edge", pick the same target + same "references" type, confirm.
     **Expect** an inline "already exists" message and no new link.
  5. Open a workstream whose only document is the working draft, click "Add edge".
     **Expect** the empty-state message and no confirm action.

### E2E Tests

| Key Scenario                                             | Test file                       | Assigned sub-task |
| -------------------------------------------------------- | ------------------------------- | ----------------- |
| Connect the viewed document to another existing document | `frontend/e2e/add-edge.spec.ts` | Task 4            |

The E2E maps ONLY the happy-path "connect two existing documents" flow (Playwright,
`baseURL http://localhost:5173`, engine + Vite running — see
`frontend/e2e/workstream-graph.spec.ts` and `frontend/e2e/README.md`). Pure-backend
error cases (self-loop, duplicate, unknown node, invalid type) are covered by the
Backend API Tests above and are NOT duplicated in E2E.

**Locator strategies:** reuse the role-based selectors from
`workstream-graph.spec.ts` — `page.goto("/workstreams/opres-v2")`,
`getByRole("button", { name: "BCBS OpRes 2021" })` to open the panel,
`getByRole("button", { name: /add edge/i })` to open the dialog, the target/type
`<select>`s via their `aria-label`s (mirror `AddNodeDialog`'s "Edge N target" /
"Edge N type" labelling — e.g. `aria-label="Connection target"` /
`aria-label="Connection type"`), and `getByRole("button", { name: /add connection/i })`
to confirm; assert a new `svg` edge/link appears after confirmation.
