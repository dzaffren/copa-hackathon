import { test, expect } from "@playwright/test";

// Happy-path E2E for the Workstream Graph hero screen (spec Verification > E2E).
// Requires the FastAPI engine and the Vite app running — see e2e/README.md.
// The automated CI equivalent lives in
// src/features/workstream-graph/WorkstreamGraphPage.test.tsx (Vitest + MSW).

test.describe("Workstream graph screen", () => {
  test("landing → inspect node → inspect edge → add-node dialog", async ({
    page,
  }) => {
    await page.goto("/workstreams/opres-v2");

    // Canvas renders the 7-node primary subgraph (one circle per node).
    await expect(page.locator("svg circle")).toHaveCount(7);
    await expect(
      page.getByRole("button", { name: "BCBS OpRes 2021" }),
    ).toBeVisible();

    // Inspect a resource node → the panel offers "Open source".
    await page.getByRole("button", { name: "BCBS OpRes 2021" }).click();
    await expect(
      page.getByRole("button", { name: /open source/i }),
    ).toBeVisible();

    // Inspect the analysed BCBS edge → three finding cards, no Analyze CTA.
    await page
      .getByRole("button", {
        name: /^edge contributes-to opres-pd-v0-3 to bcbs-opres-2021/,
      })
      .click();
    await expect(page.getByRole("button", { name: /^Review$/ })).toHaveCount(3);
    await expect(
      page.getByRole("button", { name: /analyze linkages/i }),
    ).toHaveCount(0);

    // Open the Add-node dialog → "Add to graph" starts disabled (no edge yet).
    await page.getByRole("button", { name: /add node/i }).click();
    await expect(
      page.getByRole("button", { name: /add to graph/i }),
    ).toBeDisabled();
  });
});
