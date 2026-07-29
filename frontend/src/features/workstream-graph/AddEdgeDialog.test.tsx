import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderWithProviders } from "@/test/utils";
import { server } from "@/test/msw/server";
import { AddEdgeDialog } from "./AddEdgeDialog";
import type { GraphNode } from "@/lib/types";

const NODES: GraphNode[] = [
  {
    id: "bcbs-opres-2021",
    node_type: "international-standard",
    title: "BCBS OpRes 2021",
    issuer: "BCBS",
    short_type: "Standard",
  },
  {
    id: "hkma-spm-or2",
    node_type: "peer-regulator",
    title: "HKMA SPM OR-2",
    issuer: "HKMA",
    short_type: "SPM",
  },
];

function renderDialog(nodes = NODES, onOpenChange = vi.fn()) {
  renderWithProviders(
    <AddEdgeDialog
      workstreamId="opres-v2"
      sourceNodeId="bcbs-opres-2021"
      nodes={nodes}
      open
      onOpenChange={onOpenChange}
    />,
  );
  return { onOpenChange };
}

function seedCreateEdge(status = 201, body?: unknown) {
  server.use(
    http.post("*/api/workstreams/:workstreamId/edges", () =>
      HttpResponse.json(
        body ?? {
          id: "e-bcbs_opres_2021--hkma_spm_or2",
          source: "bcbs-opres-2021",
          target: "hkma-spm-or2",
          edge_type: "references",
          analysed: false,
        },
        { status },
      ),
    ),
  );
}

describe("AddEdgeDialog", () => {
  it("does not offer the viewed node as a target (no self-connection)", () => {
    renderDialog();
    const options = screen
      .getByLabelText("Connect to")
      .querySelectorAll("option");
    const values = Array.from(options).map((o) => o.getAttribute("value"));
    expect(values).not.toContain("bcbs-opres-2021");
    expect(values).toContain("hkma-spm-or2");
  });

  it("Add edge is disabled until a target and a type are chosen", async () => {
    renderDialog();
    const submit = screen.getByRole("button", { name: /^add edge$/i });
    expect(submit).toBeDisabled();

    await userEvent.selectOptions(
      screen.getByLabelText("Connect to"),
      "hkma-spm-or2",
    );
    expect(submit).toBeDisabled();

    await userEvent.selectOptions(
      screen.getByLabelText("Connection type"),
      "references",
    );
    expect(submit).toBeEnabled();
  });

  it("offers all three connection types", () => {
    renderDialog();
    const options = screen
      .getByLabelText("Connection type")
      .querySelectorAll("option");
    const values = Array.from(options)
      .map((o) => o.getAttribute("value"))
      .filter(Boolean);
    expect(values).toEqual(["supersedes", "references", "parallel-to"]);
  });

  it("creates the connection and closes", async () => {
    seedCreateEdge();
    const { onOpenChange } = renderDialog();

    await userEvent.selectOptions(
      screen.getByLabelText("Connect to"),
      "hkma-spm-or2",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Connection type"),
      "references",
    );
    await userEvent.click(screen.getByRole("button", { name: /^add edge$/i }));

    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });

  it("explains a duplicate connection instead of closing", async () => {
    seedCreateEdge(409, {
      code: "DUPLICATE_EDGE",
      message:
        "A references connection already exists between these two documents.",
    });
    const { onOpenChange } = renderDialog();

    await userEvent.selectOptions(
      screen.getByLabelText("Connect to"),
      "hkma-spm-or2",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Connection type"),
      "references",
    );
    await userEvent.click(screen.getByRole("button", { name: /^add edge$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /already exists/i,
    );
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
  });

  it("says so when the workstream has nothing else to connect to", () => {
    renderDialog([NODES[0]]);
    expect(
      screen.getByText(/no other documents in this workstream/i),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Connect to")).not.toBeInTheDocument();
  });
});
