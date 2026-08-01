import { useEffect, useState } from "react";
import { Loader2, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Recommendation } from "@/lib/types";

interface Props {
  rec: Recommendation;
  onComment: (text: string) => void;
  isCommentPending: boolean;
  commentError?: string;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatAt(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/** Why a recommendation misses, in the drafter's own words.
 *
 *  A note, not a chat thread — discussion of a draft belongs in the Copilot. Each
 *  comment informs this card's rewrite and is available to the Copilot; none of
 *  them is promoted into the guardrails, because a model re-wording her situated
 *  correction into a standing rule would be authoring the rules it then follows.
 */
export function RecommendationComments({
  rec,
  onComment,
  isCommentPending,
  commentError,
}: Props) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);

  // Close and clear only once the comment has actually LANDED on the card. The
  // parent appends it on success, so a thread that now contains what she
  // submitted is the confirmation — and a failure leaves the box exactly as it
  // was, error and typed text together.
  useEffect(() => {
    if (
      submitted !== null &&
      rec.comments.some((comment) => comment.text === submitted)
    ) {
      setSubmitted(null);
      setText("");
      setOpen(false);
    }
  }, [rec.comments, submitted]);

  const canSubmit = text.trim().length > 0 && !isCommentPending;

  return (
    <div className="mt-2">
      {rec.comments.length > 0 && (
        <ul data-testid="comment-thread" className="mb-2 space-y-1.5">
          {rec.comments.map((comment, index) => (
            <li
              // Index is safe as a key: comments are append-only and never
              // reordered or removed, so an index cannot point at a different
              // comment later. Two comments can legitimately share a timestamp.
              key={index}
              data-testid="comment"
              className="rounded-md bg-muted/50 p-2"
            >
              <div className="mb-0.5 flex items-center gap-1.5 text-[10px] font-semibold text-muted-foreground">
                <span className="grid h-4 w-4 place-items-center rounded-full bg-accent text-[8px]">
                  {initials(comment.author.name)}
                </span>
                {comment.author.name} · {formatAt(comment.at)}
              </div>
              <p className="text-[11px] leading-relaxed">{comment.text}</p>
            </li>
          ))}
        </ul>
      )}

      {!open ? (
        <button
          type="button"
          data-testid="comment-open"
          onClick={() => setOpen(true)}
          className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground hover:text-foreground"
        >
          <MessageSquare className="h-3 w-3" />
          Comment
        </button>
      ) : (
        <div>
          <label htmlFor={`comment-${rec.id}`} className="sr-only">
            Why this recommendation misses
          </label>
          <textarea
            id={`comment-${rec.id}`}
            data-testid="comment-input"
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={3}
            placeholder="Why does this miss? What do you know that the documents do not?"
            className="w-full rounded-md border border-border/60 bg-background p-2 text-[11px] leading-relaxed outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
          />

          {commentError && (
            <p className="mt-1 text-[11px] text-destructive">{commentError}</p>
          )}

          <div className="mt-1.5 flex items-center gap-1.5">
            <Button
              size="sm"
              data-testid="comment-submit"
              disabled={!canSubmit}
              // The box stays OPEN and the text stays in it until the effect
              // above sees the comment land. Clearing on click would lose a
              // paragraph she had just typed the moment a request failed — and
              // would leave the error with nowhere to render.
              onClick={() => {
                setSubmitted(text.trim());
                onComment(text.trim());
              }}
            >
              {isCommentPending && <Loader2 className="h-3 w-3 animate-spin" />}
              Submit
            </Button>
            <button
              type="button"
              onClick={() => {
                setText("");
                setOpen(false);
              }}
              className="text-[11px] text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
