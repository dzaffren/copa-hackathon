# Comment on a Recommendation and Have It Rewritten

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Recommendations — Overview](spec.md)

Some recommendations miss for reasons no document can contain: a peer regulator's term means something different from ours, a platform operator already owns the implementation plan, two policy documents sit with different departments. This story lets Aisyah say so on the card, and have that one recommendation rewritten from her correction without disturbing the rest.

Where a correction is a rule rather than a one-off, she records it herself in the guardrails — deliberately, in her own words. Nothing is promoted there on her behalf.

## User Story

As Aisyah R., I want to tell the tool why a recommendation misses and have that one rewritten, so that I can correct a card without discarding a whole set I am otherwise happy with.

## Background & Context

**Current state:**

- Recommendations are generated from Aisyah's accepted findings and are read-only. Regenerating replaces everything she has not bookmarked. _(Stories: Recommendations from my accepted findings; Bookmark recommendations…)_
- Each recommendation states what it could not verify from the available documents, which is how the tool signals it may be missing context.
- There is nowhere in the tool to answer that signal.
- Elsewhere the drafting editor already lets Aisyah comment on a passage of text, so commenting is a familiar action in this product.

**Problem:**

- **A recommendation can be well-reasoned and still wrong.** In the reviewer's assessment behind this epic, two recommendations scored 3 and 4 and were both partly wrong — one because the platform operator was already running the detailed implementation plan, the other because the two documents involved are owned by different departments. Neither fact appears in any document the tool can read.
- **A recommendation can be wrong on a point the drafter can correct in one sentence.** The lowest-scoring recommendation of the nine asked BNM to map requirements to specific numbered provisions of another policy document — which BNM deliberately never does, because provision numbering shifts on reissue.
- **Rejecting a whole set to fix one card is the only option.** Aisyah's only lever today is to regenerate everything and hope — which also discards the recommendations she was happy with.
- **A judgement she has made has nowhere to go.** She reads a recommendation, works out precisely why it misses, and the tool offers her no way to say so at all.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, reading a generated set of recommendations.
- **Context:** She has found one that is close but wrong, and she knows exactly why — from institutional knowledge, not from any document in the workstream.
- **Current workaround:** She ignores the recommendation, and ignores it again next time.

## Goals

- Let Aisyah record why a recommendation misses, in her own words, on the recommendation itself.
- Let her have that one recommendation rewritten from her correction, without disturbing the rest.
- Make what she wrote available to the Copilot, so a correction she has already reasoned through is not lost to the drafting conversation.
- Keep a record of what a recommendation said before it was rewritten.
- Keep commenting and rewriting separate, so recording a note never costs a rewrite she did not ask for.
- Leave authorship of standing rules entirely with her.

## Non-Goals

- **A conversation.** A comment is a note, not a chat thread. Discussion of a draft belongs in the Copilot.
- **Rewriting the whole set from one comment.** A rewrite touches one recommendation. Her correction reaches the rest at the next full generation.
- **Editing a recommendation's text by hand.** Aisyah says what is wrong; the tool rewrites.
- **Comments on findings or clauses.** This story is about recommendations only.
- **Turning a comment into a standing rule automatically.** A comment stays a comment. Making a correction permanent for the recommendations engine means editing the guardrails, which is Aisyah's deliberate act — see _Business Rules_ for why.
- **Editing the guardrails.** They live behind their own badge on the Recommendations card, and this story neither writes to them nor builds them.

## User Workflow

1. **She finds one that misses.** A recommendation claims a gap on third party service providers.
2. **She says why.** She comments: _"HKMA's TSP is closer to our data consumer — our TPSP is an operational vendor. Different concepts."_ The comment is recorded on the card. Nothing is rewritten yet.
3. **She adds a second thought.** She adds a note about scope. Both comments sit on the card.
4. **She rewrites.** She presses Rewrite. That recommendation alone is rewritten from her two comments; every other recommendation is untouched.
5. **She checks what it used to say.** The card shows that it has been rewritten and what it said before.
6. **She leaves a note without rewriting.** On another recommendation she records a caveat for later and does not rewrite. It stays as it is.
7. **She decides one is a rule, not a one-off.** The terminology point will keep recurring. She opens the guardrails on the Recommendations card and records it there herself, in her own words. _(Story: Recommendations from my accepted findings, which owns that box)_
8. **She regenerates.** Days later she generates a fresh set. It does not repeat the terminology mistake, because she recorded it as a guardrail. Her other comments went with the cards they were written on, which is what she expected.

## Acceptance Criteria

### Scenario: Recording why a recommendation misses

```gherkin
Given I am reading the recommendation about a public service provider registry
When I comment "HKMA's TSP is closer to our data consumer — ours is an operational vendor"
Then the comment is shown on that recommendation with my name and the date
  And the recommendation itself is unchanged
```

### Scenario: Commenting does not rewrite

```gherkin
Given I am reading a recommendation about phased implementation milestones
When I comment "PayNet already runs the detailed plan with the pilot banks"
Then the recommendation still says exactly what it said before
  And I am not told anything is being regenerated
```

### Scenario: Rewriting one recommendation from my comment

```gherkin
Given I have commented "HKMA's TSP is closer to our data consumer — ours is an operational vendor"
When I rewrite that recommendation
Then it is rewritten taking my comment into account
  And it keeps its place among the recommendations
  And no other recommendation has changed
```

### Scenario: Several comments all inform one rewrite

```gherkin
Given I have left two comments on the recommendation about a public service provider registry
When I rewrite it
Then both comments are taken into account
```

### Scenario: A rewritten recommendation keeps what it said before

```gherkin
Given I have rewritten the recommendation about a public service provider registry
When I look at it
Then I can see that it has been rewritten
  And I can see what it said before
```

### Scenario: A rewritten recommendation keeps its bookmark

```gherkin
Given I have bookmarked the recommendation about phased implementation milestones
When I comment on it and rewrite it
Then it is still bookmarked
  And it is still shown beside my draft
```

### Scenario: A rewritten recommendation still quotes its evidence

```gherkin
Given I have rewritten a recommendation
When I expand its citations
Then it still rests on accepted findings
  And each shows its clause number and clause text word-for-word
```

### Scenario: My correction guides the next full generation

```gherkin
Given I commented that a peer regulator's third party term means something different from ours
  And I have recorded that in the guardrails
When I generate recommendations again
Then no recommendation in the new set treats those two terms as equivalent
```

### Scenario: A comment on its own does not become a standing rule

```gherkin
Given I commented on a recommendation that I did not bookmark
  And I did not record anything in the guardrails
When I generate recommendations again
Then the comment no longer appears, because its recommendation was replaced
  And the tool is not bound by what I said in it
```

### Scenario: The Copilot can still use what I said

```gherkin
Given I commented on a recommendation about third party terminology
When I ask the Copilot to draft a clause on that subject
Then it can draw on what I said in that comment
```

### Scenario: An empty comment is not recorded

```gherkin
Given I am commenting on a recommendation
When I submit without writing anything
Then no comment is recorded
  And I am still able to write one
```

### Scenario: Rewriting without a comment

```gherkin
Given I am reading a recommendation I have not commented on
When I rewrite it
Then it is rewritten from the evidence and the guardrails as they stand
  And I am not required to comment first
```

### Scenario: Nothing I write is promoted without me

```gherkin
Given I comment "HKMA's TSP is closer to our data consumer — ours is an operational vendor"
When I open the guardrails
Then my comment has not been added to them
  And I can record it there myself if I want it to be a standing rule
```

### Scenario: A rewrite that fails loses nothing

```gherkin
Given I have commented on a recommendation and asked for it to be rewritten
When the rewrite cannot be completed
Then I am told it could not be completed and can try again
  And the recommendation is unchanged
  And my comment is still recorded
```

### Scenario: Comments survive leaving and returning

```gherkin
Given I commented on two recommendations this morning
When I close the task screen and open it again this afternoon
Then both comments are still shown on their recommendations
```

## Business Rules & Constraints

- **Commenting and rewriting are separate actions.** A comment never triggers a rewrite. Aisyah may comment repeatedly and rewrite once, or comment and never rewrite.
- **A rewrite touches exactly one recommendation.** Every other recommendation in the set is untouched.
- **A rewritten recommendation keeps its identity** — its place in the set, its bookmark, and the dimensions it addresses.
- **A rewrite keeps what the recommendation said before**, so the change is visible rather than silent.
- **A rewritten recommendation is still bound by the evidence floor and the guardrails.** A correction changes what is written, never whether it must be supported by quoted clauses.
- **A comment stays on its recommendation.** It informs that card's rewrite and is available to the Copilot as context. It is not promoted, re-worded, or copied into the guardrails.
- **Nothing writes to the guardrails except Aisyah.** Making a correction permanent is her deliberate edit. The alternative — the tool re-interpreting a comment into a standing rule — would have a model authoring the rules it then follows, and an over-broad rule would silently suppress good recommendations until someone thought to read the box. A rule that governs every future generation is worth one deliberate action.
- **A comment does not survive its recommendation.** When a regeneration replaces an unbookmarked card, its comments go with it. What persists is what Aisyah put in the guardrails.
- **An empty comment is not recorded.**

## Success Metrics

- **Fixing one recommendation costs one recommendation.** She never has to discard a good set to correct a bad card.
- **A correction is never silently discarded without her seeing it.** A comment visibly belongs to its card, and the guardrails box is the visible, deliberate place a lasting rule goes — so nothing about what steers the engine is hidden from her.

## Dependencies

- **Recommendations from my accepted findings** must exist first — there is nothing to comment on otherwise. That story also owns the guardrails box a correction is recorded in.
- **A model call per rewrite**, on the same terms as generation: the running tool reaches a model, the demo runs from committed output, and the test suite injects a stub.

## Open Questions

- [x] ~~Should submitting a comment rewrite the recommendation immediately?~~ — **Resolved: no.** It would spend a model call on every stray note and rewrite a card out from under a drafter who meant to record a caveat.
- [x] ~~Should a comment be re-interpreted into a standing guardrail automatically?~~ — **Resolved: no.** It would mean a model writing the rules it then follows, and the specific failure mode is over-generalisation: "HKMA's TSP is not our TPSP" becoming "do not compare terminology against HKMA", which would suppress good recommendations invisibly. Aisyah keeps authorship of every rule that governs generation.
- [x] ~~Should Aisyah be able to edit a recommendation's text directly?~~ — **Resolved: no.** She states what is wrong and the tool rewrites, which keeps every recommendation traceable to evidence and guardrails. Hand-edited text would be neither.
- [x] ~~Where does a comment go once its recommendation is replaced?~~ — **Resolved: nowhere — it goes with the card.** The durable home for a lasting correction is the guardrails box, which she maintains herself.
- [ ] **Should the tool prompt her to record a comment as a guardrail?** — **Deferred (non-blocking).** A prompt after commenting — "make this a standing rule?", opening the guardrails with her own words, unedited — would close the gap between noticing and recording without a model re-wording anything. Worth revisiting if corrections are observed recurring in practice.

---

## Functional Requirements

- **Commenting is a filesystem write with no model call.** `PATCH` with a `comment` appends `{author, at, text}` to that recommendation's `comments` and persists. Nothing else changes.
- **Rewriting is a scoped model call.** `POST …/rewrite` regenerates one recommendation from: its current text, its `comments`, its existing `evidence` pool, and the workstream's guardrails. It does **not** re-run dimension parsing or re-collect neighbourhood evidence — the card's evidence pool is what it is rewritten against.
- **Identity is preserved across a rewrite:** `id`, `bookmarked`, `dimensions` and `comments` all carry over. Only `title`, `rationale`, `action`, `confidence_note` and `evidence` may change.
- **`revisions` is append-only.** Before overwriting, the pre-rewrite `{title, rationale, action, confidence_note, evidence, at}` is appended. The same append-only discipline `engine/linkage_review.py`'s `audit` uses — a rewrite is auditable, not silent.
- **The evidence floor applies to a rewrite too.** If the rewritten version resolves to zero valid citations, the rewrite is **rejected** (`502`) and the original is kept. A rewrite may never launder a recommendation past the evidence rule.
- **Comments are card-scoped and mortal.** They live on the recommendation, and a regeneration that replaces an unbookmarked card discards them with it. Nothing promotes them into the guardrails.
- **Not idempotent** (a model call). Two rewrites produce two versions and two `revisions` entries.
- **A failed rewrite is a no-op:** the file is written only after a successful, floor-passing parse.

### Validation & Business Rules

| Rule | Enforcement |
| ---- | ----------- |
| `comment` must be a string | `400 INVALID_PATCH` |
| `comment` must be non-empty after `.strip()` | `400 EMPTY_COMMENT` |
| `comment` ≤ 4 000 characters | `413 COMMENT_TOO_LARGE` |
| `rec_id` must exist in the file | `404 RECOMMENDATION_NOT_FOUND` |
| Rewritten version must resolve ≥1 citation | `502 REWRITE_FAILED`, original kept |

**Comment author** is the task's owner from the graph node, matching how `LinkageRefCard` and the editor's comment popover attribute — there is no auth, and inventing an author field the client supplies would let it claim any name.

## Permissions & Security

- **Scope:** internal-only, same boundary as the rest of `/api/workstreams/*`.
- **A comment is untrusted text that reaches a prompt.** Bounded at 4 000 characters and inserted into the rewrite prompt as a delimited block. The threat model is a drafter's own paste accident, not third-party injection — this is her own workstream.
- **Comments render as plain text.** No `dangerouslySetInnerHTML` on this path; the drafting editor's HTML sanitisation (`engine/drafts.py`) is a separate concern and untouched.
- **`rec_id` never reaches the filesystem** — it indexes a list in memory; the file is keyed by `node_id`, which is resolved against the graph first.

## API Design

### `PATCH /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/{rec_id}`

Shared with Story 2, which owns the `bookmarked` field. This story adds `comment`. Both may appear in one request.

**Request:**

```json
{ "comment": "HKMA's TSP is closer to our data consumer — our TPSP is an operational vendor. Different concepts." }
```

**Response (200):**

```json
{
  "id": "4f9f91c02ef5",
  "title": "Publish and maintain a list of authorised data consumers",
  "bookmarked": true,
  "comments": [
    {
      "author": { "id": "aisyah-r", "name": "Aisyah R." },
      "at": "2026-08-02T11:12:40Z",
      "text": "HKMA's TSP is closer to our data consumer — our TPSP is an operational vendor. Different concepts."
    }
  ],
  "revisions": []
}
```

**Errors:**
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `RECOMMENDATIONS_NOT_GENERATED` | No recommendations file for this task |
| 404 | `RECOMMENDATION_NOT_FOUND` | `rec_id` not in the file |
| 400 | `INVALID_PATCH` | `comment` present but not a string — message: `"comment must be a string."` |
| 400 | `EMPTY_COMMENT` | Whitespace-only — message: `"A comment cannot be empty."` |
| 413 | `COMMENT_TOO_LARGE` | Over 4 000 characters — message: `"A comment holds at most 4000 characters."` |

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/{rec_id}/rewrite`

**Request:** empty body.

**Response (200)** — the rewritten recommendation:

```json
{
  "id": "4f9f91c02ef5",
  "title": "Clarify the distinction between data consumers and outsourced service providers",
  "rationale": "The HKMA framework's publication duty attaches to entities that access banking data to provide services — the role our framework calls a data consumer. Our third party service provider provisions govern operational vendors, so the two are not comparable.",
  "action": "Add interpretive guidance distinguishing data consumers from third party service providers, and state which oversight duties attach to each.",
  "dimensions": ["third party oversight"],
  "evidence": [
    {
      "finding_id": "4f9f91c02ef5~0",
      "edge_id": "e-hkma_open_api_framework--ed_open_finance_2025",
      "label": "silent-on",
      "source_clause_number": "4.2",
      "source_clause_text": "An AI should publish on its website a list of all TSPs…",
      "target_clause_number": "10.4",
      "target_clause_text": "A data provider shall establish oversight arrangements…"
    }
  ],
  "confidence_note": "The equivalence between the two frameworks' third-party terminology could not be established from the documents in this workstream.",
  "bookmarked": true,
  "comments": [{ "author": { "id": "aisyah-r", "name": "Aisyah R." }, "at": "2026-08-02T11:12:40Z", "text": "HKMA's TSP is closer to our data consumer…" }],
  "revisions": [
    {
      "at": "2026-08-02T11:15:02Z",
      "title": "Publish and maintain a list of authorised data consumers",
      "rationale": "HKMA's framework requires banks to publish partnering providers…",
      "action": "Add a requirement for data providers to maintain and publish an up-to-date list…",
      "confidence_note": "Assumes no separate industry register already performs this function…"
    }
  ]
}
```

**Errors:**
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `RECOMMENDATIONS_NOT_GENERATED` | No recommendations file |
| 404 | `RECOMMENDATION_NOT_FOUND` | `rec_id` not in the file |
| 502 | `REWRITE_FAILED` | Model raised, response unparseable, or the rewrite resolved zero citations. Original kept — message: `"The rewrite could not be completed. The recommendation is unchanged."` |

## Data Model & Migrations

No new files. `comments` and `revisions` already exist as `[]` on every recommendation, created by Story 1.

**Comment:** `{author: {id, name}, at: ISO-8601 Z, text: string}`
**Revision:** `{at: ISO-8601 Z, title, rationale, action, confidence_note}` — the superseded content. `evidence` is deliberately **not** snapshotted: it is a projection of accepted findings that still exist and are still quotable, so storing a copy per revision would bloat the file for no gain in auditability.

No migration.

## UI/Frontend Requirements

### Components

**`RecommendationComments`** — `frontend/src/features/task/RecommendationComments.tsx` (new, ~120 LOC)

```typescript
interface Props {
  rec: Recommendation;
  onComment: (text: string) => void;
  isCommentPending: boolean;
  commentError?: string;
}
```

- Existing comments listed with author initials and date; a collapsed compose box opened by `Comment`. `Submit` disabled while the trimmed value is empty.
- Follows the compose/cancel/submit shape of `EditorPane.tsx:180-240`, without the on-page anchoring — these attach to a card, not a text range.

**`RecommendationRevisions`** — `frontend/src/features/task/RecommendationRevisions.tsx` (new, ~70 LOC)

- Shown only when `revisions.length > 0`: a "Rewritten" marker and a disclosure listing each previous version's title, rationale and action.

**`RecommendationCard`** — `frontend/src/features/task/RecommendationCard.tsx` (modify, ~45 LOC)

- Add the `Comment` and `Rewrite` actions, the comment thread, and the revisions disclosure. `Rewrite` shows a per-card spinner and disables only that card's actions — every other card stays interactive.

**`RecommendationsCard`** — `frontend/src/features/task/RecommendationsCard.tsx` (modify, ~50 LOC)

- Two more mutations. **Neither is optimistic:** a comment's stored form includes a server timestamp and resolved author, and a rewrite's content is unknown until it returns. Guessing either would show text the server did not write. Bookmarking stays optimistic because its outcome is fully known client-side.

### User Interactions

| Action | Result |
| ------ | ------ |
| Press `Comment` | Compose box opens on that card |
| Submit a comment | Appended to the thread with author and date; **nothing is rewritten** |
| Submit an empty comment | `Submit` stays disabled; no request made |
| Press `Rewrite` | That card shows a spinner; on success it is replaced in place, keeping its bookmark and position; a "Rewritten" marker appears |
| Expand the revisions disclosure | Previous versions listed |

### States

- **Comment pending:** spinner beside `Submit`; the box stays open with the text preserved.
- **Comment error:** inline message; text preserved so nothing is retyped.
- **Rewrite pending:** per-card spinner; the card's other actions disabled; the rest of the list interactive.
- **Rewrite error:** inline *"The rewrite could not be completed. Try again."*; the card unchanged; any comment still listed.
- **No comments:** the thread is absent; only the `Comment` action shows.

## Architecture Notes

- **New dependencies:** none.
- **The rewrite reuses the generation seam.** `generate_recommendations_fn` is called in a single-recommendation mode rather than a second injected function — one seam, so a test stubs one thing and both paths are covered.
- **Guardrails are read on rewrite as well as generation**, so a rule Aisyah records applies to a rewrite immediately, without regenerating the set.
- **`revisions` follows `linkage_review.py`'s `audit` discipline** — append, never mutate, so history cannot be rewritten by the thing that writes history.

## Exemplar Files

- `engine/linkage_review.py:131-197` (`apply_action`) — append-only audit and comment lists on a side-file record. The model for `revisions` and `comments`.
- `engine/api.py:1890-1978` (`patch_finding_review_state`) — single-field PATCH over a side-file with 404/400 ordering.
- `engine/api.py:1715-1831` (the `analyze` route) — calling an injected model seam from a route and mapping failure to a `502`.
- `frontend/src/features/drafting-workspace/EditorPane.tsx:180-240` — the hand-rolled comment compose/cancel/submit flow.
- `frontend/src/features/task/PairwiseFindingsCard.tsx:90-98` — the per-item error map keyed by id.

## Implementation Plan

### Sub-tasks

**Task 1: `comment` on the PATCH route** — _small_

- Files: `engine/recommendations.py` (modify — `add_comment`), `engine/api.py` (modify), `engine/tests/test_api_recommendations.py` (modify)
- SEQUENTIAL (depends on Story 2's Task 1 — same route handler)

**Task 2: `rewrite_one` + the rewrite route** — _medium_

- Files: `engine/recommendations.py` (modify — `build_rewrite_prompt`, `rewrite_one`), `engine/api.py` (modify), `engine/tests/test_api_recommendations.py` (modify)
- SEQUENTIAL (depends on Task 1)

**Task 3: API client + types** — _small_

- Files: `frontend/src/lib/api.ts` (modify — `addRecommendationComment`, `rewriteRecommendation`), `frontend/src/lib/types.ts` (modify — `RecommendationComment`, `RecommendationRevision`), `frontend/src/test/msw/handlers.ts` (modify)
- SEQUENTIAL (depends on Task 2)

**Task 4: Comment thread + revisions disclosure** — _medium_

- Files: `frontend/src/features/task/RecommendationComments.tsx` (new), `frontend/src/features/task/RecommendationRevisions.tsx` (new), `frontend/src/features/task/RecommendationCard.tsx` (modify), `frontend/src/features/task/RecommendationsCard.tsx` (modify), `frontend/src/features/task/RecommendationsCard.test.tsx` (modify)
- SEQUENTIAL (depends on Task 3)

**Task 5: E2E** — _small_

- Files: `frontend/e2e/recommendations-comment.spec.ts` (new)
- SEQUENTIAL (depends on Task 4)

### Negative Constraints

- Do NOT write anything to `guardrails.json` from this story. No promotion, no re-interpretation, no "add to guardrails" side effect. This is the story's defining constraint.
- Do NOT let a rewrite change `id`, `bookmarked`, `dimensions` or `comments`.
- Do NOT let a rewrite bypass the evidence floor.
- Do NOT mutate or delete existing `revisions` entries.
- Do NOT make the rewrite touch any other recommendation in the set.
- Do NOT add a second model seam — reuse `generate_recommendations_fn`.
- Do NOT make comment or rewrite mutations optimistic.

## Test Scenarios

**Test 1: Comment appends with author and timestamp**

- Setup: a generated set of 3 in `tmp_path`
- Action: `PATCH …/recommendations/4f9f91c02ef5` with `{"comment": "HKMA's TSP is not our TPSP."}`
- Expected: `200`; `comments` has one entry with that text, the task owner as `author`, and an ISO-8601 `at`; `title` and `rationale` unchanged

**Test 2: Commenting makes no model call**

- Setup: a stub generator that raises if called
- Action: `PATCH` with a comment
- Expected: `200`; the stub was never invoked

**Test 3: Whitespace-only comment rejected**

- Action: `PATCH` with `{"comment": "   \n  "}`
- Expected: `400 EMPTY_COMMENT`, message `"A comment cannot be empty."`; file unchanged

**Test 4: Oversized comment rejected**

- Action: `PATCH` with a 4 001-character comment
- Expected: `413 COMMENT_TOO_LARGE`; file unchanged

**Test 5: Non-string comment rejected**

- Action: `PATCH` with `{"comment": 42}`
- Expected: `400 INVALID_PATCH`, message `"comment must be a string."`

**Test 6: Comment and bookmark in one request**

- Action: `PATCH` with `{"comment": "Scope is banking only.", "bookmarked": true}`
- Expected: `200`; both applied in a single write

**Test 7: Rewrite preserves identity**

- Setup: recommendation `4f9f91c02ef5`, `bookmarked: true`, `dimensions: ["third party oversight"]`, one comment; stub returns different `title`/`rationale`/`action`
- Action: `POST …/rewrite`
- Expected: `200`; `id`, `bookmarked`, `dimensions` and `comments` identical; `title` changed; position in the list unchanged

**Test 8: Rewrite appends the previous version**

- Setup: known `title`/`rationale`/`action`/`confidence_note`
- Action: `POST …/rewrite`
- Expected: `revisions` has one entry carrying exactly the pre-rewrite values plus an `at`; no `evidence` key in the revision

**Test 9: Two rewrites append two revisions in order**

- Action: rewrite twice with different stub responses
- Expected: `len(revisions) == 2`, oldest first; the first entry holds the original text

**Test 10: Comments reach the rewrite prompt**

- Setup: two comments on the card
- Action: `POST …/rewrite` with a prompt-recording stub
- Expected: both comment texts appear in the prompt, alongside the card's current title

**Test 11: Guardrails reach the rewrite prompt**

- Setup: `PUT …/guardrails` with `"Never cite another policy document by provision number."`
- Action: `POST …/rewrite` with a prompt-recording stub
- Expected: that sentence appears in the rewrite prompt

**Test 12: Rewrite without a comment is allowed**

- Setup: a card with `comments: []`
- Action: `POST …/rewrite`
- Expected: `200`; rewritten from evidence and guardrails alone

**Test 13: A rewrite that resolves no citations is rejected**

- Setup: stub returns a version citing only `finding_id: "does-not-exist"`
- Action: `POST …/rewrite`
- Expected: `502 REWRITE_FAILED`; the file's bytes are unchanged; no `revisions` entry appended

**Test 14: A failed rewrite preserves the comment**

- Setup: comment recorded; stub raises `RuntimeError`
- Action: `POST …/rewrite`
- Expected: `502 REWRITE_FAILED`; the comment is still in the file; the recommendation unchanged

**Test 15: A rewrite touches only its own card**

- Setup: 3 recommendations; capture the other two from disk
- Action: `POST …/rewrite` on the first
- Expected: the other two dicts are `==` their captured values

**Test 16: Nothing is written to the guardrails**

- Setup: no `guardrails.json`; capture the directory listing
- Action: `PATCH` a comment, then `POST …/rewrite`
- Expected: still no `guardrails.json`; `GET …/guardrails` returns `is_default: true` with the unmodified defaults

**Test 17: A comment does not survive its card's replacement**

- Setup: comment on an **unbookmarked** recommendation
- Action: `POST …/generate` with a stub returning a different set
- Expected: that recommendation and its comment are gone; `GET` shows no trace; the guardrails are unchanged

**Test 18: A bookmarked card keeps its comments across regeneration**

- Setup: comment on a **bookmarked** recommendation
- Action: `POST …/generate`
- Expected: the entry survives byte-for-byte, `comments` included

**Test 19: Unknown recommendation id on rewrite**

- Action: `POST …/recommendations/deadbeef0000/rewrite`
- Expected: `404 RECOMMENDATION_NOT_FOUND`; file unchanged

**Test 20: Comment box disabled while empty (component test)**

- Action: render a card, open the compose box, type only spaces
- Expected: `Submit` is disabled; no request is made

**Test 21: Rewrite spinner is per card (component test)**

- Setup: MSW delays the rewrite response
- Action: press `Rewrite` on the first of three cards
- Expected: only that card shows a spinner and disables its actions; the others remain interactive

## Acceptance Criteria

- [ ] A comment persists with resolved author and server timestamp, and makes no model call
- [ ] Empty, oversized and non-string comments are refused with their stated codes
- [ ] A rewrite preserves `id`, `bookmarked`, `dimensions`, `comments` and list position
- [ ] Each rewrite appends exactly one `revisions` entry; existing entries are never altered
- [ ] Comments and guardrails both reach the rewrite prompt
- [ ] A rewrite that resolves no citations is refused and the original kept
- [ ] A failed rewrite leaves the file byte-identical and preserves the comment
- [ ] A rewrite touches no other recommendation
- [ ] **Nothing in this story writes to `guardrails.json`**
- [ ] Comment and rewrite mutations are not optimistic
- [ ] Engine suite passes with no model credentials

## Verification

Run the verifier skill. Locally `.venv/bin/python -m pytest engine/tests` and `cd frontend && npm run test`.

### Backend API Tests

| File | Covers |
| ---- | ------ |
| `engine/tests/test_api_recommendations.py` (modify) | Tests 1–19 — comment validation, rewrite identity preservation, revisions append, evidence floor on rewrite, failure isolation, and the guardrails-untouched assertions |

Test 16 is the one that would catch a regression reintroducing automatic promotion — keep it.

### Browser/UI Testing

1. Generate on `/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd`.
2. Press `Comment` on a card → box opens. Type only spaces → `Submit` disabled.
3. Type a real comment, submit → appears with author and date; the recommendation text is unchanged.
4. Add a second comment → both listed oldest-first.
5. Press `Rewrite` → only that card spins; the others stay clickable.
6. On success → text changed, bookmark intact, position unchanged, "Rewritten" marker present.
7. Expand revisions → the previous version's title, rationale and action.
8. Open the guardrails → **the comment is not there**.
9. Bookmark another card, comment on it, regenerate → the bookmarked card keeps its comment; unbookmarked cards and their comments are gone.

### E2E Tests

| Key Scenario | Test file | Assigned sub-task |
| ------------ | --------- | ----------------- |
| Recording why a recommendation misses | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| Commenting does not rewrite | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| Rewriting one recommendation from my comment | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| Several comments all inform one rewrite | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| A rewritten recommendation keeps what it said before | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| A rewritten recommendation keeps its bookmark | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| An empty comment is not recorded | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| Nothing I write is promoted without me | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |
| Comments survive leaving and returning | `frontend/e2e/recommendations-comment.spec.ts` | Task 5 |

Covered by Test Scenarios rather than E2E: prompt assembly (Tests 10, 11), the evidence floor on rewrite (13), failure isolation (14, 15), and comment mortality across regeneration (17, 18) — all of which need a stubbed model or byte-level file assertions. Two scenarios are **not** E2E-testable against a live model and are asserted at the prompt level instead: *"A rewritten recommendation still quotes its evidence"* and *"The Copilot can still use what I said"*.

**Locator strategies:** `data-testid="recommendation"` with `data-rec-id`, `data-testid="comment-open"`, `data-testid="comment-input"`, `data-testid="comment-submit"`, `data-testid="comment"`, `data-testid="rewrite"`, `data-testid="revisions-toggle"`, `data-testid="rewritten-marker"`, `data-testid="guardrails-body"`.

**Fixture discipline:** comments and rewrites write to `data/workstreams/open-finance-pd-2026/recommendations/`, a tracked path. `git checkout -- data/workstreams/open-finance-pd-2026` in `beforeEach`, as `reviewed-tab.spec.ts:47-51` does. A rewrite reaches a live model, so this spec needs engine credentials **or** a stubbed engine — note it in the file header alongside the existing convention in `e2e/README.md`.
