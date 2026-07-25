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

// Colour-codes the eight workstream node types for the light theme. Mirrors the
// node palette in @/features/workstream-graph/legend.ts (task=indigo,
// international-standard=gold, peer-regulator=coral, act-law=red,
// industry/internal=teal/emerald, supervisory-letter=violet, others=slate) —
// light tint backgrounds with darker, readable text.
export const NODE_TYPE_STYLES: Record<NodeType, NodeTypeStyle> = {
  task: {
    dot: "bg-primary",
    row: "bg-primary/10 border-primary/25 text-primary",
    chip: "border-primary/40 text-primary",
    pill: "bg-primary/10 text-primary",
  },
  "international-standard": {
    dot: "bg-amber-500",
    row: "bg-amber-400/10 border-amber-500/25 text-amber-700",
    chip: "border-amber-500/40 text-amber-700",
    pill: "bg-amber-400/15 text-amber-700",
  },
  "peer-regulator": {
    dot: "bg-pink-500",
    row: "bg-pink-500/10 border-pink-500/25 text-pink-700",
    chip: "border-pink-500/40 text-pink-700",
    pill: "bg-pink-500/15 text-pink-700",
  },
  "internal-published": {
    dot: "bg-sky-500",
    row: "bg-sky-500/10 border-sky-500/25 text-sky-700",
    chip: "border-sky-500/40 text-sky-700",
    pill: "bg-sky-500/15 text-sky-700",
  },
  "act-law": {
    dot: "bg-red-500",
    row: "bg-red-500/10 border-red-500/25 text-red-700",
    chip: "border-red-500/40 text-red-700",
    pill: "bg-red-500/15 text-red-700",
  },
  "industry-input": {
    dot: "bg-teal-500",
    row: "bg-teal-500/10 border-teal-500/25 text-teal-700",
    chip: "border-teal-500/40 text-teal-700",
    pill: "bg-teal-500/15 text-teal-700",
  },
  "supervisory-letter": {
    dot: "bg-violet-500",
    row: "bg-violet-500/10 border-violet-500/25 text-violet-700",
    chip: "border-violet-500/40 text-violet-700",
    pill: "bg-violet-500/15 text-violet-700",
  },
  others: {
    dot: "bg-slate-500",
    row: "bg-slate-500/10 border-slate-500/25 text-slate-700",
    chip: "border-slate-500/40 text-slate-700",
    pill: "bg-slate-500/15 text-slate-700",
  },
};

const FALLBACK: NodeTypeStyle = {
  dot: "bg-slate-500",
  row: "bg-slate-500/10 border-slate-500/25 text-slate-700",
  chip: "border-slate-500/40 text-slate-700",
  pill: "bg-slate-500/15 text-slate-700",
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
