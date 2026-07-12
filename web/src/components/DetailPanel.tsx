// Detail panel (spec-drafter-workspace.md · System Design "Detail panel: Routes
// selection → NodeDetail / EdgeDetail / keeps last on empty click"; the panel is
// a labelled region and is NEVER blank).
//
// Routing:
//   • a node selection → NodeDetail (status / version / note / linked-to / one
//     action, plus the "Why this changed" trail for the draft);
//   • an edge selection → EdgeDetail ("why connected" + verbatim cited clauses);
//   • a null selection (an empty-pane click) → keep the LAST rendered detail, so
//     the panel never goes blank (Test 7 "empty-pane click keeps selection").
//
// Each child is keyed by the selected node/edge id so switching selection remounts
// it — the hydration effects re-run cleanly per selection ("Selecting a node after
// a connection returns to node detail").

import { useRef } from "react";

import type { GraphEdge, GraphNode } from "../types";
import NodeDetail from "./detail/NodeDetail";
import EdgeDetail from "./detail/EdgeDetail";

/** What the workspace has selected on the map. `null` = nothing (or an empty-pane
 *  click) — the panel then keeps its last non-null detail. */
export type DetailSelection =
  { kind: "node"; node: GraphNode } | { kind: "edge"; edge: GraphEdge } | null;

export interface DetailPanelProps {
  selection: DetailSelection;
}

function renderSelection(selection: DetailSelection): JSX.Element {
  if (selection === null) {
    return (
      <p className="text-sm text-slate-400">
        Select a node or a connection on the map to see its detail.
      </p>
    );
  }
  if (selection.kind === "node") {
    return <NodeDetail key={selection.node.id} node={selection.node} />;
  }
  const { edge } = selection;
  return <EdgeDetail key={`${edge.source}__${edge.target}`} edge={edge} />;
}

export default function DetailPanel({
  selection,
}: DetailPanelProps): JSX.Element {
  // Keep the last non-null selection so an empty-pane click (null) never blanks
  // the panel. Caching a value in a ref during render is the supported pattern
  // for "remember the last non-null prop".
  const lastNonNull = useRef<DetailSelection>(null);
  if (selection !== null) {
    lastNonNull.current = selection;
  }
  const effective = selection ?? lastNonNull.current;

  return (
    <section
      data-testid="detail-panel"
      role="region"
      aria-label="Detail panel"
      className="h-full overflow-y-auto border-l border-slate-200 bg-white p-4"
    >
      {renderSelection(effective)}
    </section>
  );
}
