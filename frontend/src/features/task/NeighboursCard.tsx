import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Neighbour } from "@/lib/types";
import { nodeTypeStyle } from "./nodeType";

export function NeighboursCard({ neighbours }: { neighbours: Neighbour[] }) {
  return (
    <Card data-testid="neighbours-card" className="overflow-hidden">
      <div className="border-b px-4 py-3">
        <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          Neighbour nodes{" "}
          <span className="font-normal text-muted-foreground/70">
            ({neighbours.length} · from node creation)
          </span>
        </div>
        <p className="mt-1 text-[11px] text-muted-foreground">
          Edges defined when this task was added to the graph.
        </p>
      </div>
      <div className="space-y-2 p-3 text-xs">
        {neighbours.map((n) => {
          const style = nodeTypeStyle(n.node_type);
          return (
            <div
              key={n.edge_id}
              data-testid="neighbour-row"
              className={cn(
                "flex items-center gap-2 rounded-md border p-2",
                style.row,
              )}
            >
              <span
                className={cn("h-2 w-2 shrink-0 rounded-full", style.dot)}
              />
              <div className="min-w-0 flex-1">
                <div className="truncate font-semibold">{n.title}</div>
                <div className="text-[10px] opacity-80">
                  {n.edge_type} · {n.node_type}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
