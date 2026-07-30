import { test, expect, type Page } from "@playwright/test";

// E2E for the drafter-editable regulatory profile (spec-editable-node-metadata.md,
// Verification > E2E).
// Requires the FastAPI engine and the Vite app running — see e2e/README.md.
//
// Why these three scenarios are here and not in Vitest: the claim this story
// makes is PERSISTENCE — that what Aisyah types survives her leaving and coming
// back. Under MSW that only proves a mock echoed the payload back, so the round
// trip has to land on the real filesystem side-file
// (data/workstreams/{ws}/concepts/{node}.json) to mean anything. The component
// suite (NodeMetadataForm.test.tsx, NodeDetailPanel.test.tsx) covers the form's
// own behaviour — comma splitting, blank-to-null, cancel, the failed-save
// retry — against a mock, which is the right place for it.
//
// NOTE: the run writes a profile for BIS Papers 168 in the open-finance-pd-2026
// fixture, a tracked path. Afterwards delete the untracked side-file
// `data/workstreams/open-finance-pd-2026/concepts/bis-papers-168.json`; nothing
// tracked is modified, so no `git checkout` is needed.

// A document nobody has profiled: it carries passages and an axis cache, but no
// concepts side-file, so the panel opens on the un-set state this story replaces.
const UNPROFILED_TITLE = "BIS Papers 168";

// Every document in this workstream hangs off the published ED, so it is the one
// node from which any other is one neighbour-chip away.
const HUB_TITLE = "ED Open Finance 2025";

// The read-mode placeholder the story removes. A drafter must never see it: it
// describes a dead end ("not enabled"), where the truth is "nobody has filled
// this in yet, and you can".
const RETIRED_PLACEHOLDER = "Concept extraction not enabled in MVP1";

function nodePanelOpen(page: Page) {
  return page
    .getByText("First-order neighbours", { exact: true })
    .isVisible()
    .catch(() => false);
}

/**
 * Open a node's detail panel by title.
 *
 * The graph is drawn by react-force-graph-2d into a single `<canvas>`, so in a
 * real browser there is no per-node DOM element to click — the accessible
 * one-button-per-node DOM only exists in the Vitest stub
 * (src/test/mocks/react-force-graph-2d.tsx). The only DOM handles on a node are
 * the panel's neighbour chips, so this sweeps the canvas until *some* node
 * opens, hops to the hub, then clicks the wanted node's chip. Same approach as
 * add-task-node.spec.ts; see e2e/README.md.
 */
async function openNode(page: Page, title: string) {
  const canvas = page.getByTestId("graph-canvas");
  await canvas.waitFor();
  const heading = page.locator("h2").first();

  if (!(await nodePanelOpen(page))) {
    const box = (await canvas.boundingBox())!;
    // Node radii are 8px (anchor) / 13px (task), so a 12px stride cannot skip one.
    sweep: for (let y = box.y + 6; y < box.y + box.height - 6; y += 12) {
      for (let x = box.x + 6; x < box.x + box.width - 6; x += 12) {
        await page.mouse.click(x, y);
        if (await nodePanelOpen(page)) break sweep;
      }
    }
    expect(
      await nodePanelOpen(page),
      "swept the canvas without opening any node",
    ).toBe(true);
  }

  if ((await heading.textContent())?.trim() === title) return;

  if ((await heading.textContent())?.trim() !== HUB_TITLE) {
    await page.getByRole("button", { name: HUB_TITLE }).first().click();
    await expect(heading).toHaveText(HUB_TITLE);
  }
  await page.getByRole("button", { name: title }).first().click();
  await expect(heading).toHaveText(title);
}

/** Expand the collapsed Metadata disclosure. */
async function openMetadata(page: Page) {
  await page.getByRole("button", { name: "Metadata" }).click();
  await expect(page.getByRole("button", { name: /^edit$/i })).toBeVisible();
}

test.describe("Fill in a document's regulatory profile", () => {
  // The canvas sweep needs more than the 30s default.
  test.setTimeout(180_000);

  test("a document nobody prepared offers an empty profile, not a dead end", async ({
    page,
  }) => {
    await page.goto("/workstreams/open-finance-pd-2026");
    await openNode(page, UNPROFILED_TITLE);
    await openMetadata(page);

    // Every field is offered, and each reads as unfilled rather than absent.
    await expect(page.getByText("Policy owner")).toBeVisible();
    await expect(page.getByText("Applicability")).toBeVisible();
    await expect(page.getByText("Empowerment framework")).toBeVisible();
    expect(await page.getByText("Not set").count()).toBeGreaterThanOrEqual(6);

    // ISMP is the one field whose emptiness has a documented cause, so it says
    // so instead of reading "Not set" like the rest.
    await expect(page.getByText("Pending — RH publication form")).toBeVisible();

    // The dead-end text is gone for good.
    await expect(page.getByText(RETIRED_PLACEHOLDER)).toHaveCount(0);
  });

  test("filling in a field that was not set, and it survives coming back", async ({
    page,
  }) => {
    await page.goto("/workstreams/open-finance-pd-2026");
    await openNode(page, UNPROFILED_TITLE);
    await openMetadata(page);

    await page.getByRole("button", { name: /^edit$/i }).click();

    await page.getByLabel("Policy owner").fill("Priya S.");
    await page
      .getByLabel("Legal basis")
      .fill("FSA 2013, IFSA 2013, DFIA 2002");
    await page.getByLabel("Effective date").fill("28 November 2025");
    // A closed dropdown, not free text — these are BNM handling categories.
    await page.getByLabel("ISMP classification").selectOption("SULIT");

    await page.getByRole("button", { name: /^save$/i }).click();

    // Read mode returns with the new values — the form is gone.
    await expect(page.getByRole("button", { name: /^save$/i })).toHaveCount(0);
    const profile = page.locator("dl").first();
    await expect(profile.getByText("Priya S.", { exact: true })).toBeVisible();
    // The comma-separated line became three separate chips, not one string.
    await expect(profile.getByText("FSA 2013", { exact: true })).toBeVisible();
    await expect(profile.getByText("IFSA 2013", { exact: true })).toBeVisible();
    await expect(profile.getByText("DFIA 2002", { exact: true })).toBeVisible();
    await expect(profile.getByText("SULIT", { exact: true })).toBeVisible();
    await expect(
      profile.getByText("28 November 2025", { exact: true }),
    ).toBeVisible();

    // The persistence claim: a full reload drops every client cache, so what
    // comes back can only have come off the side-file the server wrote.
    await page.reload();
    await openNode(page, UNPROFILED_TITLE);
    await openMetadata(page);

    const reloaded = page.locator("dl").first();
    await expect(reloaded.getByText("Priya S.", { exact: true })).toBeVisible();
    await expect(reloaded.getByText("DFIA 2002", { exact: true })).toBeVisible();
    await expect(reloaded.getByText("SULIT", { exact: true })).toBeVisible();
    await expect(
      reloaded.getByText("28 November 2025", { exact: true }),
    ).toBeVisible();
    // Fields left alone stayed unfilled rather than being invented.
    await expect(reloaded.getByText("Not set").first()).toBeVisible();
  });
});
