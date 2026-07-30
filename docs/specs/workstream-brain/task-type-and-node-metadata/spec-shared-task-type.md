# One Shared Vocabulary of Deliverable Kinds

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Task Type & Editable Node Metadata — Overview](spec.md)

The tool currently describes deliverable kinds two different ways — a four-option list when a workstream is created, and a seven-option list inside the Copilot — and the two disagree. This story replaces both with one vocabulary of eight kinds, asks for it once when a working draft is created, and shows it wherever that draft appears.

## User Story

As Aisyah R., I want to record what kind of deliverable I am producing once, from a list that covers every deliverable BNM actually publishes, so that the tool knows what I am working on without asking me again.

## Background & Context

**Current state:**

- Creating a workstream asks for a deliverable kind and offers four options: Policy Document, Exposure Draft, Discussion Paper, and Other. The working draft is named after the choice, so a new Open Finance response becomes "Open Finance ED response (ED)".
- The Copilot panel asks the same question with a different, seven-option list: Policy Document, Discussion Paper, Exposure Draft, FAQ, Engagement Deck, Feedback Template for Industry, and Peer Benchmarking.
- Adding any other document to a graph asks what kind of thing it is structurally — an international standard, an act or law, industry input, a supervisory letter, a peer regulator's guidance, an internally published document, or other — and it is possible to add a further working draft this way. Nothing asks what kind of deliverable a working draft is.
- Opening a document shows its type as a badge, alongside its issuer and a short descriptor where one exists.

**Problem:**

- **A drafter producing an FAQ cannot say so.** Neither can one producing an engagement deck, a feedback template for industry, or a peer benchmarking exercise. All four are deliverables the Copilot already recognises, but the workstream form forces them all into "Other" — so four distinct kinds of work become indistinguishable the moment they are recorded.
- **The two lists disagreeing means neither can be trusted.** Aisyah answers the question at creation, and the Copilot asks it again from a different list with a different default, which is why the third story in this epic is possible at all.
- **A working draft added to an existing graph records nothing.** Aisyah can add a second working draft to a workstream — an engagement deck accompanying her policy document — and the tool captures only that it is a working draft, not what kind.

## Target User & Persona

- **Who:** Aisyah R., policy drafter at Bank Negara Malaysia, responsible for a workstream from announcement through to sign-off.
- **Context:** At the very start of a drafting cycle, when a new deliverable is announced and she sets up its workstream; and later in the cycle, when she adds a further deliverable to a workstream that already exists.
- **Current workaround:** She records anything that is not a policy document, exposure draft, or discussion paper as "Other", and re-answers the deliverable-kind question in the Copilot each session.

## Goals

- Offer one list of eight deliverable kinds everywhere the tool asks.
- Cover every deliverable BNM actually publishes, so no drafter is forced into "Other" for a kind of work the tool already understands.
- Ask for the kind whenever a working draft is created — at workstream creation and when adding one to an existing graph — and require an answer.
- Show the recorded kind wherever the working draft appears.

## Non-Goals

- **Changing a kind after it is chosen.** It is set once and thereafter read-only.
- **Asking published context documents for a kind.** Standards, acts, peer guidance, industry input, and supervisory letters are not deliverables Aisyah is producing.
- **Changing how documents are classified structurally.** The existing eight-way classification — working draft, internally published, international standard, peer regulator, act or law, industry input, supervisory letter, other — is unchanged. Deliverable kind is a second, separate question asked only of working drafts.

## User Workflow

1. **A new deliverable is announced.** The Deputy Governor asks for an FAQ to accompany the RMiT policy document. Aisyah opens the new-workstream form.
2. **She names it and picks its kind.** She types "RMiT FAQ" and chooses "FAQ" from the deliverable list — an option that did not previously exist.
3. **The workstream appears.** Its working draft sits on the canvas named "RMiT FAQ (FAQ)", and opening it shows FAQ as its deliverable kind.
4. **Later, she adds a second deliverable.** The same workstream needs an engagement deck for the industry briefing. She adds it as a working draft; the form asks what kind of deliverable it is and will not let her add it until she answers. She picks "Engagement Deck".
5. **She adds context documents.** She attaches the RMiT policy document, the Basel principles, and an industry submission. None of them asks for a deliverable kind.

## Acceptance Criteria

### Scenario: Creating a workstream for a deliverable kind the tool could not previously express

```gherkin
Given I am creating a new workstream
When I name it "RMiT FAQ"
  And I choose "FAQ" as the deliverable kind
  And I submit the form
Then the workstream is created
  And its working draft is named "RMiT FAQ (FAQ)"
  And opening that working draft shows "FAQ" as its deliverable kind
```

### Scenario Outline: Every deliverable kind is offered and recorded

```gherkin
Given I am creating a new workstream named <name>
When I choose <kind> as the deliverable kind
  And I submit the form
Then its working draft is named <draft name>
  And opening that working draft shows <kind> as its deliverable kind

Examples:
  | name                          | kind                           | draft name                                |
  | "Operational Resilience PD"   | "PD — Policy Document"          | "Operational Resilience PD (PD)"          |
  | "Climate Risk DP"             | "DP — Discussion Paper"         | "Climate Risk DP (DP)"                    |
  | "Open Finance ED response"    | "ED — Exposure Draft"           | "Open Finance ED response (ED)"           |
  | "RMiT FAQ"                    | "FAQ"                           | "RMiT FAQ (FAQ)"                          |
  | "OpRes Industry Briefing"     | "Engagement Deck"               | "OpRes Industry Briefing (DECK)"          |
  | "OpRes Feedback Form"         | "Feedback Template for Industry"| "OpRes Feedback Form (FEEDBACK)"          |
  | "MAS Technology Risk Scan"    | "Peer Benchmarking"             | "MAS Technology Risk Scan (BENCHMARK)"    |
  | "Supervisory Notes"           | "Others"                        | "Supervisory Notes (OTHERS)"              |
```

### Scenario: Adding a second working draft to an existing workstream

```gherkin
Given I am working in the "RMiT FAQ" workstream
When I add a new document
  And I classify it as a working draft
  And I choose "Engagement Deck" as its deliverable kind
  And I give it a title, attach a document, and link it to the working draft
  And I add it to the graph
Then it appears on the canvas
  And opening it shows "Engagement Deck" as its deliverable kind
```

### Scenario: A working draft cannot be added without a deliverable kind

```gherkin
Given I am adding a new document to a workstream
  And I have classified it as a working draft
  And I have given it a title, attached a document, and linked it to an existing document
When I have not chosen a deliverable kind
Then I cannot add it to the graph
  And I can see that a deliverable kind is required
```

### Scenario: Published context documents are never asked for a deliverable kind

```gherkin
Given I am adding a new document to a workstream
When I classify it as <classification>
Then I am not asked for a deliverable kind
  And I can add it to the graph once I have a title, a document, and a link

Examples:
  | classification           |
  | "international standard" |
  | "act or law"             |
  | "peer regulator"         |
  | "industry input"         |
  | "supervisory letter"     |
  | "internally published"   |
  | "others"                 |
```

### Scenario: Switching classification away from working draft drops the question

```gherkin
Given I am adding a new document
  And I have classified it as a working draft and chosen "FAQ" as its deliverable kind
When I change its classification to "international standard"
Then I am no longer asked for a deliverable kind
  And I can add it to the graph without one
```

### Scenario: A deliverable kind cannot be changed once set

```gherkin
Given the "RMiT FAQ" working draft was created as an FAQ
When I open it and view its regulatory profile
Then I can see "FAQ" recorded as its deliverable kind
  And I cannot change it, even while editing the rest of the profile
```

### Scenario: A drafter who is not yet sure has a truthful answer

```gherkin
Given I have been asked to compile some supervisory notes
  And I do not yet know what they will become
When I create the workstream and choose "Others" as the deliverable kind
Then the workstream is created
  And its working draft shows "Others" as its deliverable kind
```

## Business Rules & Constraints

- **The vocabulary is exactly these eight kinds, in this order:** PD — Policy Document, DP — Discussion Paper, ED — Exposure Draft, FAQ, Engagement Deck, Feedback Template for Industry, Peer Benchmarking, Others. The same list appears everywhere the tool asks or displays a deliverable kind.
- **Each kind has a short form** used inside automatically generated names: `PD`, `DP`, `ED`, `FAQ`, `DECK`, `FEEDBACK`, `BENCHMARK`, `OTHERS`.
- **"Other" becomes "Others".** The previous four-option list's "Other" is replaced by "Others" so a single spelling is used throughout. A workstream already recorded as "Other" continues to display exactly as it does today; nothing is rewritten behind the drafter's back.
- **A deliverable kind is mandatory for a working draft.** The new-workstream form and the add-document form both refuse to proceed without one, in the same way the add-document form already refuses without a title, a document, or a link.
- **A deliverable kind is permanent.** There is no way for a drafter to change it after creation.
- **A deliverable kind is offered only for working drafts.** Choosing any other classification removes the question, and a kind chosen before switching classification is discarded.
- **Automatically generated names use the short form; drafter-typed names are never touched.** The tool appends the short form only to the working-draft name it generates from the workstream name.
- **One existing workstream is backfilled: `open-finance-pd-2026`.** Its working draft is recorded as `PD`. Every other pre-existing working draft is being retired and is left alone.

## Success Metrics

- Every working draft created from now on has a deliverable kind recorded — so the Copilot never has to ask.
- A drafter producing an FAQ, an engagement deck, a feedback template, or a peer benchmarking exercise can say so exactly, without selecting "Others".

## Dependencies

- None. This story is independent of the editable regulatory profile, and is a prerequisite for the Copilot story.

## Open Questions

- [x] ~~Should the longer kinds carry a short form, or should names embed the full label?~~ — **Resolved:** short forms. "OpRes Feedback (FEEDBACK)" is readable where the full label is not.
- [x] ~~Should existing workstreams recorded as "Other" be rewritten to "Others"?~~ — **Resolved:** no. They display as they always have; only the option offered to drafters going forward changes. Rewriting stored records for a spelling change is churn with no benefit to the drafter.
- [x] ~~Where does `task_type` live on disk — the node, or the node's concepts side-file?~~ — **Resolved:** the node in `graph.json`. It is structural like `node_type` (the title suffix and the graph badge derive from it) and permanent, whereas the side-file holds the mutable nine-field profile. One field, one home.

---

## Functional Requirements

- **Vocabulary:** `TASK_TYPES` must be a single ordered code→label mapping in `engine/workstreams.py`, mirrored as `TASK_TYPE_OPTIONS` in `frontend/src/lib/types.ts`. It replaces `DELIVERABLE_TYPES` (`engine/workstreams.py`) and `INTENTS` (`engine/copilot.py`) — both names are deleted, not aliased.
- **Storage split (unchanged convention):** `workstream.json` stores the human **label** (`"Policy Document"`), because `list_workstreams` projects it to the sidebar and `HomePage.tsx` renders it raw. `graph.json` nodes store the **code** (`"PD"`), because the title suffix and the detail badge derive from it.
- **Validation:** `validate_node_create` must reject a `task` node with a missing or out-of-vocabulary `task_type` (`400 INVALID_TASK_TYPE`), and reject a non-task node that carries `task_type` at all (`400 TASK_TYPE_NOT_ALLOWED`) rather than silently dropping it — a client sending it has misunderstood the contract.
- **Ordering:** the `task_type` check runs immediately after the existing `node_type` check and before `doc_class`, so the response points at the topmost problem on the form (the existing convention in `validate_node_create`).
- **Immutability:** no route accepts a `task_type` change. `add_node` and `create_workstream` are the only writers. The metadata route in the sibling story must reject it (`400 TASK_TYPE_IMMUTABLE`).
- **Atomicity:** unchanged from today — `add_node` mutates the in-memory graph and `save_graph` writes once. `task_type` is set in the same dict literal as `node_type`, so a validation failure means nothing is written.
- **Idempotency:** unchanged — `POST /nodes` is not idempotent today (a repeated call adds a second node with a collision-suffixed id) and this story does not alter that.

### Validation & Business Rules

- `task_type` ∈ `{PD, DP, ED, FAQ, DECK, FEEDBACK, BENCHMARK, OTHERS}`; anything else → `400 INVALID_TASK_TYPE`, field `task_type`.
- `task_type` required when `node_type == "task"`; absent → `400 INVALID_TASK_TYPE` with message `"Choose what kind of deliverable this is."`.
- `task_type` present when `node_type != "task"` → `400 TASK_TYPE_NOT_ALLOWED`, field `task_type`.
- `deliverable_type` on `POST /api/workstreams` accepts the same eight codes; `"Other"` is no longer accepted (`400 INVALID_DELIVERABLE_TYPE`). The frontend never sends it once `TASK_TYPE_OPTIONS` replaces `DELIVERABLE_TYPE_OPTIONS`.
- Focal-node title stays `f"{name} ({code})"` — unchanged logic, wider code set.

## Permissions & Security

- **Scope:** internal demo API, no auth anywhere in this service; unchanged by this story.
- **Input validation:** `task_type` is checked against a closed frozenset before use, so it can never reach a file path or a template. It is rendered as text only — no `dangerouslySetInnerHTML` on this path.
- **Path safety:** unchanged. `task_type` never contributes to a filename; node ids still come from `make_node_id`.

## API Design

### `POST /api/workstreams/{workstream_id}/nodes`

Extends the existing route. Multipart when an attachment rides along (`payload` part + `attachment`), plain JSON otherwise.

**Request (task node):**

```json
{
  "node_type": "task",
  "task_type": "DECK",
  "title": "OpRes Industry Briefing",
  "description": "Slides for the 14 August industry engagement session.",
  "doc_class": "prose",
  "edges": [
    {
      "target_node_id": "open-finance-pd-2026-pd",
      "edge_type": "references"
    }
  ]
}
```

**Response (201):**

```json
{
  "id": "opres-industry-briefing",
  "node_type": "task",
  "task_type": "DECK",
  "title": "OpRes Industry Briefing",
  "created_edges": [
    {
      "id": "e-opres_industry_briefing--open_finance_pd_2026_pd",
      "source": "opres-industry-briefing",
      "target": "open-finance-pd-2026-pd",
      "edge_type": "references",
      "analysed": false
    }
  ],
  "document_id": "opres-industry-briefing",
  "doc_class": "prose",
  "anchor_count": 12
}
```

**Errors (new):**

| Status | Code                    | Condition                                                            |
| ------ | ----------------------- | -------------------------------------------------------------------- |
| 400    | `INVALID_TASK_TYPE`     | `node_type` is `task` and `task_type` is missing or not one of the 8 |
| 400    | `TASK_TYPE_NOT_ALLOWED` | `task_type` supplied on a node whose `node_type` is not `task`       |

Existing errors on this route (`INVALID_NODE_TYPE`, `INVALID_DOC_CLASS`, `EDGE_REQUIRED`, `INVALID_EDGE_TARGET`, `ATTACHMENT_REQUIRED`, `INGEST_FAILED`, `CHUNKING_FAILED`, `NO_PASSAGES`) are unchanged.

### `POST /api/workstreams`

Unchanged shape; the accepted `deliverable_type` set widens from 4 codes to 8.

**Request:**

```json
{
  "name": "RMiT FAQ",
  "deliverable_type": "FAQ",
  "description": "FAQ accompanying the RMiT policy document.",
  "target_publication": "Q4 2026",
  "reviewer_ids": ["fm"],
  "access": "team_only"
}
```

**Response (201)** — `deliverable_type` echoes the **label**, as today:

```json
{
  "id": "rmit-faq",
  "name": "RMiT FAQ",
  "deliverable_type": "FAQ",
  "role": "own",
  "primary_task_id": "rmit-faq-faq",
  "target_publication": "Q4 2026",
  "owner": { "id": "ar", "name": "Aisyah R." },
  "reviewers": [{ "id": "fm", "name": "Farid M." }],
  "access": "team_only",
  "created_at": "2026-07-29T04:15:00Z"
}
```

Note the focal node id is `rmit-faq-faq` — `make_node_id` slugifies the title `"RMiT FAQ (FAQ)"`. This is existing behaviour, not new.

**Errors:** `400 INVALID_DELIVERABLE_TYPE` now fires for `"Other"` as well as for `"Manifesto"`.

### `GET /api/workstreams/{workstream_id}/nodes/{node_id}`

Gains one top-level key. `null` for a non-task node, and for a legacy task node that carries none.

```json
{
  "id": "rmit-faq-faq",
  "node_type": "task",
  "task_type": "FAQ",
  "title": "RMiT FAQ (FAQ)",
  "issuer": null,
  "short_type": null,
  "description": "FAQ accompanying the RMiT policy document.",
  "source_url": null,
  "ismp_classification": null,
  "pursuant_to": null,
  "first_order_neighbours": [],
  "recent_activity": [],
  "metadata": {
    "status": "placeholder",
    "message": "Concept extraction not enabled in MVP1"
  },
  "concepts": { "status": "not_extracted", "axes": [] },
  "second_order_neighbours": {
    "status": "placeholder",
    "message": "N/A in demo"
  }
}
```

`task_type` is inserted directly after `node_type` in the response dict. `test_node_detail_orders_the_four_blocks_and_stubs_metadata` asserts the order of the four _blocks_ only, so this is safe.

## Data Model & Migrations

No database. Fixture files under `data/workstreams/` are the store.

**Node shape (`data/workstreams/{ws}/graph.json` → `nodes[]`)** — one new optional key:

| Field       | Type             | Constraints                                            | Description                         |
| ----------- | ---------------- | ------------------------------------------------------ | ----------------------------------- |
| `task_type` | string \| absent | One of the 8 codes. Present iff `node_type == "task"`. | The deliverable kind. Written once. |

### Migration Notes

- **Backfill exactly one file:** `data/workstreams/open-finance-pd-2026/graph.json` — add `"task_type": "PD"` to the `open-finance-pd-2026-pd` node. Its `workstream.json` already reads `"deliverable_type": "Policy Document"`, so no change there.
- **Do not backfill** `opres-v2`, `rmit-v2-2025`, `open-finance-ed`, or `_cross`. Those working drafts are being retired.
- The engine test fixtures under `engine/tests/` build their own graphs inline; those that create a `task` node need `task_type` added only where they exercise the create/detail routes (see Test Scenarios).

## UI/Frontend Requirements

### Components

**`AddNodeDialog`** — `frontend/src/features/workstream-graph/AddNodeDialog.tsx`

- **Type:** Modify existing
- **Purpose:** add a conditional "Task type" radio grid, shown only when `nodeType === "task"`.
- **State:** `const [taskType, setTaskType] = useState<TaskTypeCode | null>(null)`
- **Placement:** immediately after the existing "Node type" grid, before "Title".
- **Markup:** mirror the existing node-type grid exactly — `role="radiogroup" aria-label="Task type"`, one `role="radio"` button per option with `aria-label={code}` and the label as visible text. No colour dots (those encode node type).
- **Gating:** extend `canSubmit` — `title.trim() && completeEdges.length > 0 && attachment !== null && (nodeType !== "task" || taskType !== null)`.
- **Reset:** `reset()` sets `taskType` back to `null`; switching `nodeType` away from `task` also clears it, so a stale choice cannot be submitted.
- **Payload:** include `task_type` in the `createNode` body only when `nodeType === "task"`.
- **Error copy:** add `INVALID_TASK_TYPE: "Choose what kind of deliverable this is."` and `TASK_TYPE_NOT_ALLOWED: "Only a working draft carries a deliverable kind."` to `ERROR_COPY`; ring the grid red when `errorField === "task_type"`, matching the `doc_class` treatment.

**`NewWorkstreamPage`** — `frontend/src/features/new-workstream/NewWorkstreamPage.tsx`

- **Type:** Modify existing
- **Purpose:** the existing `<select aria-label="Deliverable type">` maps over `TASK_TYPE_OPTIONS` instead of `DELIVERABLE_TYPE_OPTIONS`. Eight options; default stays `"PD"`. No structural change.

**`NodeDetailPanel`** — `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`

- **Type:** Modify existing
- **Purpose:** render the deliverable kind as a chip beside the existing `node_type` badge, using the human label. Renders only when `node.task_type` is set.
- **Markup:** a `<span>` in the existing badge row carrying `data-testid="task-type-chip"`, styled with the primary-tint classes already used for the ISMP badge.

### User Interactions

- Select "task" as node type → a required "Task type" grid appears; "Add to graph" stays disabled until a kind is picked.
- Select any other node type → the grid disappears and any pick is discarded; "Add to graph" gates as it does today.
- Open a task node → its deliverable kind shows as a chip in the header.
- Open a non-task node → no chip.

### States

- **Loading / Error:** unchanged — both screens keep their current handling.
- **Empty:** not applicable; the grid always has all eight options.

## Architecture Notes

- **New dependencies:** none.
- **Dependencies & integration:** `TASK_TYPES` is imported by `engine/api.py` (validation + detail projection) and read by the Copilot story. Deleting `copilot.INTENTS` is a breaking change to the `POST .../copilot` request contract — that is the sibling story's job, and until it lands `_parse_copilot_request` must keep validating against the new eight-code set so the two stories can merge in either order.
- **Breaking change:** `deliverable_type: "Other"` is rejected after this story. The only sender is this app's own form, and `data/workstreams/` holds no workstream recorded as `"Other"` (all four read `"Policy Document"` or `"Exposure Draft"`), so nothing on disk breaks.

## Exemplar Files

- `frontend/src/features/workstream-graph/AddNodeDialog.tsx` — the node-type radio grid is the pattern the task-type grid copies verbatim (radiogroup + `aria-label` per radio + `cn()` selected styling).
- `engine/workstreams.py::validate_node_create` — the ordered `(status, code, message)` early-return validation style, and `DOC_CLASSES` as the closed-frozenset precedent.
- `engine/api.py::create_workstream_route` — how a `(code, message, field)` validation failure becomes a `field`-carrying JSON error body.
- `frontend/src/features/workstream-graph/AddNodeDialog.test.tsx` — Vitest + MSW conventions for this dialog, including how `errorField` ringing is asserted.

## Implementation Plan

### Sub-tasks

**Task 1: introduce `TASK_TYPES` in the engine and retire the two old enums** — _small_

- Files: `engine/workstreams.py` (add `TASK_TYPES`, delete `DELIVERABLE_TYPES`, point `validate_workstream_create` and `create_workstream` at the new map), `engine/copilot.py` (delete `INTENTS`), `engine/api.py` (`_parse_copilot_request` validates against `workstreams.TASK_TYPES`)
- INDEPENDENT

**Task 2: validate and persist `task_type` on add-node; project it on node detail** — _small_

- Files: `engine/workstreams.py` (`validate_node_create`, `add_node`), `engine/api.py` (node-detail projection)
- SEQUENTIAL (depends on Task 1 for `TASK_TYPES`)

**Task 3: write `task_type` onto the focal node at workstream creation** — _small_

- Files: `engine/workstreams.py` (`create_workstream` — add `"task_type": body["deliverable_type"]` to `focal_node`)
- SEQUENTIAL (depends on Task 1)

**Task 4: engine tests** — _medium_

- Files: `engine/tests/test_api_add_node_chunking.py`, `engine/tests/test_api_new_workstream.py`, `engine/tests/test_api_workstreams.py`, `engine/tests/test_copilot.py` (drop the `INTENTS`-has-seven assertion), `engine/tests/test_api_drafting.py` (intent cases follow the widened set)
- SEQUENTIAL (depends on Tasks 2 and 3)

**Task 5: frontend types + the two forms + the detail chip** — _medium_

- Files: `frontend/src/lib/types.ts` (add `TaskTypeCode`, `TASK_TYPE_OPTIONS`; delete `DeliverableTypeCode`, `DELIVERABLE_TYPE_OPTIONS`, `CopilotIntent`, `COPILOT_INTENTS`, `COPILOT_INTENT_LABELS`; add `task_type` to `NodeDetail` and `CreateNodeRequest`), `frontend/src/features/workstream-graph/AddNodeDialog.tsx`, `frontend/src/features/new-workstream/NewWorkstreamPage.tsx`, `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`
- SEQUENTIAL (depends on Task 2 for the wire contract)

**Task 6: frontend tests + MSW handlers** — _medium_

- Files: `frontend/src/test/msw/handlers.ts`, `frontend/src/features/workstream-graph/AddNodeDialog.test.tsx`, `frontend/src/features/new-workstream/NewWorkstreamPage.test.tsx`, `frontend/src/features/workstream-graph/NodeDetailPanel.test.tsx`
- SEQUENTIAL (depends on Task 5)

**Task 7: backfill the one surviving fixture** — _small_

- Files: `data/workstreams/open-finance-pd-2026/graph.json`
- INDEPENDENT

**Task 8: E2E for the add-a-working-draft flow** — _small_

- Files: `frontend/e2e/add-task-node.spec.ts`
- SEQUENTIAL (depends on Tasks 5 and 7)

### Negative Constraints

- Do NOT alter the 8-value `NODE_TYPES` or the 3-value `EDGE_TYPES` vocabularies (`contributes-to` was retired on 29 Jul 2026 — do not reintroduce it). `task_type` is a second, orthogonal question.
- Do NOT add `task_type` to `engine/concepts.py::CONCEPT_FIELDS`. The profile side-file stays nine fields; `task_type` lives on the node.
- Do NOT rewrite `deliverable_type` in any existing `workstream.json`.
- Do NOT backfill `task_type` into `opres-v2`, `rmit-v2-2025`, `open-finance-ed`, or `_cross`.
- Do NOT introduce react-hook-form, zod, or a shadcn `RadioGroup` — both forms use plain controlled state and native inputs by deliberate decision (see the `NewWorkstreamPage` docstring).
- Do NOT rename any node, or add renaming behaviour, when a deliverable kind is recorded.
- Do NOT touch `engine/connections.py` or the five-label finding taxonomy.

## Test Scenarios

**Test 1: a task node is created with its deliverable kind**

- Setup: `open-finance-pd-2026` fixture copied to `tmp_path`
- Action: `POST /api/workstreams/open-finance-pd-2026/nodes` with `{"node_type": "task", "task_type": "DECK", "title": "OpRes Industry Briefing", "doc_class": "prose", "edges": [{"target_node_id": "open-finance-pd-2026-pd", "edge_type": "references"}]}` plus a small text attachment
- Expected: `201`; body `task_type == "DECK"`; the persisted node in `graph.json` carries `"task_type": "DECK"`

**Test 2: a task node without a deliverable kind is refused**

- Setup: same
- Action: same request with `task_type` omitted
- Expected: `400`, code `INVALID_TASK_TYPE`, field `task_type`, message `"Choose what kind of deliverable this is."`; `graph.json` node count unchanged

**Test 3: an out-of-vocabulary kind is refused**

- Setup: same
- Action: same request with `"task_type": "Manifesto"`
- Expected: `400 INVALID_TASK_TYPE`; no node written

**Test 4: a non-task node carrying a deliverable kind is refused**

- Setup: same
- Action: `{"node_type": "international-standard", "task_type": "PD", ...}`
- Expected: `400 TASK_TYPE_NOT_ALLOWED`, field `task_type`

**Test 5: a non-task node without one is accepted (regression)**

- Setup: same
- Action: `{"node_type": "international-standard", "title": "BCBS OpRes 2021", "doc_class": "semi-structured", ...}` + attachment
- Expected: `201`; persisted node has no `task_type` key

**Test 6: validation order puts `node_type` before `task_type`**

- Setup: none (unit test on `validate_node_create`)
- Action: body with both an invalid `node_type` and a missing `task_type`
- Expected: returns `INVALID_NODE_TYPE`, not `INVALID_TASK_TYPE`

**Test 7: every one of the eight codes round-trips through workstream creation**

- Setup: empty `tmp_path` workstreams dir
- Action: parametrized `POST /api/workstreams` over `PD, DP, ED, FAQ, DECK, FEEDBACK, BENCHMARK, OTHERS`
- Expected: `201` each; `graph.json` focal node carries the code as `task_type`; title ends `({code})`; `workstream.json` stores the label

**Test 8: the retired `"Other"` code is refused**

- Setup: empty `tmp_path`
- Action: `POST /api/workstreams` with `"deliverable_type": "Other"`
- Expected: `400 INVALID_DELIVERABLE_TYPE`, field `deliverable_type`

**Test 9: node detail projects the kind, and `null` where there is none**

- Setup: `open-finance-pd-2026` fixture with the backfilled `"task_type": "PD"`
- Action: `GET .../nodes/open-finance-pd-2026-pd`, then `GET .../nodes/bis-papers-168`
- Expected: first returns `task_type == "PD"`; second returns `task_type is None`

**Test 10: the four ordered blocks survive the new key**

- Setup: `open-finance-pd-2026` fixture
- Action: `GET .../nodes/open-finance-pd-2026-pd`
- Expected: the `first_order_neighbours → recent_activity → metadata → concepts` key order still holds

## Acceptance Criteria

- [ ] `POST /nodes` and `POST /api/workstreams` accept and persist all eight codes
- [ ] A task node cannot be created without a deliverable kind; a non-task node cannot carry one
- [ ] `GET /nodes/{id}` returns `task_type`, `null` where absent
- [ ] `DELIVERABLE_TYPES`, `DELIVERABLE_TYPE_OPTIONS`, `INTENTS`, `COPILOT_INTENTS`, and `COPILOT_INTENT_LABELS` no longer exist anywhere in the repo
- [ ] `open-finance-pd-2026`'s working draft carries `"task_type": "PD"`; no other fixture is touched
- [ ] `pytest engine/tests` green; `npm run test` green in `frontend/`
- [ ] `mypy engine/` shows no new warnings beyond the accepted 4-warning third-party-stub baseline
- [ ] No type errors or lint warnings

## Verification

Run the verifier skill to confirm changes are clean. Build in the main working tree, not a worktree — `.venv` and `frontend/node_modules` exist only there (see `docs/learnings/blocker-forge-build-run-in-main-worktree.md`).

### Backend API Tests

| File                                         | Covers                                                                                          |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `engine/tests/test_api_add_node_chunking.py` | Tests 1–6 — create-node validation and persistence                                              |
| `engine/tests/test_api_new_workstream.py`    | Tests 7–8 — the eight codes through workstream creation, `"Other"` refused                      |
| `engine/tests/test_api_workstreams.py`       | Tests 9–10 — node-detail projection and block ordering                                          |
| `engine/tests/test_copilot.py`               | Replace `test_intents_tuple_has_the_seven_presets` with an eight-code assertion on `TASK_TYPES` |
| `engine/tests/test_api_drafting.py`          | Widen the intent parametrization to the eight codes (kept green for the sibling story)          |

Run: `.venv/bin/python -m pytest engine/tests` (on Windows, `.venv/Scripts/python.exe`).

### Browser/UI Testing

No credentials — the app is unauthenticated. Start the engine (`uvicorn engine.api:app --port 8000`) and the app (`cd frontend && npm run dev`), then:

1. Go to `/workstreams/new`. **Expect:** the Deliverable type dropdown lists all eight options, defaulted to "PD — Policy Document".
2. Create "RMiT FAQ" as **FAQ**. **Expect:** you land on the new workstream's graph with one node titled "RMiT FAQ (FAQ)".
3. Click that node. **Expect:** the detail panel shows a chip reading "FAQ" beside the `task` badge.
4. Click **Add node**, pick node type **task**. **Expect:** a "Task type" grid appears with eight options, none selected, and "Add to graph" is disabled even after you fill in title, attachment, and an edge.
5. Pick **Engagement Deck**. **Expect:** "Add to graph" becomes enabled.
6. Switch node type to **international-standard**. **Expect:** the Task type grid disappears and "Add to graph" stays enabled.
7. Switch back to **task**. **Expect:** the grid returns with nothing selected — the earlier pick was discarded.
8. Add it as an Engagement Deck. **Expect:** the node appears on the canvas; opening it shows the "Engagement Deck" chip.

### E2E Tests

| Key Scenario                                                        | Test file                            | Assigned sub-task |
| ------------------------------------------------------------------- | ------------------------------------ | ----------------- |
| Adding a second working draft to an existing workstream             | `frontend/e2e/add-task-node.spec.ts` | Task 8            |
| A working draft cannot be added without a deliverable kind          | `frontend/e2e/add-task-node.spec.ts` | Task 8            |
| Switching classification away from working draft drops the question | `frontend/e2e/add-task-node.spec.ts` | Task 8            |

The workstream-creation scenarios and the scenario outline over all eight kinds stay in Vitest + MSW (`NewWorkstreamPage.test.tsx`) — they are form-and-request assertions with no multipart round-trip, which is the one thing `frontend/e2e/README.md` says the E2E exists for. The "cannot be changed once set" and "not asked for context documents" scenarios are covered by Vitest and by engine Tests 4–5.

**Locator strategies:** `getByRole("radiogroup", { name: "Task type" })` and `getByRole("radio", { name: <code> })` for the grid (matching the existing "Breaking-up method" and node-type locators); `getByLabel("Deliverable type")` for the creation dropdown; `getByTestId("task-type-chip")` for the detail chip.

**Fixture hygiene:** the new spec adds a node to `open-finance-pd-2026`, a tracked path. Follow the existing convention in `add-node-chunking.spec.ts` — note in a comment that `git checkout data/workstreams/open-finance-pd-2026` restores it after a local run.

**Locating a node in a real browser — a constraint discovered while building this.** The graph is drawn by `react-force-graph-2d` into a single `<canvas>`, so there is **no per-node DOM element** outside Vitest. The one-button-per-node DOM the component suite relies on comes entirely from the stub at `frontend/src/test/mocks/react-force-graph-2d.tsx`. A Playwright spec must therefore sweep the canvas for any node, then navigate by the detail panel's neighbour chips — the only real DOM handles a node has. Both new specs share an `openNode` helper doing exactly that, and `frontend/e2e/README.md` documents it.

Consequently **five pre-existing E2E specs do not pass** — `add-edge`, `add-node-chunking`, `extract-concepts`, `open-finance-build`, and `workstream-graph` all target either `getByRole("button", { name: <node title> })` or `svg circle`, neither of which exists under the canvas renderer. Verified to fail identically on `staging` with none of this epic's code present, so they are **not** a regression from this work and are deliberately left untouched. Repairing them is its own task, and the better fix is probably to give `GraphCanvas` a real `sr-only` node list — which would restore E2E addressability and canvas keyboard accessibility in one change.
