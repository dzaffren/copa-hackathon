// Custom React Flow edge renderers for the cluster map (spec-drafter-workspace.md
// · UI/Frontend Requirements "Internal-overlap links and external-reference links
// are visually distinguishable"). One renderer styles every edge by its mapped
// `edgeKind` (graphModel.ts): internal overlap, version lineage, external
// reference, and the dashed cross-cluster preview each get a distinct stroke.
//
// Contract (Verification → Locator strategies): every edge carries
//   data-testid="edge-{source}__{target}".
// The clause-cited "why these are connected" explanation is NOT rendered on the
// map — that belongs to the detail panel (Task 7). Here edges are selectable,
// styled lines only.

import { getBezierPath, type EdgeProps, type EdgeTypes } from "reactflow";
import type { CSSProperties } from "react";

import type { RFEdgeData, RFEdgeKind } from "../../lib/graphModel";

/** Distinct stroke per edge kind. Internal overlap vs external reference are the
 *  two the spec calls out as "visually distinguishable"; lineage and the
 *  cross-cluster preview are further differentiated. */
const EDGE_STYLES: Record<RFEdgeKind, CSSProperties> = {
  // Internal overlap between two policies — solid slate.
  overlap: { stroke: "#475569", strokeWidth: 2 },
  // External reference link — solid sky, clearly a different colour.
  reference: { stroke: "#0284c7", strokeWidth: 2 },
  // Structural version lineage (v1 → v2) — thin dashed grey.
  lineage: { stroke: "#94a3b8", strokeWidth: 1.5, strokeDasharray: "6 4" },
  // Cross-cluster preview — dashed amber, matching the AML "preview" treatment.
  "cross-cluster": {
    stroke: "#d97706",
    strokeWidth: 2,
    strokeDasharray: "5 4",
  },
};

/** Hit-path half-width for the transparent interaction stroke. Kept narrow (10px
 *  total) so a neighbouring curved edge's hit area no longer sweeps across this
 *  edge's clickable target — the dedicated midpoint chip below is the reliable
 *  click target, so this only needs to make the visible line hover-friendly. */
const INTERACTION_WIDTH = 10;

/**
 * The single kind-driven edge renderer. Draws a bezier path styled by
 * `data.edgeKind`, a narrow transparent "interaction" path so the thin line is
 * hover-friendly, and a compact "why" chip at the edge midpoint. The chip carries
 * the `edge-{source}__{target}` test id: it is a solid, centred hit target so a
 * normal click always lands on a dedicated point instead of a thin, overlappable
 * line. Clicking it bubbles to React Flow's `onEdgeClick`, so selection is
 * unchanged. The chip shows no clause text — the "why these are connected"
 * explanation still belongs to the detail panel (Task 7), not the map.
 */
export function ClusterEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
}: EdgeProps<RFEdgeData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const kind: RFEdgeKind = data?.edgeKind ?? "overlap";
  const testId = data?.testId ?? `edge-${id}`;
  const stroke = (EDGE_STYLES[kind].stroke as string) ?? "#475569";

  return (
    <g data-edge-kind={kind}>
      <path
        className="react-flow__edge-path"
        d={edgePath}
        style={EDGE_STYLES[kind]}
        fill="none"
        markerEnd={markerEnd}
      />
      {/* Narrow transparent hit area so the thin visible line is hover-friendly. */}
      <path
        className="react-flow__edge-interaction"
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={INTERACTION_WIDTH}
      />
      {/* Compact midpoint chip — the dedicated, testid-bearing click target. */}
      <g
        data-testid={testId}
        transform={`translate(${labelX}, ${labelY})`}
        style={{ cursor: "pointer" }}
      >
        {/* Comfortable, invisible hit disc for humans + Playwright. */}
        <circle r={11} fill="transparent" />
        {/* Small visible affordance in the edge's own colour. */}
        <circle r={6} fill="#ffffff" stroke={stroke} strokeWidth={1.5} />
        <circle r={2.5} fill={stroke} />
      </g>
    </g>
  );
}

/**
 * React Flow edge-type registry. `graphModel` sets each edge's `type` to its
 * `edgeKind` string, so all four keys resolve to the kind-driven `ClusterEdge`.
 */
export const edgeTypes: EdgeTypes = {
  overlap: ClusterEdge,
  reference: ClusterEdge,
  lineage: ClusterEdge,
  "cross-cluster": ClusterEdge,
};
