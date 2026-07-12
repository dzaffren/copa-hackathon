// Workspace overlay — the client-side synthetic nodes/edges `graphModel` merges
// onto the engine graph (spec-drafter-workspace.md · Functional Requirements:
// "Cross-cluster + preview signals are client-side synthetic nodes" and
// "Reference nodes render when present, tolerate absence").
//
// Two things live here, neither guaranteed to be in `GET /graph`:
//   1. The AML / CFT cross-cluster preview node + its dashed preview edge — the
//      one node from another cluster, genuinely NOT in the technology-risk
//      corpus, shown only as a labelled "future phase" preview.
//   2. The external-reference band — a peer regulator, a national act, an
//      international standard (public), the restricted Regulatory Handbook, and
//      a preview trend/news signal — with a `references` edge to the draft and a
//      short "why this reference matters". Ids/titles mirror `engine/config.py`
//      REFERENCE_DOCUMENTS so that, once the engine reference extension seeds
//      these into the live graph, `graphModel`'s id-dedupe drops the overlay
//      copies and renders the real engine nodes instead ("reference band
//      tolerance"). The verbatim passages behind these references are #26's job,
//      NOT shown here — only that they exist, connect, and why they matter.
//
// The draft that every overlay edge originates from.
import type { GraphEdge, GraphNode } from "../types";

/** The single editable draft every reference/cross-cluster edge hangs off. */
const DRAFT_ID = "rmit-v2-2026-draft";

/** The shape `graphModel.toReactFlowModel` merges after the engine nodes. */
export interface WorkspaceOverlay {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

/**
 * Synthetic nodes merged after the engine nodes. `graphModel` adds any overlay
 * node whose id is not already present in `GET /graph`, so:
 *   • the AML node (never an engine node) is always shown; and
 *   • the reference band is shown only while the engine has not yet seeded these
 *     `kind:"reference"` nodes — once it does, the real ones win.
 */
const OVERLAY_NODES: GraphNode[] = [
  // Cross-cluster preview — NOT in the technology-risk corpus. Policy-kind node
  // whose `cluster` alone drives the "other cluster (preview only)" marking.
  {
    id: "aml-cft",
    policy_id: "aml-cft",
    title: "AML / CFT",
    version: "in force · other cluster",
    status: "In force",
    cluster: "aml-cft",
  },
  // External-reference band — public peer regulator, act, standard ------------
  {
    id: "mas-trm-2021",
    policy_id: "mas-trm",
    title: "Technology Risk Management Guidelines (MAS, Singapore)",
    version: "2021",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "peer_regulator",
    access: "public",
    preview: false,
    source_url:
      "https://www.mas.gov.sg/regulation/guidelines/" +
      "technology-risk-management-guidelines",
  },
  {
    id: "pdpa-2010",
    policy_id: "pdpa",
    title: "Personal Data Protection Act 2010 (Malaysia)",
    version: "2010 · Act 709 (as amended by Act A1727)",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "act",
    access: "public",
    preview: false,
    source_url: "https://www.pdp.gov.my/ppdpv1/en/akta/pdp-act-2010-en/",
  },
  {
    id: "basel-por-2021",
    policy_id: "basel-por",
    title: "Principles for Operational Resilience (Basel Committee)",
    version: "2021",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "standard",
    access: "public",
    preview: false,
    source_url: "https://www.bis.org/bcbs/publ/d516.htm",
  },
  // Restricted reference — content withheld, never fetched -------------------
  {
    id: "bnm-handbook",
    policy_id: "bnm-handbook",
    title: "Regulatory Handbook (BNM)",
    version: "internal",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "handbook",
    access: "restricted",
    preview: false,
  },
  // Preview signal — labelled "not yet built" trend/news band ----------------
  {
    id: "trend-cloud-signals",
    policy_id: "trend-cloud-signals",
    title: "Trends · News · foreign policies",
    version: "preview",
    status: "In force",
    cluster: "technology-risk",
    kind: "reference",
    source_type: "trend",
    access: "public",
    preview: true,
  },
];

/**
 * Synthetic edges from the draft. `graphModel` adds an overlay edge only when
 * both endpoints exist in the merged node set and the `source__target` pair is
 * not already an engine edge — so the reference edges disappear the moment the
 * engine provides its own. Each `reason` is a short "why this reference matters"
 * (or, for AML, why it surfaced as a preview) — the deep, clause-by-clause
 * detail is #26's Reference Radar, not this workspace.
 */
const OVERLAY_EDGES: GraphEdge[] = [
  {
    source: DRAFT_ID,
    target: "aml-cft",
    type: "cross-cluster",
    reason:
      "A change in RMiT 17.1 also touches AML / CFT customer due-diligence in " +
      "another cluster, so it surfaces here as a preview. Full cross-cluster " +
      "mapping is a future phase.",
    source_clauses: ["RMiT 17.1"],
    target_clauses: [],
    provenance: "synthetic",
  },
  {
    source: DRAFT_ID,
    target: "mas-trm-2021",
    type: "references",
    reason:
      "How a peer regulator (MAS) governs public-cloud adoption through " +
      "third-party risk management rather than pre-approval — the benchmark " +
      "for 17.1's shift from consultation to notification.",
    source_clauses: ["RMiT 17.1"],
    target_clauses: ["MAS TRM Cloud"],
    provenance: "llm-found",
    confidence: 0.88,
  },
  {
    source: DRAFT_ID,
    target: "pdpa-2010",
    type: "references",
    reason:
      "A cloud region outside Malaysia engages the PDPA's limits on " +
      "transferring personal data abroad, so the 17.1 notification should " +
      "still capture data residency once consulting the Bank is removed.",
    source_clauses: ["RMiT 17.1"],
    target_clauses: ["PDPA 129"],
    provenance: "llm-found",
    confidence: 0.9,
  },
  {
    source: DRAFT_ID,
    target: "basel-por-2021",
    type: "references",
    reason:
      "The international baseline keeps responsibility for third-party (incl. " +
      "cloud) dependencies with the bank whatever the approval model — 17.1 " +
      "must preserve that.",
    source_clauses: ["RMiT 17.1"],
    target_clauses: ["Basel POR TP-1"],
    provenance: "llm-found",
    confidence: 0.84,
  },
  {
    source: DRAFT_ID,
    target: "bnm-handbook",
    type: "references",
    reason:
      "The internal Regulatory Handbook connects to this clause; its content " +
      "is confidential and deferred from MVP1.",
    source_clauses: ["RMiT 17.1"],
    target_clauses: ["BNM Handbook — Cloud & Outsourcing Manual"],
    provenance: "curated",
    confidence: 1.0,
  },
  {
    source: DRAFT_ID,
    target: "trend-cloud-signals",
    type: "references",
    reason:
      "Signals such as in-country cloud regions and EU DORA — a what's-next " +
      "preview, not a committed reference.",
    source_clauses: ["RMiT 17.1"],
    target_clauses: ["Trend — in-country cloud regions"],
    provenance: "curated",
    confidence: 1.0,
  },
];

/** The overlay `graphModel` merges by default. */
export const workspaceOverlay: WorkspaceOverlay = {
  nodes: OVERLAY_NODES,
  edges: OVERLAY_EDGES,
};
