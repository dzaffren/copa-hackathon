// Tests for WorkspaceStrip (spec-drafter-workspace.md · UI/Frontend Requirements
// "Workspace strip"; Test 11 "Switch to supervisor"). The strip names the drafter
// and her single working draft and offers the one-click hand-off to the supervisor
// view — and it carries NO approve / submit action (approval is a separate manager
// step handled elsewhere, never on this screen).

import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import WorkspaceStrip from "./WorkspaceStrip";

/** Render the strip inside a router so its `<Link>` has navigation context, with a
 *  stub `/supervisor` destination to prove the route actually changes on click. */
function renderStrip() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<WorkspaceStrip />} />
        <Route path="/supervisor" element={<div>SUPERVISOR DESTINATION</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("WorkspaceStrip", () => {
  it("names the drafter, her role, and her single working draft", () => {
    renderStrip();
    expect(screen.getByText("Aisyah R.")).toBeInTheDocument();
    expect(screen.getByText(/policy drafter/i)).toBeInTheDocument();
    expect(screen.getByText(/Drafting: RMiT v2/)).toBeInTheDocument();
  });

  it("offers a 'Switch to supervisor view' control and no approve / submit action", () => {
    renderStrip();
    expect(
      screen.getByRole("link", { name: "Switch to supervisor view" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", {
        name: /approve|submit|return to bank/i,
      }),
    ).not.toBeInTheDocument();
  });

  it("navigates to /supervisor when the switch control is clicked", async () => {
    renderStrip();
    // Wrap the click so React Router's navigation state update commits inside act.
    await act(async () => {
      await userEvent.click(
        screen.getByRole("link", { name: "Switch to supervisor view" }),
      );
    });
    expect(
      await screen.findByText("SUPERVISOR DESTINATION"),
    ).toBeInTheDocument();
  });
});
