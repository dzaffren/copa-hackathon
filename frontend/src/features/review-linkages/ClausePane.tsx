import { useEffect, useRef } from "react";
import type { ReviewClause } from "@/lib/types";

interface ClausePaneProps {
  title: string;
  subtitle?: string | null;
  clauses: ReviewClause[];
  /** Clause numbers cited by the active finding — highlighted and scrolled to. */
  highlighted: string[];
  /** Distinguishes the two panes for test queries and scroll containers. */
  side: "source" | "target";
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
}: ClausePaneProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const firstHighlighted = highlighted[0];

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
      <header className="border-b border-border/60 px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        {subtitle ? (
          <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
        ) : null}
      </header>

      <div
        ref={scrollRef}
        className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4"
      >
        {clauses.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No clauses cited on this side — every finding is silent here.
          </p>
        ) : (
          clauses.map((clause) => {
            const isLit = highlighted.includes(clause.clause_number);
            return (
              <article
                key={clause.clause_number}
                data-clause={clause.clause_number}
                data-highlighted={isLit || undefined}
                className={[
                  "rounded-md border-l-4 px-3 py-2 transition-colors",
                  isLit
                    ? "border-l-cyan-400 bg-cyan-500/10 ring-1 ring-cyan-400/30"
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
