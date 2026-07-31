import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchReview, setReviewState, HttpError } from "@/lib/api";
import { labelSeverityRank } from "@/lib/labels";
import type { ReviewFinding, ReviewResponse, ReviewState } from "@/lib/types";
import { ClausePane } from "./ClausePane";
import { FindingCard } from "./FindingCard";

/** Dismissed findings sink to the bottom; the rest sort by attention order
 *  (conflicts-with → differs-on → silent-on → goes-beyond → aligns-with), as
 *  every finding list in the app does. A view concern only — the engine never
 *  reorders the findings file. */
function forDisplay(findings: ReviewFinding[]): ReviewFinding[] {
  return [...findings].sort((a, b) => {
    const aOut = a.review_state === "dismissed" ? 1 : 0;
    const bOut = b.review_state === "dismissed" ? 1 : 0;
    if (aOut !== bOut) return aOut - bOut;
    return labelSeverityRank(a.label) - labelSeverityRank(b.label);
  });
}

export function ReviewLinkagesPage() {
  const { workstreamId = "", edgeId = "" } = useParams();
  const [searchParams] = useSearchParams();
  // The Pairwise Findings box shows one card per finding, so its Review action
  // names the finding to open on. Sent to the engine too, which validates it —
  // an unknown id fails loudly rather than silently showing the wrong finding.
  const nominatedId = searchParams.get("finding");
  const queryClient = useQueryClient();
  const queryKey = ["review", workstreamId, edgeId];

  const { data, isLoading, error } = useQuery<ReviewResponse>({
    queryKey,
    queryFn: () => fetchReview(workstreamId, edgeId, nominatedId ?? undefined),
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
  //
  // A nominated finding wins over the default, but NOT over the drafter's own
  // click — once she has selected something here, the URL no longer overrides
  // her. It is also allowed to be dismissed: arriving from a deep link at a
  // dismissed finding should show it, not silently jump elsewhere.
  const active = useMemo(() => {
    const selectable = ordered.filter((f) => f.review_state !== "dismissed");
    if (activeId === null && data?.active_finding_id) {
      const nominated = ordered.find((f) => f.id === data.active_finding_id);
      if (nominated) return nominated;
    }
    return selectable.find((f) => f.id === activeId) ?? selectable[0] ?? null;
  }, [ordered, activeId, data?.active_finding_id]);

  if (isLoading) {
    return <p className="p-6 text-sm text-muted-foreground">Loading review…</p>;
  }

  if (error) {
    const notAnalysed =
      error instanceof HttpError && error.code === "EDGE_NOT_ANALYSED";
    return (
      <div className="p-6">
        <p className="text-sm text-foreground">
          {notAnalysed
            ? "This pair has not been analysed yet. Run Analyze linkages on the workstream graph first."
            : `Could not load this review: ${(error as Error).message}`}
        </p>
        <Link
          to={`/workstreams/${workstreamId}`}
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          Back to the workstream graph
        </Link>
      </div>
    );
  }

  if (!data) return null;

  const { edge, counts } = data;
  const pending = Math.max(
    0,
    counts.total - counts.accepted - counts.dismissed,
  );
  const sourceLit = active?.source_clauses.map((c) => c.clause_number) ?? [];
  const targetLit = active?.target_clauses.map((c) => c.clause_number) ?? [];

  return (
    <div className="flex h-full min-h-0 flex-col gap-4 p-4">
      <header className="glass rounded-xl px-4 py-3">
        <Link
          to={`/workstreams/${workstreamId}`}
          className="text-xs text-primary hover:underline"
        >
          ← Back to graph
        </Link>
        <h1 className="mt-1 text-lg font-semibold text-foreground">
          {edge.source_node.title}{" "}
          <span className="text-muted-foreground">↔</span>{" "}
          {edge.target_node.title}
        </h1>
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
          <span
            data-testid="count-total"
            className="rounded-full bg-accent/60 px-2 py-0.5 font-medium"
          >
            {counts.total} findings
          </span>
          <span
            data-testid="count-accepted"
            className="rounded-full border border-emerald-400/30 bg-emerald-500/15 px-2 py-0.5 font-medium text-emerald-800"
          >
            {counts.accepted} accepted
          </span>
          <span
            data-testid="count-pending"
            className="rounded-full border border-amber-300/30 bg-amber-400/15 px-2 py-0.5 font-medium text-amber-800"
          >
            {pending} pending
          </span>
          <span
            data-testid="count-dismissed"
            className="rounded-full border border-slate-400/30 bg-slate-500/15 px-2 py-0.5 font-medium text-slate-700"
          >
            {counts.dismissed} dismissed
          </span>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[1fr_1fr_20rem]">
        <ClausePane
          side="source"
          title={edge.source_node.title ?? edge.source_node.id}
          subtitle="working draft"
          clauses={data.source_clauses}
          highlighted={sourceLit}
          filterToHighlighted={true}
        />
        <ClausePane
          side="target"
          title={edge.target_node.title ?? edge.target_node.id}
          subtitle={edge.target_node.node_type}
          clauses={data.target_clauses}
          highlighted={targetLit}
          filterToHighlighted={true}
        />

        <aside
          className="min-h-0 space-y-3 overflow-y-auto"
          aria-label="findings"
        >
          {ordered.length === 0 ? (
            <p className="text-sm text-muted-foreground">
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
