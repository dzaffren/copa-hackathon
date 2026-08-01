import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  addRecommendationComment,
  fetchRecommendations,
  generateRecommendations,
  rewriteRecommendation,
  setRecommendationBookmark,
  HttpError,
} from "@/lib/api";
import type { Recommendation, RecommendationsResponse } from "@/lib/types";
import { GuardrailsPanel } from "./GuardrailsPanel";
import { NotYetReflectedSection } from "./NotYetReflectedSection";
import { RecommendationCard } from "./RecommendationCard";

interface Props {
  workstreamId: string;
  nodeId: string;
}

/** The task screen's Recommendations card — what replaced the Source card.
 *
 *  Turns the findings the drafter has ACCEPTED into written recommendations, on
 *  the dimensions she recorded herself in the draft's Policy requirement field.
 *  Nothing generates on load: it costs a model call, and she chooses when her
 *  triage is complete enough to be worth synthesising.
 *
 *  Three empty states, and they are different questions with different answers —
 *  no dimensions (go set them), nothing accepted (go triage), nothing generated
 *  (press Generate). Collapsing them into one message would leave a drafter
 *  looking at a dead button with no idea which thing was missing.
 */
export function RecommendationsCard({ workstreamId, nodeId }: Props) {
  const queryClient = useQueryClient();
  const queryKey = ["recommendations", workstreamId, nodeId];
  const [bookmarkError, setBookmarkError] = useState<string | null>(null);
  // One message for comment and rewrite failures: only one of them can be in
  // flight on a card at a time, and two separate banners would be noise.
  const [cardError, setCardError] = useState<string | null>(null);

  const query = useQuery({
    queryKey,
    queryFn: () => fetchRecommendations(workstreamId, nodeId),
  });

  const generate = useMutation({
    mutationFn: () => generateRecommendations(workstreamId, nodeId),
    // Not optimistic, deliberately: the content is unknown until it returns, and
    // guessing at it would show the drafter text the engine never wrote.
    onSuccess: (fresh: RecommendationsResponse) => {
      queryClient.setQueryData<RecommendationsResponse>(queryKey, fresh);
    },
  });

  // Optimistic, unlike generate and rewrite: the outcome of a bookmark is fully
  // known client-side (one boolean), so showing it immediately is honest. It also
  // makes a triage pass over eight cards feel responsive rather than laggy.
  // Follows PairwiseFindingsCard's snapshot-and-rollback shape.
  const bookmark = useMutation({
    mutationFn: (vars: { rec: Recommendation; bookmarked: boolean }) =>
      setRecommendationBookmark(
        workstreamId,
        nodeId,
        vars.rec.id,
        vars.bookmarked,
      ),
    onMutate: async (vars) => {
      setBookmarkError(null);
      await queryClient.cancelQueries({ queryKey });
      const previous =
        queryClient.getQueryData<RecommendationsResponse>(queryKey);
      queryClient.setQueryData<RecommendationsResponse>(queryKey, (old) =>
        old
          ? {
              ...old,
              recommendations: old.recommendations.map((rec) =>
                rec.id === vars.rec.id
                  ? { ...rec, bookmarked: vars.bookmarked }
                  : rec,
              ),
              counts: {
                ...old.counts,
                bookmarked:
                  old.counts.bookmarked + (vars.bookmarked ? 1 : -1),
              },
            }
          : old,
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      setBookmarkError("Could not save that bookmark. Try again.");
    },
  });

  // NEITHER of these is optimistic, unlike bookmarking. A comment's stored form
  // carries a server timestamp and a resolved author; a rewrite's content is
  // unknown until it returns. Guessing either would show the drafter text the
  // server never wrote.
  const comment = useMutation({
    mutationFn: (vars: { rec: Recommendation; text: string }) =>
      addRecommendationComment(workstreamId, nodeId, vars.rec.id, vars.text),
    onMutate: () => setCardError(null),
    onSuccess: (updated) => patchCard(updated),
    onError: () =>
      setCardError("Could not save that comment. Try again."),
  });

  const rewrite = useMutation({
    mutationFn: (rec: Recommendation) =>
      rewriteRecommendation(workstreamId, nodeId, rec.id),
    onMutate: () => setCardError(null),
    onSuccess: (updated) => patchCard(updated),
    onError: () =>
      setCardError("The rewrite could not be completed. Try again."),
  });

  /** Replace one card in the cached set, leaving every other card alone — a
   *  rewrite touches exactly one recommendation, and refetching the whole set
   *  would discard nothing but would cost a round trip to learn that. */
  function patchCard(updated: Recommendation) {
    queryClient.setQueryData<RecommendationsResponse>(queryKey, (old) =>
      old
        ? {
            ...old,
            recommendations: old.recommendations.map((rec) =>
              rec.id === updated.id ? updated : rec,
            ),
          }
        : old,
    );
  }

  const data = query.data;
  const hasDimensions = (data?.dimensions.length ?? 0) > 0;
  const hasAccepted = (data?.accepted_count ?? 0) > 0;
  const cards = data?.recommendations ?? [];

  // Bookmarked first, otherwise stored order. A view concern, computed here, so
  // marking one reorders the list without a refetch.
  const ordered = [...cards].sort(
    (a, b) => Number(b.bookmarked) - Number(a.bookmarked),
  );

  function generateError(): string | null {
    if (!generate.isError) return null;
    const err = generate.error;
    const code = err instanceof HttpError ? err.code : "INTERNAL_ERROR";
    if (code === "NO_POLICY_REQUIREMENTS" || code === "NO_ACCEPTED_FINDINGS") {
      return err instanceof HttpError ? err.message : null;
    }
    return "We could not generate recommendations. Try again.";
  }

  return (
    <Card
      data-testid="recommendations-card"
      className="glass flex max-h-[42rem] min-h-[18rem] flex-col overflow-hidden"
    >
      <div className="shrink-0 border-b border-border/60 px-4 py-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold">Recommendations</h2>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              What the draft should say, from the findings you accepted
            </p>
          </div>
          <Button
            size="sm"
            data-testid="generate"
            disabled={!hasDimensions || !hasAccepted || generate.isPending}
            onClick={() => generate.mutate()}
          >
            {generate.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            {cards.length > 0 ? "Regenerate" : "Generate"}
          </Button>
        </div>

        <div className="mt-2">
          <GuardrailsPanel workstreamId={workstreamId} />
        </div>

        {data && hasDimensions && hasAccepted && (
          <p className="mt-2 text-[11px] text-muted-foreground">
            {generate.isPending
              ? `Working from ${data.accepted_count} accepted findings across ${data.dimensions.length} dimensions…`
              : `${data.accepted_count} accepted findings · ${data.dimensions.length} dimensions`}
          </p>
        )}
      </div>

      {query.isPending && (
        <div
          role="status"
          className="flex items-center gap-2 p-6 text-sm text-muted-foreground"
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading recommendations…
        </div>
      )}

      {query.isError && (
        <p className="p-6 text-sm text-muted-foreground">
          We could not load the recommendations for this task.
        </p>
      )}

      {data && (
        <>
          {/* Ordered by what blocks first: without dimensions there is nothing to
              reason over, so that message wins even if nothing is accepted either. */}
          {!hasDimensions ? (
            <div data-testid="no-dimensions" className="p-6">
              <p className="text-sm text-muted-foreground">
                No policy requirements set. Recommendations are formulated on
                them, so set them first.
              </p>
              <Link
                to={`/workstreams/${workstreamId}?node=${encodeURIComponent(nodeId)}`}
                className="mt-3 inline-block text-sm font-semibold text-primary hover:text-primary/80"
              >
                Set policy requirements →
              </Link>
            </div>
          ) : !hasAccepted ? (
            <p
              data-testid="no-accepted"
              className="p-6 text-sm text-muted-foreground"
            >
              Accept findings in the Pairwise findings box first, then generate.
            </p>
          ) : cards.length === 0 ? (
            <p
              data-testid="not-generated"
              className="p-6 text-sm text-muted-foreground"
            >
              No recommendations yet. Generate them from your{" "}
              {data.accepted_count} accepted findings.
            </p>
          ) : (
            <div
              data-testid="recommendations-scroll"
              className="flex-1 space-y-2 overflow-y-auto p-4"
            >
              {ordered.map((rec) => (
                <RecommendationCard
                  key={rec.id}
                  rec={rec}
                  onToggleBookmark={() =>
                    bookmark.mutate({ rec, bookmarked: !rec.bookmarked })
                  }
                  isBookmarkPending={
                    bookmark.isPending &&
                    bookmark.variables?.rec.id === rec.id
                  }
                  onComment={(text) => comment.mutate({ rec, text })}
                  isCommentPending={
                    comment.isPending && comment.variables?.rec.id === rec.id
                  }
                  commentError={
                    comment.isError && comment.variables?.rec.id === rec.id
                      ? (cardError ?? undefined)
                      : undefined
                  }
                  onRewrite={() => rewrite.mutate(rec)}
                  // Only THIS card's actions disable while it rewrites; every
                  // other card stays interactive.
                  isRewritePending={
                    rewrite.isPending && rewrite.variables?.id === rec.id
                  }
                  rewriteError={
                    rewrite.isError && rewrite.variables?.id === rec.id
                      ? (cardError ?? undefined)
                      : undefined
                  }
                />
              ))}
            </div>
          )}

          {generateError() && (
            <p className="px-4 pb-3 text-[11px] text-destructive">
              {generateError()}
            </p>
          )}

          {bookmarkError && (
            <p className="px-4 pb-3 text-[11px] text-destructive">
              {bookmarkError}
            </p>
          )}

          {hasDimensions && hasAccepted && cards.length > 0 && (
            <NotYetReflectedSection
              workstreamId={workstreamId}
              findings={data.not_yet_reflected}
              acceptedCount={data.accepted_count}
            />
          )}
        </>
      )}
    </Card>
  );
}
