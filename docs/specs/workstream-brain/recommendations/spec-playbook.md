# A Playbook That Configures the Copilot

**Ticket:** None — this repo has no issue tracker (see `CLAUDE.md`)

**Epic:** [Recommendations — Overview](spec.md)

The Copilot walks Aisyah through five stages — explore the task, brainstorm, outline a draft, write it, deliver it for review — and behaves the same way for every drafter on every document. This story gives each stage a **Playbook** section she fills in herself: the questions she wants brainstormed, the house structure a draft should follow, the writing conventions she holds to, and who signs off in what order. The first stage stays locked, because it reads the document's own recorded profile and inventing anything there would undermine it.

## User Story

As Aisyah R., I want to configure each stage of the Copilot with my own instructions, so that it drafts to my house conventions instead of me restating them every session.

## Background & Context

**Current state:**

- The drafting workspace shows two tabs beside the editor — **Reviewed**, a read-only list of the linkages Aisyah accepted, and **Copilot**, where drafting happens.
- The Copilot runs a fixed five-stage flow, each stage unlocked by the one before it: `/explore-task` (reveal the task's regulatory profile), `/brainstorm` (pull context, align on focus through questions), `/draft` (preview an outline), `/write` (write the full draft into the editor), `/deliver` (send the draft for review).
- Every stage behaves identically on every document. Nothing about how BNM structures a policy document, how Aisyah prefers to phrase an obligation, or who approves her work is recorded anywhere the Copilot can read.
- The Reviewed tab is a reference list. Aisyah reads it; nothing else uses it. Every accepted linkage it shows is also on the task screen.

**Problem:**

- **She restates the same instructions every session.** The standard policy-document skeleton, the paragraph numbering convention, the preference for principle-based phrasing — all of it is retyped into the chat, or omitted and then corrected afterwards.
- **The Copilot cannot know what it was never told.** Who approves a draft, in what order, and what each approver looks for is institutional knowledge with no home in the tool.
- **Brainstorming starts cold.** Aisyah arrives at `/brainstorm` with questions she has been carrying for days, and has to remember and retype them at the moment she is least likely to have them to hand.
- **A tab is spending panel space on a list.** Reviewed shows Aisyah what she already decided, duplicating the task screen, next to the two things she actually works with.

## Target User & Persona

- **Who:** Aisyah R., policy drafter, in the drafting workspace.
- **Context:** Either setting up before a drafting session, or partway through one, having just corrected the Copilot on something it should have known.
- **Current workaround:** She retypes her conventions into the chat each session, or accepts output that does not follow them and fixes it by hand.

## Goals

- Replace the Reviewed tab with a **Playbook** holding one section per Copilot stage.
- Let Aisyah write, in her own words, what each stage should do differently for her.
- Make what she saves reach the Copilot at the matching stage, without her restating it.
- Keep `/explore-task` **locked**, and show her plainly what it reads and where to change it.
- Keep a workstream's Playbook its own, so conventions for one policy area do not silently govern another.

## Non-Goals

- **Configuring the recommendations engine.** That is the guardrails box on the Recommendations card, reached by its own badge. The Playbook configures the Copilot and nothing else.
- **Changing the five stages, their order, or their sequential unlocking.** This story configures the existing flow; it does not redesign it.
- **Sending anything.** `/deliver` records who approves what, in what order, so the Copilot can prepare the routing. The tool holds no addresses and dispatches no mail. See _Business Rules_.
- **A working template upload.** The `/draft` stage shows an upload affordance for demonstration only — see _Business Rules_, where its non-functional status is recorded so nobody later mistakes it for a defect.
- **A rules engine or any validation of what she writes.** Every section is free text, bounded only by length.
- **Version history or approval of the Playbook itself.** She edits and saves.
- **Sharing a Playbook between workstreams.** Each has its own.

## User Workflow

1. **She opens the draft.** The tabs read **Recommendations**, **Playbook**, **Copilot**. There is no Reviewed tab.
2. **She opens the Playbook.** Five sections, one per Copilot stage, in the order the stages run.
3. **She reads the locked one.** `/explore-task` cannot be edited. It shows which parts of the document's recorded profile it reads, and links to where those are maintained.
4. **She seeds her brainstorm.** Under `/brainstorm` she writes the three questions she has been carrying: whether consent expiry should differ for business customers, how liability interacts with the operational-resilience document, and whether the phase-two scope needs restating.
5. **She records the house structure.** Under `/draft` she describes the standard policy-document skeleton and the paragraph numbering convention.
6. **She records how she writes.** Under `/write`: obligations phrased as "must", guidance as "should", no defined term introduced outside the interpretation section.
7. **She records who signs off.** Under `/deliver`: policy sign-off first, then legal for statutory basis, then the Deputy Governor's office.
8. **She drafts.** At each stage the Copilot follows what she wrote, without her repeating any of it in the conversation.

## Acceptance Criteria

### Scenario: The Playbook replaces the Reviewed tab

```gherkin
Given I am in the drafting workspace for a working draft
When I look at the tabs beside the editor
Then they read Recommendations, Playbook and Copilot in that order
  And there is no Reviewed tab
```

### Scenario: One section per Copilot stage, in flow order

```gherkin
Given I have opened the Playbook
When I look at it
Then there is a section for each of the five Copilot stages
  And they appear in the order the stages run
  And each says what it configures
```

### Scenario: The first stage is locked

```gherkin
Given I have opened the Playbook
When I look at the explore-task section
Then I cannot edit it
  And I am told it reads the document's recorded profile
  And I am shown where that profile is maintained
```

### Scenario: Seeding the brainstorm with my own questions

```gherkin
Given I have opened the Playbook
When I write three questions under the brainstorm section
  And I save
Then the Playbook shows them
  And they are still there when I return
```

### Scenario: A configured stage changes what the Copilot does

```gherkin
Given my Playbook records under the write section that obligations are phrased as "must" and guidance as "should"
When I ask the Copilot to write the draft
Then what it writes follows that convention
  And I did not restate it in the conversation
```

### Scenario: Each stage reads only its own section

```gherkin
Given my Playbook records a house structure under the draft section
  And it records approval layers under the deliver section
When I run the draft stage
Then it follows the house structure
  And it is not influenced by the approval layers
```

### Scenario: An empty section leaves its stage as it was

```gherkin
Given I have written nothing under the brainstorm section
When I run the brainstorm stage
Then it behaves as it does today
  And I am not blocked or warned
```

### Scenario: Recording who approves the draft

```gherkin
Given I have opened the Playbook
When I record under the deliver section that policy sign-off comes first, then legal, then the Deputy Governor's office
  And I save
Then the Playbook shows what I wrote
  And when I run the deliver stage it prepares the routing in that order
```

### Scenario: Nothing is sent by the tool

```gherkin
Given my Playbook records approval layers including named recipients
When I run the deliver stage
Then the Copilot prepares what should be sent and to whom
  And nothing is dispatched
  And I remain the one who sends it
```

### Scenario: Describing a template under the draft stage

```gherkin
Given I have opened the Playbook
When I describe the standard policy document skeleton under the draft section
  And I save
Then the draft stage follows that structure
```

### Scenario: Each workstream has its own Playbook

```gherkin
Given I have configured the write section in the Open Finance workstream
When I open the Playbook in the technology risk workstream
Then it does not contain what I wrote
  And every editable section there is empty
```

### Scenario: Every draft in a workstream shares its Playbook

```gherkin
Given I have configured the draft section in the Open Finance workstream
When I open a second working draft in that same workstream
Then its Playbook shows the same configuration
```

### Scenario: A workstream that predates the Playbook

```gherkin
Given a workstream created before Playbooks existed
When I open its Playbook
Then it shows the five sections with the editable ones empty
  And I can fill them in and save
```

### Scenario: A save that cannot be completed loses nothing

```gherkin
Given I have edited my Playbook
When the save cannot be completed
Then I am told it could not be saved and can try again
  And my edits are still on screen
  And the previously saved Playbook is unchanged
```

### Scenario: Clearing a section

```gherkin
Given the write section records conventions I no longer follow
When I clear that section and save
Then it is empty
  And the write stage behaves as it does today
```

## Business Rules & Constraints

- **A Playbook belongs to one workstream.** Every working draft in it reads the same one; no other workstream is affected by an edit.
- **One section per Copilot stage**, shown in flow order, each configuring that stage and only that stage:

  | Stage           | Editable | What Aisyah records there                                             |
  | --------------- | -------- | --------------------------------------------------------------------- |
  | `/explore-task` | **No**   | Nothing. It reads the document's recorded regulatory profile.         |
  | `/brainstorm`   | Yes      | Ideas and questions she wants to bounce off the Copilot.              |
  | `/draft`        | Yes      | The template or style guide a draft should follow.                    |
  | `/write`        | Yes      | Writing preferences and house rules.                                  |
  | `/deliver`      | Yes      | Approval and review conventions, and the approval layers to route to. |

- **`/explore-task` is locked because it must stay derived.** Its whole job is to reveal what the document's profile actually records. A drafter-authored override there would let the tool report a regulatory identity the document does not have, which is the opposite of what the stage is for. The section shows what it reads and links to where that profile is maintained.
- **`/deliver` records conventions; it does not send.** The tool holds no mail transport and dispatches nothing. What Aisyah writes lets the Copilot prepare the routing — who should receive the draft, in what order, and what each approver is being asked for — which she then sends herself. Any names or addresses she types are her own text in a free-text field; the tool neither validates nor transmits them.
- **The `/draft` upload affordance is deliberately non-functional.** An upload control appears on that section for demonstration, and **nothing is stored, parsed, or read from it**. What actually configures the stage is the text she writes. This is recorded here so that a later reader finds it documented as a decision rather than filing it as a defect. A working upload is a follow-on.
- **Every editable section starts empty.** There are no default instructions: the Copilot's current behaviour is the baseline, and an empty section changes nothing.
- **An empty section is a valid and expected state**, and never blocks or warns.
- **Sections are free text.** Nothing is parsed or validated beyond a length bound.
- **The Playbook conditions the Copilot only.** The recommendations engine reads the guardrails box, not this; pairwise analysis reads neither.
- **A failed save leaves the stored Playbook unchanged** and the drafter's edits on screen.

## Success Metrics

- **A convention is stated once.** After Aisyah records her writing conventions, she does not restate them in the Copilot conversation again.
- **The locked stage stays honest.** `/explore-task` reports only what the document's profile records, and a drafter can see why it cannot be overridden and where to change what it reads.
- **Configuration reaches the stage it belongs to.** What she writes under one stage changes that stage's behaviour and no other's.

## Dependencies

- **The Copilot's existing five-stage flow** is what each section configures. No change to the stages, their order, or their sequential unlocking.
- **The document's regulatory profile** is what `/explore-task` reads, and what the locked section links to. No change to how it is recorded.

## Open Questions

- [x] ~~Should the Playbook be institution-wide, per workstream, or layered?~~ — **Resolved: per workstream.** Institution-wide would let an Open Finance convention silently govern a technology-risk draft.
- [x] ~~Should the Reviewed tab be kept alongside the Playbook?~~ — **Resolved: no.** It duplicates the task screen, and every accepted finding that matters to drafting is either cited by a recommendation, quoted in full, or named in the not-yet-reflected section.
- [x] ~~Should `/explore-task` be editable like the others?~~ — **Resolved: no, locked.** The stage exists to reveal what the profile records. Letting a drafter author its output would let the tool state a regulatory identity the document does not have.
- [x] ~~Should `/deliver` actually send email?~~ — **Resolved: no.** The tool prepares the routing; the drafter sends. Mail transport, delivery failure handling, and holding real recipients would be a separate epic with an outward-facing, irreversible action at the end of it.
- [x] ~~Should the `/draft` template upload work?~~ — **Resolved: no, mocked for the demo.** The affordance is shown; nothing is stored or parsed. Text is what configures the stage.
- [x] ~~Should the editable sections ship with default content?~~ — **Resolved: no, empty.** Unlike the recommendations guardrails, there is no body of evidence saying what a good default instruction is, and pre-filled text a drafter did not write would be followed silently.
- [ ] **Should a section offer examples or placeholder guidance?** — **Deferred (non-blocking).** An empty box with a good placeholder is likely enough, but whether drafters know what to write is worth watching once someone other than the demo drafter uses it.

---

## ⚠️ Implementation reality: the five-stage flow is scripted, not live

**Discovered while refining this spec, and it changes how one acceptance criterion is satisfied.**

`frontend/src/features/drafting-workspace/CopilotChat.tsx` implements the five stages as **client-side scripted lifecycles** over `copilotV2Data.ts` — `runExploreTask`, `runBrainstorm`, `runDraft`, `runWrite`, `runDeliver`, each appending canned messages on timers (`CopilotChat.tsx:148-300`). The file's own docstring says so: *"A static, scripted demo (no live model)."* `streamCopilotMessage` exists in `frontend/src/lib/api.ts:418` but **no component calls it** — only `frontend/src/test/msw/handlers.ts:1608` references it.

Meanwhile `engine/copilot.py` is genuinely live: `copilot_reply`, `copilot_reply_stream` and `_system_prompt` (line 190) all work, are injected as seams on `create_app`, and back the two `/copilot` routes.

So the Playbook has **two consumers, and only one of them is a model**:

| Path | Status | How the Playbook reaches it |
| ---- | ------ | --------------------------- |
| `engine/copilot.py` → `_system_prompt` | Live model, currently unused by the V2 UI | A new `PLAYBOOK` block in the system prompt, gated to the running stage |
| `CopilotChat.tsx` scripted stages | What the demo actually runs | Each stage's scripted output visibly reflects its configured section |

Both are built. The engine path makes the feature correct the moment the V2 UI is wired to the live Copilot; the scripted path makes it demonstrable now. **Neither is a mock of the other** — the engine injection is real and unit-tested against a recorded prompt, and the scripted reflection is real rendering of persisted drafter text.

This is recorded here rather than resolved silently because it changes what "the Copilot follows my Playbook" means today, and a reader who assumed live prompting would write the wrong tests.

## Functional Requirements

- **A save is a full replacement of the four editable sections.** The form always sends all four, so an omitted key lands as `""`. What is saved is exactly what was on screen — the same discipline `put_node_metadata` uses for the nine-field profile (`engine/api.py:1434-1437`).
- **`/explore-task` has no stored field.** The payload carries `brainstorm`, `draft`, `write`, `deliver` and nothing else. A client sending `explore_task` has it **ignored, not rejected** — mirroring how `_parse_copilot_request` ignores a stale `intent` (`engine/api.py:504-507`), because a stale client should not get a 400 for a field the server no longer wants.
- **Idempotent:** the same `PUT` twice yields the same state.
- **Reads never write.** A workstream with no `playbook.json` returns four empty strings and `is_default: true`; no file is created. This is what keeps the three retired fixtures byte-identical.
- **Each stage reads only its own section.** The engine's system-prompt injection takes one section keyed by the running stage. There is no combined blob, so `deliver`'s approval layers cannot influence `draft`'s structure.
- **An empty section is a no-op**, not a warning: no `PLAYBOOK` block is added to the prompt at all when the running stage's section is empty.
- **UTF-8 on write** (`encoding="utf-8"`) per `docs/learnings/pattern-engine-artifact-writes-utf8.md`.

### Validation & Business Rules

| Rule | Enforcement |
| ---- | ----------- |
| Body must be a JSON object | `400 INVALID_PLAYBOOK` |
| Each present section must be a string | `400 INVALID_PLAYBOOK` |
| Each section ≤ 20 000 characters | `413 PLAYBOOK_TOO_LARGE` (carries `field`) |
| Unknown keys, including `explore_task` | Ignored silently |

No minimum length on any section — empty is the shipped default and a valid end state.

## Permissions & Security

- **Scope:** internal-only, same boundary as the rest of `/api/workstreams/*`.
- **`workstream_id` is resolved against the loaded workstream before any read or write**, so a `../` cannot escape `data/workstreams/`. The guard-before-write ordering is the control, exactly as in `put_node_metadata`.
- **Every section is untrusted text that reaches a system prompt.** Bounded at 20 000 characters each and injected as a delimited block. No sanitisation beyond the bound: the threat model is the drafter's own paste, not third-party injection.
- **`deliver` may contain names and email addresses the drafter types.** The tool **never transmits them** and holds no mail transport. They are free text in a workstream file, and `data/workstreams/` is a tracked path in a public repo — so the demo seed must not contain a real personal address. Use role names ("Head of Department, CMC"), not individuals' addresses.
- **Sections render as plain text** in `<textarea>` elements. No `dangerouslySetInnerHTML` on this path.

## API Design

### `GET /api/workstreams/{workstream_id}/playbook`

**Response (200):**

```json
{
  "brainstorm": "Should consent expiry differ for business customers? How does liability interact with the operational resilience PD?",
  "draft": "Follow the standard PD skeleton: 1 Introduction, 2 Applicability, 3 Legal provisions, 4 Effective date, 5 Interpretation. Number standards as S 1.1 and guidance as G 1.2.",
  "write": "Obligations read \"must\". Guidance reads \"should\". Do not introduce a defined term outside the interpretation section.",
  "deliver": "Policy sign-off by the Head of Department (CMC) first. Then Legal for the statutory basis check. Then the Deputy Governor's office, copying the platform operator liaison.",
  "updated_at": "2026-08-02T10:22:14Z",
  "is_default": false
}
```

Never saved: `{"brainstorm": "", "draft": "", "write": "", "deliver": "", "updated_at": null, "is_default": true}`.

**Errors:**
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `WORKSTREAM_NOT_FOUND` | No such workstream |

### `PUT /api/workstreams/{workstream_id}/playbook`

**Request** — all four sections, always:

```json
{
  "brainstorm": "Should consent expiry differ for business customers?",
  "draft": "Follow the standard PD skeleton, numbering standards as S 1.1.",
  "write": "Obligations read \"must\". Guidance reads \"should\".",
  "deliver": "Policy sign-off first, then Legal, then the Deputy Governor's office."
}
```

**Response (200):** the stored playbook, re-read from disk after the write rather than projected from the request — the pattern at `engine/api.py:1469-1474`, which is what makes the response provably what is stored.

**Errors:**
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `WORKSTREAM_NOT_FOUND` | No such workstream |
| 400 | `INVALID_PLAYBOOK` | Body not an object, or a section not a string — message: `"write must be a string."` with `"field": "write"` |
| 413 | `PLAYBOOK_TOO_LARGE` | A section over 20 000 characters — message: `"draft holds at most 20000 characters."` with `"field": "draft"` |

### `POST …/tasks/{node_id}/copilot` and `/copilot/stream` — modified

Both gain an optional `stage` field in the request body, one of `"brainstorm" | "draft" | "write" | "deliver"`. When present and that section is non-empty, `_system_prompt` receives the section text and appends a `PLAYBOOK` block. Absent, unrecognised, or `"explore-task"` → no block, and behaviour is byte-identical to today. **No breaking change**: an existing client that sends no `stage` gets exactly what it gets now.

## Data Model & Migrations

**`{ws}/playbook.json`** — new file, one per workstream, written on first save:

| Field | Type | Constraints | Description |
| ----- | ---- | ----------- | ----------- |
| `brainstorm` | string | ≤20 000 chars | Ideas and questions to bounce off the Copilot |
| `draft` | string | ≤20 000 chars | Template or style guide a draft should follow |
| `write` | string | ≤20 000 chars | Writing preferences and house rules |
| `deliver` | string | ≤20 000 chars | Approval conventions and routing layers |
| `updated_at` | string | ISO-8601 Z | Last save |

**No `explore_task` key**, deliberately — storing one would be the first step towards overriding what that stage reports.

**Migration notes:** none. An absent file serves four empty strings. The three retired fixtures get no file. The demo workstream ships one with real content, using role names rather than personal addresses.

## UI/Frontend Requirements

### Components

**`PlaybookTab`** — `frontend/src/features/drafting-workspace/PlaybookTab.tsx` (new, ~190 LOC)

```typescript
interface Props {
  workstreamId: string;
}
```

- Owns the `["playbook", workstreamId]` query and the save mutation.
- Renders five sections in flow order from a single ordered constant, so display order cannot drift from the Copilot's actual sequence.
- One `Save` for the whole form, disabled while nothing is dirty.

**`PlaybookSection`** — `frontend/src/features/drafting-workspace/PlaybookSection.tsx` (new, ~110 LOC)

```typescript
interface Props {
  stage: SlashCommandId;
  label: string;
  helper: string;
  value: string;
  locked?: boolean;
  onChange: (next: string) => void;
}
```

- Editable: labelled `<textarea>` with helper text.
- Locked (`/explore-task`): no textarea. A `Lock` icon, the explanation *"This stage reads the document's recorded regulatory profile."*, and a link to the node's metadata form. `aria-disabled` on the section, and it is not a form control at all — locked in the markup, not merely styled as such.

**`PlaybookDraftUpload`** — `frontend/src/features/drafting-workspace/PlaybookDraftUpload.tsx` (new, ~55 LOC)

- **Deliberately non-functional.** Renders a file input on the `/draft` section that, on selection, shows the chosen filename and the note *"Template upload is not wired up in this build — describe your template in the text above."* Nothing is read, stored, or sent.
- Precedent for a visibly-inert affordance carrying its own explanation: `EditorPane.tsx:440`, `title="Formatting is not wired up in this build"`.
- The component's docstring must state its non-functional status, so a future reader finds it documented rather than filing a bug.

**`playbookStages.ts`** — `frontend/src/features/drafting-workspace/playbookStages.ts` (new, ~35 LOC)

- The single ordered list of `{stage, label, helper, locked}`, derived from `SLASH_COMMANDS` in `copilotV2Data.ts` so the two orders cannot diverge. Shared by `PlaybookTab` and the scripted stage reflection.

**`DraftingWorkspacePage`** — `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx` (modify, ~45 LOC)

- `TabKey` → `"recommendations" | "playbook" | "copilot"`; `tabs` reordered (line 156).
- **Remove** the `reviewed` tab, the `reviewed` query, `fetchReviewedLinkages`, `withdraw`, `withdrawErrors`, `reviewedCards`, `activeCardId` and the `LinkageRefCard` render at lines 231-260.
- `frontend/src/features/drafting-workspace/LinkageRefCard.tsx` becomes unreferenced — **delete it**.

**`CopilotChat`** — `frontend/src/features/drafting-workspace/CopilotChat.tsx` (modify, ~60 LOC)

- Accept the playbook as a prop. Each scripted stage whose section is non-empty appends one message naming what it is following — e.g. *"Following your Playbook for /write: obligations read \"must\", guidance reads \"should\"."* — before its canned output.
- Each stage reads **only its own** section, so the isolation acceptance criterion holds on the scripted path too.

### User Interactions

| Action | Result |
| ------ | ------ |
| Open the Playbook tab | Five sections in flow order; the first locked |
| Edit any editable section | `Save` enables |
| `Save` | Persists; a saved timestamp appears; sections stay open |
| Attempt to edit `/explore-task` | No control to focus; the explanation and profile link are shown instead |
| Follow the profile link | Navigates to the node's metadata form |
| Choose a template file on `/draft` | Filename shown with the "not wired up" note; nothing uploads |
| Clear a section and `Save` | That stage reverts to current behaviour |
| Run a configured stage in the Copilot | The stage names the section it is following, then produces its output |

### States

- **Loading:** spinner with `role="status"`, "Loading playbook…".
- **Never saved:** four empty textareas with helper text. **No warning** — empty is the expected starting state.
- **Saving:** `Save` shows a spinner and disables; textareas stay editable.
- **Save error:** inline *"We could not save your playbook. Try again."*; **every edit preserved on screen**.
- **Locked section:** always the explanation plus the profile link, never a disabled textarea.

## Architecture Notes

- **New dependencies:** none.
- **Section order derives from `SLASH_COMMANDS`** (`copilotV2Data.ts:392-425`), not a second hand-written list. A stage added or reordered there flows through, which is what stops the Playbook drifting from the flow it configures.
- **The engine injection is additive and gated.** `_system_prompt` gains an optional parameter; with no `stage` in the request the prompt is byte-identical to today. The existing `test_copilot.py` assertions therefore stay valid unchanged.
- **The citation rules outrank the Playbook.** The `PLAYBOOK` block is appended **after** the grounding and citation rules in `_system_prompt`, and `_validate_reply` still enforces citations deterministically afterwards. A Playbook instruction cannot loosen the verbatim-citation guarantee, because that guarantee is code, not prompt text.
- **Two files, two consumers, no crossover:** `playbook.json` → Copilot; `guardrails.json` → recommendations engine. Separate modules, separate routes, no shared reader.
- **Deleting the Reviewed tab does not orphan its route.** `get_reviewed_linkages` (`engine/api.py:2095`) keeps serving accepted findings across the neighbourhood — it becomes the recommendation engine's evidence input, read server-side instead of rendered. Do not delete it.

## Exemplar Files

- `engine/api.py:1428-1474` (`put_node_metadata`) — full-replacement save of a multi-field side-file: guards first, validate before write, re-read after. The direct model for `PUT …/playbook`.
- `engine/concepts.py:180-215` (`validate_metadata`) — per-field validation returning `(status, code, message, field)`, which is how the `field` key reaches the error response.
- `engine/copilot.py:190-240` (`_system_prompt`) — where the `PLAYBOOK` block is appended, after the citation rules.
- `engine/api.py:495-517` (`_parse_copilot_request`) — the ignore-unknown-fields precedent for `explore_task` and for `stage`.
- `frontend/src/features/workstream-graph/NodeMetadataForm.tsx` — multi-field controlled form with dirty tracking, plain state and native inputs, no form library. The model for `PlaybookTab`.
- `frontend/src/features/drafting-workspace/EditorPane.tsx:440` — the inert-affordance-with-its-own-explanation precedent for the mocked upload.

## Implementation Plan

### Sub-tasks

**Task 1: `engine/playbook.py` + the two routes** — _medium_

- Files: `engine/playbook.py` (new), `engine/api.py` (modify), `engine/tests/test_api_playbook.py` (new)
- `SECTIONS = ("brainstorm", "draft", "write", "deliver")`, `load`/`save`, `GET`/`PUT` with the validation table.
- INDEPENDENT

**Task 2: Playbook injection into the Copilot system prompt** — _small_

- Files: `engine/copilot.py` (modify — optional `playbook_section` on `_system_prompt`, `copilot_reply`, `copilot_reply_stream`), `engine/api.py` (modify — read `stage`, load the section, pass it), `engine/tests/test_copilot.py` (modify)
- SEQUENTIAL (depends on Task 1)

**Task 3: API client + types** — _small_

- Files: `frontend/src/lib/api.ts` (modify — `fetchPlaybook`, `savePlaybook`), `frontend/src/lib/types.ts` (modify — `Playbook`), `frontend/src/test/msw/handlers.ts` (modify)
- SEQUENTIAL (depends on Task 1)

**Task 4: `playbookStages.ts`, `PlaybookSection`, `PlaybookDraftUpload`, `PlaybookTab`** — _large_

- Files: the four new files under `frontend/src/features/drafting-workspace/`, plus `PlaybookTab.test.tsx`
- SEQUENTIAL (depends on Task 3)

**Task 5: Tab replacement — remove Reviewed, delete `LinkageRefCard`** — _medium_

- Files: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx` (modify), `frontend/src/features/drafting-workspace/LinkageRefCard.tsx` (**delete**), `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx` (modify), `frontend/e2e/reviewed-tab.spec.ts` (**delete**)
- SEQUENTIAL (depends on Task 4)

**Task 6: Scripted stages reflect their configuration** — _medium_

- Files: `frontend/src/features/drafting-workspace/CopilotChat.tsx` (modify), `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx` (modify)
- SEQUENTIAL (depends on Task 5)

**Task 7: Demo seed + E2E** — _medium_

- Files: `data/workstreams/open-finance-pd-2026/playbook.json` (new), `frontend/e2e/playbook.spec.ts` (new)
- SEQUENTIAL (depends on Task 6)

### Negative Constraints

- Do NOT add an `explore_task` field to the stored playbook, the request shape, or the form. Locked means absent, not disabled.
- Do NOT make the template upload work. It is deliberately inert and must carry its own explanation.
- Do NOT send email, add a mail dependency, or validate an address.
- Do NOT put a real personal email address in the committed demo seed. Role names only — `data/workstreams/` is tracked in a public repo.
- Do NOT change the five stages, their order, or `isCommandUnlocked`'s gating.
- Do NOT let the Playbook weaken the citation rules. Its block goes after them, and `_validate_reply` still runs.
- Do NOT delete `get_reviewed_linkages` — it becomes the recommendation engine's evidence input.
- Do NOT write a `playbook.json` for a workstream on read, and do NOT create one for any retired fixture.
- Do NOT read `guardrails.json` from this story's code paths.

## Test Scenarios

**Test 1: Playbook defaults to empty without writing a file**

- Setup: `tmp_path` copy of `data/workstreams`; no `playbook.json`
- Action: `GET /api/workstreams/open-finance-pd-2026/playbook`
- Expected: `200`, all four sections `""`, `is_default: true`, `updated_at: null`; **no file created on disk**

**Test 2: Round-trip**

- Action: `PUT …/playbook` with all four sections populated, then `GET`
- Expected: `PUT` returns `is_default: false` with an `updated_at`; `GET` returns the same four strings

**Test 3: Save is a full replacement**

- Setup: all four saved
- Action: `PUT` with only `{"write": "Obligations read must."}`
- Expected: `write` is set; `brainstorm`, `draft` and `deliver` are `""` — a field the client omits lands empty

**Test 4: `explore_task` is ignored, not rejected**

- Action: `PUT` with `{"brainstorm": "q", "explore_task": "override the profile"}`
- Expected: `200`; the stored file has **no** `explore_task` key; `brainstorm` is `"q"`

**Test 5: Non-string section rejected with its field name**

- Action: `PUT` with `{"write": ["a"]}`
- Expected: `400 INVALID_PLAYBOOK`, message `"write must be a string."`, `field: "write"`; file unchanged

**Test 6: Oversized section rejected with its field name**

- Action: `PUT` with a 20 001-character `draft`
- Expected: `413 PLAYBOOK_TOO_LARGE`, message `"draft holds at most 20000 characters."`, `field: "draft"`; file unchanged

**Test 7: Non-object body rejected**

- Action: `PUT` with `["not", "an", "object"]`
- Expected: `400 INVALID_PLAYBOOK`

**Test 8: Unknown workstream**

- Action: `GET /api/workstreams/no-such-ws/playbook`
- Expected: `404 WORKSTREAM_NOT_FOUND`

**Test 9: Path traversal refused**

- Action: `PUT /api/workstreams/..%2F..%2Fetc/playbook` with a valid body
- Expected: `404 WORKSTREAM_NOT_FOUND`; nothing written outside `data/workstreams/`

**Test 10: Per-workstream isolation, retired fixtures untouched**

- Action: `PUT` a playbook on `open-finance-pd-2026`; `GET` on `opres-v2`
- Expected: `opres-v2` returns four empty strings and `is_default: true`; **no file created under `data/workstreams/opres-v2/`**

**Test 11: The running stage's section reaches the system prompt**

- Setup: playbook with `write` = `"Obligations read must. Guidance reads should."`
- Action: `POST …/copilot` with `{"message": "Draft clause 3.1", "stage": "write"}`, stubbing `copilot_reply_fn` to record its `system`
- Expected: the system prompt contains that sentence inside a `PLAYBOOK` block

**Test 12: Only the running stage's section is injected**

- Setup: all four sections populated with distinguishable text
- Action: `POST …/copilot` with `stage: "draft"`
- Expected: the prompt contains the `draft` text and **none of** the `brainstorm`, `write` or `deliver` text

**Test 13: An empty section adds no block**

- Setup: playbook with `write` = `""`
- Action: `POST …/copilot` with `stage: "write"`
- Expected: no `PLAYBOOK` block in the prompt

**Test 14: No `stage` leaves the prompt byte-identical**

- Setup: all four sections populated
- Action: `POST …/copilot` with no `stage`, capturing the prompt; compare against the prompt produced with no `playbook.json` at all
- Expected: the two are string-equal — proving the change is additive and the existing `test_copilot.py` assertions stay valid

**Test 15: `stage: "explore-task"` injects nothing**

- Action: `POST …/copilot` with `stage: "explore-task"`
- Expected: no `PLAYBOOK` block; no error

**Test 16: An unrecognised stage is ignored**

- Action: `POST …/copilot` with `stage: "nonsense"`
- Expected: `200`, no `PLAYBOOK` block, no error — consistent with how a stale `intent` is ignored

**Test 17: The Playbook is appended after the citation rules**

- Setup: playbook with `write` = `"Quote any clause you find useful, numbered or not."`
- Action: `POST …/copilot` with `stage: "write"`
- Expected: in the prompt string, the `PLAYBOOK` block's index is **greater than** the index of the `GROUNDING AND CITATION RULES` heading; `_validate_reply` still rejects a reply citing an ungrounded clause number

**Test 18: Tab order and no Reviewed tab (component test)**

- Action: render `DraftingWorkspacePage`
- Expected: `getAllByRole("tab")` names are `["Recommendations", "Playbook", "Copilot"]`; nothing named `/reviewed/i`

**Test 19: Locked section has no editable control (component test)**

- Action: render `PlaybookTab`, locate the `/explore-task` section
- Expected: no `textbox` role within it; the profile-link is present; the explanation text is rendered

**Test 20: Five sections in flow order (component test)**

- Action: render `PlaybookTab`
- Expected: section headings in the order `/explore-task`, `/brainstorm`, `/draft`, `/write`, `/deliver`, matching `SLASH_COMMAND_IDS`

**Test 21: Save error preserves edits (component test)**

- Setup: MSW returns `500` on `PUT …/playbook`
- Action: type into `write`, press `Save`
- Expected: an inline error appears; the typed text is still in the textarea

**Test 22: Dirty tracking (component test)**

- Action: render with a saved playbook; press `Save` without editing
- Expected: `Save` is disabled and no request is made; after one keystroke it enables

**Test 23: The upload affordance does nothing (component test)**

- Action: select a file on the `/draft` section's input
- Expected: the filename and the "not wired up" note render; **no network request**; the `draft` textarea is unchanged

**Test 24: A scripted stage names its configuration (component test)**

- Setup: MSW returns a playbook with `write` populated
- Action: render the Copilot tab and run the `/write` stage
- Expected: a message names the `/write` section before the canned output; running `/brainstorm` does not mention the `write` text

## Acceptance Criteria

- [ ] `GET` returns four empty sections and `is_default: true` when no file exists, writing nothing
- [ ] `PUT` is a full replacement; an omitted section lands empty
- [ ] `explore_task` is ignored on write and absent from storage
- [ ] Per-section validation returns the offending `field` name
- [ ] Only the running stage's section reaches the system prompt
- [ ] An empty section, an absent `stage`, `"explore-task"`, and an unrecognised stage all inject nothing
- [ ] With no `stage`, the system prompt is byte-identical to today's
- [ ] The `PLAYBOOK` block sits **after** the citation rules, and `_validate_reply` still enforces them
- [ ] Tabs read Recommendations, Playbook, Copilot; no Reviewed tab; `LinkageRefCard.tsx` and `e2e/reviewed-tab.spec.ts` deleted
- [ ] `get_reviewed_linkages` still exists and still serves accepted findings
- [ ] The `/explore-task` section has no editable control in the markup
- [ ] The template upload sends nothing and says so
- [ ] No mail transport, dependency, or address validation anywhere
- [ ] The committed demo playbook contains no personal email address
- [ ] No file is created for any retired fixture
- [ ] Engine suite passes with no model credentials

## Verification

Run the verifier skill. Locally `.venv/bin/python -m pytest engine/tests` and `cd frontend && npm run test`.

### Backend Tests

| File | Covers |
| ---- | ------ |
| `engine/tests/test_api_playbook.py` (new) | Tests 1–10 — defaults without writing, round-trip, full replacement, `explore_task` ignored, per-field validation, traversal, retired-fixture isolation |
| `engine/tests/test_copilot.py` (modify) | Tests 11–17 — stage-gated injection, isolation between sections, the additive-with-no-`stage` proof, and the citation-rules-outrank-Playbook ordering |

Test 14 is the regression guard for the whole change being additive — without it, a later edit could reorder the prompt and no test would notice.

### Manual Verification

- [ ] With `data/workstreams/open-finance-pd-2026/playbook.json` deleted, open the tab → four empty sections, no error, and **no file appears on disk**
- [ ] Save, then `git status` → only `playbook.json` is modified; no retired fixture is touched
- [ ] `grep -ri "@" data/workstreams/open-finance-pd-2026/playbook.json` → no email addresses in the committed seed

### Browser/UI Testing

Engine on `:8000`, Vite on `:5173`, `VITE_API_BASE=http://localhost:8000`.

1. Open `/workstreams/open-finance-pd-2026/tasks/open-finance-pd-2026-pd/draft` → tabs read Recommendations, Playbook, Copilot. **No Reviewed tab.**
2. Open Playbook → five sections in flow order.
3. `/explore-task` → no textarea; explanation plus profile link. Click the link → the node's metadata form.
4. Tab through the form → focus skips the locked section entirely and lands on `/brainstorm`.
5. Fill all four, `Save` → timestamp appears; reload → all four persist.
6. On `/draft`, choose a file → filename plus the "not wired up" note; nothing uploads (check the network panel).
7. Clear `write`, `Save` → the section is empty; the `/write` stage stops naming it.
8. Run `/write` in the Copilot with `write` populated → the stage names that section.
9. Run `/brainstorm` → it names only the `brainstorm` section.
10. Narrow to 375 px → sections stack and remain usable.

### E2E Tests

| Key Scenario | Test file | Assigned sub-task |
| ------------ | --------- | ----------------- |
| The Playbook replaces the Reviewed tab | `frontend/e2e/playbook.spec.ts` | Task 7 |
| One section per Copilot stage, in flow order | `frontend/e2e/playbook.spec.ts` | Task 7 |
| The first stage is locked | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Seeding the brainstorm with my own questions | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Recording who approves the draft | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Describing a template under the draft stage | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Each workstream has its own Playbook | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Every draft in a workstream shares its Playbook | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Clearing a section | `frontend/e2e/playbook.spec.ts` | Task 7 |
| A configured stage changes what the Copilot does | `frontend/e2e/playbook.spec.ts` | Task 7 |
| Each stage reads only its own section | `frontend/e2e/playbook.spec.ts` | Task 7 |

The last two are asserted against the **scripted** stage output naming its section — the honest observable behaviour today, per the reality note above. The live-model equivalents are Tests 11–13 at the prompt level. Not duplicated as E2E: validation, traversal, retired-fixture isolation, prompt ordering, and the save-error path (component test 21).

**`e2e/reviewed-tab.spec.ts` is deleted in Task 5** — the tab it covers no longer exists. Its accept-then-appears loop is preserved by `recommendations-bookmark.spec.ts` (Story 2), which walks accept → generate → bookmark → find beside the draft.

**Locator strategies:** `data-testid="playbook-section"` with `data-stage` and `data-locked`, `data-testid="playbook-save"`, `data-testid="playbook-upload"`, `data-testid="playbook-upload-note"`, `data-testid="explore-task-locked"`, `data-testid="playbook-followed"` (the scripted stage's acknowledgement). Tabs via `getByRole("tab", { name: … })`; textareas via `getByLabelText`.

**Fixture discipline:** saving writes `data/workstreams/open-finance-pd-2026/playbook.json`, a tracked path. `git checkout -- data/workstreams/open-finance-pd-2026` in `beforeEach`, as `reviewed-tab.spec.ts:47-51` does. No model credentials needed — the scripted stages make no model call.
