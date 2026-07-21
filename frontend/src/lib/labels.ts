import type { SemanticLabel, Sentiment } from "@/lib/types";

// One source of truth for the five-label semantic taxonomy on the dark theme:
//   aligns-with · differs-on · conflicts-with · silent-on · goes-beyond
// Plan palette: aligns=emerald, differs=amber, conflicts=red, silent=blue,
// goes-beyond=purple. Sentiment (tighten/loosen) renders ONLY on `differs-on`.

export interface LabelStyle {
  /** Human label text. */
  label: string;
  /** Pill: translucent bg + coloured text + hairline border, reads on navy. */
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
    pill: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/30",
    accent: "border-l-emerald-400",
    dot: "bg-emerald-400",
    canvas: "#34d399",
  },
  "differs-on": {
    label: "differs-on",
    pill: "bg-amber-400/15 text-amber-300 border border-amber-300/30",
    accent: "border-l-amber-400",
    dot: "bg-amber-400",
    canvas: "#fbbf24",
  },
  "conflicts-with": {
    label: "conflicts-with",
    pill: "bg-red-500/15 text-red-300 border border-red-400/30",
    accent: "border-l-red-400",
    dot: "bg-red-400",
    canvas: "#f87171",
  },
  "silent-on": {
    label: "silent-on",
    pill: "bg-sky-500/15 text-sky-300 border border-sky-400/30",
    accent: "border-l-sky-400",
    dot: "bg-sky-400",
    canvas: "#38bdf8",
  },
  "goes-beyond": {
    label: "goes-beyond",
    pill: "bg-violet-500/15 text-violet-300 border border-violet-400/30",
    accent: "border-l-violet-400",
    dot: "bg-violet-400",
    canvas: "#a78bfa",
  },
};

const FALLBACK: LabelStyle = {
  label: "unknown",
  pill: "bg-slate-500/15 text-slate-300 border border-slate-400/30",
  accent: "border-l-slate-400",
  dot: "bg-slate-400",
  canvas: "#94a3b8",
};

export function labelStyle(label: SemanticLabel): LabelStyle {
  return LABEL_STYLES[label] ?? FALLBACK;
}

export const LABEL_ORDER: SemanticLabel[] = [
  "aligns-with",
  "differs-on",
  "conflicts-with",
  "silent-on",
  "goes-beyond",
];

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
