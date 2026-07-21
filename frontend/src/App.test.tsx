import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderApp } from "@/test/utils";

describe("App smoke", () => {
  it("renders the home dashboard with a card linking into a workstream", async () => {
    renderApp("/");
    // The dashboard lists the seeded workstreams as cards linking to the graph.
    // Both the sidebar entry and the dashboard card link to the same route, so
    // assert that at least one such link resolves rather than a single match.
    const links = await screen.findAllByRole("link", {
      name: /Operational Resilience/i,
    });
    expect(
      links.some((l) => l.getAttribute("href") === "/workstreams/opres-v2"),
    ).toBe(true);
  });
});
