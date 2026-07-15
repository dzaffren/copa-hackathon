// Contract types mirroring the Workstream Brain FastAPI engine
// (`GET /api/workstreams/{id}/tasks/{nodeId}` and `.../edges/{edgeId}/findings`).

export type NodeType =
  | "task"
  | "international-standard"
  | "peer-regulator"
  | "internal-published"
  | "act-law"
  | "industry-input";

export type EdgeType = "contributes-to" | "parallel-to" | "references";

export type SemanticLabel =
  "aligns-with" | "differs-on" | "conflicts-with" | "silent-on" | "goes-beyond";

export type Sentiment = "tighten" | "loosen" | null;

export interface Person {
  id: string;
  name: string;
}

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
