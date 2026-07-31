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

  // The working draft, and the rail's resting subject. Read from the graph so
  // it survives a node delete: the graph refetches, and the rail follows.
  const focalTaskId = graphQuery.data?.primary_task_id ?? null;

  return (
    <>
      <div className="flex min-h-0 w-full flex-1 flex-col overflow-hidden bg-background">
        <header className="flex items-center justify-between gap-4 border-b border-border/60 px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary/80">
              Workstream graph
            </p>
            <h1 className="text-lg font-bold">{name}</h1>
          </div>
          <Button
            className="bg-primary text-primary-foreground hover:bg-primary/90"
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
                className="absolute inset-0 grid place-items-center bg-muted"
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

          <div
            data-testid="graph-detail-rail"
            className="w-80 shrink-0 overflow-hidden border-l border-border/60 bg-card"
          >
            {selection.kind === "node" ? (
              <NodeDetailPanel
                workstreamId={workstreamId}
                nodeId={selection.id}
                nodes={graphQuery.data?.nodes ?? []}
                onClose={() => setSelection({ kind: "none" })}
                onSelectNode={(id) => setSelection({ kind: "node", id })}
              />
            ) : selection.kind === "edge" ? (
              <EdgeDetailPanel
                workstreamId={workstreamId}
                edgeId={selection.id}
                onClose={() => setSelection({ kind: "none" })}
              />
            ) : focalTaskId ? (
              // Nothing selected: the rail rests on the focal task node. The
              // working draft is what the drafter came to this screen for, so
              // it should not take a click to read. No `onClose` — this is the
              // resting state, not a panel laid over one.
              <NodeDetailPanel
                key={focalTaskId}
                workstreamId={workstreamId}
                nodeId={focalTaskId}
                nodes={graphQuery.data?.nodes ?? []}
                onSelectNode={(id) => setSelection({ kind: "node", id })}
              />
            ) : (
              // No focal task node (a graph still loading, or one without a
              // working draft) — the rail says what to do instead.
              <div className="flex h-full items-center justify-center p-6">
                <p className="text-center text-sm text-muted-foreground">
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
