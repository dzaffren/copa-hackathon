import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, ShieldCheck, TriangleAlert } from "lucide-react";

import { fetchAllCrossLinks } from "@/lib/api";
import { CROSS_STORE } from "@/lib/types";
import { isUnreviewed } from "@/lib/overlaps";

/**
 * The proactive surface this product exists to provide: every cross-workstream
 * overlap, on the very first screen, whether or not a drafter thought to look
 * for it. Directly answers the pain point named in product feedback —
 * overlapping policies (e.g. Business Continuity Management <-> Recovery
 * Planning) discovered only after FPWG, when unwinding them is expensive.
 * "Caught automatically — before FPWG" is the point; the card says so.
 */
export function OverlapAlertsCard() {
  const { data: links, isPending } = useQuery({
    queryKey: ["cross-links", "all"],
    queryFn: fetchAllCrossLinks,
  });

  if (isPending) return null;

  const untriaged = (links ?? []).filter(isUnreviewed);

  if (untriaged.length === 0) {
    return (
      <section
        data-testid="overlap-alerts-card"
        aria-label="Overlap alerts"
        className="mb-6 flex items-start gap-2.5 rounded-xl border border-border/60 bg-card/30 px-4 py-3 text-sm text-muted-foreground"
      >
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400/80" />
        <p>
          No overlaps detected yet. This runs automatically as workstreams are
          added — nothing to do here.
        </p>
      </section>
    );
  }

  return (
    <section
      data-testid="overlap-alerts-card"
      aria-label="Overlap alerts"
      className="mb-6 rounded-xl border border-rose-400/30 bg-rose-500/[0.07] p-4"
    >
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-rose-300">
          <TriangleAlert className="h-3.5 w-3.5" /> Overlap alerts
        </h2>
        <span className="text-[11px] font-medium text-rose-200/70">
          Caught automatically — before FPWG
        </span>
      </div>

      <ul className="mt-2.5 space-y-2">
        {untriaged.map((link) => (
          <li key={link.id}>
            <Link
              to={`/workstreams/${CROSS_STORE}/edges/${link.id}/review`}
              data-testid="overlap-alert-row"
              className="flex items-start justify-between gap-3 rounded-lg border border-rose-400/20 bg-card/60 p-2.5 transition hover:border-rose-400/50 hover:bg-card"
            >
              <p className="text-sm leading-snug">
                <span className="font-semibold">{link.near.title}</span>{" "}
                <span className="text-muted-foreground">↔</span>{" "}
                <span className="font-semibold">{link.far.title}</span>
                <span className="ml-1.5 text-muted-foreground">
                  — {link.findings_count} linkage
                  {link.findings_count === 1 ? "" : "s"} across two
                  workstreams, none reviewed yet.
                </span>
              </p>
              <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default OverlapAlertsCard;
