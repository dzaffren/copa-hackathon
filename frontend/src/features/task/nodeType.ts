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

// Colour-codes the eight workstream node types for the light theme (BNM / GEMA
// enterprise palette). Mirrors the node palette in
// @/features/workstream-graph/legend.ts (task=royal blue, international-
// standard=gold, peer-regulator=rose, act-law=red, industry-input=sky,
// internal-published=emerald, supervisory-letter=violet, others=slate). Fills
// stay subtle
// (/10–/15) so they never overpower the white page; borders sit at /30 for
// crisp definition; text uses deep -800/-900 shades for AA contrast on white.
export const NODE_TYPE_STYLES: Record<NodeType, NodeTypeStyle> = {
  task: {
    dot: "bg-primary",
    row: "bg-blue-500/10 border-blue-600/30 text-blue-900",
    chip: "border-blue-600/30 text-blue-800",
    pill: "bg-blue-500/15 text-blue-900",
  },
  "international-standard": {
    dot: "bg-amber-500",
    row: "bg-amber-400/10 border-amber-500/30 text-amber-900",
    chip: "border-amber-500/30 text-amber-800",
    pill: "bg-amber-400/15 text-amber-900",
  },
  "peer-regulator": {
    dot: "bg-rose-500",
    row: "bg-rose-500/10 border-rose-500/30 text-rose-900",
    chip: "border-rose-500/30 text-rose-800",
    pill: "bg-rose-500/15 text-rose-900",
  },
  "internal-published": {
    dot: "bg-emerald-500",
    row: "bg-emerald-500/10 border-emerald-600/30 text-emerald-900",
    chip: "border-emerald-600/30 text-emerald-800",
    pill: "bg-emerald-500/15 text-emerald-900",
  },
  "act-law": {
    dot: "bg-red-500",
    row: "bg-red-500/10 border-red-500/30 text-red-900",
    chip: "border-red-500/30 text-red-800",
    pill: "bg-red-500/15 text-red-900",
  },
  "industry-input": {
    dot: "bg-sky-500",
    row: "bg-sky-500/10 border-sky-600/30 text-sky-900",
    chip: "border-sky-600/30 text-sky-800",
    pill: "bg-sky-500/15 text-sky-900",
  },
  "supervisory-letter": {
    dot: "bg-violet-500",
    row: "bg-violet-500/10 border-violet-500/30 text-violet-900",
    chip: "border-violet-500/30 text-violet-800",
    pill: "bg-violet-500/15 text-violet-900",
  },
  others: {
    dot: "bg-slate-500",
    row: "bg-slate-500/10 border-slate-400/30 text-slate-800",
    chip: "border-slate-400/40 text-slate-700",
    pill: "bg-slate-500/15 text-slate-800",
  },
};

const FALLBACK: NodeTypeStyle = {
  dot: "bg-slate-500",
  row: "bg-slate-500/10 border-slate-400/30 text-slate-800",
  chip: "border-slate-400/40 text-slate-700",
  pill: "bg-slate-500/15 text-slate-800",
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
