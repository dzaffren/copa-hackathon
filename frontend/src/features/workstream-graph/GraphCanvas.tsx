import { useMemo, useState } from "react";
import { Maximize, ZoomIn, ZoomOut } from "lucide-react";

import type { GraphEdge, GraphNode } from "@/lib/types";
import { edgeStyle, nodeStyle } from "./legend";

const VIEW_W = 800;
const VIEW_H = 620;
const CENTER = { x: VIEW_W / 2, y: VIEW_H / 2 };
const RADIUS = 220;
const TASK_R = 44;
const ANCHOR_R = 32;

const MIN_SCALE = 0.5;
const MAX_SCALE = 2.5;

interface Placed {
  x: number;
  y: number;
  r: number;
  isTask: boolean;
}

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  primaryTaskId: string | null;
  selectedNodeId?: string | null;
  selectedEdgeId?: string | null;
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
}

/** Radial layout: the primary task node at the centre, anchors evenly around. */
function layout(
  nodes: GraphNode[],
  primaryTaskId: string | null,
): Record<string, Placed> {
  const positions: Record<string, Placed> = {};
  const task =
    nodes.find((n) => n.id === primaryTaskId) ??
    nodes.find((n) => n.node_type === "task");
  if (task) {
    positions[task.id] = { x: CENTER.x, y: CENTER.y, r: TASK_R, isTask: true };
  }
  const others = nodes.filter((n) => n.id !== task?.id);
  const count = Math.max(others.length, 1);
  others.forEach((n, i) => {
    const angle = ((-90 + (360 / count) * i) * Math.PI) / 180;
    positions[n.id] = {
      x: CENTER.x + RADIUS * Math.cos(angle),
      y: CENTER.y + RADIUS * Math.sin(angle),
      r: ANCHOR_R,
      isTask: false,
    };
  });
  return positions;
}

function nodeLabel(n: GraphNode): string {
  return n.issuer ?? n.title.split(/[\s—-]/)[0];
}

/**
 * SVG canvas of one workstream: nodes as colour-coded circles keyed by node
 * type, edges as lines keyed by structural edge type (line style only — no
 * textual labels). Zoom is clamped to [0.5, 2.5]; pan/drag is not supported.
 */
export function GraphCanvas({
  nodes,
  edges,
  primaryTaskId,
  selectedNodeId,
  selectedEdgeId,
  onSelectNode,
  onSelectEdge,
}: GraphCanvasProps) {
  const [scale, setScale] = useState(1);
  const positions = useMemo(
    () => layout(nodes, primaryTaskId),
    [nodes, primaryTaskId],
  );

  const zoomIn = () => setScale((s) => Math.min(MAX_SCALE, s * 1.25));
  const zoomOut = () => setScale((s) => Math.max(MIN_SCALE, s * 0.8));
  const resetZoom = () => setScale(1);

  return (
    <div className="relative h-full w-full overflow-hidden bg-slate-50">
      <div className="absolute right-3 top-3 z-10 flex flex-col overflow-hidden rounded-md border bg-white shadow-sm">
        <button
          type="button"
          aria-label="Zoom in"
          onClick={zoomIn}
          className="p-2 text-gray-600 hover:bg-gray-50"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          type="button"
          aria-label="Zoom out"
          onClick={zoomOut}
          className="border-t p-2 text-gray-600 hover:bg-gray-50"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          type="button"
          aria-label="Reset zoom"
          onClick={resetZoom}
          className="border-t p-2 text-gray-600 hover:bg-gray-50"
        >
          <Maximize className="h-4 w-4" />
        </button>
      </div>

      <svg
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        className="h-full w-full"
        role="img"
        aria-label="Workstream graph canvas"
      >
        <g
          data-testid="zoom-group"
          data-scale={scale}
          style={{
            transform: `scale(${scale})`,
            transformOrigin: "center center",
          }}
        >
          {edges.map((e) => {
            const a = positions[e.source];
            const b = positions[e.target];
            if (!a || !b) return null;
            const style = edgeStyle(e.edge_type);
            const selected = e.id === selectedEdgeId;
            return (
              <g
                key={e.id}
                role="button"
                aria-label={`edge ${e.edge_type} ${e.source} to ${e.target}`}
                onClick={() => onSelectEdge(e.id)}
                className="cursor-pointer"
              >
                {/* Fat transparent hit target so thin/dashed lines are clickable. */}
                <line
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke="transparent"
                  strokeWidth={16}
                />
                <line
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke={style.stroke}
                  strokeWidth={selected ? 3.5 : 2}
                  strokeDasharray={style.dash || undefined}
                />
              </g>
            );
          })}

          {nodes.map((n) => {
            const p = positions[n.id];
            if (!p) return null;
            const style = nodeStyle(n.node_type);
            const selected = n.id === selectedNodeId;
            return (
              <g
                key={n.id}
                role="button"
                aria-label={n.title}
                onClick={() => onSelectNode(n.id)}
                className="cursor-pointer"
              >
                <title>{n.title}</title>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={p.r}
                  fill={style.fill}
                  stroke={selected ? "#111827" : style.stroke}
                  strokeWidth={selected ? 4 : 2.5}
                />
                <text
                  x={p.x}
                  y={p.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontSize={p.isTask ? 12 : 10}
                  fontWeight={700}
                  fill={style.text}
                  className="pointer-events-none select-none"
                >
                  {nodeLabel(n)}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}

export default GraphCanvas;
