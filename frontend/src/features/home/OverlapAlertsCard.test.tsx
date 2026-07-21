import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { renderApp } from "@/test/utils";
import { server } from "@/test/msw/server";
import type { CrossLink } from "@/lib/types";

const UNTRIAGED_LINK: CrossLink = {
  id: "x-bcm_pd_2022--rrp_pd_v0_1",
  edge_type: "parallel-to",
  near: {
    node_id: "bcm-pd-2022",
    title: "BCM PD (19 Dec 2022)",
    workstream_id: "resolution-recovery",
  },
  far: {
    node_id: "rrp-pd-v0-1",
    title: "Recovery Planning PD — v0.1",
    workstream_id: "resolution-recovery",
    workstream_name: "Resolution & Recovery Planning",
  },
  findings_count: 22,
  labels: { "aligns-with": 11, "differs-on": 1, "silent-on": 6, "goes-beyond": 4 },
  counts: { total: 22, accepted: 0, dismissed: 0 },
};

describe("OverlapAlertsCard", () => {
  it("shows the reassuring empty state when nothing is untriaged", async () => {
    renderApp("/");
    const card = await screen.findByTestId("overlap-alerts-card");
    expect(
      within(card).getByText(/No overlaps detected yet/i),
    ).toBeInTheDocument();
  });

  it("surfaces an untriaged cross-workstream link with the FPWG framing", async () => {
    server.use(
      http.get("*/api/cross-links", () =>
        HttpResponse.json({ links: [UNTRIAGED_LINK] }),
      ),
    );
    renderApp("/");

    const card = await screen.findByTestId("overlap-alerts-card");
    expect(within(card).getByText(/Caught automatically/i)).toBeInTheDocument();
    const row = within(card).getByTestId("overlap-alert-row");
    expect(within(row).getByText(/BCM PD/)).toBeInTheDocument();
    expect(within(row).getByText(/Recovery Planning PD/)).toBeInTheDocument();
    expect(within(row).getByText(/22 linkages/)).toBeInTheDocument();
    expect(row).toHaveAttribute(
      "href",
      "/workstreams/_cross/edges/x-bcm_pd_2022--rrp_pd_v0_1/review",
    );
  });

  it("drops out once every link has been triaged", async () => {
    server.use(
      http.get("*/api/cross-links", () =>
        HttpResponse.json({
          links: [
            { ...UNTRIAGED_LINK, counts: { total: 22, accepted: 22, dismissed: 0 } },
          ],
        }),
      ),
    );
    renderApp("/");

    const card = await screen.findByTestId("overlap-alerts-card");
    expect(
      within(card).getByText(/No overlaps detected yet/i),
    ).toBeInTheDocument();
  });
});
