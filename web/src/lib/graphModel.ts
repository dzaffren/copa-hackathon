// Graph model mapper — engine `Graph` → React Flow `{ nodes, edges }`
// (spec-drafter-workspace.md · System Design: "Graph model mapper"). This is the
// single place the cluster map is built from `GET /graph`, with the client-side
// overlay (AML preview + external-reference band) merged in deterministically.
//
// Responsibilities:
//   • attach each node's derived `marking` (via treatments.ts) + a treatment
//     kind the custom node renderer switches on;
//   • give every node a deterministic curated position — the draft at centre,
//     published policies around it, references orbiting in a band above, AML off
//     to the side — so the layout never jitters between loads;
//   • expose `data-testid`-friendly ids (`node-{id}`, `edge-{source}__{target}`)
//     matching the E2E locator strategy;
//   • label edges from their `reason` and tag internal-overlap vs reference vs
//     lineage vs cross-cluster for distinct styling;
//   • MERGE the overlay so #7 renders standalone even when the live graph has no
//     reference nodes yet ("reference band tolerance"): an overlay node is added
//     only when its id is absent from `GET /graph`, an overlay edge only when
//     both endpoints exist and the pair is not already an engine edge.

import type { Edge, Node, XYPosition } from "reactflow";

import type { Graph, GraphEdge, GraphNode } from "../types";
import {
  workspaceOverlay,
  type WorkspaceOverlay,
} from "../fixtures/workspaceOverlay";
import { classifyNode, deriveMarking, type TreatmentKind } from "./treatments";

/** Which custom React Flow node renderer a node uses (Task 6 `nodeTypes.tsx`). */
export type RFNodeType = "policy" | "reference" | "preview";

/** Which custom React Flow edge renderer / style an edge uses. */
export type RFEdgeKind = "overlap" | "reference" | "lineage" | "cross-cluster";

/** Data carried on every mapped node — consumed by the custom node renderer. */
export interface RFNodeData {
  /** The raw engine node, so the detail panel can read every field. */
  node: GraphNode;
  /** Derived marking string (treatments.ts) — also emitted as `data-marking`. */
  marking: string;
  /** Treatment kind the renderer switches ring / band / lock styling on. */
  treatment: TreatmentKind;
  /** Display title. */
  title: string;
  /** Display version / kind line. */
  version: string;
  /** `node-{id}` — the E2E locator. */
  testId: string;
}

/** Data carried on every mapped edge — consumed by the edge renderer + panel. */
export interface RFEdgeData {
  /** Verbatim engine `reason` (also used as the edge label). */
  reason: string;
  /** Internal-overlap vs reference vs lineage vs cross-cluster. */
  edgeKind: RFEdgeKind;
  /** Clause anchors on the draft side (may be empty for structural edges). */
  sourceClauses: string[];
  /** Clause anchors on the other side (may be empty / a provenance label). */
  targetClauses: string[];
  provenance?: string;
  confidence?: number;
  /** True for the dashed AML cross-cluster preview edge. */
  preview: boolean;
  /** `edge-{source}__{target}` — the E2E locator. */
  testId: string;
}

export type RFNode = Node<RFNodeData>;
export type RFEdge = Edge<RFEdgeData>;

/** The mapped React Flow model. */
export interface ReactFlowModel {
  nodes: RFNode[];
  edges: RFEdge[];
}

/** treatment kind → custom node renderer. Cross-cluster + preview signals share
 *  the "preview" renderer but are told apart by `data.treatment`. */
const NODE_TYPE: Record<TreatmentKind, RFNodeType> = {
  "editable-draft": "policy",
  "published-draft": "policy",
  superseded: "policy",
  "in-force": "policy",
  "cross-cluster": "preview",
  reference: "reference",
  "reference-restricted": "reference",
  "reference-preview": "preview",
};

/** Curated, deterministic positions. The draft anchors the centre; published
 *  policies ring it; references orbit in an upper band; AML sits off to the
 *  side. Unknown ids fall back to a deterministic ring (see `fallbackPosition`)
 *  so a corpus change never produces overlapping (0,0) nodes. */
const POSITIONS: Record<string, XYPosition> = {
  // Centre — the single editable draft.
  "rmit-v2-2026-draft": { x: 0, y: 0 },
  // Superseded previous version, just left of centre.
  "rmit-v1-2020": { x: -300, y: -20 },
  // Published policies ring (right + lower arc).
  "outsourcing-v1-2019": { x: 320, y: -170 },
  "opres-v1-2025-draft": { x: 360, y: 70 },
  "bcm-v1-2022": { x: 300, y: 300 },
  "recovery-planning-v1-2021": { x: 30, y: 360 },
  "customer-info-v1-2025": { x: -280, y: 300 },
  // External-reference band (upper arc).
  "mas-trm-2021": { x: -440, y: -300 },
  "pdpa-2010": { x: -160, y: -370 },
  "basel-por-2021": { x: 150, y: -370 },
  "bnm-handbook": { x: 450, y: -320 },
  "trend-cloud-signals": { x: 690, y: -230 },
  // Cross-cluster preview, off to the side.
  "aml-cft": { x: 700, y: 170 },
};

/** Deterministic fallback for any node without a curated position. */
function fallbackPosition(index: number): XYPosition {
  const radius = 560;
  const angle = (index * 2 * Math.PI) / 12 + Math.PI / 6;
  return {
    x: Math.round(Math.cos(angle) * radius),
    y: Math.round(Math.sin(angle) * radius),
  };
}

/** Map one engine node → a React Flow node with derived marking + position. */
function toRFNode(node: GraphNode, fallbackIndex: number): RFNode {
  const treatment = classifyNode(node);
  return {
    id: node.id,
    type: NODE_TYPE[treatment],
    position: POSITIONS[node.id] ?? fallbackPosition(fallbackIndex),
    data: {
      node,
      marking: deriveMarking(node),
      treatment,
      title: node.title,
      version: node.version,
      testId: `node-${node.id}`,
    },
  };
}

/** engine/overlay edge `type` string → the styling kind + preview flag. */
function toEdgeKind(type: string): RFEdgeKind {
  switch (type) {
    case "references":
      return "reference";
    case "version-lineage":
      return "lineage";
    case "cross-cluster":
      return "cross-cluster";
    case "overlaps":
    default:
      return "overlap";
  }
}

/** Map one engine/overlay edge → a React Flow edge with a `reason` label. */
function toRFEdge(edge: GraphEdge): RFEdge {
  const edgeKind = toEdgeKind(edge.type);
  const id = `${edge.source}__${edge.target}`;
  return {
    id,
    source: edge.source,
    target: edge.target,
    type: edgeKind,
    label: edge.reason,
    animated: edgeKind === "cross-cluster",
    data: {
      reason: edge.reason,
      edgeKind,
      sourceClauses: edge.source_clauses ?? [],
      targetClauses: edge.target_clauses ?? [],
      provenance: edge.provenance,
      confidence: edge.confidence,
      preview: edgeKind === "cross-cluster",
      testId: `edge-${id}`,
    },
  };
}

/**
 * Build the React Flow model from the engine graph + overlay.
 *
 * Merge is deterministic and tolerant:
 *   • overlay nodes are appended only when their id is absent from `graph`
 *     (so real engine reference nodes always win over the fixture copies, and
 *     the AML node — never an engine node — is always shown);
 *   • overlay edges are appended only when both endpoints exist in the merged
 *     node set and the `source__target` pair is not already an engine edge.
 */
export function toReactFlowModel(
  graph: Graph,
  overlay: WorkspaceOverlay = workspaceOverlay,
): ReactFlowModel {
  const engineIds = new Set(graph.nodes.map((n) => n.id));
  const addedOverlayNodes = overlay.nodes.filter((n) => !engineIds.has(n.id));
  const mergedNodes = [...graph.nodes, ...addedOverlayNodes];
  const mergedIds = new Set(mergedNodes.map((n) => n.id));

  const engineEdgeKeys = new Set(
    graph.edges.map((e) => `${e.source}__${e.target}`),
  );
  const addedOverlayEdges = overlay.edges.filter(
    (e) =>
      mergedIds.has(e.source) &&
      mergedIds.has(e.target) &&
      !engineEdgeKeys.has(`${e.source}__${e.target}`),
  );
  const mergedEdges = [...graph.edges, ...addedOverlayEdges];

  let fallbackIndex = 0;
  const nodes = mergedNodes.map((node) => {
    const positioned = POSITIONS[node.id] !== undefined;
    return toRFNode(node, positioned ? -1 : fallbackIndex++);
  });

  return {
    nodes,
    edges: sortByPaintOrder(mergedEdges.map(toRFEdge)),
  };
}

/** Later-painted edges sit on top in the shared edge SVG. Internal-overlap policy
 *  edges are painted ABOVE the external-reference band so their midpoint click
 *  target is never covered by a reference edge's transparent hit path (E2E: the
 *  core RMiT ↔ Outsourcing connection must be directly clickable). Ties keep the
 *  original order, so this is a stable, deterministic reorder. */
const PAINT_ORDER: Record<RFEdgeKind, number> = {
  reference: 0,
  "cross-cluster": 0,
  lineage: 1,
  overlap: 2,
};

function sortByPaintOrder(edges: RFEdge[]): RFEdge[] {
  return edges
    .map((edge, index) => ({ edge, index }))
    .sort(
      (a, b) =>
        PAINT_ORDER[a.edge.data?.edgeKind ?? "overlap"] -
          PAINT_ORDER[b.edge.data?.edgeKind ?? "overlap"] || a.index - b.index,
    )
    .map(({ edge }) => edge);
}
