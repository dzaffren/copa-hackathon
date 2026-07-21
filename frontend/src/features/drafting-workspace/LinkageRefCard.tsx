import type { LinkageCard } from "@/lib/types";
import { labelStyle, labelText } from "@/features/task/semanticLabel";

interface LinkageRefCardProps {
  card: LinkageCard;
  /** Peer cards name both endpoints ("HKMA ↔ BCBS"); reviewed cards name only
   *  the anchor, since the other side is always the draft you are looking at. */
  showBothEndpoints?: boolean;
  isActive?: boolean;
  onSelect?: (card: LinkageCard) => void;
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
  showBothEndpoints = false,
  isActive = false,
  onSelect,
}: LinkageRefCardProps) {
  const style = labelStyle(card.label);
  const clauseRef = card.source_clause_number ?? card.target_clause_number;

  return (
    <article
      data-testid="linkage-ref-card"
      data-label={card.label}
      data-active={isActive || undefined}
      aria-current={isActive}
      onClick={onSelect ? () => onSelect(card) : undefined}
      className={[
        "rounded-lg border p-3 text-left transition",
        style.card,
        onSelect ? "cursor-pointer hover:border-cyan-400/40" : "",
        isActive ? "ring-2 ring-cyan-400/70" : "",
      ].join(" ")}
    >
      <div className="flex flex-wrap items-center gap-1.5">
        <span
          className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${style.pill}`}
        >
          {labelText(card.label, card.sentiment)}
        </span>
        {showBothEndpoints ? (
          <span className="text-[11px] text-muted-foreground">
            {card.left.title} ↔ {card.right.title}
          </span>
        ) : (
          <span className="text-[11px] text-muted-foreground">
            {card.right.title}
          </span>
        )}
      </div>

      <p className="mt-1.5 text-sm leading-snug">{card.summary}</p>

      {clauseRef && (
        <p className="mt-1 font-mono text-[11px] text-muted-foreground">
          {clauseRef}
          {card.source_clause_number && card.target_clause_number
            ? ` ↔ ${card.target_clause_number}`
            : // A goes-beyond cites nothing on the far side; say so rather than
              // leaving a dangling arrow.
              card.label === "goes-beyond" || card.label === "silent-on"
              ? " ↔ (silent)"
              : ""}
        </p>
      )}
    </article>
  );
}
