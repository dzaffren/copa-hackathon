# Focal Working-Draft Node on Workstream Creation

**Ticket:** TBD

When a policy drafter creates a new workstream, the workstream opens with a
single focal working-draft node already at the centre of the canvas. This node
represents the drafter's own working draft — the thing they are drafting — and
is the anchor that every document added later connects to. It solves today's
problem of landing on a blank canvas with nothing to attach documents to.

## User Story

As a policy drafter, I want a newly created workstream to open with a focal
working-draft node already at the centre of the canvas, so that I have an anchor
to connect my first source document to and can start building the workstream
immediately instead of facing an empty canvas.

## Background & Context

**Current state:**

- Creating a workstream captures a name, description, deliverable type and
  target delivery, then opens an empty canvas with no starting node.
- The drafter lands on a blank graph with nothing to attach documents to.
- Adding a document requires connecting it to at least one node that already
  exists, but on a blank canvas there is no such node — so the very first
  document cannot be added.

**Problem:**

- The drafter cannot begin assembling a workstream: with no node present, the
  "one connection is required to add a document" rule can never be satisfied for
  the first document.
- The workstream has no notion of which node is its centre, so later connections
  have no agreed anchor to read from.
- This blocks the entire build-it-yourself flow the hackathon demo depends on.

## Target User & Persona

- **Who:** Aisyah R., a Bank Negara Malaysia policy drafter working on a draft
  under active development.
- **Context:** At the very start of a new piece of policy work, when she opens
  the app and creates a fresh workstream for the draft she is about to build up.
- **Current workaround:** None. Today she creates the workstream and is stranded
  on an empty canvas; the demo has relied on pre-seeded example workstreams that
  are being removed.

## Goals

- Open every newly created workstream with exactly one focal working-draft node
  at the centre of the canvas.
- Give that focal node an identity drawn from the workstream itself — its title
  reflects the workstream name and deliverable type.
- Record which node is the workstream's focal node, so later connections have a
  known anchor to read from.
- Make it possible to add the first document immediately, by giving it a node to
  connect to.

## Non-Goals

- **Attaching a document to the focal node.** The focal node starts with no
  document; documents are added later as separate nodes. Adding documents is a
  separate story.
- **Breaking documents into passages, extracting concepts, or running analysis.**
  Those belong to their own stories and are unavailable on the empty focal node.
- **Connecting documents to one another.** Drawing connections between existing
  documents is a separate story; this story only establishes the anchor.
- **Cross-workstream anchoring.** The focal node anchors one workstream only.

## User Workflow

1. **Create the workstream** — Aisyah names a new workstream (for example
   "Operational Resilience PD v0.3"), writes a short description, picks its
   deliverable type (PD) and target delivery (Q4 2026), and creates it.
2. **Land on the anchored canvas** — Instead of a blank canvas, the workstream
   opens with a single focal working-draft node centred in the view. Its title
   reflects the workstream she just named.
3. **Recognise it as her working draft** — The node is clearly marked as the
   working draft (the task she is drafting) and sits at the centre as the anchor
   for everything to come.
4. **Start building** — Aisyah clicks to add her first document and connects it
   to the focal node, which is available to connect to from the moment the
   workstream opens.

## Acceptance Criteria

### Scenario: Workstream opens with a focal working-draft node at the centre

```gherkin
Given Aisyah is creating a new workstream
  And she names it "Operational Resilience PD v0.3"
  And she gives it a short description
  And she chooses the deliverable type "PD"
  And she sets the target delivery to "Q4 2026"
When she creates the workstream
Then the workstream opens showing a single node on the canvas
  And that node is a working-draft node representing her own draft
  And that node is positioned at the centre of the graph view
  And no other nodes are present on the canvas
```

### Scenario: The focal node's title reflects the workstream name and type

```gherkin
Given Aisyah has created a workstream named "Open Finance ED response" with deliverable type "ED"
When the workstream opens
Then the focal working-draft node's title reflects the workstream name "Open Finance ED response"
  And the node reflects its deliverable type "ED"
```

### Scenario: The workstream knows which node is its focal node

```gherkin
Given Aisyah has created a workstream named "Climate Risk DP"
When the workstream opens
Then the workstream identifies its single working-draft node as the focal node
  And later connections use that focal node as their anchor
```

### Scenario: The focal node starts with no document

```gherkin
Given Aisyah has created a workstream named "Operational Resilience PD v0.3"
When the workstream opens and she opens the focal working-draft node
Then the node shows that no document is attached to it
  And this is presented as the expected starting state, not as an error
```

### Scenario: Analysis is unavailable on the empty focal node

```gherkin
Given the focal working-draft node has no document attached
When Aisyah opens the focal node to review it
Then running linkage analysis is not offered on the focal node
  And she is not shown an error
  And she understands analysis becomes possible only once documents are added and connected
```

### Scenario: The drafter can immediately add a document that connects to the focal node

```gherkin
Given Aisyah's newly created workstream "Operational Resilience PD v0.3" has opened with its focal node centred
When she chooses to add her first document
Then the focal working-draft node is available for the new document to connect to
  And she can add the document by connecting it to the focal node
  And the requirement that a new document connect to at least one existing node is satisfied by the focal node
```

### Scenario: Only one focal node is created per workstream

```gherkin
Given Aisyah has created a new workstream
When the workstream opens
Then exactly one focal working-draft node is present
  And creating the workstream does not produce additional working-draft nodes
```

### Scenario Outline: Focal node reflects the chosen deliverable type

```gherkin
Given Aisyah creates a workstream named "<name>" with deliverable type "<type>"
When the workstream opens
Then a single focal working-draft node appears at the centre
  And its title reflects the workstream name "<name>"
  And it reflects the deliverable type "<type>"
  And it has no document attached

Examples:
  | name                            | type  |
  | Operational Resilience PD v0.3  | PD    |
  | Open Finance ED response        | ED    |
  | Climate Risk DP                 | DP    |
  | Supervisory Notes compilation   | Other |
```

## Business Rules & Constraints

- **Exactly one focal node.** Every newly created workstream opens with exactly
  one focal working-draft node; none more, none fewer.
- **Focal node is the centre and the anchor.** The focal node sits at the centre
  of the graph, and every connection added later reads from the focal node
  outward, consistent with the epic's "focal node is the anchor" rule.
- **Identity comes from the workstream.** The focal node's title reflects the
  workstream's name and its deliverable type; the drafter does not name the
  focal node separately. For example, a workstream "Climate Risk DP" opens with
  a focal working-draft node titled after it and marked as a DP.
- **No document at the start.** The focal node has no document attached. This is
  the expected state, not an error, and it means the focal node cannot be
  analysed until documents are added and connected.
- **Unblocks the first document.** Because a document can only be added by
  connecting it to a node that already exists, the focal node is what the first
  added document connects to.

## Success Metrics

- 100% of newly created workstreams open with a single focal working-draft node
  centred on the canvas, with none opening on a blank canvas.
- A drafter can add their first document immediately after creating a workstream,
  with no case where the first document cannot be added for lack of a node to
  connect to.
- The focal node's title matches the workstream name and deliverable type in
  every created workstream.

## Dependencies

- The workstream creation step, which already captures the name, description,
  deliverable type and target delivery that the focal node draws its identity
  from.
- Removal of the outdated seeded example workstreams (in progress), so the
  build-it-yourself flow starting from the focal node is the sole path.

## Open Questions

- [x] ~~Does the focal node need its own document?~~ — **Resolved:** No. The
      focal node starts empty; documents are added as separate nodes that
      connect to it, as agreed in the epic overview.
- [x] ~~Who names the focal node?~~ — **Resolved:** No one names it separately.
      Its title is drawn from the workstream's name and deliverable type.
- [x] ~~How many focal nodes does a workstream have?~~ — **Resolved:** Exactly
      one per workstream, created when the workstream is created.

---

## Functional Requirements

- **Focal node creation is part of the create operation.** The existing create
  path — `engine/workstreams.py::create_workstream`, reached via
  `POST /api/workstreams` — today writes `workstream.json` with
  `primary_task_id: None` and an empty `graph.json` (`{"nodes": [], "edges": []}`).
  This story changes that single operation to also seed exactly one focal node
  in `graph.json` and set `primary_task_id` to that node's id.
- **Node type must be `task`.** The focal node's `node_type` must be `"task"` —
  the one type the whole app treats as the focal/working-draft node.
  `primary_task_id` (`engine/workstreams.py:134`), `primary_subgraph`
  (`:147`), and the Task Screen all key off `node_type == "task"`; any other
  type would leave the workstream with no discoverable focal node.
- **Title derives from the workstream identity.** The focal node's `title` must
  be composed from the workstream `name` (already captured on the create form
  and in the create body) and the deliverable type code (`PD`/`ED`/`DP`/`Other`)
  in the form `"{name} ({type})"` — e.g. `"Operational Resilience PD v0.3 (PD)"`.
  The node id must come from `make_node_id(title, existing_ids)`
  (`engine/workstreams.py:365`); `existing_ids` is empty at create time, so the
  id is the slug of the title (e.g. `operational-resilience-pd-v0-3-pd`).
- **No document attached.** The focal node must NOT carry a `document_id`. The
  edge-detail route's `analysable` flag (`engine/api.py:1053`) requires both
  endpoints to have distinct `document_id`s, so an absent `document_id` keeps the
  focal node non-analysable — the expected empty starting state, not an error.
- **`primary_task_id` points at the focal node.** `workstream.json`'s
  `primary_task_id` must equal the seeded focal node's id (no longer `None`), so
  the graph route (`GET /api/workstreams/{id}/graph`) centres on it and later
  connections read from it as anchor.
- **Atomicity.** `workstream.json` and `graph.json` are written together in the
  same `create_workstream` call, as they are today. If either write fails
  (`OSError`), the route already returns `500 WORKSTREAM_WRITE_FAILED`; a
  half-written workstream is the pre-existing failure mode and is not widened
  here.
- **Idempotency / uniqueness.** Each `POST /api/workstreams` scaffolds a new
  workstream directory (colliding slugs are suffixed, `make_workstream_id`,
  `engine/workstreams.py:293`). Exactly one focal node is created per create
  call — never more, never fewer.

### Validation & Business Rules

- All existing create-body validation is preserved unchanged
  (`validate_workstream_create`, `engine/workstreams.py:241`), checked before any
  node is seeded: `NAME_REQUIRED`, `NAME_TOO_SHORT`, `NAME_TOO_LONG`,
  `DESCRIPTION_TOO_LONG`, `TARGET_PUBLICATION_TOO_LONG`,
  `INVALID_DELIVERABLE_TYPE`, `INVALID_ACCESS`, plus `INVALID_REVIEWER_ID` from
  the route. A rejected body seeds NO focal node and writes nothing on disk
  (existing `test_POST_a_rejected_body_writes_nothing` still holds).
- The deliverable type is one of `PD`/`ED`/`DP`/`Other` (`DELIVERABLE_TYPES`,
  `engine/workstreams.py:227`). The focal node title uses the code as passed in
  the body, while `workstream.json`'s `deliverable_type` remains the human label
  ("Policy Document") the fixtures store.
- A workstream whose name slugifies to nothing (pure punctuation) still yields a
  valid focal node id: `make_node_id` falls back to `slugify`'s default `"node"`
  fragment.

## API Design

### `POST /api/workstreams`

Unchanged request contract — the create form's field set is NOT altered.

**Request:**

```json
{
  "name": "Operational Resilience PD v0.3",
  "description": "Draft PD on operational resilience, targeting Q4 2026.",
  "deliverable_type": "PD",
  "target_publication": "Q4 2026",
  "reviewer_ids": ["fm", "ps"],
  "access": "team_only"
}
```

**Response (201):** the returned record now carries a non-null `primary_task_id`
pointing at the seeded focal node.

```json
{
  "id": "operational-resilience-pd-v0-3",
  "name": "Operational Resilience PD v0.3",
  "deliverable_type": "Policy Document",
  "role": "own",
  "description": "Draft PD on operational resilience, targeting Q4 2026.",
  "primary_task_id": "operational-resilience-pd-v0-3-pd",
  "target_publication": "Q4 2026",
  "owner": { "id": "ar", "name": "Aisyah R." },
  "reviewers": [
    { "id": "fm", "name": "Farid M." },
    { "id": "ps", "name": "Priya S." }
  ],
  "access": "team_only",
  "created_at": "2026-07-27T09:15:00Z"
}
```

The seeded focal node is written to
`data/workstreams/operational-resilience-pd-v0-3/graph.json`:

```json
{
  "nodes": [
    {
      "id": "operational-resilience-pd-v0-3-pd",
      "node_type": "task",
      "title": "Operational Resilience PD v0.3 (PD)",
      "description": "Draft PD on operational resilience, targeting Q4 2026.",
      "source_url": null
    }
  ],
  "edges": []
}
```

The immediately-following graph read
(`GET /api/workstreams/operational-resilience-pd-v0-3/graph`) then returns the
one-node subgraph with `primary_task_id` set:

```json
{
  "workstream_id": "operational-resilience-pd-v0-3",
  "primary_task_id": "operational-resilience-pd-v0-3-pd",
  "nodes": [
    {
      "id": "operational-resilience-pd-v0-3-pd",
      "node_type": "task",
      "title": "Operational Resilience PD v0.3 (PD)"
    }
  ],
  "edges": []
}
```

**A second concrete example** (Discussion Paper): `POST` with
`{"name": "Climate Risk DP", "deliverable_type": "DP", "access": "team_only"}`
yields `id: "climate-risk-dp"`, `primary_task_id: "climate-risk-dp-dp"`, and a
focal node titled `"Climate Risk DP (DP)"`. **A third** (Other): `{"name":
"Supervisory Notes compilation", "deliverable_type": "Other", "access":
"team_only"}` yields `primary_task_id: "supervisory-notes-compilation-other"`
and title `"Supervisory Notes compilation (Other)"`.

**Errors:** (unchanged — all pre-date this story and must still hold)

| Status | Code                          | Condition                                                         |
| ------ | ----------------------------- | ----------------------------------------------------------------- |
| 400    | `NAME_REQUIRED`               | `name` missing or blank after trim                                |
| 400    | `NAME_TOO_SHORT`              | `name` shorter than 3 characters                                  |
| 400    | `NAME_TOO_LONG`               | `name` longer than 120 characters                                 |
| 400    | `DESCRIPTION_TOO_LONG`        | `description` longer than 500 characters                          |
| 400    | `TARGET_PUBLICATION_TOO_LONG` | `target_publication` longer than 60 characters                    |
| 400    | `INVALID_DELIVERABLE_TYPE`    | `deliverable_type` not one of `PD`/`ED`/`DP`/`Other`              |
| 400    | `INVALID_ACCESS`              | `access` not one of `team_only`/`department_wide`                 |
| 400    | `INVALID_REVIEWER_ID`         | a `reviewer_ids` entry is not a nominable colleague (incl. owner) |
| 500    | `WORKSTREAM_WRITE_FAILED`     | `workstream.json`/`graph.json` write raised `OSError`             |

## Architecture Notes

- **New dependencies:** none. The change lives entirely inside the existing
  create path and its helpers.
- **Dependencies & integration:** The graph route
  (`GET /api/workstreams/{id}/graph`) and `primary_subgraph` already centre on
  the `task` node and clip to its one-hop subgraph; with a single node and no
  edges they return that node alone — no route change needed. The node-detail
  route (`GET /api/workstreams/{id}/nodes/{node_id}`, `engine/api.py:955`) reads
  the node as-is; a focal node without `document_id`/concepts renders the empty
  starting state. The frontend `GraphCanvas` already centres the task node and
  `NewWorkstreamPage` already navigates to `/workstreams/{id}` on success, so no
  frontend source change is required for centring.
- **Breaking changes:** `primary_task_id` moves from always-`None` on a fresh
  workstream to always-set. The existing test
  `test_POST_new_workstream_is_immediately_loadable_by_the_graph_route` asserts
  `primary_task_id is None` and an empty `nodes`/`edges`; it must be updated to
  the new contract (one node, `primary_task_id` set) — this is a deliberate
  contract change, not a regression.

## Exemplar Files

- `engine/workstreams.py` — `create_workstream` (`:310`) is the function to
  modify; follow its existing `_write_json` UTF-8 writes, its `record` shape, and
  reuse `make_node_id` (`:365`), `slugify` (`:352`), and the `add_node` node dict
  shape (`:426`, `id`/`node_type`/`title`/`description`/`source_url`) as the
  template for the seeded node — WITHOUT calling `add_node` (see Negative
  Constraints).
- `engine/api.py` — `create_workstream_route` (`:662`) is the route; the
  `analysable` derivation at `:1053` explains why a `document_id`-less focal node
  stays non-analysable.
- `engine/tests/test_api_new_workstream.py` — the test module to extend; follow
  its `_make_client`/`_create` helpers and `tmp_path` fixture-store isolation.
- `frontend/src/features/new-workstream/NewWorkstreamPage.tsx` — the create form;
  confirms the field set and the post-success `navigate(/workstreams/{id})`.
- `frontend/e2e/workstream-graph.spec.ts` — the Playwright pattern (Playwright
  `test`/`expect`, `page.goto`, `svg circle` count) for the new E2E spec.

## Implementation Plan

### Sub-tasks

**Task 1: Seed a focal `task` node in `create_workstream`** — _small_ (<100 LOC)

- Files: `engine/workstreams.py`
- In `create_workstream`, before writing files: build the focal node title as
  `f"{name} ({body['deliverable_type']})"`, derive `node_id =
make_node_id(title, set())`, construct the node dict
  (`id`/`node_type: "task"`/`title`/`description`/`source_url: None`, NO
  `document_id`), set `record["primary_task_id"] = node_id`, and write
  `graph.json` as `{"nodes": [node], "edges": []}` instead of the empty graph.
- INDEPENDENT

**Task 2: Update backend tests for the seeded focal node** — _small_ (<100 LOC)

- Files: `engine/tests/test_api_new_workstream.py`
- Update `test_POST_new_workstream_is_immediately_loadable_by_the_graph_route`
  and `test_POST_writes_workstream_json_and_an_empty_graph` (rename the latter)
  to the new contract, and add the new assertions from Test Scenarios below.
- SEQUENTIAL (depends on Task 1)

**Task 3: E2E — workstream opens with focal node centred** — _small_ (<100 LOC)

- Files: `frontend/e2e/new-workstream-focal-node.spec.ts`
- Create a workstream via the form, then assert the graph canvas shows exactly
  one node whose label reflects the entered name. No frontend source change is
  expected; if the canvas fails to centre or render the single node, that is a
  finding to raise, not to fix here.
- SEQUENTIAL (depends on Task 1)

### Negative Constraints

- Do NOT change the create form's field set or `CreateWorkstreamRequest`/
  `CreateWorkstreamResponse` shapes — `primary_task_id` already exists on both.
- Do NOT touch `add_node` (`engine/workstreams.py:417`) or its validation; the
  focal node is seeded directly in `create_workstream`, not via the add-node path
  (which requires ≥1 edge and would reject a node with none).
- Do NOT alter `primary_subgraph` (`:147`), `primary_task_id` (`:134`), or the
  graph route's projection — they already handle a one-node, zero-edge graph.
- Do NOT attach a `document_id`, concepts, or any analysis to the focal node.
- Do NOT rebuild `data/artifacts/` or re-seed existing fixtures.

## Test Scenarios

**Test 1: A created workstream's graph has exactly one focal `task` node**

- Setup: `TestClient` over a `tmp_path` copy of `data/workstreams`
  (`_make_client`); `_create(client)` with the VALID body
  (name "Climate Risk PD v2 · 2026", `deliverable_type` "PD").
- Action: `POST /api/workstreams`, then read
  `tmp_path/workstreams/{id}/graph.json`.
- Expected: `graph["nodes"]` has length 1; the single node has
  `node_type == "task"`; `graph["edges"] == []`.

**Test 2: `primary_task_id` equals the seeded node id**

- Setup: as Test 1.
- Action: `POST /api/workstreams`; read both the 201 body and
  `workstream.json`.
- Expected: `body["primary_task_id"]` is not `None`, equals
  `workstream.json`'s `primary_task_id`, and equals the sole node's `id`
  in `graph.json`.

**Test 3: Focal node title reflects name + deliverable type**

- Setup: `_create(client, name="Open Finance ED response",
deliverable_type="ED")`.
- Action: `POST /api/workstreams`; read `graph.json`.
- Expected: the node `title == "Open Finance ED response (ED)"`; the node id
  `== "open-finance-ed-response-ed"`.

**Test 4: Focal node carries no document**

- Setup: `_create(client, deliverable_type="DP", name="Climate Risk DP")`.
- Action: `POST /api/workstreams`; read `graph.json`.
- Expected: `"document_id" not in node`; a follow-up
  `GET /api/workstreams/{id}/nodes/{node_id}` returns `200` with the node and no
  fabricated document.

**Test 5: Graph route centres on the focal node immediately after create**

- Setup: `_create(client, name="Operational Resilience PD v0.3")`.
- Action: `GET /api/workstreams/{id}/graph`.
- Expected: `200`; `len(body["nodes"]) == 1`; `body["primary_task_id"]` equals
  that node's id; `body["edges"] == []`.

**Test 6: Exactly one focal node — deliverable-type outline**

- Setup: for each `(name, type)` in the Scenario Outline
  (`Operational Resilience PD v0.3`/PD, `Open Finance ED response`/ED,
  `Climate Risk DP`/DP, `Supervisory Notes compilation`/Other).
- Action: `POST /api/workstreams`; read `graph.json`.
- Expected: exactly one node, `node_type == "task"`, title ends with `({type})`,
  no `document_id`.

**Test 7: A rejected body seeds no focal node (guard)**

- Setup: `_create(client, name="")` (fails `NAME_REQUIRED`).
- Action: `POST /api/workstreams`.
- Expected: `400`; no new directory under `tmp_path/workstreams` (existing
  `test_POST_a_rejected_body_writes_nothing` still passes).

## Acceptance Criteria

- [ ] `POST /api/workstreams` returns `201` with a non-null `primary_task_id`.
- [ ] The new workstream's `graph.json` holds exactly one `task` node with no
      `document_id`, and no edges.
- [ ] `workstream.json`'s `primary_task_id` equals the seeded node's id.
- [ ] The focal node title reflects the workstream name + deliverable type code.
- [ ] All pre-existing create validation/error behaviour is unchanged.
- [ ] No type errors or new lint warnings (mypy third-party baseline aside).

## Verification

Run the verifier skill to confirm changes are clean.

### Backend API Tests

- `engine/tests/test_api_new_workstream.py` — add the seven Test Scenarios above.
  Update the two existing tests that assert the old empty-graph /
  `primary_task_id is None` contract
  (`test_POST_writes_workstream_json_and_an_empty_graph`,
  `test_POST_new_workstream_is_immediately_loadable_by_the_graph_route`) to the
  new one-focal-node contract. Follow the module's `_make_client`/`_create`
  helpers and `tmp_path` fixture-store isolation (no writes to the committed
  `data/workstreams/`). Run with
  `.venv/Scripts/python.exe -m pytest engine/tests/test_api_new_workstream.py`
  (per the forge-verify learning; the Stop hook's LINT FAIL is cosmetic here).

### Browser/UI Testing

- URL: `http://localhost:5173` (Vite dev), engine on `http://localhost:8000`
  (`VITE_API_BASE`).
- Steps:
  1. Navigate to `/` → click "New workstream". Expected: the create form opens.
  2. Enter name "Operational Resilience PD v0.3", deliverable type "PD", target
     "Q4 2026"; click "Create workstream". Expected: the app navigates to
     `/workstreams/operational-resilience-pd-v0-3`.
  3. Expected: the graph shows a single node centred, labelled after the name,
     and no other nodes.
  4. Click the focal node. Expected: the detail panel opens with no document /
     no analysis offered, presented as the starting state (no error).
  5. Click "Add node". Expected: the add-node dialog can target the focal node,
     satisfying the "≥1 edge to an existing node" rule for the first document.

### E2E Tests

| Key Scenario                                               | Test file                                        | Assigned sub-task |
| ---------------------------------------------------------- | ------------------------------------------------ | ----------------- |
| Workstream opens with a focal working-draft node at centre | `frontend/e2e/new-workstream-focal-node.spec.ts` | Task 3            |

- The Playwright framework exists at `frontend/e2e/` (baseURL
  `http://localhost:5173`; see `frontend/e2e/workstream-graph.spec.ts` and
  `frontend/e2e/README.md`). The new spec creates a workstream through the form
  and asserts the graph canvas renders exactly one node centred with a label
  reflecting the entered name.
- **Locator strategies:** name input via `page.getByLabel("Workstream name")`;
  deliverable via `page.getByLabel("Deliverable type")`; submit via
  `page.getByRole("button", { name: /create workstream/i })`; the focal node via
  `page.getByRole("button", { name: /operational resilience pd v0\.3/i })`;
  node count via `page.locator("svg circle")` expecting count `1`.
