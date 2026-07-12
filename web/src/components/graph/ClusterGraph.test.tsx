// Tests for the React Flow cluster canvas (spec-drafter-workspace.md · System
// Design "Cluster graph"; Tests 1/7/8). Rendering a real React Flow canvas in
// jsdom is brittle (it needs a sized container + ResizeObserver), so `reactflow`
// is mocked with a light stand-in that still:
//   • builds the map from `toReactFlowModel(graph)` (overlay merge included),
//   • invokes the real custom node/edge renderers (so their data-testid /
//     data-marking contract is exercised end to end), and
//   • wires onNodeClick / onEdgeClick / onPaneClick to the selection callbacks.

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// A minimal, deterministic stand-in for reactflow. `ReactFlow` renders each node
// through its registered node type and each edge through its edge type, and
// forwards clicks to the handlers — everything the component wires up.
vi.mock("reactflow", async () => {
  const React = await import("react");

  function MockReactFlow(props: any) {
    const {
      nodes = [],
      edges = [],
      nodeTypes = {},
      edgeTypes = {},
      onNodeClick,
      onEdgeClick,
      onPaneClick,
      children,
    } = props;

    return React.createElement(
      "div",
      { "data-testid": "mock-reactflow" },
      React.createElement("div", {
        "data-testid": "rf-pane",
        onClick: (e: unknown) => onPaneClick && onPaneClick(e),
      }),
      ...nodes.map((node: any) => {
        const NodeComp = nodeTypes[node.type];
        return React.createElement(
          "div",
          {
            key: node.id,
            "data-testid": `wrap-${node.id}`,
            onClick: (e: unknown) => onNodeClick && onNodeClick(e, node),
          },
          NodeComp
            ? React.createElement(NodeComp, {
                id: node.id,
                type: node.type,
                data: node.data,
                selected: !!node.selected,
              })
            : null,
        );
      }),
      ...edges.map((edge: any) => {
        const EdgeComp = edgeTypes[edge.type];
        return React.createElement(
          "svg",
          {
            key: edge.id,
            "data-testid": `wrap-${edge.id}`,
            onClick: (e: unknown) => onEdgeClick && onEdgeClick(e, edge),
          },
          EdgeComp
            ? React.createElement(EdgeComp, {
                id: edge.id,
                data: edge.data,
                source: edge.source,
                target: edge.target,
                sourceX: 0,
                sourceY: 0,
                targetX: 10,
                targetY: 10,
                sourcePosition: "bottom",
                targetPosition: "top",
              })
            : null,
        );
      }),
      children,
    );
  }

  return {
    default: MockReactFlow,
    ReactFlow: MockReactFlow,
    Background: () => null,
    Controls: () => null,
    Handle: () => null,
    Position: { Top: "top", Right: "right", Bottom: "bottom", Left: "left" },
    getBezierPath: () => ["M0 0 L10 10", 5, 5],
  };
});

import type { Graph, GraphNode } from "../../types";
import { toReactFlowModel } from "../../lib/graphModel";
import { deriveMarking } from "../../lib/treatments";
import ClusterGraph from "./ClusterGraph";

// Defensive polyfill (unused with the mock, but harmless if reactflow ever leaks).
if (!("ResizeObserver" in globalThis)) {
  (globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver =
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
}

function policyNode(overrides: Partial<GraphNode>): GraphNode {
  return {
    id: "id",
    policy_id: "p",
    title: "Policy",
    version: "v1",
    status: "In force",
    cluster: "technology-risk",
    ...overrides,
  };
}

/** A tiny slice of the real corpus: the draft + one in-force policy + an edge.
 *  The overlay (merged inside the mapper) adds the AML preview + reference band. */
const GRAPH: Graph = {
  nodes: [
    policyNode({
      id: "rmit-v2-2026-draft",
      policy_id: "rmit",
      title: "Risk Management in Technology (RMiT)",
      version: "v2 · 2026 draft",
      status: "In progress",
    }),
    policyNode({
      id: "outsourcing-v1-2019",
      policy_id: "outsourcing",
      title: "Outsourcing",
      version: "v1 · 2019",
      status: "In force",
    }),
  ],
  edges: [
    {
      source: "rmit-v2-2026-draft",
      target: "outsourcing-v1-2019",
      type: "overlaps",
      reason:
        "A public-cloud arrangement is often also a material outsourcing.",
      source_clauses: ["RMiT 17.1"],
      target_clauses: ["Outsourcing 12.1"],
      provenance: "curated",
      confidence: 1,
    },
  ],
};

const noop = () => {};

describe("ClusterGraph — model built from toReactFlowModel", () => {
  it("renders every mapped node with node-{id} + its derived data-marking", () => {
    render(
      <ClusterGraph
        graph={GRAPH}
        onNodeSelect={noop}
        onEdgeSelect={noop}
        onPaneClick={noop}
      />,
    );

    const model = toReactFlowModel(GRAPH);
    for (const node of model.nodes) {
      const el = screen.getByTestId(node.data.testId);
      expect(el).toHaveAttribute("data-marking", deriveMarking(node.data.node));
    }
    // Exactly the mapped node set is rendered.
    expect(screen.getAllByTestId(/^node-/)).toHaveLength(model.nodes.length);
  });

  it("includes the overlay AML preview node (proves the merge ran)", () => {
    render(
      <ClusterGraph
        graph={GRAPH}
        onNodeSelect={noop}
        onEdgeSelect={noop}
        onPaneClick={noop}
      />,
    );
    expect(screen.getByTestId("node-aml-cft")).toHaveAttribute(
      "data-marking",
      "other cluster (preview only)",
    );
  });

  it("renders the marking legend", () => {
    render(
      <ClusterGraph
        graph={GRAPH}
        onNodeSelect={noop}
        onEdgeSelect={noop}
        onPaneClick={noop}
      />,
    );
    expect(screen.getByTestId("legend")).toBeInTheDocument();
  });
});

describe("ClusterGraph — selection callbacks", () => {
  it("calls onNodeSelect with the node id on a node click", () => {
    const onNodeSelect = vi.fn();
    render(
      <ClusterGraph
        graph={GRAPH}
        onNodeSelect={onNodeSelect}
        onEdgeSelect={noop}
        onPaneClick={noop}
      />,
    );
    fireEvent.click(screen.getByTestId("node-outsourcing-v1-2019"));
    expect(onNodeSelect).toHaveBeenCalledWith("outsourcing-v1-2019");
  });

  it("calls onEdgeSelect with (source, target) on an edge click", () => {
    const onEdgeSelect = vi.fn();
    render(
      <ClusterGraph
        graph={GRAPH}
        onNodeSelect={noop}
        onEdgeSelect={onEdgeSelect}
        onPaneClick={noop}
      />,
    );
    // A reference edge added by the overlay: draft → PDPA.
    fireEvent.click(screen.getByTestId("edge-rmit-v2-2026-draft__pdpa-2010"));
    expect(onEdgeSelect).toHaveBeenCalledWith(
      "rmit-v2-2026-draft",
      "pdpa-2010",
    );
  });

  it("calls onPaneClick (a no-op) on an empty-pane click, selecting nothing", () => {
    const onPaneClick = vi.fn();
    const onNodeSelect = vi.fn();
    render(
      <ClusterGraph
        graph={GRAPH}
        onNodeSelect={onNodeSelect}
        onEdgeSelect={noop}
        onPaneClick={onPaneClick}
      />,
    );
    fireEvent.click(screen.getByTestId("rf-pane"));
    expect(onPaneClick).toHaveBeenCalledTimes(1);
    expect(onNodeSelect).not.toHaveBeenCalled();
  });
});

describe("ClusterGraph — selection highlight", () => {
  it("flags the selected node via data-selected", () => {
    render(
      <ClusterGraph
        graph={GRAPH}
        selectedId="outsourcing-v1-2019"
        onNodeSelect={noop}
        onEdgeSelect={noop}
        onPaneClick={noop}
      />,
    );
    expect(screen.getByTestId("node-outsourcing-v1-2019")).toHaveAttribute(
      "data-selected",
      "true",
    );
    expect(screen.getByTestId("node-rmit-v2-2026-draft")).not.toHaveAttribute(
      "data-selected",
    );
  });
});
