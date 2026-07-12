// The React Flow cluster canvas (spec-drafter-workspace.md · System Design
// "Cluster graph": nodes, selectable edges, onNodeClick / onEdgeClick /
// onPaneClick). It is a pure presenter: the map model comes from
// `toReactFlowModel(graph)` (which merges the AML preview + external-reference
// band) and every click is forwarded to the owner (WorkspacePage, Task 8) as a
// selection callback. It holds no selection state of its own.
//
// Behaviour bound to the scenarios:
//   • node click  → onNodeSelect(id)                 ("Inspecting my … draft")
//   • edge click  → onEdgeSelect(source, target)     ("Understanding a connection")
//   • pane click  → onPaneClick()  — a no-op         ("Clicking empty map space
//                                                      keeps the current detail")

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

import type { Graph } from "../../types";
import { toReactFlowModel } from "../../lib/graphModel";
import { nodeTypes } from "./nodeTypes";
import { edgeTypes } from "./edgeTypes";
import Legend from "../Legend";

export interface ClusterGraphProps {
  /** The engine graph (merged with the overlay inside the mapper). */
  graph: Graph;
  /** The currently selected node id (highlights that node). */
  selectedId?: string;
  /** Called with the node id when a node is clicked. */
  onNodeSelect: (id: string) => void;
  /** Called with the edge's endpoints when a connection is clicked. */
  onEdgeSelect: (source: string, target: string) => void;
  /** Called on an empty-pane click — a no-op that preserves selection. */
  onPaneClick: () => void;
}

/** The cluster map: a fit-to-view React Flow canvas plus the marking legend. */
export default function ClusterGraph({
  graph,
  selectedId,
  onNodeSelect,
  onEdgeSelect,
  onPaneClick,
}: ClusterGraphProps) {
  const model = useMemo(() => toReactFlowModel(graph), [graph]);

  // Reflect the owner's selection onto the mapped nodes (no internal state).
  const nodes: Node[] = useMemo(
    () =>
      model.nodes.map((node) => ({
        ...node,
        selected: node.id === selectedId,
      })),
    [model.nodes, selectedId],
  );
  const edges: Edge[] = model.edges;

  return (
    <div data-testid="cluster-graph" className="relative h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={(_, node) => onNodeSelect(node.id)}
        onEdgeClick={(_, edge) => onEdgeSelect(edge.source, edge.target)}
        onPaneClick={() => onPaneClick()}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        minZoom={0.2}
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>

      {/* The legend overlays the canvas; it is not part of the flow itself. */}
      <div className="pointer-events-none absolute left-3 top-3 z-10 max-w-[15rem]">
        <div className="pointer-events-auto">
          <Legend />
        </div>
      </div>
    </div>
  );
}
