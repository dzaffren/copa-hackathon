# Light Mode Frontend

**Ticket:** TBD

Convert the Workstream Brain app from its current dark-only theme to a single, production-quality light theme. The drafter works in a clean, institutional light interface with a deep indigo accent, a gently pulsing highlight on whatever is selected, and the interactive graph kept as a framed dark viewport. This removes the current half-tuned light theme (which looks unfinished) and the theme toggle, leaving one polished look.

## User Story

As a policy drafter (Aisyah R.), I want the Workstream Brain app to present a single, polished light interface so that the tool feels finished and professional when I use it and when it is demonstrated to approving management.

## Background & Context

**Current state:**

- The app opens in a carefully tuned dark theme (deep navy/slate with glass panels).
- A light theme exists but is the stock, un-tuned palette — text is unreadable in several places (pale grey labels on near-white chips) and action buttons use a bright cyan tuned for dark backgrounds.
- A sidebar toggle lets the user switch between the two, and the choice is remembered between visits.

**Problem:**

- The light theme looks unfinished, so the app cannot be shown in light mode with confidence.
- The team wants light mode to be the product's look, not an afterthought behind a toggle.
- Maintaining two themes doubles the polishing effort for a hackathon demo that only needs one great look.

## Target User & Persona

- **Who:** Aisyah R., the policy drafter, is the primary user throughout the product. An approving manager sees the same interface during sign-off and demos.
- **Context:** Aisyah works across the workstream graph, review, and drafting screens for extended sessions; the interface needs to be readable and calm, not glaring.
- **Current workaround:** She either tolerates the dark theme or switches to the broken light theme and lives with the readability problems.

## Goals

- Deliver one cohesive light theme that reads as production-ready across every screen.
- Establish a deep, institutional accent colour appropriate for a regulator-facing tool.
- Give the interface a sense of life: whatever the user selects gently pulses, so the app never feels static.
- Keep the interactive graph legible by presenting it as a deliberate framed dark viewport within the light app.
- Remove the now-unused dark theme and the theme toggle so there is a single look to maintain.

## Non-Goals

- No dark theme, no theme toggle, and no remembered theme preference — the app is light-only.
- No redesign of the graph's node/edge colour coding — those colours carry meaning and stay as they are on the dark viewport.
- No change to any content, data, findings, citations, or screen layout beyond what colour and highlight polish require.
- No new screens or features.

## User Workflow

1. **Opening the app** — Aisyah loads any screen and sees a clean light interface: a soft off-white background with white panels lifting off it, dark readable text, and a deep indigo used for primary actions.
2. **Scanning findings and badges** — Every label, chip, and status badge is clearly legible; nothing is pale-on-pale.
3. **Selecting something** — When Aisyah clicks a node, a navigation item, or a card, that item shows a gentle, slow pulsing highlight in the accent colour so she always knows what is currently selected. The pulse is calm, not attention-grabbing.
4. **Working in the graph** — The interactive graph appears as a framed dark panel inside the light app. Its colour-coded nodes and edges remain vivid and readable, and the hero task node keeps its living pulse.
5. **Identifying the important item** — The primary working draft (the task) reads as the most important object through its larger size and stronger weight, not through animation.
6. **Completion** — Aisyah never encounters a dark screen, a toggle, or an unreadable element; the whole app feels like one finished product.

## Acceptance Criteria

### Scenario: App presents a single light theme on load

```gherkin
Given the app has been converted to light-only
When Aisyah opens any screen for the first time
Then the interface is displayed in the light theme
  And no theme toggle control is shown
  And there is no option to switch to a dark interface
```

### Scenario: Previously saved dark preference no longer forces a dark interface

```gherkin
Given Aisyah previously used the app and had a dark preference remembered
When she opens the app after the conversion
Then the interface is displayed in the light theme
  And her old preference has no effect
```

### Scenario: All text and badges are readable on the light background

```gherkin
Given Aisyah is viewing a screen that contains status badges and labels
When she reads the finding labels, node-type chips, and status badges
Then every label has sufficient contrast to be read comfortably
  And no label appears as pale text on a pale background
```

### Scenario: Selecting an item shows a gentle pulsing highlight

```gherkin
Given Aisyah is on a screen with selectable items
When she selects a graph node, a navigation item, or a card
Then the selected item shows a slow, gentle pulsing highlight in the accent colour
  And the pulse continues while the item stays selected
  And the pulse is subtle rather than attention-grabbing
```

### Scenario: Only one selection is highlighted at a time within a group

```gherkin
Given Aisyah has selected a navigation item that is pulsing
When she selects a different navigation item
Then the newly selected item pulses
  And the previously selected item stops pulsing
```

### Scenario: The important task object is emphasised by size, not animation

```gherkin
Given Aisyah is viewing the working draft (the task) alongside other documents
When she looks at the task object
Then it appears larger and bolder than the surrounding items
  And it is not distinguished by a pulsing or blinking effect unless she has selected it
```

### Scenario: The interactive graph is a framed dark viewport

```gherkin
Given Aisyah opens a screen containing the interactive graph
When the graph is displayed
Then it appears as a clearly framed dark panel within the light interface
  And its colour-coded nodes and edges remain vivid and readable
  And the hero task node keeps its living pulse
```

### Scenario Outline: Every screen renders in the polished light theme

```gherkin
Given the app is light-only
When Aisyah navigates to the <screen>
Then the screen is displayed in the light theme with readable text and consistent accent colour

Examples:
  | screen              |
  | home                |
  | workstream graph    |
  | review linkages     |
  | drafting workspace  |
  | task screen         |
  | new workstream      |
  | institution map     |
```

## Business Rules & Constraints

- The app has exactly one theme: light. There is no toggle and no remembered preference.
- The accent colour is a single deep, institutional indigo/blue used consistently for primary actions and the selection pulse.
- Bright cyan is retained in exactly one place — the graph's hero task node on the dark viewport — and does not appear in the light interface chrome.
- The pulsing highlight means "this is selected/active" and is applied consistently; it is slow and gentle (a calm breathing effect), not fast or flashing.
- Importance of an object (such as the working draft) is signalled by size and weight, never by animation.
- The verbatim-citation rule and all content remain unchanged — this work is purely visual.

## Success Metrics

- Every screen (home, workstream graph, review linkages, drafting workspace, task screen, new workstream, institution map) is confirmed readable and consistent in light mode during a manual review pass.
- Zero pale-on-pale or otherwise unreadable text elements remain.
- The app can be demonstrated end-to-end in light mode without switching to dark or encountering a visual defect.
- Reviewers describe the interface as looking finished/production-ready.

## Dependencies

- None. This is a self-contained visual change to the existing frontend and does not depend on other features or business processes.

## Open Questions

- [x] ~~Should the app keep both themes or become light-only?~~ — **Resolved:** Light-only. Removes toggle and dark theme; one look to polish for the demo.
- [x] ~~Should the interactive graph become light or stay dark?~~ — **Resolved:** Stays dark, presented as an intentional framed viewport. Cheapest and lowest-risk; the node colour-coding already reads on dark and the glow effect only works on a dark background.
- [x] ~~Keep the cyan accent or move to a different primary colour?~~ — **Resolved:** Move to a deep institutional indigo/blue for the light chrome; cyan is retained only as the graph's task-node accent.
- [x] ~~How should a "hero"/selected element feel alive in light mode, given glow does not work on white?~~ — **Resolved:** A gentle, continuous pulsing ring in the accent colour indicates selection; importance is shown by size/weight. Pulse is slow and calm.

---

## Functional Requirements

- **Single theme:** The app renders exactly one theme (light). No runtime theme state, no class toggling on `<html>`, no persisted preference.
- **Token-driven colour:** All chrome colour must resolve through the CSS custom properties in `frontend/src/index.css` (consumed via Tailwind tokens `bg-background`, `text-foreground`, `bg-primary`, etc.). No component may hardcode a chrome colour that bypasses these tokens. Exception: the graph canvas (`bg-[#0b1220]` viewport and the JS-painted node/edge colours in `legend.ts`), which is intentionally dark and out of the token system.
- **Accent consistency:** A single primary colour (deep indigo/blue) is used for primary actions, links, active/selected states, and the selection pulse ring. Cyan (`#22d3ee`) survives only as the graph task-node fill in `legend.ts`.
- **Selection pulse:** A `pulse-ring` animation (gentle, continuous, ~2.5–3s ease-in-out loop, low amplitude) marks the currently selected/active item. Applied to: active sidebar nav items, the selected workstream row, and any selected card. It is the light-mode analogue of the graph node's existing glow.
- **Importance by size:** The task/working-draft object is emphasised through size and font weight only — never a pulse or blink unless it is the selected item.

### Validation & Business Rules

- The `.dark { … }` CSS block and all dark-theme values are removed; the light `:root` values are retuned (not left as stock shadcn slate).
- `--background` is a faint cool off-white (not pure `#fff`) so white `card` surfaces lift off it.
- `--primary` is a deep indigo tuned to meet WCAG AA contrast against `--primary-foreground` (white) for button text.
- No content, data, findings, citations, routes, or layout structure changes. Visual-only.

## UI/Frontend Requirements

### Theme tokens — `frontend/src/index.css`

- **Remove** the entire `.dark { … }` block (lines ~29–52).
- **Retune** the `:root` light palette. Target values (HSL, final values tuned during implementation to hit AA):
  - `--background: 210 40% 98%` (faint cool off-white)
  - `--card: 0 0% 100%` (pure white, lifts off background)
  - `--primary: 231 55% 45%` (deep institutional indigo; verify AA vs. white text)
  - `--primary-foreground: 0 0% 100%`
  - `--ring: 231 55% 45%` (matches primary, drives selection ring)
  - `--muted-foreground`: darken enough that badge/label text on `muted`/`secondary` reads clearly (no pale-on-pale).
- **Retune `.glass` utility** (currently `border-border/60 bg-card/70 backdrop-blur-md`) so a translucent panel reads as an elevated white surface on the light background — add/verify a subtle shadow; adjust opacity so it does not wash out.

### Selection pulse — `frontend/tailwind.config.js`

- Add a `pulse-ring` keyframe + animation to `theme.extend`:
  - Keyframes animate `box-shadow` (or ring opacity) between a faint and a slightly stronger `hsl(var(--ring))` halo — low amplitude.
  - Animation: `pulse-ring 2.75s ease-in-out infinite`.
- Reused via an `animate-pulse-ring` class wherever selection is indicated.

### Component changes

**`frontend/src/lib/theme.tsx`** — Delete entire file (ThemeProvider, useTheme, storage, `applyTheme`).

**`frontend/src/main.tsx`** — Remove `import { ThemeProvider }` and unwrap `<ThemeProvider>` (keep `QueryClientProvider` + `BrowserRouter`).

**`frontend/src/features/workstream-graph/Sidebar.tsx`**

- Remove `useTheme` import + `const { theme, toggleTheme }` (line 49).
- Remove the theme-toggle `<button>` block (lines ~206–224) and the now-unused `Sun`/`Moon` lucide imports.
- Active nav items currently use `bg-cyan-500/15 text-cyan-200 ring-1 ring-cyan-400/30` (lines 108–109, 124–125) and the active-workstream row (line 160). Change these to the indigo primary token equivalents and add `animate-pulse-ring` to the active/selected state.
- `ROLE_DOT` cyan/amber/emerald dots (lines 25–29): keep semantic colours but verify they read on the light rail; desaturate if they vibrate.
- Logo gradient `from-cyan-500/30 to-indigo-500/30` (line 72): retune for light.

**Action buttons — replace `bg-cyan-500 text-slate-950 hover:bg-cyan-400` with the shadcn `Button` default (`bg-primary text-primary-foreground`) or `bg-primary` token classes** in:

- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx:323`
- `frontend/src/features/workstream-graph/EdgeDetailPanel.tsx:128`
- `frontend/src/features/workstream-graph/AddNodeDialog.tsx:299`
- `frontend/src/features/workstream-graph/WorkstreamGraphPage.tsx:99`
- `frontend/src/features/task/TaskScreenPage.tsx:187`
- `frontend/src/features/task/NeighbourFindingsCard.tsx:97`
- `frontend/src/features/task/EmptyDraftCard.tsx:27`
- `frontend/src/features/task/PairwiseComparisonCard.tsx:136` (selected-state cyan)
- `frontend/src/features/task/ApproveDialog.tsx:42` (emerald — keep green semantics for "approve", but verify on light)
- `frontend/src/features/drafting-workspace/CopilotTab.tsx:212,283,320`
- `frontend/src/features/drafting-workspace/DraftingWorkspacePage.tsx:143,153`
- `frontend/src/features/home/HomePage.tsx:142`
- `frontend/src/features/new-workstream/NewWorkstreamPage.tsx:291`
- `frontend/src/components/DemoController.tsx:153` (`bg-cyan-400 text-slate-950`)

**Readability fixes — pale-on-pale badges** (retune `text-slate-300` on `bg-slate-500/15` to `text-secondary-foreground` / `text-muted-foreground` on `bg-secondary` or `bg-muted`):

- `frontend/src/features/review-linkages/FindingCard.tsx:83`
- `frontend/src/features/review-linkages/ReviewLinkagesPage.tsx:114`
- `frontend/src/features/task/TaskScreenPage.tsx:29`
- `frontend/src/features/workstream-graph/NodeDetailPanel.tsx:186`
- `frontend/src/features/new-workstream/NewWorkstreamPage.tsx:210` (`hover:bg-gray-300` → token)

**Graph viewport framing** (keep `bg-[#0b1220]` dark; add rounded corners + border + subtle shadow so it reads as a deliberate dark panel):

- `frontend/src/features/workstream-graph/GraphCanvas.tsx:195`
- `frontend/src/features/workstream-graph/WorkstreamGraphPage.tsx:112`
- `frontend/src/features/drafting-workspace/EditorPane.tsx:210`
- `frontend/src/features/institution-map/InstitutionMapPage.tsx:238`

**`frontend/src/components/ui/dialog.tsx:22`** — overlay `bg-black/80`: keep (a dark scrim over light content is correct).

**`frontend/src/features/drafting-workspace/EditorPane.tsx:211,225,227,237`** — the "paper" surface (`bg-white text-slate-900`) already suits light; verify it still lifts off the retuned background, no change expected.

### States

- **Selected:** `animate-pulse-ring` + solid indigo ring on the active/selected element.
- **Hover (non-selected):** existing `hover:bg-accent` behaviour, verified on light.
- **Graph viewport:** dark panel, framed; unchanged internal rendering.

## Architecture Notes

- **New dependencies:** none.
- **Dependencies & integration:** Removing `theme.tsx` deletes the `useTheme` export. Only `main.tsx` and `Sidebar.tsx` import it (confirmed via grep) — both are updated in this work. Test utils (`frontend/src/test/utils.tsx`) never wrapped components in `ThemeProvider`, so the existing Vitest suite is unaffected by the removal.
- **Out of token system (intentional):** the graph canvas colours in `frontend/src/features/workstream-graph/legend.ts` and the `bg-[#0b1220]` viewports stay dark and are NOT migrated to tokens.

## Exemplar Files

- `frontend/src/features/workstream-graph/Sidebar.tsx` — existing active-nav pattern (`aria-current` + ring classes) to convert to the pulsing indigo indicator.
- `frontend/src/components/ui/button.tsx` — the shadcn `Button` whose `bg-primary` default the cyan buttons should adopt.
- `frontend/src/index.css` + `frontend/tailwind.config.js` — the token + Tailwind extension pattern to follow.

## Implementation Plan

### Sub-tasks

**Task 1: Collapse theme system to light-only + retune tokens** — _small_

- Files: `frontend/src/index.css`, `frontend/src/lib/theme.tsx` (delete), `frontend/src/main.tsx`, `frontend/src/features/workstream-graph/Sidebar.tsx` (remove toggle + `useTheme` + `Sun`/`Moon`)
- Retune `:root`, remove `.dark`, retune `.glass`.
- SEQUENTIAL (foundation — all later visual work depends on the retuned tokens)

**Task 2: Add `pulse-ring` animation + apply selection indicator** — _small_

- Files: `frontend/tailwind.config.js`, `frontend/src/features/workstream-graph/Sidebar.tsx`
- SEQUENTIAL (depends on Task 1 tokens; also edits Sidebar, so ordered after Task 1's Sidebar edits)

**Task 3: Migrate action buttons to the indigo primary token** — _medium_

- Files: the ~15 button-spot files listed under UI/Frontend Requirements → Action buttons.
- SEQUENTIAL (depends on Task 1 `--primary`)

**Task 4: Fix pale-on-pale badges + frame the graph viewports** — _small_

- Files: the badge-readability files + the 4 graph-viewport files listed above.
- SEQUENTIAL (depends on Task 1 tokens)

> Tasks 2–4 all depend only on Task 1 and touch mostly disjoint files (Task 2 and Task 1 both touch `Sidebar.tsx`, so keep them ordered). They can otherwise proceed in sequence without conflict.

### Negative Constraints

- Do NOT migrate the graph canvas colours (`legend.ts`) or the `bg-[#0b1220]` viewports to the light token system — they stay dark by design.
- Do NOT change the dialog overlay scrim (`dialog.tsx:22`).
- Do NOT alter any content, findings, citations, routes, data fetching, or layout structure.
- Do NOT reintroduce a theme toggle, `ThemeProvider`, or persisted preference.
- Do NOT change the graph node's existing pulse/glow logic in `GraphCanvas.tsx`.
- Do NOT add new dependencies.

## Test Scenarios

**Test 1: No dark theme artifacts remain**

- Setup: Repo after implementation.
- Action: Grep `frontend/src` for `.dark`, `useTheme`, `ThemeProvider`, `wsb-theme`, `toggleTheme`.
- Expected: No matches in `src` (the string `dark` may remain only inside `dialog.tsx` `bg-black/80` scrim context — verify no theme logic).

**Test 2: No stray cyan chrome buttons**

- Setup: Repo after implementation.
- Action: Grep `frontend/src` for `bg-cyan-500 text-slate-950` and `bg-cyan-400 text-slate-950`.
- Expected: Zero matches (cyan survives only as `#22d3ee` in `legend.ts`).

**Test 3: Existing Vitest suite still green**

- Setup: Repo after implementation.
- Action: `cd frontend && npm run test`.
- Expected: All existing tests pass (Sidebar collapse test, page render tests, etc.). No test asserted theme/toggle behaviour, so none should need changes; if the Sidebar toggle removal breaks a query, update that test.

**Test 4: Production build + typecheck clean**

- Setup: Repo after implementation.
- Action: `cd frontend && npm run build`.
- Expected: Build succeeds with no TypeScript errors (removing `useTheme` must leave no dangling imports).

**Test 5: Contrast of primary button text**

- Setup: Final `--primary` value.
- Action: Compute WCAG contrast ratio of `--primary-foreground` (white) on `--primary`.
- Expected: ≥ 4.5:1 (AA for normal text).

## Acceptance Criteria

- [ ] `.dark` block, `theme.tsx`, `ThemeProvider`, and the sidebar toggle are removed; no dangling imports.
- [ ] `:root` light palette retuned (not stock slate); `--primary` is a deep indigo meeting AA.
- [ ] `pulse-ring` animation added and applied to active/selected nav, workstream row, and selected cards.
- [ ] All ~15 cyan action buttons use the indigo primary token; cyan remains only on the graph task node.
- [ ] All previously pale-on-pale badges are readable; graph viewports are framed dark panels.
- [ ] `npm run build` and `npm run test` both pass; no type errors or lint warnings.
- [ ] Manual browser pass confirms every route renders correctly in light mode.

## Verification

Run the verifier skill to confirm changes are clean.

### Frontend Unit Tests (Vitest)

- No new test files required — this is a visual change with no behavioural logic.
- Confirm the existing suite passes: `cd frontend && npm run test`.
- If removing the Sidebar toggle breaks any Sidebar test query, update that specific test to match the toggle-free rail. (Current `Sidebar.test.tsx` tests the collapse rail, not the theme toggle, so likely no change.)

### Browser/UI Testing

- **URL:** `http://localhost:5173` (run `cd frontend && npm run dev`; ensure the engine is serving `/api/workstreams/*` per CLAUDE.md, `VITE_API_BASE` default `http://localhost:8000`).
- **Steps:**
  1. Load `/` (home) → confirm light background, readable text, indigo primary CTA.
  2. Navigate each route — workstream graph, review linkages, drafting workspace, task screen, new workstream, institution map — confirm no dark chrome, no pale-on-pale text, consistent indigo accent.
  3. Select a sidebar nav item and a workstream row → confirm the gentle continuous indigo pulse ring; select another → confirm the previous stops pulsing.
  4. Open the workstream graph → confirm the canvas is a framed dark viewport, nodes/edges vivid, the hero task node still pulses/glows.
  5. Open a dialog (e.g. Add node, Approve) → confirm the dark scrim over light content reads correctly.
  6. Confirm no theme toggle control exists anywhere in the sidebar.

> No E2E framework in this repo (Vitest + testing-library only), so E2E mapping is intentionally omitted; the Browser/UI steps above cover the user-facing Key Scenarios.

## Open Questions

- [x] ~~Does the app have an E2E framework to map scenarios to?~~ — **Resolved:** No (only Vitest + testing-library). Manual browser pass covers the user-facing scenarios.
- [x] ~~Will removing `ThemeProvider` break the test suite?~~ — **Resolved:** No. `frontend/src/test/utils.tsx` never wrapped components in `ThemeProvider`, and `useTheme` had a no-op fallback; no test asserts theme behaviour.
- [x] ~~Exact `--primary` indigo value?~~ — **Resolved (non-blocking):** Start from `231 55% 45%` and adjust during implementation to hit WCAG AA against white; the tuning is a build-time detail, not a design blocker.
