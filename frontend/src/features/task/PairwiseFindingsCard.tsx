import { useMemo, useState } from "react";
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

  function handleReview(finding: PairwiseFinding) {
    navigate(
      `/workstreams/${workstreamId}/edges/${finding.edge_id}/review` +
        `?finding=${encodeURIComponent(finding.id)}`,
    );
  }

  return (
    <Card data-testid="pairwise-card" className="glass overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
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
            <div className="space-y-5 p-4">
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
