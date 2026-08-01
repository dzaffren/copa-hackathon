import { test, expect, type Page } from "@playwright/test";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

/**
 * Commenting on a recommendation (spec-comment-and-rewrite.md — Verification > E2E).
 *
 * Rewriting is deliberately NOT exercised here: it reaches a live model, costs a
 * call, and would overwrite a card in the committed demo set with output nobody
 * reviewed. The rewrite path — identity preservation, the revisions trail, the
 * evidence floor, failure isolation — is covered against an injected stub in
 * engine/tests/test_api_recommendations.py, and its UI in
 * RecommendationsCard.test.tsx against MSW.
 *
 * WRITES TO A TRACKED PATH: commenting persists into
 * data/workstreams/open-finance-pd-2026/recommendations/. `afterEach` restores
 * that one file byte-for-byte, and nothing else in the workstream is touched.
 */

const WS = "open-finance-pd-2026";
const TASK = "open-finance-pd-2026-pd";
const TASK_URL = `/workstreams/${WS}/tasks/${TASK}`;

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

function firstCard(page: Page) {
  return page.getByTestId("recommendation").first();
}

async function openTask(page: Page) {
  await page.goto(TASK_URL);
  await expect(firstCard(page)).toBeVisible();
}

test("a comment records why a recommendation misses", async ({ page }) => {
  await openTask(page);
  const card = firstCard(page);
  const titleBefore = await card.locator("h3").innerText();

  await card.getByTestId("comment-open").click();
  await card
    .getByTestId("comment-input")
    .fill("HKMA's TSP is closer to our data consumer — ours is an operational vendor.");
  await card.getByTestId("comment-submit").click();

  const comment = card.getByTestId("comment");
  await expect(comment).toBeVisible();
  await expect(comment).toContainText(/operational vendor/);
  // Attributed and dated, from the server — not a client-supplied name.
  await expect(comment).toContainText("Aisyah R.");
  // Commenting is NOT rewriting: the recommendation itself is unchanged.
  await expect(card.locator("h3")).toHaveText(titleBefore);
  await expect(card.getByTestId("rewritten-marker")).toHaveCount(0);
});

test("an empty comment cannot be submitted", async ({ page }) => {
  await openTask(page);
  const card = firstCard(page);

  await card.getByTestId("comment-open").click();

  await expect(card.getByTestId("comment-submit")).toBeDisabled();
  await card.getByTestId("comment-input").fill("   ");
  // Whitespace is not a comment.
  await expect(card.getByTestId("comment-submit")).toBeDisabled();
});

test("a comment survives leaving and returning", async ({ page }) => {
  await openTask(page);
  const card = firstCard(page);
  const recId = await card.getAttribute("data-rec-id");

  await card.getByTestId("comment-open").click();
  await card.getByTestId("comment-input").fill("A correction worth keeping.");
  await card.getByTestId("comment-submit").click();
  await expect(card.getByTestId("comment")).toBeVisible();

  await page.reload();

  await expect(
    page.locator(`[data-rec-id="${recId}"] [data-testid="comment"]`),
  ).toContainText(/A correction worth keeping/);
});

test("several comments accumulate on one card, oldest first", async ({ page }) => {
  await openTask(page);
  const card = firstCard(page);

  for (const text of ["First point.", "Second point."]) {
    await card.getByTestId("comment-open").click();
    await card.getByTestId("comment-input").fill(text);
    await card.getByTestId("comment-submit").click();
    await expect(card.getByTestId("comment").last()).toContainText(text);
  }

  const comments = await card.getByTestId("comment").allInnerTexts();
  expect(comments).toHaveLength(2);
  expect(comments[0]).toContain("First point.");
  expect(comments[1]).toContain("Second point.");
});

test("nothing the drafter writes is promoted into the guardrails", async ({
  page,
}) => {
  // The story's defining constraint. Making a correction permanent is her own
  // deliberate edit — a model re-wording a situated note into a standing rule
  // would be authoring the rules it then follows.
  await openTask(page);
  const card = firstCard(page);

  await card.getByTestId("comment-open").click();
  await card
    .getByTestId("comment-input")
    .fill("BNM never cites another PD by provision number.");
  await card.getByTestId("comment-submit").click();
  await expect(card.getByTestId("comment")).toBeVisible();

  await page.getByTestId("guardrails-badge").click();
  const box = page.getByTestId("guardrails-body");
  await expect(box).toBeVisible();
  await expect(box).not.toHaveValue(/BNM never cites another PD by provision number/);
  // Still the shipped defaults, untouched by the comment.
  await expect(page.getByText(/Showing the shipped defaults/i)).toBeVisible();
});

test("a comment does not disturb the other recommendations", async ({ page }) => {
  await openTask(page);
  const before = await page.getByTestId("recommendation").allInnerTexts();
  const card = firstCard(page);

  await card.getByTestId("comment-open").click();
  await card.getByTestId("comment-input").fill("Only about this card.");
  await card.getByTestId("comment-submit").click();
  await expect(card.getByTestId("comment")).toBeVisible();

  const after = await page.getByTestId("recommendation").allInnerTexts();
  expect(after).toHaveLength(before.length);
  // Every sibling is byte-identical; only the commented card grew.
  for (let i = 1; i < before.length; i += 1) {
    expect(after[i]).toBe(before[i]);
  }
});
