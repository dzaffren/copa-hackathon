// Contract types mirroring the Workstream Brain FastAPI engine.
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

export type EdgeType =
  "contributes-to" | "parallel-to" | "references" | "supersedes";

export type WorkstreamRole = "own" | "review" | "delivered";

export type SemanticLabel =
  "aligns-with" | "differs-on" | "conflicts-with" | "silent-on" | "goes-beyond";

export type Sentiment = "tighten" | "loosen" | null;

export interface Person {
  id: string;
  name: string;
}

// --- Task Screen (unchanged from #36) --------------------------------------

export interface Task {
  id: string;
  title: string;
  source_name: string;
  format: string;
  description: string;
  status: string;
  owner: Person;
  reviewers: Person[];
  clause_count: number;
  last_edited_at: string;
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

/** The seven concept fields, offline-enriched (scripts/enrich_node_metadata.py).
 *  Each is either a verbatim clause quote or a value already on the node
 *  (`owner`) — never invented. A field the enrichment could not derive is
 *  `null`, not omitted, so the panel can render "not available" per field. */
export interface ConceptsAvailable {
  status: "available";
  policy_owner: string | null;
  applicability: string | null;
  empowerment_framework: string | null;
  requirement: string | null;
  issuance_date: string | null;
  effective_date: string | null;
  /** A list of topic keywords once enriched (older side-files may carry a bare
   *  string or null). */
  keywords: string[] | string | null;
  /** Acts the document is issued under, e.g. `["FSA 2013", "IFSA 2013"]` — a
   *  shared Act is a strong cross-workstream overlap signal. May be absent on
   *  side-files written before this field existed. */
  legal_basis?: string[] | null;
  /** BNM ISMP classification. No offline source exists yet (its authority is
   *  CAS's RH publication form), so this is `null` today — the field is
   *  present so the panel can render "pending" rather than hide the concept. */
  ismp_classification?: string | null;
}

export interface NodeDetail {
  id: string;
  node_type: NodeType;
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
  concepts: Placeholder | ConceptsAvailable;
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

export interface CreateNodeRequest {
  node_type: NodeType;
  title: string;
  description?: string | null;
  source_url?: string | null;
  attachment_submission_id?: string | null;
  edges: CreateNodeEdge[];
}

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
  title: string;
  created_edges: CreatedEdge[];
}

export interface AnalyzeResponse {
  id: string;
  /** The finder can genuinely surface nothing for a pair — see CLAUDE.md's
   *  verbatim-citation rule ("no matching clause found" beats a fabricated
   *  one). `no_matching_source` leaves the edge unanalysed and re-analysable. */
  status: "analysed" | "no_matching_source";
  findings: Connection[];
  findings_count: number;
}

// --- Drafting Workspace ----------------------------------------------------

/** The seven Copilot intent presets. Cosmetic in MVP1 beyond keying the
 *  scripted reply map — they signal the surface area the tool will cover. */
export type CopilotIntent =
  | "PD"
  | "DP"
  | "ED"
  | "FAQ"
  | "Engagement Deck"
  | "Feedback Template for Industry"
  | "Peer Benchmarking";

export const COPILOT_INTENTS: CopilotIntent[] = [
  "PD",
  "DP",
  "ED",
  "FAQ",
  "Engagement Deck",
  "Feedback Template for Industry",
  "Peer Benchmarking",
];

/** Human labels for the intent dropdown. The wire values stay terse. */
export const COPILOT_INTENT_LABELS: Record<CopilotIntent, string> = {
  PD: "PD — Policy Document",
  DP: "DP — Discussion Paper",
  ED: "ED — Exposure Draft",
  FAQ: "FAQ",
  "Engagement Deck": "Engagement Deck",
  "Feedback Template for Industry": "Feedback Template for Industry",
  "Peer Benchmarking": "Peer Benchmarking",
};

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

export interface DraftResponse {
  node_id: string;
  content_html: string;
  last_saved_at: string | null;
}

/** A clause the Copilot quotes. `text` is verbatim from the clause index or the
 *  findings fixtures — see engine/copilot_scripts.py. */
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

// --- New Workstream --------------------------------------------------------

/** Wire codes for the deliverable dropdown. The server maps these to the human
 *  labels the fixtures store ("PD" → "Policy Document"). */
export type DeliverableTypeCode = "PD" | "ED" | "DP" | "Other";

export const DELIVERABLE_TYPE_OPTIONS: {
  code: DeliverableTypeCode;
  label: string;
}[] = [
  { code: "PD", label: "Policy Document (PD)" },
  { code: "ED", label: "Exposure Draft (ED)" },
  { code: "DP", label: "Discussion Paper (DP)" },
  { code: "Other", label: "Other" },
];

export type AccessLevel = "team_only" | "department_wide";

export interface Person {
  id: string;
  name: string;
}

export interface CreateWorkstreamRequest {
  name: string;
  description?: string;
  deliverable_type: DeliverableTypeCode;
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
  | "conflict"
  | "divergent"
  | "overlap"
  | "aligned";

export type RiskLevel = "high" | "medium" | "low";

/** What two documents share — each the shared value itself (so the panel quotes
 *  "FSA 2013, IFSA 2013"), never a bare boolean. A signal is present only when
 *  both sides carry it. */
export interface SharedAttributes {
  legal_basis: string[];
  applicability: string[];
  keywords: string[];
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
  | "claim"
  | "submit"
  | "pick_up"
  | "approve"
  | "reject"
  | "request_changes";

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
