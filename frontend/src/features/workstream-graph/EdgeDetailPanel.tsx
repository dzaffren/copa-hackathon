import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Loader2, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { analyzeEdge, fetchEdgeDetail } from "@/lib/api";
import { labelStyle, labelText } from "@/features/task/semanticLabel";

interface EdgeDetailPanelProps {
  workstreamId: string;
  edgeId: string;
}

/**
 * Right-panel detail for a selected edge. An unanalysed pair shows only the
 * "Analyze linkages" call-to-action; an analysed pair shows one finding card
 * per linkage (semantic-label pill + summary + Review) and no CTA. Structural
 * edge type is shown; semantic labels appear only on the finding cards.
 */
export function EdgeDetailPanel({
  workstreamId,
  edgeId,
}: EdgeDetailPanelProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["edge", workstreamId, edgeId],
    queryFn: () => fetchEdgeDetail(workstreamId, edgeId),
  });
  const analyze = useMutation({
    mutationFn: () => analyzeEdge(workstreamId, edgeId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["edge", workstreamId, edgeId],
      });
      queryClient.invalidateQueries({
        queryKey: ["workstream", workstreamId, "graph"],
      });
    },
  });

  if (query.isPending) {
    return (
      <div
        role="status"
        className="flex items-center gap-2 p-6 text-sm text-muted-foreground"
      >
        <Loader2 className="h-4 w-4 animate-spin" /> Loading edge…
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Could not load this edge.
      </div>
    );
  }

  const edge = query.data;
  const analysed = edge.status === "analysed";

  return (
    <Card className="flex h-full flex-col rounded-none border-0 border-l">
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="uppercase tracking-wide">
            {edge.edge_type}
          </Badge>
          <Badge
            className={cn(
              "border",
              analysed
                ? "border-emerald-200 bg-emerald-100 text-emerald-800"
                : "border-slate-200 bg-slate-100 text-slate-700",
            )}
          >
            {analysed ? `${edge.findings.length} linkage(s)` : "not analysed"}
          </Badge>
        </div>
        <h2 className="text-base font-bold leading-tight">
          {edge.source.title} ↔ {edge.target.title}
        </h2>
      </CardHeader>

      <CardContent className="flex-1 space-y-3 overflow-y-auto">
        {!analysed ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              This pair has not been analysed yet. Run the linkage analysis to
              surface how these two documents relate.
            </p>
            <Button
              className="w-full bg-indigo-600 hover:bg-indigo-700"
              disabled={analyze.isPending}
              onClick={() => analyze.mutate()}
            >
              {analyze.isPending ? (
                <>
                  <Loader2 className="animate-spin" /> Analyzing…
                </>
              ) : (
                <>
                  <Sparkles /> Analyze linkages
                </>
              )}
            </Button>
          </div>
        ) : (
          edge.findings.map((f, i) => {
            const style = labelStyle(f.label);
            return (
              <div key={i} className={cn("rounded-lg border p-3", style.card)}>
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span
                    className={cn(
                      "rounded px-2 py-0.5 text-xs font-semibold",
                      style.pill,
                    )}
                  >
                    {labelText(f.label, f.sentiment)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-indigo-600 hover:text-indigo-800"
                    onClick={() =>
                      navigate(
                        `/workstreams/${workstreamId}/edges/${edgeId}/review`,
                      )
                    }
                  >
                    Review
                  </Button>
                </div>
                <p className="text-sm">{f.summary}</p>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}

export default EdgeDetailPanel;
