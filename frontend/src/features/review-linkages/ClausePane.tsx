import { useEffect, useRef } from "react";
import { ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ReviewClause } from "@/lib/types";

interface ClausePaneProps {
  title: string;
  subtitle?: string | null;
  clauses: ReviewClause[];
  /** Clause numbers cited by the active finding — highlighted and scrolled to. */
  highlighted: string[];
  /** Distinguishes the two panes for test queries and scroll containers. */
  side: "source" | "target";
  /** When true and there are highlighted clauses, render only those cited. */
  filterToHighlighted?: boolean;
  /** The engine route serving this document's published PDF. When set, the
   *  header offers a button opening it in a new tab, so the drafter can check a
   *  card's verbatim text against the source. Absent for a working draft. */
  sourcePdfUrl?: string | null;
}

/** A vertical reader of clause cards for one side of a pair.
 *
 * Every card's text is the verbatim citation the engine returned on the finding
 * that cites it. This component must never synthesise, truncate, or reformat
 * clause text — the whole product rule rests on what is rendered here matching
 * the source document exactly.
 */
export function ClausePane({
  title,
  subtitle,
  clauses,
  highlighted,
  side,
  filterToHighlighted = false,
  sourcePdfUrl = null,
}: ClausePaneProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const firstHighlighted = highlighted[0];

  const visibleClauses =
    filterToHighlighted && highlighted.length > 0
      ? clauses.filter((clause) => highlighted.includes(clause.clause_number))
      : clauses;

  useEffect(() => {
    if (!firstHighlighted || !scrollRef.current) return;
    const target = scrollRef.current.querySelector(
      `[data-clause="${CSS.escape(firstHighlighted)}"]`,
    );
    // `block: "nearest"` keeps a clause already in view from jumping; only an
    // off-screen clause actually scrolls.
    target?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [firstHighlighted]);

  return (
    <section
      className="glass flex min-h-0 flex-col rounded-xl"
      aria-label={`${side} clauses`}
    >
      <header className="flex items-start justify-between gap-2 border-b border-border/60 px-4 py-3">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          {subtitle ? (
            <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
          ) : null}
        </div>
        {sourcePdfUrl ? (
          <Button
            variant="ghost"
            size="sm"
            className="-mr-1 -mt-0.5 shrink-0 text-xs text-muted-foreground hover:text-foreground"
            onClick={() =>
              window.open(sourcePdfUrl, "_blank", "noopener,noreferrer")
            }
          >
            <ExternalLink /> Source PDF
          </Button>
        ) : null}
      </header>

      <div
        ref={scrollRef}
        className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4"
      >
        {visibleClauses.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No clauses cited on this side — every finding is silent here.
          </p>
        ) : (
          visibleClauses.map((clause) => {
            const isLit = highlighted.includes(clause.clause_number);
            return (
              <article
                key={clause.clause_number}
                data-clause={clause.clause_number}
                data-highlighted={isLit || undefined}
                className={[
                  "rounded-md border-l-4 px-3 py-2 transition-colors",
                  isLit
                    ? "border-l-primary bg-primary/10 ring-1 ring-primary/30"
                    : "border-l-transparent bg-muted/20",
                ].join(" ")}
              >
                <p className="text-xs font-semibold text-foreground">
                  {clause.clause_number}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-foreground">
                  {clause.text}
                </p>
              </article>
            );
          })
        )}
      </div>
    </section>
  );
}
