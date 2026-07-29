# The Copilot Stops Asking What I Am Drafting

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Task Type & Editable Node Metadata — Overview](spec.md)

Opening the Copilot on a working draft currently starts with a dropdown asking what kind of deliverable it is, defaulted to Policy Document no matter what the draft actually is. Aisyah already answered that question when she created the draft. This story removes the dropdown and has the Copilot work from the kind already recorded.

## User Story

As Aisyah R., I want the Copilot to already know what kind of document I am drafting, so that I can start asking it questions instead of re-answering one I have already answered.

## Background & Context

**Current state:**

- Aisyah records a deliverable kind when she creates a workstream, and the working draft is named after it — "Open Finance ED response (ED)".
- When she opens the Copilot on that draft, the first thing in the panel is a dropdown asking what kind of deliverable she is producing. It offers seven options and always starts on Policy Document.
- The dropdown resets to Policy Document every time she opens the Copilot, because the conversation is deliberately not kept between sessions.
- The choice frames how the Copilot pitches its help — a discussion paper favours framing questions for consultation, a policy document favours policy prose.

**Problem:**

- **The tool asks a question it already knows the answer to.** Aisyah told it she was drafting an exposure draft. The Copilot greets her with a dropdown set to Policy Document and expects her to answer again.
- **The default is wrong more often than it is right.** Six of the seven options are not Policy Document, and the panel starts on Policy Document regardless. A drafter who does not notice gets help framed for the wrong kind of document.
- **It has to be re-answered every session.** The question is not asked once, it is asked every single time the panel is opened.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, working in the drafting workspace on a working draft.
- **Context:** Every time she opens the Copilot alongside her draft — several times a day during active drafting.
- **Current workaround:** She either sets the dropdown each session, or does not notice it and accepts help framed for a policy document.

## Goals

- Remove the deliverable-kind question from the Copilot panel entirely.
- Have the Copilot work from the deliverable kind already recorded on the working draft.
- Leave everything else about the Copilot's behaviour exactly as it is.

## Non-Goals

- **Teaching the Copilot to reason over the other nine profile fields.** Policy owner, applicability, legal basis, and the rest are captured by another story in this epic; what the Copilot does with them is a separate spec, deliberately not started here.
- **Changing the Copilot's answers, tone, citation behaviour, or anything else in the panel.** The only change is that a question disappears and its answer comes from what is already recorded.
- **Letting a drafter override the kind for a single question.** The recorded kind is what the Copilot uses.

## User Workflow

1. **She opens her draft.** Aisyah opens the RMiT FAQ working draft in the drafting workspace.
2. **She opens the Copilot.** The panel opens straight into the conversation. Nothing asks what she is drafting.
3. **She asks her question.** She types it and gets an answer, framed for an FAQ because that is what the draft is recorded as.

## Acceptance Criteria

### Scenario: The Copilot opens with no question to answer

```gherkin
Given I am working on the RMiT FAQ working draft
When I open the Copilot
Then I am not asked what kind of deliverable I am producing
  And I can type my first question straight away
```

### Scenario: The Copilot works from the recorded deliverable kind

```gherkin
Given the Open Finance working draft is recorded as an exposure draft
When I open the Copilot on it
  And I ask it to help me draft a section
Then its help is framed for an exposure draft
  And at no point am I asked to confirm the deliverable kind
```

### Scenario Outline: Every deliverable kind is honoured without being asked

```gherkin
Given a working draft recorded as <kind>
When I open the Copilot on it
  And I ask it a question
Then its help is framed for <kind>
  And I am not asked what kind of deliverable I am producing

Examples:
  | kind                             |
  | "PD — Policy Document"           |
  | "DP — Discussion Paper"          |
  | "ED — Exposure Draft"            |
  | "FAQ"                            |
  | "Engagement Deck"                |
  | "Feedback Template for Industry" |
  | "Peer Benchmarking"              |
  | "Others"                         |
```

### Scenario: The question does not return in a later session

```gherkin
Given I have used the Copilot on the RMiT FAQ working draft
When I close the drafting workspace and open the Copilot on that draft again
Then I am still not asked what kind of deliverable I am producing
```

### Scenario: A working draft with nothing recorded still works

```gherkin
Given a working draft that has no deliverable kind recorded
When I open the Copilot on it
Then I am not asked what kind of deliverable I am producing
  And the Copilot still answers my questions
```

## Business Rules & Constraints

- **The deliverable-kind question is removed from the Copilot panel.** There is no dropdown, no chip, and no other control asking or displaying it there. The kind is visible on the working draft itself, which is where it is recorded.
- **The Copilot uses the kind recorded on the working draft.** If the draft has none — a possibility only for a working draft created before this epic — the Copilot falls back to the kind recorded on the workstream, and if there is none of those either, it proceeds as it does today for a policy document. In no case does it ask.
- **The recorded kind cannot be overridden for a single question.** The kind is fixed once chosen, and the Copilot honours it.
- **Nothing else about the Copilot changes.** Its answers, its word-for-word citation rule, its ability to reference accepted findings, and its snippet suggestions all behave exactly as they do today.

## Success Metrics

- **The drafter is never asked what they are drafting.** Opening the Copilot on any working draft, in any workstream, presents no deliverable-kind question. This is the epic's headline measure.

## Dependencies

- **One shared vocabulary of deliverable kinds** must land first. Without it, the Copilot has nothing to read.

## Open Questions

- [x] ~~Should the dropdown be removed, or kept and pre-selected from the recorded kind?~~ — **Resolved:** removed. Pre-selecting would still show the drafter a question, and since the recorded kind cannot be changed anyway, a control that appears editable but is not would be misleading.
- [x] ~~Should the panel display the deliverable kind somewhere, even without a control?~~ — **Resolved:** no. The working draft already shows it, and the drafter opened that draft to get here. Restating it in the panel is noise.
- [x] ~~Should `intent` stay on the Copilot request body as an optional override?~~ — **Resolved:** no, it is removed from the wire contract entirely. Leaving it optional would keep a code path nothing exercises, and the kind is not overridable by decision. The `intent` parameter stays on `copilot_reply` / `copilot_reply_stream` — only its source moves from the client to the server.

---

## Functional Requirements

- **`intent` leaves the request contract.** `_parse_copilot_request` (`engine/api.py`) stops reading `intent` from the body and stops returning it in its kwargs dict. `INVALID_INTENT` is deleted. A body that still carries `intent` is ignored rather than rejected — a stale client should not get a 400 for sending a field the server no longer wants.
- **The server resolves it.** Both copilot routes derive the intent from the task node and pass it to `copilot_reply_fn` / `copilot_stream_fn` explicitly. Resolution order:
  1. `node["task_type"]` — the code recorded on the working draft;
  2. the workstream record's `deliverable_type`, reverse-mapped from label to code via `TASK_TYPES` (`"Policy Document"` → `"PD"`);
  3. `"PD"`.
     Step 2 exists only for a legacy task node created before story 1; step 3 only for a workstream record that is also missing it. Neither is reachable through the app once story 1 has landed.
- **The seam signatures are unchanged.** `copilot_reply` and `copilot_reply_stream` keep their keyword-only `intent: str`. Every injected test stub keeps working, and the injectable-seam contract in `create_app()` is untouched.
- **The system prompt reframes.** `_system_prompt`'s intent line changes from "the drafter has selected '{intent}'" to a statement of what the document is, because the drafter no longer selects anything. It must keep the existing "never licenses inventing content" clause verbatim.
- **Idempotency / atomicity:** not applicable — both routes are read-only with respect to the workstream.

### Validation & Business Rules

- No new validation. The resolved intent comes from a closed vocabulary already validated at write time by story 1, so it cannot be out of range by the time these routes read it.
- A resolved intent is always a non-empty string, so `_system_prompt` never interpolates `None`.
- The four unrelated request fields (`message`, `history`, `referenced_finding_ids`, `draft_html`, `draft_selection`) keep their current validation exactly, including `400 MESSAGE_REQUIRED`.

## Permissions & Security

- **Scope:** unchanged — internal, unauthenticated, and the only routes in the service that reach a live model.
- **Change in attack surface:** strictly narrowing. One client-supplied field that fed the system prompt is replaced by a server-side lookup from a closed vocabulary, so a caller can no longer influence the prompt's framing line at all.
- **Input validation:** unchanged for every remaining field.

## API Design

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/copilot`

**Request** — `intent` removed:

```json
{
  "message": "Draft me a governance section.",
  "history": [{ "role": "user", "text": "What does this FAQ need to cover?" }],
  "referenced_finding_ids": ["e-of_ed_2025--rmit_2025~0"],
  "draft_html": "<h2>1. Scope</h2><p>This FAQ accompanies the RMiT policy document.</p>",
  "draft_selection": "This FAQ accompanies the RMiT policy document."
}
```

**Response (200)** — unchanged:

```json
{
  "reply": {
    "role": "copilot",
    "text": "Your FAQ should address governance in question-and-answer form...",
    "citations": [
      {
        "clause_number": "RMiT 10.1",
        "text": "The board must establish a technology risk management framework."
      }
    ],
    "snippet_html": "<h3>Governance</h3><p>Q: Who approves the framework?</p>"
  }
}
```

**Errors:** `404 WORKSTREAM_NOT_FOUND`, `404 TASK_NOT_FOUND` (one code for both "no such node" and "not a task", from `_task_node`), `400 MESSAGE_REQUIRED`, `502 COPILOT_FAILED` — all unchanged. **`400 INVALID_INTENT` is removed.**

### `POST /api/workstreams/{workstream_id}/tasks/{node_id}/copilot/stream`

Same request change. SSE frame format (`token` / `done` / `error`) unchanged.

## UI/Frontend Requirements

### Components

**`CopilotTab`** — `frontend/src/features/drafting-workspace/CopilotTab.tsx`

- **Type:** Modify existing
- **Purpose:** delete the intent `<label>` / `<select>` block (the panel's first child) and the `intent` state.
- **Removals:** the `useState<CopilotIntent>("PD")` line; the `COPILOT_INTENTS` / `COPILOT_INTENT_LABELS` / `CopilotIntent` imports; the `aria-label="Intent preset"` select and its wrapping label.
- **Everything else is untouched** — the quick-prompt chips, the message list, `buildMockReply`, and the props contract all stay exactly as they are.

**Note on the current panel:** `CopilotTab` is a static mock (`buildMockReply`, no network call) as of commit `db7e7dd`; `sendCopilotMessage` and `streamCopilotMessage` in `frontend/src/lib/api.ts` have no callers. This story removes the dropdown from the mock panel **and** removes `intent` from both API client functions, so the wire contract and the UI agree whenever the panel is reconnected. Reconnecting it is out of scope.

### API client

`frontend/src/lib/api.ts` — drop the `intent: CopilotIntent` parameter from `sendCopilotMessage` and `streamCopilotMessage`, and the `intent` key from both request bodies. Both are currently uncalled, so this is a signature change with no call sites to update.

### User Interactions

- Open the Copilot → the conversation area is the first thing in the panel; no dropdown precedes it.

### States

Unchanged. No new loading, empty, or error state — a control is removed, nothing is added.

## Architecture Notes

- **New dependencies:** none.
- **Dependencies & integration:** depends on story 1 for `TASK_TYPES` and for `task_type` being present on task nodes. The label→code reverse map for fallback step 2 is derived from `TASK_TYPES` rather than hand-written, so the two cannot drift.
- **Breaking change:** `POST .../copilot` and `.../copilot/stream` no longer accept `intent`. The only callers are this repo's own API client (currently uncalled) and the engine tests. No external consumer exists.
- **Deleted symbols:** `copilot.INTENTS` (already removed by story 1), `INVALID_INTENT`, `CopilotIntent`, `COPILOT_INTENTS`, `COPILOT_INTENT_LABELS`.

## Exemplar Files

- `engine/api.py::_task_node` — the guard both copilot routes already use to resolve and type-check the task node; the resolved intent is read from the node it returns.
- `engine/api.py::post_copilot` — the existing call into `copilot_reply_fn(**fields)`; `intent` moves from `fields` to an explicit keyword argument alongside `node`.
- `engine/copilot.py::_system_prompt` — the prompt string to reword, keeping its grounding rules and output contract byte-identical.
- `engine/tests/test_api_drafting.py` — the copilot-route test conventions, including how the stub seams are injected via `create_app()`.

## Implementation Plan

### Sub-tasks

**Task 1: server-side intent resolution helper** — _small_

- Files: `engine/api.py` (a module-level `_resolve_intent(node, ws_record) -> str` implementing the three-step order), `engine/workstreams.py` (a `task_type_code_for_label(label)` reverse lookup derived from `TASK_TYPES`)
- SEQUENTIAL (depends on story 1's `TASK_TYPES`)

**Task 2: drop `intent` from the request contract and wire the resolver into both routes** — _small_

- Files: `engine/api.py` (`_parse_copilot_request`, `post_copilot`, `post_copilot_stream`)
- SEQUENTIAL (depends on Task 1)

**Task 3: reword the system prompt's intent line** — _small_

- Files: `engine/copilot.py` (`_system_prompt`)
- INDEPENDENT

**Task 4: engine tests** — _medium_

- Files: `engine/tests/test_api_drafting.py` (remove the `INVALID_INTENT` cases and the `intent` parametrization; add resolution + fallback coverage), `engine/tests/test_copilot.py` (keep the direct `intent="PD"` calls — the function signature is unchanged)
- SEQUENTIAL (depends on Task 2)

**Task 5: remove the dropdown and the client-side `intent`** — _small_

- Files: `frontend/src/features/drafting-workspace/CopilotTab.tsx`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts` (delete `CopilotIntent`, `COPILOT_INTENTS`, `COPILOT_INTENT_LABELS` — story 1 may already have done this)
- INDEPENDENT

**Task 6: frontend tests** — _small_

- Files: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx` (replace `"offers all seven intent presets"` with an assertion that no intent control exists), `frontend/src/test/msw/handlers.ts` (drop `intent` from the copilot handlers)
- SEQUENTIAL (depends on Task 5)

### Negative Constraints

- Do NOT change `copilot_reply` or `copilot_reply_stream`'s signature, including the keyword-only `intent: str`. Only its caller changes.
- Do NOT change the grounding logic, `_build_grounding_context`, `_split_reply`, `_validate_reply`, or the `<<<META>>>` sentinel contract.
- Do NOT alter the citation guardrail or the "No matching clause found" sentence.
- Do NOT reconnect `CopilotTab` to the live endpoints. It is a static mock by decision (`db7e7dd`); rewiring it is a separate piece of work.
- Do NOT feed the other nine metadata fields into the prompt — that is the deferred Copilot spec.
- Do NOT touch the SSE frame format or `StreamingResponse` setup.
- Do NOT reject a request that still carries `intent`; ignore it.

## Test Scenarios

**Test 1: the resolved intent comes from the node**

- Setup: `create_app` with a stub `copilot_reply_fn` that captures its kwargs; a task node carrying `"task_type": "FAQ"`
- Action: `POST .../tasks/{node}/copilot` with `{"message": "hi"}` and no `intent`
- Expected: `200`; the captured `intent == "FAQ"`

**Test 2: a body that still sends `intent` is ignored, not rejected**

- Setup: same, node `task_type` is `"DECK"`
- Action: `POST` with `{"intent": "BENCHMARK", "message": "hi"}`
- Expected: `200`; captured `intent == "DECK"` — the node wins and no error is raised

**Test 3: `INVALID_INTENT` no longer exists**

- Setup: same
- Action: `POST` with `{"intent": "Freestyle", "message": "hi"}`
- Expected: `200`, not `400`. The string `INVALID_INTENT` appears nowhere in `engine/`

**Test 4: fallback to the workstream's deliverable type**

- Setup: a task node with no `task_type`; its `workstream.json` reads `"deliverable_type": "Exposure Draft"`
- Action: `POST` with `{"message": "hi"}`
- Expected: captured `intent == "ED"`

**Test 5: fallback to `PD` when neither is recorded**

- Setup: a task node with no `task_type` and a workstream record with no `deliverable_type`
- Action: `POST` with `{"message": "hi"}`
- Expected: captured `intent == "PD"`; no error

**Test 6: every recorded kind reaches the seam**

- Setup: parametrized over the eight codes, each written onto the task node
- Action: `POST` with `{"message": "hi"}`
- Expected: captured `intent` equals the node's `task_type` in all eight cases

**Test 7: the streaming route resolves identically**

- Setup: stub `copilot_stream_fn` capturing kwargs; node `task_type` is `"FEEDBACK"`
- Action: `POST .../copilot/stream` with `{"message": "hi"}`
- Expected: `200`, `text/event-stream`; captured `intent == "FEEDBACK"`

**Test 8: unrelated validation is unchanged**

- Setup: any task node
- Action: `POST` with `{"message": "   "}`
- Expected: `400 MESSAGE_REQUIRED`

**Test 9: non-task nodes still refused**

- Setup: `open-finance-pd-2026`, node `bis-papers-168`
- Action: `POST .../tasks/bis-papers-168/copilot` with `{"message": "hi"}`
- Expected: `404 TASK_NOT_FOUND` (unchanged — `_task_node` uses one code for both "not a task" and "not found")

**Test 10: the prompt states the document kind without claiming the drafter chose it**

- Setup: stub `turn_fn` capturing the system prompt; call `copilot_reply(intent="FAQ", ...)` directly
- Action: inspect the captured system prompt
- Expected: contains `"FAQ"`; does not contain `"has selected"`; still contains `"never licenses inventing content"` and the `No matching clause found` sentence

## Acceptance Criteria

- [ ] Neither copilot route reads `intent` from the request body
- [ ] Both routes resolve it from the task node, falling back to the workstream record then `PD`
- [ ] A request still carrying `intent` succeeds and the field is ignored
- [ ] `INVALID_INTENT`, `CopilotIntent`, `COPILOT_INTENTS`, and `COPILOT_INTENT_LABELS` exist nowhere in the repo
- [ ] No intent control renders in the Copilot panel
- [ ] `copilot_reply` / `copilot_reply_stream` signatures unchanged; citation guardrail untouched
- [ ] `pytest engine/tests` green; `npm run test` green in `frontend/`
- [ ] `mypy engine/` shows no new warnings beyond the accepted baseline
- [ ] No type errors or lint warnings

## Verification

Run the verifier skill. Build in the main working tree.

### Backend API Tests

| File                                | Covers                                                           |
| ----------------------------------- | ---------------------------------------------------------------- |
| `engine/tests/test_api_drafting.py` | Tests 1–9 — resolution, fallbacks, ignored `intent`, both routes |
| `engine/tests/test_copilot.py`      | Test 10 — the reworded system prompt, via a captured `turn_fn`   |

CI needs no model or credentials: both routes' model calls are injected seams and every test stubs them, as `test_api_drafting.py` already does.

Run: `.venv/bin/python -m pytest engine/tests/test_api_drafting.py engine/tests/test_copilot.py` then the full suite.

### Browser/UI Testing

Start the engine and the app, then:

1. Open a workstream and click its working draft, then **Open task** and the **Copilot** tab. **Expect:** the panel opens with the conversation area first — no dropdown, and nothing asking what kind of deliverable you are producing.
2. Send a message. **Expect:** a reply appears as it does today (the panel is a static mock, so the reply is canned — this confirms nothing regressed).
3. Switch to another tab and back to Copilot. **Expect:** still no intent control.

### E2E Tests

No new E2E. The observable change is the **absence** of a control on a panel that makes no network call, which `DraftingWorkspacePage.test.tsx` asserts directly and more cheaply — it already has the `"offers all seven intent presets"` test to invert. The behavioural half of this story (which intent the server resolves) has no UI surface at all while the panel remains a mock, so it is covered by engine Tests 1–9. Adding a Playwright spec here would assert that an element does not exist, on a page whose Copilot never reaches the endpoint under test.
