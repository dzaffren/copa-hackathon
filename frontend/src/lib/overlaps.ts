import type { CrossLink } from "@/lib/types";

// The one shared definition of "alert-worthy" for a cross-workstream link, so
// the Home dashboard's Overlap Alerts card and the Institution Map's banner
// never drift into two different answers for the same data. Generalizes what
// used to be a title regex matching one named pair (BCM <-> Recovery
// Planning) — any untriaged overlap qualifies, which is the point: catching
// the next one, not just the one already known about.

/** A cross-workstream link nobody has triaged yet — its findings sit exactly
 *  as the finder/critic left them, with nothing accepted or dismissed. */
export function isUnreviewed(link: CrossLink): boolean {
  return link.counts.accepted === 0 && link.counts.dismissed === 0;
}

/** The most attention-worthy untriaged link, or null if every link has
 *  already been triaged (or there are none). Prefers the link with the most
 *  findings, since that overlap is the one most worth a drafter's time. */
export function headlineOverlap(links: CrossLink[]): CrossLink | null {
  const unreviewed = links.filter(isUnreviewed);
  if (unreviewed.length === 0) return null;
  return [...unreviewed].sort((a, b) => b.findings_count - a.findings_count)[0];
}
