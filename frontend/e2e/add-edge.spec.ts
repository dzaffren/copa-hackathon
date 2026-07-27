import { test, expect } from "@playwright/test";

// Happy-path E2E for connecting two existing documents (spec Verification > E2E).
// Requires the FastAPI engine and the Vite app running — see e2e/README.md.
//
// NOTE: a run appends an edge to the opres-v2 fixture, a tracked path —
// `git checkout data/workstreams/opres-v2` after a local run.

test.describe("Connect two existing documents", () => {
  test("add an edge from the viewed node to another on the canvas", async ({
    page,
  }) => {
    await page.goto("/workstreams/opres-v2");

    // Open a document node; its panel offers Add edge.
    await page.getByRole("button", { name: "BCBS OpRes 2021" }).click();
    await page.getByRole("button", { name: /add edge/i }).click();

    // The viewed node is not offered as a target — no self-connection.
    const target = page.getByLabel("Connect to");
    await expect(target.locator("option")).not.toHaveValue("bcbs-opres-2021");

    await target.selectOption({ label: "HKMA SPM OR-2" });
    await page.getByLabel("Connection type").selectOption("references");

    const submit = page.getByRole("button", { name: /^add edge$/i }).last();
    await expect(submit).toBeEnabled();
    await submit.click();

    // The dialog closes and the new connection is on the canvas.
    await expect(page.getByLabel("Connection type")).toHaveCount(0);
    await expect(
      page.getByRole("button", {
        name: /^edge references bcbs-opres-2021 to hkma-spm-or2/,
      }),
    ).toBeVisible();
  });
});
