import { describe, it, expect } from "vitest";
import { screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderApp } from "@/test/utils";

async function loadForm() {
  renderApp("/workstreams/new");
  await screen.findByRole("heading", { name: "Create new workstream" });
}

function pills(): HTMLElement[] {
  return screen.queryAllByTestId("reviewer-pill");
}

describe("NewWorkstreamPage — landing", () => {
  it("renders the breadcrumb, intent line and three cards", async () => {
    await loadForm();

    expect(screen.getByText("← Workstreams / New")).toBeInTheDocument();
    expect(
      screen.getByText(
        /one Discussion Paper, Exposure Draft, or Policy Document/i,
      ),
    ).toBeInTheDocument();
    for (const name of ["Basics", "People"]) {
      expect(screen.getByRole("heading", { name })).toBeInTheDocument();
    }
    // Access is a fieldset/legend rather than a heading — the right semantic
    // for a radio group, which exposes role="group" named by its legend.
    expect(screen.getByRole("group", { name: "Access" })).toBeInTheDocument();
  });

  it("pre-fills the owner as Aisyah R. (you) and offers no way to change it", async () => {
    await loadForm();
    expect(screen.getByText("Aisyah R.")).toBeInTheDocument();
    expect(screen.getByText("(you)")).toBeInTheDocument();
    expect(screen.queryByLabelText(/^Owner$/i)).not.toBeInTheDocument();
  });

  it("defaults to Team-only access and the PD deliverable type", async () => {
    await loadForm();
    expect(screen.getByRole("radio", { name: /Team-only/ })).toBeChecked();
    expect(
      screen.getByRole("radio", { name: /Department-wide/ }),
    ).not.toBeChecked();
    expect(screen.getByLabelText("Deliverable type")).toHaveValue("PD");
  });

  it("never offers the owner as a reviewer of her own workstream", async () => {
    await loadForm();
    await screen.findByRole("button", { name: "+ Farid M." });
    expect(
      screen.queryByRole("button", { name: "+ Aisyah R." }),
    ).not.toBeInTheDocument();
  });
});

describe("NewWorkstreamPage — reviewers", () => {
  it("adds a reviewer as a removable pill and takes it out of the picker", async () => {
    const user = userEvent.setup();
    await loadForm();

    await user.click(await screen.findByRole("button", { name: "+ Farid M." }));

    expect(pills()).toHaveLength(1);
    expect(pills()[0]).toHaveTextContent("Farid M.");
    expect(
      screen.queryByRole("button", { name: "+ Farid M." }),
    ).not.toBeInTheDocument();
  });

  it("removes a reviewer and returns them to the picker", async () => {
    const user = userEvent.setup();
    await loadForm();
    await user.click(await screen.findByRole("button", { name: "+ Farid M." }));
    await user.click(await screen.findByRole("button", { name: "+ Priya S." }));

    await user.click(screen.getByRole("button", { name: "Remove Farid M." }));

    expect(pills()).toHaveLength(1);
    expect(pills()[0]).toHaveTextContent("Priya S.");
    expect(
      screen.getByRole("button", { name: "+ Farid M." }),
    ).toBeInTheDocument();
  });
});

describe("NewWorkstreamPage — validation", () => {
  it("blocks submission with an empty name and flags the field", async () => {
    const user = userEvent.setup();
    await loadForm();

    await user.click(screen.getByRole("button", { name: "Create workstream" }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      /Give the workstream a name/i,
    );
    expect(screen.getByLabelText("Workstream name")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    // Still on the form — nothing was created.
    expect(
      screen.getByRole("heading", { name: "Create new workstream" }),
    ).toBeInTheDocument();
  });

  it("blocks a whitespace-only name", async () => {
    const user = userEvent.setup();
    await loadForm();

    await user.type(screen.getByLabelText("Workstream name"), "   ");
    await user.click(screen.getByRole("button", { name: "Create workstream" }));

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("clears the error once the drafter starts typing", async () => {
    const user = userEvent.setup();
    await loadForm();
    await user.click(screen.getByRole("button", { name: "Create workstream" }));
    expect(screen.getByRole("alert")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Workstream name"), "C");

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("surfaces a server-side field error on the input it belongs to", async () => {
    const user = userEvent.setup();
    await loadForm();

    // Passes the client check, fails the server's 120-char rule.
    await user.type(screen.getByLabelText("Workstream name"), "x".repeat(121));
    await user.click(screen.getByRole("button", { name: "Create workstream" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /120 characters or fewer/i,
    );
    expect(screen.getByLabelText("Workstream name")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });
});

describe("NewWorkstreamPage — creating", () => {
  it("creates with every field filled and lands on the new empty graph", async () => {
    const user = userEvent.setup();
    await loadForm();

    await user.type(
      screen.getByLabelText("Workstream name"),
      "Climate Risk PD v2 2026",
    );
    await user.type(
      screen.getByLabelText("Short description"),
      "Response to BCBS climate principles.",
    );
    await user.selectOptions(screen.getByLabelText("Deliverable type"), "ED");
    await user.type(screen.getByLabelText("Target publication"), "Q4 2026");
    await user.click(await screen.findByRole("button", { name: "+ Farid M." }));
    await user.click(screen.getByRole("button", { name: "+ Priya S." }));

    await user.click(screen.getByRole("button", { name: "Create workstream" }));

    // Landed on the graph screen — its "+ Add node" action is the tell.
    expect(
      await screen.findByRole("button", { name: /add node/i }),
    ).toBeInTheDocument();
  });

  it("lists the new workstream in the sidebar after landing", async () => {
    const user = userEvent.setup();
    await loadForm();

    await user.type(
      screen.getByLabelText("Workstream name"),
      "Cyber Risk DP 2027",
    );
    await user.click(screen.getByRole("button", { name: "Create workstream" }));

    await screen.findByRole("button", { name: /add node/i });
    const sidebar = screen.getByRole("complementary");
    expect(
      await within(sidebar).findByText("Cyber Risk DP 2027"),
    ).toBeInTheDocument();
  });

  it("creates with only the required fields", async () => {
    const user = userEvent.setup();
    await loadForm();

    await user.type(
      screen.getByLabelText("Workstream name"),
      "Bare Minimum PD",
    );
    await user.click(screen.getByRole("button", { name: "Create workstream" }));

    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { name: "Create new workstream" }),
      ).not.toBeInTheDocument(),
    );
  });
});

describe("NewWorkstreamPage — cancel", () => {
  it("leaves the form without creating anything", async () => {
    const user = userEvent.setup();
    await loadForm();
    await user.type(screen.getByLabelText("Workstream name"), "Abandoned PD");

    await user.click(screen.getByRole("link", { name: "Cancel" }));

    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { name: "Create new workstream" }),
      ).not.toBeInTheDocument(),
    );
    expect(screen.queryByText("Abandoned PD")).not.toBeInTheDocument();
  });
});
