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
  // By label, not position: the review screen orders cards by attention
  // (conflicts-with → … → aligns-with), so index 0 is not the aligns-with
  // finding on OpRes PD 4.4 that the assertions below are about.
  await screen.findAllByTestId("finding-card");
  const card = screen
    .getAllByTestId("finding-card")
    .find((c) => c.getAttribute("data-label") === "aligns-with")!;
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
  // The drafter recorded the deliverable kind when the task node was created,
  // and the server reads it off that node — so the Copilot must not ask again.
  it("never asks what kind of deliverable the drafter is producing", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    expect(screen.queryByLabelText("Intent preset")).not.toBeInTheDocument();
    // No control of any kind offers the vocabulary: the panel opens straight
    // into the conversation.
    expect(
      within(screen.getByTestId("copilot-tab")).queryByRole("combobox"),
    ).not.toBeInTheDocument();
  });

  it("shows the quick-start surface and a message box, before any chat", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    // The pre-built suggestion surface is on screen the moment the tab opens.
    expect(
      screen.getByText(/Copilot suggestions based on your workstream/i),
    ).toBeInTheDocument();
    // The drafter can also chat: a message box and Send button are present.
    expect(screen.getByLabelText("Message the Copilot")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeInTheDocument();
    // No turns yet, though — the conversation starts empty.
    expect(screen.queryByTestId("chat-copilot")).not.toBeInTheDocument();
  });

  it("renders the four global-benchmark cards with status badges", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    expect(screen.getByText(/UK PRA — PS6\/21/)).toBeInTheDocument();
    expect(screen.getByText(/MAS — BCM Guidelines/)).toBeInTheDocument();
    expect(screen.getByText(/HKMA — SA-2 Module/)).toBeInTheDocument();
    expect(
      screen.getByText(/BCBS — OpRes Principles 2021/),
    ).toBeInTheDocument();

    expect(screen.getByText("Aligned")).toBeInTheDocument();
    expect(screen.getAllByText("Gap detected")).toHaveLength(2);
    expect(screen.getByText("Deviation")).toBeInTheDocument();
  });

  it("renders the suggested next actions with finding-label tags", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    expect(
      screen.getByText(/Reconcile CBF definition conflict/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Draft Section 6 — Reporting Requirements/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Section 3 ready to draft/)).toBeInTheDocument();

    expect(screen.getByText("conflicts-with")).toBeInTheDocument();
    expect(screen.getByText("silent-on")).toBeInTheDocument();
    expect(screen.getByText("aligns-with")).toBeInTheDocument();
  });

  it("clicking a suggestion opens its reply in the conversation, with an insert action", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    await user.click(
      screen.getByText(/Reconcile CBF definition conflict/).closest("button")!,
    );

    // The click becomes a user turn and a tailored Copilot reply.
    expect(await screen.findByTestId("chat-user")).toHaveTextContent(
      "Reconcile CBF definition conflict",
    );
    const reply = await screen.findByTestId("chat-copilot");
    expect(reply).toHaveTextContent(/CBF/i);
    expect(
      within(reply).getByRole("button", { name: /Insert at cursor/i }),
    ).toBeInTheDocument();
  });

  it("lets the drafter type a message and returns a tailored reply", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    await user.type(
      screen.getByLabelText("Message the Copilot"),
      "help me draft the governance section",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByTestId("chat-user")).toHaveTextContent(
      "help me draft the governance section",
    );
    const reply = await screen.findByTestId("chat-copilot");
    expect(reply).toHaveTextContent(/Governance/i);
    expect(
      within(reply).getByRole("button", { name: /Insert at cursor/i }),
    ).toBeInTheDocument();
  });

  it("inserts a reply's snippet into the draft at the cursor", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    await user.type(
      screen.getByLabelText("Message the Copilot"),
      "draft governance",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    const reply = await screen.findByTestId("chat-copilot");
    await user.click(
      within(reply).getByRole("button", { name: /Insert at cursor/i }),
    );

    const surface = screen.getByTestId("draft-surface");
    await waitFor(() =>
      expect(surface).toHaveTextContent(/accountable officer/i),
    );
    // The provenance mark tells a reader which text the drafter did not write.
    expect(surface.querySelector(".copilot-snippet")).not.toBeNull();
  });

  it("shows the quick prompt chips", async () => {
    const user = userEvent.setup();
    await loadWorkspace();
    await user.click(screen.getByRole("tab", { name: /Copilot/ }));

    for (const chip of [
      "Summarise gaps",
      "Show full outline",
      "Compare with MAS",
      "Draft Section 3",
    ]) {
      expect(screen.getByRole("button", { name: chip })).toBeInTheDocument();
    }
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
