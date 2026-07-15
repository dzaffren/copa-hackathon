import { describe, it, expect } from "vitest";
import { screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";

const TASK_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-3";
const EMPTY_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-0";

function pairCard(neighbourId: string): HTMLElement {
  const card = screen
    .getAllByTestId("pair-card")
    .find((c) => c.getAttribute("data-neighbour") === neighbourId);
  if (!card) throw new Error(`pair-card ${neighbourId} not found`);
  return card;
}

async function loadTaskScreen() {
  renderApp(TASK_URL);
  await screen.findByRole("heading", {
    name: "Operational Resilience PD — v0.3",
  });
}

describe("TaskScreenPage — landing", () => {
  it("renders the header, source card, six neighbours, six pairs and footer", async () => {
    await loadTaskScreen();

    // Header
    expect(
      screen.getByRole("link", { name: /Workstream graph/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Working draft of the Policy Document following the 2025 Discussion Paper · 6 neighbour nodes defined at creation",
      ),
    ).toBeInTheDocument();

    // Source card
    const source = screen.getByTestId("source-card");
    expect(
      within(source).getByText("OpRes PD v0.3 working draft"),
    ).toBeInTheDocument();
    expect(within(source).getByText(/\.docx/)).toBeInTheDocument();
    expect(within(source).getByText(/42 clauses/)).toBeInTheDocument();
    expect(within(source).getByText("Aisyah R.")).toBeInTheDocument();
    expect(within(source).getByText("Farid M.")).toBeInTheDocument();
    expect(within(source).getByText("Priya S.")).toBeInTheDocument();
    expect(within(source).getByText("in progress")).toBeInTheDocument();

    // Neighbours + pairs
    expect(screen.getAllByTestId("neighbour-row")).toHaveLength(6);
    expect(screen.getAllByTestId("pair-card")).toHaveLength(6);

    // Footer
    expect(screen.getByText("4 of 6 neighbours analysed")).toBeInTheDocument();
  });
});

describe("TaskScreenPage — neighbour list", () => {
  it("lists six neighbours in graph order with structural + node types", async () => {
    await loadTaskScreen();
    const rows = screen.getAllByTestId("neighbour-row");

    const expected = [
      ["BCBS OpRes 2021", "contributes-to · international-standard"],
      ["FSB 3rd-Party Toolkit", "contributes-to · international-standard"],
      ["HKMA SPM OR-2", "contributes-to · peer-regulator"],
      ["RMiT PD (28 Nov 2025)", "parallel-to · internal-published"],
      ["FSA 2013 §143", "references · act-law"],
      ["ABM position paper", "contributes-to · industry-input"],
    ];

    expected.forEach(([title, meta], i) => {
      expect(within(rows[i]).getByText(title)).toBeInTheDocument();
      expect(within(rows[i]).getByText(meta)).toBeInTheDocument();
    });
  });
});

describe("TaskScreenPage — analysed pairs", () => {
  it("shows a semantic label, one-line summary and Open in Review link", async () => {
    await loadTaskScreen();

    const bcbs = pairCard("bcbs-opres-2021");
    expect(bcbs).toHaveAttribute("data-analysed", "true");
    expect(
      await within(bcbs).findByText(
        "Dependency mapping tracks BCBS Principle 7",
      ),
    ).toBeInTheDocument();
    expect(within(bcbs).getByText("aligns-with")).toBeInTheDocument();
    expect(
      within(bcbs).getByRole("link", { name: /Open in Review/i }),
    ).toBeInTheDocument();

    // HKMA differs-on carries its sentiment arrow.
    const hkma = pairCard("hkma-spm-or2");
    expect(
      await within(hkma).findByText(
        "Annual vs biennial scenario testing — draft pins annual cadence; HKMA requires at least biennial",
      ),
    ).toBeInTheDocument();
    expect(within(hkma).getByText("differs-on ↑")).toBeInTheDocument();

    // RMiT conflicts-with
    const rmit = pairCard("rmit-pd-2025");
    expect(
      await within(rmit).findByText(
        "Anchor to superseded RMiT version — draft anchors to the 1 June 2023 RMiT while the 28 Nov 2025 version supersedes it",
      ),
    ).toBeInTheDocument();
    expect(within(rmit).getByText("conflicts-with")).toBeInTheDocument();
  });
});

describe("TaskScreenPage — unanalysed pairs", () => {
  it("renders dashed, not-analysed state with an Analyze button and no label", async () => {
    await loadTaskScreen();

    for (const id of ["fsb-3rd-party", "abm-position"]) {
      const card = pairCard(id);
      expect(card).toHaveAttribute("data-analysed", "false");
      expect(card.className).toContain("border-dashed");
      expect(within(card).getByText("not analysed")).toBeInTheDocument();
      expect(within(card).getByText("0 findings")).toBeInTheDocument();
      expect(
        within(card).getByRole("button", { name: /Analyze linkages/i }),
      ).toBeInTheDocument();
      // No semantic label on an unanalysed pair.
      expect(within(card).queryByText("aligns-with")).toBeNull();
      expect(within(card).queryByText("differs-on")).toBeNull();
      expect(
        within(card).queryByRole("link", { name: /Open in Review/i }),
      ).toBeNull();
    }
  });
});

describe("TaskScreenPage — filter chips", () => {
  it("narrows to one pair on HKMA and restores all six on All", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: "HKMA" }));
    let cards = screen.getAllByTestId("pair-card");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveAttribute("data-neighbour", "hkma-spm-or2");
    expect(screen.getByRole("button", { name: "HKMA" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await user.click(screen.getByRole("button", { name: "All" }));
    cards = screen.getAllByTestId("pair-card");
    expect(cards).toHaveLength(6);
  });

  it.each([
    ["BCBS", "bcbs-opres-2021"],
    ["FSB", "fsb-3rd-party"],
    ["HKMA", "hkma-spm-or2"],
    ["RMiT", "rmit-pd-2025"],
    ["FSA", "fsa-2013-143"],
    ["ABM", "abm-position"],
  ])("chip %s isolates a single neighbour", async (chip, neighbourId) => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: chip }));
    const cards = screen.getAllByTestId("pair-card");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveAttribute("data-neighbour", neighbourId);
  });
});

describe("TaskScreenPage — assign dialog", () => {
  it("opens a workflow picker listing Farid M. and Priya S.", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: /Assign/i }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Farid M.")).toBeInTheDocument();
    expect(within(dialog).getByText("Priya S.")).toBeInTheDocument();
  });
});

describe("TaskScreenPage — analyze linkages", () => {
  it("flips the FSB pair to analysed and bumps the footer count", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    expect(screen.getByText("4 of 6 neighbours analysed")).toBeInTheDocument();

    const fsb = pairCard("fsb-3rd-party");
    await user.click(
      within(fsb).getByRole("button", { name: /Analyze linkages/i }),
    );

    // Card flips to analysed and renders the surfaced finding.
    expect(
      await screen.findByText(
        "Third-party register aligns with FSB Toolkit register expectations",
      ),
    ).toBeInTheDocument();
    expect(pairCard("fsb-3rd-party")).toHaveAttribute("data-analysed", "true");

    // Footer increments.
    await waitFor(() =>
      expect(
        screen.getByText("5 of 6 neighbours analysed"),
      ).toBeInTheDocument(),
    );
  });
});

describe("TaskScreenPage — empty draft", () => {
  it("renders the empty-draft card and no pair cards", async () => {
    renderApp(EMPTY_URL);
    await screen.findByRole("heading", {
      name: "Operational Resilience PD — v0.0",
    });

    expect(screen.getByText(/0 clauses/)).toBeInTheDocument();
    const empty = screen.getByTestId("empty-draft-card");
    expect(empty).toBeInTheDocument();
    expect(
      within(empty).getByText(/no pairwise findings can exist/i),
    ).toBeInTheDocument();
    expect(
      within(empty).getByRole("link", { name: /Open draft/i }),
    ).toBeInTheDocument();
    expect(screen.queryAllByTestId("pair-card")).toHaveLength(0);
  });
});

describe("TaskScreenPage — navigation", () => {
  it("breadcrumb routes back to the workstream graph", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("link", { name: /Workstream graph/i }));
    // The real workstream graph screen now mounts here (previously a
    // placeholder heading); its "+ Add node" action confirms we landed.
    expect(
      await screen.findByRole("button", { name: /add node/i }),
    ).toBeInTheDocument();
  });

  it("Open in Review routes to the HKMA edge review screen", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: "HKMA" }));
    const hkma = pairCard("hkma-spm-or2");
    await within(hkma).findByText(/Annual vs biennial/);
    await user.click(
      within(hkma).getByRole("link", { name: /Open in Review/i }),
    );

    expect(
      await screen.findByRole("heading", { name: /Review linkages/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/e-opres_v0_3--hkma_spm_or2/)).toBeInTheDocument();
  });

  it("Open draft routes to the drafting workspace", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("link", { name: /Open draft/i }));
    expect(
      await screen.findByRole("heading", { name: /Drafting workspace/i }),
    ).toBeInTheDocument();
  });
});

describe("TaskScreenPage — wrong node type", () => {
  it("shows a not-a-task message with a link back to the graph", async () => {
    renderApp("/workstreams/opres-v2/tasks/bcbs-opres-2021");
    expect(await screen.findByText(/not a task/i)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /workstream graph/i }),
    ).toBeInTheDocument();
  });
});
