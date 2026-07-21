import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, GitCompareArrows } from "lucide-react";

import { fetchCrossLinks } from "@/lib/api";
import { CROSS_STORE, type SemanticLabel } from "@/lib/types";
import { labelStyle } from "@/lib/labels";

/** Linkages from this workstream's documents into another workstream's.
 *
 * The point of the whole product, in one panel: two teams draft in parallel,
 * each anchoring to different versions of the same policy, and nobody notices
 * until publication. These linkages were found with no curated edges between the
 * two workstreams — see data/workstreams/_cross/README.md.
 *
 * Clicking through lands on the ordinary review screen. That is not a shortcut:
 * a cross-workstream linkage is reviewed, accepted, and dismissed exactly like
 * any other, so it needs no second reader.
 */
export function CrossWorkstreamPanel({
  workstreamId,
}: {
  workstreamId: string;
}) {
  const { data: links = [], isPending } = useQuery({
    queryKey: ["cross-links", workstreamId],
    queryFn: () => fetchCrossLinks(workstreamId),
  });

  if (isPending || links.length === 0) return null;

  return (
    <section
      data-testid="cross-workstream-panel"
      aria-label="Cross-workstream linkages"
      className="rounded-xl border border-amber-400/30 bg-amber-400/[0.07] p-3"
    >
      <h2 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-300">
        <GitCompareArrows className="h-3.5 w-3.5" /> Cross-workstream
      </h2>
      <p className="mt-0.5 text-[11px] leading-snug text-amber-200/70">
        Linkages into workstreams other teams are drafting in parallel.
      </p>

      <ul className="mt-2 space-y-2">
        {links.map((link) => (
          <li key={link.id}>
            <Link
              to={`/workstreams/${CROSS_STORE}/edges/${link.id}/review`}
              data-testid="cross-link-card"
              data-far-workstream={link.far.workstream_id ?? undefined}
              className="block rounded-lg border border-amber-400/20 bg-card/60 p-2.5 transition hover:border-amber-400/50 hover:bg-card"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold leading-snug">
                  {link.near.title}{" "}
                  <span className="font-normal text-muted-foreground">↔</span>{" "}
                  {link.far.title}
                </p>
                <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              </div>

              <p className="mt-0.5 text-[11px] text-muted-foreground">
                in {link.far.workstream_name ?? link.far.workstream_id}
              </p>

              <div className="mt-1.5 flex flex-wrap items-center gap-1">
                <span
                  data-testid="cross-link-count"
                  className="text-[11px] font-semibold"
                >
                  {link.findings_count} linkages
                </span>
                {(Object.entries(link.labels) as [SemanticLabel, number][]).map(
                  ([label, n]) => (
                    <span
                      key={label}
                      className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${labelStyle(label).pill}`}
                    >
                      {n} {label}
                    </span>
                  ),
                )}
                {link.counts.accepted > 0 && (
                  <span className="text-[10px] text-muted-foreground">
                    · {link.counts.accepted} accepted
                  </span>
                )}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default CrossWorkstreamPanel;
