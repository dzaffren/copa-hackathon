import type {
  ConceptsAvailable,
  CrossLink,
  Placeholder,
  RelationshipClassification,
  RiskLevel,
} from "@/lib/types";

// Presentation for the relationship classification + risk rollup the engine
// derives (engine/cross_intel.py). Kept in one place so the list, the metrics
// header, and the relationship panel never render the same relationship two
// different colours.

export interface ClassStyle {
  label: string;
  /** Translucent pill — reads on the dark navy. */
  pill: string;
  /** Small status dot. */
  dot: string;
}

export const CLASS_STYLES: Record<RelationshipClassification, ClassStyle> = {
  conflict: {
    label: "Conflict",
    pill: "bg-red-500/15 text-red-300 border border-red-400/30",
    dot: "bg-red-400",
  },
  divergent: {
    label: "Divergent",
    pill: "bg-amber-400/15 text-amber-300 border border-amber-300/30",
    dot: "bg-amber-400",
  },
  overlap: {
    label: "Overlap",
    pill: "bg-sky-500/15 text-sky-300 border border-sky-400/30",
    dot: "bg-sky-400",
  },
  aligned: {
    label: "Aligned",
    pill: "bg-emerald-500/15 text-emerald-300 border border-emerald-400/30",
    dot: "bg-emerald-400",
  },
};

const CLASS_FALLBACK: ClassStyle = {
  label: "Overlap",
  pill: "bg-slate-500/15 text-slate-300 border border-slate-400/30",
  dot: "bg-slate-400",
};

export function classStyle(c: RelationshipClassification): ClassStyle {
  return CLASS_STYLES[c] ?? CLASS_FALLBACK;
}

export const RISK_STYLES: Record<RiskLevel, { label: string; pill: string }> = {
  high: { label: "High risk", pill: "bg-red-500/15 text-red-300 border border-red-400/30" },
  medium: {
    label: "Medium risk",
    pill: "bg-amber-400/15 text-amber-300 border border-amber-300/30",
  },
  low: { label: "Low risk", pill: "bg-slate-500/15 text-slate-300 border border-slate-400/40" },
};

export function riskStyle(r: RiskLevel) {
  return RISK_STYLES[r] ?? RISK_STYLES.low;
}

/** Linkages on a relationship that no human has triaged yet (nothing accepted
 *  or dismissed). The unreviewed backlog the early-warning system exists to
 *  clear before a workstream reaches FPWG. */
export function unreviewedCount(link: CrossLink): number {
  return Math.max(0, link.counts.total - link.counts.accepted - link.counts.dismissed);
}

export interface IntelMetrics {
  activeWorkstreams: number;
  potentialOverlaps: number;
  highRiskConflicts: number;
  unreviewedLinkages: number;
  recentlyDetected: number;
  latestDetectedAt: string | null;
}

/** The summary-metrics header, computed from the corpus-wide cross-link list
 *  plus the count of active workstreams. */
export function intelMetrics(
  links: CrossLink[],
  activeWorkstreams: number,
): IntelMetrics {
  const dates = links
    .map((l) => l.detected_at)
    .filter((d): d is string => Boolean(d))
    .sort();
  return {
    activeWorkstreams,
    potentialOverlaps: links.length,
    highRiskConflicts: links.filter((l) => l.risk_level === "high").length,
    unreviewedLinkages: links.reduce((sum, l) => sum + unreviewedCount(l), 0),
    recentlyDetected: dates.length,
    latestDetectedAt: dates.length > 0 ? dates[dates.length - 1] : null,
  };
}

/** Concept fields may arrive as a list, a bare string, or null (older
 *  side-files). Normalise to a display list. */
export function asList(value: string[] | string | null | undefined): string[] {
  if (value == null) return [];
  return Array.isArray(value) ? value : [value];
}

/** The regulatory-profile concept block, or null when a node has not been
 *  enriched (so the caller can render a "pending" state instead of guessing). */
export function conceptsOf(
  c: Placeholder | ConceptsAvailable | undefined,
): ConceptsAvailable | null {
  // Placeholder.status is a wide `string`, so the union does not auto-narrow;
  // the "available" check is the discriminant and the cast is safe.
  return c && c.status === "available" ? (c as ConceptsAvailable) : null;
}
