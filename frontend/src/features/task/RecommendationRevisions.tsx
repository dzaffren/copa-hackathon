import { useState } from "react";
import { ChevronDown, ChevronRight, History } from "lucide-react";

import type { RecommendationRevision } from "@/lib/types";

interface Props {
  revisions: RecommendationRevision[];
}

function formatAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/** What a recommendation said before it was rewritten.
 *
 *  A rewrite changes what the tool asserts, so it must not be silent: the marker
 *  says the card has been rewritten, and the disclosure shows exactly what it
 *  replaced. Same append-only reasoning as the linkage audit trail — history is
 *  never edited by the thing that writes history.
 */
export function RecommendationRevisions({ revisions }: Props) {
  const [open, setOpen] = useState(false);

  if (revisions.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        type="button"
        data-testid="revisions-toggle"
        aria-expanded={open}
        onClick={() => setOpen((wasOpen) => !wasOpen)}
        className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground hover:text-foreground"
      >
        {open ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        <History className="h-3 w-3" />
        <span data-testid="rewritten-marker">
          Rewritten
          {revisions.length > 1 ? ` ${revisions.length} times` : ""}
        </span>
      </button>

      {open && (
        <ul data-testid="revisions" className="mt-1.5 space-y-1.5">
          {revisions.map((revision, index) => (
            <li
              key={`${revision.at}-${index}`}
              data-testid="revision"
              className="rounded-md border border-border/50 bg-muted/30 p-2"
            >
              <div className="mb-0.5 text-[10px] font-semibold text-muted-foreground">
                Before {formatAt(revision.at)}
              </div>
              <p className="text-[11px] font-semibold leading-snug">
                {revision.title}
              </p>
              {revision.action && (
                <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                  {revision.action}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
