import { useState } from "react";
import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderWithProviders } from "@/test/utils";
import { server } from "@/test/msw/server";
import type { NodeDetail } from "@/lib/types";
import { NodeDetailPanel } from "./NodeDetailPanel";

/** An offline-enriched supervisory letter: distinct doc type, a multi-Act legal
 *  provision, and an ISMP classification that has no offline source yet. */
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
  concepts: { status: "not_extracted", axes: [] },
  metadata: {
    status: "available",
    policy_owner: null,
    applicability: "Financial institutions subject to the RMiT policy document",
    legal_provision: ["FSA 2013", "IFSA 2013", "DFIA 2002"],
    issuance_date: null,
    effective_date: null,
    policy_requirement: null,
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

  it("distinguishes a supervisory letter, and keeps its profile in one place", async () => {
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

    // Legal provision and ISMP no longer repeat as badges under the title —
    // they are rows in the Metadata disclosure, which is also where they can be
    // edited. Two copies meant the drafter could read a value where she could
    // not change it.
    expect(screen.queryByText(/Legal provision: FSA 2013/)).toBeNull();
    expect(screen.queryByText(/ISMP: Pending/)).toBeNull();
  });

  it("shows the deliverable kind as a chip, by label not code", async () => {
    seedNode({
      ...ENRICHED_SUPERVISORY_LETTER,
      id: "opres-industry-briefing",
      node_type: "task",
      task_type: "DECK",
      title: "OpRes Industry Briefing",
    });
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="opres-industry-briefing"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    // The drafter reads "Engagement Deck", never the stored "DECK".
    expect(await screen.findByTestId("task-type-chip")).toHaveTextContent(
      "Engagement Deck",
    );
  });

  it("shows no deliverable chip for a published context document", async () => {
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="bcbs-opres-2021"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    await screen.findByText("international-standard");
    expect(screen.queryByTestId("task-type-chip")).not.toBeInTheDocument();
  });

  it("renders legal-provision chips in the Metadata disclosure", async () => {
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
    await userEvent.click(screen.getByRole("button", { name: /metadata/i }));

    // A multi-value field renders as individual chips.
    expect(await screen.findByText("Legal provision")).toBeInTheDocument();
    // The ISMP row inside the disclosure also shows the pending state.
    expect(
      screen.getAllByText(/Pending — RH publication form/).length,
    ).toBeGreaterThan(0);
  });

  it("offers a fillable profile, not a dead end, on a node nobody prepared", async () => {
    // The seeded BCBS node has no side-file, so its metadata arrives as the
    // placeholder shape the four other consumers still read.
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="bcbs-opres-2021"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    await screen.findByText("international-standard");
    await userEvent.click(screen.getByRole("button", { name: /^metadata$/i }));

    // Every field is named and honestly empty — six "Not set" plus the ISMP
    // row, which is pending rather than merely unfilled.
    expect(screen.getAllByText("Not set")).toHaveLength(6);
    expect(screen.getByText("Policy owner")).toBeInTheDocument();
    expect(screen.getByText("ISMP classification")).toBeInTheDocument();
    expect(
      screen.getByText(/Pending — RH publication form/),
    ).toBeInTheDocument();
    // The MVP1 apology must never reach the drafter again.
    expect(
      screen.queryByText(/concept extraction not enabled/i),
    ).not.toBeInTheDocument();
  });

  it("Edit turns the profile into a form and a save shows the new values", async () => {
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="bcbs-opres-2021"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    await screen.findByText("international-standard");
    await userEvent.click(screen.getByRole("button", { name: /^edit$/i }));

    // Read mode's flat values are replaced by inputs.
    const owner = screen.getByLabelText("Policy owner");
    await userEvent.type(owner, "Priya S.");
    await userEvent.type(
      screen.getByLabelText("Legal provision"),
      "FSA 2013, IFSA 2013",
    );
    await userEvent.click(screen.getByRole("button", { name: /^save$/i }));

    // Back to read mode, showing what she saved — the panel refetched the node.
    await waitFor(() =>
      expect(screen.queryByLabelText("Policy owner")).not.toBeInTheDocument(),
    );
    expect(await screen.findByText("Priya S.")).toBeInTheDocument();
    // The comma-separated line came back as separate chips.
    expect(screen.getByText("FSA 2013")).toBeInTheDocument();
    expect(screen.getByText("IFSA 2013")).toBeInTheDocument();
  });

  it("lists a working draft's deliverable kind on its profile, uneditable", async () => {
    seedNode({
      ...ENRICHED_SUPERVISORY_LETTER,
      id: "rmit-faq-v1",
      node_type: "task",
      task_type: "FAQ",
      title: "RMiT FAQ — v1",
    });
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="rmit-v2-2025"
        nodeId="rmit-faq-v1"
        onSelectNode={() => {}}
      />,
      "/workstreams/rmit-v2-2025",
    );

    await screen.findByText("task");
    await userEvent.click(screen.getByRole("button", { name: /^metadata$/i }));

    // The first row of the profile, reading the drafter-facing label. "FAQ" now
    // appears twice: the badge-row chip and this profile row.
    expect(screen.getByText("Task type")).toBeInTheDocument();
    expect(screen.getAllByText("FAQ")).toHaveLength(2);

    // It stays static text in edit mode — set once at creation, never an input.
    await userEvent.click(screen.getByRole("button", { name: /^edit$/i }));
    expect(screen.getByText("Task type")).toBeInTheDocument();
    expect(screen.queryByLabelText("Task type")).not.toBeInTheDocument();
    // Every other field is still editable.
    expect(screen.getByLabelText("Policy owner")).toBeEnabled();
  });

  it("shows no Task type row on a published context document", async () => {
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="bcbs-opres-2021"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    await screen.findByText("international-standard");
    await userEvent.click(screen.getByRole("button", { name: /^metadata$/i }));

    // A standard is never asked what kind of deliverable it is.
    expect(screen.queryByText("Task type")).not.toBeInTheDocument();
    expect(screen.getByText("Policy owner")).toBeInTheDocument();
  });

  it("abandoning a profile edit changes nothing", async () => {
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
    await userEvent.click(screen.getByRole("button", { name: /^edit$/i }));
    const applicability = screen.getByLabelText("Applicability");
    await userEvent.clear(applicability);
    await userEvent.type(applicability, "Everyone");
    await userEvent.click(screen.getByRole("button", { name: /^cancel$/i }));

    // Read mode returns with the stored value, not the typed one.
    expect(screen.queryByLabelText("Applicability")).not.toBeInTheDocument();
    expect(
      screen.getByText(
        "Financial institutions subject to the RMiT policy document",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Everyone")).not.toBeInTheDocument();
  });

  it("keeps the Edit button out of the disclosure toggle", async () => {
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="bcbs-opres-2021"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    await screen.findByText("international-standard");
    const edit = screen.getByRole("button", { name: /^edit$/i });
    // A button nested inside a button is invalid HTML and breaks keyboard
    // activation of both, so the two must be siblings.
    expect(edit.parentElement?.closest("button")).toBeNull();
    expect(
      screen.getByRole("button", { name: /^metadata$/i }).contains(edit),
    ).toBe(false);
  });

  // --- Concepts (extracted axes) -------------------------------------------

  it("shows the four sections in order: neighbours, activity, metadata, concepts", async () => {
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
    const headings = screen
      .getAllByText(
        /^(first-order neighbours|recent activity|metadata|concepts)$/i,
      )
      .map((el) => el.textContent?.trim().toLowerCase());

    expect(headings).toEqual([
      "first-order neighbours",
      "recent activity",
      "metadata",
      "concepts",
    ]);
  });

  it("offers Extract concepts when none are extracted yet", async () => {
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
    expect(screen.getByText(/no concepts extracted yet/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /extract concepts/i }),
    ).toBeEnabled();
    expect(screen.queryAllByTestId("concept-pill")).toHaveLength(0);
  });

  it("renders extracted axes as pills and drops the Extract button", async () => {
    seedNode({
      ...ENRICHED_SUPERVISORY_LETTER,
      concepts: {
        status: "extracted",
        axes: ["scenario testing cadence", "third-party dependency management"],
      },
    });
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="rmit-v2-2025"
        nodeId="bnm-supervisory-letter-rmit-2025"
        onSelectNode={() => {}}
      />,
      "/workstreams/rmit-v2-2025",
    );

    expect(
      await screen.findByText("scenario testing cadence"),
    ).toBeInTheDocument();
    expect(screen.getAllByTestId("concept-pill")).toHaveLength(2);
    expect(
      screen.queryByRole("button", { name: /extract concepts/i }),
    ).not.toBeInTheDocument();
  });

  it("surfaces a retryable message when extraction fails", async () => {
    seedNode(ENRICHED_SUPERVISORY_LETTER);
    server.use(
      http.post("*/api/workstreams/:ws/nodes/:nodeId/extract-concepts", () =>
        HttpResponse.json(
          { code: "EXTRACTION_FAILED", message: "Concept extraction failed" },
          { status: 502 },
        ),
      ),
    );
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="rmit-v2-2025"
        nodeId="bnm-supervisory-letter-rmit-2025"
        onSelectNode={() => {}}
      />,
      "/workstreams/rmit-v2-2025",
    );

    await screen.findByText("supervisory-letter");
    await userEvent.click(
      screen.getByRole("button", { name: /extract concepts/i }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /concept extraction failed/i,
    );
    expect(screen.queryAllByTestId("concept-pill")).toHaveLength(0);
  });

  // --- delete node ----------------------------------------------------------

  it("takes two clicks to delete, and names what will be lost", async () => {
    seedNode(ENRICHED_SUPERVISORY_LETTER);
    const onClose = vi.fn();
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="rmit-v2-2025"
        nodeId="bnm-supervisory-letter-rmit-2025"
        onSelectNode={() => {}}
        onClose={onClose}
      />,
      "/workstreams/rmit-v2-2025",
    );

    await screen.findByText("supervisory-letter");
    // First click only arms it — nothing is deleted yet.
    await userEvent.click(screen.getByRole("button", { name: /delete node/i }));
    expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();

    let called = false;
    server.use(
      http.delete("*/api/workstreams/:ws/nodes/:nodeId", () => {
        called = true;
        return HttpResponse.json({ id: "x", removed_edges: [] });
      }),
    );
    await userEvent.click(screen.getByRole("button", { name: /^delete$/i }));

    await waitFor(() => expect(called).toBe(true));
    // The node is gone, so the panel describing it closes.
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("cancelling the confirmation deletes nothing", async () => {
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
    await userEvent.click(screen.getByRole("button", { name: /delete node/i }));
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.queryByText(/cannot be undone/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /delete node/i }),
    ).toBeInTheDocument();
  });

  it("does not offer delete for the focal task node", async () => {
    // The seeded opres task node comes from the default MSW handler.
    renderWithProviders(
      <NodeDetailPanel
        workstreamId="opres-v2"
        nodeId="opres-pd-v0-3"
        onSelectNode={() => {}}
      />,
      "/workstreams/opres-v2",
    );

    await screen.findByRole("button", { name: /open task/i });
    expect(
      screen.queryByRole("button", { name: /delete node/i }),
    ).not.toBeInTheDocument();
  });
});
