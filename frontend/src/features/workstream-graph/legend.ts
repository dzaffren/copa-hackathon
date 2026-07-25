import type { EdgeType, NodeType } from "@/lib/types";

// Colour + label maps for the graph canvas and detail panels. Tuned for the
// light theme (see index.css + CLAUDE.md): mid-to-deep saturated node fills
// (Tailwind 500–600 range) that hold visual weight on a white canvas, a darker
// stroke for a crisp edge, and near-white label text drawn inside each filled
// circle. Badge classes are the light-tint chip variants used in the panels.
// One source of truth for every node/edge colour in the app.

export interface NodeStyle {
  label: string;
  /** Canvas circle fill — a saturated colour that reads on a white canvas. */
  fill: string;
  /** Canvas circle stroke — slightly darker than the fill for definition. */
  stroke: string;
  /** Canvas label text colour (drawn on the light canvas, so near-black). */
  text: string;
  /** Tailwind classes for a node-type chip/badge in the panels. */
  badge: string;
}

export const NODE_LEGEND: Record<NodeType, NodeStyle> = {
  task: {
    label: "task",
    fill: "#1d4ed8", // BNM blue — the hero node, matches the app primary
    stroke: "#1e40af",
    text: "#0f172a",
    badge: "bg-primary/10 text-primary border-primary/30",
  },
  "internal-published": {
    label: "internal-published",
    fill: "#4dabf7", // sky blue — lighter than the deep task blue, clearly distinct
    stroke: "#339af0",
    text: "#0f172a",
    badge: "bg-sky-500/10 text-sky-700 border-sky-500/30",
  },
  "international-standard": {
    label: "international-standard",
    fill: "#f59f00", // amber/gold
    stroke: "#e67700",
    text: "#0f172a",
    badge: "bg-amber-400/15 text-amber-700 border-amber-500/30",
  },
  "peer-regulator": {
    label: "peer-regulator",
    fill: "#e64980", // pink/magenta — separated from the pure red of act-law
    stroke: "#d6336c",
    text: "#0f172a",
    badge: "bg-pink-500/10 text-pink-700 border-pink-500/30",
  },
  "act-law": {
    label: "act-law",
    fill: "#e03131", // red
    stroke: "#c92a2a",
    text: "#0f172a",
    badge: "bg-red-500/10 text-red-700 border-red-500/30",
  },
  "industry-input": {
    label: "industry-input",
    fill: "#0ca678", // teal — blue-green, distinct from the green above
    stroke: "#099268",
    text: "#0f172a",
    badge: "bg-teal-500/10 text-teal-700 border-teal-500/30",
  },
  "supervisory-letter": {
    label: "supervisory-letter",
    fill: "#7048e8", // grape/violet
    stroke: "#6741d9",
    text: "#0f172a",
    badge: "bg-violet-500/10 text-violet-700 border-violet-500/30",
  },
  others: {
    label: "others",
    fill: "#868e96", // grey
    stroke: "#495057",
    text: "#0f172a",
    badge: "bg-slate-500/10 text-slate-700 border-slate-500/30",
  },
};

export interface EdgeStyle {
  label: string;
  stroke: string;
  /** Canvas line dash pattern (px on/off); empty for a solid line. */
  dash: number[];
}

export const EDGE_LEGEND: Record<EdgeType, EdgeStyle> = {
  supersedes: { label: "supersedes", stroke: "#dc2626", dash: [] },
  references: { label: "references", stroke: "#2563eb", dash: [] },
  "contributes-to": {
    label: "contributes-to",
    stroke: "#6366f1",
    dash: [5, 4],
  },
  "parallel-to": { label: "parallel-to", stroke: "#64748b", dash: [7, 4] },
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
export const CROSS_EDGE_STROKE = "#e11d48";
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
