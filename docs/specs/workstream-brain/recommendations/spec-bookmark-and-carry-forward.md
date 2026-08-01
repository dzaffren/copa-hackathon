# Bookmark Recommendations and Carry Them to My Draft

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Recommendations — Overview](spec.md)

Of seven recommendations, four are worth acting on. This story lets Aisyah mark those four, keeps them safe when she regenerates the rest, and puts them in front of her while she drafts — beside the Playbook that configures the Copilot and the Copilot that does the writing.

## User Story

As Aisyah R., I want to mark the recommendations worth acting on and find them beside my draft, so that the ones I chose survive the next regeneration and are in front of me when I write.

## Background & Context

**Current state:**

- Recommendations are generated on the task screen from Aisyah's accepted findings, and regenerating replaces the whole set. Beneath them, a collapsed section reports which accepted findings no recommendation drew on. _(Story: Recommendations from my accepted findings)_
- Triage is continuous: Aisyah accepts more findings over days, so the evidence base keeps growing and she will generate more than once.
- The drafting workspace shows two tabs beside the editor — **Reviewed** (accepted linkages, read-only) and **Copilot** (where drafting happens). The Reviewed tab duplicates what the task screen already shows and is being replaced. _(Story: A Playbook that configures the Copilot)_
- The Copilot is where every word that reaches the draft is written and reviewed. Nothing else writes to the page.

**Problem:**

- **Regenerating destroys judgement.** Aisyah reads seven recommendations and decides four are good. She accepts twelve more findings, regenerates, and her four decisions are gone — she must re-read and re-decide a set that mostly repeats what she already judged.
- **A new batch repeats what she already chose.** Even where a good recommendation survives in substance, it comes back reworded, and she cannot tell whether it is the one she already approved.
- **The decision does not travel.** Aisyah decides on the task screen and drafts in a different screen. Her selection stays behind, so she reconstructs it from memory while writing.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, moving between the task screen and the drafting workspace.
- **Context:** She has generated recommendations, is choosing which to act on, and will regenerate at least once more before the draft is finished.
- **Current workaround:** She notes the good ones somewhere outside the tool, or she avoids regenerating so as not to lose them — which means drafting from a stale set.

## Goals

- Let Aisyah mark a recommendation as one she is taking forward.
- Keep every marked recommendation exactly as it was when she regenerates.
- Stop a new batch restating something she has already marked.
- Show her marked set beside the draft, in the first tab, where she reads it as she writes.
- Keep sight of what no recommendation drew on, on the same terms as the task screen.

## Non-Goals

- **Any route from a recommendation into the draft.** No insert action, no hand-off to the Copilot. Everything that reaches the page arrives through the Copilot conversation, where Aisyah reviews it. A recommendation beside the draft is something she reads and then asks the Copilot for in her own words.
- **Ordering or grouping the marked set by hand.** Marked recommendations sit above the rest; there is no manual arrangement.
- **Marking recommendations across workstreams or drafts.** A recommendation belongs to one working draft.
- **Dismissing a recommendation.** Not marking it is how Aisyah passes on one; the next regeneration clears it.
- **Replacing the Reviewed tab.** That is the Playbook story's job; this story assumes the resulting tab order.

## User Workflow

1. **She marks four.** Reading seven recommendations, she bookmarks the four worth acting on. Each moves to the top of the card as she marks it.
2. **She unmarks one.** On reflection the fourth is premature. She unmarks it; it rejoins the rest.
3. **She accepts more findings and regenerates.** Twelve more accepted findings later, she generates again. Her three marked recommendations are exactly as they were. The rest of the card is new.
4. **She checks for repeats.** None of the new recommendations restates one of her three in different words.
5. **She opens the draft.** The first tab is **Recommendations**, showing three. Below them, the same not-yet-reflected count she saw on the task screen.
6. **She writes.** She reads her first bookmarked recommendation, expands its clauses, and then asks the Copilot for clause language in her own words. Nothing reached the page except through that conversation.

## Acceptance Criteria

### Scenario: Marking a recommendation to take forward

```gherkin
Given I am reading seven generated recommendations
When I bookmark the one about publishing a data consumer list
Then it is shown as bookmarked
  And it moves above the recommendations I have not bookmarked
```

### Scenario: Unmarking a recommendation

```gherkin
Given I have bookmarked the recommendation about phased implementation milestones
When I remove the bookmark
Then it is no longer shown as bookmarked
  And it rejoins the recommendations I have not bookmarked
```

### Scenario: Bookmarks survive regeneration

```gherkin
Given I have bookmarked three of seven recommendations
  And I have since accepted twelve more findings
When I generate recommendations again
Then my three bookmarked recommendations are unchanged
  And the four I did not bookmark have been replaced
```

### Scenario: A new batch does not restate what I bookmarked

```gherkin
Given I have bookmarked the recommendation about publishing a data consumer list
When I generate recommendations again
Then none of the new recommendations restates that recommendation in different words
```

### Scenario: Evidence behind a bookmark stays available to the new batch

```gherkin
Given I have bookmarked a recommendation resting on three accepted findings
  And one of those findings also bears on API security
When I generate recommendations again
Then that finding can still support a new recommendation about API security
```

### Scenario: Bookmarks survive leaving and returning

```gherkin
Given I bookmarked three recommendations this morning
When I close the task screen and open it again this afternoon
Then the same three are still bookmarked
```

### Scenario: Bookmarked recommendations appear beside the draft

```gherkin
Given I have bookmarked three recommendations on the task screen
When I open the working draft
Then the first tab is Recommendations
  And it shows my three bookmarked recommendations
  And it shows that there are three
```

### Scenario: Only bookmarked recommendations reach the draft

```gherkin
Given I have generated seven recommendations and bookmarked three
When I open the Recommendations tab beside my draft
Then I see only the three I bookmarked
  And the four I did not bookmark are not shown
```

### Scenario: Evidence is readable beside the draft

```gherkin
Given I am reading a bookmarked recommendation beside my draft
When I expand its citations
Then I see each accepted finding it rests on
  And I see the clause number and clause text for each
```

### Scenario: What no recommendation drew on is visible beside the draft too

```gherkin
Given 7 of my 30 accepted findings were not drawn on by any generated recommendation
When I open the Recommendations tab beside my draft
Then I am told that 7 accepted findings are not yet reflected
  And the number matches what the task screen reports
```

### Scenario: Nothing here writes to my draft

```gherkin
Given I am reading a bookmarked recommendation beside my draft
When I look at what I can do with it
Then I can read it, expand its citations, and remove its bookmark
  And there is no way to place its text into my draft
  And there is no way to hand it to the Copilot on my behalf
```

### Scenario: Unmarking from beside the draft

```gherkin
Given the Recommendations tab beside my draft shows three bookmarked recommendations
When I remove the bookmark from one of them
Then the tab shows two
  And that recommendation is no longer bookmarked on the task screen
```

### Scenario: Nothing bookmarked yet

```gherkin
Given I have generated recommendations but bookmarked none of them
When I open the Recommendations tab beside my draft
Then I am told that bookmarking a recommendation on the task screen brings it here
  And the Playbook and Copilot tabs are unaffected
```

### Scenario: No recommendations generated at all

```gherkin
Given I have never generated recommendations for this working draft
When I open the Recommendations tab beside my draft
Then I am told how to generate them
  And I can still use the Playbook and Copilot tabs
```

## Business Rules & Constraints

- **A regeneration keeps every bookmarked recommendation exactly as it was** — wording, reasoning, evidence and citations all unchanged — and replaces everything else.
- **Bookmarked recommendations are shown to the tool as already taken forward**, so a new batch does not restate them. This is the only reason they enter the next generation at all.
- **The accepted findings behind a bookmarked recommendation stay available as evidence.** A finding that legitimately bears on two dimensions must be able to support a new recommendation about the second.
- **Bookmarked recommendations sit above the rest.** There is no manual ordering.
- **The draft's Recommendations tab shows bookmarked recommendations only**, and is the first of three: Recommendations, Playbook, Copilot.
- **Coverage is reported identically on both surfaces** — against every generated recommendation, not only the bookmarked ones — so the number means the same thing wherever Aisyah reads it.
- **Bookmarking is one state, held in one place.** Marking or unmarking anywhere is reflected everywhere.
- **Nothing on this surface writes to the draft.** There is no insert action and no hand-off. The Copilot conversation is the only route to the page.

## Success Metrics

- **Regenerating is safe.** Aisyah regenerates without losing a decision, which is what makes generating more than once worth doing.
- **Her selection is in front of her while she writes.** She drafts from her bookmarked set without recalling anything from memory, and without any text reaching the page except through the Copilot.

## Dependencies

- **Recommendations from my accepted findings** must exist first — there is nothing to bookmark otherwise.
- **A Playbook that configures the Copilot** owns the tab replacement. This story assumes the resulting three-tab order but does not itself remove the Reviewed tab.

## Open Questions

- [x] ~~Should a new batch be prevented from reusing the evidence behind a bookmarked recommendation?~~ — **Resolved: no.** Excluding it would silently drop a finding that legitimately bears on a second dimension. Preventing repetition is handled by showing the tool what has already been taken forward, not by withholding evidence.
- [x] ~~Should the drafting workspace show all recommendations, or only bookmarked ones?~~ — **Resolved: bookmarked only.** The tab exists because Aisyah decided; showing the ones she passed over would reopen a decision she has made.
- [x] ~~Should a recommendation be handed to the Copilot directly, with its evidence attached?~~ — **Resolved: no.** Everything that reaches the draft arrives through the Copilot conversation in Aisyah's own words. A hand-off would be a second route to the page with weaker review, and the Copilot already reads the Playbook's per-stage configuration, so her standing context is there without it.
- [ ] **Should a bookmarked recommendation be markable as done once drafted?** — **Deferred (non-blocking).** Aisyah can unbookmark it, which is close enough for now. A distinct "acted on" state is a fourth status to design and nothing depends on it.

---

## Functional Requirements

- **Bookmarking is a single-field write**, not a regeneration: `PATCH` sets `bookmarked` on one recommendation and persists the file. No model call.
- **Idempotent:** `PATCH {"bookmarked": true}` twice leaves the same state and returns `200` both times. There is no "already bookmarked" error — the drafter's intent is the same either way.
- **Atomicity:** the whole recommendations file is rewritten in one `write_text`, as `findings.save` does. A failed write leaves the previous bytes.
- **Ordering is a view concern, computed in the browser.** The engine returns recommendations in stored order; `RecommendationsCard` sorts bookmarked-first. The same division `PairwiseFindingsCard` already uses for sinking judged findings, and it is why an optimistic bookmark reorders without a refetch.
- **The draft tab is a filter, not a route.** It reads the same `["recommendations", ws, node]` query the task screen populates and filters to `bookmarked === true`. No second endpoint, so the two surfaces cannot disagree.
- **Coverage on the draft tab is the server's figure, unmodified** — computed against every generated recommendation, so it does not change when a bookmark is toggled.

### Validation & Business Rules

| Rule | Enforcement |
| ---- | ----------- |
| `rec_id` must exist in the task's recommendations file | `404 RECOMMENDATION_NOT_FOUND` |
| Recommendations file must exist | `404 RECOMMENDATIONS_NOT_GENERATED` |
| `bookmarked` must be a boolean when present | `400 INVALID_PATCH` |
| Body must contain at least one of `bookmarked` / `comment` | `400 INVALID_PATCH` |

## Permissions & Security

- **Scope:** internal-only, same trust boundary as the rest of `/api/workstreams/*`.
- **`rec_id` is resolved against the loaded file before any write**, never interpolated into a path — the file is keyed by `node_id`, and `rec_id` only ever indexes a list in memory. So this parameter cannot reach the filesystem at all.
- **No new client-supplied text on this path.** `bookmarked` is a boolean; the `comment` branch belongs to Story 3.

## API Design

### `PATCH /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/{rec_id}`

Shared with Story 3, which adds the `comment` field. This story implements `bookmarked` only.

**Request:**

```json
{ "bookmarked": true }
```

**Response (200)** — the updated recommendation alone, not the whole set:

```json
{
  "id": "4f9f91c02ef5",
  "title": "Publish and maintain a list of authorised data consumers",
  "bookmarked": true,
  "dimensions": ["third party oversight"],
  "comments": [],
  "revisions": []
}
```

**Errors:**
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `WORKSTREAM_NOT_FOUND` | No such workstream |
| 404 | `NODE_NOT_FOUND` | `node_id` absent from the graph |
| 400 | `NOT_A_TASK` | Node is not a task |
| 404 | `RECOMMENDATIONS_NOT_GENERATED` | No recommendations file for this task — message: `"No recommendations have been generated for this task."` |
| 404 | `RECOMMENDATION_NOT_FOUND` | `rec_id` not in the file — message: `"No recommendation 4f9f91c02ef5 on this task."` |
| 400 | `INVALID_PATCH` | `bookmarked` present but not a boolean, or body has neither recognised field — message: `"bookmarked must be a boolean."` |

## Data Model & Migrations

No new files. `bookmarked` already exists on every recommendation, created as `false` by Story 1. No migration.

## UI/Frontend Requirements

### Components

**`RecommendationCard`** — `frontend/src/features/task/RecommendationCard.tsx` (modify, ~25 LOC)

- Wire the bookmark control to the mutation. `Bookmark` / `BookmarkCheck` from `lucide-react` (already a dependency).
- Control is a real `<button>` with `aria-pressed={rec.bookmarked}` and an accessible name that flips between "Bookmark this recommendation" and "Remove bookmark".

**`RecommendationsCard`** — `frontend/src/features/task/RecommendationsCard.tsx` (modify, ~55 LOC)

- Add the bookmark mutation with the optimistic pattern from `PairwiseFindingsCard.tsx:57-110`: `onMutate` cancels in-flight queries, snapshots, patches the cache; `onError` restores the snapshot and records a per-item message; `onSuccess` invalidates the draft view's key.
- Sort bookmarked-first for display.

**`RecommendationsTab`** — `frontend/src/features/drafting-workspace/RecommendationsTab.tsx` (new, ~130 LOC)

```typescript
interface Props {
  workstreamId: string;
  nodeId: string;
}
```

- Reads the shared query, filters to `bookmarked`, renders read-only cards with expandable citations, an unbookmark control, and the coverage figure.
- **No `Draft this` action, no insert action.** The Copilot conversation is the only route to the page.

**`DraftingWorkspacePage`** — `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx` (modify, ~30 LOC)

- `TabKey` becomes `"recommendations" | "playbook" | "copilot"`; the `tabs` array (line 156) is reordered accordingly, with `count` on the recommendations tab.
- The `reviewed` branch and `fetchReviewedLinkages` usage are removed by the Playbook story; this story adds the recommendations branch. **If built first**, leave `reviewed` in place as the second tab and let the Playbook story replace it — either merge order leaves a working three-or-four-tab panel rather than a broken one.

### User Interactions

| Action | Result |
| ------ | ------ |
| Press the bookmark control | Card marks and moves above the unbookmarked immediately (optimistic); reverts with a message if the write fails |
| Press it again | Unmarks and rejoins the rest |
| Unbookmark from the draft tab | Tab count decrements; the task screen reflects it on next read |
| Expand citations in the draft tab | Clause numbers and full clause text appear |

### States

- **Loading:** spinner with `role="status"`, "Loading recommendations…".
- **Nothing bookmarked:** *"Bookmark a recommendation on the task page and it appears here."*
- **Never generated:** *"No recommendations yet. Generate them on the task page."*
- **Error:** per-card inline message; the card keeps its pre-mutation state.

## Architecture Notes

- **New dependencies:** none.
- **One query, two consumers.** Both surfaces use `["recommendations", workstreamId, nodeId]`, so a bookmark toggled on either is reflected on the other without a bespoke sync path.
- **Cache invalidation:** the task screen's mutation invalidates its own key; because the draft tab shares it, the tab updates from the same write.
- **Tab order is data, not markup.** The `tabs` array drives rendering, so reordering is one edit — the pattern already in place at `DraftingWorkspacePage.tsx:156-159`.

## Exemplar Files

- `frontend/src/features/task/PairwiseFindingsCard.tsx:57-110` — the optimistic mutation with snapshot rollback and per-item error map. Copy this shape exactly.
- `frontend/src/features/drafting-workspace/LinkageRefCard.tsx` — the read-only reference card beside the draft, including its withdraw control; the closest model for `RecommendationsTab`'s cards.
- `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx:200-232` — the tablist and the `tabs` array.
- `engine/api.py:1890-1978` (`patch_finding_review_state`) — a single-field PATCH over a side-file, with its 404/400 ordering.

## Implementation Plan

### Sub-tasks

**Task 1: `PATCH` route with the `bookmarked` field** — _small_

- Files: `engine/recommendations.py` (modify — add `set_bookmarked`), `engine/api.py` (modify), `engine/tests/test_api_recommendations.py` (modify)
- INDEPENDENT

**Task 2: API client + type for the PATCH** — _small_

- Files: `frontend/src/lib/api.ts` (modify — `setRecommendationBookmark`), `frontend/src/test/msw/handlers.ts` (modify)
- SEQUENTIAL (depends on Task 1)

**Task 3: Optimistic bookmark on the task screen** — _medium_

- Files: `frontend/src/features/task/RecommendationsCard.tsx` (modify), `frontend/src/features/task/RecommendationCard.tsx` (modify), `frontend/src/features/task/RecommendationsCard.test.tsx` (modify)
- SEQUENTIAL (depends on Task 2)

**Task 4: `RecommendationsTab` + tab reorder** — _medium_

- Files: `frontend/src/features/drafting-workspace/RecommendationsTab.tsx` (new), `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx` (modify), `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx` (modify)
- SEQUENTIAL (depends on Task 2)

**Task 5: E2E** — _small_

- Files: `frontend/e2e/recommendations-bookmark.spec.ts` (new)
- SEQUENTIAL (depends on Tasks 3 and 4)

### Negative Constraints

- Do NOT add any action that writes to the draft — no insert, no Copilot hand-off, no "Draft this". This is the story's sharpest constraint and the reason the resolved question is recorded.
- Do NOT create a second endpoint for the draft tab. It filters the shared query.
- Do NOT change how coverage is computed. It stays measured against every generated recommendation.
- Do NOT remove the Reviewed tab in this story — that belongs to the Playbook story.
- Do NOT modify `engine/findings.py` or the review-state routes.

## Test Scenarios

**Test 1: Bookmark persists**

- Setup: a generated set of 3 in `tmp_path`, all `bookmarked: false`
- Action: `PATCH …/recommendations/4f9f91c02ef5` with `{"bookmarked": true}`
- Expected: `200`, response `bookmarked: true`; re-reading the file from disk shows `true` on that entry and `false` on the other two

**Test 2: Unbookmark persists**

- Setup: one entry `bookmarked: true`
- Action: `PATCH` with `{"bookmarked": false}`
- Expected: `200`; the file shows `false`

**Test 3: Idempotent**

- Action: `PATCH {"bookmarked": true}` twice on the same id
- Expected: `200` both times; identical state; no duplicate effect

**Test 4: Unknown recommendation id**

- Action: `PATCH …/recommendations/deadbeef0000` with `{"bookmarked": true}`
- Expected: `404 RECOMMENDATION_NOT_FOUND`, message `"No recommendation deadbeef0000 on this task."`; file unchanged

**Test 5: No recommendations generated yet**

- Setup: no recommendations file for the task
- Action: `PATCH …/recommendations/4f9f91c02ef5`
- Expected: `404 RECOMMENDATIONS_NOT_GENERATED`

**Test 6: Non-boolean `bookmarked` rejected**

- Action: `PATCH` with `{"bookmarked": "yes"}`
- Expected: `400 INVALID_PATCH`, message `"bookmarked must be a boolean."`; file unchanged

**Test 7: Empty patch body rejected**

- Action: `PATCH` with `{}`
- Expected: `400 INVALID_PATCH`; file unchanged

**Test 8: Bookmarked entry survives regeneration byte-for-byte**

- Setup: 3 generated; `PATCH` one to `bookmarked: true`; capture its full dict from disk
- Action: `POST …/generate` with a stub returning 2 different recommendations
- Expected: the captured dict is `==` the persisted entry, `id` included; total 3; the two unbookmarked originals are gone

**Test 9: Regeneration prompt names the pinned titles**

- Setup: two bookmarked recommendations with known titles
- Action: `POST …/generate` with a prompt-recording stub
- Expected: both titles appear in the prompt, with the "already taken forward — do not restate" instruction

**Test 10: A bookmarked recommendation's evidence stays available**

- Setup: bookmarked recommendation citing finding `X`; `X` also bears on another dimension
- Action: `POST …/generate` with an evidence-recording stub
- Expected: `X` is present in the evidence handed to the generator

**Test 11: Coverage is unaffected by bookmarking**

- Setup: 30 accepted findings, a set citing 23
- Action: `GET`; `PATCH` two recommendations to `bookmarked: true`; `GET` again
- Expected: `counts.not_yet_reflected == 7` both times; `counts.bookmarked` goes `0 → 2`

**Test 12: The draft tab filters client-side (component test)**

- Setup: MSW returns 5 recommendations, 2 bookmarked
- Action: render `DraftingWorkspacePage`, open the Recommendations tab
- Expected: 2 cards rendered; the count badge reads `2`; exactly one network call for recommendations

**Test 13: Tab order (component test)**

- Action: render `DraftingWorkspacePage`
- Expected: `getAllByRole("tab")` names are `["Recommendations", "Playbook", "Copilot"]` in that order

**Test 14: No draft-writing affordance (component test)**

- Action: render the Recommendations tab with 2 bookmarked recommendations
- Expected: no button matching `/draft this|insert|add to draft/i`; the editor's content is untouched after interacting with a card

**Test 15: Optimistic rollback (component test)**

- Setup: MSW returns `500` for the PATCH
- Action: click the bookmark control
- Expected: the card marks immediately, then reverts; an inline error appears; the card's state matches the server

## Acceptance Criteria

- [ ] `PATCH` persists `bookmarked` and is idempotent
- [ ] Bookmarked recommendations survive regeneration byte-for-byte, ids included
- [ ] Pinned titles reach the generation prompt as "do not restate"
- [ ] Their evidence remains available to the new batch
- [ ] Bookmarked recommendations sort above the rest on both surfaces
- [ ] The draft's tabs read Recommendations, Playbook, Copilot in that order
- [ ] The draft tab shows bookmarked recommendations only, from the shared query
- [ ] Coverage is identical on both surfaces and unaffected by bookmarking
- [ ] **No affordance anywhere writes to the draft**
- [ ] Optimistic bookmark reverts on failure with a visible message
- [ ] Engine suite passes with no model credentials

## Verification

Run the verifier skill. Locally `.venv/bin/python -m pytest engine/tests` and `cd frontend && npm run test`.

### Backend API Tests

| File | Covers |
| ---- | ------ |
| `engine/tests/test_api_recommendations.py` (modify) | Tests 1–11 — the PATCH route, validation, and bookmark survival across regeneration |

### Browser/UI Testing

1. Generate on `/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd`.
2. Bookmark two → they jump to the top; badges update.
3. Reload → still bookmarked.
4. Open the draft → the first tab is Recommendations with count `2`.
5. Confirm there is **no** button that writes to the draft.
6. Expand citations → clause text visible.
7. Unbookmark one → count drops to `1`; return to the task screen → reflected there.
8. Tab through a card with the keyboard → the bookmark control is reachable and announces its pressed state.

### E2E Tests

| Key Scenario | Test file | Assigned sub-task |
| ------------ | --------- | ----------------- |
| Marking a recommendation to take forward | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Unmarking a recommendation | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Bookmarks survive regeneration | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Bookmarks survive leaving and returning | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Bookmarked recommendations appear beside the draft | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Only bookmarked recommendations reach the draft | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Evidence is readable beside the draft | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Nothing here writes to my draft | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Unmarking from beside the draft | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |
| Nothing bookmarked yet | `frontend/e2e/recommendations-bookmark.spec.ts` | Task 5 |

Covered by component tests rather than E2E (no server round-trip needed): tab order, client-side filtering, optimistic rollback. Covered by Test Scenarios and not duplicated in the browser: pinned-title prompt assembly, evidence retention, coverage arithmetic.

**Locator strategies:** `data-testid="recommendation"` with `data-rec-id` and `data-bookmarked`, `data-testid="bookmark-toggle"`, `data-testid="count-recommendations"` (matching the existing `count-{tabKey}` convention at `DraftingWorkspacePage.tsx:219`), `data-testid="draft-surface"`. Tabs via `getByRole("tab", { name: … })`.

**Fixture discipline:** bookmarking writes to `data/workstreams/open-finance-pd-2026/recommendations/`, a tracked path. `git checkout -- data/workstreams/open-finance-pd-2026` in `beforeEach`, as `reviewed-tab.spec.ts:47-51` does.
