import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GraphCanvas } from "./GraphCanvas";
import type { GraphEdge, GraphNode } from "@/lib/types";

// react-force-graph-2d is stubbed globally (src/test/mocks) with an accessible
// DOM: one button per node (named by title) and per edge (named
// "edge <type> <source> to <target>"). These tests exercise selection through
// that stub and confirm the zoom controls are present and inert-safe.

const NODES: GraphNode[] = [
  {
    id: "opres-pd-v0-3",
    node_type: "task",
    title: "Operational Resilience PD — v0.3",
    issuer: "BNM",
    short_type: "PD (draft)",
  },
  {
    id: "bcbs-opres-2021",
    node_type: "international-standard",
    title: "BCBS OpRes 2021",
    issuer: "BCBS",
    short_type: "Principles",
  },
];

const EDGES: GraphEdge[] = [
  {
    id: "e1",
    source: "opres-pd-v0-3",
    target: "bcbs-opres-2021",
    edge_type: "contributes-to",
    analysed: true,
    findings_count: 3,
  },
];

function setup() {
  const onSelectNode = vi.fn();
  const onSelectEdge = vi.fn();
  render(
    <GraphCanvas
      nodes={NODES}
      edges={EDGES}
      primaryTaskId="opres-pd-v0-3"
      onSelectNode={onSelectNode}
      onSelectEdge={onSelectEdge}
    />,
  );
  return { onSelectNode, onSelectEdge };
}

describe("GraphCanvas", () => {
  it("clicking a node dispatches onSelectNode with the node id", async () => {
    const { onSelectNode } = setup();
    await userEvent.click(
      screen.getByRole("button", { name: "BCBS OpRes 2021" }),
    );
    expect(onSelectNode).toHaveBeenCalledWith("bcbs-opres-2021");
  });

  it("clicking an edge dispatches onSelectEdge with the edge id", async () => {
    const { onSelectEdge } = setup();
    await userEvent.click(
      screen.getByRole("button", { name: /^edge contributes-to/ }),
    );
    expect(onSelectEdge).toHaveBeenCalledWith("e1");
  });

  it("renders the zoom controls", () => {
    setup();
    expect(
      screen.getByRole("button", { name: /zoom in/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /zoom out/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /reset zoom/i }),
    ).toBeInTheDocument();
  });

  it("zoom controls do not throw when clicked", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /zoom in/i }));
    await userEvent.click(screen.getByRole("button", { name: /zoom out/i }));
    await userEvent.click(screen.getByRole("button", { name: /reset zoom/i }));
    // The mocked ForceGraph ref stubs zoom/zoomToFit — reaching here is the
    // assertion (no throw).
    expect(screen.getByTestId("graph-canvas")).toBeInTheDocument();
  });
});
