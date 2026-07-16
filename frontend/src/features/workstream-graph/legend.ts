import type { EdgeType, NodeType } from "@/lib/types";

// Colour + label maps for the graph canvas and detail panels. Mirrors the
// legend in docs/poc/workstream-brain/workstream.html so the built screen reads
// the same as the approved prototype.

export interface NodeStyle {
  label: string;
  /** SVG circle fill. */
  fill: string;
  /** SVG circle stroke. */
  stroke: string;
  /** SVG label text colour. */
  text: string;
  /** Tailwind classes for a node-type chip/badge in the panels. */
  badge: string;
}

export const NODE_LEGEND: Record<NodeType, NodeStyle> = {
  task: {
    label: "task",
    fill: "#4f46e5",
    stroke: "#312e81",
    text: "#ffffff",
    badge: "bg-indigo-600 text-white border-indigo-700",
  },
  "internal-published": {
    label: "internal-published",
    fill: "#eef2ff",
    stroke: "#6366f1",
    text: "#312e81",
    badge: "bg-indigo-100 text-indigo-800 border-indigo-300",
  },
  "international-standard": {
    label: "international-standard",
    fill: "#fdf4ff",
    stroke: "#c026d3",
    text: "#86198f",
    badge: "bg-fuchsia-100 text-fuchsia-800 border-fuchsia-300",
  },
  "peer-regulator": {
    label: "peer-regulator",
    fill: "#ecfeff",
    stroke: "#0d9488",
    text: "#134e4a",
    badge: "bg-teal-100 text-teal-800 border-teal-300",
  },
  "act-law": {
    label: "act-law",
    fill: "#fef3c7",
    stroke: "#d97706",
    text: "#92400e",
    badge: "bg-amber-100 text-amber-800 border-amber-300",
  },
  "industry-input": {
    label: "industry-input",
    fill: "#ecfdf5",
    stroke: "#059669",
    text: "#065f46",
    badge: "bg-emerald-100 text-emerald-800 border-emerald-300",
  },
  others: {
    label: "others",
    fill: "#f3f4f6",
    stroke: "#9ca3af",
    text: "#374151",
    badge: "bg-gray-100 text-gray-800 border-gray-300",
  },
};

export interface EdgeStyle {
  label: string;
  stroke: string;
  /** SVG stroke-dasharray; empty string for a solid line. */
  dash: string;
}

export const EDGE_LEGEND: Record<EdgeType, EdgeStyle> = {
  supersedes: { label: "supersedes", stroke: "#dc2626", dash: "" },
  references: { label: "references", stroke: "#0891b2", dash: "" },
  "contributes-to": { label: "contributes-to", stroke: "#4f46e5", dash: "4 3" },
  "parallel-to": { label: "parallel-to", stroke: "#6b7280", dash: "6 3" },
};

const FALLBACK_NODE: NodeStyle = NODE_LEGEND.others;

export function nodeStyle(type: NodeType): NodeStyle {
  return NODE_LEGEND[type] ?? FALLBACK_NODE;
}

export function edgeStyle(type: EdgeType): EdgeStyle {
  return EDGE_LEGEND[type] ?? EDGE_LEGEND["contributes-to"];
}

/** Ordered list for rendering the legend card. */
export const NODE_LEGEND_ORDER: NodeType[] = [
  "task",
  "internal-published",
  "international-standard",
  "peer-regulator",
  "act-law",
  "industry-input",
  "others",
];

export const EDGE_LEGEND_ORDER: EdgeType[] = [
  "supersedes",
  "references",
  "contributes-to",
  "parallel-to",
];
