import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchReview, setReviewState, HttpError } from "@/lib/api";
import type { ReviewFinding, ReviewResponse, ReviewState } from "@/lib/types";
import { ClausePane } from "./ClausePane";
import { FindingCard } from "./FindingCard";

/** Dismissed findings sink to the bottom; everything else holds file order.
 *  A view concern only — the engine never reorders the findings file. */
function forDisplay(findings: ReviewFinding[]): ReviewFinding[] {
  return [...findings].sort((a, b) => {
    const aOut = a.review_state === "dismissed" ? 1 : 0;
    const bOut = b.review_state === "dismissed" ? 1 : 0;
    return aOut - bOut;
  });
}

export function ReviewLinkagesPage() {
  const { workstreamId = "", edgeId = "" } = useParams();
  const queryClient = useQueryClient();
  const queryKey = ["review", workstreamId, edgeId];

  const { data, isLoading, error } = useQuery<ReviewResponse>({
    queryKey,
    queryFn: () => fetchReview(workstreamId, edgeId),
  });

  const [activeId, setActiveId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (vars: { findingId: string; state: ReviewState }) =>
      setReviewState(workstreamId, edgeId, vars.findingId, vars.state),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  });

  const ordered = useMemo(() => forDisplay(data?.findings ?? []), [data]);

  // The first selectable card is active on load, and stays active across a
  // refetch. Falls back when the active card was just dismissed (dismissed
  // cards are not selectable, so leaving it active would strand the panes).
  const active = useMemo(() => {
    const selectable = ordered.filter((f) => f.review_state !== "dismissed");
    return selectable.find((f) => f.id === activeId) ?? selectable[0] ?? null;
  }, [ordered, activeId]);

  if (isLoading) {
    return <p className="p-6 text-sm text-gray-500">Loading review…</p>;
  }

  if (error) {
    const notAnalysed =
      error instanceof HttpError && error.code === "EDGE_NOT_ANALYSED";
    return (
      <div className="p-6">
        <p className="text-sm text-gray-700">
          {notAnalysed
            ? "This pair has not been analysed yet. Run Analyze linkages on the workstream graph first."
            : `Could not load this review: ${(error as Error).message}`}
        </p>
        <Link
          to={`/workstreams/${workstreamId}`}
          className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
        >
          Back to the workstream graph
        </Link>
      </div>
    );
  }

  if (!data) return null;

  const { edge, counts } = data;
  const sourceLit = active?.source_clauses.map((c) => c.clause_number) ?? [];
  const targetLit = active?.target_clauses.map((c) => c.clause_number) ?? [];

  return (
    <div className="flex h-full min-h-0 flex-col gap-4 p-4">
      <header>
        <Link
          to={`/workstreams/${workstreamId}`}
          className="text-xs text-indigo-600 hover:underline"
        >
          ← {workstreamId}
        </Link>
        <h1 className="mt-1 text-lg font-semibold text-gray-900">
          {edge.source_node.title} ↔ {edge.target_node.title}
        </h1>
        <p className="mt-0.5 text-sm text-gray-500">
          <span data-testid="count-total">{counts.total} findings</span>
          {" · "}
          <span data-testid="count-accepted">{counts.accepted} accepted</span>
          {" · "}
          <span data-testid="count-dismissed">
            {counts.dismissed} dismissed
          </span>
        </p>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr_20rem]">
        <ClausePane
          side="source"
          title={edge.source_node.title ?? edge.source_node.id}
          subtitle="working draft"
          clauses={data.source_clauses}
          highlighted={sourceLit}
        />
        <ClausePane
          side="target"
          title={edge.target_node.title ?? edge.target_node.id}
          subtitle={edge.target_node.node_type}
          clauses={data.target_clauses}
          highlighted={targetLit}
        />

        <aside
          className="min-h-0 space-y-3 overflow-y-auto"
          aria-label="findings"
        >
          {ordered.length === 0 ? (
            <p className="text-sm text-gray-500">
              No linkages found on this pair.
            </p>
          ) : (
            ordered.map((finding) => (
              <FindingCard
                key={finding.id}
                finding={finding}
                isActive={active?.id === finding.id}
                isPending={mutation.isPending}
                onSelect={(f) => setActiveId(f.id)}
                onAccept={(f) =>
                  mutation.mutate({ findingId: f.id, state: "accepted" })
                }
                onDismiss={(f) =>
                  mutation.mutate({ findingId: f.id, state: "dismissed" })
                }
                onReopen={(f) =>
                  mutation.mutate({ findingId: f.id, state: "pending" })
                }
              />
            ))
          )}
        </aside>
      </div>
    </div>
  );
}
