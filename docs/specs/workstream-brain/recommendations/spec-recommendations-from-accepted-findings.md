# Recommendations From My Accepted Findings

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Recommendations — Overview](spec.md)

Aisyah finishes triaging linkages holding thirty accepted findings and no answer to what the policy document should actually say. This story turns those accepted findings into written recommendations — what to do, why, and on which clause — formulated on the policy requirements she recorded herself. It replaces the Source card, which shows her nothing she acts on.

## User Story

As Aisyah R., I want the linkages I have accepted turned into written recommendations, so that I leave the task screen with a policy position rather than a pile of comparisons.

## Background & Context

**Current state:**

- The task screen's left column holds a **Source card**: the document's name, its format and clause count, when it was last edited, its owner, its reviewers, and its status. The page header directly above it already shows the owner, the format and the status.
- The right column holds the **Pairwise findings** box, where Aisyah accepts or dismisses every AI-found linkage in the working draft's neighbourhood. On the 2026 Open Finance policy document there are 130 of them.
- Each finding compares two clauses and carries one of five labels — aligns with, differs on, conflicts with, silent on, goes beyond — with the clauses quoted word-for-word.
- Everything she accepts appears in a **Reviewed** tab beside the draft, as a read-only list.
- Every document's regulatory profile has a **Policy requirement** field, entered as a comma-separated list. Beneath it the form already reads: _"These become the dimensions the Recommendations feature is formulated on."_

**Problem:**

- **The tool does the reading and leaves her the thinking.** A finding says our clause is silent where a peer regulator's is not. It never says what to do about it. Synthesising thirty of those into policy positions is the actual work, and it happens entirely in Aisyah's head.
- **Thirty findings do not fit in a head.** Ten findings across consent, liability and API security are a theme. The tool shows a flat list and never draws it.
- **The form makes a promise the tool does not keep.** Aisyah is told her policy requirements become the dimensions recommendations are formulated on. There are no recommendations.
- **The most valuable column on the screen shows nothing actionable.** The Source card repeats the header and adds a clause count.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, on the task screen for a working draft.
- **Context:** She has just finished, or is partway through, triaging the neighbourhood's findings. She is about to open the draft and start writing.
- **Current workaround:** She reads down the Reviewed list and works out the themes herself, on paper or in her head, before she starts drafting.

## Goals

- Turn Aisyah's accepted findings into written recommendations without her leaving the task screen.
- Formulate them on the policy requirements she recorded on the working draft.
- Show her, for every recommendation, the accepted findings behind it and their clauses quoted word-for-word.
- Show her which accepted findings **nothing drew on**, so a coverage gap is visible rather than silent.
- Give the rules the engine follows a **visible, editable home** on the card that generates from them, pre-populated so it is useful from the first day.
- Tell her plainly when the tool cannot proceed, and give her the way forward.
- Free the left column by deleting the Source card.

## Non-Goals

- **Bookmarking, commenting, or rewriting.** Those are the other stories. This one generates and displays.
- **Writing policy text.** A recommendation says what should change, not how the clause should read.
- **Acting on a finding nothing drew on.** The coverage section reports and links through. Generating from one finding on its own, or marking it as needing no action, are not offered.
- **Configuring the Copilot.** That is the Playbook, in the drafting workspace. The guardrails here steer the recommendations engine and nothing else.
- **Recommending from findings she has not accepted.** Dismissed and untriaged findings are not evidence.
- **Generating anything automatically.** Nothing is produced on page load. Generating is always Aisyah's decision, because it costs time and a model call.
- **Recommendations on published documents.** Only a working draft has something to change.

## User Workflow

1. **She opens the task screen.** Where the Source card used to be there is a **Recommendations** card, empty, with a Generate action.
2. **She generates.** The card reports what it is working from — how many accepted findings, across how many dimensions — while it works.
3. **She reads the result.** Seven recommendations. Each gives its title, the dimensions it touches, its reasoning, the action for BNM, and the accepted findings behind it.
4. **She checks the evidence.** She expands one recommendation's citations and reads the two clauses in full, with their numbers, exactly as they appear in the source documents.
5. **She checks what the tool is unsure of.** Beside a title is an information marker. She hovers it and reads what the tool could not verify from the documents available.
6. **She checks what was left out.** Below the recommendations, a collapsed section reports that 7 of her 30 accepted findings were not drawn on by anything. She expands it, reads two, and agrees neither warrants a policy change.
7. **She reads the rules.** A protection badge in the card's header opens the guardrails. They already hold the five defaults in plain language, and one of them explains why a recommendation she expected never appeared.
8. **She adds a rule of her own.** She records that HKMA's third party term means our data consumer, not our TPSP, and saves.
9. **She generates again later.** Having accepted twelve more findings, she presses Generate again and gets a fresh set drawing on all of them — and following the guardrails as they now read.

## Acceptance Criteria

### Scenario: Generating recommendations from accepted findings

```gherkin
Given I am on the task screen for the 2026 Open Finance policy document
  And its policy requirements are recorded as "consent management, third party oversight, liability allocation"
  And I have accepted 30 findings in its neighbourhood
When I generate recommendations
Then I am shown a set of recommendations
  And each one states what BNM should do and why
  And each one shows which of my three policy requirements it touches
```

### Scenario: Every recommendation quotes the clause it rests on

```gherkin
Given recommendations have been generated for the 2026 Open Finance policy document
When I expand the citations on the recommendation about publishing a data consumer list
Then I see each accepted finding it draws on
  And I see the clause number and the clause text for each
  And the clause text matches the source document word-for-word
```

### Scenario: The tool will not generate without policy requirements

```gherkin
Given I am on the task screen for a working draft
  And no policy requirements are recorded on it
When I look at the Recommendations card
Then I am told that recommendations are formulated on policy requirements and none are set
  And I am offered a way to go and set them
  And I cannot generate
```

### Scenario: Setting policy requirements unblocks generation

```gherkin
Given the Recommendations card is telling me no policy requirements are set
When I record "consent management, API security" on the working draft's profile
  And I return to the task screen
Then I can generate recommendations
  And they are formulated on those two dimensions
```

### Scenario: The tool will not generate without accepted findings

```gherkin
Given I am on the task screen for a working draft
  And its policy requirements are recorded
  And I have not accepted any findings in its neighbourhood
When I look at the Recommendations card
Then I am told to accept findings first
  And I cannot generate
```

### Scenario: A dimension with no supporting evidence is reported, not invented

```gherkin
Given the working draft records "liability allocation" as one of its policy requirements
  And none of my accepted findings bears on liability
When I generate recommendations
Then no recommendation claims to address liability allocation
  And nothing is written that my accepted findings do not support
```

### Scenario: Findings I dismissed are not used

```gherkin
Given I have accepted 12 findings and dismissed 40 in the neighbourhood
When I generate recommendations
Then the recommendations draw only on the 12 I accepted
  And the card tells me it worked from 12 accepted findings
```

### Scenario: Evidence spans the whole neighbourhood, not just the draft's own comparisons

```gherkin
Given the 2026 Open Finance policy document has one direct comparison, which has no findings
  And I have accepted findings on comparisons between its neighbouring documents
When I generate recommendations
Then those accepted findings are used as evidence
  And the set I see matches the findings shown in the Pairwise findings box
```

### Scenario: The tool states what it could not verify

```gherkin
Given a recommendation proposes prescribing concrete implementation milestones
  And nothing in the workstream's documents says who owns implementation planning
When I read that recommendation
Then I can see a note about what the tool could not verify
  And it is available on hover, on keyboard focus, and on tap
```

### Scenario: A recommendation does not tell BNM to cite another document by provision number

```gherkin
Given my accepted findings include one comparing the draft to the technology risk policy document
When I generate recommendations
Then no recommendation asks for a mapping to specific numbered provisions of another policy document
  And any cross-reference it proposes is expressed in general terms
```

### Scenario: A recommendation stays inside what the draft covers

```gherkin
Given the working draft states that it applies to banking participants only
When I generate recommendations
Then no recommendation proposes obligations on entities the draft does not cover
```

### Scenario: Mutual silence is not reported as agreement

```gherkin
Given an accepted finding compares two documents that are both high-level on liability
When I generate recommendations
Then any recommendation covering liability says that neither document elaborates
  And it does not describe the two as aligned
```

### Scenario: A shared term that means different things is flagged rather than asserted

```gherkin
Given an accepted finding compares our third party service provider clauses with a peer regulator's
  And the two documents use the same term for different things
When I generate recommendations
Then any recommendation on that point either establishes that the terms match
  Or says the equivalence could not be established from the documents
```

### Scenario: Generating again replaces the previous set

```gherkin
Given recommendations were generated yesterday from 18 accepted findings
  And I have since accepted 12 more
When I generate recommendations again
Then I see a new set drawing on all 30 accepted findings
  And the card reports when it was generated
```

### Scenario: Recommendations survive leaving and returning

```gherkin
Given I generated recommendations for the 2026 Open Finance policy document this morning
When I close the task screen and open it again this afternoon
Then the same recommendations are still there
  And I am not asked to generate them again
```

### Scenario: Accepted findings no recommendation drew on are reported

```gherkin
Given I have accepted 30 findings in the neighbourhood
  And the recommendations I generated draw on 23 of them
When I look below the recommendations
Then I am told that 7 accepted findings are not yet reflected
  And that section is collapsed
```

### Scenario: Reading what was left out

```gherkin
Given 7 of my accepted findings are not yet reflected
When I expand that section
Then I see each of those findings
  And I see its label, both documents it compares, and its clauses
  And I can open any of them on the review screen
```

### Scenario: Every accepted finding was drawn on

```gherkin
Given every accepted finding was drawn on by at least one recommendation
When I look below the recommendations
Then I am told that nothing is left unreflected
```

### Scenario: Coverage counts against every recommendation, not only the ones I chose

```gherkin
Given the recommendations I generated draw on 23 of my 30 accepted findings
  And I have bookmarked only two of those recommendations
When I look at what is not yet reflected
Then it reports 7
  And the count does not change when I bookmark or unbookmark
```

### Scenario: Coverage follows my triage

```gherkin
Given 7 accepted findings are not yet reflected
When I dismiss two of those findings in the Pairwise findings box
  And I return to the Recommendations card
Then it reports 5 accepted findings not yet reflected
```

### Scenario: Nothing in that section writes or generates

```gherkin
Given I have expanded the not yet reflected section
When I look at what I can do with a finding there
Then I can read it and open it on the review screen
  And there is no way to generate a recommendation from it on its own
```

### Scenario: The guardrails ship ready to use

```gherkin
Given I have never opened the guardrails on this workstream
When I open them from the Recommendations card
Then they already contain the five default rules in plain language
  And I am not shown an empty box
```

### Scenario: Editing the guardrails

```gherkin
Given I have opened the guardrails
When I add "HKMA's TSP means our data consumer, not our TPSP — do not assert a gap on the shared acronym"
  And I save
Then the guardrails show what I wrote
  And they still show it when I return
```

### Scenario: Edited guardrails take effect on the next generation

```gherkin
Given I have recorded a guardrail about third party terminology
When I generate recommendations
Then no recommendation treats those two terms as equivalent
```

### Scenario: Removing a default guardrail

```gherkin
Given the guardrails contain the default rule about not citing provision numbers
When I delete that rule and save
  And I generate recommendations
Then the tool is no longer bound by it
```

### Scenario: Guardrails are shared across a workstream's drafts

```gherkin
Given I have recorded a guardrail while working on the 2026 Open Finance policy document
When I open the guardrails on another working draft in the same workstream
Then they contain what I recorded
```

### Scenario: Guardrails do not travel between workstreams

```gherkin
Given I have recorded a guardrail in the Open Finance workstream
When I open the guardrails in the technology risk workstream
Then they contain the five defaults
  And they do not contain what I recorded
```

### Scenario: Emptying the guardrails is allowed and honest

```gherkin
Given I have opened the guardrails
When I clear them entirely and save
Then they are empty
  And I am told that recommendations will be generated with no guardrails
```

### Scenario: A guardrail save that fails loses nothing

```gherkin
Given I have edited the guardrails
When the save cannot be completed
Then I am told it could not be saved and can try again
  And my edits are still on screen
  And the previously saved guardrails are unchanged
```

### Scenario: The Source card is gone

```gherkin
Given I am on the task screen for a working draft
When I look at the left column
Then I see the Recommendations card and the Neighbour nodes card
  And there is no Source card
  And the draft's owner, format and status are still visible in the page header
```

### Scenario: A generation that fails loses nothing

```gherkin
Given recommendations were generated for this working draft yesterday
When I generate again and the attempt cannot be completed
Then I am told it could not be completed and can try again
  And yesterday's recommendations are still shown unchanged
```

### Scenario: A published document has no recommendations

```gherkin
Given I am looking at the technology risk policy document, which is published context
When I open it
Then it has no Recommendations card
  And I am not offered a way to generate recommendations for it
```

## Business Rules & Constraints

- **Dimensions come from the working draft's own Policy requirement field**, split on commas, with surrounding spaces ignored and empty entries discarded. Neighbouring documents' requirements are not pooled in.
- **Policy requirements are required to generate, but not to save a profile.** A drafter must be able to save a half-filled profile.
- **Only accepted findings are evidence**, across the working draft's whole neighbourhood — the same scope the Pairwise findings box uses.
- **Recommendation count is free-form.** A recommendation may span several dimensions; a dimension may attract several recommendations or none.
- **No recommendation without evidence.** Each rests on at least one accepted finding and reproduces its clause number and clause text word-for-word. Where nothing supports a point, nothing is written.
- **The workstream's guardrails constrain what may be written.** They live behind a protection badge on the Recommendations card, ship pre-populated with the five defaults — the four repeatable mistakes a BNM reviewer identified, plus the repo's standing citation rule — and are free text Aisyah edits and saves. The next generation reads whatever they say at that moment.
- **Guardrails belong to the workstream**, so a rule learned drafting one document protects every other draft beside it.
- **Nothing writes to the guardrails except Aisyah.** No comment, rewrite or generation edits them. A rule that governs every future generation is worth one deliberate action, and a tool that rewrote its own rules would be authoring what it then follows.
- **Emptying the guardrails is allowed**, and the tool says plainly what that means rather than silently reinstating the defaults.
- **Coverage is derived, never stored.** What is not yet reflected is the accepted set minus everything cited by any recommendation, computed when the card is read. A stored figure would drift from the findings it describes the moment a review state changed.
- **Coverage counts against every generated recommendation**, not only bookmarked ones, so the figure means the same thing on the task screen and beside the draft.
- **The not-yet-reflected section is read-only** and collapsed by default. It reports and links through; it does not generate, dismiss, or change a finding's state.
- **Every recommendation states what it could not verify.**
- **Nothing generates on load.** Generation is always the drafter's explicit action.
- **A failed generation leaves the previous set intact.**

## Success Metrics

- **Aisyah leaves the task screen with a written position.** The workflow above completes end-to-end on the 2026 Open Finance policy document.
- **Every recommendation on screen traces to a quoted clause.** None appears without at least one named accepted finding and its clause text.
- **No accepted finding disappears silently.** Every one Aisyah accepted is either drawn on by a recommendation or named in the not-yet-reflected section.
- **The left column shows something she acts on.** The Source card is gone and nothing it uniquely carried has been lost from the screen.

## Dependencies

- **The demo working draft's profile is seeded — met, no longer blocking.** `data/workstreams/open-finance-pd-2026/metadata/open-finance-pd-2026-pd.json` records six policy requirements: Governance; Participation and scope of information sharing; Transition arrangements; Consent management; Customer protection; Management of technology risk. These are the dimensions generation reasons over. The rename story moved this file from `concepts/` to `metadata/`, so it is read canonically.
- **Pre-generated output for the demo.** As with the existing pairwise analysis, a generated set is committed with the workstream so the demo needs no model call on the day.
- **One name for the regulatory profile store** is not a functional dependency, but ships alongside so this story's code is written against the corrected name once.
- **Nothing else.** This story owns both the recommendations and the guardrails box that constrains them, so it stands alone. The Playbook story configures the Copilot and does not touch this flow.

## Open Questions

- [x] ~~Should generation run automatically when the task screen opens?~~ — **Resolved: no.** It costs time and a model call, and the drafter should choose when her triage is complete enough to be worth synthesising.
- [x] ~~Should the Source card be kept in a reduced form?~~ — **Resolved: no, deleted.** Owner, format and status are in the header; the rest is not acted on.
- [x] ~~Should coverage be measured against all recommendations or only bookmarked ones?~~ — **Resolved: all generated recommendations.** One figure that means the same thing wherever it is read, and one that does not lurch when Aisyah bookmarks.
- [x] ~~Should Aisyah be able to generate a recommendation from a single uncovered finding?~~ — **Resolved: no.** The section reports coverage; acting on it means regenerating or accepting more evidence. A per-finding generator would produce recommendations outside the dimension structure the rest of the card depends on.
- [x] ~~Should the guardrails be protected from editing, or ship empty?~~ — **Resolved: neither — pre-populated and fully editable.** A rule the drafter cannot change is not accountable to her; an empty box on day one would be a feature nobody uses. The five defaults come from real reviewer evidence, so they are worth reading before they are worth changing.
- [x] ~~Do the guardrails belong to the workstream or the working draft?~~ — **Resolved: the workstream.** A hand-maintained rule is worth more shared than retyped per draft, and it matches the Playbook's scope so the two configuration surfaces behave alike.
- [ ] **What should the demo working draft's policy requirements actually be?** — **Deferred (non-blocking for design, blocking for the demo).** They must be real Open Finance policy dimensions, and they determine what the pre-generated set contains. To be settled with the drafter when the demo data is prepared.

---

## Functional Requirements

- **Dimension parsing:** `policy_requirement` is already a `LIST_FIELDS` member in `engine/concepts.py`, so it arrives as `list[str]` (or a bare `str` on legacy side-files). Parsing splits every member on `,`, strips each part, drops empties, and de-duplicates preserving first-seen order. `["consent management, API security", " liability "]` → `["consent management", "API security", "liability"]`.
- **Generation is a full replace with bookmark carry-over:** read the existing file, partition on `bookmarked`, generate afresh, write `pinned + new`. Never a merge of unbookmarked entries.
- **Atomicity:** the side-file is written once, after a successful model call, via the existing write-then-return pattern. A failed or malformed model response leaves the file byte-identical — no partial set is ever persisted.
- **Not idempotent, and deliberately so:** two `generate` calls produce two different sets (a model call is not deterministic). The idempotent operations are `GET` and the guardrails `PUT`.
- **Recommendation ids are opaque and stable:** `secrets.token_hex(6)` at creation, matching the opaque 12-char hex ids the `open-finance-*` findings fixtures already ship (`4f9f91c02ef5`). Not index-derived: a regeneration reorders the list, so an index-derived id would silently re-point a bookmark at a different recommendation.
- **Evidence floor is enforced in code, not merely prompted:** after parsing the model response, every `evidence[].finding_id` is resolved against the accepted set. A recommendation with zero resolvable citations is **dropped** before persisting, and the drop is counted in the response's `dropped_unsupported` field. This is what makes the guarantee structural rather than a hope about prompt adherence.
- **Coverage is computed on read:** `GET` derives `not_yet_reflected` as the accepted set minus every `finding_id` cited by any recommendation in the file. Never persisted.
- **UTF-8 on every write** (`encoding="utf-8"`), per `docs/learnings/pattern-engine-artifact-writes-utf8.md` — clause text carries `§`, en-dashes and U+2212.

### Validation & Business Rules

| Rule                                                                | Enforcement                  |
| ------------------------------------------------------------------- | ---------------------------- |
| Node must exist in the workstream graph                             | `404 NODE_NOT_FOUND`         |
| Node must be `node_type == "task"`                                  | `400 NOT_A_TASK`             |
| Task's parsed dimensions must be non-empty                          | `409 NO_POLICY_REQUIREMENTS` |
| At least one accepted finding in the neighbourhood                  | `409 NO_ACCEPTED_FINDINGS`   |
| Model response must be a JSON object with a `recommendations` array | `502 RECOMMENDATIONS_FAILED` |
| Guardrails body must be a string                                    | `400 INVALID_GUARDRAILS`     |
| Guardrails body ≤ 20 000 characters                                 | `413 GUARDRAILS_TOO_LARGE`   |

Guardrails have **no minimum length** — an empty string is a valid, deliberate state (see the "generated with no guardrails" scenario).

## Permissions & Security

- **Scope:** internal-only API, same trust boundary as every other `/api/workstreams/*` route. No auth exists in this prototype, and this story adds none.
- **Path traversal is the live risk.** `workstream_id` and `node_id` interpolate into filesystem paths. Both are resolved against the loaded graph **before** any read or write, exactly as `put_node_metadata` does (`engine/api.py:1445-1456`) — that ordering is the control that stops a `../` in `node_id` escaping the workstream directory.
- **Guardrails are prompt input, so treat them as untrusted text.** They are bounded at 20 000 characters and inserted into the system prompt as a delimited block. No sanitisation beyond the length bound: this is a text field a drafter authors for her own workstream, and the threat model is accidental paste, not injection by a third party.
- **Guardrails are never rendered as HTML.** They round-trip as plain text in a `<textarea>`; no `dangerouslySetInnerHTML` anywhere on this path.
- **Verbatim clause text is copied from the accepted findings, never re-derived.** The engine reads `source_clauses` / `target_clauses` off the finding record, so a recommendation cannot cite text its own evidence does not contain.

## API Design

### `GET /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations`

**Response (200)** — never 404s on "not generated yet":

```json
{
  "generated_at": "2026-08-02T09:14:22Z",
  "dimensions": [
    "consent management",
    "third party oversight",
    "liability allocation"
  ],
  "accepted_count": 30,
  "recommendations": [
    {
      "id": "4f9f91c02ef5",
      "title": "Publish and maintain a list of authorised data consumers",
      "rationale": "HKMA's framework requires banks to publish partnering providers. The ED requires oversight but is silent on publication.",
      "action": "Add a requirement for data providers to maintain and publish an up-to-date list of authorised data consumers accessing their systems.",
      "dimensions": ["third party oversight"],
      "evidence": [
        {
          "finding_id": "4f9f91c02ef5~0",
          "edge_id": "e-hkma_open_api_framework--ed_open_finance_2025",
          "label": "silent-on",
          "left": {
            "id": "hkma-open-api-framework",
            "title": "HKMA Open API Framework"
          },
          "right": {
            "id": "ed-open-finance-2025",
            "title": "ED Open Finance 2025"
          },
          "source_clause_number": "4.2",
          "source_clause_text": "An AI should publish on its website a list of all TSPs…",
          "target_clause_number": "10.4",
          "target_clause_text": "A data provider shall establish oversight arrangements…"
        }
      ],
      "confidence_note": "Assumes no separate industry register already performs this function; not verifiable from the documents in this workstream.",
      "bookmarked": false,
      "comments": [],
      "revisions": []
    }
  ],
  "not_yet_reflected": [
    {
      "finding_id": "a17c3e9b8d20~2",
      "edge_id": "e-bis_papers_168--ed_open_finance_2025",
      "label": "differs-on",
      "sentiment": "tighten",
      "summary": "The ED mandates a fixed rollout date where BIS observes facilitative approaches.",
      "left": { "id": "bis-papers-168", "title": "BIS Papers 168" },
      "right": { "id": "ed-open-finance-2025", "title": "ED Open Finance 2025" }
    }
  ],
  "counts": {
    "total": 7,
    "bookmarked": 0,
    "cited_findings": 23,
    "not_yet_reflected": 7
  }
}
```

Before the first generation: `{"generated_at": null, "dimensions": [...], "accepted_count": 30, "recommendations": [], "not_yet_reflected": [...], "counts": {"total": 0, ...}}`. `dimensions` is populated regardless, because the card needs it to decide between its empty states.

**Errors:**

| Status | Code                   | Condition                         |
| ------ | ---------------------- | --------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | No such workstream directory      |
| 404    | `NODE_NOT_FOUND`       | `node_id` absent from the graph   |
| 400    | `NOT_A_TASK`           | Node is not `node_type == "task"` |

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/recommendations/generate`

**Request:** empty body.

**Response (201):** the same shape as `GET`, plus `"dropped_unsupported": 1` when the evidence floor removed a recommendation the model returned.

**Errors:**

| Status | Code                     | Condition                                                                                                                                            |
| ------ | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 409    | `NO_POLICY_REQUIREMENTS` | Task's parsed `policy_requirement` is empty — message: `"Recommendations are formulated on the draft's policy requirements, and none are recorded."` |
| 409    | `NO_ACCEPTED_FINDINGS`   | No accepted findings in the neighbourhood — message: `"No findings have been accepted yet. Accept findings in the Pairwise findings box first."`     |
| 502    | `RECOMMENDATIONS_FAILED` | Model call raised, or response was unparseable / not a JSON object with a `recommendations` array. The previous set is untouched.                    |

### `GET /api/workstreams/{workstream_id}/guardrails`

**Response (200):**

```json
{
  "body": "1. Never recommend that a policy document cite another policy document by specific provision number…",
  "updated_at": "2026-08-02T09:02:11Z",
  "is_default": true
}
```

`is_default: true` when no file exists and the five defaults are being served. Lets the interface distinguish "never touched" from "saved, and happens to match".

### `PUT /api/workstreams/{workstream_id}/guardrails`

**Request:**

```json
{
  "body": "1. Never recommend citing another policy document by provision number.\n2. HKMA's \"TSP\" corresponds to Malaysia's data consumer, not our TPSP — do not assert a gap on the shared acronym."
}
```

**Response (200):** `{"body": "…", "updated_at": "2026-08-02T11:40:03Z", "is_default": false}` — re-read from disk after write, not projected from the request, matching `put_node_metadata`.

**Errors:**

| Status | Code                   | Condition                                                                       |
| ------ | ---------------------- | ------------------------------------------------------------------------------- |
| 404    | `WORKSTREAM_NOT_FOUND` | No such workstream                                                              |
| 400    | `INVALID_GUARDRAILS`   | `body` absent or not a string — message: `"body must be a string."`             |
| 413    | `GUARDRAILS_TOO_LARGE` | Over 20 000 characters — message: `"Guardrails hold at most 20000 characters."` |

## Data Model & Migrations

No database — two new JSON side-files under `data/workstreams/`.

**`{ws}/recommendations/{node_id}.json`**

| Field             | Type     | Constraints | Description                                   |
| ----------------- | -------- | ----------- | --------------------------------------------- |
| `generated_at`    | string   | ISO-8601 Z  | When the current set was produced             |
| `dimensions_used` | string[] | ≥1 member   | Parsed policy requirements at generation time |
| `recommendations` | object[] | —           | Bookmarked carried across, rest replaced      |

Per recommendation: `id` (opaque 12-hex), `title`, `rationale`, `action`, `dimensions` (string[]), `evidence` (object[], never empty), `confidence_note`, `bookmarked` (bool), `comments` (object[]), `revisions` (object[]). `comments` and `revisions` are written by Story 3; this story creates them as `[]`.

**`{ws}/guardrails.json`**

| Field        | Type   | Constraints   | Description                           |
| ------------ | ------ | ------------- | ------------------------------------- |
| `body`       | string | ≤20 000 chars | The rules, drafter-authored free text |
| `updated_at` | string | ISO-8601 Z    | Last save                             |

**Migration notes:** none. An absent `guardrails.json` serves `DEFAULT_GUARDRAILS`; an absent recommendations file serves the empty set. The three retired fixtures stay byte-identical, per the retired-fixtures rule in `CLAUDE.md`.

**Demo seed data (blocking for the demo, tracked paths):**

- `data/workstreams/open-finance-pd-2026/metadata/open-finance-pd-2026-pd.json` — the working draft's seven-field profile with a real `policy_requirement` list. Written to `metadata/` because the rename ships in the same change set.
- `data/workstreams/open-finance-pd-2026/recommendations/open-finance-pd-2026-pd.json` — a pre-generated set, so the demo needs no model call.

## UI/Frontend Requirements

### Components

**`RecommendationsCard`** — `frontend/src/features/task/RecommendationsCard.tsx` (new, ~230 LOC)

- Owns the `["recommendations", workstreamId, nodeId]` query, the generate mutation, and the guardrails disclosure.
- Header: title, `Generate` / `Regenerate` button, and the `ShieldCheck` protection badge.
- Body: bookmarked recommendations first, then the rest, then the collapsed coverage section.
- Capped and internally scrolled — `max-h-[calc(100vh-12rem)]`, matching `PairwiseFindingsCard.tsx:166`.

```typescript
interface Props {
  workstreamId: string;
  nodeId: string;
}
```

**`RecommendationCard`** — `frontend/src/features/task/RecommendationCard.tsx` (new, ~170 LOC)

```typescript
interface Props {
  rec: Recommendation;
  onToggleBookmark: (rec: Recommendation) => void; // Story 2 wires this
  isBookmarkPending: boolean;
}
```

**`GuardrailsPanel`** — `frontend/src/features/task/GuardrailsPanel.tsx` (new, ~110 LOC)

- Collapsed by default; the badge toggles it. `<textarea>` + `Save`, dirty-state tracked so `Save` is disabled when unchanged.
- On an empty save, shows: _"Recommendations will be generated with no guardrails."_

**`InfoBubble`** — `frontend/src/components/InfoBubble.tsx` (new, ~60 LOC)

```typescript
interface Props {
  children: React.ReactNode;
  label?: string; // accessible name, defaults to "More information"
}
```

Hand-rolled: `frontend/src/components/ui/` holds eight primitives and **no tooltip**, and `EditorPane.tsx:180-240` already hand-rolls its comment popover rather than adding a headless-component library. Opens on `onMouseEnter`, `onFocus` and `onClick` (tap), closes on `onMouseLeave`, `onBlur` and `Escape`. Trigger is a real `<button>` with `aria-describedby` pointing at the bubble, so it is reachable by keyboard.

**`NotYetReflectedSection`** — `frontend/src/features/task/NotYetReflectedSection.tsx` (new, ~90 LOC)

- Collapsed by default with the count in its header. Read-only: each row shows label, both endpoint titles, clause numbers, and a link to `/workstreams/{ws}/edges/{edgeId}/review?finding={id}`. No generate, no state change.

**`TaskScreenPage`** — `frontend/src/features/task/TaskScreenPage.tsx` (modify, ~10 LOC)

- Delete the `SourceCard` import and its render at line 235; render `RecommendationsCard` in its place.

**`SourceCard`** — `frontend/src/features/task/SourceCard.tsx` — **delete the file.**

### API client

`frontend/src/lib/api.ts` (modify, ~70 LOC) — following the existing `fetchPairwiseFindings` / `setReviewState` shape:

```typescript
export function fetchRecommendations(
  workstreamId: string,
  nodeId: string,
): Promise<RecommendationsResponse>;
export function generateRecommendations(
  workstreamId: string,
  nodeId: string,
): Promise<RecommendationsResponse>;
export function fetchGuardrails(
  workstreamId: string,
): Promise<GuardrailsResponse>;
export function saveGuardrails(
  workstreamId: string,
  body: string,
): Promise<GuardrailsResponse>;
```

`frontend/src/lib/types.ts` (modify, ~45 LOC) — `Recommendation`, `RecommendationEvidence`, `RecommendationsResponse`, `UnreflectedFinding`, `GuardrailsResponse`.

### User Interactions

| Action                              | Result                                                                                       |
| ----------------------------------- | -------------------------------------------------------------------------------------------- |
| Press `Generate`                    | Button shows a spinner and disables; on success the list renders and the query cache updates |
| Press the shield badge              | Guardrails panel expands with current text; badge is `aria-expanded`                         |
| Edit guardrails and `Save`          | Panel persists, stays open, shows a saved timestamp                                          |
| Press the `ⓘ` marker                | Bubble opens with the confidence note (also on hover and on focus)                           |
| Expand a recommendation's citations | Clause numbers and full clause text appear inline                                            |
| Expand `Not yet reflected`          | The uncited accepted findings list; each links to the review screen                          |

### States

- **Loading:** `Loader2` spinner with `role="status"` and "Loading recommendations…", matching `PairwiseFindingsCard.tsx:185-191`.
- **No dimensions:** _"No policy requirements set. Recommendations are formulated on them, so set them first."_ plus a link to the node's metadata form (`/workstreams/{ws}` with the node selected). `Generate` disabled.
- **No accepted findings:** _"Accept findings in the Pairwise findings box first, then generate."_ `Generate` disabled.
- **Generated, empty coverage gap:** the coverage section reads _"Every accepted finding is reflected in a recommendation."_
- **Error (generate):** inline message _"We could not generate recommendations. Try again."_ The previous set stays rendered.
- **Error (guardrails save):** inline message beside `Save`; the textarea keeps the drafter's edits.

## Architecture Notes

- **New dependencies:** none. `secrets` is stdlib; no new frontend package.
- **Injected model seam:** `create_app(..., generate_recommendations_fn=None)`, mirroring `run_arm_g_fn` (`engine/api.py:593`). When omitted, the route builds a workstream-bound adapter over `engine.llm.call_chat`. Every test injects a stub, so **CI needs no model or credentials** — the same discipline `test_api_arm_g.py` and `test_copilot.py` already follow.
- **Scope reuse, not reimplementation:** `workstreams.neighbourhood_edges(edges, node_id)` — the same call `get_pairwise_findings` (`engine/api.py:2021`) and `get_reviewed_linkages` (`engine/api.py:2121`) make. On `open-finance-pd-2026` the task node has exactly one edge and that pair has **no findings file at all**, so any narrower rule returns nothing.
- **Evidence projection reuses `_linkage_card`** (`engine/api.py:1945`) for the coverage section's rows, extended with clause **text** for the evidence blocks — `_linkage_card` deliberately carries clause numbers only.
- **No new engine dependency**, so `pyproject.toml` and the explicit `pip install` list in `.github/workflows/test.yml` both stay as they are — but note the standing rule in `docs/learnings/pattern-engine-deps-live-in-two-places.md` if that changes.

## Exemplar Files

- `engine/drafts.py` — the side-file module shape: module docstring naming the on-disk path, `*_path()` helper, `load`/`save`, UTF-8 writes, typed exceptions. Closest model for `engine/recommendations.py` and `engine/guardrails.py`.
- `engine/api.py:1979-2093` (`get_pairwise_findings`) — neighbourhood scan, per-edge `findings.load` with `FindingsNotAnalysedError` handling, counts assembly.
- `engine/api.py:1428-1474` (`put_node_metadata`) — the 404-guards-before-write ordering, validate-before-persist, and re-read-after-write response.
- `engine/arm_g.py` — prompt assembly and JSON-response parsing against `engine.llm.call_chat`.
- `frontend/src/features/task/PairwiseFindingsCard.tsx` — capped scrolling card, TanStack Query key layout, optimistic mutation with rollback, per-item error map.
- `frontend/src/features/drafting-workspace/EditorPane.tsx:180-240` — the hand-rolled popover precedent for `InfoBubble`.
- `engine/tests/test_api_pairwise_findings.py` — `shutil.copytree` fixture isolation into `tmp_path`, so reads double as integrity checks on the real fixtures and writes touch only the copy.

## Implementation Plan

### Sub-tasks

**Task 1: `engine/guardrails.py` + the two guardrails routes** — _small_

- Files: `engine/guardrails.py` (new), `engine/api.py` (modify), `engine/tests/test_api_guardrails.py` (new)
- `DEFAULT_GUARDRAILS` as a module constant carrying the five rules in plain prose; `load`/`save`; `GET`/`PUT` with the validation table above.
- INDEPENDENT

**Task 2: `engine/recommendations.py` — parsing, prompt, evidence floor** — _large_

- Files: `engine/recommendations.py` (new), `engine/tests/test_recommendations.py` (new)
- `parse_dimensions()`, `collect_evidence()` (neighbourhood + accepted only), `build_prompt()` (guardrails + dimensions + evidence + pinned titles), `parse_response()`, `enforce_evidence_floor()`, `load`/`save`.
- SEQUENTIAL (depends on Task 1 — the prompt reads the guardrails)

**Task 3: the three recommendations routes + the `generate_recommendations_fn` seam** — _medium_

- Files: `engine/api.py` (modify), `engine/tests/test_api_recommendations.py` (new)
- `GET` (with derived coverage), `POST …/generate`, and the seam on `create_app`.
- SEQUENTIAL (depends on Task 2)

**Task 4: `InfoBubble` primitive** — _small_

- Files: `frontend/src/components/InfoBubble.tsx` (new), `frontend/src/components/InfoBubble.test.tsx` (new)
- INDEPENDENT

**Task 5: API client + types** — _small_

- Files: `frontend/src/lib/api.ts` (modify), `frontend/src/lib/types.ts` (modify), `frontend/src/test/msw/handlers.ts` (modify — handlers for all four routes)
- SEQUENTIAL (depends on Task 3 for the response shapes)

**Task 6: `RecommendationsCard`, `RecommendationCard`, `GuardrailsPanel`, `NotYetReflectedSection`** — _large_

- Files: the four new files under `frontend/src/features/task/`, plus `RecommendationsCard.test.tsx`
- SEQUENTIAL (depends on Tasks 4 and 5)

**Task 7: Delete `SourceCard`, wire the card into the task screen** — _small_

- Files: `frontend/src/features/task/SourceCard.tsx` (**delete**), `frontend/src/features/task/TaskScreenPage.tsx` (modify), `frontend/src/features/task/TaskScreenPage.test.tsx` (modify — drop the `source-card` assertions)
- SEQUENTIAL (depends on Task 6)

**Task 8: Demo seed data + E2E** — _medium_

- Files: `data/workstreams/open-finance-pd-2026/recommendations/open-finance-pd-2026-pd.json` (new), `frontend/e2e/recommendations.spec.ts` (new)
- The profile is **already seeded** at `concepts/open-finance-pd-2026-pd.json` with six policy requirements; the read fallback picks it up, so no profile file is written by this task. Only the pre-generated recommendations set is new.
- SEQUENTIAL (depends on Task 7)

### Negative Constraints

- Do NOT modify `engine/findings.py`, `engine/linkage_review.py`, or the pairwise/review/reviewed-linkages routes. This story reads them.
- Do NOT change `workstreams.neighbourhood_edges` — call it.
- Do NOT touch the three retired fixtures (`opres-v2`, `rmit-v2-2025`, `open-finance-ed`). No `metadata/`, `guardrails.json` or `recommendations/` is added to them.
- Do NOT add a relevance score, a type/category field, or a second critic pass — all three are explicit non-goals with recorded rationale.
- Do NOT introduce a tooltip library. `InfoBubble` is hand-rolled.
- Do NOT rebuild `data/artifacts/` — see `docs/learnings/blocker-engine-build-silently-narrows-artifacts.md`.
- Do NOT write a `guardrails.json` for a workstream on read. Defaults are served, not persisted.

## Test Scenarios

**Test 1: Dimension parsing splits, strips, dedupes**

- Setup: `metadata/{task}.json` with `"policy_requirement": ["consent management, API security", " consent management ", ""]`
- Action: `parse_dimensions(profile)`
- Expected: `["consent management", "API security"]` — split on commas, stripped, empty dropped, duplicate removed, first-seen order kept

**Test 2: Legacy scalar `policy_requirement` tolerated**

- Setup: profile with `"policy_requirement": "consent management, liability"` (a bare string, as retired fixtures carry)
- Action: `parse_dimensions(profile)`
- Expected: `["consent management", "liability"]`, no exception

**Test 3: Generate is blocked with no policy requirements**

- Setup: `tmp_path` copy of `data/workstreams`, then **delete** `open-finance-pd-2026/metadata/open-finance-pd-2026-pd.json` from the copy — the seeded profile means the gate has to be tested against an explicitly emptied state, not an assumed-absent one. (Equivalently: rewrite that file with `"policy_requirement": []`.)
- Action: `POST /api/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd/recommendations/generate`
- Expected: `409 NO_POLICY_REQUIREMENTS`; no `recommendations/` directory created; the stub generator is never called

**Test 3b: The seeded demo profile satisfies the gate**

- Setup: `tmp_path` copy of `data/workstreams`, untouched; one accepted finding in the neighbourhood
- Action: same `POST`
- Expected: not a `409`; `dimensions_used` is the six seeded requirements in order — `["Governance", "Participation and scope of information sharing", "Transition arrangements", "Consent management", "Customer protection", "Management of technology risk"]`. This is the demo path, so it is asserted directly rather than inferred from Test 3.

**Test 4: Generate is blocked with no accepted findings**

- Setup: the seeded profile left as-is; every finding in the neighbourhood left `pending`
- Action: same `POST`
- Expected: `409 NO_ACCEPTED_FINDINGS`; stub generator never called

**Test 5: Evidence comes from the whole neighbourhood**

- Setup: accept `e-hkma_open_api_framework--ed_open_finance_2025~0` — a second-order edge; the task's own edge `e-open_finance_pd_2026_pd--ed_open_finance_2025` has no findings file
- Action: `POST …/generate` with a stub echoing back the evidence it was handed
- Expected: that finding is in the generator's input; `accepted_count == 1`. Guards the exact defect the pairwise route was widened to fix.

**Test 6: Evidence floor drops an unsupported recommendation**

- Setup: three accepted findings; stub returns two recommendations, one citing `finding_id: "does-not-exist"`
- Action: `POST …/generate`
- Expected: `201`, `len(recommendations) == 1`, `dropped_unsupported == 1`; the persisted file contains only the supported one

**Test 7: Every persisted recommendation carries clause text verbatim**

- Setup: accept a finding whose `source_clauses[0].text` contains `§` and an en-dash
- Action: `POST …/generate`, then read the file from disk with `encoding="utf-8"`
- Expected: `evidence[0].source_clause_text` is character-identical to the finding's own clause text

**Test 8: Bookmarks survive regeneration byte-for-byte**

- Setup: generate 3; `PATCH` one to `bookmarked: true` (Story 2 route, or set directly in the fixture for this story's test); capture its full dict
- Action: `POST …/generate` again with a stub returning 2 different recommendations
- Expected: the bookmarked dict is `==` its captured value including `id`; the other two are gone; total is 3

**Test 9: Pinned titles reach the prompt as "do not restate"**

- Setup: one bookmarked recommendation titled `"Publish and maintain a list of authorised data consumers"`
- Action: `POST …/generate` with a stub that records its prompt
- Expected: the prompt contains that title and the phrase directing the model not to restate it

**Test 10: A failed generation leaves the previous set intact**

- Setup: a generated set of 3 on disk; stub raises `RuntimeError("model unavailable")`
- Action: `POST …/generate`
- Expected: `502 RECOMMENDATIONS_FAILED`; the file's bytes are unchanged; a subsequent `GET` returns the original 3

**Test 11: A malformed model response is a 502, not a crash**

- Setup: stub returns `"not json at all"`
- Action: `POST …/generate`
- Expected: `502 RECOMMENDATIONS_FAILED`; file unchanged

**Test 12: `GET` before any generation is not an error**

- Setup: a profile with requirements; no `recommendations/` file
- Action: `GET …/recommendations`
- Expected: `200`, `generated_at is None`, `recommendations == []`, `dimensions` populated, `not_yet_reflected` lists every accepted finding

**Test 13: Coverage is derived and tracks review state**

- Setup: 5 accepted findings; a persisted set citing 3 of them
- Action: `GET …/recommendations`; then dismiss one uncited finding via `PATCH …/findings/{id}`; `GET` again
- Expected: first `not_yet_reflected` has 2 entries; second has 1. The recommendations file is not rewritten by either `GET`.

**Test 14: A non-task node is rejected**

- Setup: `rmit-2025` — a real node, `node_type == "internal-published"`
- Action: `GET /api/workstreams/open-finance-pd-2026/tasks/rmit-2025/recommendations`
- Expected: `400 NOT_A_TASK`

**Test 15: A missing node is distinguished from a non-task node**

- Action: `GET …/tasks/no-such-node/recommendations`
- Expected: `404 NODE_NOT_FOUND` — the same distinction `get_pairwise_findings` draws

**Test 16: Guardrails default when no file exists**

- Setup: no `guardrails.json` in the workstream
- Action: `GET /api/workstreams/open-finance-pd-2026/guardrails`
- Expected: `200`, `is_default: true`, `body` containing all five default rules; **no file written to disk**

**Test 17: Guardrails round-trip and reach the prompt**

- Action: `PUT …/guardrails` with `{"body": "Never cite another policy document by provision number."}`; then `POST …/generate` with a prompt-recording stub
- Expected: `PUT` returns `is_default: false`; the file exists; the generate prompt contains that exact sentence and **not** the default text

**Test 18: Empty guardrails are accepted**

- Action: `PUT …/guardrails` with `{"body": ""}`
- Expected: `200`, `is_default: false`, file written with `body: ""`; a following `GET` returns `""`, not the defaults

**Test 19: Oversized guardrails rejected**

- Action: `PUT …/guardrails` with a 20 001-character body
- Expected: `413 GUARDRAILS_TOO_LARGE`, message `"Guardrails hold at most 20000 characters."`; existing file unchanged

**Test 20: Guardrails reject a non-string body**

- Action: `PUT …/guardrails` with `{"body": ["a", "b"]}`
- Expected: `400 INVALID_GUARDRAILS`, message `"body must be a string."`

**Test 21: Guardrails are per workstream**

- Action: `PUT` a body on `open-finance-pd-2026`; `GET` on `opres-v2`
- Expected: `opres-v2` returns `is_default: true` with the defaults; **no file created under `data/workstreams/opres-v2/`** (retired-fixture rule)

**Test 22: Path traversal is refused before any filesystem access**

- Action: `GET /api/workstreams/open-finance-pd-2026/tasks/..%2F..%2Fetc/recommendations`
- Expected: `404 NODE_NOT_FOUND`; nothing read or written outside the workstream directory

**Test 23: Recommendation ids are opaque, not index-derived**

- Action: generate twice with stubs returning different sets
- Expected: no id matches `^.*~\d+$`; each is 12 hex characters; no id from the first set reappears in the second

## Acceptance Criteria

- [ ] `GET` returns an empty set with `generated_at: null` before the first generation, never a 404
- [ ] Both 409 gates fire before the model seam is called
- [ ] Evidence scope equals `neighbourhood_edges` — the same set the Pairwise findings box shows
- [ ] Every persisted recommendation cites ≥1 resolvable accepted finding, with clause text character-identical to the finding record
- [ ] Bookmarked recommendations survive regeneration byte-for-byte, including their ids
- [ ] Guardrails serve the five defaults when absent, without writing a file
- [ ] An empty guardrails body is accepted and served back empty
- [ ] Coverage is absent from the persisted file and derived on every read
- [ ] `SourceCard.tsx` no longer exists and no test references `source-card`
- [ ] `InfoBubble` opens on hover, on keyboard focus and on tap, and closes on `Escape`
- [ ] The full engine suite passes with no model credentials present
- [ ] No new dependency in `pyproject.toml` or `frontend/package.json`

## Verification

Run the verifier skill to confirm changes are clean. Locally: `.venv/bin/python -m pytest engine/tests` and `cd frontend && npm run test`. Per `docs/learnings/blocker-forge-verify-hook-false-fail-pyenv-ruff.md`, the forge `stop-verify` hook reports a cosmetic `LINT FAIL` here — ignore it; pytest via `.venv` is the real signal. Per `docs/learnings/blocker-forge-build-run-in-main-worktree.md`, run builds in the main tree, not a worktree.

### Backend API Tests

| File                                             | Covers                                                                                                                                              |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `engine/tests/test_recommendations.py` (new)     | Tests 1, 2 (dimension parsing), evidence collection, prompt assembly, evidence-floor enforcement, response parsing — pure module tests, no HTTP     |
| `engine/tests/test_api_recommendations.py` (new) | Tests 3–15, 22, 23 — routes via `TestClient` with an injected stub generator, `shutil.copytree` into `tmp_path` per `test_api_pairwise_findings.py` |
| `engine/tests/test_api_guardrails.py` (new)      | Tests 16–21 — defaults, round-trip, empty body, size cap, type validation, per-workstream isolation                                                 |

`httpx` and `python-multipart` are already explicit deps for `TestClient` — see `docs/learnings/pattern-fastapi-testclient-deps.md`.

### Browser/UI Testing

Engine on `:8000`, Vite on `:5173`, `VITE_API_BASE=http://localhost:8000`. No credentials needed once the pre-generated set is committed.

1. Open `/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd` → left column shows Recommendations above Neighbour nodes; **no Source card**.
2. Header still shows owner, format and status.
3. Press the shield badge → guardrails expand with the five defaults.
4. Edit, `Save` → panel persists; reload → the edit is still there.
5. Clear entirely, `Save` → the "no guardrails" warning shows.
6. Hover a `ⓘ` marker → note appears. Tab to it → appears on focus. `Escape` → closes.
7. Expand a recommendation's citations → clause numbers and full text.
8. Expand `Not yet reflected` → uncited accepted findings; click one → lands on the review screen at that finding.
9. Narrow the viewport to 375 px → the card scrolls internally rather than the page.

### E2E Tests

| Key Scenario                                             | Test file                                         | Assigned sub-task |
| -------------------------------------------------------- | ------------------------------------------------- | ----------------- |
| Generating recommendations from accepted findings        | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| Every recommendation quotes the clause it rests on       | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| The tool will not generate without policy requirements   | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| The tool will not generate without accepted findings     | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| Accepted findings no recommendation drew on are reported | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| Reading what was left out                                | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| The guardrails ship ready to use                         | `frontend/e2e/recommendations-guardrails.spec.ts` | Task 8            |
| Editing the guardrails                                   | `frontend/e2e/recommendations-guardrails.spec.ts` | Task 8            |
| Emptying the guardrails is allowed and honest            | `frontend/e2e/recommendations-guardrails.spec.ts` | Task 8            |
| The tool states what it could not verify                 | `frontend/e2e/recommendations.spec.ts`            | Task 8            |
| The Source card is gone                                  | `frontend/e2e/recommendations.spec.ts`            | Task 8            |

Scenarios covered by Test Scenarios above and **not** duplicated as E2E: the four guardrail-content assertions (house convention, scope boundary, mutual silence, terminology), which are prompt-adherence properties best asserted against a recorded prompt, not a browser; and the per-workstream / persistence / failure-path scenarios.

**Locator strategies:** `data-testid="recommendations-card"`, `data-testid="recommendation"` (with `data-rec-id`), `data-testid="guardrails-badge"`, `data-testid="guardrails-body"`, `data-testid="not-yet-reflected"`, `data-testid="not-yet-reflected-count"`, `data-testid="info-bubble"`. Plus `getByRole("button", { name: /generate/i })`. Follows the `data-testid` convention in `pairwise-findings.spec.ts` and `reviewed-tab.spec.ts`.

**Fixture discipline:** generating writes to `data/workstreams/open-finance-pd-2026/recommendations/`, and accepting findings writes to `findings/`. Both are tracked paths, so the spec runs `git checkout -- data/workstreams/open-finance-pd-2026` in `beforeEach`, exactly as `reviewed-tab.spec.ts:47-51` does, and the file header carries the same warning.
