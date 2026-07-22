import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import { Maximize, ZoomIn, ZoomOut } from "lucide-react";

import type { GraphEdge, GraphNode } from "@/lib/types";
import { CROSS_EDGE_DASH, CROSS_EDGE_STROKE, edgeStyle, nodeStyle, shortLabel } from "./legend";

// --- Graph data mapped for react-force-graph-2d ----------------------------
// The library mutates link.source / link.target from ids into node objects and
// adds x/y to nodes during the simulation. We keep our own domain fields on
// each object so the canvas renderer and click handlers stay typed.

interface FGNode extends GraphNode {
  isTask: boolean;
  x?: number;
  y?: number;
}
interface FGLink extends Omit<GraphEdge, "source" | "target"> {
  source: string | FGNode;
  target: string | FGNode;
}

const TASK_R = 13;
const ANCHOR_R = 8;

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  primaryTaskId: string | null;
  selectedNodeId?: string | null;
  selectedEdgeId?: string | null;
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
  /** d3-force tuning — defaults suit a single workstream; the institution map
   *  (denser, multi-workstream) passes its own looser/tighter values. */
  chargeStrength?: number;
  linkDistance?: number;
}

/**
 * The hero canvas: one force-directed graph of a workstream rendered with
 * react-force-graph-2d. Nodes are colour-coded circles keyed by node type — the
 * task node larger with a pulsing glow; edges are keyed by structural type,
 * dashed when not yet analysed, with the edge type labelled at the midpoint and
 * a findings-count badge when analysed. Zoom in / out / reset are provided;
 * pan and drag come from the library.
 */
export function GraphCanvas({
  nodes,
  edges,
  primaryTaskId,
  selectedNodeId,
  selectedEdgeId,
  onSelectNode,
  onSelectEdge,
  chargeStrength = -300,
  linkDistance = 150,
}: GraphCanvasProps) {
  const fgRef = useRef<ForceGraphMethods<FGNode, FGLink> | undefined>(undefined);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 600 });

  const taskId = useMemo(() => {
    if (primaryTaskId && nodes.some((n) => n.id === primaryTaskId)) {
      return primaryTaskId;
    }
    return nodes.find((n) => n.node_type === "task")?.id ?? null;
  }, [nodes, primaryTaskId]);

  const data = useMemo(
    () => ({
      nodes: nodes.map<FGNode>((n) => ({ ...n, isTask: n.id === taskId })),
      links: edges.map<FGLink>((e) => ({ ...e })),
    }),
    [nodes, edges, taskId],
  );

  // Measure the container so the canvas fills it and re-fits on resize.
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const measure = () =>
      setSize({ width: el.clientWidth, height: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // d3 force config from the design brief: charge -300, link distance 150.
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force("charge")?.strength(chargeStrength);
    const link = fg.d3Force("link");
    if (link && "distance" in link) {
      (link as unknown as { distance: (d: number) => unknown }).distance(
        linkDistance,
      );
    }
  }, [data, chargeStrength, linkDistance]);

  const drawNode = useCallback(
    (node: FGNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const style = nodeStyle(node.node_type);
      const r = node.isTask ? TASK_R : ANCHOR_R;
      const x = node.x ?? 0;
      const y = node.y ?? 0;
      const selected = node.id === selectedNodeId;

      // Pulsing glow — strong on the hero task node, a gentle halo elsewhere.
      const t = performance.now() / 1000;
      const pulse = 0.5 + 0.5 * Math.sin(t * 2);
      const glow = node.isTask ? 8 + pulse * 10 : selected ? 8 : 3;
      ctx.save();
      ctx.shadowColor = style.stroke;
      ctx.shadowBlur = glow;

      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = style.fill;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.lineWidth = selected ? 3 : node.isTask ? 2.5 : 1.5;
      ctx.strokeStyle = selected ? "#e2e8f0" : style.stroke;
      ctx.stroke();
      ctx.restore();

      // Label below the node, scaled to stay legible while zooming.
      const fontSize = Math.max(9 / globalScale, node.isTask ? 4 : 3);
      ctx.font = `${node.isTask ? 700 : 500} ${fontSize}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = "#cbd5e1";
      ctx.fillText(shortLabel(node.title), x, y + r + 2);
    },
    [selectedNodeId],
  );

  const drawLink = useCallback(
    (link: FGLink, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const s = link.source as FGNode;
      const tg = link.target as FGNode;
      if (!s || !tg || s.x == null || tg.x == null) return;
      const cross = link.cross === true;
      const style = edgeStyle(link.edge_type);
      const selected = link.id === selectedEdgeId;
      const stroke = cross ? CROSS_EDGE_STROKE : style.stroke;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(s.x, s.y!);
      ctx.lineTo(tg.x, tg.y!);
      ctx.strokeStyle = stroke;
      ctx.lineWidth = (selected ? 2.5 : 1.4) / globalScale;
      // Not-analysed edges (and cross-links) read as dashed; analysed = solid.
      const dashed = cross ? CROSS_EDGE_DASH : link.analysed ? [] : style.dash;
      ctx.setLineDash(dashed.map((d) => d / globalScale));
      ctx.globalAlpha = selected ? 1 : 0.75;
      ctx.stroke();
      ctx.restore();

      // Midpoint: edge-type label, plus a findings-count badge when analysed.
      const mx = (s.x + tg.x!) / 2;
      const my = (s.y! + tg.y!) / 2;
      const fontSize = Math.max(7.5 / globalScale, 2.6);
      ctx.font = `500 ${fontSize}px Inter, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      if (link.analysed && link.findings_count > 0) {
        const badge = `${link.findings_count}`;
        ctx.fillStyle = "#34d399";
        ctx.beginPath();
        ctx.arc(mx, my, fontSize * 0.95, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = "#052e2b";
        ctx.fillText(badge, mx, my);
      } else if (globalScale > 1.2) {
        ctx.fillStyle = "#64748b";
        ctx.fillText(style.label, mx, my - fontSize);
      }
    },
    [selectedEdgeId],
  );

  const zoomIn = () => fgRef.current?.zoom((fgRef.current?.zoom() ?? 1) * 1.3, 200);
  const zoomOut = () =>
    fgRef.current?.zoom((fgRef.current?.zoom() ?? 1) * 0.75, 200);
  const resetZoom = () => fgRef.current?.zoomToFit(400, 60);

  return (
    <div
      ref={wrapRef}
      data-testid="graph-canvas"
      className="relative h-full w-full overflow-hidden bg-[#0b1220]"
    >
      <div className="absolute right-3 top-3 z-10 flex flex-col overflow-hidden rounded-lg border border-border/60 bg-card/80 shadow-sm backdrop-blur">
        <button
          type="button"
          aria-label="Zoom in"
          onClick={zoomIn}
          className="p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          type="button"
          aria-label="Zoom out"
          onClick={zoomOut}
          className="border-t border-border/60 p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          type="button"
          aria-label="Reset zoom"
          onClick={resetZoom}
          className="border-t border-border/60 p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
        >
          <Maximize className="h-4 w-4" />
        </button>
      </div>

      <ForceGraph2D
        ref={fgRef}
        width={size.width}
        height={size.height}
        graphData={data}
        backgroundColor="rgba(0,0,0,0)"
        cooldownTicks={120}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 60)}
        nodeRelSize={ANCHOR_R}
        nodeLabel={(n) => (n as FGNode).title}
        nodeCanvasObject={drawNode}
        nodePointerAreaPaint={(node, color, ctx) => {
          const n = node as FGNode;
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(n.x ?? 0, n.y ?? 0, (n.isTask ? TASK_R : ANCHOR_R) + 2, 0, 2 * Math.PI);
          ctx.fill();
        }}
        onNodeClick={(n) => onSelectNode((n as FGNode).id)}
        linkCanvasObjectMode={() => "replace"}
        linkCanvasObject={drawLink}
        linkPointerAreaPaint={(link, color, ctx) => {
          const l = link as FGLink;
          const s = l.source as FGNode;
          const tg = l.target as FGNode;
          if (!s || !tg || s.x == null || tg.x == null) return;
          ctx.strokeStyle = color;
          ctx.lineWidth = 8;
          ctx.beginPath();
          ctx.moveTo(s.x, s.y!);
          ctx.lineTo(tg.x, tg.y!);
          ctx.stroke();
        }}
        onLinkClick={(l) => onSelectEdge((l as FGLink).id)}
      />
    </div>
  );
}

export default GraphCanvas;
