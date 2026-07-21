import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchGraph, fetchWorkstreams } from "@/lib/api";
import { GraphCanvas } from "./GraphCanvas";
import { NodeDetailPanel } from "./NodeDetailPanel";
import { EdgeDetailPanel } from "./EdgeDetailPanel";
import { CrossWorkstreamPanel } from "./CrossWorkstreamPanel";
import { RegulatoryProfileCard } from "@/features/cross-intelligence/RegulatoryProfileCard";
import { AddNodeDialog } from "./AddNodeDialog";
import {
  EDGE_LEGEND,
  EDGE_LEGEND_ORDER,
  NODE_LEGEND,
  NODE_LEGEND_ORDER,
} from "./legend";

type Selection =
  | { kind: "none" }
  | { kind: "node"; id: string }
  | { kind: "edge"; id: string };

function LegendCard() {
  return (
    <div className="glass absolute bottom-3 left-3 z-10 rounded-xl p-3 text-[11px] shadow-sm">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        {NODE_LEGEND_ORDER.map((t) => (
          <div key={t} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full"
              style={{
                backgroundColor: NODE_LEGEND[t].fill,
                boxShadow: `0 0 6px ${NODE_LEGEND[t].stroke}`,
              }}
            />
            <span className="text-foreground/80">{NODE_LEGEND[t].label}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 border-t border-border/60 pt-2">
        {EDGE_LEGEND_ORDER.map((t) => (
          <div key={t} className="flex items-center gap-1.5">
            <svg width="22" height="8" aria-hidden>
              <line
                x1="0"
                y1="4"
                x2="22"
                y2="4"
                stroke={EDGE_LEGEND[t].stroke}
                strokeWidth="2"
                strokeDasharray={EDGE_LEGEND[t].dash.join(" ") || undefined}
              />
            </svg>
            <span className="text-foreground/80">{EDGE_LEGEND[t].label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * The drafter's hero screen at `/workstreams/:workstreamId`. Owns the graph
 * query, the right-panel state machine (idle / node-selected / edge-selected),
 * and the Add-node dialog open state.
 */
export default function WorkstreamGraphPage() {
  const { workstreamId = "" } = useParams();
  const [selection, setSelection] = useState<Selection>({ kind: "none" });
  const [addOpen, setAddOpen] = useState(false);

  const graphQuery = useQuery({
    queryKey: ["workstream", workstreamId, "graph"],
    queryFn: () => fetchGraph(workstreamId),
  });

  const { data: workstreams } = useQuery({
    queryKey: ["workstreams"],
    queryFn: fetchWorkstreams,
  });
  const name =
    workstreams?.find((w) => w.id === workstreamId)?.name ?? workstreamId;

  return (
    <>
      <div className="flex min-h-0 w-full flex-1 flex-col overflow-hidden bg-background">
        <header className="flex items-center justify-between gap-4 border-b border-border/60 px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-cyan-300/80">
              Workstream graph
            </p>
            <h1 className="text-lg font-bold">{name}</h1>
          </div>
          <Button
            className="bg-cyan-500 text-slate-950 hover:bg-cyan-400"
            onClick={() => setAddOpen(true)}
          >
            <Plus /> Add node
          </Button>
        </header>

        <div className="relative flex min-h-0 flex-1">
          <main className="relative min-w-0 flex-1">
            {graphQuery.isPending ? (
              <div
                role="status"
                aria-label="Loading graph"
                className="absolute inset-0 grid place-items-center bg-[#0b1220]"
              >
                <div className="relative h-64 w-64">
                  <Skeleton className="absolute left-1/2 top-1/2 h-20 w-20 -translate-x-1/2 -translate-y-1/2 rounded-full" />
                  {[0, 1, 2, 3, 4].map((i) => {
                    const a = (-90 + i * 72) * (Math.PI / 180);
                    return (
                      <Skeleton
                        key={i}
                        className="absolute h-10 w-10 rounded-full"
                        style={{
                          left: `calc(50% + ${Math.cos(a) * 110}px - 20px)`,
                          top: `calc(50% + ${Math.sin(a) * 110}px - 20px)`,
                        }}
                      />
                    );
                  })}
                </div>
              </div>
            ) : graphQuery.isError ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                Could not load this workstream.
              </div>
            ) : (
              <GraphCanvas
                nodes={graphQuery.data.nodes}
                edges={graphQuery.data.edges}
                primaryTaskId={graphQuery.data.primary_task_id}
                selectedNodeId={selection.kind === "node" ? selection.id : null}
                selectedEdgeId={selection.kind === "edge" ? selection.id : null}
                onSelectNode={(id) => setSelection({ kind: "node", id })}
                onSelectEdge={(id) => setSelection({ kind: "edge", id })}
              />
            )}
            {!graphQuery.isPending && !graphQuery.isError && <LegendCard />}
          </main>

          <div className="w-80 shrink-0 overflow-hidden border-l border-border/60 bg-card/30 backdrop-blur">
            {selection.kind === "node" ? (
              <NodeDetailPanel
                workstreamId={workstreamId}
                nodeId={selection.id}
                onClose={() => setSelection({ kind: "none" })}
                onSelectNode={(id) => setSelection({ kind: "node", id })}
              />
            ) : selection.kind === "edge" ? (
              <EdgeDetailPanel
                workstreamId={workstreamId}
                edgeId={selection.id}
                onClose={() => setSelection({ kind: "none" })}
              />
            ) : (
              // Nothing selected: the rail leads with cross-workstream drift.
              // It is the one thing on this screen a drafter cannot find by
              // reading their own workstream, so it should not need hunting for.
              <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
                <CrossWorkstreamPanel workstreamId={workstreamId} />
                <RegulatoryProfileCard workstreamId={workstreamId} />
                <p className="px-3 text-center text-sm text-muted-foreground">
                  Select a node or edge to see its details.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <AddNodeDialog
        workstreamId={workstreamId}
        nodes={graphQuery.data?.nodes ?? []}
        open={addOpen}
        onOpenChange={setAddOpen}
      />
    </>
  );
}
