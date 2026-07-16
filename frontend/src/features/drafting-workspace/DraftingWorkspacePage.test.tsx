import { describe, it, expect } from "vitest";
import { cleanup, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";

const DRAFT_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-3/draft";
const BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021";

async function loadWorkspace() {
  renderApp(DRAFT_URL);
  // The editor shell mounts before its queries resolve, so waiting on
  // draft-surface alone races the draft and task fetches. Wait for the saved
  // draft to actually be in the DOM.
  await screen.findByTestId("draft-surface");
  await waitFor(() =>
    expect(screen.getByTestId("draft-surface")).toHaveTextContent(
      /at least annually/,
    ),
  );
  await screen.findByRole("heading", {
    name: "Operational Resilience PD — v0.3",
  });
}

/** Accept a finding the way a drafter does — on the review screen — so the
 *  Reviewed tab is populated by the real path rather than a seeded fixture. */
async function acceptOnReviewScreen(user: ReturnType<typeof userEvent.setup>) {
  renderApp(`/workstreams/opres-v2/edges/${BCBS_EDGE}/review`);
  const card = (await screen.findAllByTestId("finding-card"))[0];
  await user.click(within(card).getByRole("button", { name: "Accept" }));
  await waitFor(() =>
    expect(screen.getByTestId("count-accepted")).toHaveTextContent(
      "1 accepted",
    ),
  );
  // Unmount before the workspace renders: two mounted apps would both answer
  // `screen`. The accepted state survives because the MSW handlers hold it in a
  // module-level map (cleared per-test in setup.ts) — exactly as the real
  // file-backed store survives a page navigation.
  cleanup();
}

describe("DraftingWorkspacePage — landing", () => {
  it("renders the draft surface, the three tabs, and the breadcrumb", async () => {
    await loadWorkspace();

    expect(
      screen.getByRole("heading", { name: "Operational Resilience PD — v0.3" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Workstream graph/i }),
    ).toBeInTheDocument();
    for (const name of [/Reviewed/, /Related · 1 hop/, /Copilot/]) {
      expect(screen.getByRole("tab", { name })).toBeInTheDocument();
    }
  });

  it("opens on the Reviewed tab", async () => {
    await loadWorkspace();
    expect(screen.getByRole("tab", { name: /Reviewed/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
  });

  it("shows the working draft's clause text verbatim in the editor", async () => {
    await loadWorkspace();
    expect(screen.getByTestId("draft-surface")).toHaveTextContent(
      "A financial institution shall conduct scenario testing of its operational resilience arrangements at least annually.",
    );
  });

  it("shows an auto-save indicator", async () => {
    await loadWorkspace();
    expect(screen.getByTestId("autosave-indicator")).toHaveTextContent(
      /Auto-saved \d+s ago/,
    );
  });
});

describe("DraftingWorkspacePage — Reviewed tab", () => {
  it("is empty until something is accepted, and says why", async () => {
    await loadWorkspace();
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("0");
    expect(screen.getByText(/No accepted linkages yet/i)).toBeInTheDocument();
  });

  it("shows a linkage accepted on the review screen, and counts it", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);

    await loadWorkspace();

    const cards = await screen.findAllByTestId("linkage-ref-card");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveAttribute("data-label", "aligns-with");
    expect(cards[0]).toHaveTextContent("BCBS OpRes 2021");
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("1");
  });

  it("does not show a dismissed finding", async () => {
    const user = userEvent.setup();
    renderApp(`/workstreams/opres-v2/edges/${BCBS_EDGE}/review`);
    const card = (await screen.findAllByTestId("finding-card"))[0];
    await user.click(within(card).getByRole("button", { name: "Dismiss" }));
    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );
    cleanup();

    await loadWorkspace();

    expect(screen.queryByTestId("linkage-ref-card")).not.toBeInTheDocument();
    expect(screen.getByTestId("count-reviewed")).toHaveTextContent("0");
  });

  it("highlights a clicked card and leaves the others alone", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);
    await loadWorkspace();

    const card = (await screen.findAllByTestId("linkage-ref-card"))[0];
    await user.click(card);
    expect(card).toHaveAttribute("data-active", "true");
  });

  it("renders an inline callout beside the accepted clause, colour-coded", async () => {
    const user = userEvent.setup();
    await acceptOnReviewScreen(user);
    await loadWorkspace();

    const callout = await screen.findByTestId("inline-callout");
    expect(callout).toHaveAttribute("data-label", "aligns-with");
    expect(callout).toHaveAttribute("data-clause", "4.4");
    expect(callout.className).toContain("border-emerald-400");
  });
});

describe("DraftingWorkspacePage — Related · 1 hop tab", () => {
  it("explains the tab and reports honestly that nothing is analysed", async () => {
    const user = userEvent.setup();
    await loadWorkspace();

    await user.click(screen.getByRole("tab", { name: /Related · 1 hop/ }));

    expect(
      screen.getByText(/neighbour documents themselves/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("related-empty")).toBeInTheDocument();
    expect(screen.getByTestId("count-related")).toHaveTextContent("0");
  });
});

describe("DraftingWorkspacePage — Copilot tab", () => {
  it("offers all seven intent presets", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    const select = screen.getByLabelText("Intent preset");
    expect(within(select).getAllByRole("option")).toHaveLength(7);
    expect(select).toHaveValue("PD");
  });

  it("echoes the drafter's message and answers from the script", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    await user.type(screen.getByLabelText("Message the Copilot"), "draft 6.3");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByTestId("chat-user")).toHaveTextContent(
      "draft 6.3",
    );
    expect(await screen.findByTestId("chat-copilot")).toHaveTextContent(
      /accountable-officer preamble/i,
    );
  });

  it("quotes RMiT 9.4 verbatim, with its clause number, on the snippet turn", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    const input = screen.getByLabelText("Message the Copilot");

    await user.type(input, "yes");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByTestId("chat-copilot");
    await user.type(input, "go on");
    await user.click(screen.getByRole("button", { name: "Send" }));

    const citation = await screen.findByTestId("copilot-citation");
    expect(citation).toHaveTextContent("RMiT 9.4");
    expect(citation).toHaveTextContent(
      /must designate a Chief Information Security \(CISO\) by whatever name called/,
    );
  });

  it("changing the intent preset restarts the conversation", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    await user.type(screen.getByLabelText("Message the Copilot"), "hi");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByTestId("chat-copilot");

    await user.selectOptions(screen.getByLabelText("Intent preset"), "FAQ");

    expect(screen.queryByTestId("chat-user")).not.toBeInTheDocument();
    expect(screen.queryByTestId("chat-copilot")).not.toBeInTheDocument();
  });
});

describe("DraftingWorkspacePage — inserting a Copilot snippet", () => {
  async function reachSnippet(user: ReturnType<typeof userEvent.setup>) {
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    const input = screen.getByLabelText("Message the Copilot");
    await user.type(input, "yes");
    await user.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByTestId("chat-copilot");
    await user.type(input, "go on");
    await user.click(screen.getByRole("button", { name: "Send" }));
    return screen.findByRole("button", { name: "Insert into draft" });
  }

  it("puts the snippet in the editor, marked as generated", async () => {
    const user = userEvent.setup();
    const insert = await reachSnippet(user);

    await user.click(insert);

    const surface = screen.getByTestId("draft-surface");
    await waitFor(() =>
      expect(surface).toHaveTextContent(
        /designate a single accountable officer/i,
      ),
    );
    // The provenance mark is the whole point: a reader must be able to tell
    // which text the drafter did not write.
    expect(surface.querySelector(".copilot-snippet")).not.toBeNull();
  });

  it("keeps the drafter's existing text", async () => {
    const user = userEvent.setup();
    const insert = await reachSnippet(user);
    await user.click(insert);

    await waitFor(() =>
      expect(screen.getByTestId("draft-surface")).toHaveTextContent(
        /at least annually/,
      ),
    );
  });
});

describe("DraftingWorkspacePage — tab switching", () => {
  it("does not unmount the editor, so the draft survives a round trip", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    const before = screen.getByTestId("draft-surface");

    await user.click(screen.getByRole("tab", { name: /Copilot/ }));
    await user.click(screen.getByRole("tab", { name: /Reviewed/ }));

    expect(screen.getByTestId("draft-surface")).toBe(before);
    expect(screen.getByTestId("draft-surface")).toHaveTextContent(
      /at least annually/,
    );
  });
});

describe("DraftingWorkspacePage — wrong node type", () => {
  it("explains rather than rendering an editor for a non-task node", async () => {
    renderApp("/workstreams/opres-v2/tasks/bcbs-opres-2021/draft");
    expect(await screen.findByText(/is not a task/i)).toBeInTheDocument();
    expect(screen.queryByTestId("draft-surface")).not.toBeInTheDocument();
  });
});
