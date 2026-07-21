import { useState } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Connection, Neighbour } from "@/lib/types";
import { nodeTypeStyle, shortLabelForNode } from "./nodeType";
import { NeighbourFindingsCard } from "./NeighbourFindingsCard";
import { EmptyDraftCard } from "./EmptyDraftCard";

interface Props {
  workstreamId: string;
  nodeId: string;
  neighbours: Neighbour[];
  draftEmpty: boolean;
}

const ALL = "all";

export function PairwiseComparisonCard({
  workstreamId,
  nodeId,
  neighbours,
  draftEmpty,
}: Props) {
  const [selected, setSelected] = useState<string>(ALL);
  const [analyzedEdges, setAnalyzedEdges] = useState<
    Record<string, Connection[]>
  >({});

  function handleAnalyzed(edgeId: string, findings: Connection[]) {
    setAnalyzedEdges((prev) => ({ ...prev, [edgeId]: findings }));
  }

  const analysedCount = neighbours.filter(
    (n) => n.analysed || n.edge_id in analyzedEdges,
  ).length;

  const visible =
    selected === ALL
      ? neighbours
      : neighbours.filter((n) => n.node_id === selected);

  return (
    <Card data-testid="pairwise-card" className="glass overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">
            Pairwise comparison{" "}
            <span className="text-xs font-normal text-muted-foreground">
              · draft vs neighbours
            </span>
          </h2>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            Finder→critic linkages between the working draft and each neighbour
            node.
          </p>
        </div>

        {!draftEmpty && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Filter:</span>
            <div
              role="group"
              aria-label="Filter by neighbour"
              className="flex flex-wrap items-center gap-1"
            >
              <FilterChip
                label="All"
                selected={selected === ALL}
                onClick={() => setSelected(ALL)}
                idleClasses="border-cyan-400/40 text-cyan-300"
              />
              {neighbours.map((n) => {
                const style = nodeTypeStyle(n.node_type);
                return (
                  <FilterChip
                    key={n.edge_id}
                    label={shortLabelForNode(n.node_id, n.title)}
                    selected={selected === n.node_id}
                    onClick={() => setSelected(n.node_id)}
                    idleClasses={style.chip}
                  />
                );
              })}
            </div>
          </div>
        )}
      </div>

      {draftEmpty ? (
        <EmptyDraftCard workstreamId={workstreamId} nodeId={nodeId} />
      ) : (
        <>
          <div className="space-y-3 p-4">
            {visible.map((n) => (
              <NeighbourFindingsCard
                key={n.edge_id}
                workstreamId={workstreamId}
                neighbour={n}
                preloadedFindings={analyzedEdges[n.edge_id]}
                onAnalyzed={handleAnalyzed}
              />
            ))}
          </div>
          <div className="border-t border-border/60 bg-muted/20 px-4 py-3 text-[11px] italic text-muted-foreground">
            {analysedCount} of {neighbours.length} neighbours analysed
          </div>
        </>
      )}
    </Card>
  );
}

interface ChipProps {
  label: string;
  selected: boolean;
  onClick: () => void;
  idleClasses: string;
  selectedClasses?: string;
}

function FilterChip({
  label,
  selected,
  onClick,
  idleClasses,
  selectedClasses,
}: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={cn(
        "rounded-md border bg-card/40 px-2 py-1 text-[11px] font-medium transition-colors",
        selected
          ? cn("border-cyan-400 bg-cyan-500 text-slate-950", selectedClasses)
          : idleClasses,
      )}
    >
      {label}
    </button>
  );
}
