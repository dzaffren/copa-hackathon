import { useState } from "react";
import { Check, Send } from "lucide-react";

/** A question turn in the chat — the intent picker, the leading focus question,
 *  or a clarification round. Options are stacked VERTICALLY (full-width, left
 *  aligned) like Claude Code's choices, not horizontal pills. A free-text
 *  fallback lets the drafter answer in their own words. Once answered, the card
 *  locks and shows the chosen answer. */
export function ClarificationCard({
  prompt,
  options,
  answered,
  onAnswer,
  freeTextPlaceholder = "Or type your own answer…",
}: {
  prompt: string;
  options: string[];
  answered?: string;
  onAnswer: (answer: string) => void;
  freeTextPlaceholder?: string;
}) {
  const [text, setText] = useState("");
  const locked = answered !== undefined;

  return (
    <div
      data-testid="clarification-card"
      className="space-y-2 rounded-xl border border-border/60 bg-card p-3 shadow-sm"
      style={{ animation: "fadeSlideUp 0.4s var(--ease-out-expo) both" }}
    >
      <p className="text-sm leading-snug text-foreground">{prompt}</p>

      <div data-testid="clarification-options" className="flex flex-col gap-1.5">
        {options.map((o) => {
          const chosen = answered === o;
          return (
            <button
              key={o}
              type="button"
              disabled={locked}
              onClick={() => onAnswer(o)}
              className={`flex w-full items-center gap-2 rounded-lg border px-3 py-2 text-left text-sm transition ${
                chosen
                  ? "border-primary/60 bg-primary/10 text-primary"
                  : locked
                    ? "border-border/40 text-muted-foreground opacity-60"
                    : "border-border/60 text-foreground hover:border-primary/60 hover:bg-accent"
              }`}
            >
              {chosen && <Check className="h-3.5 w-3.5 shrink-0 text-primary" />}
              <span className="min-w-0">{o}</span>
            </button>
          );
        })}
      </div>

      {!locked && (
        <form
          className="flex gap-1.5"
          onSubmit={(e) => {
            e.preventDefault();
            const t = text.trim();
            if (!t) return;
            setText("");
            onAnswer(t);
          }}
        >
          <input
            aria-label="Your answer"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={freeTextPlaceholder}
            className="min-w-0 flex-1 rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
          />
          <button
            type="submit"
            aria-label="Send answer"
            className="flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      )}
    </div>
  );
}
