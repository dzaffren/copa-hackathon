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

// Colour-codes the eight workstream node types for the dark theme. Mirrors the
// node palette in @/features/workstream-graph/legend.ts (task=cyan,
// international-standard=gold, peer-regulator=coral, act-law=red,
// industry/internal=teal/emerald, supervisory-letter=violet, others=slate).
export const NODE_TYPE_STYLES: Record<NodeType, NodeTypeStyle> = {
  task: {
    dot: "bg-cyan-400",
    row: "bg-cyan-500/10 border-cyan-400/25 text-cyan-100",
    chip: "border-cyan-400/40 text-cyan-300",
    pill: "bg-cyan-500/15 text-cyan-300",
  },
  "international-standard": {
    dot: "bg-amber-400",
    row: "bg-amber-400/10 border-amber-300/25 text-amber-100",
    chip: "border-amber-300/40 text-amber-300",
    pill: "bg-amber-400/15 text-amber-300",
  },
  "peer-regulator": {
    dot: "bg-rose-400",
    row: "bg-rose-500/10 border-rose-400/25 text-rose-100",
    chip: "border-rose-400/40 text-rose-300",
    pill: "bg-rose-500/15 text-rose-300",
  },
  "internal-published": {
    dot: "bg-emerald-400",
    row: "bg-emerald-500/10 border-emerald-400/25 text-emerald-100",
    chip: "border-emerald-400/40 text-emerald-300",
    pill: "bg-emerald-500/15 text-emerald-300",
  },
  "act-law": {
    dot: "bg-red-400",
    row: "bg-red-500/10 border-red-400/25 text-red-100",
    chip: "border-red-400/40 text-red-300",
    pill: "bg-red-500/15 text-red-300",
  },
  "industry-input": {
    dot: "bg-teal-400",
    row: "bg-teal-500/10 border-teal-400/25 text-teal-100",
    chip: "border-teal-400/40 text-teal-300",
    pill: "bg-teal-500/15 text-teal-300",
  },
  "supervisory-letter": {
    dot: "bg-violet-400",
    row: "bg-violet-500/10 border-violet-400/25 text-violet-100",
    chip: "border-violet-400/40 text-violet-300",
    pill: "bg-violet-500/15 text-violet-300",
  },
  others: {
    dot: "bg-slate-400",
    row: "bg-slate-500/10 border-slate-400/25 text-slate-100",
    chip: "border-slate-400/40 text-slate-300",
    pill: "bg-slate-500/15 text-slate-300",
  },
};

const FALLBACK: NodeTypeStyle = {
  dot: "bg-slate-400",
  row: "bg-slate-500/10 border-slate-400/25 text-slate-100",
  chip: "border-slate-400/40 text-slate-300",
  pill: "bg-slate-500/15 text-slate-300",
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
