# Copilot v2 Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the mocked-data Copilot chat panel in `frontend/src/features/drafting-workspace/` per `docs/superpowers/specs/2026-07-30-copilot-v2-redesign-design.md` — remove the intent-picker gate in favour of a welcome screen, rename the five slash commands, and substantially deepen `/draft` (instructional outline) and `/write` (full paginated document) and `/deliver` (named-supervisor handoff), plus a tone/visual pass and a wired formatting toolbar.

**Architecture:** No new architecture — this extends the already-landed "Copilot v2" chat-stream design (`CopilotChat.tsx` owns a `useReducer` message-stream state machine; `MessageRenderer.tsx` dispatches per message kind; presentational pieces live in `copilotViews.tsx`; static demo content lives in `copilotV2Data.ts`). Two new sibling data modules (`copilotDraftOutline.ts`, `copilotFullDocument.ts`) hold the new content-heavy generators so `copilotV2Data.ts` doesn't roughly quadruple in size; both re-export through `copilotV2Data.ts` where an existing call site needs it.

**Tech Stack:** Vite + React 18 + TypeScript, Tailwind CSS + shadcn/ui primitives, Vitest + Testing Library + `msw`, DOMPurify (client) / `bleach` (server, `engine/drafts.py` — untouched).

## Global Constraints

- **Frontend only, no engine/API changes.** Everything lives under `frontend/src/features/drafting-workspace/` (plus one shared CSS file). `engine/drafts.py`'s `ALLOWED_TAGS`/`ALLOWED_ATTRS` are a real security boundary, not a nicety to loosen — see the deviation note in Task 5.
- **No live LLM calls.** Every command stays scripted/timer-based, exactly as today.
- **Verbatim citation rule (CLAUDE.md).** Every clause quote in new content must be copied character-for-character from `DRAFT_SECTIONS`' existing `sourceCitations`/`targetCitations` — never paraphrased, never invented. Where no clause supports a claim (the `breach-response` section, `sourceCitations: []`), say so explicitly.
- **No emoji, no exclamation marks in new copy.** The existing codebase has zero pictographic emoji and zero `!` in string literals (verified) — this is a forward-looking constraint on everything written in this plan, not a removal task. The `✓` (U+2713) checkmark in `ConfidenceMeter`'s `"Aligned ✓"` is retained verbatim (test-asserted at `DraftingWorkspacePage.test.tsx`) — it is not a pictographic emoji.
- **Single light theme.** Reuse existing `--primary`/`--background`/`--card`/`--muted`/`--border` HSL tokens and the `fadeSlideUp`/`shimmer`/`glowPulse`/`rotateGlow`/`floatUp`/`ringExpand`/`countGlow` keyframes already in `frontend/src/index.css`. No dark mode, no new design system.
- **`DraftingWorkspacePage.test.tsx` is updated in lockstep with every behavioural change in the task that makes it, never left red and never deferred to a final cleanup task.**
- **Commits.** Per `CLAUDE.md`, only commit or push when the user explicitly asks. Do not run `git commit` as part of executing this plan — finish a task, run its verification commands, confirm green, and stop for review. (This overrides the generic "Commit" step in the writing-plans template.)

---

## Current-state ground truth (verified 2026-07-30, not from the spec's prose alone)

A "Copilot v2" chat-stream redesign has **already landed** (untracked in git, not yet committed): `CopilotChat.tsx`, `ChatInput.tsx`, `AutocompleteMenu.tsx`, `ClarificationCard.tsx`, `CommandTranscript.tsx`, `MessageRenderer.tsx`, `copilotViews.tsx`, `copilotChatTypes.ts`, `copilotV2Data.ts` all exist, are wired together, and `CopilotTab.tsx` is now a 23-line pass-through. This matches the spec's "Current state" section closely — the five *old-named* commands (`/pull-node-metadata`, `/brainstorming`, `/skeleton`, `/build`, `/release`), the intent-picker gate, and the full test suite in `DraftingWorkspacePage.test.tsx` all exist exactly as the spec describes. `WelcomeScreen.tsx`, `copilotDraftOutline.ts`, and `copilotFullDocument.ts` genuinely do not exist yet (confirmed by glob).

Key exact facts locked in below (see file reads during planning for full source):

- `SlashCommandId = "/pull-node-metadata" | "/brainstorming" | "/skeleton" | "/build" | "/release"` in `copilotV2Data.ts:365-370`.
- `CopilotChat.initialState()` seeds `[{id:"seed-greeting", kind:"text", text: GREETING}, {id:"seed-intent", kind:"question", questionKind:"intent"}]`.
- `QuestionKind = "intent" | "leading" | "clarification"` in `copilotChatTypes.ts:63`.
- `CommandDetailKind = "metadata" | "skeleton" | "release" | null` in `copilotChatTypes.ts:44`.
- `NODE_METADATA` has 9 fields, 4 null: `empowerment_framework`, `requirement`, `effective_date`, `ismp_classification`.
- `DRAFT_SECTIONS` (7 entries, unchanged ids/titles/citations, **not modified by this plan**): `objectives`, `scope`, `tsp-governance`, `api-security`, `timeline`, `consent`, `breach-response`.
- `RELEASE_REVIEWERS: string[] = []` — removed entirely (Decision 5 replaces the reviewers-list model, doesn't relabel it).
- **`engine/drafts.py`'s server-side sanitizer** (`ALLOWED_TAGS = {h1,h2,h3,p,strong,em,u,ul,ol,li,div,span,br}`, `ALLOWED_ATTRS = {div:[class], span:[class], p:[class]}`) explicitly excludes `<style>`, `<table>`, `<blockquote>`, and any `style=` attribute — this is a real, documented security boundary ("No `<style>` ... No `<a>` ... anyone can curl this endpoint"), and expanding it is an engine change, out of scope. **This plan's generated markup (Tasks 4 and 5) uses only `div`/`span`/`p`/`strong`/`em`/`u`/`ul`/`ol`/`li`/`br` tags with `class` only on `div`/`span`/`p`, and defines all new visual styling as global CSS classes in `frontend/src/index.css` rather than inline `style=` attributes or an embedded `<style>` tag** — this is a deliberate, necessary deviation from the spec's literal `<style>`/`<table>`/`<blockquote>` code sample, preserving its visual intent without an engine change and without silent data loss on a save round-trip (bleach strips disallowed tags on every `PUT`, keeping only their text — undetectable in-session but destructive on reload).

---

### Task 1: Rename the five slash commands end-to-end

Mechanical rename pass across data, types, and call sites. No new behaviour — this is the safe foundation the other 8 tasks build on.

**Files:**
- Modify: `frontend/src/features/drafting-workspace/copilotV2Data.ts`
- Modify: `frontend/src/features/drafting-workspace/copilotChatTypes.ts`
- Modify: `frontend/src/features/drafting-workspace/CopilotChat.tsx`
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx`
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Produces: `SlashCommandId = "/explore-task" | "/brainstorm" | "/draft" | "/write" | "/deliver"`, `CommandDetailKind = "metadata" | "outline" | "deliver" | null`. Every later task's code uses these exact strings.

- [ ] **Step 1: Rename `SlashCommandId` and `SLASH_COMMANDS` in `copilotV2Data.ts`**

Replace lines 365–411:

```ts
export type SlashCommandId =
  | "/explore-task"
  | "/brainstorm"
  | "/draft"
  | "/write"
  | "/deliver";

export interface SlashCommandDef {
  id: SlashCommandId;
  label: string;
  description: string;
  /** The assistant's opening line when the command is invoked. */
  intro: string;
}

export const SLASH_COMMANDS: SlashCommandDef[] = [
  {
    id: "/explore-task",
    label: "/explore-task",
    description: "Reveal the task's regulatory profile",
    intro: "Pulling the task's regulatory profile from its connected anchor document…",
  },
  {
    id: "/brainstorm",
    label: "/brainstorm",
    description: "Pull context, then align on focus through Q&A",
    intro: "Let's align on the draft. Pulling context from the anchor documents first…",
  },
  {
    id: "/draft",
    label: "/draft",
    description: "Preview an instructional draft outline",
    intro: "Here's the outline I'd draft, grounded in the confirmed citations.",
  },
  {
    id: "/write",
    label: "/write",
    description: "Write the full draft into the editor",
    intro: "Writing the full draft into your editor now…",
  },
  {
    id: "/deliver",
    label: "/deliver",
    description: "Send the draft for review",
    intro: "Ready to send this draft for review.",
  },
];

export const SLASH_COMMAND_IDS: SlashCommandId[] = SLASH_COMMANDS.map((c) => c.id);
```

Leave `RELEASE_REVIEWERS` (lines 58–62) in place for now — `MessageRenderer.tsx`'s `ReleasePanel`, unchanged until Task 6, still consumes it, and Task 1's own test-string rename pass below leaves its assertions untouched. Deleting it here would break the build; Task 6 removes it, in the same commit that replaces `ReleasePanel` with `DeliverPanel`.

- [ ] **Step 2: Rename `CommandDetailKind` in `copilotChatTypes.ts`**

Line 44, replace:

```ts
export type CommandDetailKind = "metadata" | "outline" | "deliver" | null;
```

(`"skeleton"` → `"outline"`, `"release"` → `"deliver"` — Tasks 4 and 6 give these real content.)

- [ ] **Step 3: Rename lifecycle functions and the `runCommand` switch in `CopilotChat.tsx`**

Rename in place (bodies unchanged in this task — only ids/strings referencing old command names):
- `runPullMetadata` → `runExploreTask`, its `command:` literal `"/pull-node-metadata"` → `"/explore-task"`.
- `runBrainstorming` → `runBrainstorm`, `"/brainstorming"` → `"/brainstorm"`.
- `runSkeleton` → `runDraftOutline`, `"/skeleton"` → `"/draft"`, `detailKind: "skeleton"` → `detailKind: "outline"`.
- `runBuild` → `runWrite`, `"/build"` → `"/write"`.
- `runRelease` → `runDeliver`, `"/release"` → `"/deliver"`, `detailKind: "release"` → `detailKind: "deliver"`.

Update the switch:

```ts
function runCommand(id: SlashCommandId) {
  switch (id) {
    case "/explore-task":
      return runExploreTask();
    case "/brainstorm":
      return runBrainstorm();
    case "/draft":
      return runDraftOutline();
    case "/write":
      return runWrite();
    case "/deliver":
      return runDeliver();
  }
}
```

Update every suggestion-chip label/command pair to the new ids (bodies of these functions get richer content in Tasks 3–6, but their *chip* wiring changes now):
- `runExploreTask`'s `suggest(...)` call at the end (currently `"Start brainstorming"` / `"/brainstorming"`) → rename only, for now: `suggest([{ label: "Run /brainstorm", command: "/brainstorm" }])`, still firing immediately after the metadata reveal so the app stays green after this task. Task 3 changes *when* this suggestion fires (deferring it until the missing-fields form is submitted) — that timing change belongs there, not here.
- `finalizeBrainstorming`'s `suggest([{ label: "Run /skeleton", command: "/skeleton" }])` → `suggest([{ label: "Run /draft", command: "/draft" }])`.
- `runDraftOutline`'s `suggest([{ label: "Run /build", command: "/build" }])` → `suggest([{ label: "Run /write", command: "/write" }])`.
- `runWrite`'s `suggest([{ label: "Run /release", command: "/release" }])` → `suggest([{ label: "Run /deliver", command: "/deliver" }])`.
- `onAnswerQuestion`'s intent branch: `suggest([{ label: "Run /pull-node-metadata", command: "/pull-node-metadata" }])` → `suggest([{ label: "Run /explore-task", command: "/explore-task" }])` (this whole branch is deleted in Task 2 — leave the rename here so the app stays green in between).
- `onSend`'s nudge text: `"try /brainstorming to align on the draft, or /build to populate it. Type / to see every option."` → `"try /brainstorm to align on the draft, or /write to populate it. Type / to see every option."`

- [ ] **Step 4: Rename the `commandDetail` switch and `ReleasePanel`'s `/build` special case in `MessageRenderer.tsx`**

Line 118: `if (msg.command === "/build" && msg.status === "active")` → `if (msg.command === "/write" && msg.status === "active")`.

Line 121-141 switch: `case "skeleton":` → `case "outline":` (body unchanged for now — still the bare title list; Task 4 replaces it), `case "release":` → `case "deliver":` (body unchanged for now — still `<ReleasePanel released={h.released} onRelease={h.onRelease} />`; Task 6 replaces it).

- [ ] **Step 5: Update `DraftingWorkspacePage.test.tsx` command-id strings only**

This is a pure rename pass — no new test cases yet (those land in later tasks alongside their features). Update every literal old command id / chip label to its new name:
- `"Run /pull-node-metadata"` → `"Run /explore-task"` (2 occurrences: `reachBrainstormDone`, the tab-switching test).
- `"Start brainstorming"` → `"Run /brainstorm"` (`reachBrainstormDone`).
- `"Run /skeleton"` → `"Run /draft"` (`reachBrainstormDone`, "reveals commands one at a time").
- `"Run /build"` → `"Run /write"` (`reachBuildDone`, "reveals commands one at a time").
- `"Run /release"` → `"Run /deliver"` ("releases the draft..." test).
- `commandBlock("/skeleton")` / `commandBlock("/build")` → `commandBlock("/draft")` / `commandBlock("/write")` ("reveals commands one at a time").
- The slash-menu filter test: change `await user.type(input, "bra")` / `expect(...).toHaveTextContent("/brainstorming")` → keep typing `"bra"` (still a substring of `/brainstorm`) but assert `toHaveTextContent("/brainstorm")`.
- The regulatory-profile test: `runViaChip(user, "Run /pull-node-metadata")` → `runViaChip(user, "Run /explore-task")`, `commandBlock("/pull-node-metadata")` → `commandBlock("/explore-task")`.

Leave every other assertion (intent picker, `RELEASE_REVIEWERS`, `ReleasePanel` text) untouched here — Tasks 2, 3, and 6 own those rewrites.

- [ ] **Step 6: Run the suite and confirm it's green**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all tests in `DraftingWorkspacePage.test.tsx` pass (pure rename, no behaviour change yet).

- [ ] **Step 7: Typecheck**

Run: `cd frontend && npx tsc -b --noEmit`
Expected: no errors.

- [ ] **Step 8: Cross-check `LEADING_QUESTION` against `ANCHOR_DOCS`**

The spec calls out `/brainstorm`'s leading question as needing a check that the named documents match the fixture (Decision: "`/brainstorm`" section). Read `copilotV2Data.ts`'s `LEADING_QUESTION` (line 76-77) and `ANCHOR_DOCS` (line 69-74) side by side: `LEADING_QUESTION` already names "the Open Finance PD . 2026", "the 2025 Exposure Draft", "the HKMA Open API Framework", "BIS Papers 168", and "RMiT 2025" — this matches `ANCHOR_DOCS`'s four entries (`ED Open Finance 2025`, `HKMA Open API Framework`, `BIS Papers 168`, `RMiT 2025`) exactly. No change needed; this step is a confirmation, not an edit — if a future data change to `ANCHOR_DOCS` ever drifts from this wording, that's the signal to revisit `LEADING_QUESTION`.

---

### Task 2: Remove the intent picker, add `WelcomeScreen`

**Files:**
- Create: `frontend/src/features/drafting-workspace/WelcomeScreen.tsx`
- Modify: `frontend/src/features/drafting-workspace/CopilotChat.tsx`
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx`
- Modify: `frontend/src/features/drafting-workspace/copilotChatTypes.ts`
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Consumes: `SlashCommandId` from `./copilotV2Data` (Task 1).
- Produces: `WelcomeScreen({ onRunCommand }: { onRunCommand: (id: SlashCommandId) => void })`. Rendered inside `CopilotChat.tsx` when `state.messages.length === 0` — no other file mounts it (the spec's file list names `DraftingWorkspacePage.tsx` for this, but that component has no access to the chat's message state; `CopilotChat.tsx` is the only place `messages.length` is known, so it owns the mount).

- [ ] **Step 1: Write `WelcomeScreen.tsx`**

```tsx
import type { SlashCommandId } from "./copilotV2Data";

interface QuickAction {
  label: string;
  command: SlashCommandId;
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: "Explore Task", command: "/explore-task" },
  { label: "Brainstorm", command: "/brainstorm" },
  { label: "Draft Outline", command: "/draft" },
  { label: "Write Document", command: "/write" },
];

/** The Copilot's entry point — shown whenever the conversation has no
 *  messages yet. Replaces the old greeting + intent-picker question: the
 *  four quick actions here are the sole way in, alongside typing the
 *  matching slash command directly. */
export function WelcomeScreen({
  onRunCommand,
}: {
  onRunCommand: (id: SlashCommandId) => void;
}) {
  return (
    <div
      data-testid="copilot-welcome"
      className="flex h-full flex-col items-center justify-center gap-6 px-4 text-center"
    >
      <div>
        <h2 className="text-lg font-semibold text-foreground">Welcome, Aisyah.</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          I am your drafting assistant for the Open Finance PD · 2026 workstream.
        </p>
      </div>
      <div className="grid w-full max-w-sm grid-cols-2 gap-2.5">
        {QUICK_ACTIONS.map((a) => (
          <button
            key={a.command}
            type="button"
            data-testid="welcome-quick-action"
            onClick={() => onRunCommand(a.command)}
            className="rounded-lg border-l-2 border-primary/60 bg-card px-3 py-2.5 text-left text-xs font-semibold text-foreground shadow-sm transition hover:bg-accent"
          >
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Shrink `QuestionKind` in `copilotChatTypes.ts`**

Line 63: `export type QuestionKind = "leading" | "clarification";` (`"intent"` removed — there is no more intent question anywhere).

- [ ] **Step 3: Gate `CopilotChat.tsx` on `messages.length === 0`, remove the intent seed**

Replace `initialState()`:

```ts
function initialState(): ChatState {
  return {
    messages: [],
    released: false,
    expandedCommands: new Set(),
  };
}
```

(Delete the `GREETING` constant entirely — its job is now done by `WelcomeScreen`'s own copy.)

Delete the intent branch from `onAnswerQuestion` (it can never fire now — no `"intent"` question is ever appended):

```ts
function onAnswerQuestion(msg: QuestionMsg, answer: string) {
  update(msg.id, { answered: answer });
  if (msg.questionKind === "leading") {
    append({
      id: nextId(),
      kind: "question",
      questionKind: "clarification",
      questionId: CLARIFICATION_QUESTIONS[0].id,
    });
    return;
  }
  const idx = CLARIFICATION_QUESTIONS.findIndex((q) => q.id === msg.questionId);
  const next = CLARIFICATION_QUESTIONS[idx + 1];
  if (next) {
    append({
      id: nextId(),
      kind: "question",
      questionKind: "clarification",
      questionId: next.id,
    });
  } else {
    finalizeBrainstorming();
  }
}
```

Replace the return block's message-list rendering to gate on `WelcomeScreen` and give every message a `fadeSlideUp` entry (folds in the "every message keeps its fadeSlideUp entry" visual requirement, since this is the one place that already needed restructuring):

```tsx
import { WelcomeScreen } from "./WelcomeScreen";
// ...
return (
  <div className="flex h-full flex-col" data-testid="copilot-chat">
    <div
      ref={scrollRef}
      className="flex-1 space-y-3 overflow-y-auto px-1 pb-2"
      aria-label="Copilot conversation"
    >
      {state.messages.length === 0 ? (
        <WelcomeScreen onRunCommand={runCommand} />
      ) : (
        <>
          <button
            type="button"
            onClick={reset}
            className="flex items-center gap-1.5 px-1 text-[11px] font-medium text-muted-foreground hover:text-foreground"
          >
            <RotateCcw className="h-3 w-3" />
            Start over
          </button>
          {state.messages.map((msg) => (
            <div
              key={msg.id}
              style={{ animation: "fadeSlideUp 0.4s var(--ease-out-expo) both" }}
            >
              <MessageRenderer msg={msg} handlers={handlers} />
            </div>
          ))}
        </>
      )}
    </div>

    <ChatInput onRunCommand={runCommand} onSend={onSend} />
  </div>
);
```

Delete the now-unused `started` variable (the line above the `return`) — the same `state.messages.length === 0` check now serves both purposes directly.

- [ ] **Step 4: Remove the `"intent"` branch from `MessageRenderer.tsx`**

Delete the `COPILOT_INTENT_LABELS`/`COPILOT_INTENTS` import (line 28) and the `INTENT_OPTIONS` constant (line 36). Simplify `questionParts`:

```ts
function questionParts(msg: QuestionMsg): { prompt: string; options: string[] } {
  if (msg.questionKind === "leading") {
    return { prompt: LEADING_QUESTION, options: LEADING_OPTIONS };
  }
  const q = CLARIFICATION_QUESTIONS.find((c) => c.id === msg.questionId);
  return { prompt: q?.prompt ?? "", options: q?.options ?? [] };
}
```

- [ ] **Step 5: Update `DraftingWorkspacePage.test.tsx` for the welcome screen**

Replace the test `"opens with a chat stream, an input, and asks the intent as vertical options"` with:

```tsx
it("opens on a welcome screen with four quick actions, no intent question", async () => {
  const user = userEvent.setup();
  await openCopilot(user);

  expect(screen.getByTestId("copilot-chat")).toBeInTheDocument();
  expect(screen.getByTestId("chat-input")).toBeInTheDocument();
  expect(screen.getByTestId("copilot-welcome")).toBeInTheDocument();

  const actions = screen.getAllByTestId("welcome-quick-action");
  expect(actions).toHaveLength(4);
  expect(actions.map((a) => a.textContent)).toEqual([
    "Explore Task",
    "Brainstorm",
    "Draft Outline",
    "Write Document",
  ]);
  expect(screen.queryByText("What are you drafting?")).not.toBeInTheDocument();
});

it("running a quick action starts the conversation and hides the welcome screen", async () => {
  const user = userEvent.setup();
  await openCopilot(user);

  await user.click(screen.getByRole("button", { name: "Explore Task" }));

  expect(screen.queryByTestId("copilot-welcome")).not.toBeInTheDocument();
  await screen.findByTestId("command-step", undefined, THINKING_WAIT);
});
```

Delete the `answerIntent` helper and every call to it. Rewrite `reachBrainstormDone` to start from a quick action instead of answering an intent question (the missing-fields form step is added in Task 3 — for now, since Task 1 kept the immediate post-metadata suggestion chip, this stays a direct chip click):

```tsx
async function reachBrainstormDone(
  user: ReturnType<typeof userEvent.setup>,
) {
  await user.click(screen.getByRole("button", { name: "Explore Task" }));
  await runViaChip(user, "Run /brainstorm");
  await answer(user, LEADING_OPTIONS[0], LEADING_OPTIONS[0]);
  for (const q of CLARIFICATION_QUESTIONS) {
    await answer(user, q.prompt, q.options[0]);
  }
  await screen.findByRole("button", { name: "Run /draft" }, THINKING_WAIT);
}
```

Update the tab-switching test `"keeps the Copilot conversation across a tab switch"` to start from the quick action instead of answering intent:

```tsx
it("keeps the Copilot conversation across a tab switch", async () => {
  const user = userEvent.setup();
  await loadWorkspace();
  await user.click(screen.getByRole("tab", { name: /Copilot/ }));
  await screen.findByTestId("copilot-chat");

  await user.click(screen.getByRole("button", { name: "Explore Task" }));
  await screen.findByTestId("command-step", undefined, THINKING_WAIT);

  await user.click(screen.getByRole("tab", { name: /Reviewed Findings/ }));
  await user.click(screen.getByRole("tab", { name: /Copilot/ }));

  // The conversation is intact — not reset to the welcome screen.
  expect(screen.queryByTestId("copilot-welcome")).not.toBeInTheDocument();
  expect(screen.getByTestId("command-step")).toBeInTheDocument();
});
```

Update `"starts over to a fresh conversation"`:

```tsx
it("starts over to a fresh conversation", async () => {
  const user = userEvent.setup();
  await openCopilot(user);
  await user.click(screen.getByRole("button", { name: "Explore Task" }));
  await screen.findByTestId("command-step", undefined, THINKING_WAIT);

  await user.click(screen.getByRole("button", { name: "Start over" }));

  await waitFor(() => {
    expect(screen.getByTestId("copilot-welcome")).toBeInTheDocument();
    expect(screen.queryByTestId("command-step")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2 (verification): Run the suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass. `npx tsc -b --noEmit` clean.

---

### Task 3: `/explore-task`'s missing-fields form

**Files:**
- Modify: `frontend/src/features/drafting-workspace/copilotV2Data.ts` (add `MISSING_FIELDS`)
- Modify: `frontend/src/features/drafting-workspace/copilotViews.tsx` (`NodeMetadataList` override support)
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx` (new `MissingFieldsForm`, wire into `commandDetail`)
- Modify: `frontend/src/features/drafting-workspace/CopilotChat.tsx` (resolved-fields state, defer the `/brainstorm` suggestion)
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Consumes: `NODE_METADATA` (Task 1's copy, unchanged shape), `MessageHandlers` (Task 1).
- Produces: `MISSING_FIELDS: {key,label,placeholder}[]` from `copilotV2Data.ts`. `MessageHandlers.resolvedFields: Record<string,string>` and `MessageHandlers.onSubmitMissingFields: (values: Record<string,string>) => void`, consumed by `NodeMetadataList({ overrides })` (`copilotViews.tsx`) in Task 4+ too.

- [ ] **Step 1: Add `MISSING_FIELDS` to `copilotV2Data.ts`**

Insert after the `NODE_METADATA` block:

```ts
export interface MissingField {
  key: string;
  label: string;
  placeholder: string;
}

/** One text input per NODE_METADATA field with value: null, shown once
 *  /explore-task has revealed the profile. Keys must match NODE_METADATA
 *  keys exactly — that's how a submitted value overrides its null field. */
export const MISSING_FIELDS: MissingField[] = [
  { key: "empowerment_framework", label: "Empowerment framework", placeholder: "e.g. Financial Services Act 2013, Section 47" },
  { key: "requirement", label: "Requirement", placeholder: "e.g. Mandatory compliance for all licensed banks" },
  { key: "effective_date", label: "Effective date", placeholder: "e.g. 2028-01-01" },
  { key: "ismp_classification", label: "ISMP classification", placeholder: "e.g. Restricted — Internal Use" },
];
```

- [ ] **Step 2: Add `overrides` support to `NodeMetadataList` in `copilotViews.tsx`**

Replace the function:

```tsx
/** The task's regulatory profile, revealed by /explore-task. A null value
 *  renders as an honest "Not available" unless the drafter has since
 *  resolved it through the missing-fields form (`overrides`), in which case
 *  it renders as a confirmed row instead. */
export function NodeMetadataList({
  overrides,
}: {
  overrides?: Record<string, string>;
} = {}) {
  return (
    <dl className="space-y-2 text-xs">
      {NODE_METADATA.map((f) => {
        const resolved = f.value === null ? overrides?.[f.key] : undefined;
        const value = resolved ?? f.value;
        return (
          <div key={f.key}>
            <dt className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              {f.label}
            </dt>
            <dd className="mt-0.5 text-foreground">
              {value === null ? (
                <span className="italic text-muted-foreground">Not available</span>
              ) : Array.isArray(value) ? (
                value.join(", ")
              ) : (
                value
              )}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
```

- [ ] **Step 3: Add `MissingFieldsForm` and wire it into `commandDetail` in `MessageRenderer.tsx`**

Add `import { useState } from "react";` and `MISSING_FIELDS` to the `copilotV2Data` import list. Add the component (near `ReleasePanel`):

```tsx
function MissingFieldsForm({
  onSubmit,
}: {
  onSubmit: (values: Record<string, string>) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const allFilled = MISSING_FIELDS.every((f) => (values[f.key] ?? "").trim().length > 0);

  return (
    <form
      data-testid="missing-fields-form"
      className="space-y-2 rounded-lg border border-dashed border-border/60 bg-muted/30 p-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (allFilled) onSubmit(values);
      }}
    >
      <p className="text-xs text-foreground">
        Some fields could not be resolved. Please provide the following to improve your draft:
      </p>
      {MISSING_FIELDS.map((f) => (
        <div key={f.key} className="space-y-1">
          <label
            htmlFor={`missing-${f.key}`}
            className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
          >
            {f.label}
          </label>
          <input
            id={`missing-${f.key}`}
            aria-label={f.label}
            placeholder={f.placeholder}
            value={values[f.key] ?? ""}
            onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
            className="w-full rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
          />
        </div>
      ))}
      <button
        type="submit"
        disabled={!allFilled}
        className="rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-40"
      >
        Submit
      </button>
    </form>
  );
}
```

Update `MessageHandlers` and the `"metadata"` case:

```ts
export interface MessageHandlers {
  onAnswerQuestion: (msg: QuestionMsg, answer: string) => void;
  onRunCommand: (id: SlashCommandId) => void;
  onUseSuggestion: (msg: SuggestionMsg, command?: SlashCommandId) => void;
  released: boolean;
  onRelease: () => void;
  expandedCommands: Set<string>;
  onToggleCommand: (id: string) => void;
  resolvedFields: Record<string, string>;
  onSubmitMissingFields: (values: Record<string, string>) => void;
}
```

```tsx
case "metadata":
  return (
    <div className="space-y-2">
      <ContextCard />
      <NodeMetadataList overrides={h.resolvedFields} />
      {Object.keys(h.resolvedFields).length === 0 && (
        <MissingFieldsForm onSubmit={h.onSubmitMissingFields} />
      )}
    </div>
  );
```

- [ ] **Step 4: Wire `resolvedFields` state and defer the `/brainstorm` suggestion in `CopilotChat.tsx`**

Add to `ChatState`:

```ts
interface ChatState {
  messages: ChatMsg[];
  released: boolean;
  expandedCommands: Set<string>;
  resolvedFields: Record<string, string>;
}
```

Add to `initialState()`: `resolvedFields: {}`. Add a reducer action:

```ts
type Action =
  | { type: "append"; msg: ChatMsg }
  | { type: "update"; id: string; patch: MsgPatch }
  | { type: "release" }
  | { type: "resolve-fields"; values: Record<string, string> }
  | { type: "toggle-command"; id: string }
  | { type: "reset"; state: ChatState };
```

```ts
case "resolve-fields":
  return { ...state, resolvedFields: { ...state.resolvedFields, ...action.values } };
```

Change `runExploreTask` so it no longer immediately suggests `/brainstorm` — it now stops after the profile reveal, and add `onSubmitMissingFields`:

```ts
function runExploreTask() {
  const cmdId = nextId();
  append({
    id: cmdId,
    kind: "command",
    command: "/explore-task",
    status: "active",
    statusLine: "Pulling the task's regulatory profile…",
    detailKind: null,
  });
  later(() => {
    update(cmdId, {
      status: "done",
      statusLine: `${METADATA_AVAILABLE} of ${NODE_METADATA.length} fields found on the connected anchor document.`,
      detailKind: "metadata",
    });
    append({
      id: nextId(),
      kind: "text",
      text: "Here's the task's regulatory profile — task type through legal basis. Fields with no honest source read \"Not available\" rather than a guess.",
    });
  }, METADATA_REVEAL_MS);
}

function onSubmitMissingFields(values: Record<string, string>) {
  dispatch({ type: "resolve-fields", values });
  append({
    id: nextId(),
    kind: "text",
    text: "Thanks — I've folded those into the task's profile.",
  });
  suggest([{ label: "Run /brainstorm", command: "/brainstorm" }]);
}
```

Add `onSubmitMissingFields` and `resolvedFields: state.resolvedFields` to the `handlers` object.

- [ ] **Step 5: Update tests in `DraftingWorkspacePage.test.tsx`**

Add `MISSING_FIELDS` to the `copilotV2Data` import list. Update `reachBrainstormDone` to fill and submit the form before the `/brainstorm` chip appears:

```tsx
async function fillMissingFields(user: ReturnType<typeof userEvent.setup>) {
  const form = await screen.findByTestId("missing-fields-form", undefined, THINKING_WAIT);
  for (const f of MISSING_FIELDS) {
    await user.type(within(form).getByLabelText(f.label), `Test value for ${f.key}`);
  }
  await user.click(within(form).getByRole("button", { name: "Submit" }));
}

async function reachBrainstormDone(
  user: ReturnType<typeof userEvent.setup>,
) {
  await user.click(screen.getByRole("button", { name: "Explore Task" }));
  await fillMissingFields(user);
  await runViaChip(user, "Run /brainstorm");
  await answer(user, LEADING_OPTIONS[0], LEADING_OPTIONS[0]);
  for (const q of CLARIFICATION_QUESTIONS) {
    await answer(user, q.prompt, q.options[0]);
  }
  await screen.findByRole("button", { name: "Run /draft" }, THINKING_WAIT);
}
```

Update the tab-switching test's quick-action step the same way (it only needs the command block to exist, not a completed form, so it can stay as-is — verify it still passes since it only asserts on `command-step`, not on the suggestion chip).

Add a new test for the form itself, in the `"DraftingWorkspacePage — Copilot chat"` describe block:

```tsx
it("shows a missing-fields form after /explore-task, and resolves nulls on submit", async () => {
  const user = userEvent.setup();
  await openCopilot(user);
  await user.click(screen.getByRole("button", { name: "Explore Task" }));

  const block = await waitFor(() => {
    const el = commandBlock("/explore-task");
    expect(el).toBeTruthy();
    return el!;
  }, THINKING_WAIT);
  const nullFieldLabels = NODE_METADATA.filter((f) => f.value === null).map((f) => f.label);
  expect(nullFieldLabels.length).toBeGreaterThan(0);
  for (const label of nullFieldLabels) {
    expect(within(block).getAllByText("Not available").length).toBeGreaterThan(0);
  }

  await fillMissingFields(user);

  await waitFor(() => {
    expect(screen.queryByTestId("missing-fields-form")).not.toBeInTheDocument();
  });
  expect(within(block).queryAllByText("Not available")).toHaveLength(0);
  await screen.findByRole("button", { name: "Run /brainstorm" }, THINKING_WAIT);
}, 15000);
```

- [ ] **Step 6: Run the suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass, including the new test. `npx tsc -b --noEmit` clean.

---

### Task 4: `/draft` — instructional outline (new `copilotDraftOutline.ts` module + `DraftInstructionCard`)

**Files:**
- Create: `frontend/src/features/drafting-workspace/copilotDraftOutline.ts`
- Modify: `frontend/src/features/drafting-workspace/copilotViews.tsx` (`DraftInstructionCard`)
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx` (`"outline"` detail case)
- Modify: `frontend/src/features/drafting-workspace/CopilotChat.tsx` (`runDraftOutline` inserts guidance blocks)
- Modify: `frontend/src/features/drafting-workspace/copilotV2Data.ts` (re-export `buildDraftOutline`)
- Modify: `frontend/src/index.css` (`.draft-guidance-block` class)
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Produces: `DraftOutlineSection { id, title, description, bullets, guidanceNote }`, `DRAFT_OUTLINE_SECTIONS: DraftOutlineSection[]` (8 entries, order: `executive-summary`, then the 7 `DRAFT_SECTIONS` ids in their existing order), `buildDraftOutline(): string` — all from `copilotDraftOutline.ts`. Task 5's `copilotFullDocument.ts` imports `DRAFT_OUTLINE_SECTIONS` from here to drive its page count and headings.
- **Deviation note (see Global Constraints):** `.draft-guidance-block`'s `background`/`border-left` are a CSS class in `index.css`, not an inline `style=` attribute — `engine/drafts.py`'s `ALLOWED_ATTRS` only allows `class` on `div`, never `style`, on any tag.

- [ ] **Step 1: Write `copilotDraftOutline.ts`**

```ts
export interface DraftOutlineSection {
  id: string;
  title: string;
  description: string;
  bullets: string[];
  guidanceNote: string;
}

/** The instructional outline /draft renders and inserts into the editor —
 *  one `.draft-guidance-block` per section, real editable content the
 *  drafter replaces by clicking and typing, not an HTML `placeholder`.
 *  `executive-summary` has no DRAFT_SECTIONS counterpart (Decision 4); the
 *  other 7 ids match DRAFT_SECTIONS exactly, in the same order. */
export const DRAFT_OUTLINE_SECTIONS: DraftOutlineSection[] = [
  {
    id: "executive-summary",
    title: "Executive Summary",
    description:
      "A prose synthesis of why this PD exists and what it changes, written last but read first.",
    bullets: [
      "State the policy objective in one paragraph: safer, consent-driven data sharing for banking customers.",
      "Name the anchor documents this PD consolidates and benchmarks against — ED Open Finance 2025, HKMA Open API Framework, BIS Papers 168, RMiT 2025.",
      "Flag the two areas where this PD goes further than its anchors: the mandated consent dashboard and the breach-response plan.",
      "Keep it citation-free — this section previews the draft, it does not itself make a clause-backed claim.",
    ],
    guidanceNote:
      "Write this section last, once every body section below is settled — an executive summary that outruns the draft it summarises is a common review-cycle defect.",
  },
  {
    id: "objectives",
    title: "Policy Objectives and Legal Basis",
    description:
      "Ground the PD's purpose in FSA 2013 and the customer-benefit framing both anchor documents already share.",
    bullets: [
      "Open with the FSA 2013 empowerment basis once the drafter confirms it via /explore-task.",
      "Mirror ED Open Finance 2025 §1.2's consent-driven framing — both documents agree here (aligns-with).",
      "Cite HKMA Open API Framework §8.1 as external validation that the same objective is shared regionally.",
      "State the applicability upfront: licensed banks and eligible data providers, per the task's regulatory profile.",
    ],
    guidanceNote:
      "Consider mirroring the exact language from ED Open Finance 2025 §1.2 — reviewers will look for continuity of intent, not novelty, on legal basis.",
  },
  {
    id: "scope",
    title: "Scope of Application",
    description:
      "Define \"scope of prescribed information\" precisely — this is the one area where BNM's definition is broader than HKMA's.",
    bullets: [
      "Reproduce ED Open Finance 2025 §11(a)-(g)'s defined-terms list rather than paraphrasing it.",
      "Note explicitly where this differs from HKMA §11.1's narrower \"read-only product and service information\" scope.",
      "Decide, per the drafter's earlier answer, whether scope covers individual customers, SME customers, or both.",
      "Avoid silently narrowing scope to match HKMA — the difference is intentional, not a drafting gap.",
    ],
    guidanceNote:
      "This section differs-on by design — do not soften the wider BNM scope to match HKMA's narrower one without a documented reason.",
  },
  {
    id: "tsp-governance",
    title: "TSP/TPP Governance",
    description:
      "Set out technology-operations and third-party governance obligations for participating FSPs.",
    bullets: [
      "Anchor the section on ED Open Finance 2025 §12.2's technology-operations-management language.",
      "Reference HKMA §9.3's TSP governance model as the aligned regional comparator.",
      "Reflect the drafter's brainstorming answer on the shared-baseline vs direct-obligation assessment model.",
      "Cross-reference the API Security section below rather than duplicating its control list here.",
    ],
    guidanceNote:
      "Both anchors agree here (aligns-with) — resist the urge to add net-new obligations that neither document supports.",
  },
  {
    id: "api-security",
    title: "API Security",
    description:
      "Set uniform cyber-risk and API security controls, tightened relative to HKMA's phased-by-category model.",
    bullets: [
      "Lead with ED Open Finance 2025 §12.2-12.3's uniform cyber-risk and API security control requirement.",
      "Contrast HKMA §12's four-category phased protection model as the looser comparator being tightened against.",
      "Reflect the drafter's chosen security-control model from the clarification round (uniform, phased, or uniform-now-phased-later).",
      "Call out digital fraud detection and network security explicitly — both named in §12.2-12.3.",
    ],
    guidanceNote:
      "This section tightens relative to its anchor (differs-on / tighten) — state plainly that uniform controls apply from commencement, not phased in by category.",
  },
  {
    id: "timeline",
    title: "Implementation Timeline",
    description:
      "Fix commencement dates against Appendix 2 — a deliberate move from HKMA's voluntary phasing to a mandated timeline.",
    bullets: [
      "State the 1 January 2028 commencement date for document submission and single-account-view interfaces per ED Open Finance 2025 §9.1-9.2.",
      "Note HKMA §8.2's collaborative, non-mandatory phasing as the comparator this PD deliberately moves away from.",
      "Confirm from §14 whether the 2028 cohort covers individual customers, SME customers, or both, per the drafter's scope decision.",
      "Render the phase-by-phase commencement dates as a table, not prose — this is the one section with a structured timeline.",
    ],
    guidanceNote:
      "This section loosens relative to HKMA's non-mandatory comparator (differs-on / loosen) even as it tightens BNM's own commencement certainty — flag both directions for the reviewing manager.",
  },
  {
    id: "consent",
    title: "Consumer Consent",
    description:
      "Require explicit, separate consent before any third-party disclosure — an area both anchors already agree on.",
    bullets: [
      "Anchor on ED Open Finance 2025 §6's separate-and-distinct consent requirement for third-party disclosure.",
      "Cite HKMA §34.3.2(i) as the aligned comparator on explicit customer-facing consent language.",
      "Reflect the drafter's chosen approach to the mandated real-time consent dashboard (§10.4) here, or defer detail to the next section.",
      "Keep consent language customer-facing and plain — this clause is read by compliance officers, not just lawyers.",
    ],
    guidanceNote:
      "Both anchors agree here (aligns-with) — this is a section to keep tight and uncontroversial, not to expand.",
  },
  {
    id: "breach-response",
    title: "Consent Dashboard and Breach Response",
    description:
      "The one section with no HKMA equivalent — write it as new obligation, not as a gap to be quietly filled.",
    bullets: [
      "State the real-time consent dashboard requirement from ED Open Finance 2025 §10.4 in full, per the drafter's decision to keep, soften, or research it further.",
      "Draft the breach handling and response plan required by §11.12 — theft, loss, misuse, or unauthorised access — with explicit escalation procedures and a named line of responsibility.",
      "Set the notification timeline the drafter chose in the clarification round (a fixed window, principles-based, or aligned to RMiT incident rules).",
      "State explicitly that no equivalent clause exists in HKMA Open API Framework — this is silent-on, not a citation to invent.",
    ],
    guidanceNote:
      "No matching source clause exists for this section (silent-on) — draft it as considered new policy, and say so, rather than implying HKMA precedent that isn't there.",
  },
];

function guidanceBlock(section: DraftOutlineSection): string {
  const bullets = section.bullets.map((b) => `<li>${b}</li>`).join("");
  return [
    `<div class="draft-guidance-block">`,
    `<p><strong>${section.title}</strong></p>`,
    `<p>${section.description}</p>`,
    `<ul>${bullets}</ul>`,
    `<p><em>${section.guidanceNote}</em></p>`,
    `</div>`,
  ].join("");
}

/** One editable `.draft-guidance-block` div per section, concatenated —
 *  real content the drafter overwrites by clicking and typing, never an
 *  HTML `placeholder` attribute. Uses only div/p/ul/li/strong/em, all
 *  already allowed by both the client (DOMPurify) and server (bleach,
 *  engine/drafts.py) sanitizers. */
export function buildDraftOutline(): string {
  return DRAFT_OUTLINE_SECTIONS.map(guidanceBlock).join("");
}
```

- [ ] **Step 2: Add `.draft-guidance-block` to `frontend/src/index.css`**

Inside the existing `@layer components` block (after `.glass`):

```css
  /* /draft's instructional outline blocks, inserted into the editor. A CSS
     class, not an inline `style=` attribute — engine/drafts.py's server-side
     sanitizer only allows `class` on div/span/p, never `style`, on any
     save round-trip. */
  .draft-guidance-block {
    background: #EBF5FF;
    border-left: 3px solid #93C5FD;
    padding: 12px 16px;
    margin-bottom: 16px;
  }
```

- [ ] **Step 3: Add `DraftInstructionCard` to `copilotViews.tsx`**

Add the import `import type { DraftOutlineSection } from "./copilotDraftOutline";` and the component (after `NodeMetadataList`):

```tsx
/** One card in the /draft outline preview — bold title, one-sentence
 *  description, 3-4 "what to write" bullets, and an italic guidance note.
 *  Purely instructional; the editable content this previews is inserted
 *  separately via buildDraftOutline(). */
export function DraftInstructionCard({ section }: { section: DraftOutlineSection }) {
  return (
    <article
      data-testid="draft-instruction-card"
      className="rounded-lg border border-border/60 bg-card p-3 shadow-sm"
    >
      <h4 className="text-sm font-semibold text-foreground">{section.title}</h4>
      <p className="mt-1 text-xs text-muted-foreground">{section.description}</p>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-foreground">
        {section.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-2 text-[11px] italic text-muted-foreground">{section.guidanceNote}</p>
    </article>
  );
}
```

- [ ] **Step 4: Re-export `buildDraftOutline` from `copilotV2Data.ts`**

Add near the bottom (after the `Mentionable` block, or right after the `buildFullDraft` export once Task 5 moves it — for this task, add standalone):

```ts
export { buildDraftOutline } from "./copilotDraftOutline";
```

- [ ] **Step 5: Wire `/draft` in `MessageRenderer.tsx` and `CopilotChat.tsx`**

`MessageRenderer.tsx`: import `DRAFT_OUTLINE_SECTIONS` from `./copilotDraftOutline` and `DraftInstructionCard` from `./copilotViews`. Replace the `"outline"` case:

```tsx
case "outline":
  return (
    <div className="space-y-2">
      {DRAFT_OUTLINE_SECTIONS.map((s) => (
        <DraftInstructionCard key={s.id} section={s} />
      ))}
    </div>
  );
```

`CopilotChat.tsx`: import `buildDraftOutline` (already imports `buildFullDraft` from `copilotV2Data`, add alongside it) and `DRAFT_OUTLINE_SECTIONS` — actually, since the section count is display-only, import it from `./copilotDraftOutline` directly. Replace `runDraftOutline`:

```ts
function runDraftOutline() {
  insertRef.current(buildDraftOutline());
  append({
    id: nextId(),
    kind: "command",
    command: "/draft",
    status: "done",
    statusLine: `Outline ready — ${DRAFT_OUTLINE_SECTIONS.length} sections.`,
    detailKind: "outline",
  });
  append({
    id: nextId(),
    kind: "text",
    text: "I've outlined the draft in your editor — replace each guidance block with your own drafting.",
  });
  suggest([{ label: "Run /write", command: "/write" }]);
}
```

- [ ] **Step 6: Update `DraftingWorkspacePage.test.tsx`**

Add `import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";` and add a test in the Copilot chat describe block:

```tsx
it("renders and inserts the instructional draft outline on /draft", async () => {
  const user = userEvent.setup();
  await openCopilot(user);
  await reachBrainstormDone(user);
  await runViaChip(user, "Run /draft");

  const cards = await screen.findAllByTestId("draft-instruction-card", undefined, THINKING_WAIT);
  expect(cards).toHaveLength(DRAFT_OUTLINE_SECTIONS.length);
  expect(cards[0]).toHaveTextContent("Executive Summary");

  const surface = screen.getByTestId("draft-surface");
  await waitFor(() => {
    expect(surface.querySelectorAll(".draft-guidance-block").length).toBe(
      DRAFT_OUTLINE_SECTIONS.length,
    );
  });
}, 25000);
```

- [ ] **Step 7: Run the suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass, including the new `/draft` test. `npx tsc -b --noEmit` clean.

---

### Task 5: `/write` — full paginated document (new `copilotFullDocument.ts` module)

The largest task. Produces the 8-12 page BNM-styled document per the spec, using only server-allowed tags/attributes (see Global Constraints deviation note).

**Files:**
- Create: `frontend/src/features/drafting-workspace/copilotFullDocument.ts`
- Modify: `frontend/src/features/drafting-workspace/copilotV2Data.ts` (remove local `buildSectionSnippet`/`buildFullDraft`, re-export from the new module)
- Modify: `frontend/src/features/drafting-workspace/copilotChatTypes.ts` (`BannerMsg`)
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx` (`"banner"` case)
- Modify: `frontend/src/features/drafting-workspace/CopilotChat.tsx` (`runWrite`, `onDismissBanner`)
- Modify: `frontend/src/index.css` (`.bnm-*` classes)
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Consumes: `DRAFT_SECTIONS`, `WORKSTREAM_CONTEXT`, `ClauseCitation`, `DraftSection` from `./copilotV2Data`; `DRAFT_OUTLINE_SECTIONS` from `./copilotDraftOutline` (Task 4).
- Produces: `buildFullDraft(): string` from `copilotFullDocument.ts`, re-exported from `copilotV2Data.ts` unchanged in call signature (Task 1's `CopilotChat.tsx` import site does not change).

- [ ] **Step 1: Add the `.bnm-*` CSS classes to `frontend/src/index.css`**

Inside the existing `@layer components` block (after `.draft-guidance-block` from Task 4):

```css
  /* /write's full-document template. Custom classes, not Tailwind utilities
     (per spec) — and no <table>/<blockquote>/<style> tag or `style=`
     attribute anywhere in the generated markup, since engine/drafts.py's
     server-side sanitizer allows none of those on a save round-trip. The
     "table" is a flex-based div grid; citations are styled divs. */
  .bnm-doc { font-family: "Times New Roman", Times, serif; color: #1a1a1a; }
  .bnm-page {
    background: white;
    width: 794px;
    min-height: 1123px;
    margin: 0 auto 24px auto;
    padding: 96px 80px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    position: relative;
    box-sizing: border-box;
  }
  .bnm-cover { text-align: center; padding-top: 160px; }
  .bnm-logo {
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 48px;
    color: #003366;
  }
  .bnm-title { font-size: 24px; font-weight: bold; margin-bottom: 24px; color: #003366; }
  .bnm-draft-label {
    display: inline-block;
    border: 2px solid #003366;
    color: #003366;
    font-size: 14px;
    font-weight: bold;
    padding: 6px 20px;
    letter-spacing: 1px;
    margin-bottom: 32px;
  }
  .bnm-meta { font-size: 12px; color: #444; line-height: 2; }
  .bnm-header {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #555;
    border-bottom: 1px solid #ccc;
    padding-bottom: 8px;
    margin-bottom: 40px;
  }
  .bnm-footer {
    position: absolute;
    bottom: 48px;
    left: 80px;
    right: 80px;
    border-top: 1px solid #ccc;
    padding-top: 8px;
    font-size: 10px;
    color: #777;
    display: flex;
    justify-content: space-between;
  }
  .bnm-section-num { font-size: 13px; font-weight: bold; color: #003366; margin-bottom: 4px; }
  .bnm-section-title { font-size: 15px; font-weight: bold; margin-bottom: 16px; }
  .bnm-clause { font-size: 12px; line-height: 1.8; margin-bottom: 12px; }
  .bnm-clause-num { font-weight: bold; }
  .bnm-blockquote {
    border-left: 3px solid #003366;
    padding: 8px 16px;
    margin: 12px 0;
    background: #f5f8ff;
    font-size: 11px;
    font-style: italic;
    color: #333;
  }
  .bnm-table { width: 100%; font-size: 11px; margin: 16px 0; }
  .bnm-table-header-row { display: flex; background: #003366; color: white; }
  .bnm-table-row { display: flex; }
  .bnm-table-row:nth-child(odd) { background: #fafafa; }
  .bnm-table-cell { flex: 1; padding: 8px; border: 1px solid #ccc; }
  .bnm-table-header-row .bnm-table-cell { border-color: #003366; font-weight: bold; }
```

- [ ] **Step 2: Write `copilotFullDocument.ts`**

```ts
import { DRAFT_SECTIONS, WORKSTREAM_CONTEXT, type ClauseCitation, type DraftSection } from "./copilotV2Data";
import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function formattedDate(d: Date): string {
  return `${String(d.getDate()).padStart(2, "0")} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function coverPage(): string {
  return [
    `<div class="bnm-page bnm-cover">`,
    `<div class="bnm-logo">Bank Negara Malaysia</div>`,
    `<div class="bnm-title">Open Finance Policy Document</div>`,
    `<div class="bnm-draft-label">PROJECT SELARAS — DRAFT V1</div>`,
    `<div class="bnm-meta">`,
    `<p>Drafter: ${WORKSTREAM_CONTEXT.owner}</p>`,
    `<p>Date: ${formattedDate(new Date())}</p>`,
    `<p>Workstream: ${WORKSTREAM_CONTEXT.name}</p>`,
    `</div>`,
    `</div>`,
  ].join("");
}

function pageChrome(pageNumber: number, totalPages: number, body: string): string {
  return [
    `<div class="bnm-page">`,
    `<div class="bnm-header"><span>Open Finance</span><span>${pageNumber} of ${totalPages}</span></div>`,
    body,
    `<div class="bnm-footer"><span>Bank Negara Malaysia</span><span>Internal Draft — Not for Distribution</span></div>`,
    `</div>`,
  ].join("");
}

function sectionHeading(index: number, title: string): string {
  return [
    `<div class="bnm-section-num">SECTION ${index}</div>`,
    `<div class="bnm-section-title">${title}</div>`,
  ].join("");
}

function clause(num: string, text: string): string {
  return `<p class="bnm-clause"><span class="bnm-clause-num">${num}</span> ${text}</p>`;
}

function citation(c: ClauseCitation): string {
  return `<div class="bnm-blockquote"><strong>${c.clauseNumber}:</strong> &quot;${c.text}&quot;</div>`;
}

function timelineTable(): string {
  const rows = [
    ["Milestone", "Date", "Cohort"],
    ["Document submission & single account view interfaces live", "1 January 2028", "Mandated FSPs under §8.4"],
    ["Data-sharing obligation commencement", "Per Appendix 2 schedule", "Mandated FSPs, phased by category"],
    ["Individual and SME customer coverage complete", "On or after 1 January 2028", "All mandated data providers"],
  ];
  const [header, ...body] = rows;
  return [
    `<div class="bnm-table">`,
    `<div class="bnm-table-header-row">${header.map((h) => `<div class="bnm-table-cell">${h}</div>`).join("")}</div>`,
    ...body.map(
      (r) => `<div class="bnm-table-row">${r.map((c) => `<div class="bnm-table-cell">${c}</div>`).join("")}</div>`,
    ),
    `</div>`,
  ].join("");
}

function executiveSummaryBody(): string {
  return [
    sectionHeading(1, "Executive Summary"),
    `<p class="bnm-clause">This Policy Document sets out Bank Negara Malaysia's requirements for open finance participation by licensed banks and eligible data providers. It consolidates the Exposure Draft on Open Finance 2025, benchmarked against the Hong Kong Monetary Authority's Open API Framework, BIS Papers 168 on open banking, and RMiT 2025, to produce a single set of consent-driven data-sharing obligations for the industry.</p>`,
    `<p class="bnm-clause">The draft affirms the objectives already shared across these documents — safer, consent-driven information sharing that gives customers control over how their financial data is used — while setting Malaysia-specific commencement dates, scope, and security controls. Two areas depart materially from the reviewed comparators: this PD mandates a real-time consent dashboard and a formal breach handling and response plan, neither of which has an equivalent in the HKMA framework.</p>`,
    `<p class="bnm-clause">Where this draft aligns with, differs from, or extends its anchor documents, each section below states so plainly against a verbatim clause citation, or states that no matching clause was found. No claim in this document is made without a citable source.</p>`,
  ].join("");
}

function objectivesBody(section: DraftSection): string {
  return [
    sectionHeading(2, "Policy Objectives and Legal Basis"),
    clause("S 2.1", "This Part is issued under the Financial Services Act 2013 and sets out the objectives underpinning the open finance framework for licensed banks and eligible data providers."),
    clause("S 2.2", section.summary),
    clause("S 2.3", "A financial service provider shall read this Part alongside the empowerment framework and requirement confirmed for this task, and shall not commence open finance activities in advance of the confirmed effective date."),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function scopeBody(section: DraftSection): string {
  return [
    sectionHeading(3, "Scope of Application"),
    clause("S 3.1", "This Part applies to licensed banks and eligible data providers participating in the open finance ecosystem, in respect of the scope of prescribed information defined below."),
    clause("S 3.2", section.summary),
    clause("S 3.3", "Where a term used in this Part is not separately defined, it takes the meaning given to it in the Exposure Draft on Open Finance 2025."),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function tspGovernanceBody(section: DraftSection): string {
  return [
    sectionHeading(4, "TSP/TPP Governance"),
    clause("S 4.1", "A financial service provider shall ensure that its technology operations management practices are appropriately extended to support its open finance activities, including third-party service provider governance."),
    clause("S 4.2", section.summary),
    clause("S 4.3", "A financial service provider shall maintain a register of third-party service providers engaged in its open finance arrangements and shall review that register at least annually."),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function apiSecurityBody(section: DraftSection): string {
  return [
    sectionHeading(5, "API Security"),
    clause("S 5.1", "A financial service provider shall ensure that its cyber risk management capabilities and cybersecurity controls are appropriately extended to govern, identify, prevent, detect, respond to, and address cyber risks associated with open finance activities."),
    clause("S 5.2", section.summary),
    clause("S 5.3", "These controls apply uniformly from the effective date of this Part; a financial service provider shall not implement a phased or category-differentiated level of protection in place of the uniform controls required here."),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function timelineBody(section: DraftSection): string {
  return [
    sectionHeading(6, "Implementation Timeline"),
    clause("S 6.1", "The obligations of a mandated financial service provider under this Part shall commence in accordance with the timeline specified in Appendix 2."),
    clause("S 6.2", section.summary),
    clause("S 6.3", "A mandated financial service provider shall commence its obligation to provide document submission and single account view interfaces by 1 January 2028, or the date on which its obligations under this Part otherwise commence, whichever is later."),
    timelineTable(),
    citation(section.sourceCitations[0]),
    ...section.targetCitations.map(citation),
  ].join("");
}

function consentBody(section: DraftSection): string {
  return [
    sectionHeading(7, "Consumer Consent"),
    clause("S 7.1", "A data provider shall not disclose a customer's information to a data consumer, or a third party engaged by a data consumer, without the customer's explicit and informed consent."),
    clause("S 7.2", section.summary),
    clause("S 7.3", "Separate and distinct consent must be obtained before a customer's information is disclosed to any third party engaged to support the offering of a product or service, distinct from the consent given for the underlying open finance arrangement itself."),
    citation(section.sourceCitations[0]),
    citation(section.targetCitations[0]),
  ].join("");
}

function breachResponseBody(section: DraftSection): string {
  return [
    sectionHeading(8, "Consent Dashboard and Breach Response"),
    clause("S 8.1", "A financial service provider shall provide customers with a real-time consent dashboard through which a customer may view, manage, and withdraw consents given in respect of open finance arrangements."),
    clause("S 8.2", section.summary),
    clause("S 8.3", "A financial service provider shall maintain a breach handling and response plan for theft, loss, misuse, or unauthorised access, modification, or disclosure of customer information associated with an open finance arrangement. The plan shall, at a minimum, include escalation procedures and a clear line of responsibility to contain the breach and take remedial action."),
    `<p class="bnm-clause"><em>No matching source clause was found in the connected anchor documents for the consent dashboard or breach-response requirements above — the HKMA Open API Framework addresses TSP monitoring and scam notification but has no equivalent breach-handling-plan requirement. These clauses are drafted as considered new policy, not as a citation to an anchor document.</em></p>`,
    ...section.targetCitations.map(citation),
  ].join("");
}

const SECTION_BUILDERS: Record<string, (s: DraftSection) => string> = {
  objectives: objectivesBody,
  scope: scopeBody,
  "tsp-governance": tspGovernanceBody,
  "api-security": apiSecurityBody,
  timeline: timelineBody,
  consent: consentBody,
  "breach-response": breachResponseBody,
};

/** The full document /write auto-populates into the editor: a cover page
 *  plus one page per DRAFT_OUTLINE_SECTIONS entry (executive summary, then
 *  the 7 DRAFT_SECTIONS-backed sections), each quoting its citation(s)
 *  verbatim from DRAFT_SECTIONS — never re-paraphrased. */
export function buildFullDraft(): string {
  const totalPages = 1 + DRAFT_OUTLINE_SECTIONS.length;
  const bodyPages = DRAFT_OUTLINE_SECTIONS.map((outline, i) => {
    const pageNumber = i + 2;
    const body =
      outline.id === "executive-summary"
        ? executiveSummaryBody()
        : SECTION_BUILDERS[outline.id](DRAFT_SECTIONS.find((s) => s.id === outline.id) as DraftSection);
    return pageChrome(pageNumber, totalPages, body);
  });
  return `<div class="bnm-doc">${coverPage()}${bodyPages.join("")}</div>`;
}
```

- [ ] **Step 3: Remove `buildSectionSnippet`/`buildFullDraft` from `copilotV2Data.ts`, re-export the new one**

Delete the `buildSectionSnippet` and `buildFullDraft` functions (the block with the `/** Builds the HTML snippet... */` and `/** The full 2–3 page draft... */` comments). In their place:

```ts
export { buildFullDraft } from "./copilotFullDocument";
```

(`CopilotChat.tsx`'s `import { ..., buildFullDraft, ... } from "./copilotV2Data"` needs no change — the re-export keeps that path stable.)

- [ ] **Step 4: Add `BannerMsg` to `copilotChatTypes.ts`**

```ts
export type ChatMsgKind =
  | "user"
  | "text"
  | "command"
  | "thinking"
  | "question"
  | "suggestion"
  | "draft-summary"
  | "banner";
```

```ts
/** A one-time dismissable notice — used after /write to confirm the full
 *  document landed in the editor. */
export interface BannerMsg {
  id: string;
  kind: "banner";
  text: string;
  dismissed?: boolean;
}
```

```ts
export type ChatMsg =
  | UserMsg
  | TextMsg
  | CommandMsg
  | ThinkingMsg
  | QuestionMsg
  | SuggestionMsg
  | DraftSummaryMsg
  | BannerMsg;
```

- [ ] **Step 5: Render `BannerMsg` in `MessageRenderer.tsx`**

Add `X` to the `lucide-react` import. Add `onDismissBanner: (id: string) => void;` to `MessageHandlers`. Add the case:

```tsx
case "banner":
  if (msg.dismissed) return null;
  return (
    <div
      data-testid="write-banner"
      className="flex items-center justify-between gap-2 rounded-lg border border-primary/30 bg-primary/5 px-3 py-2 text-xs text-foreground"
    >
      <span>{msg.text}</span>
      <button
        type="button"
        aria-label="Dismiss"
        onClick={() => handlers.onDismissBanner(msg.id)}
        className="text-muted-foreground hover:text-foreground"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
```

- [ ] **Step 6: Update `runWrite` and add `onDismissBanner` in `CopilotChat.tsx`**

```ts
function runWrite() {
  const cmdId = nextId();
  append({
    id: cmdId,
    kind: "command",
    command: "/write",
    status: "active",
    statusLine: `Writing ${DRAFT_SECTIONS.length} sections…`,
    detailKind: null,
  });
  later(() => {
    insertRef.current(buildFullDraft());
    update(cmdId, {
      status: "done",
      statusLine: `${DRAFT_SECTIONS.length} sections written into your editor.`,
    });
    append({
      id: nextId(),
      kind: "draft-summary",
      sectionIds: DRAFT_SECTIONS.map((s) => s.id),
    });
    append({
      id: nextId(),
      kind: "banner",
      text: "This draft has been inserted into the editor. You may edit it directly.",
    });
    append({
      id: nextId(),
      kind: "text",
      text: "Done — I've written the full document straight into your editor, every clause quoted verbatim. Review and edit it inline.",
    });
    suggest([{ label: "Run /deliver", command: "/deliver" }]);
  }, BUILD_REVEAL_MS);
}

function onDismissBanner(id: string) {
  update(id, { dismissed: true });
}
```

Add `onDismissBanner` to the `handlers` object.

- [ ] **Step 7: Update `DraftingWorkspacePage.test.tsx`**

Add `import { DRAFT_OUTLINE_SECTIONS } from "./copilotDraftOutline";` (if not already added in Task 4). Update `reachBuildDone`:

```tsx
async function reachBuildDone(user: ReturnType<typeof userEvent.setup>) {
  await reachBrainstormDone(user);
  await runViaChip(user, "Run /draft");
  await runViaChip(user, "Run /write");
  await screen.findByTestId("draft-summary", undefined, THINKING_WAIT);
}
```

Update `"auto-populates the full draft into the editor on /build, no insert buttons"` — rename and fix the title assertions to the outline's first/last section (executive summary and breach-response), since the full document now uses the expanded titles, not `DRAFT_SECTIONS[i].title`:

```tsx
it("writes the full document into the editor on /write, no insert buttons", async () => {
  const user = userEvent.setup();
  await openCopilot(user);
  await reachBuildDone(user);

  const surface = screen.getByTestId("draft-surface");
  const first = DRAFT_OUTLINE_SECTIONS[0];
  const last = DRAFT_OUTLINE_SECTIONS[DRAFT_OUTLINE_SECTIONS.length - 1];
  await waitFor(() => {
    expect(surface).toHaveTextContent(first.title);
    expect(surface).toHaveTextContent(last.title);
  });
  // Provenance mark for text the drafter did not write.
  expect(surface.querySelector(".copilot-snippet")).not.toBeNull();
  // No manual per-section insert affordance anywhere.
  expect(
    screen.queryByRole("button", { name: /Insert into Editor/i }),
  ).not.toBeInTheDocument();

  const banner = await screen.findByTestId("write-banner");
  expect(banner).toHaveTextContent(
    "This draft has been inserted into the editor. You may edit it directly.",
  );
  await user.click(within(banner).getByRole("button", { name: "Dismiss" }));
  expect(screen.queryByTestId("write-banner")).not.toBeInTheDocument();
}, LONG_FLOW);
```

- [ ] **Step 8: Run the suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass. `npx tsc -b --noEmit` clean.

---

### Task 6: `/deliver` — named-supervisor `DeliverPanel` (replaces `ReleasePanel`)

**Files:**
- Modify: `frontend/src/features/drafting-workspace/copilotV2Data.ts` (supervisor constants)
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx` (`DeliverPanel`)
- Modify: `frontend/src/features/drafting-workspace/CopilotChat.tsx` (`deliver` reducer action, `runDeliver`, `onDeliver`)
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:**
- Produces: `SUPERVISOR_NAME`, `SUPERVISOR_ROLE`, `SUPERVISOR_EMAIL` from `copilotV2Data.ts`.

- [ ] **Step 1: Add supervisor constants to `copilotV2Data.ts`**

```ts
/** The single named recipient /deliver sends to — a different concept from
 *  the old owner/reviewers-list model (Decision 5), not a relabelling of
 *  it. Real value from data/workstreams/open-finance-pd-2026/. */
export const SUPERVISOR_NAME = "Jarod N.";
export const SUPERVISOR_ROLE = "Policy Owner, Open Finance Division";
export const SUPERVISOR_EMAIL = "jarod.ng@bnm.gov.my";
```

Delete the `RELEASE_REVIEWERS` export (Task 1 deliberately left it in place, since `ReleasePanel` still consumed it until now — this is where it actually goes):

```ts
// Deleted: export const RELEASE_REVIEWERS: string[] = [];
```

- [ ] **Step 2: Replace `ReleasePanel` with `DeliverPanel` in `MessageRenderer.tsx`**

Update imports: drop `RELEASE_REVIEWERS`, add `SUPERVISOR_EMAIL, SUPERVISOR_NAME, SUPERVISOR_ROLE`. Replace the whole `ReleasePanel` function:

```tsx
function DeliverPanel({
  delivered,
  onDeliver,
}: {
  /** The email it was sent to, once delivered — null before confirmation. */
  delivered: string | null;
  onDeliver: (email: string) => void;
}) {
  const [email, setEmail] = useState(SUPERVISOR_EMAIL);

  return (
    <div data-testid="deliver-panel" className="space-y-2 text-xs">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
          Supervisor
        </p>
        <p className="mt-0.5 text-foreground">{SUPERVISOR_NAME}</p>
        <p className="text-muted-foreground">{SUPERVISOR_ROLE}</p>
      </div>
      {!delivered ? (
        <>
          <div>
            <label
              htmlFor="deliver-email"
              className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              Email
            </label>
            <input
              id="deliver-email"
              aria-label="Supervisor email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-0.5 w-full rounded-md border border-border/60 bg-background/60 px-2.5 py-1.5 text-xs outline-none focus:border-primary/60"
            />
          </div>
          <button
            type="button"
            onClick={() => onDeliver(email)}
            className="flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
          >
            <Send className="h-3.5 w-3.5" />
            Send for Review
          </button>
        </>
      ) : (
        <p className="flex items-center gap-1.5 font-semibold text-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Draft submitted to {SUPERVISOR_NAME} ({delivered}) for review.
        </p>
      )}
    </div>
  );
}
```

Update `MessageHandlers`: replace `released: boolean; onRelease: () => void;` with `delivered: string | null; onDeliver: (email: string) => void;`. Update the `commandDetail` `"deliver"` case: `<DeliverPanel delivered={h.delivered} onDeliver={h.onDeliver} />`.

- [ ] **Step 3: Update the reducer, `runDeliver`, and `onDeliver` in `CopilotChat.tsx`**

`ChatState`: replace `released: boolean` with `delivered: string | null`. `initialState()`: `delivered: null`. Reducer action: replace `{ type: "release" }` with `{ type: "deliver"; email: string }`:

```ts
case "deliver":
  return { ...state, delivered: action.email };
```

Rename `releaseCmdId` → `deliverCmdId`, and replace `runRelease`/`onRelease`:

```ts
function runDeliver() {
  const cmdId = nextId();
  deliverCmdId.current = cmdId;
  append({
    id: cmdId,
    kind: "command",
    command: "/deliver",
    status: "active",
    statusLine: "Ready to send for review.",
    detailKind: "deliver",
  });
}

function onDeliver(email: string) {
  dispatch({ type: "deliver", email });
  if (deliverCmdId.current) {
    update(deliverCmdId.current, {
      status: "done",
      statusLine: `Sent to ${SUPERVISOR_NAME} (${email}).`,
    });
  }
}
```

Import `SUPERVISOR_NAME` from `./copilotV2Data`. Update the `handlers` object: `delivered: state.delivered, onDeliver,` (replacing `released`/`onRelease`).

- [ ] **Step 4: Update `DraftingWorkspacePage.test.tsx`**

Add `SUPERVISOR_EMAIL, SUPERVISOR_NAME, SUPERVISOR_ROLE` to the `copilotV2Data` import list; remove `RELEASE_REVIEWERS, WORKSTREAM_CONTEXT` if no longer used elsewhere in the file (check — `WORKSTREAM_CONTEXT` is still used by `reachBuildDone`'s neighbours? Verify via search; if unused after this change, remove the import). Replace `"releases the draft to the task's owner, honestly with no reviewers"`:

```tsx
it("delivers the draft to the named supervisor, with an editable email", async () => {
  const user = userEvent.setup();
  await openCopilot(user);
  await reachBuildDone(user);

  await runViaChip(user, "Run /deliver");

  await screen.findByText(SUPERVISOR_NAME, undefined, THINKING_WAIT);
  expect(screen.getByText(SUPERVISOR_ROLE)).toBeInTheDocument();
  const emailInput = screen.getByLabelText("Supervisor email") as HTMLInputElement;
  expect(emailInput.value).toBe(SUPERVISOR_EMAIL);

  await user.clear(emailInput);
  await user.type(emailInput, "aisyah.r@bnm.gov.my");
  await user.click(screen.getByRole("button", { name: "Send for Review" }));

  expect(
    (await screen.findAllByText(
      `Draft submitted to ${SUPERVISOR_NAME} (aisyah.r@bnm.gov.my) for review.`,
    )).length,
  ).toBeGreaterThan(0);
  expect(
    (await screen.findAllByText(`Sent to ${SUPERVISOR_NAME} (aisyah.r@bnm.gov.my).`)).length,
  ).toBeGreaterThan(0);
  expect(
    screen.queryByRole("button", { name: "Send for Review" }),
  ).not.toBeInTheDocument();
}, LONG_FLOW);
```

- [ ] **Step 5: Run the suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass. `npx tsc -b --noEmit` clean.

---

### Task 7: Visual/tone pass — assistant monogram, input bar, welcome-screen copy check

**Files:**
- Modify: `frontend/src/features/drafting-workspace/MessageRenderer.tsx` (assistant text avatar)
- Modify: `frontend/src/features/drafting-workspace/ChatInput.tsx` (placeholder + bar styling)
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:** none new — purely presentational.

- [ ] **Step 1: Add the "C" monogram to assistant text messages in `MessageRenderer.tsx`**

Replace the `case "text":` block:

```tsx
case "text":
  return (
    <div className="flex items-start gap-2" data-testid="assistant-text">
      <span
        aria-hidden
        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary"
      >
        C
      </span>
      <div className="min-w-0 flex-1 space-y-1.5">
        <p className="whitespace-pre-wrap text-sm leading-snug text-foreground">
          {msg.text}
        </p>
        {msg.citations && msg.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {msg.citations.map((c) => (
              <span
                key={c.clauseNumber}
                className="rounded border border-border/60 bg-muted/40 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
              >
                {c.clauseNumber}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
```

- [ ] **Step 2: Restyle the input bar in `ChatInput.tsx`**

Replace the placeholder and wrapper `className`:

```tsx
placeholder="Type a message or / for commands..."
```

```tsx
<div className="flex items-end gap-1.5 rounded-xl border border-border/60 bg-card px-2.5 py-1.5 shadow-sm focus-within:border-primary/60">
```

(was `bg-background/60` with no shadow — "full-width rounded bar, thin border + subtle shadow" per spec; full-width already comes from the parent `<form>`'s layout, unchanged.)

- [ ] **Step 3: Confirm no test depends on the old placeholder or `assistant-text`'s DOM shape**

Run: `cd frontend && npx vitest run --grep "chat-input|assistant"`
Expected: no failures (existing tests query by role/text/testid, not by the exact placeholder string or `assistant-text`'s inner structure — verify this holds; if any test does assert the literal old placeholder, update it to the new string).

- [ ] **Step 4: Run the full Copilot suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass. `npx tsc -b --noEmit` clean.

---

### Task 8: Wire the editor's Bold/Italic/Underline toolbar

**Files:**
- Modify: `frontend/src/features/drafting-workspace/EditorPane.tsx`
- Modify: `frontend/src/features/drafting-workspace/DraftingWorkspacePage.test.tsx`

**Interfaces:** none new — internal to `EditorPane`.

- [ ] **Step 1: Add selection-tracking state and `applyFormat` to `EditorPane.tsx`**

Add `import { useState } from "react";` is already present via the existing import line — add `useState` to it if missing (currently imports `forwardRef, useEffect, useImperativeHandle, useRef, useState` — `useState` is already imported for `secondsAgo`, so just add a second piece of state).

```ts
const [hasSelection, setHasSelection] = useState(false);

function updateSelectionState() {
  const el = editorRef.current;
  const selection = window.getSelection();
  if (!el || !selection || selection.rangeCount === 0 || selection.isCollapsed) {
    setHasSelection(false);
    return;
  }
  const range = selection.getRangeAt(0);
  setHasSelection(el.contains(range.commonAncestorContainer));
}

function handleSelectionChange() {
  saveCursor();
  updateSelectionState();
}

/** Bold/Italic/Underline via document.execCommand — deprecated but still
 *  universally supported, and the spec explicitly calls for it (H and •
 *  stay disabled, out of scope). No richer rich-text editor is warranted
 *  for three toggle buttons. */
function applyFormat(command: "bold" | "italic" | "underline") {
  editorRef.current?.focus();
  document.execCommand(command);
  handleSelectionChange();
  const el = editorRef.current;
  if (el) onChange(el.innerHTML);
}
```

- [ ] **Step 2: Replace the toolbar and wire selection handlers on the editable div**

Replace the toolbar block:

```tsx
<div className="flex gap-0.5" aria-label="Formatting">
  {(["B", "I", "U"] as const).map((b) => {
    const command = b === "B" ? "bold" : b === "I" ? "italic" : "underline";
    return (
      <button
        key={b}
        type="button"
        disabled={!hasSelection}
        title={hasSelection ? `Toggle ${command}` : "Select text in the editor to format it"}
        onMouseDown={(e) => e.preventDefault()}
        onClick={() => applyFormat(command)}
        className="h-6 w-6 rounded text-xs font-semibold text-muted-foreground enabled:text-foreground enabled:hover:bg-accent"
      >
        {b}
      </button>
    );
  })}
  {["H", "•"].map((b) => (
    <button
      key={b}
      type="button"
      disabled
      title="Formatting is not wired up in this build"
      className="h-6 w-6 rounded text-xs font-semibold text-muted-foreground"
    >
      {b}
    </button>
  ))}
</div>
```

Update the contentEditable div's handlers from `onMouseUp={saveCursor} onKeyUp={saveCursor} onBlur={saveCursor}` to `onMouseUp={handleSelectionChange} onKeyUp={handleSelectionChange} onBlur={handleSelectionChange}`.

Remove the now-stale comment above the toolbar (`{/* Toolbar is a visual signal only — MVP1 does not require these to function, and execCommand is deprecated. Kept non-functional rather than wired to something that half-works. */}`).

- [ ] **Step 3: Add a test for the wired toolbar in `DraftingWorkspacePage.test.tsx`**

In the `"DraftingWorkspacePage — landing"` describe block (or a new small describe block for the editor), add:

```tsx
it("enables Bold/Italic/Underline once text is selected in the editor", async () => {
  const user = userEvent.setup();
  await loadWorkspace();

  const surface = screen.getByTestId("draft-surface");
  const boldButton = screen.getByRole("button", { name: "B" });
  expect(boldButton).toBeDisabled();

  // Select the clause text already rendered in the surface.
  const range = document.createRange();
  range.selectNodeContents(surface);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
  await user.pointer([{ target: surface }]); // fires mouseup on the surface
  fireEvent.mouseUp(surface);

  await waitFor(() => expect(boldButton).not.toBeDisabled());
});
```

Add `fireEvent` to the `@testing-library/react` import at the top of the file.

- [ ] **Step 4: Run the suite**

Run: `cd frontend && npm test -- DraftingWorkspacePage`
Expected: all pass, including the new toolbar test. If the synthetic-selection approach above doesn't reliably trigger `onMouseUp` in jsdom, fall back to directly invoking `fireEvent.mouseUp(surface)` after setting `window.getSelection()`'s range (already shown above) — jsdom's `Selection` API supports `addRange`, so this should be sufficient without needing real pointer drag simulation.

---

### Task 9: Final verification pass

No new code — confirms every prior task's changes compose correctly across the whole app, not just the Copilot-scoped tests.

**Files:** none modified.

- [ ] **Step 1: Full frontend test suite**

Run: `cd frontend && npm test`
Expected: all suites pass, not just `DraftingWorkspacePage.test.tsx` — confirm no regression in unrelated features (e.g. `IntroPage.tsx`'s already-modified-but-out-of-scope diff doesn't intersect with this work, but its own tests, if any, should still be green).

- [ ] **Step 2: Full typecheck + build**

Run: `cd frontend && npm run build`
Expected: `tsc -b` reports zero errors, `vite build` completes.

- [ ] **Step 3: Manual smoke check of the demo path**

Run: `cd frontend && npm run dev`, open `/workstreams/opres-v2/tasks/opres-pd-v0-3/draft`, click the Copilot tab, and walk the full path by hand: welcome screen → Explore Task → fill + submit missing fields → Run /brainstorm → answer the leading question and all 6 clarification rounds → Run /draft (confirm 8 instruction cards + 8 `.draft-guidance-block` divs land in the editor, styled with the light-blue background) → Run /write (confirm the cover page + 8 styled BNM pages render, the dismissable banner appears and dismisses) → Run /deliver (confirm Jarod N.'s name/role, edit the email, send, confirm both the panel and the command status line update) → Start over (confirm it returns to the welcome screen).
Expected: no console errors, every screen matches the spec's described tone (no emoji, no exclamation marks, formal copy), citations visible in `/write`'s output are exact matches to `DRAFT_SECTIONS`' `sourceCitations`/`targetCitations` text.

- [ ] **Step 4: Confirm the save round-trip doesn't silently strip the new markup**

With the dev server running from Step 3, after `/write` completes, wait ~2.5s (past the `SAVE_DEBOUNCE_MS` debounce) for the auto-save to fire, then reload the page. Confirm the `.bnm-page`/`.bnm-blockquote`/`.bnm-table` styling survives the reload (it should — Task 5's generated markup only uses `div`/`span`/`p`/`strong`/`em`/`ul`/`li` tags with `class` on `div`/`span`/`p`, all of which `engine/drafts.py`'s `bleach.clean` allows through unchanged). If anything renders unstyled after reload, the CSS class was applied to a tag/attribute combination `engine/drafts.py` doesn't allow — check `data/workstreams/opres-v2/drafts/opres-pd-v0-3.json` after the reload to see exactly what the server persisted, and fix the offending element in `copilotFullDocument.ts`/`copilotDraftOutline.ts` to use an allowed tag instead (never by loosening `engine/drafts.py` — out of scope).
