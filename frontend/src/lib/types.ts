// Contract types mirroring the Project SELARAS FastAPI engine.
// Task Screen: `GET /api/workstreams/{id}/tasks/{nodeId}`, `.../edges/{edgeId}/findings`.
// Graph Screen: `GET /api/workstreams`, `.../{id}/graph`, `.../nodes/{id}`,
//   `.../edges/{id}`, `POST .../nodes`, `POST .../edges/{id}/analyze`.

export type NodeType =
  | "task"
  | "international-standard"
  | "peer-regulator"
  | "internal-published"
  | "act-law"
  | "industry-input"
  | "supervisory-letter"
  | "others";

export type EdgeType = "parallel-to" | "references" | "supersedes";

export type WorkstreamRole = "own" | "review" | "delivered";

export type SemanticLabel =
  "aligns-with" | "differs-on" | "conflicts-with" | "silent-on" | "goes-beyond";

export type Sentiment = "tighten" | "loosen" | null;

export interface Person {
  id: string;
  name: string;
}

// --- Task Screen (unchanged from #36) --------------------------------------

// Every field below the identity pair is nullable because a focal node
// scaffolded by `create_workstream` carries identity only — no document is
// attached, so there is no source name, format, status or edit stamp to report.
// `owner` is filled from the workstream record, but stays nullable: nothing
// guarantees a record has one, and a non-null type here is what let a live
// workstream crash the Task Screen.
export interface Task {
  id: string;
  title: string;
  source_name: string | null;
  format: string | null;
  description: string | null;
  status: string | null;
  owner: Person | null;
  reviewers: Person[];
  clause_count: number;
  last_edited_at: string | null;
}

export interface Neighbour {
  node_id: string;
  title: string;
  node_type: NodeType;
  edge_type: EdgeType;
  edge_id: string;
  analysed: boolean;
  findings_count: number;
}

export type TaskWorkflowStatus = "draft" | "pending_review" | "approved";

/** The persisted Maker-Checker state for a task (`engine/tasks.py`) — the
 *  single source of truth the frontend reads instead of re-deriving it. */
export interface TaskWorkflow {
  status: TaskWorkflowStatus;
  checker: Person | null;
  approved_by: Person | null;
  approved_at: string | null;
}

export interface TaskResponse {
  task: Task;
  workflow: TaskWorkflow;
  neighbours: Neighbour[];
  draft_empty: boolean;
}

export interface ClauseRef {
  clause_number: string;
  text: string;
}

export interface Connection {
  summary: string;
  label: SemanticLabel;
  sentiment: Sentiment;
  scope_note: string | null;
  supported: boolean;
  source_clauses: ClauseRef[];
  target_clauses: ClauseRef[];
}

// --- Review Linkages -------------------------------------------------------
// `GET .../edges/{edgeId}/review`, `PATCH .../edges/{edgeId}/findings/{id}`.

export type ReviewState = "pending" | "accepted" | "dismissed";

/** A finding as the review screen sees it: a Connection plus the two fields the
 *  engine derives on read — a stable id and a review state. */
export interface ReviewFinding extends Connection {
  id: string;
  review_state: ReviewState;
}

/** A clause card in a pane. Text is the verbatim citation stored on the finding
 *  that cites it — the engine never re-parses it from a clause index. */
export interface ReviewClause {
  clause_number: string;
  text: string;
}

export interface ReviewEdgeNode {
  id: string;
  title: string | null;
  node_type: NodeType | null;
}

export interface ReviewCounts {
  total: number;
  accepted: number;
  dismissed: number;
}

export interface ReviewResponse {
  edge: {
    id: string;
    edge_type: EdgeType | null;
    source_node: ReviewEdgeNode;
    target_node: ReviewEdgeNode;
  };
  /** The finding named by the caller's `finding_id`, echoed back so the screen
   *  can open on the card the drafter clicked in the Pairwise Findings box.
   *  `null` when no finding was nominated — the screen then falls back to its
   *  own first-selectable default. */
  active_finding_id: string | null;
  source_clauses: ReviewClause[];
  target_clauses: ReviewClause[];
  findings: ReviewFinding[];
  counts: ReviewCounts;
}

export interface PatchReviewStateResponse {
  finding: ReviewFinding;
  counts: ReviewCounts;
}

// --- Graph Screen ----------------------------------------------------------

export interface WorkstreamSummary {
  id: string;
  name: string;
  deliverable_type: string | null;
  role: WorkstreamRole;
}

export interface GraphNode {
  id: string;
  node_type: NodeType;
  title: string;
  issuer: string | null;
  short_type: string | null;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: EdgeType;
  analysed: boolean;
  findings_count: number;
  /** Set by callers merging multiple workstreams' graphs into one canvas
   *  (the institution map) to force the cross-workstream rose/dashed
   *  rendering regardless of `edge_type`. Absent/false for an ordinary
   *  intra-workstream edge. */
  cross?: boolean;
}

export interface WorkstreamGraph {
  workstream_id: string;
  primary_task_id: string | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NeighbourRef {
  id: string;
  node_type: NodeType;
  title: string;
}

export interface RecentActivity {
  kind: "edit" | "comment" | string;
  author: string;
  at: string;
  summary: string;
}

export interface Placeholder {
  status: string;
  message: string;
}

/** The six regulatory-profile fields, drafter-editable and also written by the
 *  offline enrichment (scripts/enrich_node_metadata.py). A field nobody has
 *  filled in is `null`, not omitted, so the panel renders "Not set" per field.
 *
 *  `keywords` and `requirement` were removed on 30 Jul 2026 — the extracted axes
 *  (the Concepts section) carry a document's topics from the document itself.
 *  `empowerment_framework` was removed on 31 Jul 2026 — `legal_basis` and the
 *  node's `pursuant_to` already carry the statutory basis. */
export interface ConceptsAvailable {
  status: "available";
  policy_owner: string | null;
  applicability: string | null;
  issuance_date: string | null;
  effective_date: string | null;
  /** Acts the document is issued under, e.g. `["FSA 2013", "IFSA 2013"]`. May be
   *  absent on side-files written before this field existed. */
  legal_basis?: string[] | null;
  /** BNM security classification — one of UMUM / TERHAD / SULIT / RAHSIA, or
   *  `null` when nobody has recorded one, which the panel renders as pending
   *  rather than as a guess. */
  ismp_classification?: string | null;
}

export interface NodeDetail {
  id: string;
  node_type: NodeType;
  /** The deliverable kind, set once at creation and thereafter read-only.
   *  `null` on a context document, and on a legacy draft that carries none. */
  task_type: TaskTypeCode | null;
  title: string;
  issuer: string | null;
  short_type: string | null;
  description: string | null;
  source_url: string | null;
  /** Governance badges — present only once offline enrichment has run for
   *  this node; `null` otherwise, never fabricated. */
  ismp_classification: string | null;
  pursuant_to: string | null;
  first_order_neighbours: NeighbourRef[];
  second_order_neighbours: Placeholder;
  recent_activity: RecentActivity[];
  /** The six-field regulatory profile. Formerly served as `concepts`; renamed
   *  when `concepts` was repurposed for extracted axes. */
  metadata: Placeholder | ConceptsAvailable;
  /** The document's extracted topics, shown as pills. `not_extracted` (with an
   *  empty list) is the expected state until the drafter extracts them. */
  concepts: NodeConcepts;
}

export type NodeConcepts =
  | { status: "extracted"; axes: string[] }
  | { status: "not_extracted"; axes: [] };

export interface ExtractConceptsResponse {
  node_id: string;
  concepts: NodeConcepts;
  recent_activity: RecentActivity[];
}

/** The six editable profile fields. Every key is sent on every save — the
 *  server does a full replacement, so an omitted field is stored as null. That
 *  is what makes "clear a field" and "never filled it in" the same state. */
export interface NodeMetadataRequest {
  policy_owner: string | null;
  applicability: string | null;
  issuance_date: string | null;
  effective_date: string | null;
  legal_basis: string[] | null;
  /** One of UMUM / TERHAD / SULIT / RAHSIA, or null for unset. */
  ismp_classification: string | null;
}

export interface NodeMetadataResponse {
  node_id: string;
  /** The saved profile in the GET's `metadata` shape, so the client can drop it
   *  straight into its cache. */
  metadata: ConceptsAvailable;
}

export interface EdgeEndpoint {
  id: string;
  title: string;
  node_type: NodeType;
  document_id: string | null;
}

export interface EdgeDetail {
  id: string;
  source: EdgeEndpoint;
  target: EdgeEndpoint;
  edge_type: EdgeType;
  status: "analysed" | "not_analysed";
  findings: Connection[];
  analysable: boolean;
}

export interface CreateNodeEdge {
  target_node_id: string;
  edge_type: EdgeType;
}

/** How an attached document is broken into citable passages. Declared by the
 *  drafter, never inferred — a wrong guess chops a document into useless
 *  passages. `structured-rules` only suits numbered BNM policies. */
export type DocClass = "structured-rules" | "semi-structured" | "prose";

export interface CreateNodeRequest {
  node_type: NodeType;
  /** Required when `node_type` is `task`, refused otherwise — the server sends
   *  `INVALID_TASK_TYPE` / `TASK_TYPE_NOT_ALLOWED` rather than dropping it. */
  task_type?: TaskTypeCode;
  title: string;
  description?: string | null;
  source_url?: string | null;
  attachment_submission_id?: string | null;
  edges: CreateNodeEdge[];
  /** Opt out of the server-side URL download + ingest of `source_url`. */
  skip_ingest?: boolean;
  /** Required when an attachment is sent; the server rejects a file without it. */
  doc_class?: DocClass;
}

export interface CreateEdgeRequest {
  source_node_id: string;
  target_node_id: string;
  edge_type: EdgeType;
}

/** The persisted edge. `source`/`target` may be swapped relative to the request:
 *  a task endpoint is always stored as the source (edges read task → anchor). */
export type CreateEdgeResponse = CreatedEdge;

export interface CreatedEdge {
  id: string;
  source: string;
  target: string;
  edge_type: EdgeType;
  analysed: boolean;
}

export interface CreateNodeResponse {
  id: string;
  node_type: NodeType;
  task_type?: TaskTypeCode | null;
  title: string;
  created_edges: CreatedEdge[];
  /** Present only when a document was attached and chunked. */
  document_id?: string;
  doc_class?: DocClass;
  anchor_count?: number;
}

export interface DeleteNodeResponse {
  id: string;
  /** Ids of the edges removed with the node — their findings went too. */
  removed_edges: string[];
}

export interface DeleteEdgeResponse {
  id: string;
}

export interface AnalyzeResponse {
  id: string;
  /** The finder can genuinely surface nothing for a pair — see CLAUDE.md's
   *  verbatim-citation rule ("no matching clause found" beats a fabricated
   *  one). `no_linkages_found` leaves the edge unanalysed and re-analysable. */
  status: "analysed" | "no_linkages_found";
  findings: Connection[];
  findings_count: number;
}

// --- Drafting Workspace ----------------------------------------------------

// The Copilot's intent preset vocabulary lived here as `CopilotIntent` /
// `COPILOT_INTENTS` / `COPILOT_INTENT_LABELS`. It is gone: the deliverable kind
// is now `TASK_TYPE_OPTIONS` above, recorded on the task node at creation, and
// the server reads it off that node. The drafter is never asked what they are
// drafting, so there is no dropdown and no client-sent `intent`.

export interface LinkageEndpoint {
  id: string;
  title: string | null;
  node_type: NodeType | null;
}

/** A side-panel card. Carries clause NUMBERS only, never clause text: the
 *  cards are references into the review reader, so they cannot misquote. */
export interface LinkageCard {
  id: string;
  label: SemanticLabel;
  sentiment: Sentiment;
  summary: string;
  edge_id: string;
  left: LinkageEndpoint;
  right: LinkageEndpoint;
  source_clause_number: string | null;
  target_clause_number: string | null;
}

export interface LinkagesResponse {
  findings: LinkageCard[];
}

// --- Pairwise Findings -----------------------------------------------------
// `GET .../tasks/{nodeId}/pairwise-findings`. Every finding in the task's
// neighbourhood — the task's own edges plus every edge incident to a first-order
// neighbour — whatever its review state. Grouping, sinking judged cards and
// filtering by node are all view concerns, so the server sends the full set in
// graph order and the browser never refetches to reorder.

/** A `LinkageCard` plus the review state the box needs to mute and sink a
 *  judged card. Clause NUMBERS only, as with every card shape. */
export interface PairwiseFinding extends LinkageCard {
  review_state: ReviewState;
}

/** One chip in the node filter. Every neighbourhood document except the viewed
 *  task — including a second task node, where the fixture has one. A document
 *  whose pair is unanalysed still gets a chip, at zero. */
export interface PairwiseFilterNode {
  id: string;
  title: string | null;
  node_type: NodeType | null;
  findings_count: number;
}

/** A pair with no findings file: never analysed, as distinct from analysed with
 *  zero findings. Drives the coverage strip. */
export interface UnanalysedPair {
  edge_id: string;
  edge_type: EdgeType | null;
  left: LinkageEndpoint;
  right: LinkageEndpoint;
}

/** Per-label totals. `total` never moves as findings are judged; `pending`
 *  falls. All five labels are always present, including zeroes, so the UI never
 *  synthesises a missing group. */
export interface LabelCount {
  total: number;
  pending: number;
}

export interface PairwiseFindingsResponse {
  findings: PairwiseFinding[];
  nodes: PairwiseFilterNode[];
  unanalysed_pairs: UnanalysedPair[];
  counts: {
    total: number;
    by_label: Record<SemanticLabel, LabelCount>;
    analysed_pairs: number;
    total_pairs: number;
  };
}

export interface DraftResponse {
  node_id: string;
  content_html: string;
  last_saved_at: string | null;
}

/** A clause the Copilot quotes. `text` is always re-quoted server-side from
 *  already-verbatim clause/finding text — see engine/copilot.py's
 *  `_validate_reply` guardrail — never trusted from the model's own echo. */
export interface CopilotCitation {
  clause_number: string;
  text: string;
}

export interface CopilotReply {
  role: "copilot";
  text: string;
  citations?: CopilotCitation[];
  snippet_html?: string;
}

export interface CopilotResponse {
  reply: CopilotReply;
}

/** A rendered chat turn. The user's own turns never carry citations. */
export interface ChatMessage {
  role: "user" | "copilot";
  text: string;
  citations?: CopilotCitation[];
  snippet_html?: string;
}

/** One turn of the request-side conversation history sent to the Copilot —
 *  the server holds no conversation state (deliberately not persisted across
 *  sessions), so the client sends the full prior history on every call. */
export interface ChatHistoryTurn {
  role: "user" | "copilot";
  text: string;
}

/** The drafter's live editor state, sent with each Copilot message so the
 *  Copilot can see what they are working on. `draftHtml` is the full current
 *  draft (possibly unsaved); `selectionText` is the passage they have
 *  highlighted, if any. Both are non-citable context server-side. */
export interface CopilotDraftContext {
  draftHtml: string;
  selectionText: string;
}

/** Payload of the SSE `done` event from `POST .../copilot/stream`. */
export interface StreamingCopilotDone {
  text?: string;
  citations?: CopilotCitation[];
  snippet_html?: string;
}

/** A parsed SSE event from the Copilot streaming endpoint. */
export type SSEEvent =
  | { event: "token"; data: { t: string } }
  | { event: "done"; data: StreamingCopilotDone }
  | { event: "error"; data: { code: string; message: string } };

// --- New Workstream --------------------------------------------------------

/** Wire codes for the eight deliverable kinds BNM publishes — the one vocabulary
 *  asked at workstream creation and of every new working draft. Mirrors
 *  `engine/workstreams.py::TASK_TYPES`, whose order this preserves. */
export type TaskTypeCode =
  "PD" | "DP" | "ED" | "FAQ" | "DECK" | "FEEDBACK" | "BENCHMARK" | "OTHERS";

/** Drafter-facing labels. These differ from the labels the engine STORES
 *  ("PD" → "Policy Document"): a picker needs the short form visible, because
 *  the code is what an auto-generated draft title embeds. The asymmetry is
 *  deliberate and documented above `TASK_TYPES` in the engine. */
export const TASK_TYPE_OPTIONS: { code: TaskTypeCode; label: string }[] = [
  { code: "PD", label: "PD — Policy Document" },
  { code: "DP", label: "DP — Discussion Paper" },
  { code: "ED", label: "ED — Exposure Draft" },
  { code: "FAQ", label: "FAQ" },
  { code: "DECK", label: "Engagement Deck" },
  { code: "FEEDBACK", label: "Feedback Template for Industry" },
  { code: "BENCHMARK", label: "Peer Benchmarking" },
  { code: "OTHERS", label: "Others" },
];

export type AccessLevel = "team_only" | "department_wide";

export interface Person {
  id: string;
  name: string;
}

export interface CreateWorkstreamRequest {
  name: string;
  description?: string;
  deliverable_type: TaskTypeCode;
  target_publication?: string;
  reviewer_ids: string[];
  access: AccessLevel;
}

export interface CreateWorkstreamResponse {
  id: string;
  name: string;
  deliverable_type: string;
  role: WorkstreamRole;
  description: string | null;
  primary_task_id: string | null;
  target_publication: string | null;
  owner: Person;
  reviewers: Person[];
  access: AccessLevel;
  created_at: string;
}

// --- Cross-workstream linkage ----------------------------------------------

export interface CrossLinkEnd {
  node_id: string;
  title: string | null;
  workstream_id: string | null;
  /** Only the far side carries this — the near side is the workstream you asked from. */
  workstream_name?: string | null;
}

/** How a relationship's linkages roll up: a `conflicts-with` anywhere makes it
 *  a conflict, `differs-on` divergent, `goes-beyond`/`silent-on` an overlap,
 *  and only `aligns-with` aligned. Derived server-side (engine/cross_intel.py). */
export type RelationshipClassification =
  "conflict" | "divergent" | "overlap" | "aligned";

export type RiskLevel = "high" | "medium" | "low";

/** What two documents share — each the shared value itself (so the panel quotes
 *  "FSA 2013, IFSA 2013"), never a bare boolean. A signal is present only when
 *  both sides carry it. */
export interface SharedAttributes {
  legal_basis: string[];
  applicability: string[];
  policy_owner: string | null;
  ismp_classification: string | null;
}

export interface CrossLink {
  id: string;
  edge_type: EdgeType;
  near: CrossLinkEnd;
  far: CrossLinkEnd;
  findings_count: number;
  /** Tally by semantic label, so the card reads "12 linkages · 4 differ"
   *  without fetching every finding. */
  labels: Partial<Record<SemanticLabel, number>>;
  counts: ReviewCounts;
  /** Cross-Workstream Intelligence enrichment (engine/cross_intel.py). */
  classification: RelationshipClassification;
  risk_level: RiskLevel;
  detected_at: string | null;
  shared_attributes: SharedAttributes;
  reasons: string[];
}

export interface CrossLinksResponse {
  links: CrossLink[];
}

/** One side of a relationship-detail: the document plus its regulatory profile
 *  (concept metadata), for the intelligence panel and the comparison view. */
export interface CrossProfile {
  node_id: string;
  title: string | null;
  node_type: NodeType | null;
  issuer: string | null;
  short_type: string | null;
  description: string | null;
  workstream_id: string | null;
  workstream_name: string | null;
  concepts: Placeholder | ConceptsAvailable;
}

/** The full "why do these overlap, and what's the evidence" payload behind the
 *  Cross-Workstream Intelligence relationship panel. */
export interface CrossLinkDetail {
  id: string;
  edge_type: EdgeType;
  detected_at: string | null;
  classification: RelationshipClassification;
  risk_level: RiskLevel;
  near: CrossProfile;
  far: CrossProfile;
  shared_attributes: SharedAttributes;
  reasons: string[];
  labels: Partial<Record<SemanticLabel, number>>;
  counts: ReviewCounts;
  findings: ReviewFinding[];
}

// --- Per-linkage Maker-Checker workflow ------------------------------------

/** The seven maker-checker statuses a linkage moves through
 *  (engine/linkage_review.py). ai_detected → maker_review → submitted_for_check
 *  → checker_review → approved | rejected | changes_requested (which loops back
 *  to submitted_for_check). */
export type LinkageStatus =
  | "ai_detected"
  | "maker_review"
  | "submitted_for_check"
  | "checker_review"
  | "approved"
  | "rejected"
  | "changes_requested";

/** The transition verbs the API accepts. */
export type LinkageAction =
  "claim" | "submit" | "pick_up" | "approve" | "reject" | "request_changes";

export interface LinkageComment {
  author: Person;
  at: string;
  text: string;
}

export interface LinkageAuditEntry {
  actor: Person;
  action: LinkageAction;
  from: LinkageStatus;
  to: LinkageStatus;
  at: string;
  comment: string | null;
}

/** A single linkage's maker-checker record — a real audit trail, not a flag. */
export interface LinkageReviewRecord {
  status: LinkageStatus;
  maker: Person | null;
  checker: Person | null;
  created_at: string | null;
  checked_at: string | null;
  comments: LinkageComment[];
  audit: LinkageAuditEntry[];
}

export interface LinkageReviewRow {
  finding_id: string;
  summary: string | null;
  label: SemanticLabel;
  sentiment: Sentiment;
  review: LinkageReviewRecord;
}

export interface LinkageReviewResponse {
  edge_id: string;
  linkages: LinkageReviewRow[];
}

/** One row in the Review Queue: a cross-workstream linkage plus its status. */
export interface ReviewQueueItem {
  workstream_id: string;
  edge_id: string;
  finding_id: string;
  summary: string | null;
  label: SemanticLabel;
  sentiment: Sentiment;
  near: CrossLinkEnd;
  far: CrossLinkEnd;
  status: LinkageStatus;
  maker: Person | null;
  checker: Person | null;
  created_at: string | null;
  checked_at: string | null;
}

export interface ReviewQueueResponse {
  items: ReviewQueueItem[];
  counts_by_status: Record<LinkageStatus, number>;
}

export interface LinkageTransitionRequest {
  action: LinkageAction;
  actor_id: string;
  comment?: string;
}

export interface LinkageTransitionResponse {
  finding_id: string;
  review: LinkageReviewRecord;
}

/** The store holding edges whose endpoints live in different workstreams. Not a
 *  workstream: it has no workstream.json and never appears in the sidebar. */
export const CROSS_STORE = "_cross";
