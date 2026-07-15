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
