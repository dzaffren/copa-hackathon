import type { EdgeType, NodeType } from "@/lib/types";

// Colour + label maps for the graph canvas and detail panels. Tuned for the
// dark navy/slate theme (see index.css + CLAUDE.md): saturated node fills that
// glow against the deep background, with translucent Tailwind badge classes for
// the panels. One source of truth for every node/edge colour in the app.

export interface NodeStyle {
  label: string;
  /** Canvas circle fill — a saturated colour that reads on dark navy. */
  fill: string;
  /** Canvas circle stroke / halo colour. */
  stroke: string;
  /** Canvas label text colour. */
  text: string;
  /** Tailwind classes for a node-type chip/badge in the panels. */
  badge: string;
}

export const NODE_LEGEND: Record<NodeType, NodeStyle> = {
  task: {
    label: "task",
    fill: "#22d3ee", // bright cyan — the hero node
    stroke: "#67e8f9",
    text: "#e0faff",
    badge: "bg-cyan-500/15 text-cyan-300 border-cyan-400/30",
  },
  "internal-published": {
    label: "internal-published",
    fill: "#34d399", // emerald
    stroke: "#6ee7b7",
    text: "#062a1e",
    badge: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  },
  "international-standard": {
    label: "international-standard",
    fill: "#fbbf24", // gold
    stroke: "#fcd34d",
    text: "#3a2606",
    badge: "bg-amber-400/15 text-amber-300 border-amber-300/30",
  },
  "peer-regulator": {
    label: "peer-regulator",
    fill: "#fb7185", // coral
    stroke: "#fda4af",
    text: "#3a0b13",
    badge: "bg-rose-500/15 text-rose-300 border-rose-400/30",
  },
  "act-law": {
    label: "act-law",
    fill: "#ef4444", // red
    stroke: "#f87171",
    text: "#fee2e2",
    badge: "bg-red-500/15 text-red-300 border-red-400/30",
  },
  "industry-input": {
    label: "industry-input",
    fill: "#2dd4bf", // teal
    stroke: "#5eead4",
    text: "#052e2b",
    badge: "bg-teal-500/15 text-teal-300 border-teal-400/30",
  },
  "supervisory-letter": {
    label: "supervisory-letter",
    fill: "#a78bfa", // violet
    stroke: "#c4b5fd",
    text: "#1e1b3a",
    badge: "bg-violet-500/15 text-violet-300 border-violet-400/30",
  },
  others: {
    label: "others",
    fill: "#94a3b8", // slate/gray
    stroke: "#cbd5e1",
    text: "#0b1220",
    badge: "bg-slate-400/15 text-slate-300 border-slate-400/30",
  },
};

export interface EdgeStyle {
  label: string;
  stroke: string;
  /** Canvas line dash pattern (px on/off); empty for a solid line. */
  dash: number[];
}

export const EDGE_LEGEND: Record<EdgeType, EdgeStyle> = {
  supersedes: { label: "supersedes", stroke: "#f87171", dash: [] },
  references: { label: "references", stroke: "#38bdf8", dash: [] },
  "contributes-to": { label: "contributes-to", stroke: "#818cf8", dash: [5, 4] },
  "parallel-to": { label: "parallel-to", stroke: "#94a3b8", dash: [7, 4] },
};

const FALLBACK_NODE: NodeStyle = NODE_LEGEND.others;

export function nodeStyle(type: NodeType): NodeStyle {
  return NODE_LEGEND[type] ?? FALLBACK_NODE;
}

export function edgeStyle(type: EdgeType): EdgeStyle {
  return EDGE_LEGEND[type] ?? EDGE_LEGEND["contributes-to"];
}

/** Cross-workstream edges (institution map) always render in this bright
 *  rose, dashed, regardless of their structural `edge_type` — the signal is
 *  "this crosses a workstream boundary," not the structural relationship. */
export const CROSS_EDGE_STROKE = "#f43f5e";
export const CROSS_EDGE_DASH = [6, 4];

/** A short on-canvas label fragment for a node — the first word/segment of
 *  its title, split on whitespace/hyphen/en-dash/em-dash. Deliberately NOT
 *  `issuer`: issuer is frequently shared across distinct nodes in the same
 *  graph (e.g. two BNM-issued documents both showing "BNM"), which makes
 *  nodes visually indistinguishable. The full title remains available via
 *  the canvas hover tooltip and in detail panels. */
export function shortLabel(title: string): string {
  return title.split(/[\s—–-]/)[0];
}

/** Ordered list for rendering the legend card. */
export const NODE_LEGEND_ORDER: NodeType[] = [
  "task",
  "internal-published",
  "international-standard",
  "peer-regulator",
  "act-law",
  "industry-input",
  "supervisory-letter",
  "others",
];

export const EDGE_LEGEND_ORDER: EdgeType[] = [
  "supersedes",
  "references",
  "contributes-to",
  "parallel-to",
];
