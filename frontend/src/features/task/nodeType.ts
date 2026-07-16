import type { NodeType } from "@/lib/types";

export interface NodeTypeStyle {
  /** Small status dot colour. */
  dot: string;
  /** Neighbour-row container (bg + border + text). */
  row: string;
  /** Filter-chip border/text when not selected. */
  chip: string;
  /** Neighbour-name pill inside a pair card. */
  pill: string;
}

// Colour-codes the six workstream node types. Mirrors docs/poc/workstream-brain/task.html.
export const NODE_TYPE_STYLES: Record<NodeType, NodeTypeStyle> = {
  task: {
    dot: "bg-indigo-500",
    row: "bg-indigo-50 border-indigo-200 text-indigo-900",
    chip: "border-indigo-300 text-indigo-800",
    pill: "bg-indigo-100 text-indigo-800",
  },
  "international-standard": {
    dot: "bg-fuchsia-500",
    row: "bg-fuchsia-50 border-fuchsia-200 text-fuchsia-900",
    chip: "border-fuchsia-300 text-fuchsia-800",
    pill: "bg-fuchsia-100 text-fuchsia-800",
  },
  "peer-regulator": {
    dot: "bg-teal-500",
    row: "bg-teal-50 border-teal-200 text-teal-900",
    chip: "border-teal-300 text-teal-800",
    pill: "bg-teal-100 text-teal-800",
  },
  "internal-published": {
    dot: "bg-indigo-500",
    row: "bg-indigo-50 border-indigo-200 text-indigo-900",
    chip: "border-indigo-300 text-indigo-800",
    pill: "bg-indigo-100 text-indigo-800",
  },
  "act-law": {
    dot: "bg-amber-500",
    row: "bg-amber-50 border-amber-200 text-amber-900",
    chip: "border-amber-300 text-amber-800",
    pill: "bg-amber-100 text-amber-800",
  },
  "industry-input": {
    dot: "bg-emerald-500",
    row: "bg-emerald-50 border-emerald-200 text-emerald-900",
    chip: "border-emerald-300 text-emerald-800",
    pill: "bg-emerald-100 text-emerald-800",
  },
  others: {
    dot: "bg-gray-400",
    row: "bg-gray-50 border-gray-200 text-gray-900",
    chip: "border-gray-300 text-gray-800",
    pill: "bg-gray-100 text-gray-800",
  },
};

const FALLBACK: NodeTypeStyle = {
  dot: "bg-slate-400",
  row: "bg-slate-50 border-slate-200 text-slate-900",
  chip: "border-slate-300 text-slate-800",
  pill: "bg-slate-100 text-slate-800",
};

export function nodeTypeStyle(nodeType: NodeType): NodeTypeStyle {
  return NODE_TYPE_STYLES[nodeType] ?? FALLBACK;
}

// Short filter-chip labels keyed by the neighbour node id (falls back to the
// leading token of the title for any unmapped node).
const SHORT_LABELS: Record<string, string> = {
  "bcbs-opres-2021": "BCBS",
  "fsb-3rd-party": "FSB",
  "hkma-spm-or2": "HKMA",
  "rmit-pd-2025": "RMiT",
  "fsa-2013-143": "FSA",
  "abm-position": "ABM",
};

export function shortLabelForNode(nodeId: string, title: string): string {
  return SHORT_LABELS[nodeId] ?? title.split(/[\s—-]/)[0];
}
