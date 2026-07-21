import { useState } from "react";
import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderWithProviders } from "@/test/utils";
import { server } from "@/test/msw/server";
import type { NodeDetail } from "@/lib/types";
import { NodeDetailPanel } from "./NodeDetailPanel";

/** An offline-enriched supervisory letter: distinct doc type, a multi-Act legal
 *  basis, and an ISMP classification that has no offline source yet. */
const ENRICHED_SUPERVISORY_LETTER: NodeDetail = {
  id: "bnm-supervisory-letter-rmit-2025",
  node_type: "supervisory-letter",
  title: "Supervisory Letter — RMiT Implementation Guidance",
  issuer: "BNM",
  short_type: "Supervisory Letter",
  description: "Implementation guidance on RMiT.",
  source_url: null,
  ismp_classification: null,
  pursuant_to: null,
  first_order_neighbours: [],
  second_order_neighbours: { status: "placeholder", message: "N/A in demo" },
  recent_activity: [],
  concepts: {
    status: "available",
    policy_owner: null,
    applicability: "Financial institutions subject to the RMiT policy document",
    empowerment_framework: null,
    requirement: null,
    issuance_date: null,
    effective_date: null,
    keywords: ["RMiT", "implementation guidance", "technology risk"],
    legal_basis: ["FSA 2013", "IFSA 2013", "DFIA 2002"],
    ismp_classification: null,
  },
};

function seedNode(detail: NodeDetail) {
  server.use(
    http.get("*/api/workstreams/:workstreamId/nodes/:nodeId", () =>
      HttpResponse.json(detail),
    ),
  );
}

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

  it("distinguishes a supervisory letter and surfaces its legal basis + ISMP", async () => {
    seedNode(ENRICHED_SUPERVISORY_LETTER);
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="rmit-v2-2025"
        nodeId="bnm-supervisory-letter-rmit-2025"
        onSelectNode={() => {}}
      />,
      "/workstreams/rmit-v2-2025",
    );

    // The document type is visually distinguished by its own badge.
    expect(await screen.findByText("supervisory-letter")).toBeInTheDocument();
    // Legal basis (multi-Act) is surfaced first-class, not hidden in a disclosure.
    expect(screen.getByText(/Legal basis: FSA 2013, IFSA 2013, DFIA 2002/)).toBeInTheDocument();
    // ISMP is supported but honestly pending — no fabricated classification.
    expect(screen.getByText(/ISMP: Pending — RH publication form/)).toBeInTheDocument();
  });

  it("renders keyword + legal-basis concept chips in the Concepts disclosure", async () => {
    seedNode(ENRICHED_SUPERVISORY_LETTER);
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="rmit-v2-2025"
        nodeId="bnm-supervisory-letter-rmit-2025"
        onSelectNode={() => {}}
      />,
      "/workstreams/rmit-v2-2025",
    );

    await screen.findByText("supervisory-letter");
    await userEvent.click(screen.getByRole("button", { name: /concepts/i }));

    // Keywords render as individual chips.
    expect(await screen.findByText("implementation guidance")).toBeInTheDocument();
    expect(screen.getByText("technology risk")).toBeInTheDocument();
    // The ISMP row inside the disclosure also shows the pending state.
    expect(
      screen.getAllByText(/Pending — RH publication form/).length,
    ).toBeGreaterThan(0);
  });
});
