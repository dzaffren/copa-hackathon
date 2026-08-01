import { describe, expect, it, beforeEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { RecommendationsCard } from "./RecommendationsCard";
import {
  DEFAULT_GUARDRAILS_TEXT,
  makeRecommendation,
  resetRecommendations,
} from "@/test/msw/handlers";

const WS = "open-finance-pd-2026";
const TASK = "opres-pd-v0-3"; // a node the MSW TASKS map knows

function renderCard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <RecommendationsCard workstreamId={WS} nodeId={TASK} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const UNREFLECTED = {
  finding_id: "f-uncited-1",
  edge_id: "e-bis_papers_168--ed_open_finance_2025",
  label: "differs-on" as const,
  sentiment: "tighten" as const,
  summary:
    "The ED mandates a fixed rollout date where BIS observes flexibility.",
  left: { id: "bis-papers-168", title: "BIS Papers 168" },
  right: { id: "ed-open-finance-2025", title: "ED Open Finance 2025" },
  source_clause_number: "3.1",
  source_clause_text: "Jurisdictions may adopt a facilitative approach.",
  target_clause_number: "14.2",
  target_clause_text: "Phase one obligations take effect on 1 January 2027.",
};

describe("RecommendationsCard — empty states", () => {
  beforeEach(() => resetRecommendations());

  it("tells the drafter to set policy requirements, and cannot generate", async () => {
    resetRecommendations({ dimensions: [] });
    renderCard();

    expect(await screen.findByTestId("no-dimensions")).toHaveTextContent(
      /No policy requirements set/i,
    );
    expect(
      screen.getByRole("link", { name: /Set policy requirements/i }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("generate")).toBeDisabled();
  });

  it("asks for accepted findings first when none are accepted", async () => {
    resetRecommendations({ acceptedCount: 0 });
    renderCard();

    expect(await screen.findByTestId("no-accepted")).toHaveTextContent(
      /Accept findings in the Pairwise findings box first/i,
    );
    expect(screen.getByTestId("generate")).toBeDisabled();
  });

  it("offers Generate when nothing has been generated yet", async () => {
    renderCard();

    expect(await screen.findByTestId("not-generated")).toBeInTheDocument();
    expect(screen.getByTestId("generate")).toBeEnabled();
    expect(screen.getByTestId("generate")).toHaveTextContent("Generate");
  });

  it("prefers the dimensions message when both are missing", async () => {
    // Without dimensions there is nothing to reason over, so that is the honest
    // first thing to fix — showing "accept findings" would send her to the wrong
    // screen.
    resetRecommendations({ dimensions: [], acceptedCount: 0 });
    renderCard();

    expect(await screen.findByTestId("no-dimensions")).toBeInTheDocument();
    expect(screen.queryByTestId("no-accepted")).not.toBeInTheDocument();
  });
});

describe("RecommendationsCard — generating and reading", () => {
  beforeEach(() =>
    resetRecommendations({
      nextBatch: [
        makeRecommendation({
          id: "rec-a",
          title: "Publish a data consumer list",
        }),
        makeRecommendation({
          id: "rec-b",
          title: "Clarify transition milestones",
          dimensions: ["Transition arrangements"],
          confidence_note: "",
        }),
      ],
      unreflected: [UNREFLECTED],
    }),
  );

  it("renders the generated recommendations with their dimensions", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(2),
    );
    expect(
      screen.getByText("Publish a data consumer list"),
    ).toBeInTheDocument();
    expect(screen.getByText("Transition arrangements")).toBeInTheDocument();
    // The button becomes Regenerate once a set exists.
    expect(screen.getByTestId("generate")).toHaveTextContent("Regenerate");
  });

  it("quotes the cited clause verbatim, with its number, when expanded", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    const first = (await screen.findAllByTestId("recommendation"))[0];

    await userEvent.click(within(first).getByTestId("citations-toggle"));

    const citation = within(first).getByTestId("citation");
    expect(citation).toHaveTextContent("4.2");
    expect(citation).toHaveTextContent(
      /An AI should publish on its website a list of all TSPs/,
    );
    expect(citation).toHaveTextContent("10.4");
  });

  it("reveals the confidence note on the marker, and omits it when empty", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    const cards = await screen.findAllByTestId("recommendation");

    const marker = within(cards[0]).getByRole("button", {
      name: /could not verify/i,
    });
    await userEvent.hover(marker);
    expect(await screen.findByTestId("info-bubble")).toHaveTextContent(
      /Assumes no separate industry register/i,
    );

    // rec-b has no confidence note, so it must carry no marker at all rather
    // than an empty bubble.
    expect(
      within(cards[1]).queryByRole("button", { name: /could not verify/i }),
    ).not.toBeInTheDocument();
  });

  it("sorts bookmarked recommendations above the rest", async () => {
    resetRecommendations({
      nextBatch: [
        makeRecommendation({ id: "plain", title: "Not bookmarked" }),
        makeRecommendation({
          id: "pinned",
          title: "Bookmarked one",
          bookmarked: true,
        }),
      ],
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(2),
    );
    const order = screen
      .getAllByTestId("recommendation")
      .map((el) => el.getAttribute("data-rec-id"));
    expect(order).toEqual(["pinned", "plain"]);
  });

  it("reports the accepted findings no recommendation drew on", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    const section = await screen.findByTestId("not-yet-reflected");
    expect(section).toHaveAttribute("data-count", "1");
    expect(screen.getByTestId("not-yet-reflected-count")).toHaveTextContent(
      "1",
    );

    await userEvent.click(screen.getByTestId("not-yet-reflected-toggle"));
    const row = screen.getByTestId("unreflected-finding");
    expect(row).toHaveTextContent(/fixed rollout date/i);
    // Read-only: it links through to the review screen and offers nothing else.
    expect(within(row).getByRole("link", { name: /Open/i })).toHaveAttribute(
      "href",
      expect.stringContaining("f-uncited-1"),
    );
    expect(
      within(row).queryByRole("button", { name: /recommend/i }),
    ).not.toBeInTheDocument();
  });

  it("says so plainly when every accepted finding is reflected", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation()],
      unreflected: [],
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    await waitFor(() =>
      expect(screen.getByTestId("not-yet-reflected")).toHaveTextContent(
        /Every accepted finding is reflected/i,
      ),
    );
  });

  it("surfaces a failed generation without losing the previous set", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(2),
    );

    resetRecommendations({ failGenerate: true });
    await userEvent.click(screen.getByTestId("generate"));

    expect(
      await screen.findByText(/could not generate recommendations/i),
    ).toBeInTheDocument();
    expect(screen.getAllByTestId("recommendation")).toHaveLength(2);
  });
});

describe("RecommendationsCard — guardrails", () => {
  beforeEach(() => resetRecommendations());

  it("hides the guardrails until the badge is pressed", async () => {
    renderCard();
    const badge = await screen.findByTestId("guardrails-badge");

    expect(screen.queryByTestId("guardrails-panel")).not.toBeInTheDocument();
    expect(badge).toHaveAttribute("aria-expanded", "false");

    await userEvent.click(badge);

    expect(await screen.findByTestId("guardrails-panel")).toBeInTheDocument();
    expect(badge).toHaveAttribute("aria-expanded", "true");
  });

  it("ships populated with the five defaults", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("guardrails-badge"));

    const box = await screen.findByTestId("guardrails-body");
    expect(box).toHaveValue(DEFAULT_GUARDRAILS_TEXT);
    // The house-convention rule is the one a BNM reviewer scored 1/5 against, so
    // it is named explicitly rather than left to the whole-body comparison.
    expect(DEFAULT_GUARDRAILS_TEXT).toContain("provision number");
    expect(
      screen.getByText(/Showing the shipped defaults/i),
    ).toBeInTheDocument();
  });

  it("only enables Save once something is edited", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("guardrails-badge"));
    await screen.findByTestId("guardrails-body");

    expect(screen.getByTestId("guardrails-save")).toBeDisabled();

    await userEvent.type(screen.getByTestId("guardrails-body"), " extra rule");

    expect(screen.getByTestId("guardrails-save")).toBeEnabled();
  });

  it("warns plainly when the box is emptied, rather than restoring defaults", async () => {
    renderCard();
    await userEvent.click(await screen.findByTestId("guardrails-badge"));
    const box = await screen.findByTestId("guardrails-body");

    await userEvent.clear(box);

    expect(screen.getByTestId("guardrails-empty-warning")).toHaveTextContent(
      /generated with no guardrails/i,
    );

    await userEvent.click(screen.getByTestId("guardrails-save"));

    await waitFor(() => expect(box).toHaveValue(""));
    expect(
      screen.queryByText(/Showing the shipped defaults/i),
    ).not.toBeInTheDocument();
  });

  it("keeps the drafter's edits on screen when the save fails", async () => {
    resetRecommendations({ failGuardrailsSave: true });
    renderCard();
    await userEvent.click(await screen.findByTestId("guardrails-badge"));
    const box = await screen.findByTestId("guardrails-body");

    await userEvent.clear(box);
    await userEvent.type(box, "A rule I do not want to retype.");
    await userEvent.click(screen.getByTestId("guardrails-save"));

    expect(
      await screen.findByText(/could not save your guardrails/i),
    ).toBeInTheDocument();
    expect(box).toHaveValue("A rule I do not want to retype.");
  });
});

describe("RecommendationsCard — rationale rendering", () => {
  beforeEach(() => resetRecommendations());

  it("renders a bulleted rationale as a list, without literal markers", async () => {
    resetRecommendations({
      nextBatch: [
        makeRecommendation({
          rationale:
            "- ED clause 1.3 anchors sharing in the PDPA 2010.\n- HKMA clause 34.3.2(i) requires the same of third parties.\n- Neither elaborates a substantive standard.",
        }),
      ],
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    const list = await screen.findByTestId("rec-rationale");
    expect(list.tagName).toBe("UL");
    expect(within(list).getAllByRole("listitem")).toHaveLength(3);
    // The "- " marker is a wire-format detail, not something to show the drafter.
    expect(list).not.toHaveTextContent(/- ED clause/);
    expect(list).toHaveTextContent(/ED clause 1.3 anchors sharing in the PDPA/);
  });

  it("still reads correctly when the rationale is one paragraph", async () => {
    // An older committed set predates the bullet instruction, and a model can
    // ignore it. Either way the drafter must not see a collapsed run-on bullet.
    resetRecommendations({
      nextBatch: [
        makeRecommendation({
          rationale: "One continuous paragraph with no bullet markers at all.",
        }),
      ],
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(1),
    );
    expect(screen.queryByTestId("rec-rationale")).not.toBeInTheDocument();
    expect(
      screen.getByText(/One continuous paragraph with no bullet markers/),
    ).toBeInTheDocument();
  });
});

describe("RecommendationsCard — the confidence marker", () => {
  beforeEach(() => resetRecommendations());

  it("omits the marker when there is genuinely nothing to disclose", async () => {
    // The engine returns "Nothing unverified." rather than an empty string, so
    // the card has to recognise it. A marker revealing "nothing to report"
    // teaches the drafter to stop pressing the ones that matter.
    resetRecommendations({
      nextBatch: [
        makeRecommendation({
          id: "clean",
          confidence_note: "Nothing unverified.",
        }),
        makeRecommendation({
          id: "caveated",
          confidence_note: "Cannot verify which department owns the dashboard.",
        }),
      ],
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));

    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(2),
    );
    const [clean, caveated] = screen.getAllByTestId("recommendation");
    expect(
      within(clean).queryByRole("button", { name: /could not verify/i }),
    ).not.toBeInTheDocument();
    expect(
      within(caveated).getByRole("button", { name: /could not verify/i }),
    ).toBeInTheDocument();
  });
});

describe("RecommendationsCard — bookmarking", () => {
  beforeEach(() =>
    resetRecommendations({
      nextBatch: [
        makeRecommendation({ id: "first", title: "First recommendation" }),
        makeRecommendation({ id: "second", title: "Second recommendation" }),
      ],
    }),
  );

  async function generated() {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(2),
    );
    return screen.getAllByTestId("recommendation");
  }

  it("offers a bookmark control on every card, right of the confidence marker", async () => {
    const [first] = await generated();
    const controls = within(first).getAllByRole("button");
    const bookmarkIndex = controls.findIndex(
      (el) => el.getAttribute("data-testid") === "bookmark-toggle",
    );
    const markerIndex = controls.findIndex((el) =>
      /could not verify/i.test(el.getAttribute("aria-label") ?? ""),
    );

    expect(bookmarkIndex).toBeGreaterThanOrEqual(0);
    expect(markerIndex).toBeGreaterThanOrEqual(0);
    // Order is the point: she reads what could not be verified, THEN decides
    // whether to carry it forward — so the disclosure precedes the decision in
    // both reading order and the tab order.
    expect(markerIndex).toBeLessThan(bookmarkIndex);
  });

  it("marks a recommendation and reports it as pressed", async () => {
    const [first] = await generated();
    const toggle = within(first).getByTestId("bookmark-toggle");
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    expect(toggle).toHaveAccessibleName("Bookmark this recommendation");

    await userEvent.click(toggle);

    await waitFor(() => {
      const marked = screen
        .getAllByTestId("recommendation")
        .find((el) => el.getAttribute("data-rec-id") === "first")!;
      const control = within(marked).getByTestId("bookmark-toggle");
      expect(control).toHaveAttribute("aria-pressed", "true");
      // The name flips too — a screen reader must hear what the press will do
      // next, not what it just did.
      expect(control).toHaveAccessibleName("Remove bookmark");
    });
  });

  it("moves a bookmarked recommendation above the rest", async () => {
    const cards = await generated();
    const second = cards.find(
      (el) => el.getAttribute("data-rec-id") === "second",
    )!;

    await userEvent.click(within(second).getByTestId("bookmark-toggle"));

    await waitFor(() => {
      const order = screen
        .getAllByTestId("recommendation")
        .map((el) => el.getAttribute("data-rec-id"));
      expect(order).toEqual(["second", "first"]);
    });
  });

  it("unmarks a bookmarked recommendation", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ id: "pinned", bookmarked: true })],
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    const toggle = await screen.findByTestId("bookmark-toggle");
    expect(toggle).toHaveAttribute("aria-pressed", "true");

    await userEvent.click(toggle);

    await waitFor(() =>
      expect(screen.getByTestId("bookmark-toggle")).toHaveAttribute(
        "aria-pressed",
        "false",
      ),
    );
  });

  it("reverts the optimistic mark when the save fails", async () => {
    const [first] = await generated();
    resetRecommendations({ failBookmark: true });

    await userEvent.click(within(first).getByTestId("bookmark-toggle"));

    expect(
      await screen.findByText(/could not save that bookmark/i),
    ).toBeInTheDocument();
    const reverted = screen
      .getAllByTestId("recommendation")
      .find((el) => el.getAttribute("data-rec-id") === "first")!;
    expect(within(reverted).getByTestId("bookmark-toggle")).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });
});

describe("RecommendationsCard — commenting and rewriting", () => {
  beforeEach(() =>
    resetRecommendations({
      nextBatch: [
        makeRecommendation({ id: "first", title: "First recommendation" }),
        makeRecommendation({ id: "second", title: "Second recommendation" }),
      ],
    }),
  );

  async function generated() {
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    await waitFor(() =>
      expect(screen.getAllByTestId("recommendation")).toHaveLength(2),
    );
    return screen.getAllByTestId("recommendation");
  }

  it("keeps Submit disabled until something is actually written", async () => {
    const [first] = await generated();

    await userEvent.click(within(first).getByTestId("comment-open"));
    expect(within(first).getByTestId("comment-submit")).toBeDisabled();

    await userEvent.type(within(first).getByTestId("comment-input"), "   ");
    // Whitespace is not a comment.
    expect(within(first).getByTestId("comment-submit")).toBeDisabled();

    await userEvent.type(within(first).getByTestId("comment-input"), "Real note.");
    expect(within(first).getByTestId("comment-submit")).toBeEnabled();
  });

  it("records a comment without rewriting the recommendation", async () => {
    const [first] = await generated();

    await userEvent.click(within(first).getByTestId("comment-open"));
    await userEvent.type(
      within(first).getByTestId("comment-input"),
      "HKMA's TSP is not our TPSP.",
    );
    await userEvent.click(within(first).getByTestId("comment-submit"));

    await waitFor(() => {
      const card = screen
        .getAllByTestId("recommendation")
        .find((el) => el.getAttribute("data-rec-id") === "first")!;
      expect(within(card).getByTestId("comment")).toHaveTextContent(
        /HKMA's TSP is not our TPSP/,
      );
    });
    // The recommendation itself is untouched — commenting is not rewriting.
    expect(screen.getByText("First recommendation")).toBeInTheDocument();
    expect(screen.queryByTestId("rewritten-marker")).not.toBeInTheDocument();
  });

  it("rewrites one card and shows what it said before", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ id: "only", title: "Original wording" })],
      rewrittenTitle: "Rewritten wording",
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    const card = await screen.findByTestId("recommendation");

    await userEvent.click(within(card).getByTestId("rewrite"));

    await waitFor(() =>
      expect(screen.getByText("Rewritten wording")).toBeInTheDocument(),
    );
    // Not silent: the marker says it changed, and the disclosure holds the
    // superseded text.
    expect(screen.getByTestId("rewritten-marker")).toBeInTheDocument();
    await userEvent.click(screen.getByTestId("revisions-toggle"));
    expect(screen.getByTestId("revision")).toHaveTextContent("Original wording");
  });

  it("rewrites only the card asked for", async () => {
    resetRecommendations({
      nextBatch: [
        makeRecommendation({ id: "first", title: "First recommendation" }),
        makeRecommendation({ id: "second", title: "Second recommendation" }),
      ],
      rewrittenTitle: "Only this one changed",
    });
    const cards = await generated();

    await userEvent.click(within(cards[0]).getByTestId("rewrite"));

    await waitFor(() =>
      expect(screen.getByText("Only this one changed")).toBeInTheDocument(),
    );
    // The sibling is untouched.
    expect(screen.getByText("Second recommendation")).toBeInTheDocument();
    expect(screen.getAllByTestId("recommendation")).toHaveLength(2);
  });

  it("keeps the card unchanged when the rewrite fails", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ id: "only", title: "Untouched" })],
      failRewrite: true,
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    const card = await screen.findByTestId("recommendation");

    await userEvent.click(within(card).getByTestId("rewrite"));

    expect(
      await screen.findByText(/rewrite could not be completed/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Untouched")).toBeInTheDocument();
    expect(screen.queryByTestId("rewritten-marker")).not.toBeInTheDocument();
  });

  it("surfaces a failed comment without losing what was typed", async () => {
    resetRecommendations({
      nextBatch: [makeRecommendation({ id: "only" })],
      failComment: true,
    });
    renderCard();
    await userEvent.click(await screen.findByTestId("generate"));
    const card = await screen.findByTestId("recommendation");

    await userEvent.click(within(card).getByTestId("comment-open"));
    await userEvent.type(
      within(card).getByTestId("comment-input"),
      "A note I do not want to retype.",
    );
    await userEvent.click(within(card).getByTestId("comment-submit"));

    expect(
      await screen.findByText(/could not save that comment/i),
    ).toBeInTheDocument();
  });
});
