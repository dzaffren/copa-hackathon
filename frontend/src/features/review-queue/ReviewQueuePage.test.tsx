import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "@/test/utils";

describe("ReviewQueuePage", () => {
  it("lists cross-workstream linkages needing review with their status", async () => {
    renderApp("/review-queue");

    expect(
      await screen.findByRole("heading", { name: /Maker-checker review/i }),
    ).toBeInTheDocument();
    // Both seeded cross linkages appear under the default "open" filter.
    expect(await screen.findAllByTestId("queue-row")).toHaveLength(2);
    // The flagship pair is attributed correctly.
    expect(
      screen.getByText("Business Continuity Management"),
    ).toBeInTheDocument();
  });

  it("runs a full maker-checker flow with an audit trail, enforcing maker≠checker", async () => {
    const user = userEvent.setup();
    renderApp("/review-queue");

    // Show "all" so the linkage stays visible once it reaches a terminal state
    // (approved linkages correctly drop out of the default "open" filter).
    await screen.findAllByTestId("queue-row");
    await user.click(screen.getByRole("button", { name: /^all$/i }));

    // The first (flagship) linkage is selected by default.
    const panel = await screen.findByTestId("linkage-review-panel");
    expect(await within(panel).findByText("AI detected")).toBeInTheDocument();

    // Maker (default actor Farid M.) claims it.
    await user.click(within(panel).getByRole("button", { name: /Claim as maker/i }));
    expect(await within(panel).findByText("Maker review")).toBeInTheDocument();
    const audit = within(panel).getByTestId("audit-trail");
    expect(within(audit).getByText(/Farid M\./)).toBeInTheDocument();
    expect(within(audit).getByText(/claimed/)).toBeInTheDocument();

    // Maker submits for check.
    await user.click(within(panel).getByRole("button", { name: /Submit for check/i }));
    expect(await within(panel).findByText("Submitted for check")).toBeInTheDocument();

    // The maker cannot check their own work — picking up as Farid is refused.
    await user.click(within(panel).getByRole("button", { name: /Pick up as checker/i }));
    expect(
      await within(panel).findByText(/checker.*cannot be.*maker/i),
    ).toBeInTheDocument();

    // Switch actor to Priya S. and pick up as the checker.
    await user.selectOptions(within(panel).getByRole("combobox"), "ps");
    await user.click(within(panel).getByRole("button", { name: /Pick up as checker/i }));
    expect(await within(panel).findByText("Checker review")).toBeInTheDocument();

    // Checker approves.
    await user.click(within(panel).getByRole("button", { name: /^Approve$/i }));
    expect(await within(panel).findByText("Approved")).toBeInTheDocument();
    expect(within(within(panel).getByTestId("audit-trail")).getByText(/approved/)).toBeInTheDocument();
  });

  it("filters the queue by status", async () => {
    const user = userEvent.setup();
    renderApp("/review-queue");

    await screen.findAllByTestId("queue-row");
    // Nothing is approved yet → the Approved filter empties the list.
    await user.click(screen.getByRole("button", { name: /^Approved$/i }));
    expect(screen.queryByTestId("queue-row")).not.toBeInTheDocument();
    expect(screen.getByText(/No linkages match this filter/i)).toBeInTheDocument();
  });
});
