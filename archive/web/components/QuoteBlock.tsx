import { VERIFICATION } from "@/lib/labels";
import type { Quote } from "@/lib/types";

/**
 * A verbatim source quote with its verification marker. The marker rendered
 * ALWAYS equals `quote.verification` — this component can never upgrade an
 * illustrative/pending quote to verified (the anti-hallucination guarantee).
 * A pending_extraction quote (text: null) renders a labelled placeholder, never
 * an approximated string.
 */
export function QuoteBlock({ quote }: { quote: Quote }) {
  const v = VERIFICATION[quote.verification];
  const pending =
    quote.verification === "pending_extraction" || quote.text === null;

  return (
    <figure
      className="mt-2"
      data-testid="quote-block"
      data-verification={quote.verification}
    >
      <blockquote
        className={`border-l-2 pl-3 text-sm ${
          pending
            ? "border-slate-300 italic text-slate-400"
            : "border-slate-300 text-slate-700"
        }`}
      >
        {pending
          ? "Source passage pending extraction — not yet confirmed word-for-word."
          : `“${quote.text}”`}
      </blockquote>
      <figcaption
        className={`mt-1 flex items-center gap-1 text-xs ${v.className}`}
      >
        <span aria-hidden>{v.mark}</span>
        <span>
          {quote.clause_number} · {v.label}
        </span>
      </figcaption>
    </figure>
  );
}
