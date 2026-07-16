import { useState } from "react";
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderWithProviders } from "@/test/utils";
import { NodeDetailPanel } from "./NodeDetailPanel";

describe("NodeDetailPanel", () => {
  it("action button reads Open task for a task node", async () => {
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="opres-pd-v0-3"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );
    expect(
      await screen.findByRole("button", { name: /open task/i }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /open source/i })).toBeNull();
  });

  it("action button reads Open source for a resource node", async () => {
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="bcbs-opres-2021"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );
    expect(
      await screen.findByRole("button", { name: /open source/i }),
    ).toBeInTheDocument();
  });

  it("re-renders with the clicked neighbour's data when nodeId changes", async () => {
    function Harness() {
      const [nodeId, setNodeId] = useState("opres-pd-v0-3");
      return (
        <NodeDetailPanel
          workstreamId="opres-v2"
          nodeId={nodeId}
          onSelectNode={setNodeId}
        />
      );
    }
    renderWithProviders(<Harness />, "/workstreams/opres-v2");

    // Task node first: Open task action + HKMA available as a neighbour chip.
    expect(
      await screen.findByRole("heading", {
        name: /Operational Resilience PD/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /open task/i }),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: "HKMA SPM OR-2" }),
    );

    // Panel refocuses on HKMA → its heading + an Open source action.
    expect(
      await screen.findByRole("heading", { name: "HKMA SPM OR-2" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /open source/i }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /open task/i })).toBeNull();
  });
});
