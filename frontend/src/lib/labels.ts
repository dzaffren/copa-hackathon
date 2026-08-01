import type { ReviewState, SemanticLabel, Sentiment } from "@/lib/types";

// One source of truth for the five-label semantic taxonomy:
//   aligns-with · differs-on · conflicts-with · silent-on · goes-beyond
// Plan palette: aligns=emerald, differs=amber, conflicts=red, silent=blue,
// goes-beyond=purple. Sentiment (tighten/loosen) renders ONLY on `differs-on`.

export interface LabelStyle {
  /** Human label text. */
  label: string;
  /** What the label means, for the legend. Written for the drafter, so it does
   *  NOT track `_TAXONOMY_PROMPT_BLOCK` in `engine/connections.py` word for
   *  word — that block is model instruction and reads like it. The two must
   *  still agree in MEANING: the block is what the finder and critic are
   *  actually told, so a legend that contradicts it would be describing a
   *  taxonomy the engine does not apply. */
  description: string;
  /** Pill: translucent bg + coloured text + hairline border, reads on white. */
  pill: string;
  /** Left-border accent for cards and inline callouts. */
  accent: string;
  /** Small status dot. */
  dot: string;
  /** Solid colour for canvas strokes (institution-map cross-links). */
  canvas: string;
}

export const LABEL_STYLES: Record<SemanticLabel, LabelStyle> = {
  "aligns-with": {
    label: "aligns-with",
    description:
      "Both documents take the same position on this concept, no reconciliation required.",
    pill: "bg-emerald-500/15 text-emerald-700 border border-emerald-400/30",
    accent: "border-l-emerald-400",
    dot: "bg-emerald-400",
    canvas: "#34d399",
  },
  "differs-on": {
    label: "differs-on",
    description:
      "Both address this concept but set different requirements, ↑/↓/- this document is tighter/looser/neutral.",
    pill: "bg-amber-400/15 text-amber-700 border border-amber-300/30",
    accent: "border-l-amber-400",
    dot: "bg-amber-400",
    canvas: "#fbbf24",
  },
  "conflicts-with": {
    label: "conflicts-with",
    description:
      "The two requirements are incompatible, i.e. an institution complying with one contradicts the other.",
    pill: "bg-red-500/15 text-red-700 border border-red-400/30",
    accent: "border-l-red-400",
    dot: "bg-red-400",
    canvas: "#f87171",
  },
  "silent-on": {
    label: "silent-on",
    description:
      "Concept omitted from this document but not the other document.",
    pill: "bg-sky-500/15 text-sky-700 border border-sky-400/30",
    accent: "border-l-sky-400",
    dot: "bg-sky-400",
    canvas: "#38bdf8",
  },
  "goes-beyond": {
    label: "goes-beyond",
    description:
      "Concept addressed only in this document but not the other document.",
    pill: "bg-violet-500/15 text-violet-700 border border-violet-400/30",
    accent: "border-l-violet-400",
    dot: "bg-violet-400",
    canvas: "#a78bfa",
  },
};

const FALLBACK: LabelStyle = {
  label: "unknown",
  description: "Not one of the five semantic labels.",
  pill: "bg-slate-500/15 text-slate-700 border border-slate-400/30",
  accent: "border-l-slate-400",
  dot: "bg-slate-400",
  canvas: "#94a3b8",
};

export function labelStyle(label: SemanticLabel): LabelStyle {
  return LABEL_STYLES[label] ?? FALLBACK;
}

/** Taxonomy declaration order — for legends and label-count grids, where the
 *  point is "here are the five labels", not "here is what needs attention". */
export const LABEL_ORDER: SemanticLabel[] = [
  "aligns-with",
  "differs-on",
  "conflicts-with",
  "silent-on",
  "goes-beyond",
];

/** Attention order — most→least urgent for the drafter. Every list of finding
 *  cards in the app renders in this order so a conflict is never buried under
 *  the alignments that happened to precede it in the findings file. */
export const LABEL_SEVERITY_ORDER: SemanticLabel[] = [
  "conflicts-with",
  "differs-on",
  "silent-on",
  "goes-beyond",
  "aligns-with",
];

const SEVERITY_RANK: Record<SemanticLabel, number> =
  LABEL_SEVERITY_ORDER.reduce(
    (acc, label, i) => ({ ...acc, [label]: i }),
    {} as Record<SemanticLabel, number>,
  );

/** Rank of a label in `LABEL_SEVERITY_ORDER`; an unknown label sorts last. */
export function labelSeverityRank(label: SemanticLabel): number {
  return SEVERITY_RANK[label] ?? LABEL_SEVERITY_ORDER.length;
}

/** Copy of `items` in attention order. A view concern only — the engine never
 *  reorders a findings file. `Array.prototype.sort` is stable, so findings
 *  sharing a label keep their original (file) order. */
export function bySeverity<T extends { label: SemanticLabel }>(
  items: readonly T[],
): T[] {
  return [...items].sort(
    (a, b) => labelSeverityRank(a.label) - labelSeverityRank(b.label),
  );
}

/** Review-state rank within a label group: pending floats, judged sinks.
 *  Accepted and dismissed share a rank so they sink together and keep their
 *  server order relative to each other — the drafter's own sequence of
 *  decisions is the order she expects to see them in. */
export function reviewStateRank(state: ReviewState): number {
  return state === "pending" ? 0 : 1;
}

/** One label group's findings in display order: pending first, then judged,
 *  each block preserving server order (`Array.prototype.sort` is stable).
 *
 *  A view concern only — the engine never reorders a findings file. Distinct
 *  from `bySeverity`, which orders ACROSS labels: inside a group every finding
 *  shares a label, so review state is the only axis left to sort on. */
export function forGroupDisplay<T extends { review_state: ReviewState }>(
  items: readonly T[],
): T[] {
  return [...items].sort(
    (a, b) => reviewStateRank(a.review_state) - reviewStateRank(b.review_state),
  );
}

/** "tighten" → "↑", "loosen" → "↓". Only meaningful on `differs-on`. */
export function sentimentArrow(sentiment: Sentiment): string {
  if (sentiment === "tighten") return "↑";
  if (sentiment === "loosen") return "↓";
  return "";
}

/** Full label text: "differs-on ↑" when a sentiment applies, else the label. */
export function labelText(label: SemanticLabel, sentiment: Sentiment): string {
  const arrow = label === "differs-on" ? sentimentArrow(sentiment) : "";
  return arrow ? `${label} ${arrow}` : label;
}
