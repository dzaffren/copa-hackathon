import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "@/test/utils";

describe("WorkstreamGraphPage", () => {
  it("rests the rail on the focal task node with nothing selected", async () => {
    renderApp("/workstreams/opres-v2");

    const rail = await screen.findByTestId("graph-detail-rail");
    // The working draft's detail, unprompted — and no close button, because
    // there is nothing behind it to close back to.
    expect(
      await within(rail).findByText(/Operational Resilience PD/),
    ).toBeInTheDocument();
    expect(
      within(rail).queryByRole("button", { name: /close panel/i }),
    ).not.toBeInTheDocument();
  });

  it("falls back to the prompt when a workstream has no focal task", async () => {
    renderApp("/workstreams/outsourcing-v2");
    expect(
      await screen.findByText(/Select a node or edge to see its details/i),
    ).toBeInTheDocument();
  });

  it("renders the seeded canvas and opens node then edge detail", async () => {
    renderApp("/workstreams/opres-v2");

    // Nodes render on the canvas (accessible name = node title).
    const bcbsNode = await screen.findByRole("button", {
      name: "BCBS OpRes 2021",
    });
    expect(bcbsNode).toBeInTheDocument();

    // Click BCBS node → resource node detail with Open source.
    await userEvent.click(bcbsNode);
    expect(
      await screen.findByRole("button", { name: /open source/i }),
    ).toBeInTheDocument();

    // Click the analysed BCBS edge → three finding cards, no Analyze CTA.
    await userEvent.click(
      screen.getByRole("button", {
        name: /^edge references opres-pd-v0-3 to bcbs-opres-2021/,
      }),
    );
    expect(
      await screen.findAllByRole("button", { name: /^review$/i }),
    ).toHaveLength(3);
  });

  it("opens the Add node dialog with Add to graph disabled", async () => {
    renderApp("/workstreams/opres-v2");
    await userEvent.click(
      await screen.findByRole("button", { name: /add node/i }),
    );
    expect(
      await screen.findByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });
});
