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
