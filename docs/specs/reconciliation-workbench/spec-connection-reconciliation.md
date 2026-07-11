# Connection Reconciliation & Decision Trail

**Ticket:** TBD

When Aisyah opens one of the sources connected to a paragraph of her open draft, this
feature puts her paragraph and the connected source side by side, shows the AI's proposed
verdict (Consensus, Conflict, Gap, Duplicate, or Partial) with the exact source passage quoted
verbatim and a plain-language read of how it affects her paragraph, and lets her **confirm
or override** that verdict before acting on it. The act she can take adapts to the verdict
— pull a principle in, anchor to an existing rule, note a gap, or flag a conflict — and
every act she takes accumulates into a defensible, verbatim-cited decision trail: the
IMF-ready record of why each clause aligns with or deviates from its benchmark.

## User Story

As Aisyah R., a policy drafter enhancing Bank Negara Malaysia's Discussion Paper on AI in
the Malaysian Financial Sector, I want to open each source connected to my paragraph, judge
the AI's verdict for myself, and record my decision with the exact source passage attached,
so that every clause I keep or change carries a defensible, verbatim justification I can
stand behind in front of the IMF assessment — instead of a reconciliation that lives only
in my memory.

## Background & Context

**Current state:**

- Aisyah has uploaded her open draft and, in the workspace, selected a paragraph. She sees
  the list of sources connected to it, each with a source type, a proposed verdict, and a
  short quote (this comes from the upload & workspace feature — not this one).
- Today, without the tool, once she has found a relevant source she reads it beside her
  paragraph by hand, decides whether the draft follows it or departs from it, and — if she
  records the reasoning at all — writes it in a personal note that no reviewer or auditor
  later sees. Months later, why a clause follows or departs from a benchmark is hard to
  reconstruct.

**Problem:**

- The reconciliation call — "is this a gap the draft should close, or a deliberate,
  justified deviation?" — is genuinely ambiguous. A blind test on RMiT 17.1 against MAS
  §3.4.2 had two reasonable readers split between Gap and Deviates. An AI verdict cannot be
  trusted blindly; the drafter must settle the call.
- Because the reasoning lives only in memory, the institution carries no clause-by-clause,
  verbatim record of why the rulebook says what it says — which is exactly the record the
  IMF FSAP assessment expects.
- Nothing today distinguishes a source that was considered and deliberately set aside from
  one that was never looked at. A reviewer cannot see what Aisyah weighed and dismissed.

## Target User & Persona

- **Who:** Aisyah R., a Bank Negara Malaysia policy drafter enhancing the AI Discussion
  Paper. She is the domain expert; the tool proposes, she decides.
- **Context:** She has opened a specific connection between one of her paragraphs and one
  connected source, having selected it from the paragraph's connection list in the
  workspace. She is deciding whether and how the source should shape her draft.
- **Current workaround:** Reads the source beside her paragraph by hand, decides align or
  deviate from experience, and keeps the reasoning in her head or a private note that never
  reaches a reviewer or the IMF assessment.

## Goals

- Show the drafter's paragraph and the connected source side by side, with the source
  type, the AI's proposed verdict, the source passage quoted verbatim (marked verified or
  illustrative), and a plain-language read of how the source affects the paragraph.
- Let the drafter **confirm or override** the proposed verdict before acting, so the human
  settles the Gap-vs-deviation ambiguity — the system never trusts its own verdict blindly.
- Offer the act that fits the (confirmed) verdict — pull in as a guiding principle, anchor
  as a cross-reference, note as a gap, or flag a conflict for resolution — and prevent
  nonsensical acts such as adopting a conflict as a guiding principle.
- Let the drafter dismiss a connection as "not relevant" with a recorded reason, and count
  that dismissal as a resolved connection for submission purposes.
- Accumulate every acted-on connection into a verbatim-cited decision trail (paragraph
  number, verdict, source, the exact quote, verified/illustrative status), and show a
  completed connection in a done state.
- Keep one shared state: acting here is reflected live in the workspace, the trail, and
  every other view.

## Non-Goals

- **Browsing or generating the list of connections.** Uploading the draft, extracting
  paragraphs, and surfacing which sources connect to which paragraph belong to the Upload &
  reconciliation workspace feature. This feature begins once a single connection is opened.
- **Generating cross-source insights.** The "what you might have missed" insight cards
  belong to the Cross-source insights feature. This feature owns only the decision-trail
  portion of that view — the running record of acted-on connections — which is shared state
  both features read.
- **Rewriting the body text of the draft.** Inserting a full redrafted paragraph into the
  living document belongs to the Grounded redraft assistant & Word write-back feature. Here, the "act"
  produces a **tracked note** (a guiding-principle note, a cross-reference, a gap note, or a
  conflict flag) attached to the paragraph — not a rewrite of the paragraph's prose.
- **The drift monitor** and the underlying connection/verdict engine internals.

## User Workflow

1. **Open a connection** — From a paragraph's connection list in the workspace, Aisyah
   opens one connection. She lands on a view with her paragraph on the left and the
   connected source on the right.
2. **Read the source and the AI's read** — On the right she sees the source type (for
   example, international standard, act/law, internal BNM policy, or industry feedback), the
   AI's proposed verdict, the exact source passage quoted verbatim with a verified or
   illustrative marker, and the AI's plain-language read of how the source affects her
   paragraph.
3. **Confirm or override the verdict** — She either confirms the AI's proposed verdict or
   changes it to the verdict she judges correct. The available act updates to match the
   verdict currently in force.
4. **Act on the connection** — She takes the act that fits the verdict — pull in as a
   guiding principle, anchor to the rule, note as a gap, or flag the conflict — or she
   dismisses the connection as not relevant and records why.
5. **See it recorded and done** — The connection shows a done state; the tracked note is
   echoed onto her paragraph; and the connection appears in her decision trail with its
   paragraph number, verdict, source, verbatim quote, and verification status. Returning to
   the workspace, the connection reads as resolved everywhere.

## Acceptance Criteria

### Scenario: Opening a connection shows the paragraph beside the source with a verbatim quote

```gherkin
Given Aisyah has opened the connection between paragraph 3.5 (Fair usage & bias) and OECD AI Principles 1.2
When the connection view loads
Then she sees her paragraph 3.5 text on one side
  And she sees the source labelled as an international standard on the other side
  And she sees the proposed verdict "Consensus"
  And she sees the source passage quoted verbatim: "AI actors should implement mechanisms and safeguards, such as capacity for human agency and oversight, including to address risks arising from uses outside of intended purpose."
  And she sees the AI's read that OECD backs her fairness stance and adds a human agency & oversight mechanism paragraph 3.5 does not yet name
  And the quote is marked "verified word-for-word against the source document"
```

### Scenario: A quote that has not been verified is shown as illustrative, never as verified

```gherkin
Given Aisyah has opened the connection between paragraph 3.5 and the BNM Fair Treatment of Financial Consumers policy clause 8.1
  And the source passage for that connection has not yet been checked word-for-word
When the connection view loads
Then she sees the source passage quoted: "A financial service provider must ensure that financial consumers are treated fairly at all stages of their relationship with the financial service provider."
  And the quote is marked "illustrative — not yet verified against the source document"
  And the quote is never presented as verified
```

### Scenario: A connection with no supporting passage states so instead of inventing one

```gherkin
Given Aisyah has opened a connection for which the tool holds no verifiable source passage
When the connection view loads
Then she sees "No matching clause found" in place of a quote
  And no source passage is fabricated or paraphrased as if it were quoted
```

### Scenario: Confirming the AI's proposed verdict

```gherkin
Given Aisyah has opened the connection between paragraph 3.5 and OECD AI Principles 1.2
  And the AI proposes the verdict "Consensus"
When she confirms the proposed verdict
Then the verdict in force remains "Consensus"
  And the available act is "Pull in as guiding principle"
```

### Scenario: Overriding the AI's proposed verdict from Gap to Deviates-nuance

```gherkin
Given Aisyah has opened the connection between her draft's capital-treatment paragraph and the BCBS Basel III 72.5% output-floor rule
  And the AI proposes the verdict "Gap"
  And Aisyah judges this to be a deliberate, justified deviation rather than an omission
When she overrides the verdict to "Deviates (nuance)"
Then the verdict in force is "Deviates (nuance)"
  And she is prompted to record why this call was made
  And her override, not the AI's proposal, is what is carried into the decision trail
```

### Scenario: Overriding changes which act is offered

```gherkin
Given Aisyah has opened the connection between paragraph 3.5 and NIST AI Risk Management Framework MEASURE 2.11
  And the AI proposes the verdict "Gap"
  And the offered act is "Note as a gap to address"
When she overrides the verdict to "Consensus"
Then the offered act changes to "Pull in as guiding principle"
```

### Scenario Outline: The act offered adapts to the verdict in force

```gherkin
Given Aisyah has opened a connection with the verdict <verdict> in force
When she looks at how she can act on the connection
Then the offered act is "<act>"
  And acting records the note type "<note type>" against her paragraph
  And the trail records the source as "<relationship>" the paragraph

Examples:
  | verdict    | act                             | note type          | relationship        |
  | Consensus  | Pull in as guiding principle    | guiding principle  | cited in            |
  | Duplicate  | Anchor to this rule             | cross-reference    | cross-referenced in |
  | Gap        | Note as a gap to address        | gap to address     | flagged on          |
  | Conflict   | Flag conflict for resolution    | conflict to resolve| flagged on          |
  | Partial    | Note what to reconcile          | partial to reconcile| flagged on         |
```

### Scenario: A drafter cannot adopt a conflict as a guiding principle

```gherkin
Given Aisyah has opened the connection between paragraph 4.6 (Data & personal information) and the Personal Data Protection Act 2010 (amended 2024) §129
  And the verdict in force is "Conflict"
When she looks at how she can act on the connection
Then the only act offered for a conflict is "Flag conflict for resolution before the Exposure Draft"
  And "Pull in as guiding principle" is not offered for this connection
```

### Scenario: Pulling in a Consensus source as a guiding principle

```gherkin
Given Aisyah has opened the connection between paragraph 3.5 and OECD AI Principles 1.2
  And she has confirmed the verdict "Consensus"
When she pulls it in as a guiding principle
Then the connection shows a done state
  And a guiding-principle note is echoed onto paragraph 3.5 recording that OECD AI Principles 1.2 is now cited in paragraph 3.5
  And the connection appears in her decision trail
```

### Scenario: Flagging a Conflict for resolution keeps the conflicting text

```gherkin
Given Aisyah has opened the connection between paragraph 4.6 and PDPA 2010 (amended 2024) §129
  And the verdict in force is "Conflict"
When she flags the conflict for resolution before the Exposure Draft
Then the connection shows a done state
  And a conflict-to-resolve note is recorded on paragraph 4.6 together with the conflicting passage: "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act; or (b) that place ensures an adequate level of protection…"
  And the connection appears in her decision trail with the verdict "Conflict"
```

### Scenario: Anchoring a Duplicate to an existing rule as a cross-reference

```gherkin
Given Aisyah has opened the connection between paragraph 3.5 and the BNM Fair Treatment of Financial Consumers policy clause 8.1
  And the verdict in force is "Duplicate"
When she anchors paragraph 3.5 to that rule
Then the connection shows a done state
  And a cross-reference note is echoed onto paragraph 3.5 recording that Fair Treatment of Financial Consumers 8.1 is cross-referenced in paragraph 3.5
  And the connection appears in her decision trail with the illustrative marking preserved on its quote
```

### Scenario: Acting on a Partial verdict requires noting what to reconcile

```gherkin
Given Aisyah has opened the connection between paragraph 4.6 and the industry feedback from 3 financial-service-provider respondents
  And the feedback is "The requirement to obtain informed consent is unworkable for models already trained on legacy datasets collected before AI use was contemplated."
  And the verdict in force is "Partial" because the sector supports responsible data handling but rejects the informed-consent mechanism for legacy datasets
When she acts on the connection with "Note what to reconcile"
Then she is required to record which part to keep and which part to resolve before the note is saved
  And a partial-to-reconcile note is echoed onto paragraph 4.6
  And the connection appears in her decision trail with the verdict "Partial" and her recorded reconciliation note
```

### Scenario: A deliberate deviation cannot be saved without a "why this call" note

```gherkin
Given Aisyah has overridden a Gap to a deliberate "Deviates" on the Basel output-floor connection
When she attempts to record the decision without a justification
Then the decision is not saved
  And she is asked to record why the deviation is deliberate before it can be committed to the trail
```

### Scenario: Dismissing a connection requires a reason and counts as resolved

```gherkin
Given Aisyah has opened the connection between paragraph 3.11 (GenAI hallucinations) and a source she judges off-topic
When she dismisses the connection as "not relevant"
Then she is asked to record why it is not relevant before the dismissal is accepted
  And her stated reason is kept in the audit trail so a reviewer can see what was considered and set aside
  And the connection counts as resolved for submission purposes
  And the connection no longer appears as an open item on paragraph 3.11
```

### Scenario: Dismissing without a reason is not accepted

```gherkin
Given Aisyah has opened a connection and chosen to dismiss it as "not relevant"
When she attempts to confirm the dismissal without recording a reason
Then the dismissal is not accepted
  And she is asked to provide the reason before it can be recorded
```

### Scenario: An acted-on connection accumulates a verbatim-cited entry in the decision trail

```gherkin
Given Aisyah has pulled in OECD AI Principles 1.2 as a guiding principle on paragraph 3.5
  And she has flagged the PDPA §129 conflict on paragraph 4.6
When she opens her decision trail
Then she sees an entry for paragraph 3.5 with the verdict "Consensus", the source OECD AI Principles 1.2, its verbatim quote, and a "verified" marking
  And she sees an entry for paragraph 4.6 with the verdict "Conflict", the source PDPA 2010 (amended 2024) §129, its verbatim quote, and a "verified" marking
  And each entry shows enough to justify why the clause aligns with or deviates from its benchmark
```

### Scenario: The illustrative marking carries through to the trail entry

```gherkin
Given Aisyah has anchored paragraph 3.5 to Fair Treatment of Financial Consumers 8.1, whose quote is marked illustrative
When she opens her decision trail
Then the trail entry for that decision shows its quote marked "illustrative — not yet verified"
  And the entry is never shown as verified
```

### Scenario: Acting on a connection updates every view live

```gherkin
Given Aisyah has flagged the PDPA §129 conflict on paragraph 4.6
When she returns to the workspace
Then paragraph 4.6's connection to PDPA §129 reads as resolved
  And the same decision appears in her decision trail without her switching to reload it
```

### Scenario: Revisiting an already-acted connection shows the done state, not a fresh action

```gherkin
Given Aisyah has already pulled in OECD AI Principles 1.2 as a guiding principle on paragraph 3.5
When she reopens that same connection
Then it shows a done state marked "Done"
  And the guiding-principle note is shown echoed onto paragraph 3.5
  And she is not offered to act on it again as if it were unresolved
```

### Scenario: The illustrative Basel deviation carries its "why this call" justification

```gherkin
Given Aisyah has opened the connection between her draft's capital-treatment paragraph and the BCBS Basel III 72.5% output-floor rule
  And she has recorded the verdict "Deviates (nuance)" with a note on why Malaysia's treatment departs from the international floor
When she opens her decision trail
Then the entry shows the verdict "Deviates (nuance)", the BCBS source, and her recorded "why this call" justification
  And the entry is presented as the deviation-justification record the IMF assessment expects
```

### Scenario: A Basel source whose passage is not yet extracted is labelled, never approximated

```gherkin
Given Aisyah has opened the Basel III output-floor connection
  And the exact source passage has not yet been extracted word-for-word
When the connection view loads
Then the quote area shows a labelled "pending extraction" placeholder
  And no approximated or paraphrased Basel wording is shown as if it were the source passage
```

### Scenario: An unknown or stale connection sends the drafter back to the workspace

```gherkin
Given Aisyah follows a link to a connection that is out of date, unknown, or could not be retrieved
When the connection view tries to open
Then she sees a message that the connection is not available, with a plain explanation that it may have been a source the tool could not retrieve or the link is out of date
  And she is offered a way back to the workspace
  And no error, blank page, or fabricated connection is shown
```

## Business Rules & Constraints

- **AI proposes, the human commits.** Every connection carries exactly one proposed verdict
  — Consensus, Conflict, Gap, Duplicate, or Partial. The drafter must confirm or override it
  before the act is recorded; the verdict carried into the trail is always the one in force
  after the human's decision, never the AI's unconfirmed proposal.
- **The Gap-vs-deviation ambiguity is settled by the human.** Where a connection reads as
  both a Gap and a deliberate deviation (as with the Basel output floor), the drafter's
  confirmation or override settles the call.
- **Deviations and partials require a recorded justification before saving.** An override
  from Gap to a deliberate **Deviates**, and any act on a **Partial**, cannot be saved until
  the drafter records a "why this call" note. This is what makes the trail IMF-defensible.
  ("Deviates" is a documented nuance on Gap, not a separate verdict.)
- **The act adapts to the verdict, and a conflict is never a principle.** Consensus offers
  "pull in as a guiding principle" (source recorded as cited in the paragraph); Duplicate
  offers "anchor as a cross-reference" (cross-referenced in); Gap offers "note as a gap to
  address" (flagged on); Conflict offers only "flag for resolution before the Exposure
  Draft" (flagged on, recorded with the conflicting text); Partial offers "note what to
  reconcile" — which part to keep and which to resolve (flagged on). "Adopt a conflict as a
  principle" is never offered.
- **The act produces a tracked note, not a rewrite.** Acting attaches a guiding-principle
  note, cross-reference, gap note, conflict flag, or partial-to-reconcile note to the
  paragraph — it does not rewrite the paragraph's body text (that is the grounded redraft assistant's job).
- **Every AI judgement carries evidence and justification.** Every connection view, verdict,
  and trail entry quotes the exact source passage with its clause or section number and
  source name (the evidence) **and** shows the AI's rationale for the call (the
  justification). If no supporting passage exists, the view states "No matching clause found"
  and never fabricates one.
- **Verbatim-integrity marking.** Every displayed quote — in the connection view and in the
  trail — is marked either "verified" (checked word-for-word) or "illustrative" (not yet
  verified). An illustrative quote is visibly distinct and is never presented as verified. A
  source passage not yet extracted (for example, the Basel output-floor rule) is shown as a
  labelled "pending extraction" placeholder, never approximated.
- **Dismissal records a reason and resolves the connection.** A connection may be dismissed
  as "not relevant" instead of acted on, but only with a recorded reason, which is kept in
  the audit trail. A dismissed connection counts as resolved for submission purposes.
- **One shared state.** Acting on a connection or dismissing it updates the same finding
  state read by the workspace, the trail, and every other view; a completed connection shows
  a "Done" state with its note echoed onto the paragraph, and revisiting it does not offer
  the act again.
- **Graceful handling of missing connections.** An unknown, stale, or unretrievable
  connection shows an explanatory message and a route back to the workspace, never a crash,
  blank page, or fabricated connection.

## Success Metrics

- **Evidential completeness:** a higher share of reconciled connections end with a
  verbatim, verifiable justification recorded in the trail than a from-memory baseline.
- **Zero unsupported claims:** 100% of connection views, verdicts, and trail entries quote
  an existing passage verbatim or explicitly state none was found; any unverifiable citation
  is treated as a defect.
- **Human-settled verdicts:** every recorded decision reflects a confirmed or overridden
  verdict — no decision is recorded on an unconfirmed AI proposal.
- **Deviations justified:** every deviation from an international benchmark that the drafter
  records carries a "why this call" justification, forming the IMF-ready trail.
- **Considered-and-set-aside visibility:** every dismissed connection carries a recorded
  reason a reviewer can read.

## Dependencies

- **The connection engine** — supplies each connection's proposed verdict, source type,
  source passage, verification status, and the AI's plain-language read.
- **The Upload & reconciliation workspace** — the drafter reaches a connection by selecting
  it from a paragraph's connection list; the workspace reflects a connection's resolved
  state after it is acted on.
- **The Cross-source insights feature** — shares the decision-trail state this feature
  writes; insights and the trail live in the same view but are owned separately.
- **The Grounded redraft assistant & Word write-back feature** — consumes the tracked notes this
  feature records when it later rewrites paragraph text as tracked changes.
- **The curated source library and the illustrative Basel row** — provide the sources shown
  in connections, including the Basel output-floor row carrying the IMF deviation story.

## Open Questions

- [x] ~~Should the drafter be able to override the AI's proposed verdict, or only confirm
      it?~~ — **Resolved:** the drafter can confirm **or** override. The Gap-vs-deviation
      split is a genuine ambiguity two reasonable readers disagree on, so the human settles
      it, per the shared "AI proposes, human commits" rule; the demo must show confirming,
      never blind trust.
- [x] ~~Does a dismissed connection count as resolved?~~ — **Resolved:** yes. Dismissal with
      a recorded reason counts as resolved for submission purposes, and the reason is kept in
      the audit trail so a reviewer sees what was considered and set aside.
- [x] ~~Does acting here rewrite the paragraph text?~~ — **Resolved:** no. Acting records a
      tracked note (guiding principle, cross-reference, gap, or conflict); rewriting the
      paragraph's prose belongs to the grounded redraft assistant feature.
- [x] ~~Should the trail distinguish "considered and rejected" references from those that
      shaped the final text as a separate view?~~ — **Resolved:** no separate view in MVP1.
      The trail records only the references that shaped the final text; dismissal-with-reason
      keeps rejected references in the audit log, and a dedicated "rejected references" view
      is deferred to the roadmap. The IMF story is carried by the "why this call" note on each
      accepted deviation.
- [x] ~~When the drafter overrides to a "Deviates" verdict, is that a first-class verdict
      label or a nuance on Gap?~~ — **Resolved:** a **documented nuance**, not a fifth
      verdict. The canonical set stays Consensus / Conflict / Gap / Duplicate; "Deviates" is a
      flag plus a required "why this call" justification the drafter records when a Gap is in
      fact a deliberate, justified deviation from a benchmark. No fifth badge is built.
