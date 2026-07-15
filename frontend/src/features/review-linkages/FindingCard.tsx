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
 * repo has already been bitten by.
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
        "rounded-lg border p-3 text-left transition",
        isDismissed
          ? "cursor-default border-gray-200 bg-gray-50 opacity-60"
          : "cursor-pointer " + style.card,
        isActive && !isDismissed ? "ring-2 ring-indigo-400" : "",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${style.pill}`}
        >
          {labelText(finding.label, finding.sentiment)}
        </span>
        {isAccepted ? (
          <span
            data-testid="accepted-badge"
            className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800"
          >
            accepted
          </span>
        ) : null}
        {isDismissed ? (
          <span className="rounded-full bg-gray-200 px-2 py-0.5 text-xs font-medium text-gray-600">
            dismissed
          </span>
        ) : null}
      </div>

      <p className="mt-2 text-sm text-gray-900">{finding.summary}</p>

      <p className="mt-1 font-mono text-xs text-gray-500">
        {sourceRef} ↔ {targetRef}
      </p>

      {finding.scope_note ? (
        <p className="mt-1 text-xs italic text-gray-500">
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
            className="text-xs font-medium text-indigo-600 hover:underline disabled:opacity-50"
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
                className="rounded border border-emerald-300 px-2 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-50 disabled:opacity-50"
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
              className="rounded border border-gray-300 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Dismiss
            </button>
          </>
        )}
      </div>
    </article>
  );
}
