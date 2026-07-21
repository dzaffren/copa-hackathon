import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Loader2, Search, Sparkles, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { analyzeEdge, fetchEdgeDetail } from "@/lib/api";
import { labelStyle, labelText } from "@/lib/labels";

interface EdgeDetailPanelProps {
  workstreamId: string;
  edgeId: string;
  onClose?: () => void;
}

function PanelHeader({ onClose }: { onClose?: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 px-4 py-2.5">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        Edge detail
      </span>
      {onClose && (
        <button
          type="button"
          aria-label="Close panel"
          onClick={onClose}
          className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
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
  onClose,
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
      <div className="flex h-full flex-col">
        <PanelHeader onClose={onClose} />
        <div
          role="status"
          className="flex items-center gap-2 p-6 text-sm text-muted-foreground"
        >
          <Loader2 className="h-4 w-4 animate-spin" /> Loading edge…
        </div>
      </div>
    );
  }
  if (query.isError) {
    return (
      <div className="flex h-full flex-col">
        <PanelHeader onClose={onClose} />
        <div className="p-6 text-sm text-muted-foreground">
          Could not load this edge.
        </div>
      </div>
    );
  }

  const edge = query.data;
  const analysed = edge.status === "analysed";
  const analysable = edge.analysable;

  return (
    <div className="flex h-full flex-col animate-in slide-in-from-right-4 duration-200">
      <PanelHeader onClose={onClose} />
      <div className="space-y-2 px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="uppercase tracking-wide">
            {edge.edge_type}
          </Badge>
          <Badge
            className={cn(
              "border",
              analysed
                ? "border-emerald-400/30 bg-emerald-500/15 text-emerald-300"
                : "border-amber-300/30 bg-amber-400/15 text-amber-300",
            )}
          >
            {analysed ? `${edge.findings.length} linkage(s)` : "not analysed"}
          </Badge>
        </div>
        <h2 className="text-base font-bold leading-tight">
          {edge.source.title}{" "}
          <span className="text-muted-foreground">↔</span> {edge.target.title}
        </h2>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 pb-4">
        {!analysed ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              This pair has not been analysed yet. Run the linkage analysis to
              surface how these two documents relate.
            </p>
            <Button
              className="w-full bg-cyan-500 text-slate-950 hover:bg-cyan-400"
              disabled={analyze.isPending || !analysable}
              onClick={() => analyze.mutate()}
            >
              {analyze.isPending ? (
                <>
                  <Loader2 className="animate-spin" /> Analyzing… the AI is
                  reading both documents
                </>
              ) : (
                <>
                  <Sparkles /> Analyze linkages
                </>
              )}
            </Button>
            {!analysable && (
              <p className="text-xs text-muted-foreground">
                Live analysis needs both documents ingested — this pair isn’t in
                the corpus yet.
              </p>
            )}
            {analyze.isError && (
              <p className="text-xs text-red-600">
                Analysis failed. Check the engine has model credentials, then
                retry.
              </p>
            )}
            {/* The finder can genuinely surface nothing for a pair — say so
                rather than leaving the CTA to silently reset with no feedback. */}
            {analyze.data?.status === "no_matching_source" && (
              <p className="flex items-start gap-1.5 text-xs italic text-muted-foreground">
                <Search className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                No matching clause found — no linkages surfaced for this pair.
              </p>
            )}
          </div>
        ) : (
          edge.findings.map((f, i) => {
            const style = labelStyle(f.label);
            return (
              <div
                key={i}
                className={cn(
                  "rounded-lg border border-l-2 border-border/60 bg-card/50 p-3",
                  style.accent,
                )}
              >
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-semibold",
                      style.pill,
                    )}
                  >
                    {labelText(f.label, f.sentiment)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-cyan-300 hover:text-cyan-200"
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
      </div>
    </div>
  );
}

export default EdgeDetailPanel;
