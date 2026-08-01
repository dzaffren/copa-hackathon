import { test, expect, type Page } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

/**
 * Bookmarking, and carrying the selection into the drafting workspace
 * (spec-bookmark-and-carry-forward.md — Verification > E2E).
 *
 * The loop this story closes: mark a recommendation on the task page, open the
 * draft, and find it waiting beside the editor. Runs on `open-finance-pd-2026`,
 * which ships a generated set — no model credentials needed.
 *
 * WRITES TO A TRACKED PATH: bookmarking persists into
 * data/workstreams/open-finance-pd-2026/recommendations/. `afterEach` restores
 * that one file byte-for-byte. It deliberately does NOT `git checkout` the
 * workstream — that destroys the drafter's accepted findings and the graph's
 * source_pdf fields, as it did twice during this feature's development.
 */

const WS = "open-finance-pd-2026";
const TASK = "open-finance-pd-2026-pd";
const TASK_URL = `/workstreams/${WS}/tasks/${TASK}`;
const DRAFT_URL = `${TASK_URL}/draft`;

const RECS_FILE = path.resolve(
  process.cwd(),
  "..",
  `data/workstreams/${WS}/recommendations/${TASK}.json`,
);

let snapshot: Buffer;

test.beforeEach(() => {
  snapshot = readFileSync(RECS_FILE);
});

test.afterEach(() => {
  writeFileSync(RECS_FILE, snapshot);
});

function cards(page: Page) {
  return page.getByTestId("recommendation");
}

async function bookmarkFirst(page: Page): Promise<string> {
  // A full navigation, not a client-side one: `afterEach` rewrites the
  // recommendations file between tests, so a cached TanStack query from a prior
  // test would otherwise decide what this one sees.
  await page.goto(TASK_URL, { waitUntil: "networkidle" });
  await expect(cards(page).first()).toBeVisible();
  const first = cards(page).first();
  const recId = (await first.getAttribute("data-rec-id"))!;

  // Wait for the PATCH itself, not just the optimistic flip: the toggle marks
  // immediately from cache, which can be true before the write has reached disk —
  // and the next navigation re-reads the file.
  const [response] = await Promise.all([
    page.waitForResponse(
      (res) =>
        res.url().includes(`/recommendations/${recId}`) &&
        res.request().method() === "PATCH",
    ),
    first.getByTestId("bookmark-toggle").click(),
  ]);
  expect(response.ok()).toBe(true);

  await expect(
    page.locator(`[data-rec-id="${recId}"] [data-testid="bookmark-toggle"]`),
  ).toHaveAttribute("aria-pressed", "true");
  return recId;
}

test("a bookmarked recommendation appears beside the draft", async ({ page }) => {
  const recId = await bookmarkFirst(page);

  await page.goto(DRAFT_URL, { waitUntil: "networkidle" });

  // The first tab, and it holds what she marked.
  await expect(page.getByRole("tab", { name: /Recommendations/ })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByTestId("draft-recommendation")).toHaveCount(1);
  await expect(page.getByTestId("draft-recommendation")).toHaveAttribute(
    "data-rec-id",
    recId,
  );
  await expect(page.getByTestId("count-recommendations")).toHaveText("1");

  // And ONLY that one: the task page holds several, so a count of 1 here is the
  // filter working, not a coincidence. Asserted in this test rather than its own
  // — a second test would need a second navigation, which races the write.
  await page.goto(TASK_URL, { waitUntil: "networkidle" });
  await expect(cards(page).first()).toBeVisible();
  expect(await cards(page).count()).toBeGreaterThan(1);
});

test("the evidence is readable beside the draft", async ({ page }) => {
  await bookmarkFirst(page);
  await page.goto(DRAFT_URL, { waitUntil: "networkidle" });
  const card = page.getByTestId("draft-recommendation");
  await expect(card).toBeVisible();

  await card.getByTestId("tab-citations-toggle").click();

  // A clause number and a real quotation — the citation rule, visible where she
  // is writing from it.
  const citations = card.getByTestId("tab-citations");
  await expect(citations).toBeVisible();
  expect((await citations.innerText()).length).toBeGreaterThan(60);
});

test("nothing beside the draft writes to the draft", async ({ page }) => {
  // The story's defining constraint: everything that reaches the page arrives
  // through the Copilot conversation, where it is reviewed.
  await bookmarkFirst(page);
  await page.goto(DRAFT_URL, { waitUntil: "networkidle" });
  const card = page.getByTestId("draft-recommendation");

  await expect(
    card.getByRole("button", { name: /draft this|insert|add to draft/i }),
  ).toHaveCount(0);
});

test("unbookmarking from the draft is reflected on the task page", async ({
  page,
}) => {
  const recId = await bookmarkFirst(page);
  await page.goto(DRAFT_URL, { waitUntil: "networkidle" });

  await page.getByTestId("draft-recommendation").getByTestId("unbookmark").click();

  await expect(page.getByTestId("tab-none-bookmarked")).toBeVisible();

  // One decision, everywhere.
  await page.goto(TASK_URL, { waitUntil: "networkidle" });
  await expect(
    page.locator(`[data-rec-id="${recId}"] [data-testid="bookmark-toggle"]`),
  ).toHaveAttribute("aria-pressed", "false");
});

test("the draft tab explains itself when nothing is bookmarked", async ({
  page,
}) => {
  await page.goto(DRAFT_URL, { waitUntil: "networkidle" });

  await expect(page.getByTestId("tab-none-bookmarked")).toContainText(
    /Bookmark a recommendation on the task page/i,
  );
});

test("the coverage figure matches the task page", async ({ page }) => {
  await page.goto(TASK_URL, { waitUntil: "networkidle" });
  const onTask = await page
    .getByTestId("not-yet-reflected")
    .getAttribute("data-count");

  await bookmarkFirst(page);
  await page.goto(DRAFT_URL, { waitUntil: "networkidle" });

  // Measured against every generated recommendation, not the bookmarked subset,
  // so the number means the same thing on both surfaces.
  await expect(page.getByTestId("tab-not-yet-reflected")).toHaveAttribute(
    "data-count",
    onTask!,
  );
});
