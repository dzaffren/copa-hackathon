import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { Sidebar } from "./Sidebar";

function LocationProbe() {
  const loc = useLocation();
  return <div data-testid="loc">{loc.pathname}</div>;
}

function renderSidebar(initial = "/workstreams/opres-v2") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initial]}>
        <Sidebar activeWorkstreamId="opres-v2" />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Sidebar", () => {
  it("collapse toggle hides workstream names and reveals the icon-only rail", async () => {
    renderSidebar();
    expect(
      await screen.findByText("Operational Resilience v0.3"),
    ).toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("button", { name: /collapse sidebar/i }),
    );

    // Names + labels are gone from the DOM…
    expect(
      screen.queryByText("Operational Resilience v0.3"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("New workstream")).not.toBeInTheDocument();
    expect(screen.queryByText("Institution map")).not.toBeInTheDocument();
    // …but the rail icons/links remain reachable (via their title).
    expect(
      screen.getByRole("button", { name: /expand sidebar/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /new workstream/i }),
    ).toBeInTheDocument();
  });

  it("expands back after collapsing", async () => {
    renderSidebar();
    await screen.findByText("Operational Resilience v0.3");
    await userEvent.click(
      screen.getByRole("button", { name: /collapse sidebar/i }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /expand sidebar/i }),
    );
    expect(screen.getByText("Operational Resilience v0.3")).toBeInTheDocument();
    expect(screen.getByText("New workstream")).toBeInTheDocument();
  });

  it("+ New workstream navigates to /workstreams/new", async () => {
    renderSidebar();
    await userEvent.click(
      screen.getByRole("link", { name: /new workstream/i }),
    );
    expect(screen.getByTestId("loc")).toHaveTextContent("/workstreams/new");
  });

  it("Institution map navigates to /institution-map", async () => {
    renderSidebar();
    await userEvent.click(
      screen.getByRole("link", { name: /institution map/i }),
    );
    expect(screen.getByTestId("loc")).toHaveTextContent("/institution-map");
  });

  it("clicking a workstream navigates to its graph", async () => {
    renderSidebar();
    const item = await screen.findByRole("link", { name: /outsourcing v2/i });
    await userEvent.click(item);
    expect(screen.getByTestId("loc")).toHaveTextContent(
      "/workstreams/outsourcing-v2",
    );
  });
});
