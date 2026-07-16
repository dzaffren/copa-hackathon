import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";

async function loadGraph(workstreamId = "opres-v2") {
  renderApp(`/workstreams/${workstreamId}`);
  await screen.findByRole("button", { name: /add node/i });
}

describe("CrossWorkstreamPanel", () => {
  it("leads the idle rail with the linkage into the other workstream", async () => {
    await loadGraph();

    const panel = await screen.findByTestId("cross-workstream-panel");
    expect(
      within(panel).getByText(/OpRes DP \(Dec 2025\)/),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(/Open Finance ED — 18 Nov 2025/),
    ).toBeInTheDocument();
    expect(
      within(panel).getByText(/in Open Finance ED · 2025/),
    ).toBeInTheDocument();
  });

  it("tallies the findings by semantic label", async () => {
    await loadGraph();
    const panel = await screen.findByTestId("cross-workstream-panel");

    expect(within(panel).getByTestId("cross-link-count")).toHaveTextContent(
      "12 linkages",
    );
    expect(within(panel).getByText("6 aligns-with")).toBeInTheDocument();
    expect(within(panel).getByText("4 differs-on")).toBeInTheDocument();
    expect(within(panel).getByText("2 goes-beyond")).toBeInTheDocument();
  });

  it("routes into the ordinary review screen — no second reader", async () => {
    const user = userEvent.setup();
    await loadGraph();

    await user.click(await screen.findByTestId("cross-link-card"));

    expect(
      await screen.findByRole("heading", {
        name: /Open Finance ED — 18 Nov 2025 ↔ OpRes DP \(Dec 2025\)/,
      }),
    ).toBeInTheDocument();
  });

  it("reads the same link from the other workstream's end", async () => {
    await loadGraph("open-finance-ed");

    const panel = await screen.findByTestId("cross-workstream-panel");
    // near/far flip: from Open Finance, OpRes is the far side.
    expect(
      within(panel).getByText(/in Operational Resilience/),
    ).toBeInTheDocument();
  });

  it("stays out of the way when a workstream has no cross-links", async () => {
    await loadGraph("outsourcing-v2");
    expect(
      screen.queryByTestId("cross-workstream-panel"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/Select a node or edge to see its details/i),
    ).toBeInTheDocument();
  });
});
