import { useMemo, useState, type UIEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { fetchPairwiseFindings, setReviewState } from "@/lib/api";
import { LABEL_SEVERITY_ORDER, forGroupDisplay } from "@/lib/labels";
import type {
  PairwiseFinding,
  PairwiseFindingsResponse,
  ReviewState,
  SemanticLabel,
} from "@/lib/types";
import { CoverageStrip } from "./CoverageStrip";
import { FindingGroup } from "./FindingGroup";
import { NodeFilterChips } from "./NodeFilterChips";

interface Props {
  workstreamId: string;
  nodeId: string;
}

const DESCRIPTION =
  "Semantic linkages (differs-on, conflicts-with, silent-on, aligns-with, " +
  "goes-beyond) between nodes";

// Two thresholds, not one. Collapsing the coverage strip makes the findings
// viewport taller, which can pull `scrollTop` back under a single threshold and
// re-expand — which grows the strip, shrinks the viewport, and flaps. The gap
// between these two is what breaks that loop.
const COLLAPSE_AT = 24;
const EXPAND_AT = 4;

/** The task screen's Pairwise Findings box.
 *
 *  Draws on the task's whole neighbourhood, so it is populated from the moment
 *  the workstream has been analysed — the draft's content is never a gate. The
 *  server sends every finding in graph order; grouping by label, sinking judged
 *  cards and filtering by node all happen here, which is why accepting a finding
 *  reorders the list without a refetch.
 */
export function PairwiseFindingsCard({ workstreamId, nodeId }: Props) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const queryKey = ["pairwise-findings", workstreamId, nodeId];

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [stripCollapsed, setStripCollapsed] = useState(false);

  const query = useQuery({
    queryKey,
    queryFn: () => fetchPairwiseFindings(workstreamId, nodeId),
  });

  const mutation = useMutation({
    mutationFn: (vars: { finding: PairwiseFinding; state: ReviewState }) =>
      setReviewState(
        workstreamId,
        vars.finding.edge_id,
        vars.finding.id,
        vars.state,
      ),
    // Optimistic: the card mutes and sinks immediately. A review decision is a
    // judgement the drafter already made — waiting on a round trip to reflect it
    // makes a 130-card triage pass feel broken.
    onMutate: async (vars) => {
      setErrors((prev) => {
        const { [vars.finding.id]: _dropped, ...rest } = prev;
        return rest;
      });
      await queryClient.cancelQueries({ queryKey });
      const previous =
        queryClient.getQueryData<PairwiseFindingsResponse>(queryKey);
      queryClient.setQueryData<PairwiseFindingsResponse>(queryKey, (old) =>
        old
          ? {
              ...old,
              findings: old.findings.map((f) =>
                f.id === vars.finding.id
                  ? { ...f, review_state: vars.state }
                  : f,
              ),
            }
          : old,
      );
      return { previous };
    },
    onError: (_err, vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKey, context.previous);
      }
      setErrors((prev) => ({
        ...prev,
        [vars.finding.id]: "Could not save that decision. Try again.",
      }));
    },
    onSuccess: (_data, vars) => {
      // The Reviewed tab and the comparison screen read the same review state.
      // Missing any of these three leaves a surface showing a decision the
      // drafter has already reversed.
      queryClient.invalidateQueries({
        queryKey: ["reviewed-linkages", workstreamId, nodeId],
      });
      queryClient.invalidateQueries({
        queryKey: ["review", workstreamId, vars.finding.edge_id],
      });
    },
  });

  const data = query.data;

  const grouped = useMemo(() => {
    // Seeded from the taxonomy so all five keys exist regardless of content.
    const groups = new Map<SemanticLabel, PairwiseFinding[]>(
      LABEL_SEVERITY_ORDER.map((label) => [label, []]),
    );
    for (const finding of data?.findings ?? []) {
      // An empty selection means "no filter". A finding matches when either of
      // its endpoints is selected — cards come from pairs, not single nodes.
      const visible =
        selected.size === 0 ||
        selected.has(finding.left.id) ||
        selected.has(finding.right.id);
      if (!visible) continue;
      groups.get(finding.label)?.push(finding);
    }
    return groups;
  }, [data, selected]);

  function toggleNode(nodeIdToToggle: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(nodeIdToToggle)) next.delete(nodeIdToToggle);
      else next.add(nodeIdToToggle);
      return next;
    });
  }

  function handleFindingsScroll(event: UIEvent<HTMLDivElement>) {
    const top = event.currentTarget.scrollTop;
    setStripCollapsed((wasCollapsed) =>
      wasCollapsed ? top > EXPAND_AT : top > COLLAPSE_AT,
    );
  }

  function handleReview(finding: PairwiseFinding) {
    navigate(
      `/workstreams/${workstreamId}/edges/${finding.edge_id}/review` +
        `?finding=${encodeURIComponent(finding.id)}`,
    );
  }

  return (
    // Capped and internally scrolled so the header, the node filter and the
    // coverage strip stay put while a 130-card triage pass runs — on the demo
    // workstream the ungoverned list ran several screens past the fold, taking
    // the whole page with it.
    //
    // 12rem of headroom is a deliberate trade, not the largest gap that fits:
    // the page header runs ~13rem and the DemoController overlays the last ~4rem
    // of the viewport, so ~17rem is the most that clears both. At 12rem the last
    // finding sits behind the controller until the page is scrolled a little —
    // accepted, because the controller is a dismissible demo aid and the taller
    // box is worth more than the overlap costs.
    <Card
      data-testid="pairwise-card"
      className="glass flex max-h-[calc(100vh-12rem)] min-h-[24rem] flex-col overflow-hidden"
    >
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">Pairwise findings</h2>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            {DESCRIPTION}
          </p>
        </div>
        {data && data.nodes.length > 0 && (
          <NodeFilterChips
            nodes={data.nodes}
            selected={selected}
            onToggle={toggleNode}
            onClear={() => setSelected(new Set())}
          />
        )}
      </div>

      {query.isPending && (
        <div
          role="status"
          className="flex items-center gap-2 p-6 text-sm text-muted-foreground"
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading findings…
        </div>
      )}

      {query.isError && (
        <p className="p-6 text-sm text-muted-foreground">
          We could not load the findings for this task.
        </p>
      )}

      {data && (
        <>
          <CoverageStrip
            workstreamId={workstreamId}
            pairs={data.unanalysed_pairs}
            onAnalysed={() => queryClient.invalidateQueries({ queryKey })}
            collapsed={stripCollapsed}
          />

          {data.nodes.length === 0 ? (
            <p className="p-6 text-sm text-muted-foreground">
              This task has no neighbouring documents yet. Add connections on
              the workstream graph to surface linkages here.
            </p>
          ) : data.findings.length === 0 ? (
            <p className="p-6 text-sm text-muted-foreground">
              No linkages have been surfaced yet.
            </p>
          ) : (
            <div
              data-testid="findings-scroll"
              onScroll={handleFindingsScroll}
              className="flex-1 space-y-5 overflow-y-auto p-4"
            >
              {LABEL_SEVERITY_ORDER.map((label) => (
                <FindingGroup
                  key={label}
                  label={label}
                  findings={forGroupDisplay(grouped.get(label) ?? [])}
                  onReview={handleReview}
                  onSetState={(finding, state) =>
                    mutation.mutate({ finding, state })
                  }
                  isPending={(findingId) =>
                    mutation.isPending &&
                    mutation.variables?.finding.id === findingId
                  }
                  errorFor={(findingId) => errors[findingId]}
                />
              ))}
            </div>
          )}
        </>
      )}
    </Card>
  );
}
