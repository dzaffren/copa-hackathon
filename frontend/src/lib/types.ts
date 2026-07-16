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

export interface TaskResponse {
  task: Task;
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

export interface NodeDetail {
  id: string;
  node_type: NodeType;
  title: string;
  issuer: string | null;
  short_type: string | null;
  description: string | null;
  source_url: string | null;
  first_order_neighbours: NeighbourRef[];
  second_order_neighbours: Placeholder;
  recent_activity: RecentActivity[];
  concepts: Placeholder;
}

export interface EdgeEndpoint {
  id: string;
  title: string;
  node_type: NodeType;
}

export interface EdgeDetail {
  id: string;
  source: EdgeEndpoint;
  target: EdgeEndpoint;
  edge_type: EdgeType;
  status: "analysed" | "not_analysed";
  findings: Connection[];
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
  status: "analysed";
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
}

export interface CrossLinksResponse {
  links: CrossLink[];
}

/** The store holding edges whose endpoints live in different workstreams. Not a
 *  workstream: it has no workstream.json and never appears in the sidebar. */
export const CROSS_STORE = "_cross";
