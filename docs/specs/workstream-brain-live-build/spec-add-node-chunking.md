# Add a Document and Break It Into Passages

**Ticket:** TBD

This feature lets a policy drafter attach a source document when adding a node to
a workstream, choose how that document should be broken into citable passages, and
have the breaking-up happen immediately when the node is added. It fixes the gap
where a document added to a workstream was never broken into passages, leaving it
unusable for later linkage analysis. The drafter benefits by turning any source
document they attach into something the tool can quote and reason about.

## User Story

As a policy drafter, I want to attach a source document when I add a node and
choose how it is broken into passages, so that the document becomes a set of exact,
quotable passages I can later connect and analyse — without any incorrect
breaking-up and without waiting.

## Background & Context

**Current state:**

- The "Add node" form accepts a node type, title, description, a source link and
  one or more connections to nodes already on the canvas.
- An added document is never broken into passages, so it has no quotable content
  and cannot be used for linkage analysis.
- The workstream opens with a focal working-draft node at its centre, which is the
  first thing a newly added document connects to.

**Problem:**

- A document a drafter adds is effectively inert — there is nothing to quote from
  it, so the tool's headline capability of surfacing labelled, verbatim linkages
  is unreachable for anything the drafter adds.
- Because breaking-up never happens, a drafter cannot build a real workstream
  themselves; they can only view workstreams prepared in advance.

## Target User & Persona

- **Who:** Aisyah R., a policy drafter at Bank Negara Malaysia working on the
  Operational Resilience policy document.
- **Context:** She is assembling a workstream around her focal working draft and
  needs to bring in the source documents — international standards, peer-regulator
  guidance, acts and published policies — that she wants to check her draft
  against.
- **Current workaround:** She can add a node for a document, but the document is
  never broken into passages, so she cannot analyse it against her draft at all.

## Goals

- Let the drafter attach one document to a new node and pick one of three
  breaking-up methods when adding it.
- Break the document into citable, word-for-word passages immediately on adding
  the node, with no waiting.
- Place the new node on the canvas connected exactly as the drafter declared.
- Prevent half-formed nodes: if the document cannot be read, cannot be broken up
  by the chosen method, or yields no usable passages, add nothing and explain why.

## Non-Goals

- **Concept extraction.** Deriving a document's topics is a separate, explicit
  action covered by another story; it does not happen when the document is added.
- **Connecting two documents that already exist on the canvas.** Adding new
  connections between existing nodes is a separate story; here, connections are
  only declared while adding the new node.
- **Linkage analysis.** Finding and labelling linkages between documents is a
  separate story.
- **Automatic detection of a document's structure.** The drafter always chooses
  the breaking-up method; the tool never guesses it.
- **Editing or re-attaching a document's file after the node has been added.**

## User Workflow

1. **Open the add-document form** — From the canvas, Aisyah clicks "Add node". She
   sees fields for the node type, a title, a description, a place to attach one
   document, a choice of breaking-up method, and a way to declare connections to
   nodes already on the canvas.
2. **Fill it in** — She picks a node type (for example, international-standard),
   types a title and a short description, attaches one document, chooses the
   breaking-up method that fits the document (structured-rules, semi-structured,
   or prose), and selects at least one node already on the canvas to connect to.
3. **Add to graph** — She clicks "Add to graph". The document is broken into
   passages right away, effectively instantly.
4. **See the result** — The new node appears on the canvas, connected as she
   declared. The document is now made of citable passages, each an exact
   word-for-word slice of the source, ready to be connected and analysed later.
5. **Or see a clear problem** — If the document cannot be read, the chosen method
   cannot break it up, or it produces no usable passages, she sees a plain-language
   message explaining what went wrong, and no node is created.

## Acceptance Criteria

### Scenario: Add an international standard broken up as semi-structured

```gherkin
Given Aisyah is on the canvas of her Operational Resilience workstream
  And the workstream has a focal working-draft node on the canvas
When she opens the add-document form
  And she chooses the node type "international-standard"
  And she enters the title "BCBS Principles for Operational Resilience 2021"
  And she enters a short description
  And she attaches the document
  And she chooses the breaking-up method "semi-structured"
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then a new node titled "BCBS Principles for Operational Resilience 2021" appears on the canvas
  And it is connected to the focal working-draft node
  And the document is made up of citable passages
  And each passage is an exact word-for-word slice of the document
  And she is returned to the canvas without any wait for processing
```

### Scenario: Add a peer-regulator document broken up as prose

```gherkin
Given Aisyah is on the canvas with her focal working-draft node and the
      "BCBS Principles for Operational Resilience 2021" node already added
When she opens the add-document form
  And she chooses the node type "peer-regulator"
  And she enters the title "Bank of England Operational Resilience — Chapter 3"
  And she enters a short description
  And she attaches the document
  And she chooses the breaking-up method "prose"
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then a new node titled "Bank of England Operational Resilience — Chapter 3" appears on the canvas
  And it is connected to the focal working-draft node
  And the document is made up of citable passages
  And each passage is an exact word-for-word slice of the document
```

### Scenario: Add a numbered Bank Negara Malaysia policy broken up as structured-rules

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she opens the add-document form
  And she chooses the node type "internal-published"
  And she enters the title "Risk Management in Technology (RMiT)"
  And she enters a short description
  And she attaches the numbered policy document
  And she chooses the breaking-up method "structured-rules"
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then a new node titled "Risk Management in Technology (RMiT)" appears on the canvas
  And it is connected to the focal working-draft node
  And the document is broken into passages that keep the policy's numbering
  And each passage is an exact word-for-word slice of the document
```

### Scenario Outline: Each breaking-up method produces citable passages immediately

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she adds a "<document>" using the breaking-up method "<method>"
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then a new node for "<document>" appears on the canvas connected to the focal working-draft node
  And the document is made up of citable, word-for-word passages
  And she is returned to the canvas without waiting for processing

Examples:
  | document                                        | method            |
  | BCBS Principles for Operational Resilience 2021 | semi-structured   |
  | Bank of England Operational Resilience — Chapter 3 | prose          |
  | Risk Management in Technology (RMiT)            | structured-rules  |
```

### Scenario: A connection is required to add a document

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she opens the add-document form
  And she chooses a node type, enters a title and description, attaches a document, and chooses a breaking-up method
  And she does not connect it to any node already on the canvas
  And she tries to add it to the graph
Then she is told that a document must be connected to at least one node already on the canvas
  And no new node is created
```

### Scenario: The chosen method cannot break up the document

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she opens the add-document form
  And she enters the title "Bank of England Operational Resilience — Chapter 3"
  And she attaches the flowing-text document
  And she chooses the breaking-up method "structured-rules"
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then she sees a plain-language message that this document does not look like a
      numbered Bank Negara Malaysia policy and cannot be broken up as structured-rules
  And she is prompted to choose a different breaking-up method such as prose or semi-structured
  And no new node is created
```

### Scenario: The attached document cannot be read

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she opens the add-document form
  And she fills in a node type, title, description, and a breaking-up method
  And she attaches a document that cannot be read
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then she sees a plain-language message that the document could not be read and to try a different file
  And no new node is created
```

### Scenario: The document produces no usable passages

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she opens the add-document form
  And she fills in a node type, title, description, and a breaking-up method
  And she attaches a document that contains no usable text
  And she connects it to the focal working-draft node
  And she clicks "Add to graph"
Then she sees a plain-language message that the document produced no passages and cannot be added
  And no new node is created
```

### Scenario: No document is attached

```gherkin
Given Aisyah is on the canvas with her focal working-draft node already added
When she opens the add-document form
  And she enters a node type, title, description and a connection but attaches no document
  And she tries to add it to the graph
Then she is told that a document must be attached to add it to the graph
  And no new node is created
```

### Scenario: Concepts are not extracted when the document is added

```gherkin
Given Aisyah has just added "BCBS Principles for Operational Resilience 2021" to the canvas
When she opens the new node
Then the document is already made up of citable passages
  And no concepts have been extracted yet
  And she can extract concepts later as a separate, explicit action
```

## Business Rules & Constraints

- **Exactly one document per added node.** A node is added with a single attached
  document. Re-attaching or editing the file afterwards is out of scope.
- **One breaking-up method, chosen by the drafter.** The drafter picks exactly one
  of structured-rules, semi-structured, or prose. The tool never guesses it.
  - _structured-rules_ is only appropriate for recognised numbered Bank Negara
    Malaysia policy documents (for example, RMiT). For an arbitrary uploaded PDF,
    the realistic choices are semi-structured or prose.
- **Breaking-up is immediate.** Breaking a document into passages happens the
  moment the drafter adds the node and returns them to the canvas effectively
  instantly, with no waiting.
- **Verbatim passages.** Every passage is an exact, word-for-word slice of the
  source document — never reworded or summarised.
- **At least one connection is required.** A new document must be connected to at
  least one node already on the canvas. For the first document added, that node is
  the focal working-draft node.
- **No half-formed nodes.** If the document cannot be read, the chosen method
  cannot break it up, or it yields no usable passages, no node is created and the
  drafter sees a clear, non-technical message.
- **Concept extraction is separate.** Adding a document only breaks it into
  passages; its concepts are not derived here.

## Success Metrics

- A drafter can add a document by each of the three methods and, on adding, see a
  node on the canvas whose document is made up of citable, word-for-word passages.
- 100% of passages produced are exact slices of the source document; none are
  reworded or invented.
- Adding a document returns the drafter to the canvas quickly, with breaking-up
  perceived as immediate.
- When a document cannot be read, cannot be broken up by the chosen method, or
  yields no passages, no node is created and the drafter always sees a clear,
  non-technical message rather than a silent empty node.

## Dependencies

- The workstream already opens with a focal working-draft node, so the first added
  document has something to connect to (Focal working-draft node story).
- The three breaking-up methods (structured-rules, semi-structured, prose) already
  exist in the product and are reused unchanged.
- Results are stored durably with the workstream so a document broken into
  passages before the demo is present, unchanged, during it.

## Open Questions

- [x] ~~Should breaking up a document be automatic or chosen by the drafter?~~ —
      **Resolved:** The drafter chooses one of the three methods when adding the
      document, to avoid documents being broken up incorrectly.
- [x] ~~Should concept extraction happen when the document is added?~~ —
      **Resolved:** No. Adding a document only breaks it into passages; extracting
      concepts is a separate, explicit action in another story.
- [x] ~~What happens when the chosen method cannot break up the document?~~ —
      **Resolved:** The add fails with a clear, non-technical message suggesting a
      different method, and no node is created.
- [x] ~~Can more than one document be attached to a single added node?~~ —
      **Resolved:** No. Exactly one document is attached per added node.

---

## Functional Requirements

- **Attachment ingest:** On "Add to graph" the route MUST convert the single
  attached PDF/DOCX to markdown via the existing `engine.ingest` path
  (`ingest_document`, which already accepts an injectable `converter`) before any
  graph write. No new extractor — reuse MarkItDown / Azure Document Intelligence
  exactly as `ingest_from_url` does.
- **Deterministic segmentation:** After ingest succeeds, the route MUST call
  `engine.anchors.segment(document_id, markdown, doc_class)` with the drafter's
  chosen `doc_class`. Segmentation is regex/tree-walk only — no model call — so it
  returns effectively instantly; the drafter is never asked to wait.
- **Per-node anchor persistence:** The resulting `list[Anchor]` MUST be written by
  `engine.ws_anchors.save(workstreams_dir, workstream_id, node_id, anchors)` to
  `data/workstreams/{workstream_id}/anchors/{node_id}.json`, mirroring the per-edge
  `engine/findings.py` side-file pattern.
- **document_id assignment:** The created graph node MUST gain a `document_id` set
  to the new node's own id (`document_id == node_id`), so its anchors (and the axis
  cache written by later stories) key off the same identifier consistently. Today
  `add_node` writes no `document_id`; this story adds it for a chunked node.
- **Recent-activity trail:** On success the node's `recent_activity` list MUST gain
  two entries in order — `"node created"` then `"chunking completed"` — each carrying
  an author and an ISO-8601 UTC `at` timestamp (same `RecentActivity` shape the
  node-detail route already returns).
- **No concept extraction here:** The route MUST NOT derive concepts. The created
  node's `concepts` continues to render the existing placeholder; extraction is a
  separate, explicit story.
- **Atomicity — no half-formed node:** Ingest and segmentation MUST run BEFORE
  `add_node`/`save_graph`, exactly as the current route downloads the URL up front.
  If ingest fails, segmentation raises, or segmentation yields zero anchors, NO node
  and NO edges are appended to `graph.json`, and NO `anchors/{node_id}.json` file is
  written.
- **Edge requirement preserved:** At least one edge to an existing node is still
  required (`validate_node_create`'s existing `EDGE_REQUIRED` rule), checked before
  ingest.

### Validation & Business Rules

- **`doc_class` is one of exactly three values** — `structured-rules` /
  `semi-structured` / `prose`. Any other (or missing) value → `400 INVALID_DOC_CLASS`.
  The enum is validated in `engine/workstreams.py::validate_node_create` alongside
  `node_type`/`edges`, before ingest is attempted.
- **Attachment is required** — the request must carry exactly one file. A missing
  attachment → `400 ATTACHMENT_REQUIRED`, checked before ingest, no node created.
- **Verbatim passages** — every emitted `Anchor.text` is a literal substring of the
  ingested markdown. This is not re-checked in the route; it is guaranteed inside
  `segment(...)`, which calls `engine.anchors.verify_substring(...)` on every anchor
  and raises `AnchorTextNotFoundError` before returning. The route trusts that
  guardrail — it never re-slices or rewrites anchor text.
- **`structured-rules` only for recognised BNM policies** — segmenting a non-BNM
  document as `structured-rules` raises `UnknownDocumentIdError` (no entry in
  `engine.clauses.POLICY_SHORT_NAMES`); the route maps this to `422 CHUNKING_FAILED`
  with a message steering the drafter to `prose`/`semi-structured`.
- **Zero passages is a failure, not an empty success** — a segment call that returns
  `[]` → `422 NO_PASSAGES`, no node created. (Distinct from an unreadable document,
  which fails earlier at ingest with `422 INGEST_FAILED`.)

## Permissions & Security

- **Scope:** Public engine API (`/api/workstreams/*`); no auth layer in MVP1 — same
  posture as every other route in `engine/api.py`.
- **Authorization:** None enforced; the drafter persona (Aisyah R.) is assumed.
- **Input validation:**
  - `doc_class` is a closed enum of three strings; rejected server-side before ingest
    (`400 INVALID_DOC_CLASS`) — the frontend picker cannot be the only guard.
  - Exactly one attachment; extra parts or none → rejected (`400 ATTACHMENT_REQUIRED`).
  - Only `.pdf`/`.docx` are meaningful; a corrupt or unrecognised file surfaces as
    `422 INGEST_FAILED` (MarkItDown raises → `UnreadableDocumentError`), never a 500.
  - The attachment is written to a `tempfile` for conversion and unlinked in a
    `finally`, matching `ingest_from_url`; nothing sensitive is persisted beyond the
    resulting markdown artifact and anchors side-file.
  - `title`/`description` are stored verbatim as node fields (already the case);
    no markup interpretation.

## API Design

### `POST /api/workstreams/{workstream_id}/nodes`

The route already reads its body. Today it is `await request.json()`. This story
adds a file attachment and a `doc_class`, so the request becomes **`multipart/form-data`**:

- One file part named `attachment` (the single PDF/DOCX).
- One text part named `payload` carrying the existing JSON body (`node_type`,
  `title`, `description`, `edges`, and now `doc_class`). Sending the node fields as a
  single JSON blob keeps `validate_node_create` and `add_node` reading one `dict`,
  rather than spreading every field across form fields.

The legacy `source_url` + `skip_ingest` JSON shape is retained for callers that add a
node without a file (e.g. a node whose document is fetched by URL); when an
`attachment` part is present it takes precedence and `source_url` is ignored for
ingest. The frontend for this story always sends the multipart shape with an
attachment.

**Request (multipart/form-data):**

```
--boundary
Content-Disposition: form-data; name="payload"
Content-Type: application/json

{
  "node_type": "international-standard",
  "title": "BCBS Principles for Operational Resilience 2021",
  "description": "Basel Committee principles paper, 2021.",
  "doc_class": "semi-structured",
  "edges": [
    { "target_node_id": "opres-pd-v0-3", "edge_type": "references" }
  ]
}
--boundary
Content-Disposition: form-data; name="attachment"; filename="bcbs-opres-2021.pdf"
Content-Type: application/pdf

<binary PDF bytes>
--boundary--
```

**Response (201):**

```json
{
  "id": "bcbs-principles-for-operational-resilience-2021",
  "node_type": "international-standard",
  "title": "BCBS Principles for Operational Resilience 2021",
  "document_id": "bcbs-principles-for-operational-resilience-2021",
  "doc_class": "semi-structured",
  "anchor_count": 41,
  "created_edges": [
    {
      "id": "e-opres_pd_v0_3--bcbs_principles_for_operational_resilience_2021",
      "source": "opres-pd-v0-3",
      "target": "bcbs-principles-for-operational-resilience-2021",
      "edge_type": "references",
      "analysed": false
    }
  ]
}
```

Notes on the response: `document_id` equals `id` (the chunked-node contract);
`anchor_count` is `len(anchors)` just written to the side-file; `created_edges`
preserves the existing shape, including the task-node-as-source flip in `add_node`
(so the BCBS anchor surfaces under the OpRes PD task's outgoing edges).

**Errors:**

| Status | Code                   | Condition                                                                                                                                                                                                                                                                         |
| ------ | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 400    | `ATTACHMENT_REQUIRED`  | No file part present. No node created.                                                                                                                                                                                                                                            |
| 400    | `INVALID_DOC_CLASS`    | `doc_class` missing or not one of `structured-rules`/`semi-structured`/`prose`. No node created.                                                                                                                                                                                  |
| 400    | `EDGE_REQUIRED`        | No edge to an existing node declared (existing rule, preserved). No node created.                                                                                                                                                                                                 |
| 400    | `INVALID_NODE_TYPE`    | `node_type` not one of the eight flat types (existing rule).                                                                                                                                                                                                                      |
| 400    | `INVALID_EDGE_TYPE`    | `edge_type` not one of the four structural types (existing rule).                                                                                                                                                                                                                 |
| 400    | `INVALID_EDGE_TARGET`  | An edge target is not an existing node (existing rule).                                                                                                                                                                                                                           |
| 404    | `WORKSTREAM_NOT_FOUND` | No workstream with `workstream_id` (existing rule).                                                                                                                                                                                                                               |
| 422    | `INGEST_FAILED`        | The attached document cannot be read (`UnreadableDocumentError`). Message: "The attached document could not be read; try a different file." No node created.                                                                                                                      |
| 422    | `CHUNKING_FAILED`      | The chosen method cannot segment this document (`UnknownDocumentIdError` or any `segment` failure). Message: "This document doesn't look like a numbered Bank Negara Malaysia policy and can't be broken up as structured-rules — try prose or semi-structured." No node created. |
| 422    | `NO_PASSAGES`          | `segment(...)` returned zero anchors. Message: "The document produced no passages and can't be added." No node created.                                                                                                                                                           |

Error bodies use the existing `_ws_error` shape: `{ "code": ..., "message": ...,
"field"?: ... }` (`field: "attachment"` on `ATTACHMENT_REQUIRED`/`INGEST_FAILED`,
`field: "doc_class"` on `INVALID_DOC_CLASS`/`CHUNKING_FAILED`).

Concrete realistic mappings:

- "BCBS Principles for Operational Resilience 2021" + `semi-structured` → 201, ~41
  heading-leaf anchors.
- "Bank of England Operational Resilience — Chapter 3" + `prose` → 201, prose window
  anchors.
- "RMiT" (a recognised BNM policy) + `structured-rules` → 201, clause-numbered anchors
  (`RMiT 17.1`, `RMiT 17.2`, …).
- "Bank of England Operational Resilience — Chapter 3" + `structured-rules` → 422
  `CHUNKING_FAILED` (not a BNM policy).

## Data Model

No SQL database. Anchors are a per-node JSON side-file, mirroring the per-edge
findings files under `data/workstreams/{workstream_id}/findings/{edge_id}.json`.

**File layout (new):**

```
data/workstreams/{workstream_id}/
├── graph.json                    # node now carries document_id (== node id)
├── findings/{edge_id}.json       # existing per-edge findings
├── anchors/{node_id}.json        # NEW — per-node list[Anchor] for a chunked node
└── axes/axes-{document_id}.json  # later story; per-workstream axis cache
```

**`anchors/{node_id}.json`** — a bare JSON list of `engine.anchors.Anchor` records,
written UTF-8 with `ensure_ascii=False` (anchor text carries §, en-dashes, U+2212):

| Field           | Type                                                 | Description                                                              |
| --------------- | ---------------------------------------------------- | ------------------------------------------------------------------------ |
| `anchor_id`     | string                                               | Unique within the document; e.g. `"RMiT 17.1"` or a prose/heading id.    |
| `anchor_label`  | string                                               | UI-render label (equal to `anchor_id` for the three shipped strategies). |
| `text`          | string                                               | Verbatim substring of the ingested markdown — the citable passage.       |
| `doc_class`     | `"structured-rules"`\|`"semi-structured"`\|`"prose"` | The method that produced it (the drafter's choice).                      |
| `document_id`   | string                                               | The owning node's id (== the graph node's `document_id`).                |
| `heading_path`  | string[]                                             | Section heading breadcrumb; `[]` for structured-rules.                   |
| `page_span`     | `[int, int]` \| null                                 | Source page range when known (prose/semi-structured); `null` otherwise.  |
| `parent_anchor` | string \| null                                       | Parent anchor_id for nesting; `null` at the top level.                   |

Example record (semi-structured leaf from the BCBS paper):

```json
{
  "anchor_id": "BCBS-OpRes-2021 §Principle 6",
  "anchor_label": "Principle 6",
  "text": "Principle 6: Banks should identify their critical operations...",
  "doc_class": "semi-structured",
  "document_id": "bcbs-principles-for-operational-resilience-2021",
  "heading_path": ["Principles for operational resilience"],
  "page_span": [7, 7],
  "parent_anchor": null
}
```

**`graph.json` node change:** a chunked node gains `"document_id": "<node id>"`
alongside the existing `id`/`node_type`/`title`/`description`, plus a
`recent_activity` list with the two entries described above.

## UI/Frontend Requirements

### Components

**AddNodeDialog** — `frontend/src/features/workstream-graph/AddNodeDialog.tsx`

- **Type:** Modify existing.
- **Purpose:** Extend the existing add-node modal (which already has a node-type grid,
  title, description, an attachment file input, and edge rows) with a **breaking-up
  method picker** and wire the attachment + `doc_class` into the create-node call.
- **Breaking-up method picker:** a `radiogroup` of exactly three options —
  `structured-rules`, `semi-structured`, `prose` — with plain-language helper text
  noting `structured-rules` suits numbered BNM policies (RMiT) and `prose`/
  `semi-structured` suit arbitrary uploads. Default selection: `semi-structured`
  (the safe choice for an arbitrary PDF).
- **Attachment:** the file input already present (`accept=".pdf,.docx"`) becomes
  required; capture the selected `File` into state.
- **Submit gating:** "Add to graph" stays disabled until a title is set, at least one
  complete edge row exists (existing rule), an attachment is chosen, and a `doc_class`
  is selected.

### Types & client

- `frontend/src/lib/types.ts` — `CreateNodeRequest` gains
  `doc_class: "structured-rules" | "semi-structured" | "prose"`. The response type
  `CreateNodeResponse` gains `document_id: string`, `doc_class: string`, and
  `anchor_count: number`.
- `frontend/src/lib/api.ts` — `createNode` sends `multipart/form-data`
  (a `FormData` with a `payload` JSON part and an `attachment` file part) rather than
  `postJson`, since a file must go over the wire. It still parses the `{code,message}`
  error body via `throwHttpError`.

### User Interactions

- Choose a breaking-up method → the picker highlights the selection; no network call.
- Attach a file + fill title + declare an edge + pick a method → "Add to graph"
  becomes enabled.
- Click "Add to graph" → the button shows a **"Chunking…"** label while the mutation
  is in flight, then the dialog closes and the graph query is invalidated so the new
  node appears on the canvas.

### States

- **Loading:** button reads "Chunking…" (chunking is fast, but the ingest round-trip
  is not instant); the form is disabled.
- **Empty:** unchanged — the edge list shows "At least one edge to an existing node
  is required" until a row is added.
- **Error (per code):** an inline message, keyed by the returned `code`:
  - `ATTACHMENT_REQUIRED` → "Attach a document to add it to the graph."
  - `INVALID_DOC_CLASS` → "Choose how the document should be broken up."
  - `INGEST_FAILED` → "The document could not be read. Try a different file."
  - `CHUNKING_FAILED` → "This document can't be broken up as structured-rules. Try
    prose or semi-structured." (echo the server message when present)
  - `NO_PASSAGES` → "The document produced no passages and can't be added."
  - `EDGE_REQUIRED` → "Connect the document to at least one node already on the canvas."
    When the error carries a `field`, flag the matching input (attachment / method).

## Architecture Notes

- **New dependencies:** none. `python-multipart` is already a declared dep (used by
  other multipart routes / TestClient support per CLAUDE.md); `MarkItDown` and the
  anchor segmenters already exist.
- **Dependencies & integration:** a new module `engine/ws_anchors.py` (mirrors
  `engine/findings.py`); a change to `engine/api.py::create_workstream_node` to accept
  multipart, ingest the attachment, segment, and persist anchors; a change to
  `engine/workstreams.py` (`validate_node_create` gains the `doc_class` enum check;
  `add_node` sets `document_id` and seeds `recent_activity`). Frontend changes are
  confined to `AddNodeDialog.tsx`, `types.ts`, and `api.ts`.

**SHARED CONTRACT (verbatim — three sibling specs share this; all three must agree):**

A NEW module `engine/ws_anchors.py` mirrors `engine/findings.py`:

- Storage path: `data/workstreams/{workstream_id}/anchors/{node_id}.json` — a JSON
  list of `engine.anchors.Anchor` records for that one document/node.
- `anchors_path(workstreams_dir, workstream_id, node_id) -> Path`
- `load(workstreams_dir, workstream_id, node_id) -> list[Anchor]` — raises
  `AnchorsNotSegmentedError` when the file is absent.
- `save(workstreams_dir, workstream_id, node_id, anchors)` — writes UTF-8,
  `ensure_ascii=False` (anchor text carries §, en-dashes, U+2212).
- `build_index(workstreams_dir, workstream_id) -> AnchorIndex` — unions every
  `anchors/*.json` file in the workstream into one `engine.anchors.AnchorIndex`
  (duplicate anchor_id already raises in `AnchorIndex.__init__`).
- The graph node gains a `document_id` at add time (today `add_node` never sets one).
  For a chunked node, `document_id` = the new node's id (so anchors and axes key off
  it consistently).
- Axis cache (used by later stories) relocates from `engine/arm_g.py`'s
  `AXES_DIR = REPO_ROOT/"experiments"` to per-workstream
  `data/workstreams/{workstream_id}/axes/axes-{document_id}.json`.

## Exemplar Files

- `engine/findings.py` — the per-edge side-file module to MIRROR for `ws_anchors.py`
  (`*_path`, `load` raising a not-found error, `save` with UTF-8 + `ensure_ascii=False`).
- `engine/anchors.py` — `segment(document_id, source_markdown, doc_class)` dispatcher
  (~918), the `Anchor` TypedDict (~29), `AnchorIndex`, and the errors
  `UnknownDocClassError` / `UnknownDocumentIdError` / `AnchorTextNotFoundError`.
- `engine/ingest.py` — `ingest_document` (injectable `converter`), `ingest_from_url`,
  `UnreadableDocumentError` — the ingest pattern and the up-front temp-file handling.
- `engine/api.py` `create_workstream_node` route (~1060) — the route to extend
  (currently ingests URL to markdown but never segments; ingest happens BEFORE
  `add_node`, the atomicity pattern to preserve).
- `engine/workstreams.py` `add_node` (~417) and `validate_node_create` (~382).
- `frontend/src/features/workstream-graph/AddNodeDialog.tsx` — the form to extend.
- `frontend/src/lib/types.ts` (`CreateNodeRequest`), `frontend/src/lib/api.ts`
  (`createNode`).
- `engine/tests/test_ingest.py` — the `_FakeConverter`/`_FakeResult` stub pattern for
  ingest with no network. `engine/tests/test_api_workstreams.py` — the node-create
  test harness (`_graph_on_disk`, tmp-path fixture). `engine/tests/test_anchors.py` —
  segmenter test patterns.

## Implementation Plan

### Sub-tasks

**Task 1: Create `engine/ws_anchors.py` (mirror `engine/findings.py`)** — _small_
(<100 LOC)

- Files: `engine/ws_anchors.py`, `engine/tests/test_ws_anchors.py`
- Implement `anchors_path`, `load` (raising `AnchorsNotSegmentedError` when the file
  is absent), `save` (UTF-8, `ensure_ascii=False`), and `build_index` (union all
  `anchors/*.json` into an `AnchorIndex`). Follow the SHARED CONTRACT exactly.
- INDEPENDENT.

**Task 2: Wire segmentation into the create-node route** — _medium_ (100–300 LOC)

- Files: `engine/api.py` (`create_workstream_node`), `engine/workstreams.py`
  (`validate_node_create` + `add_node`), `engine/tests/test_api_add_node_chunking.py`
- Accept `multipart/form-data` (a `payload` JSON part + an `attachment` file part);
  add the `doc_class` enum check to `validate_node_create`; ingest the attachment to
  markdown up front (injectable converter for tests), then `segment(...)`, mapping
  `UnreadableDocumentError`→422 `INGEST_FAILED`, `UnknownDocumentIdError`/other
  segment failures→422 `CHUNKING_FAILED`, empty result→422 `NO_PASSAGES`; only then
  `add_node` (which sets `document_id == node_id` and seeds the two `recent_activity`
  entries) and `save_graph`; `ws_anchors.save(...)` the anchors; extend the 201 body
  with `document_id`, `doc_class`, `anchor_count`.
- SEQUENTIAL (depends on Task 1).

**Task 3: Frontend `doc_class` picker + multipart create** — _medium_ (100–300 LOC)

- Files: `frontend/src/features/workstream-graph/AddNodeDialog.tsx`,
  `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`,
  `frontend/e2e/add-node-chunking.spec.ts`
- Add the three-option method picker; capture the attachment `File`; gate submit;
  extend `CreateNodeRequest` with `doc_class` and `CreateNodeResponse` with
  `document_id`/`doc_class`/`anchor_count`; make `createNode` send `FormData`; render
  the per-code error messages and the "Chunking…" loading label; add the E2E happy
  path.
- INDEPENDENT (can proceed against the API contract above; final wiring verified once
  Task 2 lands).

### Negative Constraints

- Do NOT extract concepts in this route — concept extraction is a separate story; the
  node's `concepts` stays a placeholder.
- Do NOT segment against the global `data/artifacts/anchor-index.json` (or any
  `data/artifacts/` clause index) — anchors are per-workstream, written only under
  `data/workstreams/{workstream_id}/anchors/`.
- Do NOT change the three segmenter algorithms in `engine/anchors.py`
  (`structured_rules_segment`, `semi_structured_segment`, `prose_segment`) or the
  `Anchor` TypedDict — this story only calls `segment(...)` and persists its output.
- Do NOT rebuild `data/artifacts/` (see the CLAUDE.md narrowing blocker); this path
  never touches it.
- Do NOT relax the verbatim guarantee — never re-slice, normalise, or rewrite an
  anchor's `text` in the route.

## Test Scenarios

Ingest is stubbed exactly as `engine/tests/test_ingest.py` does it — inject a
`_FakeConverter` returning canned markdown (a `text_content` attribute) so no network
or Azure credentials are needed. The route accepts an injectable converter (or the
test monkeypatches `engine.api.ingest_document`) and posts multipart via
`TestClient` (`files=`/`data=`).

**Test 1: Happy path — semi-structured attachment produces a chunked node**

- Setup: `opres-v2` copied to a tmp workstreams dir; a `_FakeConverter` returning
  markdown that the `semi-structured` segmenter breaks into N (>0) leaf anchors.
- Action: `POST /api/workstreams/opres-v2/nodes` multipart with
  `payload={node_type:"international-standard", title:"BCBS Principles for
Operational Resilience 2021", doc_class:"semi-structured", edges:[{target_node_id:
"opres-pd-v0-3", edge_type:"references"}]}` and an `attachment` file part.
- Expected: 201; response `document_id == id` and `anchor_count == N`;
  `data/workstreams/opres-v2/anchors/{node_id}.json` exists with N anchor records;
  the graph node on disk carries `document_id == node_id`; its `recent_activity`
  contains "node created" then "chunking completed".

**Test 2: structured-rules on a non-BNM document → 422, graph unchanged**

- Setup: tmp workstream; `_FakeConverter` returning arbitrary (non-BNM) markdown;
  the `document_id`/title is not in `engine.clauses.POLICY_SHORT_NAMES`.
- Action: `POST .../nodes` multipart with `doc_class:"structured-rules"` and the
  attachment.
- Expected: 422 `CHUNKING_FAILED` with a message steering to prose/semi-structured;
  `graph.json` unchanged (node count equal to before); no `anchors/{node_id}.json`
  written.

**Test 3: Segment yields zero anchors → 422 NO_PASSAGES**

- Setup: tmp workstream; `_FakeConverter` returning markdown that the chosen
  segmenter maps to `[]` (e.g. whitespace-only headings).
- Action: `POST .../nodes` multipart with a valid `doc_class` and attachment.
- Expected: 422 `NO_PASSAGES`; `graph.json` unchanged; no anchors file.

**Test 4: Missing attachment → 400 ATTACHMENT_REQUIRED**

- Setup: tmp workstream.
- Action: `POST .../nodes` multipart with a valid `payload` but no `attachment` part.
- Expected: 400 `ATTACHMENT_REQUIRED` (`field: "attachment"`); `graph.json` unchanged.

**Test 5: Invalid doc_class → 400 INVALID_DOC_CLASS**

- Setup: tmp workstream.
- Action: `POST .../nodes` multipart with `doc_class:"auto"` and an attachment.
- Expected: 400 `INVALID_DOC_CLASS` (`field: "doc_class"`); `graph.json` unchanged;
  ingest not attempted.

**Test 6: Unreadable attachment → 422 INGEST_FAILED**

- Setup: tmp workstream; `_FakeConverter` returning whitespace-only text (raises
  `UnreadableDocumentError` inside `ingest_document`).
- Action: `POST .../nodes` multipart with a valid `doc_class` and the attachment.
- Expected: 422 `INGEST_FAILED` (`field: "attachment"`); `graph.json` unchanged; no
  anchors file.

**Test 7 (`test_ws_anchors.py`): save then load round-trips a chunked node**

- Setup: tmp workstreams dir; a hand-built `list[Anchor]` with §/en-dash text.
- Action: `ws_anchors.save(...)` then `ws_anchors.load(...)`.
- Expected: identical list back; the file is UTF-8 with the Unicode preserved
  (not escaped); `load` on an absent node raises `AnchorsNotSegmentedError`;
  `build_index` unions two nodes' files into one `AnchorIndex` and a duplicate
  `anchor_id` across files raises `ValueError`.

## Acceptance Criteria

- [ ] `POST .../nodes` accepts a `doc_class` + attachment and, on success, returns 201
      with `document_id`, `doc_class`, `anchor_count`, and `created_edges`.
- [ ] A chunked node writes `data/workstreams/{id}/anchors/{node_id}.json` with the
      segmenter's anchors and sets the node's `document_id == node_id`.
- [ ] Recent activity gains "node created" then "chunking completed".
- [ ] Every error condition returns its code with a clear, actionable message and
      leaves `graph.json` unchanged (no half-formed node).
- [ ] Anchor text is verbatim (guaranteed inside `segment`); the route never rewrites it.
- [ ] No concept extraction happens on add.
- [ ] No type errors or lint warnings (mypy third-party stub baseline excepted).

## Verification

Run the verifier skill to confirm changes are clean.

### Backend API Tests

- `engine/tests/test_ws_anchors.py` (new) — covers Test 7: `anchors_path`, `save`/
  `load` round-trip with UTF-8/`ensure_ascii=False`, `AnchorsNotSegmentedError` on
  absent file, `build_index` union + duplicate-id `ValueError`. Mirror the structure
  of `engine/tests/test_findings.py` where present.
- `engine/tests/test_api_add_node_chunking.py` (new) — covers Tests 1–6: happy path
  writes anchors + document_id + recent-activity; `CHUNKING_FAILED`, `NO_PASSAGES`,
  `ATTACHMENT_REQUIRED`, `INVALID_DOC_CLASS`, `INGEST_FAILED` each leave `graph.json`
  unchanged. Reuse the `_graph_on_disk` helper and tmp-path fixture from
  `engine/tests/test_api_workstreams.py`, and the `_FakeConverter` stub pattern from
  `engine/tests/test_ingest.py`. Run with
  `.venv/Scripts/python.exe -m pytest engine/tests` (see the forge-verify-hook
  false-fail learning).

### Browser/UI Testing

- URL: `http://localhost:5173/workstreams/opres-v2` (engine on
  `http://localhost:8000`; CORS already allows `:5173`).
- Steps:
  1. Click "Add node" → the dialog opens with the node-type grid, title,
     description, attachment input, breaking-up method picker, and edge rows.
     Expected: the picker shows exactly three options; `semi-structured` selected.
  2. Choose "international-standard", enter the BCBS title, attach a PDF, choose
     `semi-structured`, add an edge to the OpRes PD task node.
     Expected: "Add to graph" enables.
  3. Click "Add to graph".
     Expected: the button reads "Chunking…", then the dialog closes and the new node
     appears on the canvas connected to the task node.
  4. Repeat step 2 with `structured-rules` and a non-BNM PDF, then submit.
     Expected: an inline message steering to prose/semi-structured; no new node.

### E2E Tests

Playwright exists (`frontend/e2e/`, `baseURL http://localhost:5173`; see
`frontend/e2e/workstream-graph.spec.ts`). The happy-path Key Scenario (add a document
by `semi-structured`, see it appear chunked) maps to an E2E test; backend-only error
cases stay in Test Scenarios above.

| Key Scenario                                                       | Test file                                | Assigned sub-task |
| ------------------------------------------------------------------ | ---------------------------------------- | ----------------- |
| Add an international standard broken up as semi-structured (happy) | `frontend/e2e/add-node-chunking.spec.ts` | Task 3            |

**Locator strategies:** reuse the graph spec's role-based selectors — `getByRole
("button", { name: /add node/i })` to open the dialog; the node-type `radio`s by
`aria-label`; a `radiogroup` labelled "Breaking-up method" for the three method
options; the file input by `aria-label="Attachment"`; edge target/type `select`s by
`aria-label`; `getByRole("button", { name: /add to graph/i })` to submit; assert the
new node button (`name: "BCBS Principles for Operational Resilience 2021"`) appears on
the canvas.

## Open Questions

- [x] ~~How does the attachment arrive on the wire?~~ — **Resolved:** `multipart/
    form-data` with a JSON `payload` part (the existing node fields + `doc_class`)
      and a single `attachment` file part; the route stops using `await
    request.json()` and reads the form instead. Legacy `source_url`+`skip_ingest`
      JSON callers are still accepted when no attachment is present.
- [x] ~~What is a chunked node's `document_id`?~~ — **Resolved:** the new node's own
      id, per the SHARED CONTRACT, so anchors and the later axis cache key off one
      identifier.
