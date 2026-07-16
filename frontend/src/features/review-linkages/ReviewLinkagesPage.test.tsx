import { describe, it, expect } from "vitest";
import { screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";

const BCBS_EDGE = "e-opres_v0_3--bcbs_opres_2021"; // analysed, 3 findings
const FSB_EDGE = "e-opres_v0_3--fsb_3rd_party"; // not analysed
const url = (edge: string) => `/workstreams/opres-v2/edges/${edge}/review`;

function cards(): HTMLElement[] {
  return screen.getAllByTestId("finding-card");
}

function card(index: number): HTMLElement {
  return cards()[index];
}

async function loadReview(edge = BCBS_EDGE) {
  renderApp(url(edge));
  await screen.findByRole("heading", { level: 1 });
}

// scrollIntoView stubbing and review-state reset live in src/test/setup.ts.

describe("ReviewLinkagesPage — landing", () => {
  it("renders the pair heading, both clause panes and the findings sidebar", async () => {
    await loadReview();

    expect(
      screen.getByRole("heading", {
        name: /Operational Resilience PD — v0.3 ↔ BCBS OpRes 2021/,
      }),
    ).toBeInTheDocument();

    const source = screen.getByLabelText("source clauses");
    const target = screen.getByLabelText("target clauses");
    expect(within(source).getByText("OpRes PD 4.4")).toBeInTheDocument();
    expect(
      within(target).getByText("BCBS OpRes Principle 7"),
    ).toBeInTheDocument();
    expect(cards()).toHaveLength(3);
  });

  it("shows verbatim clause text, not a truncated summary", async () => {
    await loadReview();
    const source = screen.getByLabelText("source clauses");
    expect(
      within(source).getByText(
        "A financial institution shall map its dependencies on external service providers that support critical operations.",
      ),
    ).toBeInTheDocument();
  });

  it("starts with 3 findings, 0 accepted, 0 dismissed", async () => {
    await loadReview();
    expect(screen.getByTestId("count-total")).toHaveTextContent("3 findings");
    expect(screen.getByTestId("count-accepted")).toHaveTextContent(
      "0 accepted",
    );
    expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
      "0 dismissed",
    );
  });

  it("auto-selects the first finding and highlights its cited clauses", async () => {
    await loadReview();
    expect(card(0)).toHaveAttribute("data-active", "true");

    const source = screen.getByLabelText("source clauses");
    // "OpRes PD ...", not "Operational Resilience ...": the fixture draft is
    // namespaced away from the real Discussion Paper's clause numbers, which
    // the clause index now holds with entirely different text.
    const lit = within(source)
      .getAllByText(/OpRes PD/)
      .map((el) => el.closest("[data-clause]"))
      .filter((el) => el?.getAttribute("data-highlighted"));
    expect(lit).toHaveLength(1);
  });

  it("prompts to analyse when the edge has no findings yet", async () => {
    renderApp(url(FSB_EDGE));
    expect(
      await screen.findByText(/has not been analysed yet/i),
    ).toBeInTheDocument();
    expect(screen.queryByTestId("finding-card")).not.toBeInTheDocument();
  });
});

describe("ReviewLinkagesPage — selecting a finding", () => {
  it("moves the highlight to the newly clicked card's clauses", async () => {
    const user = userEvent.setup();
    await loadReview();

    await user.click(card(1));

    expect(card(1)).toHaveAttribute("data-active", "true");
    expect(card(0)).not.toHaveAttribute("data-active");
  });
});

describe("ReviewLinkagesPage — accept / dismiss / reopen", () => {
  it("accepting pins a badge, drops Accept, and bumps the accepted count", async () => {
    const user = userEvent.setup();
    await loadReview();

    await user.click(within(card(0)).getByRole("button", { name: "Accept" }));

    await waitFor(() =>
      expect(screen.getByTestId("count-accepted")).toHaveTextContent(
        "1 accepted",
      ),
    );
    const accepted = cards().find(
      (c) => c.getAttribute("data-review-state") === "accepted",
    )!;
    expect(within(accepted).getByTestId("accepted-badge")).toBeInTheDocument();
    expect(
      within(accepted).queryByRole("button", { name: "Accept" }),
    ).not.toBeInTheDocument();
  });

  it("dismissing greys the card, sinks it to the bottom, and offers Reopen", async () => {
    const user = userEvent.setup();
    await loadReview();
    const dismissedSummary = within(card(0)).getByText(
      /Dependency mapping/,
    ).textContent;

    await user.click(within(card(0)).getByRole("button", { name: "Dismiss" }));

    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );
    const last = card(cards().length - 1);
    expect(last).toHaveAttribute("data-review-state", "dismissed");
    expect(last).toHaveTextContent(dismissedSummary!);
    expect(
      within(last).getByRole("button", { name: "Reopen" }),
    ).toBeInTheDocument();
  });

  it("reopening restores the Accept/Dismiss controls and clears the count", async () => {
    const user = userEvent.setup();
    await loadReview();

    await user.click(within(card(0)).getByRole("button", { name: "Dismiss" }));
    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );
    const last = card(cards().length - 1);
    await user.click(within(last).getByRole("button", { name: "Reopen" }));

    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "0 dismissed",
      ),
    );
    expect(
      within(card(0)).getByRole("button", { name: "Accept" }),
    ).toBeInTheDocument();
  });

  it("never deletes a dismissed finding — the total holds", async () => {
    const user = userEvent.setup();
    await loadReview();

    await user.click(within(card(0)).getByRole("button", { name: "Dismiss" }));

    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );
    expect(screen.getByTestId("count-total")).toHaveTextContent("3 findings");
    expect(cards()).toHaveLength(3);
  });

  it("a dismissed card is inert — clicking it does not make it active", async () => {
    const user = userEvent.setup();
    await loadReview();

    await user.click(within(card(1)).getByRole("button", { name: "Dismiss" }));
    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );

    const dismissed = card(cards().length - 1);
    await user.click(dismissed);
    expect(dismissed).not.toHaveAttribute("data-active");
  });

  it("moves the active selection off a card that gets dismissed", async () => {
    const user = userEvent.setup();
    await loadReview();
    expect(card(0)).toHaveAttribute("data-active", "true");

    await user.click(within(card(0)).getByRole("button", { name: "Dismiss" }));

    await waitFor(() =>
      expect(screen.getByTestId("count-dismissed")).toHaveTextContent(
        "1 dismissed",
      ),
    );
    const active = cards().filter((c) => c.getAttribute("data-active"));
    expect(active).toHaveLength(1);
    expect(active[0]).toHaveAttribute("data-review-state", "pending");
  });
});
