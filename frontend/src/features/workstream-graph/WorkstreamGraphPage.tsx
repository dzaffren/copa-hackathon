import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { fetchGraph } from "@/lib/api";
import { Sidebar } from "./Sidebar";
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
    <div className="absolute bottom-3 left-3 z-10 rounded-md border bg-white/95 p-3 text-[11px] shadow-sm">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        {NODE_LEGEND_ORDER.map((t) => (
          <div key={t} className="flex items-center gap-1.5">
            <span
              className="inline-block h-3 w-3 rounded-full border-2"
              style={{
                backgroundColor: NODE_LEGEND[t].fill,
                borderColor: NODE_LEGEND[t].stroke,
              }}
            />
            <span>{NODE_LEGEND[t].label}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 border-t pt-2">
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
                strokeDasharray={EDGE_LEGEND[t].dash || undefined}
              />
            </svg>
            <span>{EDGE_LEGEND[t].label}</span>
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

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white">
      <Sidebar activeWorkstreamId={workstreamId} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Workstream graph
            </p>
            <h1 className="text-lg font-bold">{workstreamId}</h1>
          </div>
          <Button
            className="bg-indigo-600 hover:bg-indigo-700"
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
                className="flex h-full items-center justify-center gap-2 text-sm text-muted-foreground"
              >
                <Loader2 className="h-4 w-4 animate-spin" /> Loading graph…
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
            <LegendCard />
          </main>

          <div className="w-80 shrink-0 overflow-hidden border-l">
            {selection.kind === "node" ? (
              <NodeDetailPanel
                workstreamId={workstreamId}
                nodeId={selection.id}
                onSelectNode={(id) => setSelection({ kind: "node", id })}
              />
            ) : selection.kind === "edge" ? (
              <EdgeDetailPanel
                workstreamId={workstreamId}
                edgeId={selection.id}
              />
            ) : (
              <div className="flex h-full items-center justify-center p-6 text-center text-sm text-muted-foreground">
                Select a node or edge to see its details.
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
    </div>
  );
}
