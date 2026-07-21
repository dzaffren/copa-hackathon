import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";

import { renderWithProviders } from "@/test/utils";
import { EdgeDetailPanel } from "./EdgeDetailPanel";

describe("EdgeDetailPanel", () => {
  it("unanalysed edge shows Analyze linkages and no finding cards", async () => {
    renderWithProviders(
      <EdgeDetailPanel
        workstreamId="opres-v2"
        edgeId="e-opres_v0_3--fsb_3rd_party"
      />,
      "/workstreams/opres-v2",
    );
    expect(
      await screen.findByRole("button", { name: /analyze linkages/i }),
    ).toBeInTheDocument();
    // No finding cards → no Review buttons.
    expect(screen.queryByRole("button", { name: /^review$/i })).toBeNull();
    expect(screen.getByText(/not analysed/i)).toBeInTheDocument();
  });

  it("analysed edge shows finding cards and no Analyze button", async () => {
    renderWithProviders(
      <EdgeDetailPanel
        workstreamId="opres-v2"
        edgeId="e-opres_v0_3--bcbs_opres_2021"
      />,
      "/workstreams/opres-v2",
    );
    const reviews = await screen.findAllByRole("button", { name: /^review$/i });
    expect(reviews).toHaveLength(3);
    expect(
      screen.queryByRole("button", { name: /analyze linkages/i }),
    ).toBeNull();
    expect(screen.getByText(/3 linkage\(s\)/i)).toBeInTheDocument();
  });

  it("disables Analyze when the edge is not analysable", async () => {
    // e-opres_v0_3--fsb_3rd_party: fsb-3rd-party has no document_id, so the
    // edge is not analysable even though it is unanalysed.
    renderWithProviders(
      <EdgeDetailPanel
        workstreamId="opres-v2"
        edgeId="e-opres_v0_3--fsb_3rd_party"
      />,
      "/workstreams/opres-v2",
    );
    const btn = await screen.findByRole("button", {
      name: /analyze linkages/i,
    });
    expect(btn).toBeDisabled();
  });
});
