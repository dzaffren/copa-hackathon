import { describe, it, expect } from "vitest";
import { screen, within, fireEvent } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { renderApp } from "@/test/utils";
import { server } from "@/test/msw/server";
import type { CrossLink } from "@/lib/types";

// The flagship scenario: BCM vs Resolution & Recovery Planning, detected early.
const FLAGSHIP: CrossLink = {
  id: "x-bcm_pd_2022--rrp_pd_v0_1",
  edge_type: "parallel-to",
  near: {
    node_id: "bcm-pd-2022",
    title: "BCM PD (19 Dec 2022)",
    workstream_id: "bcm",
    workstream_name: "Business Continuity Management",
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
  classification: "divergent",
  risk_level: "medium",
  detected_at: "2026-07-14",
  shared_attributes: {
    legal_basis: ["FSA 2013", "IFSA 2013"],
    applicability: ["licensed banks"],
    keywords: ["continuity of critical functions"],
    policy_owner: null,
    ismp_classification: null,
  },
  reasons: [
    "Both apply to licensed banks",
    "Both issued under FSA 2013 and IFSA 2013",
    "Both address continuity of critical functions",
  ],
};

function seedLinks(links: CrossLink[]) {
  server.use(
    http.get("*/api/cross-links", () => HttpResponse.json({ links })),
  );
}

describe("CrossIntelligencePage", () => {
  it("renders the early-warning header and summary metrics", async () => {
    seedLinks([FLAGSHIP]);
    renderApp("/intelligence");

    expect(
      await screen.findByRole("heading", {
        name: /Overlap, duplication & conflict/i,
      }),
    ).toBeInTheDocument();
    // Wait for the links query to settle (a card proves it loaded).
    await screen.findByTestId("relationship-card");

    // Potential overlaps metric reflects the one detected relationship.
    const overlaps = screen.getByText("Potential overlaps").closest("div")!;
    expect(within(overlaps).getByText("1")).toBeInTheDocument();
    // No genuine conflicts in this pair — the metric must not overstate.
    const conflicts = screen.getByText("High-risk conflicts").closest("div")!;
    expect(within(conflicts).getByText("0")).toBeInTheDocument();
  });

  it("lists the flagship relationship with its shared-attribute reasons", async () => {
    seedLinks([FLAGSHIP]);
    renderApp("/intelligence");

    const card = await screen.findByTestId("relationship-card");
    expect(within(card).getByText("Business Continuity Management")).toBeInTheDocument();
    expect(within(card).getByText("Resolution & Recovery Planning")).toBeInTheDocument();
    expect(within(card).getByText(/Divergent/i)).toBeInTheDocument();
    expect(within(card).getByText(/apply to licensed banks/i)).toBeInTheDocument();
  });

  it("shows why-detected reasons and verbatim clause evidence in the panel", async () => {
    seedLinks([FLAGSHIP]);
    renderApp("/intelligence");

    // The highest-risk relationship's panel is shown by default.
    const panel = await screen.findByTestId("relationship-panel");
    expect(within(panel).getByText(/Why this was detected/i)).toBeInTheDocument();
    // A reason line renders inside the panel (from the detail endpoint).
    expect(
      await within(panel).findByText(/issued under FSA 2013/i),
    ).toBeInTheDocument();
    // Verbatim clause evidence with its number, on both sides.
    expect(await within(panel).findByText("Open Finance 7.1")).toBeInTheDocument();
    expect(within(panel).getByText("Operational Resilience 6.3")).toBeInTheDocument();
  });

  it("filters relationships by classification", async () => {
    seedLinks([FLAGSHIP]);
    renderApp("/intelligence");

    // Present under "All"; a "Conflicts" filter should hide the divergent one.
    expect(await screen.findByTestId("relationship-card")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Conflicts" }));
    expect(screen.queryByTestId("relationship-card")).not.toBeInTheDocument();
    expect(screen.getByText(/No relationships match your filter/i)).toBeInTheDocument();
  });
});
