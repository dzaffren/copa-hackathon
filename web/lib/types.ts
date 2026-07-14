// Shared types mirroring the Two-Branch Source Connection Engine read API
// (see docs/specs/reconciliation-workbench/spec-source-connection-engine.md → "API Design").
// The frontend never invents these shapes; it renders exactly what the engine emits.

export type Verdict =
  "Consensus" | "Conflict" | "Gap" | "Duplicate" | "Partial";

export type Verification = "verified" | "illustrative" | "pending_extraction";

export type Branch = "cited" | "uncited" | "feedback";

export type SourceType =
  | "international_standard"
  | "peer_regulator"
  | "act"
  | "internal_bnm"
  | "industry_feedback";

export type ParagraphState = "analysed" | "not_analysed";

/** One paragraph row on the workspace canvas (`GET …/paragraphs`). */
export interface ParagraphSummary {
  number: string;
  title: string;
  text?: string;
  state: ParagraphState;
  connection_count: number;
}

export interface ParagraphsResponse {
  document_id: string;
  total_paragraphs: number;
  paragraphs: ParagraphSummary[];
}

export interface SourceRef {
  document_id: string;
  title: string;
  source_type: SourceType;
  /** industry_feedback only */
  stance?: "agree" | "partial" | "disagree";
}

export interface Quote {
  clause_number: string;
  /** null when verification === "pending_extraction". */
  text: string | null;
  verification: Verification;
}

/** A fully-analysed connection with a proposed verdict + verbatim quote. */
export interface AnalysedConnection {
  id: string;
  branch: Branch;
  source: SourceRef;
  verdict: Verdict;
  verdict_status: "proposed";
  confidence: "High" | "Medium" | "Low";
  rationale: string;
  quote: Quote;
  status?: undefined;
}

/** A source the engine identified but could not retrieve — no verdict, no quote. */
export interface BlockedConnection {
  id: string;
  branch: Branch;
  source: SourceRef;
  status: "could_not_retrieve";
  reason: string;
  verdict: null;
  quote: null;
}

export type Connection = AnalysedConnection | BlockedConnection;

export interface ConnectionsResponse {
  paragraph: { number: string; title: string; text?: string };
  state: ParagraphState;
  no_matching_source: boolean;
  connections: Connection[];
}

export function isBlocked(c: Connection): c is BlockedConnection {
  return (c as BlockedConnection).status === "could_not_retrieve";
}
