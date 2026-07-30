import { describe, it, expect, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import * as api from "@/lib/api";
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

async function attachFile(name = "bcbs-opres-2021.pdf") {
  const file = new File([new Uint8Array([1, 2, 3])], name, {
    type: "application/pdf",
  });
  await userEvent.upload(screen.getByLabelText("Attachment"), file);
  return file;
}

describe("AddNodeDialog", () => {
  it("Add to graph is disabled when there are no edge rows", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await attachFile();
    expect(
      screen.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });

  it("Add to graph re-enables after adding one complete edge row", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await attachFile();
    await addCompleteRow(1, "opres-pd-v0-3", "references");
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
  });

  it("removing rows below one disables Add to graph again", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await attachFile();
    await addCompleteRow(1, "opres-pd-v0-3", "references");
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Remove edge 1" }),
    );
    expect(
      screen.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });

  it("supports multiple edges and submits with the chosen method + file", async () => {
    // The multipart round-trip itself is NOT asserted here: a FormData `fetch`
    // never resolves under MSW v2 + jsdom (verified — a JSON POST to the same
    // handler returns 201 while a FormData POST hangs), so the request is
    // intercepted at `createNode` and the real round-trip is covered by
    // frontend/e2e/add-node-chunking.spec.ts in a browser.
    const createNode = vi
      .spyOn(api, "createNode")
      .mockResolvedValue({} as never);
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    const file = await attachFile();
    await addCompleteRow(1, "opres-pd-v0-3", "references");
    await addCompleteRow(2, "rmit-pd-2025", "parallel-to");
    await userEvent.click(screen.getByRole("radio", { name: "prose" }));
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
    await userEvent.click(
      screen.getByRole("button", { name: /add to graph/i }),
    );

    await waitFor(() => expect(createNode).toHaveBeenCalled());
    const [workstreamId, body, attachment] = createNode.mock.calls[0];
    expect(workstreamId).toBe("opres-v2");
    expect(body.doc_class).toBe("prose");
    expect(body.edges).toHaveLength(2);
    expect(attachment).toBe(file);
    createNode.mockRestore();
  });

  // --- breaking-up method (doc_class) ---------------------------------------

  it("offers exactly the three breaking-up methods, semi-structured by default", () => {
    renderDialog();
    const group = screen.getByRole("radiogroup", {
      name: "Breaking-up method",
    });
    const options = within(group).getAllByRole("radio");
    expect(options.map((o) => o.getAttribute("aria-label"))).toEqual([
      "semi-structured",
      "prose",
      "structured-rules",
    ]);
    expect(
      within(group).getByRole("radio", { name: "semi-structured" }),
    ).toBeChecked();
  });

  it("selecting a different method checks it and unchecks the previous", async () => {
    renderDialog();
    const group = screen.getByRole("radiogroup", {
      name: "Breaking-up method",
    });
    await userEvent.click(within(group).getByRole("radio", { name: "prose" }));
    expect(within(group).getByRole("radio", { name: "prose" })).toBeChecked();
    expect(
      within(group).getByRole("radio", { name: "semi-structured" }),
    ).not.toBeChecked();
  });

  it("Add to graph stays disabled without an attachment", async () => {
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "Companion Guide");
    await addCompleteRow(1, "opres-pd-v0-3", "references");
    expect(
      screen.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });

  // --- task type (deliverable kind) ----------------------------------------

  it("asks for a task type only once the node is a working draft", async () => {
    renderDialog();
    expect(
      screen.queryByRole("radiogroup", { name: "Task type" }),
    ).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("radio", { name: "task" }));

    const group = screen.getByRole("radiogroup", { name: "Task type" });
    const options = within(group).getAllByRole("radio");
    expect(options.map((o) => o.getAttribute("aria-label"))).toEqual([
      "PD",
      "DP",
      "ED",
      "FAQ",
      "DECK",
      "FEEDBACK",
      "BENCHMARK",
      "OTHERS",
    ]);
    // Nothing is preselected — the drafter must say which kind this is.
    expect(
      options.every((o) => o.getAttribute("aria-checked") === "false"),
    ).toBe(true);
  });

  it("never asks a published context document for a task type", async () => {
    renderDialog();
    for (const nodeType of [
      "international-standard",
      "act-law",
      "peer-regulator",
      "industry-input",
      "supervisory-letter",
      "internal-published",
      "others",
    ]) {
      await userEvent.click(screen.getByRole("radio", { name: nodeType }));
      expect(
        screen.queryByRole("radiogroup", { name: "Task type" }),
      ).not.toBeInTheDocument();
    }
  });

  it("keeps Add to graph disabled for a working draft with no kind picked", async () => {
    renderDialog();
    await userEvent.click(screen.getByRole("radio", { name: "task" }));
    await userEvent.type(screen.getByLabelText("Title"), "OpRes Briefing");
    await attachFile();
    await addCompleteRow(1, "opres-pd-v0-3", "references");

    // Everything else the server asks for is present; only the kind is missing.
    expect(
      screen.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();

    await userEvent.click(screen.getByRole("radio", { name: "DECK" }));
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
  });

  it("discards the kind when the drafter switches away from working draft", async () => {
    renderDialog();
    await userEvent.click(screen.getByRole("radio", { name: "task" }));
    await userEvent.click(screen.getByRole("radio", { name: "FAQ" }));
    await userEvent.click(
      screen.getByRole("radio", { name: "international-standard" }),
    );
    await userEvent.click(screen.getByRole("radio", { name: "task" }));

    const group = screen.getByRole("radiogroup", { name: "Task type" });
    expect(within(group).getByRole("radio", { name: "FAQ" })).not.toBeChecked();
  });

  it("sends task_type for a working draft", async () => {
    const createNode = vi
      .spyOn(api, "createNode")
      .mockResolvedValue({} as never);
    renderDialog();
    await userEvent.click(screen.getByRole("radio", { name: "task" }));
    await userEvent.click(screen.getByRole("radio", { name: "DECK" }));
    await userEvent.type(screen.getByLabelText("Title"), "OpRes Briefing");
    await attachFile();
    await addCompleteRow(1, "rmit-pd-2025", "references");
    await userEvent.click(
      screen.getByRole("button", { name: /add to graph/i }),
    );

    await waitFor(() => expect(createNode).toHaveBeenCalled());
    expect(createNode.mock.calls[0][1].task_type).toBe("DECK");
    createNode.mockRestore();
  });

  it("omits task_type entirely for a context document", async () => {
    const createNode = vi
      .spyOn(api, "createNode")
      .mockResolvedValue({} as never);
    renderDialog();
    await userEvent.type(screen.getByLabelText("Title"), "BCBS OpRes 2021");
    await attachFile();
    await addCompleteRow(1, "opres-pd-v0-3", "references");
    await userEvent.click(
      screen.getByRole("button", { name: /add to graph/i }),
    );

    await waitFor(() => expect(createNode).toHaveBeenCalled());
    // Absent, not null: the server rejects the key outright on a non-task node.
    expect(createNode.mock.calls[0][1]).not.toHaveProperty("task_type");
    createNode.mockRestore();
  });

  // --- first document on a brand-new workstream ----------------------------

  it("pre-fills the edge row when the focal node is the only target", async () => {
    const focalOnly: GraphNode[] = [NODES[0]];
    renderWithProviders(
      <AddNodeDialog
        workstreamId="opres-v2"
        nodes={focalOnly}
        open
        onOpenChange={vi.fn()}
      />,
    );

    // The row exists already, pointing at the one legal target.
    expect(screen.getByLabelText("Edge 1 target")).toHaveValue("opres-pd-v0-3");
    expect(screen.getByLabelText("Edge 1 type")).toHaveValue("references");

    // So title + attachment is all that stands between here and submitting.
    await userEvent.type(screen.getByLabelText("Title"), "BCBS OpRes 2021");
    await attachFile();
    expect(screen.getByRole("button", { name: /add to graph/i })).toBeEnabled();
  });

  it("does not pre-fill when several targets exist", () => {
    renderDialog(); // NODES has two entries
    expect(screen.queryByLabelText("Edge 1 target")).not.toBeInTheDocument();
    // The empty-state hint stands in for the row the drafter must add. (The
    // same sentence is also in the dialog description, hence getAllByText.)
    expect(
      screen.getAllByText(/at least one edge to an existing node is required/i)
        .length,
    ).toBeGreaterThan(0);
  });
});
