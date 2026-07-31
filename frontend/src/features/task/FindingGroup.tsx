import { cn } from "@/lib/utils";
import { labelStyle } from "./semanticLabel";
import { PairwiseFindingCard } from "./PairwiseFindingCard";
import type { PairwiseFinding, ReviewState, SemanticLabel } from "@/lib/types";

interface Props {
  label: SemanticLabel;
  /** Already filtered and sorted by the parent (pending first, judged sunk). */
  findings: PairwiseFinding[];
  onReview: (finding: PairwiseFinding) => void;
  onSetState: (finding: PairwiseFinding, state: ReviewState) => void;
  isPending: (findingId: string) => boolean;
  errorFor: (findingId: string) => string | undefined;
}

/** One semantic label's findings.
 *
 *  Always rendered, even at zero — a group that vanished would leave the drafter
 *  unable to tell "no conflicts here" from "conflicts not checked". Every card
 *  renders: no truncation, no "show more", because the counts have to be
 *  trustworthy and the node filter is the tool for narrowing.
 */
export function FindingGroup({
  label,
  findings,
  onReview,
  onSetState,
  isPending,
  errorFor,
}: Props) {
  const total = findings.length;
  const pending = findings.filter((f) => f.review_state === "pending").length;
  const style = labelStyle(label);

  return (
    <section
      data-testid="finding-group"
      data-label={label}
      className="space-y-2"
    >
      <header className="flex flex-wrap items-center gap-2">
        <span
          className={cn(
            "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
            style.pill,
          )}
        >
          {label}
        </span>
        <span className="text-[11px] text-muted-foreground">
          <span data-testid="group-total">{total}</span>
          {total > 0 && (
            <>
              {" · "}
              <span data-testid="group-pending">{pending}</span> pending
            </>
          )}
        </span>
      </header>

      {total === 0 ? (
        <p
          data-testid="group-empty"
          className="rounded-lg border border-dashed border-border/60 px-3 py-2 text-xs italic text-muted-foreground"
        >
          None found.
        </p>
      ) : (
        <div className="space-y-2">
          {findings.map((f) => (
            <PairwiseFindingCard
              key={f.id}
              finding={f}
              onReview={() => onReview(f)}
              onSetState={(state) => onSetState(f, state)}
              isPending={isPending(f.id)}
              errorMessage={errorFor(f.id)}
            />
          ))}
        </div>
      )}
    </section>
  );
}
