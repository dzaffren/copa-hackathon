import { Check, Eye, Loader2, Undo2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { PairwiseFinding, ReviewState } from "@/lib/types";
import { labelStyle, labelText } from "./semanticLabel";

interface Props {
  finding: PairwiseFinding;
  onReview: () => void;
  onSetState: (state: ReviewState) => void;
  isPending: boolean;
  errorMessage?: string;
}

const STATE_BADGE: Record<Exclude<ReviewState, "pending">, string> = {
  accepted: "border border-emerald-400/30 bg-emerald-500/15 text-emerald-800",
  dismissed: "border border-slate-400/30 bg-slate-500/15 text-slate-700",
};

/** One finding in the Pairwise Findings box.
 *
 *  Summary only — clause NUMBERS travel but never clause text, so a card cannot
 *  misquote; the quoted clauses live on the comparison screen behind Review.
 *  Actions stack vertically on the right. Once judged the card mutes and its
 *  action column collapses to Undo, and the parent sinks it to the bottom of its
 *  label group.
 */
export function PairwiseFindingCard({
  finding,
  onReview,
  onSetState,
  isPending,
  errorMessage,
}: Props) {
  const judged = finding.review_state !== "pending";
  const style = labelStyle(finding.label);

  return (
    <article
      data-testid="finding-card"
      data-finding-id={finding.id}
      data-edge-id={finding.edge_id}
      data-review-state={finding.review_state}
      className={cn(
        "flex gap-3 rounded-lg border p-3",
        style.card,
        judged && "opacity-60",
      )}
    >
      <div className="min-w-0 flex-1">
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
              style.pill,
            )}
          >
            {labelText(finding.label, finding.sentiment)}
          </span>
          {judged && (
            <span
              className={cn(
                "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                STATE_BADGE[finding.review_state as "accepted" | "dismissed"],
              )}
            >
              {finding.review_state}
            </span>
          )}
          <span className="text-[11px] text-muted-foreground">
            {finding.left.title ?? finding.left.id}
            {" ↔ "}
            {finding.right.title ?? finding.right.id}
          </span>
        </div>

        <p
          className={cn(
            "text-sm leading-relaxed",
            judged ? "text-muted-foreground" : "text-foreground",
          )}
        >
          {finding.summary}
        </p>

        <p className="mt-1 text-[11px] text-muted-foreground">
          <ClauseRef value={finding.source_clause_number} />
          {" · "}
          <ClauseRef value={finding.target_clause_number} />
        </p>

        {errorMessage && (
          <p className="mt-1 text-[11px] text-red-600">{errorMessage}</p>
        )}
      </div>

      <div className="flex w-24 shrink-0 flex-col gap-1.5">
        {judged ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onSetState("pending")}
            disabled={isPending}
            className="justify-center"
          >
            {isPending ? <Loader2 className="animate-spin" /> : <Undo2 />} Undo
          </Button>
        ) : (
          <>
            {/* The only action that opens the quoted clauses, so it is the one
                the drafter should reach for first — a dark slate against the
                card's pale label tint, where an outline button disappeared. */}
            <Button
              size="sm"
              onClick={onReview}
              className="justify-center bg-[#3F4350] text-white hover:bg-[#4B5060] [&_svg]:text-white"
            >
              <Eye /> Review
            </Button>
            <Button
              size="sm"
              onClick={() => onSetState("accepted")}
              disabled={isPending}
              className="justify-center bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isPending ? <Loader2 className="animate-spin" /> : <Check />}{" "}
              Accept
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onSetState("dismissed")}
              disabled={isPending}
              className="justify-center"
            >
              <X /> Dismiss
            </Button>
          </>
        )}
      </div>
    </article>
  );
}

/** A clause number, or the honest absence of one. A `silent-on` or
 *  `goes-beyond` finding may cite nothing on one side — say so rather than
 *  inventing a clause. */
function ClauseRef({ value }: { value: string | null }) {
  if (!value) return <span className="italic">No matching clause found</span>;
  return <span className="font-medium">{value}</span>;
}
