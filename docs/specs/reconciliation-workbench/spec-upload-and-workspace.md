# Upload & Reconciliation Workspace

**Ticket:** TBD

This feature is the drafter's front door to the Reconciliation Workbench. The drafter uploads the policy document they are enhancing; the tool runs a visible, honestly-labelled analysis sequence that extracts the document's paragraphs, parses the sources it cites, retrieves those sources, matches its topics against a curated library of sources it did _not_ cite, and pulls in the industry feedback the published paper attracted. The drafter then lands in a workspace where their document is the canvas: selecting any paragraph reveals every source connected to it — each with its source type, verdict, verbatim quote, and a plain-language read of how it affects that paragraph. It replaces the slow, scattered, by-hand hunt for the sources that bear on a draft.

## User Story

As Aisyah R., a Bank Negara Malaysia policy drafter, I want to upload the document I am enhancing and immediately see every source that bears on each of its paragraphs — the ones it already cites and the relevant ones it did not — so that I can do my due diligence in one place instead of hunting through scattered standards, peer regulators, acts, and industry feedback by hand.

## Background & Context

**Current state:**

- When Aisyah enhances a policy document, she does her due diligence by scouring scattered sources — international standards (BCBS, FSB, OECD, NIST), peer regulators (MAS, OSFI, APRA), national acts (the Personal Data Protection Act, the Financial Services Act), Bank Negara Malaysia's own policies, and industry feedback on published papers.
- Each source lives somewhere different. Today Aisyah opens each one by hand, reads it, and mentally maps it back to the paragraph it touches.
- The document she is enhancing already names many of its own sources in its footnotes, but those citations are just titles — she still has to find, open, and read each cited document herself.

**Problem:**

- The research is slow, scattered, and manual, yet it is what most directly shapes the wording of the policy.
- Reading sources one at a time, Aisyah cannot easily see which paragraph each source actually bears on, nor whether a source agrees with her draft, conflicts with it, exposes a gap, or duplicates an existing rule.
- Relevant sources the document did _not_ cite — where the real risk of a missed benchmark or a silent gap lives — are the hardest to find, because nothing in the document points to them.

## Target User & Persona

- **Who:** Aisyah R., a policy drafter at Bank Negara Malaysia, enhancing an in-progress policy document.
- **Context:** At the start of a drafting cycle, when she opens the document she is enhancing and needs to know which authoritative sources, peer regulators, acts, and industry comments bear on each paragraph before she starts changing wording.
- **Current workaround:** She keeps a personal list of sources, opens each one in a separate window, reads it, and notes by hand which paragraph it relates to — a process that lives only in her head and her notes.

## Goals

- Let Aisyah upload the document she is enhancing and see, transparently, each step the tool takes to analyse it.
- Present her document as a browsable canvas where every paragraph is clickable.
- For any selected paragraph, show every connected source with its source type, verdict, branch (cited / surfaced-not-cited / industry feedback), the verbatim supporting quote marked verified or illustrative, and a plain-language read of how it affects the paragraph.
- Let her supply a source the tool identified but could not retrieve, and add a source the curated library missed — both keyed to the paragraph.
- Be honest at every step about which parts are real (upload and extraction) and which are pre-prepared (the curated source set and the replayed analysis).

## Non-Goals

- **Acting on a connection.** Confirming or overriding a verdict, pulling a principle into the draft, flagging a conflict for resolution, or recording a decision trail is owned by the _Connection reconciliation & decision trail_ story. This story only links each connection out to that view via an "Open connection & act" affordance.
- **Cross-source insights.** Reasoning _across_ the connected sources to surface what the drafter might have missed is owned by the _Cross-source insights_ story.
- **Editing the draft or the grounded redraft assistant.** Changing the document's text (in Microsoft Word, via source-grounded suggestions written back through Microsoft Graph) is owned by the _Grounded redraft assistant & Word write-back_ story.
- **The drift monitor.** Alerting the drafter when a watched source changes is owned by the _Source drift monitor_ story.
- **The engine internals.** How connections are found and verdicts proposed is owned by the _Two-branch source connection engine_ story.

## User Workflow

1. **Start with the open document** — Aisyah opens the Workbench and sees an upload area inviting her to upload the policy she is drafting. A demo shortcut lets her use the real, public _Discussion Paper on AI in the Malaysian Financial Sector_ (August 2025).
2. **Upload** — She uploads the document (or takes the demo shortcut). The upload area is replaced by a labelled analysis sequence that names the document she uploaded.
3. **Watch the analysis run** — The tool works through visible, labelled steps in order: extract the paragraphs and structure, parse the sources the document cites, retrieve those cited sources (noting any it could not retrieve), match paragraph topics to relevant un-cited library sources, pull in industry feedback on the published paper, and analyse every connection. Each step completes before the next begins.
4. **See the analysis-complete summary** — When every step finishes, she sees an "Analysis complete" summary — for example, "10 connections across 3 paragraphs analysed in depth, 6 more ready to analyse, 5 source types, 1 source it couldn't retrieve (you can supply it)" — and an option to open the workspace.
5. **Explore her document** — In the workspace her document is the canvas on the left: real extracted paragraphs, each showing its number, a short title, and a count of connected sources. She selects a paragraph.
6. **Read the connected sources** — The right rail lists every source connected to the selected paragraph. Each connection shows a source-type dot, a verdict badge (Consensus / Conflict / Gap / Duplicate / Partial), a branch tag (cited in your doc / surfaced-not-cited / industry feedback), the verbatim quote marked verified or illustrative, and a plain-language "how it affects this paragraph" read. If the paragraph was analysed but nothing bears on it, the rail shows "No matching source found." A source-type legend and a running count of connected sources are always visible.
7. **Handle a blocked source** — Where the tool identified a source but could not retrieve it, the connection shows a "couldn't retrieve" card with an option to upload the source. Once she supplies it, it becomes a normal analysed connection.
8. **Add a missing source** — Where she knows a source the library missed, she adds it to the selected paragraph; it is recorded against that paragraph.
9. **Hand off to reconcile** — From any connection she follows "Open connection & act" into the reconciliation view (owned by another story) to decide what to do about it.

## Acceptance Criteria

> All scenarios are from Aisyah's perspective. Behaviour is grounded in the _Discussion Paper on AI in the Malaysian Financial Sector_ (August 2025) demo vehicle and its real connected sources.

### Scenario: Uploading the open document starts the analysis sequence

```gherkin
Given I am on the Workbench start screen
  And I see an upload area with a demo shortcut for the "Discussion Paper on AI in the Malaysian Financial Sector (August 2025)"
When I upload the document
Then the upload area is replaced by an analysis sequence
  And the sequence names the document as "AI in the Malaysian Financial Sector (Discussion Paper)" from Bank Negara Malaysia, August 2025
  And I see a note that upload and extraction are real while the analysis replays a pre-prepared result over a curated source set
```

### Scenario: Watching the analysis sequence run to completion

```gherkin
Given I have uploaded the Discussion Paper
When the analysis sequence runs
Then I see each step labelled and completed in order:
  | Step                                                                 | Detail I can read                                                        |
  | Extracting the document — paragraphs and structure                   | 73,601 characters · 54 numbered paragraphs                               |
  | Parsing the sources it cites                                         | found OECD, BCBS 239, FSB, NIST, MAS, PDPA and others                    |
  | Retrieving those cited sources                                       | 9 retrieved · 1 blocked because a source site blocks automated access    |
  | Matching paragraph topics to relevant sources it did not cite        | fairness · hallucination · personal data · cross-border transfer         |
  | Pulling in industry feedback on this published paper                 | Association of Banks and 3 financial-service-provider respondents        |
  | Analysing every connection — consensus / conflict / gap / duplicate  | plus surfacing cross-source insights                                     |
  And each step is marked done only after it finishes and before the next begins
```

### Scenario: Analysis-complete summary and entry to the workspace

```gherkin
Given the analysis sequence has finished all its steps
When the sequence completes
Then I see an "Analysis complete" summary reading "10 connections across 3 paragraphs analysed in depth · 6 more ready to analyse · 5 source types · 1 source it couldn't retrieve (you can supply it)"
  And I see an option to open the workspace
When I choose to open the workspace
Then I land in the workspace with my document shown as the canvas
```

### Scenario: The workspace opens with a paragraph selected and its sources shown

```gherkin
Given I have opened the workspace for the Discussion Paper
Then my document is shown on the left as clickable extracted paragraphs
  And each paragraph shows its number, a short title, and a count of connected sources
  And a running total of "sources connected" is shown
  And a source-type legend is shown listing international standard/principle, peer regulator, act/law, internal BNM, and industry feedback
  And paragraph 4.6 "Data & personal information" is selected by default — its PDPA §129 Conflict is the strongest opening hook — with its connected sources listed on the right
```

### Scenario: The whole document is browsable, with analysed paragraphs clearly marked

```gherkin
Given I have opened the workspace for the Discussion Paper
Then every one of the document's 54 extracted paragraphs is shown and selectable
  And between 8 and 10 paragraphs are fully analysed
  And each analysed paragraph carries a distinct marker showing its count of connected sources
  And each not-yet-analysed paragraph is visibly distinguished as "not yet analysed"
  And paragraphs 3.5, 3.11, and 4.6 are among the fully analysed paragraphs
```

### Scenario: Selecting a not-yet-analysed paragraph offers to analyse it live

```gherkin
Given I am in the workspace
When I select a paragraph that has not yet been analysed
Then the right rail shows that this paragraph is "not yet analysed"
  And no fabricated connections or quotes are shown for it
  And I am offered an option to "Analyse this paragraph"
```

### Scenario: Analysing a paragraph on demand finds its connections live

```gherkin
Given I have selected a not-yet-analysed paragraph
When I choose "Analyse this paragraph"
Then the tool analyses that paragraph and returns the sources that bear on it
  And each returned connection carries a verdict and a verbatim quote marked verified or illustrative
  And if no source in the library bears on the paragraph, I see "No matching clause found" rather than an invented connection
```

### Scenario: Selecting a paragraph reveals every source connected to it

```gherkin
Given I am in the workspace
When I select paragraph 4.6 "Data & personal information"
Then the right rail heading reads "Paragraph 4.6 — Data & personal information"
  And I see every source connected to paragraph 4.6, each showing a source-type indicator, a verdict badge, a branch tag, a verbatim quote, and a "how it affects this paragraph" read
```

### Scenario Outline: The connected sources shown for each analysed paragraph

```gherkin
Given I am in the workspace
When I select paragraph <paragraph>
Then I see a connection to <source> with verdict <verdict> tagged <branch>
  And the connection shows the plain-language read of how <source> affects <paragraph>

Examples:
  | paragraph                          | source                                             | verdict   | branch               |
  | 3.5 "Fair usage & bias"            | OECD AI Principles                                 | Consensus | cited in your doc    |
  | 3.5 "Fair usage & bias"            | NIST AI Risk Management Framework                  | Gap       | surfaced — not cited |
  | 3.5 "Fair usage & bias"            | BNM Fair Treatment of Financial Consumers          | Duplicate | surfaced — not cited |
  | 3.11 "GenAI hallucinations"        | BCBS 239                                           | Consensus | cited in your doc    |
  | 3.11 "GenAI hallucinations"        | EU AI Act (Regulation 2024/1689)                   | Gap       | surfaced — not cited |
  | 3.11 "GenAI hallucinations"        | Association of Banks industry feedback (agree)     | Consensus | industry feedback    |
  | 4.6 "Data & personal information"  | PDPA 2010 (as amended 2024), §129                  | Conflict  | surfaced — not cited |
  | 4.6 "Data & personal information"  | BCBS 239                                           | Consensus | cited in your doc    |
  | 4.6 "Data & personal information"  | 3 FSP respondents industry feedback (partial)      | Partial   | industry feedback    |
```

### Scenario: A verified quote is shown for a connection on a cited source

```gherkin
Given I am in the workspace
  And paragraph 3.5 "Fair usage & bias" is selected
When I read the OECD AI Principles connection
Then I see the verbatim quote "AI actors should implement mechanisms and safeguards, such as capacity for human agency and oversight, including to address risks arising from uses outside of intended purpose."
  And the quote is marked "✓ verbatim — verified against source document"
```

### Scenario: An illustrative quote is clearly distinguished from a verified one

```gherkin
Given I am in the workspace
  And paragraph 3.5 "Fair usage & bias" is selected
When I read the BNM Fair Treatment of Financial Consumers connection
Then I see the verbatim quote "A financial service provider must ensure that financial consumers are treated fairly at all stages of their relationship with the financial service provider."
  And the quote is marked "◦ illustrative quote — not yet verified against source"
  And this illustrative marking is visibly distinct from a verified marking
```

### Scenario: A source the tool could not retrieve is shown as a blocked connection

```gherkin
Given I am in the workspace
  And paragraph 3.5 "Fair usage & bias" is selected
When I read the connections
Then I see a connection for "MAS — FEAT Principles (Fairness)" marked "couldn't retrieve"
  And it explains the source was identified as a likely peer benchmark for 3.5 but could not be retrieved automatically because the source site blocks automated access
  And it offers an option to "Upload this source"
  And no verdict badge or quote is shown for it until it is supplied
```

### Scenario: Supplying a blocked source turns it into a normal analysed connection

```gherkin
Given paragraph 3.5 "Fair usage & bias" is selected
  And the "MAS — FEAT Principles (Fairness)" connection is marked "couldn't retrieve"
When I choose to upload that source
Then the connection updates to show "you supplied it"
  And it explains the tool can now quote it verbatim and analyse this connection like any other source
  And it is no longer offered as a source to upload
```

### Scenario: Adding a source the library missed, keyed to the selected paragraph

```gherkin
Given I am in the workspace
  And paragraph 3.11 "GenAI hallucinations" is selected
  And the running total of connected sources is 10
When I add the source "IOSCO — AI in capital markets (2025)" to this paragraph
Then a new connection for "IOSCO — AI in capital markets (2025)" appears for paragraph 3.11 marked as added by me
  And it notes the tool will link it to this paragraph and analyse the connection
  And the running total of connected sources increases to 11
```

### Scenario: Every connection offers a way to open it in the reconciliation view

```gherkin
Given I am in the workspace
  And paragraph 4.6 "Data & personal information" is selected
When I read the PDPA §129 connection
Then I see an "Open connection & act" option on the connection
When I follow "Open connection & act"
Then I am taken to the reconciliation view for that connection
```

### Scenario: Nothing selected yet shows an empty prompt in the right rail

```gherkin
Given the workspace has just opened and no paragraph is selected
Then the right rail shows a prompt to "Select a paragraph on the left"
  And no connections are listed
```

### Scenario: The honest labelling of real-versus-prepared content is visible

```gherkin
Given I am using the Workbench for the Discussion Paper demo
When I view the start screen and the workspace
Then I see that upload and extraction are labelled as real
  And I see that the curated source set and the analysis are labelled as pre-prepared
  And I see that the extracted document paragraphs are labelled as real extracted text
  And no prepared content is presented as if it were live
```

### Scenario: The workspace reflects an added source without leaving the page

```gherkin
Given I am in the workspace
  And I have added the source "IOSCO — AI in capital markets (2025)" to paragraph 3.11
When I select another paragraph and then return to paragraph 3.11
Then the added source is still listed for paragraph 3.11
  And the running total of connected sources still reflects the added source
```

## Business Rules & Constraints

- **Verbatim-citation guardrail.** Every connection shown for a paragraph quotes the exact clause or passage it relies on, with its clause or paragraph number and source. Where no supporting passage can be shown — for example, a source the tool identified but could not retrieve — the connection must say so plainly and must not display an invented quote or verdict.
- **Verbatim-integrity marking.** Every displayed quote is marked either "✓ verified" (checked word-for-word against the source) or "◦ illustrative" (not yet verified). Illustrative quotes are visibly distinct and are never presented as verified. In the demo, OECD, NIST, BCBS 239, the EU AI Act, and PDPA §129 quotes are shown verified; the BNM Fair Treatment of Financial Consumers quote and the industry-feedback quotes are shown illustrative.
- **Two branches, clearly labelled.** Every connection is tagged with its branch: "cited in your doc" (parsed from the document's own references, yielding consensus or duplicate), "surfaced — not cited" (matched by topic against the curated library, yielding gap or conflict), or "industry feedback" (what the sector sent back on the published paper).
- **Five verdicts.** Every retrieved connection carries exactly one verdict — Consensus, Conflict, Gap, Duplicate, or Partial (a source that agrees in part and diverges in part; also the home for industry feedback marked "partial"). A blocked (not-yet-retrieved) source carries no verdict until it is supplied. An analysed paragraph with no bearing source shows "No matching source found," distinct from "not yet analysed." Confirming or overriding a verdict is out of scope here (owned by the reconciliation story).
- **Source types are first-class.** Every source is shown as one of: international standard/principle, peer regulator, act/law, internal BNM policy, or industry feedback. Industry feedback is analysed on the same footing as any top-down source and is categorised agree / partial / disagree — for example, the Association of Banks agrees with paragraph 3.11 (Consensus) while 3 FSP respondents partly agree with paragraph 4.6 (Partial: they support responsible data handling but reject the informed-consent mechanism for legacy datasets).
- **The drafter can add or supply sources.** As the expert, Aisyah can add a source the curated library missed and supply a source the tool identified but could not retrieve. Both are keyed to the selected paragraph. A supplied blocked source becomes a normal analysed connection; an added source is recorded against the paragraph and increases the connected-source count.
- **One shared state across the drafter's pages.** Sources Aisyah supplies or adds persist and are reflected live in the workspace — she does not switch pages to see the current state, and the connected-source count always reflects added sources.
- **A single editable document (MVP1).** The workspace centres on exactly one uploaded document; every connected source is read-only context. The uploaded document is honestly labelled as a constructed what-if for the demo — the verifiable content is the sources, not the draft text.
- **A fresh upload is a fresh session.** Starting a new upload clears any sources supplied or added in a prior session so the analysis begins clean.
- **Public data only.** The drafter experience runs entirely on published documents — the demo vehicle plus public external references. Confidential sources do not appear here with real content.

## Success Metrics

- **Fewer missed connections (recall):** across the 8–10 analysed paragraphs (with 3.5, 3.11, and 4.6 as the worked showcase examples), the workspace surfaces every known relevant source — including the un-cited ones (NIST, EU AI Act, PDPA §129) that an unaided drafter is most likely to miss.
- **Document depth:** the drafter can browse all 54 paragraphs and see that 8–10 carry full analysis, so the tool reads as a real document rather than a hand-picked trio; any paragraph can be analysed on demand.
- **Zero unsupported claims:** every connection shown quotes an existing passage verbatim, correctly marked verified or illustrative; a blocked source shows no quote or verdict until supplied. Any displayed quote that cannot be verified against its source, or is mismarked, is treated as a defect.
- **Time efficiency (MW10 KR3):** Aisyah can see every source that bears on a paragraph, with its verbatim quote and impact read, in one place — contributing to reconciling a draft against its sources at least 15% faster than the by-hand baseline.
- **Drafter control:** Aisyah can supply a blocked source and add a missed source, and both are reflected in the workspace and the connected-source count without leaving the page.

## Dependencies

- **The two-branch source connection engine** (separate story) supplies the connections, verdicts, branch tags, and verbatim quotes this workspace displays.
- **Demo vehicle:** the _Discussion Paper on AI in the Malaysian Financial Sector_ (August 2025), which extracts cleanly to 73,601 characters across 54 numbered paragraphs.
- **Curated source library:** a preloaded set of public references matched to the vehicle's topics — OECD AI Principles, NIST AI Risk Management Framework, BCBS 239, the EU AI Act (Regulation 2024/1689), the Personal Data Protection Act 2010 (as amended 2024), and the Fair Treatment of Financial Consumers policy — plus sample industry feedback.
- **The reconciliation view** (separate story) is the destination for the "Open connection & act" link on each connection.

## Open Questions

- [x] ~~Which verdict vocabulary is shown on a connection?~~ — **Resolved:** Consensus / Conflict / Gap / Duplicate / Partial (five verdicts), matching the epic's shared business rules. "Deviates" is a nuance recorded on a Gap, not a badge; "No matching source found" is a distinct state for an analysed-but-empty paragraph.
- [x] ~~Should a blocked source show a verdict before it is supplied?~~ — **Resolved:** No. A blocked source shows only that it was identified and could not be retrieved, plus the option to supply it; no verdict or quote appears until it is supplied, to preserve the verbatim-citation guardrail.
- [x] ~~Which quotes are verified versus illustrative in the demo?~~ — **Resolved:** OECD, NIST, BCBS 239, EU AI Act, and PDPA §129 are verified; the Fair Treatment of Financial Consumers quote and the two industry-feedback quotes are illustrative and visibly marked as such.
- [ ] Should adding a source let the drafter attach the source file at add-time (so it is analysed immediately), or only record the reference for later retrieval? — **Deferred (non-blocking):** the prototype records the reference and queues analysis; supporting an immediate file attach at add-time is an enhancement that does not block this story.
- [x] ~~Beyond the demo paragraphs, should every one of the document's 54 paragraphs be selectable in MVP1, or only the analysed ones?~~ — **Resolved:** MVP1 fully analyses **8–10 paragraphs** (with 3.5, 3.11, and 4.6 as the worked showcase examples), and every other paragraph is **selectable but shows "not yet analysed"** with an option to analyse it. This gives the document real depth rather than a hand-picked trio, and lets the drafter drive which paragraph is analysed next.
- [x] ~~Should analysed paragraphs be visually distinguished on the canvas?~~ — **Resolved:** yes. Analysed paragraphs carry a distinct marker with their connected-source count; not-yet-analysed paragraphs are visibly marked as such, so a viewer instantly sees where the depth is and that the rest can be analysed on demand.
- [x] ~~What happens when the drafter analyses a not-yet-analysed paragraph in the demo?~~ — **Resolved:** it runs **live** — the tool matches that paragraph against the preloaded curated library and returns real connections (or "No matching clause found"), for any of the 54 paragraphs. **Risk flagged:** live branch-② matching is proven on known pairs but not at scale across a large source universe; this is the acknowledged live-demo risk, mitigated by the verbatim-citation guardrail (no fabricated connections) and the curated library keeping the demo's universe bounded.
- [x] ~~What is the default-selected paragraph?~~ — **Resolved:** paragraph 4.6 (Data & personal information), because its PDPA §129 Conflict is the strongest opening hook for the demo.

---

> **Technical refinement (added by `/prd-refine`; re-platformed to Next.js on 2026-07-11).**
> Everything above is the approved product content and is unchanged. The sections below add
> the buildable detail. This is the **first** UI story to be refined, so it establishes the
> **shared technical spine** — the Next.js frontend, the read-API/snapshot contract, and the
> Zustand shared-state store — that the other four UI stories (reconciliation, insights,
> grounded redraft assistant, drift monitor) reuse verbatim. Read this spine there rather
> than re-deriving it. The stack decision and its rationale live in
> `frontend-nextjs-migration-design.md`.

## Shared Technical Spine (all UI stories)

- **Frontend = a Next.js + React app under `web/`.** Every drafter surface is a route in one
  **Next.js (App Router) + React + Tailwind + shadcn/ui** application at the repo-root `web/`
  directory, deployed to **Vercel** (per `CLAUDE.md`, updated 11 Jul 2026 — this supersedes
  the earlier "self-contained HTML, no build step" convention). The six legacy prototype
  pages under `docs/poc/drafter-knowledge-graph/` (`index.html`, `workspace.html`,
  `connections.html`, `insights.html`, `assistant.html`, `monitor.html`) are kept as the
  read-only **UX reference** the `web/` build follows — they are not extended as the live
  demo. Routes: `web/app/page.tsx` (upload), `web/app/workspace/page.tsx`,
  `web/app/connections/[id]/page.tsx`, `web/app/insights/page.tsx`,
  `web/app/assistant/page.tsx`, `web/app/monitor/page.tsx`.
- **Data source = the engine read API, with a bundled snapshot default.** Pages read
  connections/verdicts/paragraphs through one seam, `web/lib/data.ts`, which wraps the
  Two-Branch Source Connection Engine's routes (`GET /documents/{id}/paragraphs`,
  `GET …/paragraphs/{n}/connections`, `POST …/paragraphs/{n}/analyse`). A build-time exporter
  writes a JSON **snapshot** of those responses into `web/public/data/` so the demo runs with
  **no backend** (deploy-safe on Vercel/any static host). The `NEXT_PUBLIC_API_BASE` env var
  selects the source: unset → `fetch()` the bundled snapshot (default); a URL → call the live
  FastAPI engine (enables the live "analyse any paragraph" moment). Honestly labelled either
  way.
- **"One shared finding state" = a Zustand store (`web/lib/store.ts`) with `persist` to
  `localStorage`.** One store, imported as a `useStore` hook by every route/component, holds
  all drafter state in named slices. Zustand's `persist` middleware keeps it in
  `localStorage` (so state survives reload) and its cross-tab `storage` sync keeps every open
  tab live — the honest MVP1 realisation of "one shared state." **No backend write routes**
  (the engine is read-only, per its negative constraints); all drafter actions are
  client-side.
- **Store slices** (extended across stories; each story owns the ones it writes). These
  replace the earlier `rr_*` `localStorage` keys 1:1; the `persist` key namespace stays
  `rr` so the mental model carries over:
  | Slice       | Owner story            | Shape                                                                                                  |
  | ----------- | ---------------------- | ------------------------------------------------------------------------------------------------------ |
  | `sources`   | this story             | `{ "<para>": [ {title, source_type, added_by:"drafter"} ] }`                                           |
  | `blocked`   | this story             | `["<connection_id>", …]` (blocked sources the drafter supplied)                                        |
  | `verdicts`  | reconciliation         | `{ "<connection_id>": {verdict, status:"confirmed", why?} }`                                           |
  | `trail`     | reconciliation         | `[ {connection_id, paragraph, verdict, source, quote, verification, note_type} ]` (the decision trail) |
  | `resolved`  | grounded redraft asst. | `{ "<finding_id>": {kind:"edit"\|"dismissal", reason?} }`                                              |
  | `draft`     | grounded redraft asst. | `{ "<para>": {text, tracked_changes:[…]} }` (browser-held working copy)                                |
  | `watch`     | insights               | `[ {insight_id, source, added_at} ]` ("track this" watch-items)                                        |
  | `setAside`  | insights               | `["<insight_id>", …]`                                                                                  |
  | `submitted` | grounded redraft asst. | `{ submitted:true, trail:[…] }` \| null                                                                |
- **Testing.** **Vitest + React Testing Library** is the gate (store slices + guarantee-bearing
  components); **Playwright** hero flows are **optional/non-blocking**; backend `pytest`
  covers any engine/exporter change. (No E2E test may block the demo.)
- **Honesty labelling is a build requirement, not decoration:** every page renders the
  real-vs-prepared and verified-vs-illustrative markers from the data, never hard-codes a
  "verified" badge.

## Functional Requirements

- **Analyse sequence is scripted, not fetched.** The six-step sequence (`app/page.tsx`) is a
  timed client-side animation over a fixed step list; each step marks done before the next
  starts. It does **not** call the model — the "real" claim it makes is only about
  upload+extraction. The completion summary counts are read from the snapshot
  (`data/paragraphs.json` + `data/connections/*.json`) via `lib/data.ts`, never hard-coded,
  so they cannot drift from the data actually shown in the workspace.
- **Canvas renders all 54 paragraphs; 8–10 carry analysis.** `app/workspace/page.tsx` renders
  every paragraph from `data.fetchParagraphs()`. A paragraph with `state: "analysed"` shows
  its `connection_count` badge; `state: "not_analysed"` renders the muted "not yet analysed"
  marker and, on selection, the "Analyse this paragraph" affordance. Paragraph 4.6 is
  selected on first load.
- **Right rail renders connections verbatim from the engine payload.** For the selected
  paragraph, the rail (a `ConnectionRail` component) lists each connection with: source-type
  dot, verdict badge (`VerdictBadge`), branch tag (`cited` → "cited in your doc", `uncited` →
  "surfaced — not cited", `feedback` → "industry feedback"), the `quote.text` with its
  `verification` marker (`verified` → "✓ verbatim", `illustrative` → "◦ illustrative",
  `pending_extraction` → "pending extraction" placeholder — rendered by a shared `QuoteBlock`
  component), the `rationale` as the "how it affects this paragraph" read, and an "Open
  connection & act" link to `/connections/<connection_id>`. A connection with
  `status: "could_not_retrieve"` renders the blocked card (no verdict, no quote) plus "Upload
  this source"; `no_matching_source: true` renders "No matching source found"; `state:
"not_analysed"` renders the analyse prompt. These four states are mutually exclusive and
  visually distinct.
- **Live analyse of a bare paragraph.** "Analyse this paragraph" calls `data.analyse(n)`,
  which hits `POST …/paragraphs/{n}/analyse` when `NEXT_PUBLIC_API_BASE` is set; in snapshot
  mode it reads `data/connections/{n}.json` if present, else renders "No matching clause
  found." Either path renders returned connections through the same `ConnectionRail` — never
  a fabricated card.
- **Supply a blocked source (client-side).** Choosing "Upload this source" on a blocked
  connection calls `useStore.supplyBlocked(connId)` (appends to the `blocked` slice) and
  re-renders the card as "you supplied it — the tool can now quote it verbatim and analyse
  this connection." The demo does not actually retrieve the source; the state flip is honest
  MVP1 behaviour, labelled.
- **Add a missing source (client-side).** Adding a source to the selected paragraph calls
  `useStore.addSource(para, {title, source_type})` (appends `{…, added_by:"drafter"}` under
  that paragraph key in the `sources` slice), renders an "added by you" connection, and
  increments the running connected-source count.
- **Running count = engine connections + supplied + added, from the store.** The count and
  the added/supplied cards survive navigation to another paragraph and back (they read from
  the persisted store, not component memory).
- **A fresh upload clears the session.** Taking the upload/demo-shortcut on `app/page.tsx`
  calls `useStore.reset()` so every slice starts clean.
- **Idempotency.** Re-selecting a paragraph, re-adding an already-added source (same title +
  paragraph), or re-supplying an already-supplied blocked connection causes no duplicate card
  and no double-count.

### Validation & Business Rules

- Adding a source with an empty title is rejected inline ("Give the source a title"); no
  `sources` entry is written.
- The verification marker shown must equal the payload's `verification` field — a component
  may never upgrade `illustrative`/`pending_extraction` to `verified`. A mismatch is a defect
  (asserted by a `QuoteBlock` unit test).

## Permissions & Security

- **Scope:** public. Every byte derives from public BNM documents and public references; the
  read routes are public (unchanged from `engine/api.py`). No auth on the drafter surface.
- **No sensitive data:** the confidential handbook and any "own past positions" never appear
  with real content — the snapshot exporter must **skip** any node with
  `access: "restricted"` (reuse the engine's carve-out) so no restricted text lands in the
  tracked `web/public/data/` path. This is enforced by the confidentiality guard.
- **Input validation:** the added-source title is trimmed and length-capped (≤200 chars)
  before storage; the `[id]` route param is matched against known ids, and an unknown id
  renders the empty-rail prompt rather than throwing.

## API Design (consumed — owned by the engine story)

This story **consumes** the engine's read API through `web/lib/data.ts`; it defines no new
engine routes. The contract it relies on (see `spec-source-connection-engine.md` → "API
Design"):

- `GET /documents/{document_id}/paragraphs` → canvas paragraphs + `state` + `connection_count`.
- `GET /documents/{document_id}/paragraphs/{number}/connections` → the right-rail payload
  (connections with `branch`, `source`, `verdict`, `confidence`, `rationale`, `quote`;
  `no_matching_source`; `could_not_retrieve`/`pending_extraction` shapes).
- `POST /documents/{document_id}/paragraphs/{number}/analyse` → live analyse; returns the
  same shape as the `connections` route; `503 ANALYSE_UNAVAILABLE` is caught and rendered as
  "live analysis is temporarily unavailable — pre-analysed paragraphs are unaffected."

**New (owned here): the static snapshot exporter.** A script serialises the engine's built
artifacts into the Next.js app's `public/data/` directory so the deployed app needs no
server:

```
scripts/export_poc_snapshot.py
  reads  data/artifacts/{clause-index,graph,verdicts}.json
  writes web/public/data/paragraphs.json
         web/public/data/connections/{number}.json   (one per analysed paragraph)
  skips  any node with access == "restricted"
```

Example `data/paragraphs.json` (excerpt) — byte-shape mirrors `GET …/paragraphs`:

```json
{
  "document_id": "ai-dp-2025",
  "total_paragraphs": 54,
  "paragraphs": [
    {
      "number": "4.6",
      "title": "Data & personal information",
      "state": "analysed",
      "connection_count": 3
    },
    {
      "number": "3.5",
      "title": "Fair usage & bias",
      "state": "analysed",
      "connection_count": 4
    },
    {
      "number": "3.2",
      "title": "Board & senior management oversight",
      "state": "not_analysed",
      "connection_count": 0
    }
  ]
}
```

Example `data/connections/3.5.json` (excerpt) — mirrors `GET …/connections`, including a
blocked and an illustrative connection:

```json
{
  "paragraph": { "number": "3.5", "title": "Fair usage & bias" },
  "state": "analysed",
  "no_matching_source": false,
  "connections": [
    {
      "id": "ai-dp-2025:3.5::oecd:OECD 1.2",
      "branch": "cited",
      "source": {
        "document_id": "oecd-ai",
        "title": "OECD AI Principles",
        "source_type": "international_standard"
      },
      "verdict": "Consensus",
      "confidence": "High",
      "rationale": "OECD backs the fairness stance and adds a human-agency & oversight mechanism 3.5 does not yet name.",
      "quote": {
        "clause_number": "OECD 1.2",
        "text": "AI actors should implement mechanisms and safeguards, such as capacity for human agency and oversight, including to address risks arising from uses outside of intended purpose.",
        "verification": "verified"
      }
    },
    {
      "id": "ai-dp-2025:3.5::mas-feat",
      "branch": "uncited",
      "source": {
        "document_id": "mas-feat",
        "title": "MAS — FEAT Principles (Fairness)",
        "source_type": "peer_regulator"
      },
      "status": "could_not_retrieve",
      "reason": "The MAS site blocks automated access; upload the source to analyse this connection.",
      "verdict": null,
      "quote": null
    }
  ]
}
```

## Data Model & Artifacts

No database. State lives in two places:

- **Static snapshot** (read-only, produced by the exporter): `web/public/data/paragraphs.json`
  and `web/public/data/connections/{number}.json` above. Immutable per build; committed to the
  tracked `web/public/data/` path (public content only).
- **Zustand store (mutable, per browser, persisted to `localStorage`):** this story writes the
  `sources` and `blocked` slices (shapes in the spine table). All access goes through the
  `useStore` hook in `web/lib/store.ts` (`addSource(para, {title, source_type})`,
  `supplyBlocked(connId)`, `connectionsFor(para)` which merges snapshot + added, `reset()`).

## UI/Frontend Requirements

- **`web/app/page.tsx`** (new) — upload zone + demo shortcut; on start, `useStore.reset()`
  then run the scripted six-step analyse sequence; completion summary counts computed from the
  snapshot via `lib/data.ts`; "Open the workspace →" links to `/workspace`.
- **`web/app/workspace/page.tsx`** (new) — two-pane layout: left canvas of 54 paragraphs
  (analysed badge vs "not yet analysed"), right rail (`ConnectionRail`) of connections for the
  selected paragraph. Includes the source-type legend, running connected-source count,
  "Analyse this paragraph", "Upload this source" (blocked), "Add a source", and per-connection
  "Open connection & act". Default selection 4.6.
- **`web/lib/store.ts`** (new) — the shared Zustand store (`persist` to `localStorage`),
  exposing the `sources`/`blocked` slices plus `addSource`, `supplyBlocked`, `connectionsFor`,
  and `reset`. **Every** UI story extends this one store.
- **`web/lib/data.ts`** (new) — the read seam: `fetchParagraphs()`, `fetchConnections(para)`,
  `analyse(para)`; snapshot-vs-live selected by `NEXT_PUBLIC_API_BASE`.
- **Shared components** (`web/components/`): `ConnectionRail`, `VerdictBadge`, `QuoteBlock`
  (renders the verification marker), `SourceTypeDot` — reused by the reconciliation and
  insights stories.
- **States:** _Loading_ — skeleton rows while the snapshot/API resolves. _Empty (nothing
  selected)_ — right rail shows "Select a paragraph on the left." _Empty (analysed, no
  source)_ — "No matching source found." _Not analysed_ — muted marker + analyse prompt.
  _Blocked_ — "couldn't retrieve" card. _Error_ — snapshot/API failure shows "couldn't load
  the analysis — retry," never a blank canvas.

## Architecture Notes

- **New dependencies:** the frontend introduces the repo's first `package.json` — Next.js,
  React, Tailwind, shadcn/ui, and Zustand (dev: Vitest, React Testing Library, optional
  Playwright), all isolated under `web/`. The exporter uses the standard library plus the
  existing `engine` package — no new Python deps.
- **Integration points:** consumes the engine read API / snapshot via `lib/data.ts`;
  `lib/store.ts` is the shared store the other four UI stories extend; `components/` are shared;
  the "Open connection & act" link is the hand-off into the reconciliation story.
- **Deploy:** the Next.js app deploys to **Vercel** (the exporter runs in CI before the build
  so the bundled snapshot is fresh). The existing `.github/workflows/deploy-poc.yml`
  (GitHub Pages of the legacy HTML) is retained until `web/` reaches parity, then retired or
  repurposed — settled at parity (see `frontend-nextjs-migration-design.md`).

## Exemplar Files

- `docs/poc/drafter-knowledge-graph/workspace.html` — the legacy two-pane workspace and its
  `localStorage` helpers are the **UX reference** the `web/` workspace re-implements (layout,
  the four connection states, the running count).
- `docs/poc/drafter-knowledge-graph/index.html` — the legacy scripted analyse sequence, the
  reference for `app/page.tsx`.
- `engine/api.py` `create_app(...)` + `engine/tests/test_api.py` — the exact response shapes
  the snapshot must mirror and the fixture pattern the exporter test follows.

## Implementation Plan

### Sub-tasks

**Task 1: Scaffold the `web/` Next.js app + shared store/data seams** — _medium_

- Scaffold Next.js (App Router) + Tailwind + shadcn/ui under `web/`; add `lib/store.ts`
  (Zustand + persist, `sources`/`blocked` slices, `addSource`/`supplyBlocked`/`connectionsFor`/
  `reset`) and `lib/data.ts` (`fetchParagraphs`/`fetchConnections`/`analyse`, snapshot-or-live
  via `NEXT_PUBLIC_API_BASE`).
- Files: `web/package.json`, `web/app/layout.tsx`, `web/lib/store.ts`, `web/lib/data.ts`,
  `web/tailwind.config.ts` (+ scaffold defaults)
- SEQUENTIAL (foundation for every UI story)

**Task 2: Static snapshot exporter** — _medium_

- Serialise `data/artifacts/*` → `web/public/data/paragraphs.json` +
  `web/public/data/connections/{n}.json`; skip `access:"restricted"` nodes.
- Files: `scripts/export_poc_snapshot.py` (new),
  `engine/tests/test_export_poc_snapshot.py` (new)
- INDEPENDENT (needs the engine artifacts, but not the `web/` scaffold)

**Task 3: Upload + analyse sequence** — _small_

- `app/page.tsx`: `useStore.reset()`, run the scripted six-step sequence, compute summary
  counts from the snapshot, route to `/workspace`.
- Files: `web/app/page.tsx`
- SEQUENTIAL (depends on Tasks 1, 2)

**Task 4: Workspace canvas + right-rail renderer** — _large_

- `app/workspace/page.tsx` + `components/ConnectionRail`, `VerdictBadge`, `QuoteBlock`,
  `SourceTypeDot`: render 54 paragraphs with analysed/not-analysed markers; render the four
  connection states; legend + running count; default 4.6.
- Files: `web/app/workspace/page.tsx`, `web/components/*.tsx`
- SEQUENTIAL (depends on Tasks 1, 2)

**Task 5: Analyse-on-demand, supply-blocked, add-source** — _medium_

- "Analyse this paragraph" (live/snapshot), supply-blocked flip, add-source with count
  update, all through the store and reflected live.
- Files: `web/app/workspace/page.tsx`, `web/lib/store.ts`
- SEQUENTIAL (depends on Task 4)

**Task 6: Vercel deploy + CI snapshot step** — _small_

- Add Vercel config (or project settings) for the `web/` app; run the exporter in CI before
  build so `web/public/data/` ships fresh.
- Files: `web/vercel.json` (or CI workflow), `.github/workflows/*`
- INDEPENDENT

### Negative Constraints

- Do NOT add engine write routes or a server-side session store — shared state is the Zustand
  store persisted to `localStorage`.
- Do NOT export or commit any `access:"restricted"` node text into `web/public/data/`.
- Do NOT hard-code connection counts, verdicts, or "verified" badges — every marker renders
  from the data.
- Do NOT change the engine's `GET …/paragraphs` / `…/connections` contracts (owned by the
  engine story).
- Do NOT extend the legacy `docs/poc/drafter-knowledge-graph/*.html` pages as the live demo —
  they are the read-only UX reference only.

## Test Scenarios

**Test 1: Snapshot exporter mirrors the API shape and skips restricted nodes**

- Setup: a fixture `graph.json` with one `access:"public"` reference node and one
  `access:"restricted"` handbook node; a `verdicts.json` with a Consensus record for 3.5.
- Action: run `export_poc_snapshot.py` against a tmp artifacts dir.
- Expected: `data/connections/3.5.json` contains the public OECD connection with
  `verification:"verified"`; **no** field anywhere contains the restricted node's title or
  text; `paragraphs.json` `total_paragraphs == 54`.

**Test 2: Workspace renders the four connection states distinctly**

- Setup: `data/connections/3.5.json` with a verified OECD (Consensus), an illustrative BNM
  (Duplicate), and a `could_not_retrieve` MAS card; `3.2` `not_analysed`; a paragraph with
  `no_matching_source:true`.
- Action: render `<WorkspacePage>` (RTL), select 3.5, then 3.2, then the empty paragraph.
- Expected: 3.5 shows verified vs illustrative markers distinctly and a blocked card with no
  verdict/quote; 3.2 shows the analyse prompt; the empty paragraph shows "No matching source
  found" — four visually distinct states, no fabricated card.

**Test 3: Add-source persists and survives navigation (idempotent)**

- Setup: `<WorkspacePage>`, paragraph 3.11 selected, running count 10.
- Action: add "IOSCO — AI in capital markets (2025)"; select 4.6; return to 3.11; add the
  same source again.
- Expected: count reads 11 on first add, the IOSCO card is still present after navigating
  back (store persistence), and the second identical add does not create a duplicate or move
  the count to 12.

**Test 4: Supply-blocked flips the card without fabricating a quote**

- Setup: 3.5 selected, MAS FEAT `could_not_retrieve`.
- Action: choose "Upload this source."
- Expected: card re-renders as "you supplied it," is no longer offered to upload, and shows
  no fabricated verdict or quote; the store's `blocked` slice contains the connection id.

**Test 5: Fresh upload clears the whole store**

- Setup: `sources`, `trail`, `resolved` slices all populated.
- Action: take the demo shortcut on `app/page.tsx` (calls `useStore.reset()`).
- Expected: every slice is emptied; the workspace opens with only the snapshot connections and
  the running count matching the snapshot.

## Verification

Run the `verifier` skill (Python/pytest for the exporter; Vitest/RTL for the frontend).

### Backend Tests

- `engine/tests/test_export_poc_snapshot.py` (new) — Test 1 (shape parity + restricted-node
  skip; asserts `verification` markers pass through unchanged).

### Component / Unit Tests (Vitest + React Testing Library — the gate)

- `web/lib/store.test.ts` — Tests 3–5 (add-source idempotency + persistence, supply-blocked,
  `reset()`).
- `web/components/QuoteBlock.test.tsx` — the verification marker equals the payload field and
  is never upgraded (Validation rule).
- `web/app/workspace/*.test.tsx` — Test 2 (four connection states render distinctly).

### E2E Tests (Playwright — optional, non-blocking)

| Key Scenario                                         | Test file                          | Assigned sub-task |
| ---------------------------------------------------- | ---------------------------------- | ----------------- |
| Uploading the open document starts the analysis seq. | `web/e2e/upload-workspace.spec.ts` | Task 3            |
| The workspace opens with 4.6 selected + its sources  | `web/e2e/upload-workspace.spec.ts` | Task 4            |
| Adding a source the library missed                   | `web/e2e/upload-workspace.spec.ts` | Task 5            |

**Locator strategy:** `data-testid` on the paragraph rows (`para-<number>`), the connection
cards (`conn-<id>`), and the running count (`connected-count`). Flagged non-blocking — a red
E2E never blocks the demo; the Vitest gate above is authoritative.

## Open Questions (technical)

- [x] ~~Where does the deployed app get its data with no backend?~~ — **Resolved:** a
      build-time exporter (`scripts/export_poc_snapshot.py`) writes a JSON snapshot of the
      engine's read-API responses into `web/public/data/`; `lib/data.ts` +
      `NEXT_PUBLIC_API_BASE` switch between the bundled snapshot (default, deploy-safe) and a
      live engine.
- [x] ~~How is "one shared state" realised without a server?~~ — **Resolved:** a Zustand
      store (`web/lib/store.ts`) persisted to `localStorage`, imported as a `useStore` hook by
      every route; Zustand's cross-tab sync keeps open tabs live. No engine write routes.
- [ ] Should the analyse sequence's per-step timing be fixed or data-driven? — **Deferred
      (non-blocking):** MVP1 uses fixed timings; deriving them from real extraction time is a
      later polish that does not change the steps shown.
