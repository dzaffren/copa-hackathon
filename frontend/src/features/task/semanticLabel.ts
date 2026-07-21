import type { SemanticLabel } from "@/lib/types";
import { LABEL_STYLES } from "@/lib/labels";

// Task-screen view of the five-label taxonomy. Pills come from the shared dark
// palette in @/lib/labels; `card` and `calloutBorder` add the container accents
// the task/drafting cards need on top of that. `labelText` is re-exported from
// the shared module so there is exactly one sentiment-arrow implementation.
export { labelText } from "@/lib/labels";

export interface LabelStyle {
  /** Label pill (bg + text + border). */
  pill: string;
  /** Analysed pair-card container accent. */
  card: string;
  /** Left-border accent for the drafting workspace's inline callouts. */
  calloutBorder: string;
}

const CARD_ACCENT: Record<
  SemanticLabel,
  { card: string; calloutBorder: string }
> = {
  "aligns-with": {
    card: "border-border/60 bg-card/50",
    calloutBorder: "border-emerald-400",
  },
  "differs-on": {
    card: "border-border/60 bg-card/50",
    calloutBorder: "border-amber-400",
  },
  "conflicts-with": {
    card: "border-red-400/30 bg-red-500/[0.06]",
    calloutBorder: "border-red-400",
  },
  "silent-on": {
    card: "border-border/60 bg-card/50",
    calloutBorder: "border-sky-400",
  },
  "goes-beyond": {
    card: "border-border/60 bg-card/50",
    calloutBorder: "border-violet-400",
  },
};

const FALLBACK: LabelStyle = {
  pill: "bg-slate-500/15 text-slate-300 border border-slate-400/30",
  card: "border-border/60 bg-card/50",
  calloutBorder: "border-slate-300",
};

export function labelStyle(label: SemanticLabel): LabelStyle {
  const base = LABEL_STYLES[label];
  const accent = CARD_ACCENT[label];
  if (!base || !accent) return FALLBACK;
  return {
    pill: base.pill,
    card: accent.card,
    calloutBorder: accent.calloutBorder,
  };
}
