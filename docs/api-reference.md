<!-- last-updated: 2026-08-02 -->

# API Reference — Project SELARAS

> Companion to [`docs/architecture.md`](architecture.md). This is the full route
> surface of `engine/api.py`'s `create_app()` — the single FastAPI app that backs
> the SELARAS frontend. Every route lives in one file; this reference groups them
> by the screen that calls them, the same grouping `engine/api.py`'s own section
> comments use.

## Conventions that hold across every route

- **Error shape.** Every error response is `{code, message}`, optionally with a
  `field` naming the offending form input (`_ws_error` in `engine/api.py`). There
  is no other error shape anywhere in the API.
- **Read routes are file projections; `analyze` and `copilot`/`copilot/stream`
  are live.** Every GET route below reads `data/workstreams/<id>/` fresh on each
  request — no cache, no database. `analyze`, `copilot`, and `copilot/stream` call
  out to a model via injectable seams (`run_finder_pipeline_fn`, `copilot_reply_fn`,
  `copilot_stream_fn`) — see `docs/architecture.md`'s Architecture Pattern section.
- **`WORKSTREAM_NOT_FOUND` (404) is the first check on every workstream-scoped
  route.** It also doubles as the security boundary before any filesystem
  interpolation of `workstream_id`/`node_id`/`edge_id` — resolving the graph first
  is what stops a `../` in an id from escaping `data/workstreams/`.
- **`analysed` is derived, never stored.** An edge is "analysed" iff
  `findings/{edge_id}.json` exists on disk; there is no separate status field to
  drift from that file's presence.
- **CORS** allows `http://localhost:5173` and `http://localhost:3000` (the Vite
  dev server and common local ports).
- **Direction is never assumed.** Nothing here treats `source` as "the task's
  side" — the two live fixtures point edges opposite ways, so every route that
  needs "ours vs. theirs" resolves it explicitly (`workstreams.analysis_direction`)
  rather than reading `edge["source"]`.

---

## Task Screen routes

The drafter's per-task landing view: the working draft's status, its first- and
second-order document context, and per-neighbour analysis state.

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}`

The task's identity, workflow state, and its neighbourhood in two rings.

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **400** `NOT_A_TASK` — `node_id` resolves but isn't a `task` node
- **500** `INTERNAL_ERROR` — any unexpected load failure (the one route with a
  blanket `except Exception`, since a caller reaching here has no other recourse)
- **200** body:
  ```json
  {
    "task": { "id", "title", "source_name", "format", "description", "status",
              "owner", "reviewers", "clause_count", "last_edited_at" },
    "workflow": { /* engine.tasks.load_workflow shape */ },
    "neighbours": [ { "node_id", "title", "node_type", "edge_type", "edge_id",
                       "analysed", "findings_count" } ],
    "second_order_neighbours": [ { /* same shape + "via_node_id", "via_title" */ } ],
    "draft_empty": true
  }
  ```
  `neighbours` = every document directly joined to the task (**both** edge
  endpoints are read — never just `source`, since the live fixtures point
  opposite ways). `second_order_neighbours` = documents joined to a first-order
  neighbour but not to the task itself — context the drafter's own context is
  grounded in. An edge with both endpoints two hops out is excluded from either
  list. `draft_empty` reads the saved draft's `content_html`, not the fixture's
  static `clause_count` field, since only the former can tell whether a _live_
  draft has been written.

### `PATCH /api/workstreams/{workstream_id}/tasks/{node_id}/workflow`

Move a task through Maker-Checker: Draft → Pending Review → Approved.

- **Body:** `{"status": "<workflow-state>", "actor_id": "<person-id>"}`
- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **400** `NOT_A_TASK`, `INVALID_WORKFLOW_STATE` (must be one of
  `engine.tasks.WORKFLOW_STATES`), `INVALID_ACTOR` (must resolve via
  `engine.directory.person`)
- **200** `{"workflow": {...}}` — `actor` is recorded as `checker` on entry to
  Pending Review, `approved_by` on entry to Approved.

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}/findings`

The raw finding array for one edge.

- **404** `WORKSTREAM_NOT_FOUND`, `EDGE_NOT_FOUND`
- **200** `[]` if the edge has never been analysed, else the finding array
  verbatim from `findings/{edge_id}.json`.

---

## Graph Screen routes

The workstream canvas, node/edge detail panels, cross-workstream linkage
surfaces, the Review Queue, and per-workstream playbook/guardrails config.

### `GET /api/workstreams`

`{"workstreams": [...]}` — every workstream **except** the three retired ones
(`hidden: true` in `workstream.json`) and the `_cross` pseudo-store. This is the
**only** route that honours the `hidden` flag — every direct-id route below still
serves a hidden workstream on request, so existing links/tests keep working.

### `GET /api/reviewers`

`{"reviewers": [...]}` — the static colleague directory minus the current user
(`engine.directory.selectable_reviewers`). No staff directory exists in MVP1.

### `POST /api/workstreams` — 201

Scaffold a new workstream. **The only route that creates a new tracked directory
under `data/workstreams/`** — on the demo host, calling it dirties the working
tree, a property of the fixture-store-as-database design as a whole.

- **Body:** workstream fields validated by `workstreams.validate_workstream_create`
  (name, deliverable type, etc.) plus optional `reviewer_ids`.
- **400** `NAME_REQUIRED` (non-object body), the specific code+field from
  `validate_workstream_create`, or `INVALID_REVIEWER_ID` (an id not in the
  directory)
- **500** `WORKSTREAM_WRITE_FAILED` — write error
- **200** the new workstream record.

### `GET /api/cross-links`

`{"links": [...]}` — every cross-workstream link in the whole corpus (not scoped
to one workstream). Backs the Home dashboard's Overlap Alerts card and the
Institution Map banner. Each link carries `near`/`far` document identity, a
label tally, `counts`, and the Cross-Workstream Intelligence block
(`classification`, `risk_level`, `shared_attributes`, `reasons`).

### `GET /api/workstreams/{workstream_id}/cross-links`

`{"links": [...]}` — the same link shape, reoriented so `near` is always this
workstream's side. Cross-workstream edges live in the separate `_cross` store
(`data/workstreams/_cross/`, no `workstream.json` of its own, invisible to
`list_workstreams`) because a link's two endpoints belong to different
workstreams' `graph.json` files.

- **404** `WORKSTREAM_NOT_FOUND`
- **200** `{"links": []}` if no `_cross` store exists on disk yet.

### `GET /api/cross-links/{edge_id}`

One cross-workstream relationship in full: both sides' regulatory profile
(`_cross_profile`), what they share, why it was flagged, the label rollup, and
every finding's verbatim clause evidence. Backs the Cross-Workstream
Intelligence relationship panel.

- **404** `CROSS_LINK_NOT_FOUND`

### `GET /api/review-queue`

`{"items": [...], "counts_by_status": {...}}` — every cross-workstream linkage
with its Maker-Checker status, built over the `_cross` store (cross-workstream
overlaps are what most need a human before FPWG).

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}/linkage-review`

`{"edge_id", "linkages": [...]}` — the Maker-Checker record for every finding on
an edge, defaulted to `ai_detected` for a finding never acted on.

- **404** `WORKSTREAM_NOT_FOUND`

### `PATCH /api/workstreams/{workstream_id}/edges/{edge_id}/findings/{finding_id}/linkage-review`

Apply one Maker-Checker action (accept/reject/etc.) to one finding.

- **Body:** `{"action", "actor_id", "comment"?}`
- **400** `UNKNOWN_ACTOR`, `EDGE_NOT_ANALYSED`
- **404** `FINDING_NOT_FOUND`
- **400** the specific `linkage_review.LinkageReviewError` code (invalid
  transition, or maker == checker — enforced by the state machine)
- **200** `{"finding_id", "review": {...}}`

### `GET /api/workstreams/{workstream_id}/playbook`

The drafter's per-stage Copilot instructions. Returns four empty sections for a
workstream that has never saved one — **without creating a file** — so reading a
retired fixture leaves it byte-identical on disk.

- **404** `WORKSTREAM_NOT_FOUND`

### `PUT /api/workstreams/{workstream_id}/playbook`

Full replacement of all four editable sections (the form always sends all four;
an omitted section lands empty).

- **404** `WORKSTREAM_NOT_FOUND`
- **400** `INVALID_PLAYBOOK` (unparseable/non-object body), or the specific
  `playbook.PlaybookValidationError` code+field

### `GET /api/workstreams/{workstream_id}/guardrails`

The rules the recommendations engine follows for this workstream. Serves
`engine.guardrails.DEFAULT_GUARDRAILS` when nothing has been saved yet —
**without creating a file**. `is_default` distinguishes shipped content from a
drafter's deliberate save of the same text.

- **404** `WORKSTREAM_NOT_FOUND`

### `PUT /api/workstreams/{workstream_id}/guardrails`

Replace the guardrails text. An **empty body is accepted deliberately** — clearing
the box is a real decision, and silently reinstating the defaults would overrule
it.

- **Body:** `{"body": "<string>"}`
- **400** `INVALID_GUARDRAILS`
- **413** `GUARDRAILS_TOO_LARGE` (over `guardrails.MAX_GUARDRAILS_CHARS`)

### `GET /api/workstreams/{workstream_id}/graph`

`{"workstream_id", "primary_task_id", "nodes": [...], "edges": [...]}` — the
**whole** workstream graph, not a one-hop projection: a drafter can chain
documents (focal → ED → the sources ED itself references), so clipping to one
hop would make everything beyond the first hop invisible. `primary_task_id`
marks which node the canvas centres on; each edge carries `analysed` and
`findings_count`.

- **404** `WORKSTREAM_NOT_FOUND`

### `GET /api/workstreams/{workstream_id}/nodes/{node_id}`

Full node detail: identity, first-order neighbours (read from the **whole**
workstream, matching the canvas), `recent_activity`, the 7-field `metadata`
regulatory profile, and the extracted-axis `concepts` block.

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **200** — `task_type` is `None` for a context document, or for a working draft
  that predates the deliverable-kind vocabulary (a legacy seeded draft is never
  backfilled). `second_order_neighbours` is a fixed placeholder
  (`{"status": "placeholder", "message": "N/A in demo"}`), retained rather than
  dropped to avoid churning its consumers.

### `GET /api/workstreams/{workstream_id}/nodes/{node_id}/source-pdf`

The node's published PDF, served inline (`Content-Disposition: inline`) so the
browser renders it in a new tab. Resolved against `corpus_dir`; anything that
escapes that root is treated identically to "missing" — the response never
confirms what lies outside the corpus.

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`, `SOURCE_PDF_NOT_FOUND` (no
  `source_pdf` field, or it resolves outside `corpus_dir`, or the file is absent —
  a working draft has none of these by design)

### `DELETE /api/workstreams/{workstream_id}/nodes/{node_id}`

Remove a node and **cascade**: every edge touching it, those edges' findings,
and the node's own anchors + axis cache. Half-deleting would leave findings
citing a gone document, or anchors belonging to no node — states no read path
renders honestly.

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **409** `FOCAL_NODE_PROTECTED` — the primary task node cannot be deleted (it's
  the workstream's anchor; delete the documents around it instead)
- **200** `{"id", "removed_edges": [...]}`

### `DELETE /api/workstreams/{workstream_id}/edges/{edge_id}`

Remove one linkage; both documents stay in place. The edge's findings go with
it, but each document keeps its own passages/concepts, so the pair can be
re-connected and re-analysed later.

- **404** `WORKSTREAM_NOT_FOUND`, `EDGE_NOT_FOUND`
- **200** `{"id"}`

### `POST /api/workstreams/{workstream_id}/nodes/{node_id}/extract-concepts`

Derive a chunked document's concepts (topic axes) from its anchors.
**Synchronous** — the drafter waits while one small-model call runs per anchor;
a per-anchor disk cache makes a re-run on unchanged anchors a hit (no model
call). Every side effect (cache write, activity entry) lands only after full
success.

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **409** `NOT_SEGMENTED` — the node has no anchors (was never chunked)
- **502** `EXTRACTION_FAILED` — model/creds/unparseable-reply failure
- **200** `{"node_id", "concepts": {...}, "recent_activity": [...]}`

### `PUT /api/workstreams/{workstream_id}/nodes/{node_id}/metadata`

Full replacement of the drafter's 7-field regulatory profile for a document. Not
a patch — every save writes all seven keys, so an omitted field lands as `null`
rather than surviving from a prior save.

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **400** the specific `node_metadata.validate_metadata` code+field
- **200** `{"node_id", "metadata": {"status": "available", ...}}` — re-read from
  disk after the write, so the response is provably what got stored.

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}`

Edge detail: both endpoints' identity, `status` (`analysed`/`not_analysed`), the
full finding array, and `analysable` — true only when both endpoints resolve to
**different** ingested documents (comparing a document against itself yields
nothing).

- **404** `WORKSTREAM_NOT_FOUND`, `EDGE_NOT_FOUND`

### `POST /api/workstreams/{workstream_id}/nodes` — 201

Add a new document node. Two request shapes:

1. **`multipart/form-data`** — a JSON `payload` part + one `attachment` file
   (the chunking screen's path). Requires `doc_class`
   (`structured-rules`/`semi-structured`/`prose`) so the segmenter knows how to
   break the document up — the tool never guesses.
2. **Plain JSON body** — a node whose document is fetched by `source_url`, or no
   document at all (`skip_ingest: true` opts out of the URL fetch).

Ingest **and** segment run before the node is persisted, so any failure aborts
before a half-formed node exists.

- **404** `WORKSTREAM_NOT_FOUND`
- **400** `EDGE_REQUIRED` (unparseable body), `ATTACHMENT_REQUIRED` (form POST
  with no file), the specific `workstreams.validate_node_create` code+field,
  `INVALID_DOC_CLASS` (attachment with no `doc_class`), `INVALID_EDGE_TARGET`
- **422** `INGEST_FAILED`, `CHUNKING_FAILED`, `NO_PASSAGES` (document produced
  zero passages)
- **201** `{"id", "node_type", "task_type", "title", "created_edges": [...]}`,
  plus `document_id`/`doc_class`/`anchor_count` when an attachment was chunked.

### `POST /api/workstreams/{workstream_id}/edges` — 201

Connect two **existing** nodes already on the canvas — no analysis runs. Before
this route, linking two existing documents meant deleting and re-adding one
(destroying its passages/concepts).

- **Body:** `{"source_node_id", "target_node_id", "edge_type"}`
- **404** `WORKSTREAM_NOT_FOUND`
- **400** `EDGE_REQUIRED`, the specific `workstreams.validate_edge_create` code
- **404** `NODE_NOT_FOUND` — a referenced node doesn't exist in this workstream
- **409** `DUPLICATE_EDGE` — the same pair joined by the same type in the same
  direction already exists (a _different_ type between the same pair is allowed
  alongside)
- **201** `{...edge, "analysed": false}`

### `POST /api/workstreams/{workstream_id}/edges/{edge_id}/analyze`

**Live model call.** Runs the finder pipeline (`engine.finder_pipeline`) on the
edge's two documents and persists the result. See
[`docs/architecture.md`](architecture.md#secondary-flow-analyzing-an-unanalyzed-edge-live-model-call)
for the full sequence.

- **404** `WORKSTREAM_NOT_FOUND`, `EDGE_NOT_FOUND`
- **409** `NOT_ANALYSABLE` — either endpoint has no ingested document
  (`field: "source"`/`"target"`), or both endpoints resolve to the **same**
  document (nothing to compare)
- **502** `ANALYZE_FAILED` — any pipeline-stage failure (model, creds, network);
  **no partial write** happens, since `save_findings` runs only after full
  success
- **200**:
  - `{"id", "status": "no_linkages_found", "findings": [], "findings_count": 0}`
    when the pipeline found nothing — the edge is deliberately left
    **unanalysed** (not flipped to analysed-with-zero) so it stays re-analysable
  - `{"id", "status": "analysed", "findings": [...], "findings_count": n}`
    otherwise

  "Ours" vs. "theirs" is resolved by the node's position relative to the primary
  task (`workstreams.analysis_direction`), never by edge direction — the live
  fixtures point opposite ways. Findings are persisted in **edge** orientation
  (`source_clauses` belongs to `edge["source"]`), so when "ours" is the edge's
  target, the route analyses target→source and flips the result back before
  saving.

---

## Review Linkages routes

The pairwise clause reader for one edge, and per-finding review-state updates.
Clause text here is served from each finding's own stored `source_clauses` /
`target_clauses` — **never** re-parsed from `data/artifacts/clause-index.json`
(which covers only the RMiT documents) — so the verbatim guarantee holds even
for documents with no clause index at all.

### `GET /api/workstreams/{workstream_id}/edges/{edge_id}/review`

- **Query param:** `finding_id` (optional) — the Pairwise Findings box's deep
  link; echoed back as `active_finding_id`. An **unknown** id 404s rather than
  silently falling back (which would hide a stale link); an **absent** id
  returns `active_finding_id: null` and the screen picks its own default.
- **404** `WORKSTREAM_NOT_FOUND`, `EDGE_NOT_FOUND`, `FINDING_NOT_FOUND`
- **400** `EDGE_NOT_ANALYSED` — distinct from "analysed, zero findings"
- **200**:
  ```json
  {
    "edge": { "id", "edge_type", "source_node": {...}, "target_node": {...} },
    "active_finding_id": null,
    "source_clauses": [ {"clause_number", "text"} ],
    "target_clauses": [ {"clause_number", "text"} ],
    "findings": [...],
    "counts": {...}
  }
  ```
  `source_clauses`/`target_clauses` are every clause any finding on this edge
  cites, de-duplicated by number, in first-cited order. `source_node`/
  `target_node` each carry `has_source_pdf` so the pane knows whether to offer
  the Source PDF button without a separate probe.

### `PATCH /api/workstreams/{workstream_id}/edges/{edge_id}/findings/{finding_id}`

Set one finding's review state (pending/accepted/rejected — see
`engine.findings.REVIEW_STATES`).

- **Body:** `{"review_state": "<state>"}`
- **400** `INVALID_REVIEW_STATE`
- **400** `EDGE_NOT_ANALYSED`
- **404** `FINDING_NOT_FOUND`
- **200** `{"finding": {...}, "counts": {...}}`

---

## Drafting Workspace routes

The editor plus its recommendations / pairwise-findings / draft / Copilot
context panel.

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations`

Never 404s on "not generated yet" — an absent file returns an empty list with
`generated_at: null`, so the card's empty states are ordinary data. `dimensions`
is always populated (needed to distinguish "no policy requirements" from
"nothing accepted yet"). `not_yet_reflected` is **derived on every read**, never
persisted (a stored figure would drift as findings are accepted/rejected after
generation).

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **400** `NOT_A_TASK`

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/generate` — 201

**Live model call.** Generate a fresh recommendation set from the task's
accepted findings.

- **404**/**400** — same task-resolution errors as the GET above
- **409** `NO_POLICY_REQUIREMENTS`, `NO_ACCEPTED_FINDINGS` — both gates are
  checked **before** the model is called, so a closed gate never costs a model
  call
- **502** the specific `recommendations.RecommendationsError` code (any other
  error from that class), or `RECOMMENDATIONS_FAILED` for a raw model/creds/
  network failure
- **201** the generated set, in the same shape as the GET route plus
  `dropped_unsupported` (count of candidates the citation floor rejected)

### `PATCH /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/{rec_id}`

Update one recommendation — currently `bookmarked` (bool) and/or `comment`
(string, appended with the server-resolved author — never taken from the
request body, so a client cannot forge a name). **Idempotent**: setting the
same `bookmarked` value twice succeeds both times.

- **400** `INVALID_PATCH` (missing/wrong-typed field)
- **404** `RECOMMENDATIONS_NOT_GENERATED`, `RECOMMENDATION_NOT_FOUND`
- **400** `EMPTY_COMMENT`
- **413** `COMMENT_TOO_LARGE` (over `recommendations.MAX_COMMENT_CHARS`)
- **200** the updated recommendation.

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/{rec_id}/rewrite`

**Live model call.** Rewrite **one** recommendation from the drafter's comments
on it — keeps its id, bookmark, dimensions, and comments; appends the
superseded text to `revisions`. The citation evidence floor still applies: a
rewrite that resolves no citations is refused and the original is kept
unchanged.

- **404** `RECOMMENDATIONS_NOT_GENERATED`, `RECOMMENDATION_NOT_FOUND`
- **502** the specific `RecommendationsError` code, or `REWRITE_FAILED` for a
  raw failure
- **200** the rewritten recommendation.

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/pairwise-findings`

Every finding in the task's **neighbourhood** (`workstreams.neighbourhood_edges`
— the task's own edges plus every edge incident to a first-order neighbour),
whatever its review state. Backs the Pairwise Findings box. Nothing is
filtered, grouped, or reordered server-side — that's a view concern — except
that unanalysed pairs are reported **separately** from findings (an edge with
no findings file has never been run, a different condition from "analysed, zero
findings").

- **404** `WORKSTREAM_NOT_FOUND`, `NODE_NOT_FOUND`
- **400** `NOT_A_TASK`
- **200**:
  ```json
  {
    "findings": [ /* one card per finding, full neighbourhood, graph order */ ],
    "nodes": [ /* filter chips: every neighbourhood node except the viewed task */ ],
    "unanalysed_pairs": [ {"edge_id", "edge_type", "left", "right"} ],
    "counts": { "total", "by_label": {...all 5 labels, incl. zeroes...},
                "analysed_pairs", "total_pairs" }
  }
  ```

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/reviewed-linkages`

Accepted findings across the same neighbourhood scope as Pairwise Findings —
filtered server-side so the Reviewed tab never receives a dismissed finding to
filter away client-side.

- **404** `WORKSTREAM_NOT_FOUND`
- **400** the `_task_node` error (not-found vs. not-a-task)
- **200** `{"findings": [...]}`

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/related-linkages`

**Deprecated — no frontend surface calls this.** Findings on edges strictly
between the task's neighbours (never touching the task itself). Retained
deliberately as a rollback seam; its tests still run.

- **Query param:** `hops` (must be exactly `1`)
- **400** `HOPS_OUT_OF_RANGE` if `hops != 1`
- **404**/**400** — same task-resolution errors as above
- **200** `{"findings": [...]}`

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/draft`

The working draft's saved HTML (`engine.drafts.load`).

- **404** `WORKSTREAM_NOT_FOUND`, or the `_task_node` error

### `PUT /api/workstreams/{workstream_id}/tasks/{node_id}/draft`

Save the draft. Server-side sanitized with `bleach` — this, not the frontend's
DOMPurify, is the real security boundary (anyone can `curl` this endpoint).

- **Body:** `{"content_html": "<string>"}`
- **400** `INVALID_HTML` (non-string body, or nothing survives sanitization)
- **413** `DRAFT_TOO_LARGE` (over `drafts.MAX_DRAFT_BYTES` post-sanitization)

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/copilot`

**Live model call.** One Copilot turn. The server holds **no conversation
state** — the client sends the full prior history, plus its live (possibly
unsaved) draft HTML and current selection, on every call. `intent` is never
read from the request body — the server resolves it from the task node's
`task_type` (`_resolve_intent`), so a stale client sending `intent` is silently
ignored rather than rejected.

- **Body:** `{"message", "history"?, "referenced_finding_ids"?, "draft_html"?,
"draft_selection"?, "stage"?}`
- **400** `MESSAGE_REQUIRED`
- **404**/**400** — same task-resolution errors as above
- **502** `COPILOT_FAILED`
- **200** `{"reply": {...}}`

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/copilot/stream`

Same contract as `copilot` above, but returns an SSE stream
(`text/event-stream`) via `copilot_stream_fn` instead of a single JSON reply.

---

## Error code index

Every `{code}` value used above, for quick lookup:

| Code                                                         | Where                         | Meaning                                                                                     |
| ------------------------------------------------------------ | ----------------------------- | ------------------------------------------------------------------------------------------- |
| `WORKSTREAM_NOT_FOUND`                                       | almost every route            | `workstream_id` has no `graph.json`                                                         |
| `NODE_NOT_FOUND`                                             | node/task routes              | node id not in the workstream's graph                                                       |
| `EDGE_NOT_FOUND`                                             | edge routes                   | edge id not in the workstream's graph                                                       |
| `FINDING_NOT_FOUND`                                          | review/linkage-review routes  | finding id not on that edge                                                                 |
| `NOT_A_TASK`                                                 | task-scoped routes            | node exists but isn't `node_type: task`                                                     |
| `TASK_NOT_FOUND`                                             | drafting-workspace routes     | collapses not-found + not-a-task into one code (workspace is only ever reached from a task) |
| `EDGE_NOT_ANALYSED`                                          | review, linkage-review        | no `findings/{edge_id}.json` yet                                                            |
| `NOT_ANALYSABLE`                                             | analyze                       | an endpoint has no document, or both sides are the same document                            |
| `ANALYZE_FAILED`                                             | analyze                       | pipeline call raised (model/creds/network)                                                  |
| `FOCAL_NODE_PROTECTED`                                       | delete node                   | the primary task node can't be deleted                                                      |
| `DUPLICATE_EDGE`                                             | create edge                   | same pair + type + direction already exists                                                 |
| `INVALID_EDGE_TARGET`                                        | create node                   | an inline edge's target doesn't exist                                                       |
| `ATTACHMENT_REQUIRED` / `INVALID_DOC_CLASS`                  | create node                   | form POST needs a file / a `doc_class`                                                      |
| `INGEST_FAILED` / `CHUNKING_FAILED` / `NO_PASSAGES`          | create node                   | document read/segment failure                                                               |
| `NOT_SEGMENTED`                                              | extract-concepts              | node has no anchors yet                                                                     |
| `EXTRACTION_FAILED`                                          | extract-concepts              | model call failed                                                                           |
| `INVALID_METADATA`                                           | node metadata                 | validation failure (see `field`)                                                            |
| `INVALID_PLAYBOOK` / `INVALID_GUARDRAILS`                    | playbook, guardrails          | bad body shape                                                                              |
| `GUARDRAILS_TOO_LARGE`                                       | guardrails                    | over `MAX_GUARDRAILS_CHARS`                                                                 |
| `INVALID_REVIEW_STATE`                                       | patch finding                 | not one of `findings.REVIEW_STATES`                                                         |
| `INVALID_WORKFLOW_STATE` / `INVALID_ACTOR`                   | workflow                      | bad status / unknown actor id                                                               |
| `UNKNOWN_ACTOR`                                              | linkage-review                | actor id not in the directory                                                               |
| `NO_POLICY_REQUIREMENTS` / `NO_ACCEPTED_FINDINGS`            | recommendations/generate      | pre-model gates                                                                             |
| `RECOMMENDATIONS_NOT_GENERATED` / `RECOMMENDATION_NOT_FOUND` | recommendations patch/rewrite | no set yet / bad `rec_id`                                                                   |
| `EMPTY_COMMENT` / `COMMENT_TOO_LARGE`                        | recommendation comment        | validation                                                                                  |
| `REWRITE_FAILED` / `RECOMMENDATIONS_FAILED`                  | recommendations               | raw model/creds/network failure                                                             |
| `INVALID_HTML` / `DRAFT_TOO_LARGE`                           | draft                         | sanitization / size limit                                                                   |
| `MESSAGE_REQUIRED`                                           | copilot                       | empty/missing `message`                                                                     |
| `COPILOT_FAILED`                                             | copilot                       | live model call failed                                                                      |
| `HOPS_OUT_OF_RANGE`                                          | related-linkages (deprecated) | `hops != 1`                                                                                 |
| `SOURCE_PDF_NOT_FOUND`                                       | source-pdf                    | no PDF, or path escapes `corpus_dir`                                                        |
| `CROSS_LINK_NOT_FOUND`                                       | cross-links detail            | edge id not in the `_cross` store                                                           |
| `WORKSTREAM_WRITE_FAILED`                                    | create workstream             | disk write error                                                                            |
| `NAME_REQUIRED` / `INVALID_REVIEWER_ID`                      | create workstream             | body/field validation                                                                       |
| `INTERNAL_ERROR`                                             | get task                      | any unexpected load failure (500)                                                           |
