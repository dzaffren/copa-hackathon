# A Regulatory Profile the Drafter Can Edit

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Task Type & Editable Node Metadata — Overview](spec.md)

Every document in a workstream has a Regulatory profile card — policy owner, applicability, empowerment framework, issuance date, effective date, legal basis, and ISMP classification. Today it is read-only, and for most documents it shows a placeholder saying the information is not available. This story lets Aisyah fill it in and correct it herself, on any document, and keeps what she saves.

## User Story

As Aisyah R., I want to fill in and correct a document's regulatory profile myself, so that what I know about a document lives in the workstream rather than in my head.

## Background & Context

**Current state:**

- Opening any document shows a collapsed Regulatory profile section. Expanding it lists seven fields: policy owner, applicability, empowerment framework, issuance date, effective date, legal basis, and ISMP classification. (`keywords` and `requirement` were removed on 30 Jul 2026 — the extracted axes in the Concepts section carry a document's topics from the document itself.)
- For a small number of documents the card has content, prepared ahead of time outside the tool. The Operational Resilience working draft, for instance, shows Aisyah as its policy owner, and quotes the Financial Services Act provision it is issued under.
- For every other document — the Basel operational resilience principles, the Financial Services Act, industry submissions — the card shows a single line of text explaining that concept extraction is not enabled, and nothing else.
- ISMP classification is empty on every document, and displays as "Pending — RH publication form" where a profile exists at all, because its source is not available to the tool. Its four values are UMUM, TERHAD, SULIT and RAHSIA.
- Nothing in the tool can change any of it.

**Problem:**

- **A drafter cannot record what she knows.** Aisyah knows the RMiT policy document came into force on 28 November 2025. The card has a field for exactly that and no way to put it there.
- **A drafter cannot correct what is wrong.** If a prepared profile names the wrong policy owner, it stays wrong.
- **Most documents show an apology instead of a profile.** A card that says information is not available, on a document the drafter knows a great deal about, makes the tool look like a fixture rather than a workspace — and there is no route from that state to a filled-in one.
- **What the drafter knows is not recorded anywhere the tool can use.** Later work — a Copilot that understands a document's applicability and legal basis before answering — has nothing to read.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, working across several documents in a workstream.
- **Context:** While building out or reviewing a workstream's graph — inspecting a document she has just attached, or one that has been in the workstream for weeks.
- **Current workaround:** She keeps this knowledge in her own notes, or in her head. Nothing about a document's regulatory identity is recorded unless it was prepared before the workstream was demonstrated.

## Goals

- Let Aisyah edit the seven profile fields on **any** document in **any** workstream.
- Replace the "not available" placeholder with a profile she can start filling in.
- Keep what she saves, so it is there when she comes back and available to later work.
- Preserve the tool's honesty: a field she has not filled in says so, and nothing she types is ever presented as a quotation from the document.

## Non-Goals

- **Filling the profile in automatically by reading the document.** Existing preparation work does this outside the tool and is unchanged.
- **Letting a drafter mark a field as "not applicable".** A field is filled in or it is not.
- **Editing the deliverable kind.** It appears on a working draft's profile as a read-only line; it is set once at creation and cannot be changed here.
- **Obtaining ISMP classifications.** The field stays editable like any other, but the tool still has no source of its own for it.

## User Workflow

1. **She opens a document.** Inspecting the RMiT policy document, she expands its Regulatory profile. The policy owner is recorded; the effective date is not set.
2. **She presses Edit.** The card becomes a form, with the current values already in place.
3. **She fills in what she knows.** She types 28 November 2025 as the effective date and picks TERHAD as the ISMP classification.
4. **She saves.** The form becomes a card again, showing her new values.
5. **She comes back later.** The values are still there.
6. **She works on a document nobody prepared.** Opening the Basel principles, she finds a profile where every field reads "Not set", with the same Edit button. She fills in the two she is confident about and leaves the rest.

## Acceptance Criteria

### Scenario: Filling in a field that was not set

```gherkin
Given I am viewing the RMiT policy document's regulatory profile
  And its effective date is not set
When I press Edit
  And I enter "28 November 2025" as the effective date
  And I save
Then the profile shows "28 November 2025" as the effective date
  And the profile is no longer in editing mode
```

### Scenario: Correcting a value that is already recorded

```gherkin
Given I am viewing the Operational Resilience working draft's regulatory profile
  And its policy owner is recorded as "Aisyah R."
When I press Edit
  And I change the policy owner to "Priya S."
  And I save
Then the profile shows "Priya S." as the policy owner
```

### Scenario: A document nobody prepared can be filled in from scratch

```gherkin
Given I am viewing the Basel operational resilience principles
  And none of its profile fields has been filled in
When I expand its regulatory profile
Then every field reads "Not set"
  And I can see an Edit action
  And I am not told that the information is unavailable
```

### Scenario: Saved values survive leaving and returning

```gherkin
Given I have saved "FSA 2013" as the legal basis on the Basel operational resilience principles
When I close the document and open it again
Then its regulatory profile still shows "FSA 2013" as its legal basis
```

### Scenario: Abandoning an edit changes nothing

```gherkin
Given I am editing the RMiT policy document's regulatory profile
  And its policy owner is recorded as "Aisyah R."
When I change the policy owner to "Farid M."
  And I cancel instead of saving
Then the profile still shows "Aisyah R." as the policy owner
```

### Scenario: Clearing a field returns it to not set

```gherkin
Given the Operational Resilience working draft records "FSA 2013" as its legal basis
When I press Edit
  And I clear the legal basis
  And I save
Then the profile shows the legal basis as "Not set"
```

### Scenario: Recording several Acts at once

```gherkin
Given I am editing the RMiT policy document's regulatory profile
When I enter "FSA 2013, IFSA 2013, DFIA 2002" as its legal basis
  And I save
Then the profile shows three separate Acts
  And they read "FSA 2013", "IFSA 2013", and "DFIA 2002"
```

### Scenario: ISMP classification is chosen from the four, never typed

```gherkin
Given I am editing a document's regulatory profile
When I look at the ISMP classification field
Then I can choose between UMUM, TERHAD, SULIT and RAHSIA
  And I can leave it unset
  And I cannot type a classification of my own
```

### Scenario: A working draft's deliverable kind is shown but not editable

```gherkin
Given I am viewing the RMiT FAQ working draft's regulatory profile
  And it was created as an FAQ
When I press Edit
Then I can see "FAQ" recorded as its deliverable kind
  And I cannot change it
  And I can still edit every other field
```

### Scenario: A published context document has no deliverable kind on its profile

```gherkin
Given I am viewing the Financial Services Act 2013's regulatory profile
When I expand it
Then no deliverable kind is shown
  And the seven remaining fields are listed
  And I can edit them
```

### Scenario: ISMP classification keeps its honest pending wording

```gherkin
Given I am viewing the Operational Resilience working draft's regulatory profile
  And nobody has recorded an ISMP classification for it
When I expand the profile
Then the ISMP classification reads "Pending — RH publication form"
  And it is distinguishable from a field that simply has not been filled in
```

### Scenario: A save that cannot be completed loses nothing

```gherkin
Given I am editing the RMiT policy document's regulatory profile
  And I have entered "28 November 2025" as the effective date
When I save and the save cannot be completed
Then I can see that the profile could not be saved
  And my entered values are still in the form
  And I can try again
```

## Business Rules & Constraints

- **All seven fields are editable on every document**, in every workstream, regardless of how the document is classified.
- **A working draft's profile also shows its deliverable kind, read-only.** It is set once when the draft is created and cannot be changed. Published context documents show no deliverable kind at all.
- **Blank means "not set yet."** It does not mean the field is inapplicable, and there is no way for a drafter to say that it is.
- **ISMP classification continues to read "Pending — RH publication form"** when nothing has been recorded, because the tool genuinely has no source for it. A drafter may still record one.
- **Keywords and legal basis hold several values;** the other seven hold one. A drafter enters several by separating them with commas.
- **What a drafter types is her own account of the document, never a quotation from it.** No profile field is ever presented as a citation, and the tool's rule that every citation is quoted word-for-word with its clause number is untouched.
- **The empowerment framework holds a word-for-word clause quote by convention**, which the tool does not verify. An on-screen note saying so was built and then removed on 30 Jul 2026 as UI noise; the convention stands, unenforced and undocumented in the UI.
- **Saving is a deliberate action.** The card is read-only until Edit is pressed, so a stray keystroke cannot alter a recorded value, and an abandoned edit changes nothing.
- **A profile that was prepared ahead of time is edited the same way as one that was not.** There is no distinction in the interface between the two.

## Success Metrics

- Any document in any workstream can have its regulatory profile completed by the drafter, with no document showing an "information not available" dead end.
- Values a drafter saves are still there when she returns, and are available to later work that needs to read them.

## Dependencies

- **The deliverable kind must be recorded on working drafts** for the read-only line on their profiles to have anything to show. That is the first story in this epic; this story is otherwise independent of it and the two can be built in parallel.

## Open Questions

- [x] ~~Should the profile always be a form, or read-only until Edit is pressed?~~ — **Resolved:** read-only until Edit. Several fields hold word-for-word quotations from the document, and an always-live form makes it easy to alter one by accident.
- [x] ~~Should only working drafts be editable, or every document?~~ — **Resolved:** every document. The existing prepared profiles already cover context documents, such as a supervisory letter in the RMiT workstream, so restricting editing to working drafts would leave those uncorrectable.
- [x] ~~Should the tool check that the empowerment framework really is quoted from the document?~~ — **Resolved:** no. Verifying it would require the document to have been broken into passages first, which would block editing on documents that have not been, for a field the drafter is best placed to get right. An on-screen note was tried and removed as noise.
- [x] ~~Should the placeholder shape be dropped from the node-detail response now that every node is editable?~~ — **Resolved:** no, keep it. Four other consumers read the `{status, message}` union (the cross-workstream intelligence panel, the comparison view, and their tests), and collapsing it would churn all of them for no gain in this story. The panel decides what to render from `status`.
- [ ] Whether saving a profile should appear in the document's recent activity — **Deferred (non-blocking):** the existing activity trail is written inconsistently by the features that already add to it (`add_node` writes an `event` key, the panel renders a `kind` key), and widening it here would spread that inconsistency. Worth resolving on its own terms rather than as a side effect of this story.

---

## Functional Requirements

- **Write path:** a new `PUT /api/workstreams/{workstream_id}/nodes/{node_id}/metadata` persists the seven profile fields through the existing `engine/concepts.py::save_concepts`, which already writes `data/workstreams/{ws}/concepts/{node_id}.json` with the exact `CONCEPT_FIELDS` key set. No new storage module.
- **Full replacement, not a patch:** the route accepts the complete seven-field object and writes it whole. `save_concepts` already normalises to `{field: fields.get(field) for field in CONCEPT_FIELDS}`, so a field omitted by the client lands as `null`. The form always sends all seven, so this is exact rather than lossy.
- **Atomicity:** one `write_text` call per save, as `save_concepts` does today. A validation failure returns before any write, so a rejected save leaves the side-file untouched.
- **Idempotency:** naturally idempotent — the same payload written twice yields a byte-identical file and the same `200`.
- **`task_type` is not writable here.** It lives on the node, is permanent, and the route rejects it (`400 TASK_TYPE_IMMUTABLE`) rather than ignoring it. The node-detail response is where the panel reads it for display.
- **Absence is not an error.** A node with no side-file yet returns the existing placeholder from `GET`, and the first `PUT` creates the file — `save_concepts` already does `mkdir(parents=True, exist_ok=True)`.
- **No axis-cache interaction.** The seven-field profile (`concepts/`) and the extracted axis pills (`axes/`) are separate stores that happen to share a screen section name. This route touches only the former; `POST .../extract-concepts` is unaffected.

### Validation & Business Rules

- Body must be a JSON object → else `400 INVALID_METADATA "Metadata must be an object."`
- Unknown keys are rejected → `400 UNKNOWN_METADATA_FIELD` naming the first offender, e.g. `"'policy_owner_name' is not a metadata field."` Silently dropping a typo'd key would lose a drafter's edit without telling them.
- `task_type` in the body → `400 TASK_TYPE_IMMUTABLE "A deliverable kind is set when the document is created and cannot be changed."`
- `legal_basis` accepts a list of strings, a bare string, or `null`. A bare string is stored as-is (older side-files carry scalars and `asList` in the panel already tolerates both). Any non-string list member → `400 INVALID_METADATA`.
- The other seven accept a string or `null`. A non-string → `400 INVALID_METADATA` naming the field.
- Empty string, whitespace-only string, and empty list all normalise to `null` before writing, so "cleared" and "never set" are one state on disk — which is what "blank means not set yet" requires.
- Per-field max length **2000 characters** for the scalar fields. The empowerment framework holds a full clause quote, so 2000 is generous rather than tight.
- `legal_basis` bounds the **number** of values (at most **50**), never their length — in either the list or the bare-string form. A statutory citation can legitimately run long ("Financial Services Act 2013, section 143(2), read together with…"), and truncating one corrupts a reference rather than tidying it.
- Over either bound → `413 METADATA_TOO_LARGE` naming the field.
- No HTML sanitisation is needed: every value is rendered as text (`{value}` in JSX), never as markup. Unlike the draft route, nothing here reaches `dangerouslySetInnerHTML`.

## Permissions & Security

- **Scope:** internal demo API, unauthenticated like every other route in this service.
- **Authorization:** none. Any caller who can reach the service can edit any node's profile — consistent with the rest of the app and acceptable for a hackathon prototype. Worth stating plainly rather than implying a control that does not exist.
- **Path safety:** `concepts_path` interpolates `workstream_id` and `node_id` into a filesystem path. Both must be resolved against the loaded graph **before** any write — the route returns `404 WORKSTREAM_NOT_FOUND` / `404 NODE_NOT_FOUND` for anything not present in `graph.json`, which is what stops a `../` traversal reaching the write. This mirrors how `delete_workstream_node` and `extract_node_concepts` already guard.
- **Input validation:** closed key set, per-field type checks, length caps as above.

## API Design

### `PUT /api/workstreams/{workstream_id}/nodes/{node_id}/metadata`

**Request:**

```json
{
  "policy_owner": "Aisyah R.",
  "applicability": "Licensed banks and licensed investment banks.",
  "empowerment_framework": "This policy document is issued pursuant to section 143(2) of the Financial Services Act 2013.",
  "issuance_date": "2025-11-28",
  "effective_date": "2025-11-28",
  "legal_basis": ["FSA 2013", "IFSA 2013"],
  "ismp_classification": null
}
```

**Response (200)** — the saved profile, in the `GET`'s `metadata` shape so the client can drop it straight into its cache:

```json
{
  "node_id": "rmit-pd-v2",
  "metadata": {
    "status": "available",
    "policy_owner": "Aisyah R.",
    "applicability": "Licensed banks and licensed investment banks.",
    "empowerment_framework": "This policy document is issued pursuant to section 143(2) of the Financial Services Act 2013.",
      "issuance_date": "2025-11-28",
    "effective_date": "2025-11-28",
      "legal_basis": ["FSA 2013", "IFSA 2013"],
    "ismp_classification": null
  }
}
```

**Errors:**

| Status | Code                     | Condition                                                                 |
| ------ | ------------------------ | ------------------------------------------------------------------------- |
| 400    | `INVALID_METADATA`       | Body is not an object, or a field has the wrong type                      |
| 400    | `UNKNOWN_METADATA_FIELD` | A key outside the seven profile fields                                     |
| 400    | `TASK_TYPE_IMMUTABLE`    | `task_type` present in the body                                           |
| 404    | `WORKSTREAM_NOT_FOUND`   | No such workstream                                                        |
| 404    | `NODE_NOT_FOUND`         | No such node in that workstream                                           |
| 413    | `METADATA_TOO_LARGE`     | A scalar field exceeds 2000 chars, or `legal_basis` exceeds 50 members    |

Errors carry `field` where one field is at fault, matching `_ws_error`'s existing optional `field` argument so the form can ring the offending input.

### `GET /api/workstreams/{workstream_id}/nodes/{node_id}` — unchanged

Still returns `metadata` as either `{"status": "available", ...seven fields}` or `{"status": "placeholder", "message": "Concept extraction not enabled in MVP1"}`. The panel keys off `status`; the placeholder message is no longer shown to the drafter, but the shape stays for the four other consumers.

## Data Model & Migrations

No database. The store is `data/workstreams/{ws}/concepts/{node_id}.json`, already written by `scripts/enrich_node_metadata.py` and read by `engine/concepts.py::load_concepts`.

**File shape** — unchanged, exactly `CONCEPT_FIELDS`:

| Field                   | Type                       | Constraints        | Description                            |
| ----------------------- | -------------------------- | ------------------ | -------------------------------------- |
| `policy_owner`          | string \| null             | ≤ 2000 chars       | Who owns the document                  |
| `applicability`         | string \| null             | ≤ 2000 chars       | Who it applies to                      |
| `empowerment_framework` | string \| null             | ≤ 2000 chars       | Verbatim statutory-basis clause        |
| `issuance_date`         | string \| null             | ≤ 2000 chars       | Free text — no date parsing (see note) |
| `effective_date`        | string \| null             | ≤ 2000 chars       | Free text                              |
| `legal_basis`           | string[] \| string \| null | ≤ 50 members, each uncapped | Acts, rendered as chips       |
| `ismp_classification`   | string \| null             | One of UMUM / TERHAD / SULIT / RAHSIA | `null` renders as the pending state |

**Dates are stored as free text, not validated or normalised.** The committed fixtures leave them `null`, and the drafter's own phrasing ("28 November 2025", "2025-11-28") is what the field is for. Imposing a format would reject valid input for a display-only value; the panel renders whatever string is stored.

### Migration Notes

- No backfill. Existing side-files (`opres-v2/concepts/opres-pd-v0-3.json`, `open-finance-ed/concepts/of-ed-2025.json`, `rmit-v2-2025/concepts/{rmit-pd-v2,bnm-supervisory-letter-rmit-2025}.json`) already match the schema and load unchanged.
- A side-file written before `legal_basis` / `ismp_classification` existed still loads — `load_concepts` returns the raw dict and missing keys read back as `None`. The first save through this route normalises it to all seven keys.

## UI/Frontend Requirements

### Components

**`NodeMetadataForm`** — `frontend/src/features/workstream-graph/NodeMetadataForm.tsx`

- **Type:** New
- **Purpose:** the edit mode of the Metadata disclosure — seven controlled inputs, Save and Cancel. Extracted rather than inlined because `NodeDetailPanel.tsx` is already ~500 lines carrying the header, five sections, the delete flow, and the footer actions; adding a seven-field form inline would make it the largest file in the feature.
- **Props:**
  ```typescript
  interface NodeMetadataFormProps {
    workstreamId: string;
    nodeId: string;
    /** Current values, or null when the node has no profile yet. */
    initial: ConceptsAvailable | null;
    onDone: () => void;
  }
  ```
- **Fields:** five single-line `<input>`s; `empowerment_framework` as `<textarea rows={3}>` (it holds a clause-length quote); `legal_basis` as a single-line input taking comma-separated values, split on `,` and trimmed on submit, joined with `", "` on load; `ismp_classification` as a `<select>` offering a blank "Not set" option plus UMUM / TERHAD / SULIT / RAHSIA.
- **Labels:** reuse `CONCEPT_FIELD_ORDER`'s existing label strings so read and edit modes cannot drift. Move that constant into the new file and import it back into the panel, or into a shared `metadata.ts` — either is fine, but it must exist once.
- **Mutation:** TanStack `useMutation` calling `saveNodeMetadata`; on success invalidate `["node", workstreamId, nodeId]` and call `onDone()`.
- **Error state:** `role="alert"` paragraph with copy keyed off the error code; the form stays mounted with the drafter's values intact so they can retry.

**`NodeDetailPanel`** — `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`

- **Type:** Modify existing
- **Purpose:** add `metadataEditing` state; render `NodeMetadataForm` in place of the `<dl>` when editing.
- **Read mode changes:** when `metadata.status !== "available"`, render the seven labels each reading "Not set" instead of the placeholder message — the "no dead end" requirement. `ismp_classification` keeps its `ISMP_PENDING` treatment in both cases.
- **Edit affordance:** a small "Edit" button in the disclosure header row, beside the chevron. Do not nest it inside the existing disclosure `<button>` — a button inside a button is invalid and breaks keyboard activation. Make the header a flex row containing the disclosure toggle and the Edit button as siblings.
- **`task_type` line:** for a task node, the first row of the read-mode list, labelled "Task type", showing the human label. Rendered in edit mode too, as static text, never an input.

### API client

**`saveNodeMetadata`** — `frontend/src/lib/api.ts`

```typescript
export function saveNodeMetadata(
  workstreamId: string,
  nodeId: string,
  body: NodeMetadataRequest,
): Promise<NodeMetadataResponse>;
```

Add a `putJson` helper alongside the existing `postJson` if none exists, following the same `throwHttpError` path so `HttpError.code` / `.field` reach the form.

### User Interactions

- Expand Metadata → seven labelled values, or six "Not set" rows plus the pending ISMP row; an Edit button either way.
- Press Edit → the list becomes a form pre-filled with current values; Save and Cancel appear.
- Press Save → the form disables while saving, then closes back to read mode showing the new values.
- Press Cancel → the form closes, discarding everything typed; stored values are unchanged.
- Save fails → an inline message appears, the form stays open, values are preserved.

### States

- **Loading:** the panel's existing "Loading node…" spinner covers initial load. While saving, the Save button shows "Saving…" and both buttons disable.
- **Empty:** six rows reading "Not set", with `ismp_classification` reading "Pending — RH publication form".
- **Error:** inline `role="alert"` text under the form; nothing is lost.

## Architecture Notes

- **New dependencies:** none. No date picker, no form library — plain controlled inputs, consistent with `AddNodeDialog` and `NewWorkstreamPage`.
- **Dependencies & integration:** `concepts/{node_id}.json` is read by `GET /nodes/{id}` and by both cross-links routes (`GET /api/cross-links/{edge_id}`, `GET /api/workstreams/{id}/cross-links`), which project it as `CrossProfile.concepts`. Editing a profile therefore changes what the Cross-Workstream Intelligence panel and the comparison view show — intended, and the reason `RegulatoryProfileCard` needs no change to benefit.
- **No breaking changes.** The `GET` contract is untouched; the new route is additive.
- **Cache invalidation:** invalidating `["node", workstreamId, nodeId]` refreshes the panel. The cross-links queries are not invalidated — they are a different screen, and TanStack refetches them on next mount. Chasing that would mean invalidating queries this component knows nothing about.

## Exemplar Files

- `engine/api.py::put_draft` — the write-route shape this one follows: load graph → 404 guards → parse body → typed validation → delegate to a persistence module → map its exceptions to `_ws_error` codes.
- `engine/concepts.py` — `save_concepts` already exists and already writes UTF-8 with the normalised key set; this story calls it rather than reimplementing it.
- `engine/api.py::extract_node_concepts` — the node-resolution guard pair (`WORKSTREAM_NOT_FOUND` then `NODE_NOT_FOUND`) to copy verbatim.
- `frontend/src/features/workstream-graph/AddEdgeDialog.tsx` — a small controlled form with a TanStack mutation, `HttpError` code mapping, and query invalidation: the closest pattern to `NodeMetadataForm`.
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx` — the existing `<dl>` read mode, `CONCEPT_FIELD_ORDER`, `CHIP_FIELDS`, `asList`, and `ISMP_PENDING`, all reused.

## Implementation Plan

### Sub-tasks

**Task 1: metadata validation helper in the engine** — _small_

- Files: `engine/concepts.py` (add `validate_metadata(body) -> Optional[tuple[int, str, str, Optional[str]]]` returning `(status, code, message, field)`, plus a `normalise(body)` that trims strings, splits nothing, and maps empty → `None`)
- INDEPENDENT

**Task 2: the PUT route** — _small_

- Files: `engine/api.py` (new route beside the existing `extract-concepts` and node-detail routes)
- SEQUENTIAL (depends on Task 1)

**Task 3: engine tests for the route** — _medium_

- Files: `engine/tests/test_api_node_metadata.py` (extend — it already covers the read side)
- SEQUENTIAL (depends on Task 2)

**Task 4: API client + types** — _small_

- Files: `frontend/src/lib/types.ts` (`NodeMetadataRequest`, `NodeMetadataResponse`), `frontend/src/lib/api.ts` (`saveNodeMetadata`, `putJson` if absent)
- SEQUENTIAL (depends on Task 2 for the contract)

**Task 5: `NodeMetadataForm`** — _medium_

- Files: `frontend/src/features/workstream-graph/NodeMetadataForm.tsx` (new)
- SEQUENTIAL (depends on Task 4)

**Task 6: wire the panel — edit toggle, "Not set" read mode, `task_type` row** — _medium_

- Files: `frontend/src/features/workstream-graph/NodeDetailPanel.tsx`
- SEQUENTIAL (depends on Task 5)

**Task 7: frontend tests + MSW handler for the PUT** — _medium_

- Files: `frontend/src/test/msw/handlers.ts`, `frontend/src/features/workstream-graph/NodeMetadataForm.test.tsx` (new), `frontend/src/features/workstream-graph/NodeDetailPanel.test.tsx`
- SEQUENTIAL (depends on Task 6)

**Task 8: E2E for the edit-and-persist flow** — _small_

- Files: `frontend/e2e/edit-node-metadata.spec.ts`
- SEQUENTIAL (depends on Task 6)

### Negative Constraints

- Do NOT re-add `keywords` or `requirement` to `CONCEPT_FIELDS`, and do NOT let `task_type` join it. Seven fields, same names, same order.
- Do NOT modify `scripts/enrich_node_metadata.py`. The offline path keeps working against the same side-file, unchanged.
- Do NOT remove the `{status, message}` placeholder branch from the node-detail response — `CompareWorkstreamsPage.tsx`, `RegulatoryProfileCard.tsx`, and their tests read that union.
- Do NOT touch the axis-extraction route, the `axes/` cache, or `engine/arm_g.py`. "Concepts" the pills and "Metadata" the profile are different stores.
- Do NOT add date parsing, a date picker, or format normalisation to the two date fields.
- Do NOT introduce react-hook-form or zod.
- Do NOT add a `recent_activity` entry on save (deferred above, deliberately).
- Do NOT rebuild `data/artifacts/` — this story never touches the clause index (see `docs/learnings/blocker-engine-build-silently-narrows-artifacts.md`).

## Test Scenarios

**Test 1: a first save creates the side-file**

- Setup: `open-finance-pd-2026` fixture in `tmp_path`; no `concepts/bis-papers-168.json`
- Action: `PUT .../nodes/bis-papers-168/metadata` with `{"policy_owner": "Priya S.", "legal_basis": ["FSA 2013"], ...five nulls}`
- Expected: `200`; `metadata.status == "available"`; the file now exists with all seven keys, five of them `null`

**Test 2: a save overwrites an existing profile whole**

- Setup: `rmit-v2-2025` fixture, whose `rmit-pd-v2` profile is populated
- Action: `PUT .../nodes/rmit-pd-v2/metadata` with only `{"policy_owner": "Farid M."}` and the other eight omitted
- Expected: `200`; `policy_owner == "Farid M."`; every other field now `null` (full replacement, not a patch)

**Test 3: values round-trip through GET**

- Setup: Test 1's state
- Action: `PUT` then `GET .../nodes/bis-papers-168`
- Expected: `GET` body `metadata.legal_basis == ["FSA 2013"]`

**Test 4: an unknown key is refused**

- Setup: `open-finance-pd-2026` fixture
- Action: `PUT` with `{"policy_owner_name": "Aisyah R."}`
- Expected: `400 UNKNOWN_METADATA_FIELD`, field `policy_owner_name`; no file written

**Test 5: `task_type` in the body is refused**

- Setup: same
- Action: `PUT` with `{"task_type": "FAQ", "policy_owner": "Aisyah R."}`
- Expected: `400 TASK_TYPE_IMMUTABLE`, field `task_type`; no file written

**Test 6: a wrong-typed field is refused**

- Setup: same
- Action: `PUT` with `{"policy_owner": 42}`
- Expected: `400 INVALID_METADATA`, field `policy_owner`

**Test 7: a non-string list member is refused**

- Setup: same
- Action: `PUT` with `{"legal_basis": ["FSA 2013", 7]}`
- Expected: `400 INVALID_METADATA`, field `legal_basis`

**Test 8: blank input normalises to null**

- Setup: same
- Action: `PUT` with `{"policy_owner": "   ", "legal_basis": []}`
- Expected: `200`; both stored as `null`

**Test 9: an over-long field is refused**

- Setup: same
- Action: `PUT` with `{"applicability": "x" * 2001}`
- Expected: `413 METADATA_TOO_LARGE`, field `applicability`; no file written

**Test 10: too many list members refused, but a long one is not**

- Setup: same
- Action: `PUT` with 51 legal-basis members
- Expected: `413 METADATA_TOO_LARGE`, field `legal_basis`
- Action: `PUT` with a single 3000-character statutory citation, as a list member and again as a bare string
- Expected: `200` both times — `legal_basis` caps the count, never the length

**Test 11: unknown workstream and unknown node**

- Setup: `tmp_path` with the fixture
- Action: `PUT /api/workstreams/nope/nodes/x/metadata`, then `PUT .../open-finance-pd-2026/nodes/nope/metadata`
- Expected: `404 WORKSTREAM_NOT_FOUND`, then `404 NODE_NOT_FOUND`; nothing written in either case

**Test 12: a traversal-shaped node id is refused before any write**

- Setup: same
- Action: `PUT .../open-finance-pd-2026/nodes/..%2F..%2Fescape/metadata` with a valid body
- Expected: `404 NODE_NOT_FOUND`; no file created anywhere under `tmp_path`

**Test 13: repeated identical saves are idempotent**

- Setup: same
- Action: the same `PUT` body twice
- Expected: both `200`; file content byte-identical after each

**Test 14: a legacy side-file missing the newer keys is upgraded on save**

- Setup: write a `concepts/{node}.json` holding only the original seven fields
- Action: `GET` (confirm it loads), then `PUT` the seven-field form payload
- Expected: `GET` succeeds with `legal_basis`/`ismp_classification` reading `None`; after `PUT` the file holds all seven keys

## Acceptance Criteria

- [ ] `PUT .../nodes/{id}/metadata` persists all nine fields and returns the saved profile
- [ ] Unknown keys, wrong types, over-long values, and `task_type` are each refused with the documented code and `field`
- [ ] Unknown workstream / node return 404 before any filesystem write
- [ ] A node with no profile shows nine "Not set" rows and an Edit button — no "not enabled in MVP1" text reaches the drafter
- [ ] Cancel discards; a failed save preserves the drafter's input
- [ ] A task node shows its deliverable kind in the profile, and it cannot be edited
- [ ] `scripts/enrich_node_metadata.py` still runs and its output still loads
- [ ] `pytest engine/tests` green; `npm run test` green in `frontend/`
- [ ] `mypy engine/` shows no new warnings beyond the accepted baseline
- [ ] No type errors or lint warnings

## Verification

Run the verifier skill. Build in the main working tree (`.venv` and `frontend/node_modules` live only there).

### Backend API Tests

| File                                     | Covers                                                            |
| ---------------------------------------- | ----------------------------------------------------------------- |
| `engine/tests/test_api_node_metadata.py` | Tests 1–14 — extends the existing read-side coverage in this file |

Run: `.venv/bin/python -m pytest engine/tests/test_api_node_metadata.py` then the full `engine/tests`.

### Browser/UI Testing

Start the engine and the app (unauthenticated), then:

1. Open `/workstreams/open-finance-pd-2026` and click the **BIS Papers 168** node.
2. Expand **Metadata**. **Expect:** nine rows each reading "Not set", ISMP reading "Pending — RH publication form", and an **Edit** button. No text about MVP1.
3. Press **Edit**. **Expect:** seven inputs, empty, with ISMP classification as a dropdown; Save and Cancel.
4. Type "Priya S." as policy owner, "FSA 2013, IFSA 2013" as legal basis, and pick SULIT as the ISMP classification. Press **Save**. **Expect:** read mode returns showing Priya S., two Act chips, and SULIT.
5. Close the panel, reselect the node, expand Metadata. **Expect:** both values are still there.
6. Press **Edit**, change policy owner to "Farid M.", press **Cancel**. **Expect:** still Priya S.
7. Click the workstream's working draft and expand Metadata. **Expect:** a "Task type" row reading "PD — Policy Document"; pressing Edit leaves it as text with no input.
8. Stop the engine, press Edit on any node, change a field, press Save. **Expect:** an inline error, the form still open, your typing intact. Restart the engine and Save again — it succeeds.

### E2E Tests

| Key Scenario                                             | Test file                                 | Assigned sub-task |
| -------------------------------------------------------- | ----------------------------------------- | ----------------- |
| Filling in a field that was not set                      | `frontend/e2e/edit-node-metadata.spec.ts` | Task 8            |
| Saved values survive leaving and returning               | `frontend/e2e/edit-node-metadata.spec.ts` | Task 8            |
| A document nobody prepared can be filled in from scratch | `frontend/e2e/edit-node-metadata.spec.ts` | Task 8            |

These three need a real round-trip to the filesystem to mean anything — persistence is the claim. The remaining scenarios (cancel, clearing a field, several Acts, the ISMP dropdown's four options, the read-only task-type row, the ISMP pending wording, and the failed save) are Vitest + MSW in `NodeMetadataForm.test.tsx` and `NodeDetailPanel.test.tsx`; the validation-rejection scenarios are engine Tests 4–10.

**Locator strategies:** `getByRole("button", { name: /^edit$/i })` for the edit toggle; `getByLabel(<field label>)` for each input, reusing the `CONCEPT_FIELD_ORDER` labels; `getByRole("button", { name: /^save$/i })` and `/^cancel$/i`; `getByTestId("task-type-chip")` for the read-only kind.

**Match chip text exactly.** `legal_basis` renders its values as sibling `<span>` chips inside one `<dd>`, so a non-exact `getByText("FSA 2013")` resolves to the containing `<dd>` — which holds every Act and reads as not visible. Scope to the profile list and pass `{ exact: true }`. Found the hard way; the assertion failed while the data was correct on disk.

**Node selection:** the graph renders to a single `<canvas>`, so there is no per-node DOM element in a real browser — this spec shares the `openNode` canvas-sweep helper described in [spec-shared-task-type.md](spec-shared-task-type.md)'s Verification section.

**Fixture hygiene:** the spec writes `data/workstreams/open-finance-pd-2026/concepts/bis-papers-168.json`, a tracked path. Note in a comment that `git checkout data/workstreams/open-finance-pd-2026` (and deleting that untracked file) restores the tree, following `add-node-chunking.spec.ts`'s precedent.
