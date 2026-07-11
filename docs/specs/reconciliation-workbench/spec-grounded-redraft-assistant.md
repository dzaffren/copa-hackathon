# Grounded Redraft Assistant & Word Write-Back

**Ticket:** TBD

This feature closes the loop between the Reconciliation Workbench and the drafter's real
working document. Aisyah drafts in **Microsoft Word** (saved to SharePoint for
collaboration, alongside Microsoft's own Copilot); our tool does **not** rebuild the
editor or compete as a general writing assistant. Instead, for a paragraph with an open
finding, our **grounded redraft assistant** proposes replacement wording that is backed by
a **verbatim clause from the source graph** — the one thing a general copilot cannot do,
because it has no access to BNM's sources. When Aisyah accepts a suggestion, it is written
back into her Word document as a **tracked change** via Microsoft Graph, the matching
finding is marked resolved across every view, and — once findings are resolved — she
submits the draft for her manager's approval with the verbatim-cited decision trail
attached as the justification pack.

> **Positioning — "Microsoft writes; we cite."** Microsoft Word + M365 Copilot already
> handle drafting, collaboration, and fluent text generation. Our differentiator is
> **source grounding**: every suggestion is tied to an exact, verifiable clause from the
> graph, or the assistant says "No matching clause found." Drafting stays in Word; we are
> the source-intelligence layer that makes the draft defensible.

## User Story

As Aisyah R., a Bank Negara Malaysia policy drafter who writes in Microsoft Word on
SharePoint, I want an assistant that suggests replacement wording backed by the exact
source clause it relies on, and writes my accepted suggestion back into my Word document as
a tracked change, so that resolving a finding reflects a real, source-grounded edit — not
just a checkbox — and my manager receives a draft whose every decision is backed by a
verifiable citation, without me leaving the document I already work in.

## Background & Context

**Current state:**

- Aisyah drafts in Microsoft Word, with the document saved to SharePoint so colleagues can
  collaborate, and Microsoft's own Copilot available in the ribbon. Drafting, comments, and
  tracked changes already happen there.
- In our companion tool she has uploaded the same draft, explored the sources connected to
  each paragraph, and reconciled individual connections into tracked notes and a
  verbatim-cited decision trail (those steps belong to the workspace and reconciliation
  features). She has, for example, flagged the Personal Data Protection Act §129 conflict on
  paragraph 4.6.
- Today the two worlds are disconnected: the source intelligence lives in our tool, the
  actual wording lives in Word, and nothing carries a source-grounded fix from one to the
  other.

**Problem:**

- **A general copilot writes fluently but cannot cite.** Microsoft's Copilot will happily
  redraft a clause, but it has no access to BNM's source graph, so it cannot back the wording
  with the exact BCBS / PDPA / OECD clause, cannot tie the change to a verdict, and cannot
  build the IMF-defensible decision trail. The drafter is left to hunt the citation herself.
- She can mark a flagged finding "resolved" in our tool without the conflicting sentence in
  her Word document ever changing. That lets a draft be certified "consistent" while the
  conflict still stands — actively misleading to the manager who signs it off.
- The source that prompted a change and the change itself live in separate places, so the
  reasoning behind each edit is lost.
- Nothing re-checks a paragraph after she edits it, so the tool can only reflect the wording
  she started with, never the wording she just wrote.

## Target User & Persona

- **Who:** Aisyah R., a Bank Negara Malaysia policy drafter and the domain expert. She
  drafts in Word; the assistant proposes source-grounded wording, and she decides and
  commits every change herself.
- **Context:** She has a paragraph with an open finding in our tool and wants a fix she can
  trust and trace — one backed by the exact source clause — written back into her real Word
  document, then to submit the clean draft for sign-off.
- **Current workaround:** Rewrites clauses by hand in Word, re-reads the source from memory
  or a private note (or asks a general copilot that can't cite the clause), and emails the
  draft to her manager with no attached record of why each clause says what it says.

## Goals

- Read the drafter's paragraphs from her Word document (on SharePoint) so our tool works
  against the same text she is actually drafting — not a separate copy she has to keep in
  sync.
- Offer a **grounded redraft assistant** that, for a selected or flagged paragraph, proposes
  replacement wording grounded in that paragraph's connected sources — and, where relevant,
  in a grounded search restricted to an approved list of authoritative sources — with every
  source it used quoted **verbatim** and archived so the result stays reproducible.
- Never generate ungrounded text: if no source supports a suggestion, the assistant says
  "No matching clause found" rather than writing plausible-but-uncited prose (the distinction
  from a general copilot).
- Write an accepted suggestion back into the Word document as a **tracked change** via
  Microsoft Graph — AI proposes, human commits — never a silent or final edit.
- Close the loop so accepting a suggestion both writes the tracked change and marks the
  matching finding resolved, with every view reflecting the one shared state — and so a
  finding can only be resolved by a real edit or a reasoned dismissal, never a bare "mark
  resolved".
- Let her re-run analysis on a paragraph she has just edited so the tool re-finds the
  connections that apply to the new wording.
- Let her submit the draft for the approving manager's sign-off once findings are resolved,
  with the verbatim-cited decision trail attached as the justification pack.

## Non-Goals

- **Rebuilding a text editor or a general writing assistant.** Drafting, formatting,
  collaboration, comments, and fluent free-text generation stay in Microsoft Word and M365
  Copilot. We do not reproduce them. Our assistant only proposes **source-grounded** wording.
- **Competing with Microsoft Copilot on ungrounded drafting.** If a request can't be tied to
  a source clause, our assistant declines with "No matching clause found" — it is not a
  general-purpose writer.
- **Generating the connections and verdicts.** Deciding which sources bear on a paragraph and
  proposing each verdict belongs to the connection engine feature.
- **Creating the per-verdict tracked notes and the decision trail.** Pulling a principle in,
  anchoring a cross-reference, noting a gap, or flagging a conflict — and accumulating those
  into the trail — belongs to the connection reconciliation feature. This feature owns the
  **body-text write-back** to Word, the shared-state resolve tied to that real edit, the
  edit-then-analyse trigger, and submission.
- **Generating cross-source insights.** The "what you might have missed" cards belong to the
  cross-source insights feature. This feature does accept a **carried insight** as an entry
  point — the assistant opens pre-loaded with the insight's paragraphs and cited sources —
  but it never generates the insights themselves.
- **The drift monitor.**
- **The approving manager's own review-and-sign-off screen.** This feature owns only the
  drafter's submit action and the resulting notification; the manager's approval interface is
  out of scope for MVP1.

## Word / SharePoint integration (how it actually works)

> This section makes the integration explicit so it is not mistaken for rebuilding Word.

- **Where drafting happens:** in Microsoft Word, on a document stored in SharePoint. Our tool
  is a **companion web app**, not an editor.
- **Read path:** our tool reads the document's paragraphs from SharePoint (via Microsoft
  Graph) so its analysis runs against the real, current text.
- **Write path:** an accepted suggestion is written back into the Word document as a **tracked
  change** (an insertion Word shows, and the drafter or a collaborator can review, accept, or
  reject inside Word) via Microsoft Graph. Our tool never finalises the text — Word's own
  accept/reject on the tracked change is the final human step.
- **Demo reality (honest labelling):** for the hackathon, the read/write-back is shown as a
  **mock tracked change** in a browser-held working copy; the live Microsoft Graph read/write
  against SharePoint is the **documented production path**, clearly labelled as such and not
  claimed to be running live. The draft text is a constructed what-if; the verifiable content
  is the cited sources.

## User Workflow

1. **Draft in Word, analyse in the companion tool** — Aisyah writes in her Word document on
   SharePoint. Our tool reads its paragraphs and shows the sources and findings on each — for
   example, the PDPA §129 conflict on paragraph 4.6.
2. **Ask the assistant for a source-grounded fix** — On a paragraph with an open finding, she
   asks the grounded redraft assistant to propose wording. It draws on the paragraph's
   connected sources and, where relevant, a grounded search across the approved source list,
   then proposes replacement wording that quotes **verbatim** the exact passages it relied on
   and names each source.
3. **Review the proposal** — She reads the proposed wording beside her current text, with the
   supporting quotes and their sources shown and each marked verified or illustrative. If the
   assistant found nothing to support the ask, it says so plainly rather than inventing a
   source (unlike a general copilot, which would write uncited prose).
4. **Accept or reject** — If she accepts, the wording is written back into her Word document as
   a tracked change (which she can still review, accept, or reject in Word), and the matching
   finding is marked resolved everywhere. If she rejects, the document is left exactly as it
   was.
5. **Re-analyse the edited paragraph** — After editing in Word or accepting a suggestion, she
   runs "Analyse this paragraph" so the tool re-finds the connections that apply to the new
   wording.
6. **Submit for approval** — When her findings are resolved, she submits the draft for her
   manager's sign-off. Submission attaches the verbatim-cited decision trail as the
   justification pack and notifies the manager. If any finding is still open, submission is
   blocked and she is shown what remains.

## Acceptance Criteria

> All scenarios are from Aisyah's perspective, on the _Discussion Paper on AI in the Malaysian
> Financial Sector_ (August 2025) demo vehicle and its real connected sources. Drafting
> happens in Word on SharePoint; our tool proposes source-grounded wording and writes accepted
> suggestions back as tracked changes. The assistant never finalises text — it proposes,
> Aisyah commits, and Word's tracked-change accept is the final step.

### Scenario: The tool reads the drafter's paragraphs from her Word document

```gherkin
Given Aisyah's draft is a Microsoft Word document stored on SharePoint
When she opens it in the companion tool
Then the tool shows her paragraphs read from that document, including 3.5 (Fair usage & bias), 3.11 (GenAI hallucinations) and 4.6 (Data & personal information)
  And the tool works against the same text she drafts in Word rather than a separate copy
  And the tool does not offer to replace Word as her editor
```

### Scenario: Asking the assistant for a source-grounded fix to the PDPA conflict on 4.6

```gherkin
Given paragraph 4.6 (Data & personal information) has an open finding: a Conflict with the Personal Data Protection Act 2010 (amended 2024) §129
When Aisyah asks the grounded redraft assistant to propose a fix for paragraph 4.6
Then she sees proposed replacement wording that names the cross-border transfer test from PDPA §129
  And the proposal quotes verbatim the exact passage it relied on: "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act; or (b) that place ensures an adequate level of protection…"
  And the proposal names its source as the Personal Data Protection Act 2010 (amended 2024) §129
  And the proposed wording is shown beside her current paragraph 4.6 text, not yet written to the Word document
```

### Scenario: The assistant opens pre-loaded from a carried cross-source insight

```gherkin
Given Aisyah carried the cross-source implication about paragraphs 3.5 and 4.6 from the insights view
When the grounded redraft assistant opens
Then it is pre-loaded with paragraphs 3.5 and 4.6 and the insight's cited sources (OECD 1.2, NIST MEASURE 2.11, BCBS 239)
  And she can ask it to propose wording adding the missing pre-deployment data bias assessment
  And no change is written to her Word document until she accepts a proposal
```

### Scenario: The assistant cites its sources verbatim and marks each verified or illustrative

```gherkin
Given Aisyah has asked the assistant to propose wording for paragraph 3.5 (Fair usage & bias) grounded in its connected sources
When the assistant returns its proposal
Then every source it relied on is shown with its exact passage quoted, its clause or section number, and its source name
  And a passage checked word-for-word is marked "verified"
  And a passage not yet checked is marked "illustrative — not yet verified" and is never presented as verified
  And no passage is paraphrased or invented and shown as if it were a quote
```

### Scenario: The assistant will not produce ungrounded wording (the distinction from a general copilot)

```gherkin
Given Aisyah asks the assistant to add a numeric capital-buffer percentage to paragraph 4.6 (Data & personal information)
  And no connected source and no approved-list source supports such a figure for that paragraph
When the assistant responds
Then she sees "No matching clause found" for that request
  And no wording with an unsupported figure is proposed
  And no source passage is fabricated to justify the change
  And she is reminded that ungrounded free-text drafting belongs in Word, not this assistant
```

### Scenario: Accepting a suggestion writes a tracked change to Word and resolves the finding

```gherkin
Given the assistant has proposed wording for paragraph 4.6 that resolves the PDPA §129 conflict
When Aisyah accepts the proposal
Then the accepted wording is written into her Word document as a tracked change she can review, accept, or reject in Word
  And the document is not silently or finally overwritten
  And the PDPA §129 conflict finding on paragraph 4.6 is marked resolved
  And the resolution records that it reflects a real edit to paragraph 4.6
```

### Scenario: Accepting a suggestion updates every view live off one shared state

```gherkin
Given Aisyah has accepted the assistant's wording for paragraph 4.6 that resolves the PDPA §129 conflict
When she opens the reconciliation view without reloading it herself
Then the PDPA §129 finding on paragraph 4.6 reads as resolved there too
  And the decision trail shows the resolution was made by an accepted edit to paragraph 4.6
  And the workbench, the reconciliation view, and the trail all reflect the same single finding state
```

### Scenario: Rejecting a suggestion leaves the Word document unchanged

```gherkin
Given the assistant has proposed wording for paragraph 3.5 (Fair usage & bias)
When Aisyah rejects the proposal
Then paragraph 3.5 keeps its original wording with no tracked change written to Word
  And no finding on paragraph 3.5 is marked resolved
  And she can ask the assistant for a different proposal
```

### Scenario: Strengthening 3.5 with the connected OECD human-oversight principle

```gherkin
Given paragraph 3.5 (Fair usage & bias) is connected to OECD AI Principles 1.2 with the verdict Consensus
When Aisyah asks the assistant to strengthen paragraph 3.5 with the connected OECD principle and accepts the proposal
Then the proposal quotes verbatim: "AI actors should implement mechanisms and safeguards, such as capacity for human agency and oversight, including to address risks arising from uses outside of intended purpose."
  And the proposal names its source as OECD AI Principles 1.2
  And the accepted wording is written into paragraph 3.5 as a tracked change that names human agency and oversight
  And the OECD Consensus finding on paragraph 3.5 is marked resolved as reflecting a real edit
```

### Scenario: Grounded search is restricted to the approved source list, cited and archived

```gherkin
Given Aisyah asks the assistant to reinforce paragraph 3.11 (GenAI hallucinations) with the latest peer-regulator position
When the assistant runs a grounded search to answer
Then it searches only sources on the approved list of authoritative sources (central banks, standard-setters, and major regulatory wires)
  And any result it returns is shown with its exact passage quoted verbatim and its source named
  And the result is archived so this finding can be reproduced later from the same evidence
```

### Scenario: The assistant does not return a source outside the approved list

```gherkin
Given Aisyah asks the assistant a question whose only apparent answer sits on an unapproved website
When the assistant runs a grounded search
Then it does not present that unapproved source as evidence
  And it either returns an approved-list source that supports the point or states "No matching clause found"
```

### Scenario: Re-analysing an edited paragraph re-finds connections on the new wording

```gherkin
Given Aisyah has edited paragraph 4.6 (Data & personal information) so it now names the PDPA cross-border transfer test
When she runs "Analyse this paragraph" on paragraph 4.6
Then the tool re-finds the connections that apply to the new wording
  And she sees the updated set of sources connected to paragraph 4.6 as re-analysed
  And any finding the edit has addressed is no longer shown as an open connection on paragraph 4.6
```

### Scenario: Trying to submit with an unresolved finding is blocked

```gherkin
Given the PDPA §129 conflict on paragraph 4.6 is still open
When Aisyah tries to submit the draft for manager approval
Then submission is blocked
  And she is shown that paragraph 4.6's PDPA §129 conflict remains unresolved
  And she is offered a way to open it and resolve it
  And the draft is not sent to the manager
```

### Scenario: A finding cannot be marked resolved without a real edit or a reasoned dismissal

```gherkin
Given the PDPA §129 conflict on paragraph 4.6 is still open
  And paragraph 4.6's conflicting wording in Word has not been changed
When Aisyah attempts to mark the finding resolved without accepting a suggestion or dismissing it with a reason
Then the finding is not marked resolved
  And she is told the finding can only be resolved by an accepted edit to the text or a dismissal with a recorded reason
  And she cannot certify the draft consistent while the conflicting text still stands
```

### Scenario: A dismissed finding with a recorded reason counts as resolved for submission

```gherkin
Given the industry-feedback finding on paragraph 4.6 is open
When Aisyah dismisses it as "not relevant" and records why
Then the finding counts as resolved for submission purposes
  And her recorded reason is kept in the decision trail so a reviewer can see what was considered and set aside
```

### Scenario: Submitting with all findings resolved succeeds and notifies the manager

```gherkin
Given every finding on the draft has been resolved by an accepted edit or a dismissal with a recorded reason
When Aisyah submits the draft for manager approval
Then the submission succeeds
  And the approving manager is notified that the draft is ready for sign-off
  And the verbatim-cited decision trail is attached as the justification pack behind every resolved finding
  And Aisyah sees confirmation that the draft has been submitted for approval
```

### Scenario: The Word write-back is honestly labelled as a demonstration in the demo

```gherkin
Given Aisyah has accepted a suggestion for paragraph 4.6 in the demo
When the tracked change is applied
Then it is shown as a tracked change in a browser-held working copy for the demo
  And it is clearly labelled that the live Microsoft Graph write-back to the Word document on SharePoint is a documented production path, not the demo behaviour
  And the draft remains the constructed what-if it is honestly labelled to be, while the cited sources are the verifiable content
```

## Business Rules & Constraints

- **Microsoft writes; we cite.** Drafting, formatting, collaboration, and ungrounded
  free-text generation stay in Microsoft Word and M365 Copilot. Our assistant only proposes
  wording it can back with a verbatim source clause; a request that cannot be grounded is
  declined with "No matching clause found," not answered with uncited prose.
- **AI proposes, the human commits.** The assistant never finalises policy text. Every
  proposal must be accepted or rejected; accepting writes a tracked change to Word (which the
  drafter can still review, accept, or reject in Word), and rejecting leaves the document
  unchanged. No assistant output is ever written without her acceptance.
- **Verbatim-citation guardrail.** Every proposal quotes the exact passage it relies on, with
  its clause or section number and source name. If no supporting passage exists, the assistant
  states "No matching clause found" and never invents, paraphrases-as-quote, or asserts an
  unsupported source.
- **Verbatim-integrity marking.** Every quote the assistant shows is marked "verified" (checked
  word-for-word) or "illustrative" (not yet verified); an illustrative quote is visibly
  distinct and never shown as verified.
- **Grounded search is allowlist-only and archived.** When the assistant searches beyond the
  connected sources, it searches only the approved list of authoritative sources (central
  banks, standard-setters, major regulatory wires). Every result it uses is cited verbatim and
  archived so the finding stays reproducible; a source outside the approved list is never
  presented as evidence.
- **Write-back is to the real document via Microsoft Graph.** An accepted suggestion is
  written into the Word document on SharePoint as a tracked change through Microsoft Graph, so
  the source intelligence and the drafting surface stay in sync. In the demo this is a mock
  tracked change in a browser-held copy, with the live Graph write-back documented as the
  production path.
- **Resolving requires a real edit or a reasoned dismissal.** A finding is marked resolved only
  when Aisyah accepts a suggestion that changes the text, makes the change herself in Word, or
  dismisses the finding with a recorded reason. A finding can never be marked resolved while
  its conflicting text still stands and no reason is recorded — the drafter cannot certify a
  draft consistent when the conflict remains.
- **Dismissal records a reason and counts as resolved.** A dismissed finding requires a
  recorded reason, kept in the decision trail, and then counts as resolved for submission
  purposes.
- **One shared finding state across every view.** The workbench, the reconciliation view, the
  trail, and the assistant read and write one shared finding state. Accepting a suggestion
  updates the draft, resolves the matching finding, and is reflected live in every view
  without Aisyah switching pages to learn the current state.
- **Edit-then-analyse is a drafter action.** After Aisyah edits a paragraph, she can re-run
  analysis on that paragraph so the tool re-finds the connections that apply to the new wording.
- **Submission gate.** The draft can be submitted for manager approval only when every finding
  is resolved (by an accepted edit or a dismissal with a reason). Submitting attaches the
  verbatim-cited decision trail as the justification pack and notifies the approving manager;
  there is no separate reviewer persona in MVP1.
- **Honest labelling.** The draft is a constructed what-if and is labelled as such; the
  verifiable content is the cited sources. The Word write-back is a demonstration mock in the
  demo, with the live Microsoft Graph integration documented as the production path.

## Success Metrics

- **Source-grounded edits:** every suggestion the assistant offers is backed by a verbatim
  source clause, or is declined with "No matching clause found"; a suggestion with uncited or
  unverifiable wording is treated as a defect — this is the measurable difference from a
  general copilot.
- **Real-edit resolution:** every finding marked resolved is backed either by an accepted edit
  to the text or a dismissal with a recorded reason — zero findings resolved while the
  conflicting text still stands.
- **Reproducible grounded results:** every grounded-search result used in a proposal is
  archived and can be reproduced from the same cited evidence.
- **Live shared state:** accepting a suggestion resolves the matching finding in every view
  without the drafter reloading or switching pages.
- **Loop completion:** in the demo, Aisyah completes the acting loop — ask for a grounded
  suggestion → accept as a tracked change to Word → finding resolved everywhere → re-analyse
  → submit for approval with the trail attached.

## Dependencies

- **Microsoft Word + SharePoint + Microsoft Graph** — the drafter's real drafting surface and
  the read/write-back channel. Word and M365 Copilot own drafting; Graph is the API for
  reading paragraphs and writing tracked changes. (Demo: mock tracked change; production: live
  Graph integration.)
- **The Upload & reconciliation workspace** — supplies the paragraph view and the
  paragraph-to-source connections the assistant grounds on.
- **The Connection reconciliation & decision trail feature** — supplies the findings this
  feature resolves and the verbatim-cited trail this feature attaches at submission; that
  feature owns the per-verdict tracked notes, while this feature owns the body-text write-back
  and the shared-state resolve.
- **The connection engine** — supplies each connection's source passage, verification status,
  and the material the assistant grounds its proposals on.
- **The curated source library and the approved source list** — provide the connected sources
  and the allowlist the assistant's grounded search is restricted to.
- **The approving manager** — receives the submitted draft and the attached justification pack;
  the manager's own approval interface is out of scope for this feature.

## Open Questions

- [x] ~~Should we build our own editable draft surface and drafting copilot?~~ — **Resolved:**
      no. Drafting stays in Microsoft Word on SharePoint (with M365 Copilot available); we do
      not rebuild the editor or compete as a general writer. Our tool is a **companion web app**
      that reads the Word document and writes accepted, source-grounded suggestions back as
      tracked changes via Microsoft Graph. Positioning: "Microsoft writes; we cite."
- [x] ~~What distinguishes our assistant from Microsoft Copilot?~~ — **Resolved:** source
      grounding. Our assistant only proposes wording backed by a verbatim clause from the
      graph, or declines with "No matching clause found." A general copilot writes fluent but
      uncited text and cannot build the IMF-defensible trail; that grounding is our moat.
- [x] ~~Does accepting a suggestion rewrite the paragraph body text, or only record a note?~~ —
      **Resolved:** it writes the replacement body text into Word as a tracked change. The
      per-verdict tracked notes (guiding principle, cross-reference, gap, conflict flag) belong
      to the reconciliation feature; body-text write-back belongs here.
- [x] ~~Can a finding be marked resolved without changing the text?~~ — **Resolved:** no. A
      finding is resolved only by an accepted edit or a dismissal with a recorded reason,
      closing the gap where a draft could be certified consistent while the conflict still
      stands.
- [x] ~~Is there a separate reviewer who signs the draft off?~~ — **Resolved:** no. In MVP1 the
      drafter submits directly to the approving manager for sign-off; there is no separate
      reviewer persona.
- [x] ~~May the assistant's grounded search use the open web?~~ — **Resolved:** no. Grounded
      search is restricted to an approved list of authoritative sources, and every result is
      cited verbatim and archived for reproducibility.
- [ ] **How much of the Word/Graph write-back is shown live in the demo versus mocked?** —
      **Deferred (non-blocking):** MVP1 demonstrates the write-back as a mock tracked change in
      a browser-held copy, with the live Microsoft Graph read/write against SharePoint as the
      documented production path. How much of the live Graph round-trip can be shown safely is
      settled during implementation and honestly labelled either way.
- [ ] **Should our tool run as a Word add-in (task pane) rather than a separate companion
      web app in a later phase?** — **Deferred (non-blocking):** MVP1 is the companion web app
      with Graph write-back. A native Word task pane (living inside the ribbon) is a stronger
      in-context experience and a natural roadmap step, but does not change the MVP behaviour.
- [ ] **Should the assistant re-analyse an edited paragraph automatically on accept, or only
      when the drafter runs "Analyse this paragraph"?** — **Deferred (non-blocking):** MVP1
      exposes re-analysis as an explicit drafter action; automatic re-analysis on accept is a
      later convenience that does not change the acting loop.
- [ ] **When the drafter edits a paragraph directly in Word (not via the assistant), which
      findings, if any, should auto-resolve before she re-analyses?** — **Deferred
      (non-blocking):** MVP1 resolves findings on an accepted suggestion or a reasoned
      dismissal, and relies on re-analysis to reflect a direct manual edit; auto-resolving on
      manual edits is deferred.
