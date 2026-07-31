import { describe, it, expect } from "vitest";
import {
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";
import { PairwiseFindingCard } from "./PairwiseFindingCard";
import type { PairwiseFinding } from "@/lib/types";

const TASK_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-3";
const EMPTY_URL = "/workstreams/opres-v2/tasks/opres-pd-v0-0";

/** The `opres-v2` mock: 4 analysed pairs carrying 6 findings, 3 unanalysed
 *  pairs, 7 neighbourhood documents. Labels break down as aligns-with 3,
 *  differs-on 1, conflicts-with 1, goes-beyond 1, silent-on 0 — so the fixture
 *  itself exercises the empty-group case. */
const TOTAL_FINDINGS = 6;

function group(label: string): HTMLElement {
  const el = screen
    .getAllByTestId("finding-group")
    .find((g) => g.getAttribute("data-label") === label);
  if (!el) throw new Error(`finding-group ${label} not found`);
  return el;
}

function cardsIn(label: string): HTMLElement[] {
  return Array.from(
    group(label).querySelectorAll<HTMLElement>('[data-testid="finding-card"]'),
  );
}

function findingCard(findingId: string): HTMLElement {
  const card = screen
    .getAllByTestId("finding-card")
    .find((c) => c.getAttribute("data-finding-id") === findingId);
  if (!card) throw new Error(`finding-card ${findingId} not found`);
  return card;
}

async function loadTaskScreen(url = TASK_URL) {
  renderApp(url);
  await screen.findByRole("heading", {
    name:
      url === EMPTY_URL
        ? "Operational Resilience PD — v0.0"
        : "Operational Resilience PD — v0.3",
  });
  // All five groups always render, so this must be the plural query.
  await screen.findAllByTestId("finding-group");
}

describe("TaskScreenPage — landing", () => {
  it("renders the header, source card and neighbour list", async () => {
    await loadTaskScreen();

    expect(
      screen.getByRole("link", { name: /Workstream graph/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Aisyah R. · .docx · 7 neighbour nodes"),
    ).toBeInTheDocument();

    const source = screen.getByTestId("source-card");
    expect(
      within(source).getByText("OpRes PD v0.3 working draft"),
    ).toBeInTheDocument();
    expect(within(source).getByText(/42 clauses/)).toBeInTheDocument();
    expect(within(source).getByText("Aisyah R.")).toBeInTheDocument();
    expect(within(source).getByText("in progress")).toBeInTheDocument();

    // The direct tier: one row per edge the task itself carries.
    expect(screen.getAllByTestId("neighbour-row")).toHaveLength(7);
  });

  it("lists 2-hop neighbours as their own tier, each naming the hop it arrives through", async () => {
    await loadTaskScreen();
    const box = screen.getByTestId("neighbours-card");

    const twoHop = within(box).getAllByTestId("neighbour-row-2hop");
    expect(twoHop).toHaveLength(2);
    expect(within(box).getByText("2 hops away")).toBeInTheDocument();
    expect(
      within(box).getByText(/IAIS Draft Application Paper/),
    ).toBeInTheDocument();

    // A 2-hop row sits on an edge the TASK does not have, so it must say which
    // neighbour it came through rather than implying a direct edge.
    expect(within(twoHop[0]).getByText("via BCBS OpRes 2021")).toBeVisible();

    // The two tiers stay separate: the header count and the page byline both
    // still describe direct neighbours only.
    expect(within(box).getByText(/7 · from node creation/)).toBeInTheDocument();
    expect(
      screen.getByText("Aisyah R. · .docx · 7 neighbour nodes"),
    ).toBeInTheDocument();
  });

  it("renders no 2-hop section when nothing sits two hops out", async () => {
    renderApp("/workstreams/opres-v2/tasks/opres-pd-fresh");
    const box = await screen.findByTestId("neighbours-card");

    expect(within(box).queryByTestId("neighbour-row-2hop")).toBeNull();
    expect(within(box).queryByText("2 hops away")).toBeNull();
  });

  it("titles and describes the box in the semantic-linkage vocabulary", async () => {
    await loadTaskScreen();
    const box = screen.getByTestId("pairwise-card");

    expect(
      within(box).getByRole("heading", { name: "Pairwise findings" }),
    ).toBeInTheDocument();
    expect(
      within(box).getByText(
        /Semantic linkages \(differs-on, conflicts-with, silent-on, aligns-with, goes-beyond\) between nodes/,
      ),
    ).toBeInTheDocument();
    // The retired framing is gone.
    expect(within(box).queryByText(/draft vs neighbours/i)).toBeNull();
    expect(within(box).queryByText(/Finder→critic/i)).toBeNull();
  });

  it("reports the neighbourhood in the metric tiles, not the neighbour list", async () => {
    await loadTaskScreen();

    // Labelled "Documents" deliberately: the neighbourhood is a different set
    // from `neighbours`, so calling both "Neighbours" would let two visible
    // numbers contradict each other.
    const tileValue = (label: string) =>
      screen.getByText(label).parentElement?.querySelector(".font-bold")
        ?.textContent;

    expect(screen.getByText("Documents")).toBeInTheDocument();
    expect(screen.queryByText("Neighbours")).toBeNull();
    expect(tileValue("Documents")).toBe("7");
    expect(tileValue("Analysed")).toBe("4 of 7");
    expect(tileValue("Findings")).toBe(String(TOTAL_FINDINGS));
  });
});

describe("TaskScreenPage — label groups", () => {
  it("renders all five labels in attention order", async () => {
    await loadTaskScreen();

    expect(
      screen.getAllByTestId("finding-group").map((g) => g.dataset.label),
    ).toEqual([
      "conflicts-with",
      "differs-on",
      "silent-on",
      "goes-beyond",
      "aligns-with",
    ]);
  });

  it("shows an empty group with its zero rather than hiding it", async () => {
    await loadTaskScreen();
    const silent = group("silent-on");

    expect(within(silent).getByTestId("group-total")).toHaveTextContent("0");
    expect(within(silent).getByTestId("group-empty")).toHaveTextContent(
      "None found.",
    );
  });

  it("renders every finding, with no truncation control", async () => {
    await loadTaskScreen();

    expect(screen.getAllByTestId("finding-card")).toHaveLength(TOTAL_FINDINGS);
    expect(cardsIn("aligns-with")).toHaveLength(3);
    expect(cardsIn("conflicts-with")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /show all/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /show more/i })).toBeNull();
  });

  it("carries the total and pending count per group", async () => {
    await loadTaskScreen();
    const aligns = group("aligns-with");

    expect(within(aligns).getByTestId("group-total")).toHaveTextContent("3");
    expect(within(aligns).getByTestId("group-pending")).toHaveTextContent("3");
  });
});

describe("TaskScreenPage — finding cards", () => {
  it("shows the summary, both documents and clause numbers, with no clause text", async () => {
    await loadTaskScreen();
    const card = cardsIn("conflicts-with")[0];

    expect(
      within(card).getByText(
        "Anchor to superseded RMiT version — draft anchors to the 1 June 2023 RMiT while the 28 Nov 2025 version supersedes it",
      ),
    ).toBeInTheDocument();
    expect(
      within(card).getByText(/Operational Resilience PD — v0\.3 ↔ RMiT PD/),
    ).toBeInTheDocument();
    // Clause NUMBERS on both sides, never the clauses' text.
    expect(within(card).getByText("OpRes PD 7.1")).toBeInTheDocument();
    expect(within(card).getByText("RMiT PD 1.2")).toBeInTheDocument();
    expect(card).not.toHaveTextContent(/shall anchor its operational/i);
  });

  it("offers Review, Accept and Dismiss on a pending card", async () => {
    await loadTaskScreen();
    const card = cardsIn("conflicts-with")[0];

    expect(card).toHaveAttribute("data-review-state", "pending");
    expect(
      within(card).getByRole("button", { name: "Review" }),
    ).toBeInTheDocument();
    expect(
      within(card).getByRole("button", { name: /Accept/ }),
    ).toBeInTheDocument();
    expect(
      within(card).getByRole("button", { name: /Dismiss/ }),
    ).toBeInTheDocument();
    expect(within(card).queryByRole("button", { name: /Undo/ })).toBeNull();
  });

  it("shows the sentiment arrow only on differs-on", async () => {
    await loadTaskScreen();

    expect(
      within(cardsIn("differs-on")[0]).getByText("differs-on ↑"),
    ).toBeInTheDocument();
    // The others carry a bare label with no arrow.
    expect(
      within(cardsIn("conflicts-with")[0]).getByText("conflicts-with"),
    ).toBeInTheDocument();
    expect(
      within(cardsIn("goes-beyond")[0]).queryByText(/goes-beyond [↑↓]/),
    ).toBeNull();
  });

  it("names a clause number on both sides when the finding cites both", async () => {
    await loadTaskScreen();
    const card = cardsIn("goes-beyond")[0];

    expect(within(card).getByText(/OpRes PD 4\.7/)).toBeInTheDocument();
    expect(
      within(card).getByText(/BCBS OpRes Principle 7/),
    ).toBeInTheDocument();
    expect(within(card).queryByText(/No matching clause found/)).toBeNull();
  });
});

// The one-sided case has no representative in the opres-v2 mock (every seeded
// finding cites both sides), so it is proved against the card directly rather
// than by inventing a fixture finding.
describe("PairwiseFindingCard — a finding that cites nothing on one side", () => {
  const ONE_SIDED: PairwiseFinding = {
    id: "e-x~0",
    label: "silent-on",
    sentiment: null,
    summary: "The draft is silent on the customer-consent revocation window.",
    review_state: "pending",
    edge_id: "e-x",
    left: { id: "a", title: "Working draft", node_type: "task" },
    right: { id: "b", title: "HKMA SPM OR-2", node_type: "peer-regulator" },
    source_clause_number: null,
    target_clause_number: "HKMA OR-2 4.1",
  };

  it("says no matching clause was found rather than inventing one", () => {
    render(
      <PairwiseFindingCard
        finding={ONE_SIDED}
        onReview={() => {}}
        onSetState={() => {}}
        isPending={false}
      />,
    );

    expect(screen.getByText("No matching clause found")).toBeInTheDocument();
    expect(screen.getByText("HKMA OR-2 4.1")).toBeInTheDocument();
  });
});

describe("TaskScreenPage — accept, dismiss and undo", () => {
  it("sinks an accepted card to the bottom of its own group", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    const before = cardsIn("aligns-with").map((c) => c.dataset.findingId);
    const target = before[0]!;

    await user.click(
      within(findingCard(target)).getByRole("button", { name: /Accept/ }),
    );

    await waitFor(() =>
      expect(findingCard(target)).toHaveAttribute(
        "data-review-state",
        "accepted",
      ),
    );

    const after = cardsIn("aligns-with").map((c) => c.dataset.findingId);
    // Still in the same group, now last, and the group's total is unmoved.
    expect(after).toHaveLength(3);
    expect(after[after.length - 1]).toBe(target);
    const aligns = group("aligns-with");
    expect(within(aligns).getByTestId("group-total")).toHaveTextContent("3");
    expect(within(aligns).getByTestId("group-pending")).toHaveTextContent("2");
  });

  it("sinks a dismissed card the same way", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    const target = cardsIn("aligns-with")[0]!.dataset.findingId!;
    await user.click(
      within(findingCard(target)).getByRole("button", { name: /Dismiss/ }),
    );

    await waitFor(() =>
      expect(findingCard(target)).toHaveAttribute(
        "data-review-state",
        "dismissed",
      ),
    );
    const after = cardsIn("aligns-with").map((c) => c.dataset.findingId);
    expect(after[after.length - 1]).toBe(target);
    expect(
      within(group("aligns-with")).getByTestId("group-pending"),
    ).toHaveTextContent("2");
  });

  it("restores a judged card to pending on Undo", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    const target = cardsIn("aligns-with")[0]!.dataset.findingId!;
    await user.click(
      within(findingCard(target)).getByRole("button", { name: /Accept/ }),
    );
    await waitFor(() =>
      expect(findingCard(target)).toHaveAttribute(
        "data-review-state",
        "accepted",
      ),
    );

    await user.click(
      within(findingCard(target)).getByRole("button", { name: /Undo/ }),
    );

    await waitFor(() =>
      expect(findingCard(target)).toHaveAttribute(
        "data-review-state",
        "pending",
      ),
    );
    expect(
      within(group("aligns-with")).getByTestId("group-pending"),
    ).toHaveTextContent("3");
    // Back above the judged block.
    expect(cardsIn("aligns-with")[0]!.dataset.findingId).toBe(target);
  });
});

describe("TaskScreenPage — node filter", () => {
  it("selects several documents at once", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: /^HKMA/ }));
    await user.click(screen.getByRole("button", { name: /^RMiT/ }));

    expect(screen.getByRole("button", { name: /^HKMA/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: /^RMiT/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    // One differs-on (HKMA) + one conflicts-with (RMiT), and nothing else.
    expect(screen.getAllByTestId("finding-card")).toHaveLength(2);
    expect(cardsIn("differs-on")).toHaveLength(1);
    expect(cardsIn("conflicts-with")).toHaveLength(1);
    expect(cardsIn("aligns-with")).toHaveLength(0);
  });

  it("recomputes group counts over the filtered set", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: /^BCBS/ }));
    const aligns = group("aligns-with");
    // BCBS carries 2 of the 3 alignments.
    expect(within(aligns).getByTestId("group-total")).toHaveTextContent("2");
  });

  it("deselects one of two without clearing the other", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: /^HKMA/ }));
    await user.click(screen.getByRole("button", { name: /^RMiT/ }));
    await user.click(screen.getByRole("button", { name: /^HKMA/ }));

    expect(screen.getByRole("button", { name: /^HKMA/ })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(screen.getByRole("button", { name: /^RMiT/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getAllByTestId("finding-card")).toHaveLength(1);
  });

  it("restores everything on All", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("button", { name: /^HKMA/ }));
    expect(screen.getAllByTestId("finding-card")).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getAllByTestId("finding-card")).toHaveLength(TOTAL_FINDINGS);
    screen
      .getAllByTestId("node-filter-chip")
      .slice(1)
      .forEach((chip) => expect(chip).toHaveAttribute("aria-pressed", "false"));
  });
});

describe("TaskScreenPage — coverage strip", () => {
  it("folds to its count line while the findings are scrolled, and reopens at the top", async () => {
    await loadTaskScreen();
    const strip = screen.getByTestId("coverage-strip");
    const scroller = screen.getByTestId("findings-scroll");

    expect(strip).toHaveAttribute("data-collapsed", "false");
    expect(within(strip).getAllByTestId("coverage-pair")[0]).toBeVisible();

    fireEvent.scroll(scroller, { target: { scrollTop: 240 } });
    expect(strip).toHaveAttribute("data-collapsed", "true");
    expect(within(strip).getAllByTestId("coverage-pair")[0]).not.toBeVisible();
    // The count survives the fold — the gap is still declared, just not listed.
    expect(
      within(strip).getByText(/Not yet analysed · 3 pairs/),
    ).toBeInTheDocument();
    // Hidden, never unmounted: a row owns its own in-flight analyze, and
    // dropping it mid-request would take the progress bar with it.
    expect(within(strip).getAllByTestId("coverage-pair")).toHaveLength(3);

    fireEvent.scroll(scroller, { target: { scrollTop: 0 } });
    expect(strip).toHaveAttribute("data-collapsed", "false");
    expect(within(strip).getAllByTestId("coverage-pair")[0]).toBeVisible();
  });

  it("keeps the strip open on a scroll too small to be a read", async () => {
    // Collapsing makes the viewport taller, which can pull `scrollTop` back
    // down; one threshold would flap, so expanding and collapsing use different
    // ones and a nudge inside the gap changes nothing.
    await loadTaskScreen();
    const strip = screen.getByTestId("coverage-strip");

    fireEvent.scroll(screen.getByTestId("findings-scroll"), {
      target: { scrollTop: 12 },
    });
    expect(strip).toHaveAttribute("data-collapsed", "false");
  });

  it("lists the pairs that have never been analysed", async () => {
    await loadTaskScreen();
    const strip = screen.getByTestId("coverage-strip");

    // fsb-3rd-party, abm-position and opres-dp-2025 have no findings file.
    const pairs = within(strip).getAllByTestId("coverage-pair");
    expect(pairs).toHaveLength(3);
    expect(
      within(strip).getByText(/Not yet analysed · 3 pairs/),
    ).toBeInTheDocument();
    expect(pairs.map((p) => p.getAttribute("data-edge-id"))).toEqual([
      "e-opres_v0_3--fsb_3rd_party",
      "e-opres_v0_3--abm_position",
      "e-opres_v0_3--opres_dp_2025",
    ]);
  });

  it("folds an analysed pair into its label group and clears it from the strip", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    const fsb = screen
      .getAllByTestId("coverage-pair")
      .find((p) => p.dataset.edgeId === "e-opres_v0_3--fsb_3rd_party")!;
    await user.click(within(fsb).getByRole("button", { name: /Analyze/i }));

    // The surfaced finding is an alignment, so that group grows by one.
    await waitFor(() =>
      expect(
        within(group("aligns-with")).getByTestId("group-total"),
      ).toHaveTextContent("4"),
    );
    await waitFor(() =>
      expect(screen.getAllByTestId("coverage-pair")).toHaveLength(2),
    );
  });
});

describe("TaskScreenPage — the draft's content is never a gate", () => {
  it("populates the box even though the seeded draft has no clauses saved", async () => {
    // The point of the epic: findings show from the moment the workstream has
    // been analysed. Nothing about the draft's emptiness reaches the box.
    await loadTaskScreen();

    expect(screen.getAllByTestId("finding-card")).toHaveLength(TOTAL_FINDINGS);
    const box = screen.getByTestId("pairwise-card");
    expect(box).not.toHaveTextContent(/until the draft has content/i);
    expect(box).not.toHaveTextContent(/no pairwise findings can exist/i);
  });

  it("has no empty-draft card anywhere in the app", async () => {
    // The card and its whole component were deleted, not just hidden.
    await loadTaskScreen();
    expect(screen.queryByTestId("empty-draft-card")).toBeNull();

    renderApp(EMPTY_URL);
    await screen.findByRole("heading", {
      name: "Operational Resilience PD — v0.0",
    });
    expect(screen.queryByTestId("empty-draft-card")).toBeNull();
  });

  it("tells a task with no connected documents to add some", async () => {
    // v0-0 declares neighbours but sits on no edges in the graph, so its
    // neighbourhood is genuinely empty — which is a different message from
    // "analysed and found nothing", and never a complaint about the draft.
    renderApp(EMPTY_URL);
    expect(
      await screen.findByText(/no neighbouring documents yet/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
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

describe("TaskScreenPage — Maker-Checker workflow", () => {
  it("persists Draft -> Pending Review -> Approved, with an audit line on sign-off", async () => {
    const user = userEvent.setup();
    const first = renderApp(TASK_URL);
    await screen.findByRole("heading", {
      name: "Operational Resilience PD — v0.3",
    });

    expect(screen.getByText("Draft")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Assign/i }));
    const assignDialog = await screen.findByRole("dialog");
    await user.click(within(assignDialog).getByText("Farid M."));

    expect(await screen.findByText("Pending Review")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Assign/i }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Approve/i }));
    const approveDialog = await screen.findByRole("dialog");
    await user.click(within(approveDialog).getByText(/Approve as Farid M\./i));

    expect(await screen.findByText("Approved")).toBeInTheDocument();
    expect(screen.getByText(/Approved by Farid M\./)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Approve/i }),
    ).not.toBeInTheDocument();

    first.unmount();
    renderApp(TASK_URL);
    await screen.findByRole("heading", {
      name: "Operational Resilience PD — v0.3",
    });
    expect(await screen.findByText("Approved")).toBeInTheDocument();
  });
});

describe("TaskScreenPage — navigation", () => {
  it("breadcrumb routes back to the workstream graph", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("link", { name: /Workstream graph/i }));
    expect(
      await screen.findByRole("button", { name: /add node/i }),
    ).toBeInTheDocument();
  });

  it("Review opens the comparison on the clicked finding", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    const card = cardsIn("differs-on")[0]!;
    await user.click(within(card).getByRole("button", { name: "Review" }));

    expect(
      await screen.findByRole("heading", {
        name: /Operational Resilience PD — v0.3 ↔ HKMA SPM OR-2/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("findings")).toBeInTheDocument();
  });

  it("Open draft routes to the drafting workspace", async () => {
    const user = userEvent.setup();
    await loadTaskScreen();

    await user.click(screen.getByRole("link", { name: /Open draft/i }));
    expect(await screen.findByTestId("draft-surface")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Reviewed/ })).toBeInTheDocument();
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

describe("TaskScreenPage — a freshly scaffolded focal task", () => {
  // A new workstream's focal node carries identity only, so the engine reports
  // null for source_name/format/status/last_edited_at. The screen used to throw
  // on `task.owner.name`, and with no error boundary that blanked the whole app
  // — Open task looked like a dead button.
  const FRESH_URL = "/workstreams/opres-v2/tasks/opres-pd-fresh";

  it("opens without crashing when the document fields are absent", async () => {
    renderApp(FRESH_URL);
    expect(
      await screen.findByRole("heading", {
        name: "Operational Resilience PD (PD)",
      }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("source-card")).toBeInTheDocument();
  });

  it("names the owner and says no document is attached, never 'null'", async () => {
    renderApp(FRESH_URL);
    const source = await screen.findByTestId("source-card");
    expect(within(source).getByText("Aisyah R.")).toBeInTheDocument();
    expect(
      within(source).getByText("No document attached"),
    ).toBeInTheDocument();
    expect(source).not.toHaveTextContent(/null/i);
    expect(source).not.toHaveTextContent(/1970/);
  });

  it("presents a task with no neighbours as a starting state, not an error", async () => {
    renderApp(FRESH_URL);
    expect(
      await screen.findByText(/no neighbouring documents yet/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
