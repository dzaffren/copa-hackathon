import { test, expect } from "@playwright/test";

// Happy-path E2E for extract-concepts (spec Verification > E2E).
// Requires the FastAPI engine and the Vite app running — see e2e/README.md.
//
// Extraction is synchronous and makes one small-model call per passage, so this
// spec needs live model credentials and a generous timeout. It also needs a
// node whose document has already been chunked (see add-node-chunking.spec.ts).
//
// NOTE: a run writes an axis cache under data/workstreams/opres-v2/axes/ and
// appends to graph.json — both tracked paths. `git checkout data/workstreams`
// after a local run.

test.describe("Extract a document's concepts", () => {
  test("open a node, extract concepts, see pills", async ({ page }) => {
    test.setTimeout(180_000); // one model call per passage

    await page.goto("/workstreams/opres-v2");
    await page.getByRole("button", { name: "BCBS OpRes 2021" }).click();

    // The four sections render in the fixed order.
    for (const heading of [
      "First-order neighbours",
      "Recent activity",
      "Metadata",
      "Concepts",
    ]) {
      await expect(page.getByText(heading, { exact: true })).toBeVisible();
    }

    const extract = page.getByRole("button", { name: /extract concepts/i });
    if (await extract.isVisible()) {
      await extract.click();
      // Pills replace the empty state once extraction finishes.
      await expect(page.getByTestId("concept-pill").first()).toBeVisible({
        timeout: 170_000,
      });
      await expect(extract).toHaveCount(0);
    }

    // Concepts persist: re-opening the node still shows the pills without a
    // second extraction.
    await expect(page.getByTestId("concept-pill").first()).toBeVisible();
  });
});
