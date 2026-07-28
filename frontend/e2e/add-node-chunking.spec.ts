import { test, expect } from "@playwright/test";

// Happy-path E2E for add-node-with-chunking (spec Verification > E2E).
// Requires the FastAPI engine and the Vite app running — see e2e/README.md.
//
// This is the ONLY place the multipart round-trip is exercised end to end: a
// FormData `fetch` never resolves under MSW v2 + jsdom, so the Vitest suite
// (src/features/workstream-graph/AddNodeDialog.test.tsx) stops at the
// `createNode` call and this spec covers the real upload.
//
// NOTE: the run adds a node to the opres-v2 fixture, which is a tracked path —
// `git checkout data/workstreams/opres-v2` after a local run.

const TITLE = "BCBS Principles for Operational Resilience 2021";

test.describe("Add a document and break it into passages", () => {
  test("attach a PDF, pick semi-structured, see the node on the canvas", async ({
    page,
  }) => {
    await page.goto("/workstreams/opres-v2");

    const before = await page.locator("svg circle").count();

    await page.getByRole("button", { name: /add node/i }).click();

    await page.getByRole("radio", { name: "international-standard" }).click();
    await page.getByLabel("Title").fill(TITLE);
    await page
      .getByLabel("Description")
      .fill("Basel Committee principles paper, 2021.");

    // The breaking-up method picker offers exactly three options and defaults
    // to semi-structured — the safe choice for an arbitrary upload.
    const methods = page.getByRole("radiogroup", {
      name: "Breaking-up method",
    });
    await expect(methods.getByRole("radio")).toHaveCount(3);
    await expect(
      methods.getByRole("radio", { name: "semi-structured" }),
    ).toBeChecked();

    // A numbered-paragraph document the semi-structured segmenter can walk.
    await page.getByLabel("Attachment").setInputFiles({
      name: "bcbs-opres-2021.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from(
        "# Principles for operational resilience\n\n" +
          "1.1 A bank should establish a governance framework for operational " +
          "resilience approved by the board and reviewed at least annually.\n\n" +
          "1.2 A bank should identify and map its critical operations and the " +
          "people, processes, technology and third parties that support them.\n",
      ),
    });

    await page.getByRole("button", { name: /add edge/i }).click();
    await page.getByLabel("Edge 1 target").selectOption({ label: /OpRes/ });
    await page.getByLabel("Edge 1 type").selectOption("references");

    const submit = page.getByRole("button", { name: /add to graph/i });
    await expect(submit).toBeEnabled();
    await submit.click();

    // The dialog closes and the chunked node joins the canvas.
    await expect(page.getByRole("button", { name: TITLE })).toBeVisible();
    await expect(page.locator("svg circle")).toHaveCount(before + 1);
  });
});
