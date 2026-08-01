import { test, expect, type Page } from "@playwright/test";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";

/**
 * The Recommendations card on the task page (spec Verification > E2E).
 *
 * Runs on `open-finance-pd-2026`, which ships everything the card needs:
 * a working draft profile recording six policy requirements, 15 accepted
 * findings, and a committed pre-generated set of recommendations. That is the
 * build-and-persist strategy in CLAUDE.md — **no model credentials are needed to
 * read**, because generation already happened and its output is tracked.
 *
 * Requires the FastAPI engine (:8000) and Vite (:5173) — see e2e/README.md.
 *
 * The Generate button is deliberately NOT pressed here. It would reach a live
 * model, cost a call, and overwrite the committed demo set with output nobody
 * reviewed — so the button's presence and enabled state are asserted, and the
 * generate path itself is covered by the engine suite against an injected stub
 * (engine/tests/test_api_recommendations.py).
 *
 * WRITES: the guardrails test saves
 * data/workstreams/open-finance-pd-2026/guardrails.json, which is UNTRACKED.
 * `afterEach` deletes exactly that file and nothing else.
 *
 * It deliberately does NOT `git checkout data/workstreams/<ws>`, which is what
 * the older specs in this directory do. That was safe when the fixture held no
 * uncommitted work; it is not safe now. The demo workstream carries real
 * uncommitted state — the drafter's accepted findings, the `source_pdf` fields,
 * the `concepts/` → `metadata/` rename — and a `git checkout` silently destroys
 * all of it. It did, once, during this feature's development. Undo only what
 * this spec created.
 */

const WS = "open-finance-pd-2026";
const TASK = "open-finance-pd-2026-pd";
const TASK_URL = `/workstreams/${WS}/tasks/${TASK}`;

const GUARDRAILS_FILE = path.resolve(
  process.cwd(),
  "..",
  `data/workstreams/${WS}/guardrails.json`,
);

// Bookmarking writes into the committed recommendations set, so it is snapshotted
// and restored byte-for-byte — the demo ships with none bookmarked and must stay
// that way.
const RECS_FILE = path.resolve(
  process.cwd(),
  "..",
  `data/workstreams/${WS}/recommendations/${TASK}.json`,
);

let recsSnapshot: Buffer;

test.beforeEach(() => {
  recsSnapshot = readFileSync(RECS_FILE);
});

// Surgical cleanup: remove the one file the guardrails test creates, so the
// specs pass in any order without touching anything else in the workstream.
// Absent is the shipped state — an absent file is what makes the engine serve
// the five default guardrails.
test.afterEach(() => {
  rmSync(GUARDRAILS_FILE, { force: true });
  writeFileSync(RECS_FILE, recsSnapshot);
});

async function openTask(page: Page) {
  await page.goto(TASK_URL);
  await expect(page.getByTestId("recommendations-card")).toBeVisible();
}

function cards(page: Page) {
  return page.getByTestId("recommendation");
}

test("the Recommendations card replaces the Source card", async ({ page }) => {
  await openTask(page);

  await expect(page.getByTestId("source-card")).toHaveCount(0);
  // Nothing the Source card uniquely showed is lost: the page header still
  // carries the owner byline. Scoped to the header holding the task's own
  // heading — the app shell renders a header too, so a bare `header` locator is
  // ambiguous and strict mode rejects it.
  const pageHeader = page.locator("header").filter({
    has: page.getByRole("heading", { level: 1 }),
  });
  await expect(pageHeader).toContainText("Aisyah R.");
  // And the left column still holds the neighbour list beneath the new card.
  // Matched on the card's own heading text — a bare "Neighbour nodes" also hits
  // the header byline's "1 neighbour nodes".
  await expect(page.getByTestId("recommendations-card")).toBeVisible();
  await expect(page.getByTestId("neighbour-row").first()).toBeVisible();
});

test("the committed recommendations are shown with their dimensions", async ({
  page,
}) => {
  await openTask(page);

  await expect(cards(page).first()).toBeVisible();
  expect(await cards(page).count()).toBeGreaterThan(0);

  // Every card is tagged with at least one of the drafter's own policy
  // requirements — the axes she recorded, not categories the tool invented.
  const first = cards(page).first();
  await expect(first.getByTestId("rec-dimension").first()).toBeVisible();
  await expect(first).toContainText(/Action for BNM/i);

  // A generated set means Regenerate, not Generate.
  await expect(page.getByTestId("generate")).toHaveText(/Regenerate/);
  await expect(page.getByTestId("generate")).toBeEnabled();
});

test("a recommendation quotes the clause it rests on, with its number", async ({
  page,
}) => {
  await openTask(page);
  const first = cards(page).first();

  await first.getByTestId("citations-toggle").click();

  const citation = first.getByTestId("citation").first();
  await expect(citation).toBeVisible();
  // A clause number and a real quotation, not a paraphrase — the product's
  // verbatim-citation rule, visible on screen.
  await expect(citation).toHaveAttribute("data-finding-id", /.+/);
  const quoted = await citation.innerText();
  expect(quoted.length).toBeGreaterThan(60);
});

test("the tool states what it could not verify, on hover and on focus", async ({
  page,
}) => {
  await openTask(page);
  await expect(cards(page).first()).toBeVisible();

  // Not necessarily the first card: a recommendation with nothing to disclose
  // reports "Nothing unverified." and deliberately carries no marker, so the
  // test finds one that has a caveat rather than assuming every card does.
  const marker = page
    .getByRole("button", { name: /could not verify/i })
    .first();
  await expect(marker).toBeVisible();

  await marker.hover();
  await expect(page.getByTestId("info-bubble")).toBeVisible();

  // Keyboard reachable too: a pointer-only disclosure would put the honesty
  // caveat out of reach.
  await page.keyboard.press("Escape");
  await marker.focus();
  await expect(page.getByTestId("info-bubble")).toBeVisible();
});

test("accepted findings no recommendation drew on are reported", async ({
  page,
}) => {
  await openTask(page);

  const section = page.getByTestId("not-yet-reflected");
  await expect(section).toBeVisible();

  const count = Number(await section.getAttribute("data-count"));
  expect(count).toBeGreaterThanOrEqual(0);

  if (count > 0) {
    // Collapsed by default, so it reports without competing with the
    // recommendations themselves.
    await expect(page.getByTestId("unreflected-finding")).toHaveCount(0);
    await page.getByTestId("not-yet-reflected-toggle").click();
    await expect(page.getByTestId("unreflected-finding").first()).toBeVisible();

    // Read-only: it links through to the review screen and offers nothing else.
    const row = page.getByTestId("unreflected-finding").first();
    await expect(row.getByRole("link", { name: /Open/i })).toBeVisible();
  } else {
    await expect(section).toContainText(/Every accepted finding is reflected/i);
  }
});

test("the guardrails ship populated and can be edited and saved", async ({
  page,
}) => {
  await openTask(page);

  const badge = page.getByTestId("guardrails-badge");
  await expect(badge).toHaveAttribute("aria-expanded", "false");

  await badge.click();

  const box = page.getByTestId("guardrails-body");
  await expect(box).toBeVisible();
  // Populated on day one from the five defaults, so the box is worth reading
  // before it is worth changing. The house-convention rule is the one a BNM
  // reviewer scored 1/5 against.
  await expect(box).toHaveValue(/provision number/);
  await expect(page.getByText(/Showing the shipped defaults/i)).toBeVisible();

  // Save is inert until something actually changes.
  await expect(page.getByTestId("guardrails-save")).toBeDisabled();

  await box.fill(
    "HKMA's TSP means our data consumer, not our TPSP — do not assert a gap on the shared acronym.",
  );
  await expect(page.getByTestId("guardrails-save")).toBeEnabled();
  await page.getByTestId("guardrails-save").click();

  await expect(page.getByText(/Showing the shipped defaults/i)).toHaveCount(0);

  // Persisted, not just held in component state.
  await page.reload();
  await page.getByTestId("guardrails-badge").click();
  await expect(page.getByTestId("guardrails-body")).toHaveValue(
    /shared acronym/,
  );
});

test("emptying the guardrails says what that means", async ({ page }) => {
  await openTask(page);
  await page.getByTestId("guardrails-badge").click();
  const box = page.getByTestId("guardrails-body");
  await expect(box).toBeVisible();

  await box.fill("");

  // Clearing the box is a deliberate act, so it is reported rather than quietly
  // overruled by reinstating the defaults.
  await expect(page.getByTestId("guardrails-empty-warning")).toContainText(
    /generated with no guardrails/i,
  );
});

test("a published document has no Recommendations card", async ({ page }) => {
  // Only a working draft has something to change, so the card is a task-screen
  // surface and a context document must not offer one.
  await page.goto(`/workstreams/${WS}/tasks/ed-open-finance-2025`);

  await expect(page.getByTestId("recommendations-card")).toHaveCount(0);
  await expect(page.getByText(/not a task/i)).toBeVisible();
});

test("a recommendation can be bookmarked, and the mark persists", async ({
  page,
}) => {
  await openTask(page);
  const first = cards(page).first();
  const recId = await first.getAttribute("data-rec-id");

  const toggle = first.getByTestId("bookmark-toggle");
  await expect(toggle).toHaveAttribute("aria-pressed", "false");

  await toggle.click();

  await expect(
    page.locator(`[data-rec-id="${recId}"] [data-testid="bookmark-toggle"]`),
  ).toHaveAttribute("aria-pressed", "true");

  // Persisted, not just held in component state — and bookmarked cards sort to
  // the top, which is what carries them into the drafting workspace later.
  await page.reload();
  await expect(cards(page).first()).toHaveAttribute("data-rec-id", recId!);
  await expect(cards(page).first().getByTestId("bookmark-toggle")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
});

test("the bookmark control is reachable and announced to a screen reader", async ({
  page,
}) => {
  await openTask(page);
  const toggle = cards(page).first().getByTestId("bookmark-toggle");

  // A real button with a name that says what the next press will do — the mark
  // is an icon, so there is no text for a screen reader to fall back on.
  await expect(toggle).toHaveAccessibleName("Bookmark this recommendation");
  await toggle.focus();
  await expect(toggle).toBeFocused();

  await page.keyboard.press("Enter");

  await expect(toggle).toHaveAccessibleName("Remove bookmark");
});
