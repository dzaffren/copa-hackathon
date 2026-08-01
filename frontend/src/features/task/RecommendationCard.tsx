import { useState } from "react";
import {
  Bookmark,
  BookmarkCheck,
  ChevronDown,
  ChevronRight,
  Loader2,
  Quote,
  RotateCcw,
} from "lucide-react";

import { InfoBubble } from "@/components/InfoBubble";
import { cn } from "@/lib/utils";
import type { Recommendation } from "@/lib/types";
import { labelStyle, labelText } from "./semanticLabel";
import { RecommendationComments } from "./RecommendationComments";
import { RecommendationRevisions } from "./RecommendationRevisions";

interface Props {
  rec: Recommendation;
  onToggleBookmark: () => void;
  isBookmarkPending: boolean;
  onComment: (text: string) => void;
  isCommentPending: boolean;
  commentError?: string;
  onRewrite: () => void;
  isRewritePending: boolean;
  rewriteError?: string;
}

/** One recommendation: what to do, why, and the clauses it rests on.
 *
 *  Unlike a finding card, this quotes clause TEXT inline rather than only its
 *  number. A finding card is a reference the drafter clicks through from; a
 *  recommendation has to be checkable where it is read, so the evidence travels
 *  with it. The engine copies that text off the finding record, so it cannot
 *  diverge from what it cites.
 *
 *  The `ⓘ` marker beside the title carries the confidence note — what the tool
 *  could not verify from the documents available. It exists because two of the
 *  nine sample recommendations a BNM reviewer scored were well-reasoned and
 *  still partly wrong, on facts no document in the workstream contains.
 */
export function RecommendationCard({
  rec,
  onToggleBookmark,
  isBookmarkPending,
  onComment,
  isCommentPending,
  commentError,
  onRewrite,
  isRewritePending,
  rewriteError,
}: Props) {
  const [citationsOpen, setCitationsOpen] = useState(false);

  return (
    <article
      data-testid="recommendation"
      data-rec-id={rec.id}
      data-bookmarked={rec.bookmarked}
      className={cn(
        "rounded-lg border p-3",
        rec.bookmarked
          ? "border-primary/40 bg-primary/5"
          : "border-border/60 bg-card",
      )}
    >
      <div className="flex items-start gap-2">
        <h3 className="min-w-0 flex-1 text-sm font-semibold leading-snug">
          {rec.title}
        </h3>

        {/* The confidence marker reads BEFORE the bookmark: she takes in what
            the tool could not verify, then decides whether to carry it forward.
            "Nothing unverified." is the engine's honest answer when there is no
            caveat to give, so it carries no marker — an `ⓘ` that reveals only
            "nothing to report" trains the drafter to stop pressing the ones that
            matter. */}
        {rec.confidence_note &&
          !/^nothing unverified\.?$/i.test(rec.confidence_note.trim()) && (
            <InfoBubble label="What this recommendation could not verify">
              {rec.confidence_note}
            </InfoBubble>
          )}

        {/* Rightmost, and last in the tab order: the decision comes after the
            disclosure it depends on. */}
        <button
          type="button"
          data-testid="bookmark-toggle"
          aria-pressed={rec.bookmarked}
          aria-label={
            rec.bookmarked ? "Remove bookmark" : "Bookmark this recommendation"
          }
          disabled={isBookmarkPending}
          onClick={onToggleBookmark}
          className={cn(
            "shrink-0 rounded-full p-0.5 transition focus:outline-none focus-visible:ring-1 focus-visible:ring-primary/50",
            rec.bookmarked
              ? "text-primary hover:text-primary/80"
              : "text-muted-foreground hover:bg-accent hover:text-foreground",
            isBookmarkPending && "opacity-50",
          )}
        >
          {rec.bookmarked ? (
            <BookmarkCheck className="h-4 w-4" />
          ) : (
            <Bookmark className="h-4 w-4" />
          )}
        </button>
      </div>

      {rec.dimensions.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {rec.dimensions.map((dimension) => (
            <span
              key={dimension}
              data-testid="rec-dimension"
              className="rounded bg-accent px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground"
            >
              {dimension}
            </span>
          ))}
        </div>
      )}

      {rec.rationale && <Rationale text={rec.rationale} />}

      {rec.action && (
        <div className="mt-2 rounded-md bg-muted/50 p-2">
          <div className="mb-0.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Action for BNM
          </div>
          <p className="text-xs leading-relaxed">{rec.action}</p>
        </div>
      )}

      <button
        type="button"
        data-testid="citations-toggle"
        aria-expanded={citationsOpen}
        onClick={() => setCitationsOpen((wasOpen) => !wasOpen)}
        className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80"
      >
        {citationsOpen ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        {rec.evidence.length} clause
        {rec.evidence.length === 1 ? "" : "s"} cited
      </button>

      {citationsOpen && (
        <div data-testid="citations" className="mt-2 space-y-2">
          {rec.evidence.map((item) => {
            const style = labelStyle(item.label ?? "aligns-with");
            return (
              <div
                key={item.finding_id}
                data-testid="citation"
                data-finding-id={item.finding_id}
                className="rounded-md border border-border/50 bg-muted/30 p-2"
              >
                <div className="mb-1 flex flex-wrap items-center gap-1.5">
                  {item.label && (
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider",
                        style.pill,
                      )}
                    >
                      {labelText(item.label, item.sentiment)}
                    </span>
                  )}
                  <span className="text-[10px] text-muted-foreground">
                    {item.left.title ?? item.left.id} ↔{" "}
                    {item.right.title ?? item.right.id}
                  </span>
                </div>

                {/* Verbatim, with its clause number. This is the citation the
                    product rule is about — never a paraphrase. */}
                {item.source_clause_number && (
                  <Clause
                    document={item.left.title ?? item.left.id}
                    number={item.source_clause_number}
                    text={item.source_clause_text}
                  />
                )}
                {item.target_clause_number && (
                  <Clause
                    document={item.right.title ?? item.right.id}
                    number={item.target_clause_number}
                    text={item.target_clause_text}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}
      <RecommendationRevisions revisions={rec.revisions} />

      <RecommendationComments
        rec={rec}
        onComment={onComment}
        isCommentPending={isCommentPending}
        commentError={commentError}
      />

      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          data-testid="rewrite"
          disabled={isRewritePending}
          onClick={onRewrite}
          className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80 disabled:opacity-50"
        >
          {isRewritePending ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <RotateCcw className="h-3 w-3" />
          )}
          Rewrite
        </button>
      </div>

      {rewriteError && (
        <p className="mt-1 text-[11px] text-destructive">{rewriteError}</p>
      )}
    </article>
  );
}

/** The rationale, rendered as the bullet list the engine asks the model for.
 *
 *  Markdown-ish by contract, not by parser: the prompt requires one `- ` bullet
 *  per line, so lines are split and the marker stripped. Rendering it as a plain
 *  paragraph instead would show the drafter literal "- " prefixes.
 *
 *  Falls back to a paragraph when nothing looks like a bullet — an older
 *  committed set (or a model that ignored the instruction) still reads correctly
 *  rather than collapsing into one run-on line item. */
function Rationale({ text }: { text: string }) {
  const bullets = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => /^[-*•]\s+/.test(line))
    .map((line) => line.replace(/^[-*•]\s+/, ""));

  if (bullets.length === 0) {
    return (
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
        {text}
      </p>
    );
  }

  return (
    <ul
      data-testid="rec-rationale"
      className="mt-2 space-y-1 text-xs leading-relaxed text-muted-foreground"
    >
      {bullets.map((bullet, index) => (
        <li key={index} className="flex gap-1.5">
          <span aria-hidden="true" className="text-muted-foreground/60">
            ·
          </span>
          <span className="min-w-0">{bullet}</span>
        </li>
      ))}
    </ul>
  );
}

function Clause({
  document,
  number,
  text,
}: {
  document: string;
  number: string;
  text: string | null;
}) {
  return (
    <div className="mt-1 border-l-2 border-primary/30 pl-2">
      <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground">
        <Quote className="h-2.5 w-2.5" />
        {document} · {number}
      </div>
      {text && (
        <p className="mt-0.5 text-[11px] leading-relaxed text-foreground/80">
          {text}
        </p>
      )}
    </div>
  );
}
