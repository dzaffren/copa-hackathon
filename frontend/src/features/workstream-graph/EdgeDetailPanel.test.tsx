import { describe, it, expect, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { server } from "@/test/msw/server";

import { renderWithProviders } from "@/test/utils";
import { LABEL_ORDER } from "@/lib/labels";
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
    // No cards to explain, so no heading and no legend either.
    expect(
      screen.queryByRole("heading", { name: "Pairwise findings" }),
    ).toBeNull();
    expect(screen.queryByTestId("label-legend-trigger")).toBeNull();
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
    // Headed like the task screen's box, so the taxonomy is explained wherever
    // these cards appear rather than only on one screen.
    expect(
      screen.getByRole("heading", { name: "Pairwise findings" }),
    ).toBeInTheDocument();
  });

  it("explains the labels from the edge panel's own legend", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <EdgeDetailPanel
        workstreamId="opres-v2"
        edgeId="e-opres_v0_3--bcbs_opres_2021"
      />,
      "/workstreams/opres-v2",
    );
    await screen.findAllByRole("button", { name: /^review$/i });

    await user.hover(screen.getByTestId("label-legend-trigger"));

    const legend = await screen.findByTestId("label-legend");
    for (const label of LABEL_ORDER) {
      expect(within(legend).getByText(label)).toBeInTheDocument();
    }
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

  // --- delete linkage -------------------------------------------------------

  it("takes two clicks to delete, and says the documents stay", async () => {
    const onClose = vi.fn();
    renderWithProviders(
      <EdgeDetailPanel
        workstreamId="opres-v2"
        edgeId="e-opres_v0_3--bcbs_opres_2021"
        onClose={onClose}
      />,
      "/workstreams/opres-v2",
    );

    await userEvent.click(
      await screen.findByRole("button", { name: /delete linkage/i }),
    );
    // The confirmation is explicit that only the connection goes.
    expect(screen.getByText(/both documents stay/i)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();

    let called = false;
    server.use(
      http.delete("*/api/workstreams/:ws/edges/:edgeId", () => {
        called = true;
        return HttpResponse.json({ id: "e-opres_v0_3--bcbs_opres_2021" });
      }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^delete$/i }));

    await waitFor(() => expect(called).toBe(true));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("cancelling leaves the linkage alone", async () => {
    renderWithProviders(
      <EdgeDetailPanel
        workstreamId="opres-v2"
        edgeId="e-opres_v0_3--bcbs_opres_2021"
      />,
      "/workstreams/opres-v2",
    );

    await userEvent.click(
      await screen.findByRole("button", { name: /delete linkage/i }),
    );
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.queryByText(/both documents stay/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /delete linkage/i }),
    ).toBeInTheDocument();
  });
});
