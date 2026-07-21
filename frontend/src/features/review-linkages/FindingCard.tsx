import type { ReviewFinding } from "@/lib/types";
import { labelStyle, labelText } from "@/features/task/semanticLabel";

interface FindingCardProps {
  finding: ReviewFinding;
  isActive: boolean;
  isPending: boolean;
  onSelect: (finding: ReviewFinding) => void;
  onAccept: (finding: ReviewFinding) => void;
  onDismiss: (finding: ReviewFinding) => void;
  onReopen: (finding: ReviewFinding) => void;
}

/** One AI-found linkage, with its accept / dismiss / reopen controls.
 *
 * Reuses the task screen's `semanticLabel` helpers rather than restating the
 * colour map: two label palettes that drift apart is a real failure mode this
 * repo has already been bitten by. Sentiment (tighten/loosen) is shown as a
 * separate tag and ONLY on `differs-on`.
 */
export function FindingCard({
  finding,
  isActive,
  isPending,
  onSelect,
  onAccept,
  onDismiss,
  onReopen,
}: FindingCardProps) {
  const isDismissed = finding.review_state === "dismissed";
  const isAccepted = finding.review_state === "accepted";
  const style = labelStyle(finding.label);

  const sourceRef = finding.source_clauses[0]?.clause_number ?? "(silent)";
  // A goes-beyond finding cites nothing on the target side — the card says so
  // rather than rendering a dangling arrow.
  const targetRef = finding.target_clauses[0]?.clause_number ?? "(silent)";

  // Sentiment is only meaningful on differs-on (tighten/loosen).
  const sentimentTag =
    finding.label === "differs-on" && finding.sentiment
      ? finding.sentiment
      : null;

  return (
    <article
      data-testid="finding-card"
      data-finding-id={finding.id}
      data-active={isActive || undefined}
      data-review-state={finding.review_state}
      aria-current={isActive}
      // Dismissed cards are inert: clicking one must not steal the active
      // selection or re-highlight the panes.
      onClick={isDismissed ? undefined : () => onSelect(finding)}
      className={[
        "rounded-xl border p-3 text-left transition",
        isDismissed
          ? "cursor-default border-border/60 bg-muted/20 opacity-60"
          : "cursor-pointer " + style.card,
        isActive && !isDismissed ? "ring-2 ring-cyan-400/70" : "",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${style.pill}`}
        >
          {labelText(finding.label, finding.sentiment)}
        </span>
        {sentimentTag ? (
          <span className="rounded-full border border-amber-300/30 bg-amber-400/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300">
            {sentimentTag}
          </span>
        ) : null}
        {isAccepted ? (
          <span
            data-testid="accepted-badge"
            className="rounded-full border border-emerald-400/30 bg-emerald-500/15 px-2 py-0.5 text-xs font-medium text-emerald-300"
          >
            accepted
          </span>
        ) : null}
        {isDismissed ? (
          <span className="rounded-full border border-slate-400/30 bg-slate-500/15 px-2 py-0.5 text-xs font-medium text-slate-300">
            dismissed
          </span>
        ) : null}
      </div>

      <p className="mt-2 text-sm text-foreground">{finding.summary}</p>

      <p className="mt-1 font-mono text-xs text-muted-foreground">
        {sourceRef} ↔ {targetRef}
      </p>

      {finding.scope_note ? (
        <p className="mt-1 text-xs italic text-muted-foreground">
          {finding.scope_note}
        </p>
      ) : null}

      <div className="mt-3 flex gap-2">
        {isDismissed ? (
          <button
            type="button"
            disabled={isPending}
            onClick={(e) => {
              e.stopPropagation();
              onReopen(finding);
            }}
            className="text-xs font-medium text-cyan-300 hover:underline disabled:opacity-50"
          >
            Reopen
          </button>
        ) : (
          <>
            {/* An accepted card keeps only Dismiss — re-accepting is a no-op,
                and the badge already states the outcome. */}
            {!isAccepted ? (
              <button
                type="button"
                disabled={isPending}
                onClick={(e) => {
                  e.stopPropagation();
                  onAccept(finding);
                }}
                className="rounded-md border border-emerald-400/40 px-2 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-50"
              >
                Accept
              </button>
            ) : null}
            <button
              type="button"
              disabled={isPending}
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(finding);
              }}
              className="rounded-md border border-border/70 px-2 py-1 text-xs font-medium text-foreground hover:bg-accent disabled:opacity-50"
            >
              Dismiss
            </button>
          </>
        )}
      </div>
    </article>
  );
}
