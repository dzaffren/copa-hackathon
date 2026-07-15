import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GraphCanvas } from "./GraphCanvas";
import type { GraphEdge, GraphNode } from "@/lib/types";

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

  it("zoom-in clamps at 2.5 after repeated clicks", async () => {
    setup();
    const zoomIn = screen.getByRole("button", { name: /zoom in/i });
    for (let i = 0; i < 12; i++) await userEvent.click(zoomIn);
    expect(screen.getByTestId("zoom-group")).toHaveAttribute(
      "data-scale",
      "2.5",
    );
  });

  it("zoom-out clamps at 0.5 after repeated clicks", async () => {
    setup();
    const zoomOut = screen.getByRole("button", { name: /zoom out/i });
    for (let i = 0; i < 12; i++) await userEvent.click(zoomOut);
    expect(screen.getByTestId("zoom-group")).toHaveAttribute(
      "data-scale",
      "0.5",
    );
  });

  it("reset returns to the default scale", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /zoom in/i }));
    await userEvent.click(screen.getByRole("button", { name: /reset zoom/i }));
    expect(screen.getByTestId("zoom-group")).toHaveAttribute("data-scale", "1");
  });
});
