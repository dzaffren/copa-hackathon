import { test, expect, type Page } from "@playwright/test";
import { execFileSync } from "node:child_process";
import path from "node:path";

/**
 * The Reviewed tab in the open-draft view (spec Verification > E2E).
 *
 * The loop this epic exists to close: accept a finding in the Pairwise Findings
 * box, open the draft, and find it waiting. On `open-finance-pd-2026` every
 * acceptance a drafter can make is on a second-order edge, so before the
 * widening the tab was empty no matter how much she had judged.
 *
 * Requires the FastAPI engine (:8000) and Vite (:5173) — see e2e/README.md. No
 * model credentials needed.
 *
 * WRITES TO TRACKED PATHS: accepting and withdrawing persist review state into
 * data/workstreams/open-finance-pd-2026/findings/. Run
 * `git checkout data/workstreams/open-finance-pd-2026` afterwards.
 */

const WS = "open-finance-pd-2026";
const TASK = "open-finance-pd-2026-pd";
const TASK_URL = `/workstreams/${WS}/tasks/${TASK}`;
const DRAFT_URL = `${TASK_URL}/draft`;

function group(page: Page, label: string) {
  return page.locator(`[data-testid="finding-group"][data-label="${label}"]`);
}

/** How many findings the Reviewed tab already holds.
 *
 *  Review state persists to the fixture, so every assertion is a DELTA from the
 *  count at the start of the test rather than an absolute. Combined with the
 *  per-test reset below this is belt and braces, but it keeps a single test
 *  runnable on a tree where someone has already accepted things by hand.
 */
async function reviewedBaseline(page: Page): Promise<number> {
  await page.goto(DRAFT_URL);
  await expect(page.getByTestId("draft-surface")).toBeVisible();
  await expect(page.getByTestId("count-reviewed")).toBeVisible();
  return Number(await page.getByTestId("count-reviewed").innerText());
}

// Accepting writes review state into the tracked fixture, so without a reset the
// specs only pass in one order on a clean tree. `git checkout` restores the
// findings files between tests; the note in the file header still applies for a
// run that is interrupted.
test.beforeEach(() => {
  execFileSync("git", ["checkout", "--", `data/workstreams/${WS}`], {
    cwd: path.resolve(process.cwd(), ".."),
  });
});

/** Accept `count` findings from one label group, through the box, and return
 *  their ids — the drafter's real path, not a seeded fixture. */
async function acceptFromBox(
  page: Page,
  label: string,
  count: number,
): Promise<string[]> {
  await page.goto(TASK_URL);
  const g = group(page, label);
  await expect(g.getByTestId("finding-card").first()).toBeVisible();

  const ids: string[] = [];
  for (let i = 0; i < count; i += 1) {
    // Always the first pending card: accepted ones sink, so the top of the
    // group is the next unjudged finding.
    const card = g
      .locator('[data-testid="finding-card"][data-review-state="pending"]')
      .first();
    const id = await card.getAttribute("data-finding-id");
    await card.getByRole("button", { name: /Accept/ }).click();
    await expect(g.locator(`[data-finding-id="${id}"]`)).toHaveAttribute(
      "data-review-state",
      "accepted",
    );
    ids.push(id!);
  }
  return ids;
}

/** Accept `count` pending findings that sit on one named pair, wherever in the
 *  label groups they fall. Used when a test needs findings from a SPECIFIC pair
 *  rather than a specific label. */
async function acceptFromPair(
  page: Page,
  edgeId: string,
  count: number,
): Promise<string[]> {
  await page.goto(TASK_URL);
  await expect(group(page, "differs-on")).toBeVisible();

  const ids: string[] = [];
  for (let i = 0; i < count; i += 1) {
    const card = page
      .locator(
        `[data-testid="finding-card"][data-edge-id="${edgeId}"]` +
          `[data-review-state="pending"]`,
      )
      .first();
    const id = await card.getAttribute("data-finding-id");
    await card.getByRole("button", { name: /Accept/ }).click();
    await expect(page.locator(`[data-finding-id="${id}"]`)).toHaveAttribute(
      "data-review-state",
      "accepted",
    );
    ids.push(id!);
  }
  return ids;
}

test.describe("Reviewed tab", () => {
  test("holds acceptances made on pairs the draft is not part of", async ({
    page,
  }) => {
    const before = await reviewedBaseline(page);
    const accepted = await acceptFromBox(page, "differs-on", 3);

    await page.goto(DRAFT_URL);
    await expect(page.getByTestId("linkage-ref-card")).toHaveCount(before + 3);
    await expect(page.getByTestId("count-reviewed")).toHaveText(
      String(before + 3),
    );

    // Each accepted finding is individually present — these all sit on the RMiT
    // pair, which is two steps from the draft and was invisible here before.
    for (const id of accepted) {
      await expect(page.locator(`[data-finding-id="${id}"]`)).toBeVisible();
    }
  });

  test("gathers acceptances from across the whole neighbourhood", async ({
    page,
  }) => {
    const before = await reviewedBaseline(page);
    // Accept from two NAMED pairs. Picking by label would not do it: HKMA leads
    // both differs-on and goes-beyond on this fixture, so "two labels" can
    // easily mean one edge, and the test would prove nothing about aggregation.
    const fromHkma = await acceptFromPair(
      page,
      "e-hkma_open_api_framework--ed_open_finance_2025",
      2,
    );
    const fromRmit = await acceptFromPair(
      page,
      "e-rmit_2025--ed_open_finance_2025",
      2,
    );

    await page.goto(DRAFT_URL);
    await expect(page.getByTestId("linkage-ref-card")).toHaveCount(before + 4);

    // All four are present, and they came off two different pairs — the tab is
    // genuinely aggregating across the neighbourhood.
    const edgeIds = new Set<string>();
    for (const id of [...fromHkma, ...fromRmit]) {
      const card = page.locator(`[data-finding-id="${id}"]`);
      await expect(card).toBeVisible();
      edgeIds.add((await card.getAttribute("data-edge-id"))!);
    }
    expect(edgeIds.size).toBe(2);

    // Every card names both of its documents — with findings arriving from
    // several pairs, one title would not identify them.
    await expect(page.getByTestId("linkage-ref-card").first()).toContainText(
      "ED Open Finance 2025",
    );
  });

  test("offers two tabs and no Related placeholder", async ({ page }) => {
    await page.goto(DRAFT_URL);

    await expect(page.getByRole("tab")).toHaveCount(2);
    await expect(page.getByRole("tab", { name: /Reviewed/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Copilot/ })).toBeVisible();
    await expect(page.getByRole("tab", { name: /Related/ })).toHaveCount(0);
    await expect(page.getByTestId("related-empty")).toHaveCount(0);
  });

  test("a card opens the comparison with its clauses quoted", async ({
    page,
  }) => {
    await acceptFromBox(page, "differs-on", 1);

    await page.goto(DRAFT_URL);
    const card = page.getByTestId("linkage-ref-card").first();
    const findingId = await card.getAttribute("data-finding-id");
    await card.locator("p").first().click();

    await expect(page).toHaveURL(
      new RegExp(
        `/edges/.+/review\\?finding=${encodeURIComponent(findingId!)}`,
      ),
    );
    // Clause text is quoted here, and only here — the cards carry numbers.
    await expect(page.getByLabel("findings")).toBeVisible();
    await expect(
      page.locator('[data-testid="finding-card"][data-active="true"]'),
    ).toBeVisible();
  });

  test("withdrawing an acceptance removes it and returns it to the box", async ({
    page,
  }) => {
    const before = await reviewedBaseline(page);
    const [accepted] = await acceptFromBox(page, "aligns-with", 2);

    await page.goto(DRAFT_URL);
    await expect(page.getByTestId("count-reviewed")).toHaveText(
      String(before + 2),
    );

    await page
      .locator(`[data-finding-id="${accepted}"]`)
      .getByRole("button", { name: /Withdraw/ })
      .click();

    await expect(page.locator(`[data-finding-id="${accepted}"]`)).toHaveCount(
      0,
    );
    await expect(page.getByTestId("count-reviewed")).toHaveText(
      String(before + 1),
    );

    // One decision, everywhere: pending again on the task page.
    await page.goto(TASK_URL);
    await expect(
      page.locator(`[data-finding-id="${accepted}"]`),
    ).toHaveAttribute("data-review-state", "pending");
  });

  test("reflects a decision made moments earlier", async ({ page }) => {
    const before = await reviewedBaseline(page);
    // Accept, then walk Open draft as a drafter would rather than navigating by
    // URL — this is the handoff the epic is about.
    const [accepted] = await acceptFromBox(page, "silent-on", 1);
    await page.getByRole("link", { name: /Open draft/i }).click();

    await expect(page.getByTestId("draft-surface")).toBeVisible();
    await expect(page.locator(`[data-finding-id="${accepted}"]`)).toBeVisible();
    await expect(page.getByTestId("count-reviewed")).toHaveText(
      String(before + 1),
    );
  });
});
