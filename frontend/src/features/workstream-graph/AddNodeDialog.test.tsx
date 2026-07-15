import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderWithProviders } from "@/test/utils";
import { AddNodeDialog } from "./AddNodeDialog";
import type { GraphNode } from "@/lib/types";

const NODES: GraphNode[] = [
  {
    id: "opres-pd-v0-3",
    node_type: "task",
    title: "Operational Resilience PD — v0.3",
    issuer: "BNM",
    short_type: "PD (draft)",
  },
  {
    id: "rmit-pd-2025",
    node_type: "internal-published",
    title: "RMiT PD (28 Nov 2025)",
    issuer: "BNM",
    short_type: "PD (in force)",
  },
];

function renderDialog(onOpenChange = vi.fn()) {
  renderWithProviders(
    <AddNodeDialog
      workstreamId="opres-v2"
      nodes={NODES}
      open
      onOpenChange={onOpenChange}
    />,
  );
  return { onOpenChange };
}

async function addCompleteRow(index: number, target: string, type: string) {
  await userEvent.click(screen.getByRole("button", { name: /add edge/i }));
  await userEvent.selectOptions(
    screen.getByLabelText(`Edge ${index} target`),
    target,
  );
  await userEvent.selectOptions(
    screen.getByLabelText(`Edge ${index} type`),
    type,
  );
}

describe("AddNodeDialog", () => {
  it("Add to graph is disabled when there are no edge rows", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    expect(
      screen.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });

  it("Add to graph re-enables after adding one complete edge row", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await addCompleteRow(1, "opres-pd-v0-3", "contributes-to");
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
  });

  it("removing rows below one disables Add to graph again", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await addCompleteRow(1, "opres-pd-v0-3", "contributes-to");
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Remove edge 1" }),
    );
    expect(
      screen.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });

  it("supports multiple edges and submits then closes", async () => {
    const { onOpenChange } = renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await addCompleteRow(1, "opres-pd-v0-3", "contributes-to");
    await addCompleteRow(2, "rmit-pd-2025", "parallel-to");
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
    await userEvent.click(
      screen.getByRole("button", { name: /add to graph/i }),
    );
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false));
  });
});
