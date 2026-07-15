import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "@/test/utils";

describe("WorkstreamGraphPage", () => {
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
        name: /^edge contributes-to opres-pd-v0-3 to bcbs-opres-2021/,
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
