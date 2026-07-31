import { Loader2, Undo2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { LinkageCard } from "@/lib/types";
import { labelStyle, labelText } from "@/features/task/semanticLabel";

interface LinkageRefCardProps {
  card: LinkageCard;
  /** Both endpoints are named by default: cards now arrive from across the
   *  task's whole neighbourhood, so the other side is NOT always the draft and
   *  a single title would leave the drafter unable to tell an HKMA difference
   *  from a RMiT one. */
  showBothEndpoints?: boolean;
  isActive?: boolean;
  onSelect?: (card: LinkageCard) => void;
  /** Withdraw an acceptance (accepted → pending). The Reviewed tab offers this
   *  and nothing else: it holds what was accepted, so accept/dismiss belong to
   *  the Pairwise Findings box and the comparison screen. */
  onWithdraw?: (card: LinkageCard) => void;
  isWithdrawing?: boolean;
  errorMessage?: string;
}

/** One linkage, as a reference into the review reader.
 *
 * Deliberately shows clause NUMBERS and never clause text. The full verbatim
 * quotation lives on the review screen; a card that paraphrased a clause here
 * would be a second, unchecked rendering of it.
 *
 * Reuses the task screen's `semanticLabel` helpers rather than restating the
 * colour map — two palettes drifting apart is a failure this repo has had.
 */
export function LinkageRefCard({
  card,
  showBothEndpoints = true,
  isActive = false,
  onSelect,
  onWithdraw,
  isWithdrawing = false,
  errorMessage,
}: LinkageRefCardProps) {
  const style = labelStyle(card.label);

  return (
    <article
      data-testid="linkage-ref-card"
      data-label={card.label}
      data-finding-id={card.id}
      data-edge-id={card.edge_id}
      data-active={isActive || undefined}
      aria-current={isActive}
      className={[
        "rounded-lg border p-3 text-left transition",
        style.card,
        isActive ? "ring-2 ring-primary/70" : "",
      ].join(" ")}
    >
      <div
        onClick={onSelect ? () => onSelect(card) : undefined}
        className={onSelect ? "cursor-pointer" : undefined}
      >
        <div className="flex flex-wrap items-center gap-1.5">
          <span
            className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${style.pill}`}
          >
            {labelText(card.label, card.sentiment)}
          </span>
          {showBothEndpoints ? (
            <span className="text-[11px] text-muted-foreground">
              {card.left.title ?? card.left.id} ↔{" "}
              {card.right.title ?? card.right.id}
            </span>
          ) : (
            <span className="text-[11px] text-muted-foreground">
              {card.right.title ?? card.right.id}
            </span>
          )}
        </div>

        <p className="mt-1.5 text-sm leading-snug">{card.summary}</p>

        <p className="mt-1 font-mono text-[11px] text-muted-foreground">
          <ClauseRef value={card.source_clause_number} /> ↔{" "}
          <ClauseRef value={card.target_clause_number} />
        </p>
      </div>

      {errorMessage && (
        <p className="mt-1.5 text-[11px] text-red-600">{errorMessage}</p>
      )}

      {onWithdraw && (
        <Button
          size="sm"
          variant="outline"
          className="mt-2"
          disabled={isWithdrawing}
          onClick={() => onWithdraw(card)}
        >
          {isWithdrawing ? <Loader2 className="animate-spin" /> : <Undo2 />}{" "}
          Withdraw
        </Button>
      )}
    </article>
  );
}

/** A clause number, or the honest absence of one. A `silent-on` or
 *  `goes-beyond` finding cites nothing on one side — say so rather than leaving
 *  a dangling arrow or inventing a clause. */
function ClauseRef({ value }: { value: string | null }) {
  if (!value)
    return <span className="not-italic">No matching clause found</span>;
  return <>{value}</>;
}
