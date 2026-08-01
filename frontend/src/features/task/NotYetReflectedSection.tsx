import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";

import { cn } from "@/lib/utils";
import type { UnreflectedFinding } from "@/lib/types";
import { labelStyle, labelText } from "./semanticLabel";

interface Props {
  workstreamId: string;
  findings: UnreflectedFinding[];
  /** Total accepted, for the "N of M" framing — a bare count of leftovers reads
   *  as alarming without the denominator. */
  acceptedCount: number;
}

/** Accepted findings no recommendation drew on.
 *
 *  Closes the gap that would otherwise open when a finding is accepted and then
 *  never cited: without this, it would simply be invisible. It is also a
 *  two-way quality signal — a large pile means either the engine under-read the
 *  evidence, or those findings genuinely warrant no policy change, and both are
 *  worth seeing.
 *
 *  **Read-only, and counted against every generated recommendation** (not only
 *  bookmarked ones), so the figure means the same thing here and beside the
 *  draft. It reports and links through; it does not generate, dismiss, or change
 *  a finding's state.
 */
export function NotYetReflectedSection({
  workstreamId,
  findings,
  acceptedCount,
}: Props) {
  const [open, setOpen] = useState(false);

  if (findings.length === 0) {
    return (
      <p
        data-testid="not-yet-reflected"
        data-count="0"
        className="border-t border-border/60 px-4 py-3 text-[11px] text-muted-foreground"
      >
        Every accepted finding is reflected in a recommendation.
      </p>
    );
  }

  return (
    <div
      data-testid="not-yet-reflected"
      data-count={findings.length}
      className="border-t border-border/60"
    >
      <button
        type="button"
        data-testid="not-yet-reflected-toggle"
        aria-expanded={open}
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        className="flex w-full items-center gap-1.5 px-4 py-2.5 text-left text-[11px] font-semibold text-muted-foreground hover:bg-accent/50"
      >
        {open ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        <span data-testid="not-yet-reflected-count">{findings.length}</span> of{" "}
        {acceptedCount} accepted findings not yet reflected
      </button>

      {open && (
        <ul className="space-y-1.5 px-4 pb-3">
          {findings.map((finding) => {
            const style = labelStyle(finding.label ?? "aligns-with");
            return (
              <li
                key={finding.finding_id}
                data-testid="unreflected-finding"
                data-finding-id={finding.finding_id}
                className="rounded-md border border-border/50 bg-muted/20 p-2"
              >
                <div className="mb-1 flex flex-wrap items-center gap-1.5">
                  {finding.label && (
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                        style.pill,
                      )}
                    >
                      {labelText(finding.label, finding.sentiment)}
                    </span>
                  )}
                  <span className="text-[10px] text-muted-foreground">
                    {finding.left.title ?? finding.left.id} ↔{" "}
                    {finding.right.title ?? finding.right.id}
                  </span>
                </div>

                {finding.summary && (
                  <p className="text-[11px] leading-relaxed text-muted-foreground">
                    {finding.summary}
                  </p>
                )}

                <div className="mt-1 flex items-center gap-2 text-[10px] text-muted-foreground">
                  {finding.source_clause_number && (
                    <span>{finding.source_clause_number}</span>
                  )}
                  {finding.target_clause_number && (
                    <span>↔ {finding.target_clause_number}</span>
                  )}
                  <Link
                    to={
                      `/workstreams/${workstreamId}/edges/${finding.edge_id}/review` +
                      `?finding=${encodeURIComponent(finding.finding_id)}`
                    }
                    className="inline-flex items-center gap-0.5 font-semibold text-primary hover:text-primary/80"
                  >
                    Open <ExternalLink className="h-2.5 w-2.5" />
                  </Link>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
