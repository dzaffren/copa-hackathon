import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import { renderApp } from "@/test/utils";

describe("InstitutionMapPage", () => {
  it("lists cross-workstream linkages with a Review link into the _cross store", async () => {
    renderApp("/institution-map");

    // The default selection surfaces the seeded OpRes ↔ Open Finance cross-link.
    const row = await screen.findByTestId("cross-link-row");
    expect(within(row).getByText(/OpRes DP/i)).toBeInTheDocument();

    const review = within(row).getByRole("link", { name: /review/i });
    expect(review).toHaveAttribute(
      "href",
      "/workstreams/_cross/edges/x-open_finance_ed--opres_dp_2025/review",
    );
  });
});
