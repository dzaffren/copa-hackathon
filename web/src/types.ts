// Shared TypeScript contract for Rulebook Radar's web app.
//
// The engine-facing types bind EXACTLY to the FastAPI read service in
// `engine/api.py` (+ the `GraphNode`/`GraphEdge` TypedDicts in `engine/graph.py`
// and the `FindConnectionsResult` shape in `engine/connections.py`). No invented
// fields — every property here appears in a real engine response. See
// `docs/specs/rulebook-radar/spec-drafter-workspace.md` (API Design / Data Model).
//
// The workflow-state types (`Finding`, `TrackedChange`) are client-only records
// stored in `localStorage` by `web/src/lib/workflowState.ts` (Task 3) and written
// by the alignment (#8) and copilot (#9) stories. #7 only defines + reads them.

// ---------------------------------------------------------------------------
// Engine graph contract (GET /graph, from engine/graph.py)
// ---------------------------------------------------------------------------

/**
 * A node in the knowledge graph. Internal policy nodes carry the six required
 * fields; external **reference** nodes (`kind === "reference"`, #26) additionally
 * carry `source_type` / `access` / `preview` and, for public references, a
 * `source_url`. A consumer that ignores the reference fields is unaffected
 * (existing policy nodes default `kind` to `"policy"`).
 */
export interface GraphNode {
  id: string;
  policy_id: string;
  title: string;
  version: string;
  /** Derived by the engine: "In force" | "Superseded" | "In progress". */
  status: string;
  cluster: string;
  // Reference-node fields — present ONLY on `kind === "reference"` nodes.
  kind?: string; // "policy" (default) | "reference"
  source_type?: string; // peer_regulator | act | standard | handbook | trend
  access?: string; // public | restricted
  preview?: boolean; // true → labelled preview band, no verbatim excerpt
  source_url?: string; // public references only
}

/**
 * An edge in the knowledge graph. `GET /graph` returns full edges with clause
 * anchors + provenance + confidence; the clause-anchor fields are optional here
 * because structural `version-lineage` edges carry empty anchor arrays and the
 * per-node convenience shape (`NodeDetail.edges`) omits them entirely.
 */
export interface GraphEdge {
  source: string;
  target: string;
  /** e.g. "overlaps" | "version-lineage" | "references". */
  type: string;
  reason: string;
  source_clauses?: string[];
  target_clauses?: string[];
  provenance?: string; // structural | curated | llm-found
  confidence?: number; // 0.0 – 1.0
}

/** The whole graph as returned by `GET /graph`. */
export interface Graph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ---------------------------------------------------------------------------
// Clause contract (GET /clauses/{clause_number}, from engine/api.py)
// ---------------------------------------------------------------------------

/**
 * A single clause fetched verbatim from the engine. `heading` and `parent` are
 * nullable (the engine returns `null` for top-level clauses). `full_text` (the
 * composed parent + children span) is present only for a parent that has
 * `children`; a leaf/sub-item never carries it. The private `_full_text` slice
 * is never exposed by the API and is intentionally absent here.
 */
export interface Clause {
  clause_number: string;
  text: string;
  policy_id: string;
  document_id: string;
  /** Provenance of the clause text: "published" | "draft" | "reference". */
  source: string;
  heading?: string | null;
  parent?: string | null;
  children?: string[];
  superseded_versions?: string[];
  full_text?: string;
}

// ---------------------------------------------------------------------------
// Node-detail contract (GET /nodes/{node_id}, from engine/api.py)
// ---------------------------------------------------------------------------

/** One outgoing edge on a node-detail response (no clause anchors — that is why
 *  the workspace also reads the full `GET /graph`). */
export interface NodeDetailEdge {
  target: string;
  type: string;
  reason: string;
}

/** `GET /nodes/{id}`: a node's derived status plus its **outgoing** edges only. */
export interface NodeDetail {
  id: string;
  title: string;
  status: string;
  edges: NodeDetailEdge[];
}

// ---------------------------------------------------------------------------
// Connection-finder contract (POST /connections/find, from engine/connections.py)
// ---------------------------------------------------------------------------

/** A clause citation whose `text` is fetched verbatim from the index by number. */
export interface ClauseCitation {
  clause_number: string;
  text: string;
}

/** A supported, clause-anchored connection (every cited clause resolved). */
export interface Connection {
  summary: string;
  source_clauses: ClauseCitation[];
  target_clauses: ClauseCitation[];
  scope_note: string | null;
  supported: boolean;
}

/** A candidate that cited a clause absent from the index — reported honestly. */
export interface UnsupportedConnection {
  summary: string;
  message: string;
  supported: boolean;
}

/** `POST /connections/find` result (used by #8, not by #7's read-only workspace). */
export interface ConnectionResult {
  connections: Connection[];
  unsupported: UnsupportedConnection[];
}

// ---------------------------------------------------------------------------
// Client-only workflow state (localStorage — owned by workflowState.ts, Task 3)
// ---------------------------------------------------------------------------

/** Workflow status of a finding as the drafter triages it. */
export type FindingStatus = "open" | "accepted" | "dismissed";

/** Which alignment lane a finding belongs to (set by #8's classifier). */
export type FindingTier =
  "reference-gap" | "supports-draft" | "internal-overlap";

/** Internal sub-type / reference polarity of a finding (set by #8). */
export type FindingType = "conflict" | "duplication" | "gap" | "supports";

/**
 * A draft-alignment finding, stored under `rr:findings:v1:{documentId}`.
 * #7 defines and reads these; #8/#9 write them.
 */
export interface Finding {
  /** Stable finding id, e.g. "finding-rmit-17-1-outsourcing". */
  id: string;
  /** The document this finding is about (also the localStorage key suffix). */
  documentId: string;
  tier: FindingTier;
  type: FindingType;
  status: FindingStatus;
  /** Required when `status === "dismissed"`. */
  reason?: string;
  /** True once an accepted fix has become a tracked change in the draft. */
  inDraft: boolean;
}

/**
 * A tracked-change marker, stored under `rr:tracked-changes:v1:{documentId}`.
 * Written by the copilot (#9) and rendered in `DraftDocViewer`.
 */
export interface TrackedChange {
  /** Marker id. */
  id: string;
  /** The `Finding.id` this change resolves. */
  findingId: string;
  /** Anchor clause, e.g. "RMiT 17.1". */
  clauseNumber: string;
  /** The redraft inserted by the copilot. */
  insertedText: string;
  /** ISO-8601 timestamp when the change was accepted. */
  acceptedAt: string;
}
