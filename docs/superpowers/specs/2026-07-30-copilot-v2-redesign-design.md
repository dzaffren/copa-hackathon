# Copilot v2 Redesign — Design

**Date:** 2026-07-30
**Status:** Approved design → ready for implementation plan
**Scope:** Frontend only, `frontend/src/features/drafting-workspace/`. Tone,
visual style, command renames, and command-behavior upgrades for the
mocked-data Copilot chat panel; no engine/API changes.

## Problem

The Copilot panel is a working, fully-scripted demo (no live model calls) built
around five slash commands. Two things need to change before it's demo-ready
for a BNM audience:

1. **Tone/polish** — the panel needs to read as a professional government
   tool: no emoji, formal copy, a ChatGPT-style conversation layout, and a
   proper welcome state instead of dropping straight into an intent question.
2. **Command depth** — three of the five commands (`/skeleton`, `/build`,
   `/release`) currently do less than the demo needs: `/skeleton` is a bare
   title list, `/build` inserts a single generic draft, `/release` sends to an
   empty reviewer list. These get renamed and substantially expanded.

## Current state (verified against the actual code, not assumed)

- `CopilotChat.tsx` seeds a greeting **and** a 7-option intent-picker
  (`questionKind: "intent"`, options from `COPILOT_INTENTS`) before anything
  else is reachable. This whole gate is removed (see Decision 1).
- `copilotV2Data.ts` already has `NODE_METADATA` with 4 null-valued fields
  (`empowerment_framework`, `requirement`, `effective_date`,
  `ismp_classification`), 6 `CLARIFICATION_QUESTIONS`, and 7 `DRAFT_SECTIONS`
  (`objectives`, `scope`, `tsp-governance`, `api-security`, `timeline`,
  `consent`, `breach-response`) each with real verbatim `sourceCitations` /
  `targetCitations`.
- `EditorPane.tsx` already has `insertAtCursor` (DOMPurify-sanitized insert at
  saved cursor) and a fully-built but `disabled` formatting toolbar (B/I/U/H/•)
  with the tooltip "Formatting is not wired up in this build" — this gets
  wired up rather than rebuilt (Decision 6).
- `MessageRenderer.tsx` has an inline `ReleasePanel` keyed to
  `WORKSTREAM_CONTEXT.owner` + `RELEASE_REVIEWERS` (currently empty) — this is
  replaced conceptually, not just relabeled (Decision 5).
- The only non-ASCII glyph in the feature is `✓` (U+2713) in three places, one
  of which (`ConfidenceMeter`'s `"Aligned ✓"`) is asserted verbatim by
  `DraftingWorkspacePage.test.tsx:289`. `✓` is not a pictographic emoji and
  stays untouched.
- `DraftingWorkspacePage.test.tsx` (432 lines) asserts exact copy and flow
  order throughout and will need lockstep updates (Decision 7).

## Decisions

**1. Remove the intent picker entirely.** The welcome screen's 4 quick-action
buttons become the sole entry point; clicking one (or typing the matching
slash command) runs that command directly. `CopilotChat.initialState()` seeds
zero messages; `WelcomeScreen` renders whenever `messages.length === 0`.

**2. `/write` goes full depth, not a shortened demo version.** 8-12 rendered
pages, all 8 body sections (see Decision 4) expanded into real multi-paragraph
prose with numbered sub-clauses and blockquote citations, plus one structured
table (implementation timeline). This is explicitly the demo's centerpiece.

**3. Command renames** (`SlashCommandId` and every call site):

| Old | New |
|---|---|
| `/pull-node-metadata` | `/explore-task` |
| `/brainstorming` | `/brainstorm` |
| `/skeleton` | `/draft` |
| `/build` | `/write` |
| `/release` | `/deliver` |

Lifecycle functions rename in step: `runPullMetadata→runExploreTask`,
`runBrainstorming→runBrainstorm`, `runSkeleton→runDraftOutline`,
`runBuild→runWrite`, `runRelease→runDeliver`.

**4. `/draft`'s instructional outline covers 8 sections, one more than
`DRAFT_SECTIONS` currently has.** The spec's section list (Executive Summary,
Policy Objectives and Legal Basis, Scope of Application, TSP/TPP Governance,
API Security, Implementation Timeline, Consumer Consent, Consent Dashboard and
Breach Response) adds a lead **Executive Summary** section that is prose-only
synthesis with no citations — it doesn't map to an existing `DraftSection`
entry. The other 7 map onto the existing `DRAFT_SECTIONS` entries with their
titles expanded to match the spec's fuller wording (e.g. `objectives` →
"Policy Objectives and Legal Basis").

**5. `/deliver` replaces the owner/reviewers-list model, it doesn't relabel
it.** Today's `ReleasePanel` shows `WORKSTREAM_CONTEXT.owner` and an (empty)
`RELEASE_REVIEWERS` list. The new `DeliverPanel` shows a single named
supervisor (Jarod N., Policy Owner — Open Finance Division) with a read-only
name/role and an editable, pre-filled email, confirmed via "Send for Review."
This is a different concept (one confirmable recipient vs. a reviewer list),
confirmed intentional.

**6. The editor's formatting toolbar gets wired up, not rebuilt.**
`EditorPane.tsx` already renders the B/I/U/H/• toolbar in disabled state.
Enable it on text selection inside the editor, backed by
`document.execCommand`, matching the spec's "floating toolbar: Bold, Italic,
Underline" ask (H and • stay disabled — out of scope, not requested).

**7. Content-heavy generators move out of `copilotV2Data.ts`, its existing
exports don't change shape.** Adding 8-12 pages of prose plus 8 outline blocks
to the already-435-line `copilotV2Data.ts` would roughly quadruple it. Two new
modules:
- `copilotDraftOutline.ts` — the instructional-outline data (title,
  description, bullets, guidance note) for `/draft`.
- `copilotFullDocument.ts` — the expanded `buildFullDraft()` HTML generator
  and its prose content for `/write`.

Both are imported back into `copilotV2Data.ts`, which keeps re-exporting
`buildFullDraft` / a new `buildDraftOutline` so every other file's import path
is unchanged.

**8. `DraftingWorkspacePage.test.tsx` is updated in lockstep, not left red.**
The suite asserts exact copy/flow for the intent picker, old command names,
`/build`'s "no Insert button" invariant, and `/release`'s owner/reviewers
text — all of which change here. Updating it is required follow-through per
`CLAUDE.md`'s verification norms, not optional polish. New coverage is added
for: welcome-screen quick actions, `/explore-task`'s missing-fields form,
`/draft`'s instructional-outline render + `.draft-guidance-block` insert, and
`/deliver`'s email-confirmation step.

## Detailed behavior per command

### `/explore-task` (was `/pull-node-metadata`)
Same metadata reveal as today. After rendering, if any `NODE_METADATA` field
has `value: null`, show a compact inline form: "Some fields could not be
resolved. Please provide the following to improve your draft:" with one text
input per null field —

```ts
const MISSING_FIELDS = [
  { key: "empowerment_framework", label: "Empowerment framework", placeholder: "e.g. Financial Services Act 2013, Section 47" },
  { key: "requirement", label: "Requirement", placeholder: "e.g. Mandatory compliance for all licensed banks" },
  { key: "effective_date", label: "Effective date", placeholder: "e.g. 2028-01-01" },
  { key: "ismp_classification", label: "ISMP classification", placeholder: "e.g. Restricted — Internal Use" },
];
```

On submit, those values render as confirmed rows in `NodeMetadataList` (no
longer italic "Not available"). Suggests `/brainstorm` next.

### `/brainstorm` (was `/brainstorming`)
Same thinking-orb + Q&A mechanics (`THINKING_STEPS`, 6
`CLARIFICATION_QUESTIONS`, `ConfidenceMeter` 0→100%, "Aligned ✓" unchanged).
Leading question text updated to name the actual documents in play: "I see
you are consolidating the Open Finance PD · 2026 against the ED Open Finance
2025 exposure draft, benchmarked against the HKMA Open API Framework, BIS
Papers 168, and RMiT 2025..." — cross-check this against `ANCHOR_DOCS` during
implementation so the named documents match what's actually in the fixture.
Suggests `/draft` next (not `/skeleton`).

### `/draft` (was `/skeleton`)
Renders a structured instructional outline, not a title list — for each of
the 8 sections: bold title, one-sentence description, 3-4 bullets (what to
write / what angle / which clauses to reference), and an italic guidance note
("Consider mirroring the exact language from ED Open Finance 2025 §1.2").
Shown in chat via a new `DraftInstructionCard` (`copilotViews.tsx`) and
inserted into the editor as one `.draft-guidance-block` div per section
(inline `background: #EBF5FF`, `border-left: 3px solid #93C5FD`) — real
editable content the user replaces by clicking and typing, not an HTML
`placeholder`. Suggests `/write` next.

### `/write` (was `/build`)
Inserts a full paginated document styled like `ED_Open_Finance_2025.html`,
built from the template skeleton below (`copilotFullDocument.ts`, inline
styles only since it lands inside a sanitized contentEditable div — no
Tailwind classes):

- **Cover page**: "BANK NEGARA MALAYSIA" wordmark placeholder, title "Open
  Finance Policy Document", draft-label box "PROJECT SELARAS — DRAFT V1",
  `Drafter: {WORKSTREAM_CONTEXT.owner}`, `Date: {formatted current date}`
  (real `new Date()` at generation time, formatted `DD Month YYYY`),
  `Workstream: Open Finance PD · 2026`.
- **Every body page**: header ("Open Finance" left, "X of N" right), footer
  (thin rule + "Bank Negara Malaysia" / "Internal Draft — Not for
  Distribution").
- **8 body sections**, numbered headings, each expanding its `DRAFT_SECTIONS`
  citations into full prose with numbered sub-clauses (`S 1.1`, `S 1.2`, …)
  and `.bnm-blockquote` verbatim citations; the Implementation Timeline
  section includes a `.bnm-table`.

```html
<style>
  .bnm-doc { font-family: 'Times New Roman', Times, serif; color: #1a1a1a; }
  .bnm-page { background: white; width: 794px; min-height: 1123px; margin: 0 auto 24px auto;
              padding: 96px 80px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
              position: relative; box-sizing: border-box; }
  .bnm-cover { text-align: center; padding-top: 160px; }
  .bnm-logo { font-size: 13px; font-weight: bold; letter-spacing: 2px;
              text-transform: uppercase; margin-bottom: 48px; color: #003366; }
  .bnm-title { font-size: 24px; font-weight: bold; margin-bottom: 24px; color: #003366; }
  .bnm-draft-label { display: inline-block; border: 2px solid #003366; color: #003366;
                      font-size: 14px; font-weight: bold; padding: 6px 20px;
                      letter-spacing: 1px; margin-bottom: 32px; }
  .bnm-meta { font-size: 12px; color: #444; line-height: 2; }
  .bnm-header { display: flex; justify-content: space-between; font-size: 10px;
                color: #555; border-bottom: 1px solid #ccc; padding-bottom: 8px; margin-bottom: 40px; }
  .bnm-footer { position: absolute; bottom: 48px; left: 80px; right: 80px;
                border-top: 1px solid #ccc; padding-top: 8px; font-size: 10px; color: #777;
                display: flex; justify-content: space-between; }
  .bnm-section-num { font-size: 13px; font-weight: bold; color: #003366; margin-bottom: 4px; }
  .bnm-section-title { font-size: 15px; font-weight: bold; margin-bottom: 16px; }
  .bnm-clause { font-size: 12px; line-height: 1.8; margin-bottom: 12px; }
  .bnm-clause-num { font-weight: bold; }
  .bnm-blockquote { border-left: 3px solid #003366; padding: 8px 16px; margin: 12px 0;
                    background: #f5f8ff; font-size: 11px; font-style: italic; color: #333; }
  .bnm-table { width: 100%; border-collapse: collapse; font-size: 11px; margin: 16px 0; }
  .bnm-table th { background: #003366; color: white; padding: 8px; text-align: left; }
  .bnm-table td { border: 1px solid #ccc; padding: 8px; vertical-align: top; }
</style>
<div class="bnm-doc">
  <div class="bnm-page bnm-cover"> ... </div>
  <div class="bnm-page">
    <div class="bnm-header"><span>Open Finance</span><span>2 of N</span></div>
    <!-- section content -->
    <div class="bnm-footer"><span>Bank Negara Malaysia</span><span>Internal Draft — Not for Distribution</span></div>
  </div>
</div>
```

Entire document is editable in place (inherits `EditorPane`'s existing
contentEditable behavior — no new editing mechanism needed here). A one-time
dismissable banner reads "This draft has been inserted into the editor. You
may edit it directly." Suggests `/deliver` next.

### `/deliver` (was `/release`)
`DeliverPanel` (replacing `ReleasePanel`) shows:

```ts
const SUPERVISOR_EMAIL = "jarod.ng@bnm.gov.my";
const SUPERVISOR_NAME = "Jarod N.";
const SUPERVISOR_ROLE = "Policy Owner, Open Finance Division";
```

Name and role read-only; email pre-filled and editable. "Send for Review"
button; on confirm, shows "Draft submitted to Jarod N. (jarod.ng@bnm.gov.my)
for review." — mirroring today's tested pattern of updating both the panel
body and the command's `statusLine`.

## Welcome screen (`WelcomeScreen.tsx`, new)

Centered state shown when `messages.length === 0`:
- "Welcome, Aisyah." + subtitle: "I am your drafting assistant for the Open
  Finance PD · 2026 workstream."
- 2×2 grid, minimal labels with a left-border accent, no icons/emoji:
  "Explore Task" (`/explore-task`), "Brainstorm" (`/brainstorm`), "Draft
  Outline" (`/draft`), "Write Document" (`/write`).
- Clicking a button or sending any message triggers `fadeSlideUp`/slide-away
  to the thread view (reuses the existing `fadeSlideUp` keyframe already in
  `index.css`).

## Visual redesign (existing files, no new visual system)

- Chat panel: light background, assistant messages left-aligned with a small
  "C" monogram avatar (no bubble), user messages right-aligned pills in
  `--primary`. Every message keeps its `fadeSlideUp` entry.
- Input bar: full-width rounded bar, thin border + subtle shadow, placeholder
  "Type a message or / for commands...", send arrow active only with text.
  Autocomplete (`AutocompleteMenu`, already built) continues to float above
  the input — no changes to its logic, only to the commands it lists.
- All existing `--primary`/`--background`/`--card` CSS variables are reused;
  no new tokens are added to `index.css` beyond what a chat-panel layout pass
  needs (spacing/shadow utility classes if not already present as Tailwind
  utilities).

## Tone/emoji pass

Remove exclamation marks from system copy; no pictographic emoji exist today
(verified by grep) so this is a forward-looking constraint on all new copy,
not a removal task. The `✓` checkmark is retained as-is (test-asserted,
not an emoji).

## Files touched

**Modified:**
1. `CopilotChat.tsx` — drop intent-picker seed, rename lifecycle functions,
   welcome-screen integration, `/deliver` email-confirm handler.
2. `copilotV2Data.ts` — rename `SlashCommandId`/`SLASH_COMMANDS`, re-export
   from the two new content modules, `MISSING_FIELDS` constant, supervisor
   constants.
3. `MessageRenderer.tsx` — `DeliverPanel` (was `ReleasePanel`), `/draft`
   instructional-outline render path, `/explore-task` missing-fields form,
   emoji-free labels.
4. `copilotViews.tsx` — new `DraftInstructionCard`.
5. `ChatInput.tsx` — new command names in autocomplete (data-driven off
   `SLASH_COMMANDS`, likely no logic change needed).
6. `DraftingWorkspacePage.tsx` — mount `WelcomeScreen` conditionally.
7. `EditorPane.tsx` — enable the existing disabled B/I/U toolbar on
   selection.
8. `DraftingWorkspacePage.test.tsx` — updated in lockstep.

**New:**
9. `WelcomeScreen.tsx`
10. `copilotDraftOutline.ts`
11. `copilotFullDocument.ts`

## Out of scope

- No engine/API changes — this is entirely within the mocked
  `copilotV2Data.ts` fixture layer, consistent with "the API is a fixture
  projection" (`CLAUDE.md`).
- No live LLM calls anywhere — all command output stays scripted/timer-based.
- H (heading) and bullet-list toolbar buttons stay disabled — only Bold/
  Italic/Underline are wired, per the spec's explicit ask.
- Mobile/responsive layout is not a target; this is a desktop hackathon demo.
- No changes to `ED_Open_Finance_2025.html` itself — it's a reference only.
