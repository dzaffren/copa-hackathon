# Create New Workstream

**Ticket:** TBD

**Epic:** [Workstream Brain MVP1 — Overview](spec.md)

A short, three-card form that lets a policymaker spin up a new workstream (one Discussion Paper, Exposure Draft, or Policy Document under active drafting) in under a minute. On submission, the user lands on the new workstream's empty graph, ready to add its first anchor. Reached from the collapsible sidebar's **+ New workstream** action on any screen.

## User Story

As Aisyah R., I want to spin up a new workstream in under a minute, so that when the DG announces one on Monday morning I can start adding anchors that afternoon.

## Background & Context

**Current state:**

- The collapsible sidebar (shared across every screen in the tool) lists every workstream Aisyah is added to, plus a **+ New workstream** action and an Institution map link at the bottom.
- Today, when a new drafting cycle is announced, there is no lightweight home for it — the drafter has no place to start collecting anchors and nominating reviewers before drafting begins.
- An earlier form scaffold used labels like "prior version", "anchor", "benchmark", and "constraint" that no longer map to the tool's current node and edge model. Those labels are being removed from this screen.

**Problem:**

- The moment between "the Chair announces a workstream" and "the drafter has a place to start collecting anchors" is friction: notes get scattered across email, chat, and personal folders.
- Without an owner and a reviewer set on record from day one, cross-team coordination on the workstream cannot begin.
- Legacy scaffolding fields on the old form confused new users and produced data the rest of the tool could not consume.

## Target User & Persona

- **Who:** A senior policymaker in the Prudential Policy Department who owns and drafts BNM policy documents. Aisyah R. is the canonical example.
- **Context:** A new workstream is announced (for example, the Deputy Governor asks for a Climate Risk PD by Q4 2026). Aisyah opens the tool, clicks **+ New workstream** in the sidebar, and wants to be inside the new workstream's graph within a minute.
- **Current workaround:** Ad-hoc note in a personal folder or an email thread; no shared home until drafting starts weeks later.

## Goals

- Let a policymaker create a new workstream in under a minute with only the two fields that are strictly required.
- Capture, on day one, who owns the workstream, who reviews it, and who is allowed to open its nodes.
- Send the user straight from the form onto the new workstream's empty graph so the very next click can be "add the first anchor".

## Non-Goals

- No workflow for approving, archiving, or deleting a workstream after creation.
- No fields for prior version, anchor, benchmark, or constraint. These legacy labels are explicitly excluded; the current model uses seven node types plus four structural edge types, which are declared later on the workstream graph, not on this form.
- No integration with a live staff directory in this milestone. Reviewer search draws from a small static list of colleagues.
- No node creation on this screen. The new workstream lands on an empty graph; the first node is added there.

## User Workflow

1. **Open the form** — Aisyah clicks **+ New workstream** in the sidebar from any screen. The form opens with a breadcrumb reading "← Workstreams / New", a heading "Create new workstream", and a one-line intent explaining that a workstream is one Discussion Paper, Exposure Draft, or Policy Document under active drafting.
2. **Fill in the Basics** — She types a workstream name (for example, "Climate Risk PD v2 · 2026"), an optional one-line description, chooses a deliverable type from a short dropdown (Policy Document, Exposure Draft, Discussion Paper, or Other), and optionally types a target publication quarter (for example, "Q4 2026").
3. **Confirm People** — She sees her own name and initials pre-filled as the owner, marked "(you)", and cannot change it on this form. She searches for reviewers by name; each colleague she selects appears as a small pill she can remove with a close control.
4. **Choose Access** — She picks either "Team-only" (only the owner and reviewers can open nodes) or "Department-wide" (any Prudential Policy Department colleague can open nodes). Team-only is selected by default.
5. **Submit or cancel** — She clicks **Create workstream** to submit, or **Cancel** to return to the previous graph without saving. On successful submission she lands on the new workstream's empty graph, and the workstream appears in the sidebar's workstream list.

## Acceptance Criteria

### Scenario: Landing on the form from the sidebar

```gherkin
Given Aisyah R. is signed in and viewing any screen in the tool
When she clicks "+ New workstream" in the sidebar
Then she sees a breadcrumb reading "← Workstreams / New"
  And she sees a heading "Create new workstream"
  And she sees a one-line intent describing what a workstream is
  And she sees three cards titled "Basics", "People", and "Access"
  And the Owner field in the People card is pre-filled with "Aisyah R. (you)"
  And the Access card has "Team-only" selected by default
```

### Scenario: Creating a workstream with all fields filled in

```gherkin
Given Aisyah R. is on the "Create new workstream" form
  And the reviewer picker offers "Farid M." and "Priya S." among the selectable colleagues
When she fills in the following in the Basics card
  | Field               | Value                                                              |
  | Workstream name     | Climate Risk PD v2 · 2026                                          |
  | Short description   | Response to BCBS climate principles 2022 — draft PD targeting Q4 2026. |
  | Deliverable type    | Policy Document (PD)                                               |
  | Target publication  | Q4 2026                                                            |
  And she adds "Farid M." and "Priya S." as reviewers in the People card
  And she leaves the Access card set to "Team-only"
  And she clicks "Create workstream"
Then she lands on the new workstream's graph
  And the graph has no nodes and no edges
  And the sidebar lists "Climate Risk PD v2 · 2026" as one of her workstreams
  And the new workstream shows Aisyah R. as owner
  And the new workstream shows Farid M. and Priya S. as reviewers
  And the new workstream's access is "Team-only"
```

### Scenario: Creating a workstream with only the required fields

```gherkin
Given Aisyah R. is on the "Create new workstream" form
When she types "Cyber Risk DP · 2027" into the Workstream name field
  And she leaves the description and target publication fields empty
  And she leaves the deliverable type at its default "Policy Document (PD)"
  And she adds no reviewers
  And she clicks "Create workstream"
Then she lands on the new workstream's graph
  And the graph has no nodes and no edges
  And the sidebar lists "Cyber Risk DP · 2027" as one of her workstreams
  And the new workstream shows Aisyah R. as owner
  And the new workstream shows no reviewers
  And the new workstream's access is "Team-only"
```

### Scenario Outline: Blocked submissions when a required field is missing

```gherkin
Given Aisyah R. is on the "Create new workstream" form
When she leaves the <missing field> empty
  And she clicks "Create workstream"
Then the form does not submit
  And the <missing field> is flagged as needing attention
  And no new workstream is added to the sidebar

Examples:
  | missing field    |
  | Workstream name  |
  | Deliverable type |
```

### Scenario: Adding and removing reviewers before submitting

```gherkin
Given Aisyah R. is on the "Create new workstream" form
  And she has added "Farid M." and "Priya S." as reviewers
When she clicks the close control on the "Farid M." reviewer pill
Then "Farid M." no longer appears in the reviewer list
  And "Priya S." still appears in the reviewer list
```

### Scenario: Cancelling the form

```gherkin
Given Aisyah R. is on the "Create new workstream" form
  And she has typed "Draft workstream" into the Workstream name field
When she clicks "Cancel"
Then she returns to the workstream graph she came from
  And no new workstream is added to the sidebar
  And nothing she typed is retained
```

### Scenario: Owner cannot be changed on this form

```gherkin
Given Aisyah R. is on the "Create new workstream" form
When she looks at the Owner field in the People card
Then the Owner field shows "Aisyah R. (you)"
  And the Owner field cannot be edited from this form
```

### Scenario: Access options are mutually exclusive with Team-only as default

```gherkin
Given Aisyah R. is on the "Create new workstream" form
When she looks at the Access card
Then "Team-only" is selected
  And "Department-wide" is not selected
  And each option has a short explainer describing who can open nodes
When she selects "Department-wide"
Then "Department-wide" is selected
  And "Team-only" is no longer selected
```

### Scenario: Legacy scaffolding labels are not shown

```gherkin
Given Aisyah R. is on the "Create new workstream" form
When she reviews every field, label, dropdown option, and helper text on the form
Then she does not see any field or label named "prior version"
  And she does not see any field or label named "anchor"
  And she does not see any field or label named "benchmark"
  And she does not see any field or label named "constraint"
```

### Scenario: Sidebar highlights the New workstream action while the form is open

```gherkin
Given Aisyah R. is on the "Create new workstream" form
When she looks at the sidebar
Then the "+ New workstream" item is highlighted as the active screen
  And the sidebar still lists every workstream she is added to
  And the sidebar still shows an "Institution map" link at the bottom
```

### Scenario: New workstream is immediately usable after creation

```gherkin
Given Aisyah R. has just created the workstream "Climate Risk PD v2 · 2026"
  And she has landed on its empty graph
When she looks at the graph
Then she sees no nodes and no edges
  And an "+ Add node" action is available as the natural next step
```

## Business Rules & Constraints

- **Every workstream has exactly one owner.** The owner is the creator of the workstream. The owner cannot be changed on this form.
- **Reviewers are optional.** A workstream can be created with zero reviewers and can have reviewers added later.
- **Only two fields are required at creation:** Workstream name and Deliverable type. Deliverable type has a default value of "Policy Document (PD)" so a user can create a workstream by supplying the name alone. Description, target publication, reviewers, and access can all be filled in later.
- **Team-only is the default access setting.** Under Team-only, only the owner and named reviewers can open the workstream's nodes. Under Department-wide, any colleague in the Prudential Policy Department can open the workstream's nodes.
- **The new workstream lands on an empty graph.** No nodes, no edges. The first node is added on the workstream graph, not on this form.
- **Legacy labels are forbidden.** The labels "prior version", "anchor", "benchmark", and "constraint" from an earlier scaffold must not appear anywhere on this form. Node types and edge types are declared later on the workstream graph, using the current seven node types and four structural edge types.
- **Deliverable type choices are fixed** at "Policy Document (PD)", "Exposure Draft (ED)", "Discussion Paper (DP)", and "Other".
- **Sidebar reflects the new workstream immediately** after successful creation.

## Success Metrics

- A policymaker who has used the tool once can create a new workstream from an announcement in under 60 seconds.
- Zero new workstreams are created without an owner or a deliverable type on record.
- No user support requests reference the legacy "prior version / anchor / benchmark / constraint" labels after this form ships.

## Dependencies

- **Workstream graph story.** The user is routed onto the new workstream's empty graph after submission; the graph screen must accept an empty state.
- **Shared collapsible sidebar.** The **+ New workstream** action, the workstream list, and the Institution map link all live in the sidebar shared with every other screen in this epic.
- **Persona set.** Reviewer search draws from the tool's known colleague list, which includes Farid M. and Priya S. among a small number of seeded colleagues for this milestone.

## Open Questions

- [x] ~~Should the owner be editable on this form?~~ — **Resolved:** No. The creator is always the owner on this form. Ownership transfer is a separate flow, out of scope for this milestone.
- [x] ~~Should reviewer search be backed by a live staff directory?~~ — **Resolved:** No, not in this milestone. A small static list of colleagues (including Farid M. and Priya S.) is sufficient for the demo.
- [ ] Whether the target publication field should be a free text input or a structured quarter picker — **Deferred (non-blocking):** free text input is acceptable for this milestone; a structured picker can be introduced later without changing the rest of the form.

---

## Functional Requirements

- Route: `/workstreams/new` in the frontend React Router v6 tree.
- Form validation runs client-side with a zod schema wired into `react-hook-form` via `@hookform/resolvers/zod`:
  - `name` — required, minimum 3 characters, maximum 120 characters.
  - `deliverable_type` — required, one of `PD | ED | DP | Other`. Defaults to `PD`.
  - `description` — optional, maximum 500 characters.
  - `target_publication` — optional, maximum 60 characters (free text, e.g. "Q4 2026", "H1 2027", "By end 2026").
  - `reviewer_ids` — optional list, zero or more entries drawn from the static reviewer directory.
  - `access` — required, one of `team_only | department_wide`. Defaults to `team_only`.
- Owner is derived server-side from the authenticated user. In MVP1 this is hard-coded to Aisyah R. (`{"id": "ar", "name": "Aisyah R."}`). Any `owner` field submitted in the request body is ignored.
- `workstream_id` is a URL-safe kebab-case slug derived from the name. Non-ASCII characters and diacritics are stripped or transliterated; separators and punctuation collapse to single hyphens; leading/trailing hyphens are trimmed. Examples:
  - "Climate Risk PD v2 · 2026" -> `climate-risk-pd-v2-2026`
  - "Cyber Risk DP · 2027" -> `cyber-risk-dp-2027`
  - "RMiT v2 — Technology Risk" -> `rmit-v2-technology-risk`
- Slug collision policy: if `climate-risk-pd-v2-2026` already exists, append `-2`, then `-3`, and so on until a free slot is found. If no free slot is found after 10 attempts, return `WORKSTREAM_SLUG_COLLISION`.
- After a successful create, the frontend uses `useNavigate` to redirect to `/workstreams/{workstream_id}` — the workstream graph screen showing an empty graph.
- Reviewer picker is populated from `GET /api/reviewers`, which returns the static list defined in `engine/directory.py`. No real staff directory integration in MVP1.
- The Owner block is a read-only shadcn `Avatar` + name + "(you)" tag; there is no input to edit it.

## Permissions & Security

- Internal tool, no authentication in MVP1. Owner is hard-coded server-side to `ar` (Aisyah R.).
- Server-side validation duplicates all client-side zod rules. The server does not trust the client to enforce constraints.
- All free-text inputs (`name`, `description`, `target_publication`) are HTML-stripped and control-character-stripped before persisting.
- `reviewer_ids` are validated against `engine/directory.py::REVIEWERS`. Any id not in the directory returns `INVALID_REVIEWER_ID` and the workstream is not created.
- `data/workstreams/` is a local JSON store, not committed to git (`data/` should be added to `.gitignore` if not already).

## API Design (extend `engine/api.py`)

### `POST /api/workstreams`

Request body:

```json
{
  "name": "Climate Risk PD v2 · 2026",
  "description": "Response to BCBS climate principles 2022 — draft PD targeting Q4 2026.",
  "deliverable_type": "PD",
  "target_publication": "Q4 2026",
  "reviewer_ids": ["fm", "ps"],
  "access": "team_only"
}
```

Response `201 Created`:

```json
{
  "id": "climate-risk-pd-v2-2026",
  "name": "Climate Risk PD v2 · 2026",
  "description": "Response to BCBS climate principles 2022 — draft PD targeting Q4 2026.",
  "deliverable_type": "PD",
  "target_publication": "Q4 2026",
  "owner": { "id": "ar", "name": "Aisyah R." },
  "reviewers": [
    { "id": "fm", "name": "Farid M." },
    { "id": "ps", "name": "Priya S." }
  ],
  "access": "team_only",
  "created_at": "2026-07-13T14:30:00Z"
}
```

### `GET /api/reviewers`

Response `200 OK`:

```json
[
  { "id": "fm", "name": "Farid M." },
  { "id": "ps", "name": "Priya S." },
  { "id": "jn", "name": "Jarod N." }
]
```

The owner (`ar`, Aisyah R.) is excluded from this list — a user cannot pick themselves as a reviewer.

### Error table

| Status | Code                          | Condition                                                                      |
| ------ | ----------------------------- | ------------------------------------------------------------------------------ |
| 400    | `NAME_REQUIRED`               | `name` field missing or empty after trimming.                                  |
| 400    | `NAME_TOO_SHORT`              | `name` length < 3 characters after trimming.                                   |
| 400    | `NAME_TOO_LONG`               | `name` length > 120 characters after trimming.                                 |
| 400    | `DESCRIPTION_TOO_LONG`        | `description` length > 500 characters.                                         |
| 400    | `TARGET_PUBLICATION_TOO_LONG` | `target_publication` length > 60 characters.                                   |
| 400    | `INVALID_DELIVERABLE_TYPE`    | `deliverable_type` not in `PD                                                  | ED                | DP  | Other`. |
| 400    | `INVALID_ACCESS`              | `access` not in `team_only                                                     | department_wide`. |
| 400    | `INVALID_REVIEWER_ID`         | Any element of `reviewer_ids` not present in `engine/directory.py::REVIEWERS`. |
| 409    | `WORKSTREAM_SLUG_COLLISION`   | Collision on generated slug persists after 10 retries.                         |
| 500    | `WORKSTREAM_WRITE_FAILED`     | Filesystem write to `data/workstreams/{id}/workstream.json` failed.            |

Error response shape:

```json
{
  "error": {
    "code": "NAME_TOO_LONG",
    "message": "Workstream name must be 120 characters or fewer.",
    "field": "name"
  }
}
```

## Data Model

`data/workstreams/{workstream_id}/workstream.json` — one file per workstream:

```json
{
  "id": "climate-risk-pd-v2-2026",
  "name": "Climate Risk PD v2 · 2026",
  "description": "Response to BCBS climate principles 2022 — draft PD targeting Q4 2026.",
  "deliverable_type": "PD",
  "target_publication": "Q4 2026",
  "owner": { "id": "ar", "name": "Aisyah R." },
  "reviewers": [
    { "id": "fm", "name": "Farid M." },
    { "id": "ps", "name": "Priya S." }
  ],
  "access": "team_only",
  "created_at": "2026-07-13T14:30:00Z"
}
```

`data/workstreams/{workstream_id}/graph.json` — initialised on create as:

```json
{ "nodes": [], "edges": [] }
```

`data/workstreams/{workstream_id}/drafts/` — empty directory created on scaffold for the future drafts feature.

Additional concrete workstream examples (used for demo seeding):

```json
{
  "id": "rmit-v2-technology-risk",
  "name": "RMiT v2 — Technology Risk",
  "description": "Refresh of RMiT anchoring on technology risk clauses 17.1 and 17.2.",
  "deliverable_type": "PD",
  "target_publication": "Q2 2027",
  "owner": { "id": "ar", "name": "Aisyah R." },
  "reviewers": [{ "id": "fm", "name": "Farid M." }],
  "access": "team_only",
  "created_at": "2026-06-02T09:15:00Z"
}
```

```json
{
  "id": "operational-resilience-v2",
  "name": "Operational Resilience v2",
  "description": "Second edition, aligning with OpRes 6.11 and BCBS operational resilience principles.",
  "deliverable_type": "ED",
  "target_publication": "Q1 2027",
  "owner": { "id": "ar", "name": "Aisyah R." },
  "reviewers": [
    { "id": "fm", "name": "Farid M." },
    { "id": "jn", "name": "Jarod N." }
  ],
  "access": "department_wide",
  "created_at": "2026-05-20T11:45:00Z"
}
```

Static reviewer directory — `engine/directory.py`:

```python
REVIEWERS = [
    {"id": "ar", "name": "Aisyah R."},
    {"id": "fm", "name": "Farid M."},
    {"id": "ps", "name": "Priya S."},
    {"id": "jn", "name": "Jarod N."},
]

OWNER_ID = "ar"  # hard-coded MVP1 owner
```

## UI / Frontend Requirements

Components under `frontend/src/features/new-workstream/`:

- `NewWorkstreamPage.tsx` — page route registered at `/workstreams/new` in the app router.
- `NewWorkstreamForm.tsx` — the three-card form. Uses `useForm` from `react-hook-form` with `zodResolver(newWorkstreamSchema)`.
- `schema.ts` — exports `newWorkstreamSchema` (zod) and its inferred TS type `NewWorkstreamInput`.
- `ReviewerCombobox.tsx` — shadcn `Command` combobox driven by `useQuery(['reviewers'], fetchReviewers)`. Selected reviewers render as removable pills using shadcn `Badge` + close icon.
- `OwnerBlock.tsx` — read-only shadcn `Avatar` (initials "AR") + "Aisyah R." + a muted "(you)" tag.
- `AccessRadio.tsx` — shadcn `RadioGroup` with two options: `team_only` (default, "Only the owner and named reviewers can open nodes.") and `department_wide` ("Anyone in the Prudential Policy Department can open nodes.").

Layout:

- Page shell reuses the shared collapsible sidebar from other stories.
- Breadcrumb: "← Workstreams / New" using shadcn `Breadcrumb`.
- Three shadcn `Card` sections stacked vertically: **Basics**, **People**, **Access**.
- Footer: "Cancel" (secondary, navigates back) and "Create workstream" (primary submit) buttons.

Client behaviour:

- Submit uses `useMutation` from TanStack Query v5 posting to `POST /api/workstreams`.
- On `201`, invalidate the `['workstreams']` query so the sidebar workstream list refetches, then `useNavigate` to `/workstreams/{id}`.
- On `400`/`409`, map `error.code` -> `error.field` and call `form.setError(field, { message })` so the inline error appears under the correct input via shadcn `FormMessage`.
- The primary submit button is disabled until both `name` (>= 3 chars) and `deliverable_type` pass zod validation.

Route registration example:

```tsx
<Route path="/workstreams/new" element={<NewWorkstreamPage />} />
<Route path="/workstreams/:workstreamId" element={<WorkstreamGraphPage />} />
```

## Architecture Notes

- Reuses shadcn primitives already introduced by the workstream-graph story: `Card`, `Form`, `Input`, `Select`, `Textarea`, `Button`, `Command`, `RadioGroup`, `Avatar`, `Badge`, `Breadcrumb`.
- No new frontend dependencies beyond what the graph story pulls in (`react-hook-form`, `zod`, `@hookform/resolvers`, `@tanstack/react-query`).
- Backend integration point: extend `engine/api.py` with two new FastAPI routes; add a new module `engine/directory.py` for the static reviewer list.
- Persistence is a plain JSON write; no database in MVP1. Folder scaffolding uses `pathlib.Path.mkdir(parents=True, exist_ok=False)` per attempt inside the slug collision loop.
- Sidebar highlight: the sidebar reads the active route via `useLocation()`; when `pathname === '/workstreams/new'`, the "+ New workstream" item gets the active-state styles.

## Exemplar Files

- `engine/api.py` — existing FastAPI app + route pattern to follow for `POST /api/workstreams` and `GET /api/reviewers`.
- `docs/poc/workstream-brain/new-workstream.html` — reference layout for the three-card form (Basics, People, Access).

## Implementation Plan

- **Task 1 (small, INDEPENDENT):** create `engine/directory.py` with the `REVIEWERS` list and `OWNER_ID` constant. Add a unit test asserting the four expected entries and that ids are unique.
- **Task 2 (small, INDEPENDENT):** extend `engine/api.py` with `GET /api/reviewers` (returns list excluding the owner) and `POST /api/workstreams`. Implement:
  - server-side zod-equivalent validation (Pydantic model) mapping to the error table,
  - slug generation with collision retry (up to 10 attempts, then `WORKSTREAM_SLUG_COLLISION`),
  - folder scaffolding: create `data/workstreams/{id}/` with `workstream.json`, `graph.json` (`{"nodes": [], "edges": []}`), and an empty `drafts/` directory,
  - all-or-nothing behaviour: if any validation error occurs, no folder is created; if write fails midway, clean up the partial directory before returning the error.
- **Task 3 (medium, SEQUENTIAL — after workstream-graph Task 1 lands the shared shell/sidebar):** build `NewWorkstreamPage` under `frontend/src/features/new-workstream/`:
  - zod schema + `react-hook-form`,
  - three shadcn `Card` sections,
  - reviewer combobox wired to `GET /api/reviewers`,
  - Owner block (read-only), Access radio,
  - submit via `useMutation`, on `201` invalidate `['workstreams']` and navigate to `/workstreams/{id}`,
  - map server error codes to inline field errors.
- **Task 4 (small, SEQUENTIAL — after Task 3):** wire the sidebar so that (a) the "+ New workstream" item is highlighted when `pathname === '/workstreams/new'`, and (b) on successful create the workstream list refreshes via `queryClient.invalidateQueries(['workstreams'])`.

## Negative Constraints

- Do NOT render the legacy labels "prior version", "anchor", "benchmark", or "constraint" anywhere on this form. These fields must not exist in the schema, in the DOM, or in any helper text.
- Do NOT allow the user to change the owner in MVP1. The Owner block is read-only; the server ignores any `owner` field submitted in the request body.
- Do NOT persist reviewer or access changes after creation via this screen. Post-creation edits are the responsibility of a future workstream-settings screen and are explicitly out of scope.
- Do NOT create the `data/workstreams/{id}/` folder if any validation error occurs. Creation is all-or-nothing: validate first, write second, and clean up on partial failure.
- Do NOT allow the current user to pick themselves as a reviewer. `GET /api/reviewers` excludes the owner id.
- Do NOT introduce a database, ORM, or migration tooling. Persistence is JSON on disk under `data/workstreams/` for MVP1.
- Do NOT add a live staff directory integration. The reviewer list is the static `engine/directory.py::REVIEWERS`.

## Test Scenarios (implementation-level)

Backend (`engine/tests/test_api.py`):

- `test_POST_workstream_creates_folder_and_workstream_json_and_empty_graph` — happy path for "Climate Risk PD v2 · 2026", asserts `workstream.json` content, `graph.json` equals `{"nodes": [], "edges": []}`, and `drafts/` directory exists.
- `test_POST_workstream_400_NAME_REQUIRED_when_name_missing` — empty `name` field returns 400 with code `NAME_REQUIRED`.
- `test_POST_workstream_400_NAME_TOO_SHORT_at_2_chars` — `name` of "AB" returns `NAME_TOO_SHORT`.
- `test_POST_workstream_400_NAME_TOO_LONG_at_121_chars` — 121-character name returns `NAME_TOO_LONG`.
- `test_POST_workstream_400_INVALID_DELIVERABLE_TYPE` — `deliverable_type` of "White Paper" returns `INVALID_DELIVERABLE_TYPE`.
- `test_POST_workstream_400_INVALID_ACCESS` — `access` of "public" returns `INVALID_ACCESS`.
- `test_POST_workstream_slug_generation_climate_risk_pd_v2_2026` — asserts "Climate Risk PD v2 · 2026" -> `climate-risk-pd-v2-2026`.
- `test_POST_workstream_slug_generation_strips_diacritics_and_punctuation` — "RMiT v2 — Technology Risk" -> `rmit-v2-technology-risk`.
- `test_POST_workstream_slug_collision_retry_appends_suffix` — creating "Climate Risk PD v2 · 2026" twice yields the second id `climate-risk-pd-v2-2026-2`.
- `test_POST_workstream_409_WORKSTREAM_SLUG_COLLISION_after_10_retries` — pre-seed 10 collisions, next create returns 409.
- `test_POST_workstream_400_INVALID_REVIEWER_ID_when_reviewer_not_in_directory` — `reviewer_ids: ["xx"]` returns 400 with code `INVALID_REVIEWER_ID`.
- `test_POST_workstream_owner_ignored_in_body_uses_server_default` — client sends `"owner": {"id": "fm", "name": "Farid M."}`; persisted owner is still Aisyah R.
- `test_POST_workstream_no_folder_created_on_validation_error` — after a 400, asserts `data/workstreams/{would-be-id}/` does not exist.
- `test_POST_workstream_html_stripped_from_description` — description `"<script>x</script>Hello"` persists as `"Hello"`.
- `test_GET_reviewers_returns_static_list_excluding_owner` — response contains `fm`, `ps`, `jn` but not `ar`.

Frontend component tests (`frontend/src/features/new-workstream/*.test.tsx`):

- Submit button is disabled until `name` (>= 3 chars) and `deliverable_type` both pass validation.
- Reviewer pills are removable with the close (×) button; removing "Farid M." leaves "Priya S." in place.
- No rendered field, label, dropdown option, or helper text contains the strings "prior version", "anchor", "benchmark", or "constraint".
- Owner block renders "Aisyah R. (you)" and is not an input element.
- Access radio defaults to `team_only`; selecting `department_wide` deselects `team_only`.
- On mocked 400 `NAME_TOO_LONG` response, the inline error appears under the Workstream name input.

## Verification

- **Backend:** `pytest engine/tests/test_api.py -k new_workstream -v`
- **Frontend unit/component:** `cd frontend && npm run test -- new-workstream`
- **E2E:** `frontend/e2e/new-workstream.spec.ts` (assigned to Task 3) — Playwright script that:
  1. loads the app,
  2. clicks "+ New workstream" in the sidebar,
  3. fills in Workstream name = "Climate Risk PD v2 · 2026", description = "Response to BCBS climate principles 2022 — draft PD targeting Q4 2026.", deliverable type = "Policy Document (PD)", target publication = "Q4 2026",
  4. adds "Farid M." and "Priya S." as reviewers,
  5. submits,
  6. asserts URL is `/workstreams/climate-risk-pd-v2-2026`, the graph is empty (no nodes, no edges), and the sidebar lists the new workstream.
