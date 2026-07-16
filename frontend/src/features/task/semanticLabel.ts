import type { SemanticLabel, Sentiment } from "@/lib/types";

export interface LabelStyle {
  /** Label pill (bg + text). */
  pill: string;
  /** Analysed pair-card container accent. */
  card: string;
  /** Left-border accent for the drafting workspace's inline callouts.
   *
   *  Derived from this same palette rather than the drafting spec's own colour
   *  list, which asks for sky on `goes-beyond` where the app has long used
   *  violet. One palette that disagrees with a spec beats two palettes that
   *  disagree with each other. */
  calloutBorder: string;
}

// The five-label taxonomy (aligns-with, differs-on, conflicts-with, silent-on,
// goes-beyond) plus the neutral fallback.
const LABEL_STYLES: Record<SemanticLabel, LabelStyle> = {
  "aligns-with": {
    pill: "bg-emerald-100 text-emerald-800",
    card: "border-gray-200 bg-white",
    calloutBorder: "border-emerald-400",
  },
  "differs-on": {
    pill: "bg-indigo-100 text-indigo-800",
    card: "border-gray-200 bg-white",
    calloutBorder: "border-indigo-400",
  },
  "conflicts-with": {
    pill: "bg-red-100 text-red-800",
    card: "border-red-200 bg-red-50",
    calloutBorder: "border-red-400",
  },
  "silent-on": {
    pill: "bg-slate-100 text-slate-700",
    card: "border-gray-200 bg-white",
    calloutBorder: "border-slate-300",
  },
  "goes-beyond": {
    pill: "bg-violet-100 text-violet-800",
    card: "border-gray-200 bg-white",
    calloutBorder: "border-violet-400",
  },
};

const FALLBACK: LabelStyle = {
  pill: "bg-slate-100 text-slate-700",
  card: "border-gray-200 bg-white",
  calloutBorder: "border-slate-300",
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
