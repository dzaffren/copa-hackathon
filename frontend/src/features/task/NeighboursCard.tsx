import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Neighbour, SecondOrderNeighbour } from "@/lib/types";
import { nodeTypeStyle } from "./nodeType";

interface Props {
  neighbours: Neighbour[];
  /** Documents joined to a neighbour rather than to the task. Optional so a
   *  caller holding an older cached response still renders. */
  secondOrder?: SecondOrderNeighbour[];
}

/** The task's declared context, in two tiers.
 *
 *  The tiers stay visually separate and are never summed into one count: a
 *  second-order document sits on an edge the task does not have, and folding it
 *  in would claim a relationship the drafter never declared. Each 2-hop row
 *  names the neighbour it arrives through for the same reason.
 *
 *  Both tiers now carry the same bar treatment, and the card takes the same
 *  height cap and internal scroll as the Pairwise Findings box beside it — the
 *  two sit in one row, so a shorter card left a ragged edge and a taller one
 *  pushed the row down.
 */
export function NeighboursCard({ neighbours, secondOrder = [] }: Props) {
  return (
    // Height matched to PairwiseFindingsCard, deliberately the same expression
    // rather than a similar one: they share a grid row, and two different caps
    // would drift apart the moment either is tuned.
    <Card
      data-testid="neighbours-card"
      className="glass flex max-h-[calc(100vh-12rem)] flex-col overflow-hidden"
    >
      {/* The card header, matching Pairwise findings and Recommendations: a
          sentence-case title with a one-line description beneath. */}
      <div className="shrink-0 border-b border-border/60 px-4 py-3">
        <h2 className="text-sm font-semibold">Neighbour nodes</h2>
        <p className="mt-0.5 text-[11px] text-muted-foreground">
          The documents this task's context is built from, in two tiers
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* 1 hop gets the same bar as 2 hops — the tiers are peers, and only one
            of them having a bar read as though the other were the card's default
            rather than a tier in its own right. */}
        <div className="border-b border-border/60 bg-muted/30 px-4 py-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            1 hop away{" "}
            <span className="font-normal text-muted-foreground/70">
              ({neighbours.length} · from node creation)
            </span>
          </div>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            Edges defined when this task was added to the graph.
          </p>
        </div>

        {neighbours.length === 0 ? (
          <p className="p-3 text-xs text-muted-foreground">
            No documents are joined to this task yet.
          </p>
        ) : (
          <div className="space-y-2 p-3 text-xs">
            {neighbours.map((n) => (
              <NeighbourRow
                key={n.edge_id}
                neighbour={n}
                testId="neighbour-row"
              />
            ))}
          </div>
        )}

        {secondOrder.length > 0 && (
          <>
            <div className="border-y border-border/60 bg-muted/30 px-4 py-2">
              <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                2 hops away{" "}
                <span className="font-normal text-muted-foreground/70">
                  ({secondOrder.length})
                </span>
              </div>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                Reached through a neighbour — context this task's context rests
                on.
              </p>
            </div>
            <div className="space-y-2 p-3 text-xs">
              {secondOrder.map((n) => (
                <NeighbourRow
                  key={n.edge_id}
                  neighbour={n}
                  testId="neighbour-row-2hop"
                  via={n.via_title}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

function NeighbourRow({
  neighbour,
  testId,
  via,
}: {
  neighbour: Neighbour;
  testId: string;
  via?: string;
}) {
  const style = nodeTypeStyle(neighbour.node_type);
  return (
    <div
      data-testid={testId}
      data-node-id={neighbour.node_id}
      className={cn(
        "flex items-center gap-2 rounded-md border p-2",
        style.row,
        // Muted against the direct rows: further out, and one step less certain
        // to matter to the draft.
        via && "opacity-75",
      )}
    >
      <span className={cn("h-2 w-2 shrink-0 rounded-full", style.dot)} />
      <div className="min-w-0 flex-1">
        <div className="truncate font-semibold">{neighbour.title}</div>
        <div className="text-[10px] opacity-80">
          {neighbour.edge_type} · {neighbour.node_type}
        </div>
        {via && (
          <div className="truncate text-[10px] opacity-70">via {via}</div>
        )}
      </div>
    </div>
  );
}
