# One Name for the Regulatory Profile Store

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Type:** Technical — refactor (naming / internal consistency)

**Epic:** [Recommendations — Overview](spec.md)

The directory named `concepts/` does not hold concepts. It holds the seven-field regulatory profile, which the API serves as `metadata`. The thing that actually is a document's concepts — its extracted axes — lives in `axes/` and is served as `concepts`. This story moves the profile store to the name the API already uses for it, and leaves the axes alone.

## Motivation

Two vocabularies describe one thing and they disagree: the API and the interface call the seven-field regulatory profile `metadata`, while the storage layer and its engine module call it `concepts`. Worse, `concepts` is genuinely taken — a document's **extracted axes** are served under that name from `axes/`. So the directory called `concepts/` is the one thing in the system that is not concepts, and a reader who opens it looking for axes reads the wrong file.

**Current state:** the profile lives in `{ws}/concepts/{node}.json`, read and written by `engine/concepts.py`. The node-detail response carries both a `metadata` block (that profile) and a `concepts` block (the axes).

**Desired state:** the profile lives in `{ws}/metadata/{node}.json`, read and written by `engine/node_metadata.py`. `concepts` refers only to extracted axes, everywhere.

**Trigger:** the Recommendations epic reads `policy_requirement` out of this store. Written against the old name, that code would either propagate the confusion or need renaming a week later.

## Background & Context

**Current state:**

The node-detail response carries two distinct blocks whose names cross over:

| Block in the response | What it is                         | Read from   |
| --------------------- | ---------------------------------- | ----------- |
| `metadata`            | The seven-field regulatory profile | `concepts/` |
| `concepts`            | A document's **extracted axes**    | `axes/`     |

The profile store was named `concepts/` before the word was repurposed. When axis extraction landed, `concepts` became the name for extracted axes on the API surface and in the interface, but the profile's directory and its module kept the old name. The frontend already calls the profile `metadata` — the write route is `…/nodes/{id}/metadata`, the response key is `metadata` — so the split is only in the storage layer and the engine module.

This matters now because the Recommendations epic reads `policy_requirement` out of that store. New code written against the current name would either propagate the confusion or be renamed shortly afterwards.

**Problem:**

- **The name is actively misleading, not merely dated.** A reader looking for a document's concepts finds `concepts/` and reads the wrong file. This is a trap that a new contributor hits by doing the obvious thing.
- **Two vocabularies for one thing, in one codebase.** The API and interface say `metadata`; the storage layer and engine module say `concepts`. Every reader has to hold the mapping in their head.
- **The next feature depends on this store.** Recommendations is formulated on a field inside it, so the confusion is about to spread into new code.

## Affected System

- The regulatory-profile store on disk, and the engine module that reads and writes it.
- The application's node-detail and profile-save routes, which call that module.
- The frontend type name for the profile shape.

**Explicitly not affected:** the axis extraction route, the node-detail `concepts` response block, the `axes/` store, and everything that reads extracted axes. Those are the real concepts and keep the name.

## Goals

- Move the regulatory-profile store to `metadata/`, matching the name the API and interface already use for it.
- Rename the engine module and its read/write functions to match.
- Rename the frontend type for the profile shape to match.
- Leave the API surface — routes, request shapes, response shapes, field names — completely unchanged.
- Leave the three retired workstream fixtures byte-identical on disk.

## Non-Goals

- **Renaming the axis vocabulary.** The extraction route and the `concepts` response block keep their names. They describe extracted axes, which genuinely are concepts. Changing them would break the API surface and reach a dozen files with no relation to this epic.
- **Changing the profile's contents or field names.** The seven fields are untouched.
- **Migrating the retired workstreams.** They keep their existing directory, read through a fallback.
- **Any user-visible change.** Nothing in the interface behaves differently.

## Scope

**In scope:**

- The profile store directory name, for new writes.
- The engine module name and its path/load/save function names.
- The frontend type name for the profile shape.
- A read fallback so an absent new directory falls back to the old one.
- Test updates following the renames.

**Out of scope:**

- Axis extraction and the `axes/` store.
- The `concepts` block in the node-detail response.
- The profile's field set, validation rules, and size limits.
- Retired workstream fixture contents.

## Acceptance Criteria

### Scenario: A profile saved after the rename lands in the new store

```gherkin
Given a document with no regulatory profile recorded
When a drafter fills in its profile and saves
Then the profile is stored under the new name
  And reading the document back returns exactly what was saved
```

### Scenario: A retired workstream's profile is still readable

```gherkin
Given a retired workstream whose profiles are stored under the old name
  And it has no store under the new name
When a document from it is opened
Then its regulatory profile is returned unchanged
  And nothing on disk has been altered
```

### Scenario: Saving into a retired workstream moves it forward

```gherkin
Given a retired workstream whose profiles are stored under the old name
When a drafter saves a profile on one of its documents
Then the saved profile is written under the new name
  And reading it back returns the saved profile, not the older one
```

### Scenario: Extracted axes are untouched

```gherkin
Given a document with extracted axes
When it is opened
Then its extracted axes are returned exactly as before
  And they are still presented under the concepts name
  And axis extraction behaves exactly as it did
```

### Scenario: The API surface is unchanged

```gherkin
Given the rename has been applied
When a document is opened or its profile is saved
Then the routes, request shapes and response shapes are identical to before
  And every field name in the response is unchanged
```

### Scenario: Retired fixtures are not modified

```gherkin
Given the three retired workstreams
When the rename has been applied
Then none of their files has changed
  And every test that reads them still passes
```

## Business Rules & Constraints

- **Reads try the new store, then fall back to the old one.** This is what keeps the retired fixtures untouched — the repo's standing rule is that a retired fixture's contents are recorded history, not a defect to correct.
- **Writes always go to the new store.** A retired workstream saved through the tool moves forward; it is never migrated in bulk.
- **The API surface does not change.** No route, request shape, response shape or field name moves. The rename is entirely internal.
- **The axis vocabulary is untouched.** `concepts` on the API surface continues to mean extracted axes.
- **No behaviour changes.** This is a pure rename, verifiable by the existing suite passing without changes to what it asserts, beyond the renamed identifiers themselves.

## Success Metrics

- **The suite passes with no assertion changed**, only renamed identifiers — the definition of a behaviour-preserving refactor.
- **One name per concept.** After this story, the profile is called `metadata` in the storage layer, the engine, the API and the interface; `concepts` refers only to extracted axes.
- **The next feature is written once.** Recommendations reads `policy_requirement` from a correctly named store and never needs renaming.

## Dependencies

- **None.** This story stands alone and can be built and merged before, alongside, or independently of the rest of the epic. It ships in the same change set as the first Recommendations story so that story's code is written against the corrected name from the outset.

## Risks

- **A missed call site would break profile reads.** Mitigated by the small, enumerable blast radius — roughly thirty call sites across two engine files and two test files — and by the existing profile test suite, which covers save, read-back, validation and the retired-fixture path.
- **Confusing this rename with the axis vocabulary would break the API surface.** Mitigated by stating the boundary explicitly in scope, and by an acceptance criterion asserting extracted axes are unchanged.

## Open Questions

- [x] ~~Should the axis vocabulary be renamed too, so the word `concepts` disappears entirely?~~ — **Resolved: no.** Extracted axes genuinely are concepts and deserve the name. Renaming them would break the API surface and reach files unrelated to this epic.
- [x] ~~Should the retired workstreams' directories be renamed on disk?~~ — **Resolved: no.** A read fallback achieves the same result while honouring the repo's rule that retired fixture contents are not modified.
- [x] ~~Should the rename ship separately from the feature?~~ — **Resolved: same change set.** The drafter chose this so the new code is written against the corrected name once rather than renamed straight after.

---

## Solution Design

A pure rename with a read fallback. Reads try `metadata/` and fall back to `concepts/`; writes always go to `metadata/`. That fallback is what lets the three retired fixtures stay byte-identical while new code reads one name.

**Before:**

```
engine/concepts.py
  concepts_path(dir, ws, node)  → {ws}/concepts/{node}.json
  load_concepts(...)            → reads that path
  save_concepts(...)            → writes that path
```

**After:**

```
engine/node_metadata.py
  metadata_path(dir, ws, node)  → {ws}/metadata/{node}.json          (canonical)
  legacy_metadata_path(...)     → {ws}/concepts/{node}.json          (read-only fallback)
  load_metadata(...)            → metadata/ if present, else concepts/, else None
  save_metadata(...)            → always metadata/
```

Everything else in the module — `CONCEPT_FIELDS`, `LIST_FIELDS`, `MAX_FIELD_CHARS`, `MAX_LIST_MEMBERS`, `ISMP_CLASSIFICATIONS`, `validate_metadata`, `normalise_metadata` — moves across **unchanged in behaviour**. `CONCEPT_FIELDS` is renamed `METADATA_FIELDS` for consistency; its tuple contents are untouched.

### Changes

- `engine/concepts.py` → **`engine/node_metadata.py`** (git mv). Rename the three path/IO functions and `CONCEPT_FIELDS` → `METADATA_FIELDS`; add `legacy_metadata_path` and the fallback in `load_metadata`. Update the module docstring to explain the two directories and why the fallback exists.
- `engine/api.py` — update the import and all call sites. **Critically: `_node_concepts_block` (line 369) is NOT touched** — it reads `axes/`, not the profile store, and is the _real_ concepts. Same for `extract_axes_fn`, the `extract-concepts` route (line 1361), and the `concepts` key in the node-detail response (line 1270).
- `engine/arm_g.py`, `engine/cross_intel.py` — update imports and call sites only.
- `frontend/src/lib/types.ts` — `ConceptsAvailable` → `NodeMetadata`. **`NodeConcepts`, `ExtractConceptsResponse` and the `concepts` response fields stay** — they are the axes.
- `frontend/src/features/workstream-graph/metadata.ts` — `ConceptField` → `NodeMetadataField`; update the `ConceptsAvailable` reference in its `Omit<>`.
- Consumers of the renamed type: `NodeDetailPanel.tsx`, `NodeMetadataForm.tsx`, `CompareWorkstreamsPage.tsx`, `intel.ts`, `copilotV2Data.ts`, `CopilotTab.tsx`, plus their test files.
- `engine/tests/test_api_node_metadata.py`, `engine/tests/test_build_cli.py` — update imports and function names. **Assertions unchanged.**

**No route, request shape, response shape, or field name changes.** The node-detail response still carries `metadata` (the profile) and `concepts` (the axes), both spelled exactly as today.

### Data Model & Migrations

**Storage location moves; contents do not.**

|            | Before                      | After                                                         |
| ---------- | --------------------------- | ------------------------------------------------------------- |
| New writes | `{ws}/concepts/{node}.json` | `{ws}/metadata/{node}.json`                                   |
| Reads      | `{ws}/concepts/{node}.json` | `{ws}/metadata/{node}.json`, falling back to `{ws}/concepts/` |

File contents are the same seven-key object. No schema change, no field rename inside the file.

**Migration notes:**

- **No bulk migration, deliberately.** The three retired fixtures (`rmit-v2-2025`, `open-finance-ed`, `opres-v2`) keep their `concepts/` directories exactly as they are, per the retired-fixtures hard rule in `CLAUDE.md`. Five files across three workstreams stay on disk untouched.
- A retired workstream saved through the app writes to `metadata/`, leaving its `concepts/` file behind as dead-but-harmless history. `load_metadata` prefers `metadata/`, so the newer value wins.
- **The live demo workstream is migrated outright, not left on the fallback.** `open-finance-pd-2026/concepts/` was renamed to `metadata/` in this change (one file, `open-finance-pd-2026-pd.json`, moved with `git mv`). The no-migration rule covers **retired** fixtures only — `open-finance-pd-2026` is the live demo workstream, so leaving it on a legacy path would have been over-applying that rule. After this change exactly three workstreams read through the fallback, all retired.

## Architecture Notes

- **New dependencies:** none.
- **Why the rename belongs in this epic:** the Recommendations engine reads `policy_requirement` from this store. Written against the old name, that code would either propagate the confusion or need renaming a week later.
- **The `concepts` name is genuinely taken.** `_node_concepts_block` (`engine/api.py:369-378`) serves extracted axes from `axes/` under the key `concepts`. That is the correct use of the word. The directory called `concepts/` is the one thing in the system that is not concepts, which is exactly the trap being removed.
- **The fallback is permanent, not transitional.** There is no plan to migrate the retired fixtures, so `legacy_metadata_path` stays. Its docstring must say so, or a future contributor will "clean it up" and silently break three fixtures the engine suite reads by id.
- **`git mv`, not delete-and-create**, so the module's history follows it.

## Exemplar Files

- `engine/concepts.py` — the file being renamed. Its existing structure (module-level constants, `*_path` helper, `load`/`save`, `validate`/`normalise`) carries over as-is.
- `engine/findings.py` — the sibling side-file module, for the shape a `*_path` helper and its docstring take.
- `engine/api.py:1428-1474` (`put_node_metadata`) — the only writer, and the docstring that must be updated to name the new directory.
- `engine/tests/test_api_node_metadata.py:588` — already documents a field-rename compatibility concern (`legal_basis` → `legal_provision`), so it is the natural home for the directory-fallback tests.

## Implementation Plan

### Sub-tasks

**Task 1: `git mv` the module, rename its functions, add the fallback** — _medium_

- Files: `engine/concepts.py` → `engine/node_metadata.py`
- Rename `concepts_path`/`load_concepts`/`save_concepts` → `metadata_path`/`load_metadata`/`save_metadata`; `CONCEPT_FIELDS` → `METADATA_FIELDS`; add `legacy_metadata_path`; implement the read fallback; rewrite the module docstring to explain both directories and the fallback's permanence.
- INDEPENDENT

**Task 2: Update engine call sites** — _small_

- Files: `engine/api.py`, `engine/arm_g.py`, `engine/cross_intel.py`
- Imports and call sites only. **Do not touch** `_node_concepts_block`, `extract_axes_fn`, the `extract-concepts` route, or the `concepts` response key.
- SEQUENTIAL (depends on Task 1)

**Task 3: Update engine tests** — _small_

- Files: `engine/tests/test_api_node_metadata.py`, `engine/tests/test_build_cli.py`
- Renamed identifiers only. Add the three fallback tests below.
- SEQUENTIAL (depends on Task 2)

**Task 4: Rename the frontend type** — _small_

- Files: `frontend/src/lib/types.ts`, `frontend/src/features/workstream-graph/metadata.ts`, `NodeDetailPanel.tsx`, `NodeMetadataForm.tsx`, `CompareWorkstreamsPage.tsx`, `intel.ts`, `copilotV2Data.ts`, `CopilotTab.tsx`, and the matching `.test.tsx` files
- `ConceptsAvailable` → `NodeMetadata`, `ConceptField` → `NodeMetadataField`. **Leave `NodeConcepts` and `ExtractConceptsResponse` alone.**
- INDEPENDENT (type-only; no shared file with Tasks 1–3)

### Negative Constraints

- Do NOT rename the axes vocabulary: `extract-concepts` route, `_node_concepts_block`, the `axes/` store, `NodeConcepts`, `ExtractConceptsResponse`, or the `concepts` key in any response.
- Do NOT change any route, request shape, response shape, or response field name.
- Do NOT rename, move, or edit any file under a retired fixture's `concepts/` directory.
- Do NOT add a migration script or a bulk rewrite.
- Do NOT remove `legacy_metadata_path` or the fallback — they are permanent.
- Do NOT change the seven field names, the validation rules, or the size limits.
- Do NOT change what any existing test asserts, only the identifiers it imports.
- Do NOT use find-and-replace on the bare word `concepts` — it would hit the axes vocabulary, which is the one thing that must not move.

## Test Scenarios

**Test 1: A save lands in the new directory**

- Setup: `tmp_path` copy of `data/workstreams`. Target **`ed-open-finance-2025`** — a context document in `open-finance-pd-2026` with no profile file of its own. (Do **not** target the working draft `open-finance-pd-2026-pd`: it was seeded on 1 Aug 2026 and already has a `concepts/` file, so "no `concepts/` created" could not be asserted against it.)
- Action: `PUT /api/workstreams/open-finance-pd-2026/nodes/ed-open-finance-2025/metadata` with a full seven-field profile
- Expected: `200`; `{tmp}/open-finance-pd-2026/metadata/ed-open-finance-2025.json` exists; **no `concepts/ed-open-finance-2025.json` is created**; the response is the stored profile

**Test 2: A legacy `concepts/` profile is still readable**

- Setup: `opres-v2`, whose profiles live in `concepts/` and which has no `metadata/`
- Action: `GET /api/workstreams/opres-v2/nodes/opres-pd-v0-3`
- Expected: `200`; the `metadata` block carries `status: "available"` and the stored fields; the response is byte-equal to what the pre-rename code returned; **nothing on disk changed**

**Test 3: `metadata/` wins over `concepts/` when both exist**

- Setup: `opres-v2` with its existing `concepts/opres-pd-v0-3.json` (policy owner `"Aisyah R."`), plus a hand-written `metadata/opres-pd-v0-3.json` (policy owner `"Priya S."`)
- Action: `GET /api/workstreams/opres-v2/nodes/opres-pd-v0-3`
- Expected: policy owner is `"Priya S."`; the `concepts/` file is untouched on disk

**Test 4: Saving into a legacy workstream moves it forward**

- Setup: `opres-v2` with only `concepts/`
- Action: `PUT …/nodes/opres-pd-v0-3/metadata` with an edited profile
- Expected: `metadata/opres-pd-v0-3.json` is created with the new values; `concepts/opres-pd-v0-3.json` is **unmodified**; a following `GET` returns the new values

**Test 5: Extracted axes are unaffected**

- Setup: a node with an `axes/` file
- Action: `GET /api/workstreams/open-finance-pd-2026/nodes/ed-open-finance-2025`
- Expected: the `concepts` block still reports `status: "extracted"` with its axes; identical to pre-rename output

**Test 6: The `extract-concepts` route is unchanged**

- Action: `POST /api/workstreams/open-finance-pd-2026/nodes/ed-open-finance-2025/extract-concepts` with a stubbed `extract_axes_fn`
- Expected: same status, same response shape, same `concepts` key as before the rename

**Test 7: The API surface is byte-identical**

- Action: `GET …/nodes/{node_id}` on a node with both a profile and axes
- Expected: the response's top-level key set is unchanged, and both `metadata` and `concepts` are spelled exactly as before

**Test 8: Retired fixtures are not modified**

- Action: run the full engine suite, then `git status --porcelain data/workstreams/`
- Expected: empty output — no tracked fixture file changed. (Tests copy into `tmp_path`; this asserts none of them writes through to the source tree.)

**Test 9: Validation and limits still behave**

- Action: `PUT …/metadata` with a 2 001-character `policy_owner`, then with 51 `legal_provision` members
- Expected: `413 METADATA_TOO_LARGE` in both cases, with the same `field` values and messages as before the rename

**Test 10: `parse_dimensions` reads through the fallback**

- Setup: a workstream whose profile with a populated `policy_requirement` exists only in `concepts/`
- Action: `POST …/recommendations/generate`
- Expected: the dimensions are found and generation proceeds — the fallback works for the new consumer too, not just the node-detail route

## Acceptance Criteria

- [ ] `engine/concepts.py` no longer exists; `engine/node_metadata.py` does, with history preserved via `git mv`
- [ ] No reference to `load_concepts`, `save_concepts`, `concepts_path` or `CONCEPT_FIELDS` remains anywhere
- [ ] Writes go to `metadata/`; reads fall back to `concepts/`; `metadata/` wins when both exist
- [ ] `extract-concepts`, `_node_concepts_block`, the `axes/` store, `NodeConcepts` and every `concepts` response key are untouched
- [ ] No route, request shape, response shape or field name changed
- [ ] `git status data/workstreams/` is clean after the full suite
- [ ] No file under any retired fixture's `concepts/` directory is renamed, moved or edited
- [ ] `legacy_metadata_path`'s docstring states that the fallback is permanent
- [ ] The existing profile tests pass with only their imports and identifiers changed — **no assertion edited**
- [ ] All existing tests pass; no type errors or lint warnings

## Verification

Run the verifier skill. Locally `.venv/bin/python -m pytest engine/tests` and `cd frontend && npm run test`.

### Backend Tests

| File                                                    | Covers                                                                                                                                                                                                                                                 |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `engine/tests/test_api_node_metadata.py` (modify)       | Tests 1–5, 7, 9 — new-directory writes, legacy reads, precedence, forward-migration on save, axes untouched, surface stability, validation. Existing assertions unchanged; new tests added alongside the `legal_basis` compatibility test at line 588. |
| `engine/tests/test_api_extract_concepts.py` (unchanged) | Test 6 — must pass **with no edits at all**. If this file needs changing, the axes boundary has been crossed.                                                                                                                                          |
| `engine/tests/test_build_cli.py` (modify)               | Identifier renames only                                                                                                                                                                                                                                |
| `engine/tests/test_api_recommendations.py` (modify)     | Test 10 — the new consumer reads through the fallback                                                                                                                                                                                                  |

**The strongest signal that this refactor is behaviour-preserving:** `test_api_extract_concepts.py` passes untouched. It exercises the vocabulary that must not move.

### Manual Verification

- [ ] `grep -rn "load_concepts\|save_concepts\|concepts_path\|CONCEPT_FIELDS" engine/ frontend/src/` → no hits
- [ ] `grep -rn "extract-concepts\|_node_concepts_block\|NodeConcepts" engine/ frontend/src/` → hits unchanged in count from before the rename
- [ ] `git status --porcelain data/workstreams/` → empty after a full suite run
- [ ] `git log --follow engine/node_metadata.py` → shows the pre-rename history
- [ ] Open a `rmit-v2-2025` document in the app → its regulatory profile still renders from `concepts/`

No E2E tier: this task changes no user-facing behaviour. `frontend/e2e/edit-node-metadata.spec.ts` and `frontend/e2e/extract-concepts.spec.ts` already cover both surfaces and must pass **unchanged** — that they need no edits is the verification.
