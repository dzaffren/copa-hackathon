import type { SemanticLabel, Sentiment } from "@/lib/types";

export interface LabelStyle {
  /** Label pill (bg + text). */
  pill: string;
  /** Analysed pair-card container accent. */
  card: string;
}

// The five-label taxonomy (aligns-with, differs-on, conflicts-with, silent-on,
// goes-beyond) plus the neutral fallback.
const LABEL_STYLES: Record<SemanticLabel, LabelStyle> = {
  "aligns-with": {
    pill: "bg-emerald-100 text-emerald-800",
    card: "border-gray-200 bg-white",
  },
  "differs-on": {
    pill: "bg-indigo-100 text-indigo-800",
    card: "border-gray-200 bg-white",
  },
  "conflicts-with": {
    pill: "bg-red-100 text-red-800",
    card: "border-red-200 bg-red-50",
  },
  "silent-on": {
    pill: "bg-slate-100 text-slate-700",
    card: "border-gray-200 bg-white",
  },
  "goes-beyond": {
    pill: "bg-violet-100 text-violet-800",
    card: "border-gray-200 bg-white",
  },
};

const FALLBACK: LabelStyle = {
  pill: "bg-slate-100 text-slate-700",
  card: "border-gray-200 bg-white",
};

export function labelStyle(label: SemanticLabel): LabelStyle {
  return LABEL_STYLES[label] ?? FALLBACK;
}

/** "differs-on ↑" (tighten) / "differs-on ↓" (loosen); label alone otherwise. */
export function labelText(label: SemanticLabel, sentiment: Sentiment): string {
  if (label === "differs-on" && sentiment === "tighten") return "differs-on ↑";
  if (label === "differs-on" && sentiment === "loosen") return "differs-on ↓";
  return label;
}
