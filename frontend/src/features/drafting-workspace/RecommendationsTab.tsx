import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bookmark,
  ChevronDown,
  ChevronRight,
  Loader2,
  Quote,
} from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { fetchRecommendations, setRecommendationBookmark } from "@/lib/api";
import type { Recommendation, RecommendationsResponse } from "@/lib/types";

interface Props {
  workstreamId: string;
  nodeId: string;
}

/** The recommendations the drafter is taking forward, beside her draft.
 *
 *  **A filter, not a second endpoint.** It reads the same
 *  `["recommendations", ws, node]` query the task screen populates and shows only
 *  the bookmarked ones — so the two surfaces cannot disagree about what is
 *  bookmarked, and unbookmarking here is reflected there without a bespoke sync.
 *
 *  **Nothing here writes to the draft.** No insert, no "Draft this", no hand-off.
 *  Everything that reaches the page arrives through the Copilot conversation,
 *  where the drafter reviews it. A recommendation here is something she reads and
 *  then asks the Copilot for in her own words.
 */
export function RecommendationsTab({ workstreamId, nodeId }: Props) {
  const queryClient = useQueryClient();
  const queryKey = ["recommendations", workstreamId, nodeId];
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey,
    queryFn: () => fetchRecommendations(workstreamId, nodeId),
  });

  const unbookmark = useMutation({
    mutationFn: (rec: Recommendation) =>
      setRecommendationBookmark(workstreamId, nodeId, rec.id, false),
    onMutate: async (rec) => {
      setError(null);
      await queryClient.cancelQueries({ queryKey });
      const previous =
        queryClient.getQueryData<RecommendationsResponse>(queryKey);
      queryClient.setQueryData<RecommendationsResponse>(queryKey, (old) =>
        old
          ? {
              ...old,
              recommendations: old.recommendations.map((r) =>
                r.id === rec.id ? { ...r, bookmarked: false } : r,
              ),
              counts: {
                ...old.counts,
                bookmarked: Math.max(0, old.counts.bookmarked - 1),
              },
            }
          : old,
      );
      return { previous };
    },
    onError: (_err, _rec, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      setError("Could not remove that bookmark. Try again.");
    },
  });

  if (query.isPending) {
    return (
      <div
        role="status"
        className="flex items-center gap-2 p-4 text-sm text-muted-foreground"
      >
        <Loader2 className="h-4 w-4 animate-spin" /> Loading recommendations…
      </div>
    );
  }

  if (query.isError || !query.data) {
    return (
      <p className="p-4 text-sm text-muted-foreground">
        We could not load the recommendations for this draft.
      </p>
    );
  }

  const bookmarked = query.data.recommendations.filter((r) => r.bookmarked);

  // Two different empty states, because they need two different answers: nothing
  // generated at all sends her to Generate; nothing bookmarked sends her to pick.
  if (query.data.generated_at === null) {
    return (
      <p
        data-testid="tab-not-generated"
        className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground"
      >
        No recommendations yet. Generate them in the Recommendations card on the
        task page, then bookmark the ones worth taking forward.
      </p>
    );
  }

  if (bookmarked.length === 0) {
    return (
      <p
        data-testid="tab-none-bookmarked"
        className="rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground"
      >
        Nothing bookmarked yet. Bookmark a recommendation on the task page and
        it appears here, beside the draft you are writing from it.
      </p>
    );
  }

  return (
    <div data-testid="recommendations-tab" className="space-y-2">
      {error && <p className="text-[11px] text-destructive">{error}</p>}

      {bookmarked.map((rec) => (
        <DraftRecommendationCard
          key={rec.id}
          rec={rec}
          onUnbookmark={() => unbookmark.mutate(rec)}
          isPending={
            unbookmark.isPending && unbookmark.variables?.id === rec.id
          }
        />
      ))}

      {/* The same figure the task screen reports, measured against every
          generated recommendation rather than the bookmarked subset — so the
          number means the same thing on both surfaces. */}
      <p
        data-testid="tab-not-yet-reflected"
        data-count={query.data.counts.not_yet_reflected}
        className="pb-2 pt-1 text-[11px] text-muted-foreground"
      >
        {query.data.counts.not_yet_reflected === 0
          ? "Every accepted finding is reflected in a recommendation."
          : `${query.data.counts.not_yet_reflected} of ${query.data.accepted_count} accepted findings are not yet reflected.`}
      </p>
    </div>
  );
}

function DraftRecommendationCard({
  rec,
  onUnbookmark,
  isPending,
}: {
  rec: Recommendation;
  onUnbookmark: () => void;
  isPending: boolean;
}) {
  const [citationsOpen, setCitationsOpen] = useState(false);

  return (
    <article
      data-testid="draft-recommendation"
      data-rec-id={rec.id}
      className="rounded-lg border border-primary/40 bg-primary/5 p-3"
    >
      <div className="flex items-start gap-2">
        <h3 className="min-w-0 flex-1 text-sm font-semibold leading-snug">
          {rec.title}
        </h3>
        <button
          type="button"
          data-testid="unbookmark"
          aria-label="Remove bookmark"
          disabled={isPending}
          onClick={onUnbookmark}
          className={cn(
            "shrink-0 rounded-full p-0.5 text-primary transition hover:text-primary/80 focus:outline-none focus-visible:ring-1 focus-visible:ring-primary/50",
            isPending && "opacity-50",
          )}
        >
          <Bookmark className="h-4 w-4 fill-current" />
        </button>
      </div>

      {rec.action && (
        <div className="mt-2 rounded-md bg-card/70 p-2">
          <div className="mb-0.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Action for BNM
          </div>
          <p className="text-xs leading-relaxed">{rec.action}</p>
        </div>
      )}

      <button
        type="button"
        data-testid="tab-citations-toggle"
        aria-expanded={citationsOpen}
        onClick={() => setCitationsOpen((wasOpen) => !wasOpen)}
        className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80"
      >
        {citationsOpen ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        {rec.evidence.length} clause{rec.evidence.length === 1 ? "" : "s"} cited
      </button>

      {citationsOpen && (
        <div data-testid="tab-citations" className="mt-2 space-y-1.5">
          {rec.evidence.map((item) => (
            <div
              key={item.finding_id}
              className="rounded-md border border-border/50 bg-card/70 p-2"
            >
              {item.source_clause_number && (
                <div className="border-l-2 border-primary/30 pl-2">
                  <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground">
                    <Quote className="h-2.5 w-2.5" />
                    {item.left.title ?? item.left.id} ·{" "}
                    {item.source_clause_number}
                  </div>
                  {item.source_clause_text && (
                    <p className="mt-0.5 text-[11px] leading-relaxed text-foreground/80">
                      {item.source_clause_text}
                    </p>
                  )}
                </div>
              )}
              {item.target_clause_number && (
                <div className="mt-1 border-l-2 border-primary/30 pl-2">
                  <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground">
                    <Quote className="h-2.5 w-2.5" />
                    {item.right.title ?? item.right.id} ·{" "}
                    {item.target_clause_number}
                  </div>
                  {item.target_clause_text && (
                    <p className="mt-0.5 text-[11px] leading-relaxed text-foreground/80">
                      {item.target_clause_text}
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
