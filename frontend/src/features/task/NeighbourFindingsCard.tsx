import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { analyzeEdge, fetchEdgeFindings } from "@/lib/api";
import type { Connection, Neighbour } from "@/lib/types";
import { nodeTypeStyle } from "./nodeType";
import { labelStyle, labelText } from "./semanticLabel";

interface Props {
  workstreamId: string;
  neighbour: Neighbour;
  /** Findings surfaced by a local "Analyze linkages" click. */
  preloadedFindings?: Connection[];
  onAnalyzed: (edgeId: string, findings: Connection[]) => void;
}

export function NeighbourFindingsCard({
  workstreamId,
  neighbour,
  preloadedFindings,
  onAnalyzed,
}: Props) {
  const [analyzing, setAnalyzing] = useState(false);
  const [noLinkages, setNoLinkages] = useState(false);

  const effectiveAnalysed = neighbour.analysed || preloadedFindings != null;
  const nodeStyle = nodeTypeStyle(neighbour.node_type);

  const findingsQuery = useQuery({
    queryKey: ["findings", workstreamId, neighbour.edge_id],
    queryFn: () => fetchEdgeFindings(workstreamId, neighbour.edge_id),
    enabled: neighbour.analysed && preloadedFindings == null,
  });

  const findings = preloadedFindings ?? findingsQuery.data;
  const headline = findings?.[0];

  const reviewHref = `/workstreams/${workstreamId}/edges/${neighbour.edge_id}/review`;

  async function handleAnalyze() {
    setAnalyzing(true);
    setNoLinkages(false);
    try {
      // Run the real finder→critic analysis (not a re-read of already-stored
      // findings, which is always empty for a pair that has never been
      // analysed) — mirrors the graph screen's "Analyze linkages" action.
      const result = await analyzeEdge(workstreamId, neighbour.edge_id);
      if (result.status === "analysed" && result.findings.length > 0) {
        onAnalyzed(neighbour.edge_id, result.findings);
      } else {
        setNoLinkages(true);
      }
    } finally {
      setAnalyzing(false);
    }
  }

  const namePill = (
    <span
      className={cn(
        "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
        nodeStyle.pill,
      )}
    >
      {neighbour.title}
    </span>
  );

  if (!effectiveAnalysed) {
    return (
      <article
        data-testid="pair-card"
        data-neighbour={neighbour.node_id}
        data-analysed="false"
        className="rounded-lg border-2 border-dashed border-border/70 bg-muted/20 p-3"
      >
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            {namePill}
            <Badge className="border border-amber-300/30 bg-amber-400/15 text-amber-300 hover:bg-amber-400/15">
              not analysed
            </Badge>
          </div>
          <span className="text-[11px] text-muted-foreground">0 findings</span>
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          No pairwise linkages have been surfaced yet. Run finder→critic to
          compare this task&apos;s draft against {neighbour.title}.
        </p>
        {noLinkages && (
          <p className="mt-1 text-xs italic text-muted-foreground">
            No matching clause found — no linkages surfaced for this pair.
          </p>
        )}
        <Button
          size="sm"
          className="mt-2 bg-cyan-500 text-slate-950 hover:bg-cyan-400"
          onClick={handleAnalyze}
          disabled={analyzing}
        >
          {analyzing ? (
            <>
              <Loader2 className="animate-spin" /> Analyzing…
            </>
          ) : (
            <>
              <Search /> Analyze linkages
            </>
          )}
        </Button>
      </article>
    );
  }

  const style = headline ? labelStyle(headline.label) : null;

  return (
    <article
      data-testid="pair-card"
      data-neighbour={neighbour.node_id}
      data-analysed="true"
      className={cn("rounded-lg border p-3", style?.card ?? "border-border/60 bg-card/50")}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          {namePill}
          {headline && (
            <span
              className={cn(
                "rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                labelStyle(headline.label).pill,
              )}
            >
              {labelText(headline.label, headline.sentiment)}
            </span>
          )}
        </div>
        <span className="text-[11px] text-muted-foreground">
          {neighbour.findings_count || findings?.length || 0} findings
        </span>
      </div>

      {headline ? (
        <p className="text-sm font-semibold text-foreground">
          {headline.summary}
        </p>
      ) : (
        <p className="text-xs italic text-muted-foreground">
          Loading findings…
        </p>
      )}

      <Link
        to={reviewHref}
        className="mt-2 inline-block text-xs font-semibold text-cyan-300 hover:text-cyan-200"
      >
        Open in Review →
      </Link>
    </article>
  );
}
