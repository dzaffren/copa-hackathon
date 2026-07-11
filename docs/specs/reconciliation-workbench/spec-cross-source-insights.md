# Cross-source insights ("what you might have missed")

**Ticket:** TBD

The insights view reads across _every_ connected source at once — instead of one
document at a time — and surfaces connections a drafter scouring source-by-source would
likely miss: cross-source implications, silent gaps, and second-order links. Every
insight is presented honestly as an **AI-generated hypothesis to verify**, names the
sources it reasoned across, and leaves the decision to the drafter. The same view also
displays the running decision trail — the guiding principles the drafter has already
pulled into the draft — so she can see what she has committed alongside what she may
still be missing.

## User Story

As Aisyah R., a Bank Negara Malaysia policy drafter enhancing an in-progress Discussion
Paper, I want the tool to reason across all the sources connected to my draft at once and
tell me what a source-by-source read would likely miss — clearly flagged as hypotheses to
check, not facts — so that I can catch cross-source implications, silent gaps, and
emerging shifts before my draft is finalised, and see them next to the decisions I have
already recorded.

## Background & Context

**Current state:**

- A drafter strengthens a policy by reading her sources one at a time — an OECD principle,
  then a NIST framework, then a BCBS standard — and holds the connections between them in
  her head.
- Connections that only appear when several sources are read _together_ — two paragraphs
  that need the same missing control, a system-level risk no single source frames as
  urgent, a live regulatory shift that could reshape the benchmark — are easy to overlook
  when each source is read in isolation and under time pressure.
- The decisions she has already made (the principles she has pulled into the draft) live
  in a separate reconciliation view; she has no single place that shows "what I might have
  missed" next to "what I have committed."

**Problem:**

- Reading sources one at a time, a drafter misses cross-source implications and silent
  gaps that only surface when many sources are read together — a named problem in the
  epic.
- Without an honest, source-cited way to surface these, a drafter either misses them or
  cannot tell an AI hunch from a verified fact, which erodes trust in the tool.
- The value the drafter most wants to see — "what I could not have found on my own" —
  lives in reasoning _across_ the un-cited and cited sources, not in any single one of
  them.

## Target User & Persona

- **Who:** Aisyah R., a policy drafter at Bank Negara Malaysia, enhancing the _Discussion
  Paper on AI in the Malaysian Financial Sector_ (August 2025) — a citation-heavy,
  in-progress draft. She is the domain expert and the decision-maker.
- **Context:** She reaches the insights view after connecting her draft to its sources and
  reconciling individual connections. She opens it to ask "what did I miss?" before moving
  the draft toward its Exposure Draft.
- **Current workaround:** She re-reads each connected source by hand, tries to hold the
  cross-source picture in her head, and relies on memory and experience to notice
  implications spanning several sources.

## Goals

- Surface cross-source insights a source-by-source read would likely miss — across four
  categories: **cross-source implication**, **silent gap**, **second-order link**, and
  **temporal self-consistency** (a divergence from a prior version or "what we said last
  year").
- Present every insight honestly as an **AI-generated hypothesis to verify**, never as an
  asserted fact; make each insight name the sources it reasoned across, and show a
  **confidence band (High / Medium / Low)** so the drafter can triage which hypotheses to
  verify first. A high-confidence insight is still a hypothesis she must verify — confidence
  never converts inference into fact.
- Preserve the verbatim-citation guardrail: any exact passage an insight quotes is shown
  with its clause/paragraph number and source, marked verified or illustrative.
- Display the running decision trail ("Pulled into your draft so far") from the one shared
  finding state, including an honest empty state, so the drafter sees her committed
  decisions alongside the insights.
- Let the drafter act on an insight without committing anything from the card: **set it
  aside**, or **carry it** (hand-off with context) into the surface where action actually
  happens — the grounded redraft assistant for a cross-source implication or silent gap, a "track this"
  watch-item for a second-order link — so nothing is written to the draft until she confirms
  it downstream.

## Non-Goals

- **Creating decision-trail entries.** Producing trail entries is owned by the connection
  reconciliation story. This story only _displays_ the trail and its empty state; it never
  writes to it.
- **Generating the insight text.** How the engine reasons across sources and produces the
  insight wording is owned by the source-connection engine story.
- **Committing an insight to the draft.** Redrafting a clause, writing a new paragraph, or
  flagging a conflict happens in the grounded redraft assistant and reconciliation stories. This story lets the
  drafter **carry** an insight (a hand-off that pre-loads context) or **set it aside** — it
  never writes to the draft itself, and the destination story owns the actual change.
- **Upload, the workspace canvas, the grounded redraft assistant (Word write-back), and the drift monitor.**
  These are separate stories; this view is reached from the workspace.

## User Workflow

> From Aisyah's perspective — what she sees, does, and feels.

1. **Opens the insights view** — From her workspace, Aisyah opens "What you might have
   missed." She sees an explanation that the AI has read across every connected source at
   once, and that what follows are hypotheses to verify — not facts.
2. **Reviews the insights** — She sees a list of insights, each labelled with its category
   (cross-source implication, silent gap, second-order link, or temporal self-consistency),
   a plain-language explanation, a **confidence band (High / Medium / Low)** she can triage
   by, and a line naming the sources the AI reasoned across.
3. **Checks an insight's reasoning** — For any insight, she reads which sources it
   synthesised (for example, "Reasoned across: OECD 1.2 · NIST MEASURE 2.11 · BCBS 239")
   and any exact passage it quotes, marked verified or illustrative, so she can judge it.
   Even a High-confidence insight is a hypothesis she still verifies.
4. **Decides what to do** — She **sets aside** an insight she has considered and does not
   want to pursue, or **carries** it (a hand-off with context) into the surface where action
   happens — the grounded redraft assistant for a cross-source implication or silent gap, a "track this"
   watch-item for a second-order link. Nothing is committed to the draft from the card
   itself; the change is only made when she confirms it in the destination.
5. **Sees her decision trail** — Below the insights, she sees "Pulled into your draft so
   far": every guiding principle she has already committed, each with its paragraph,
   verdict, source, and verbatim (or illustrative) quote — or an honest empty-state message
   if she has recorded nothing yet.
6. **Knows the picture is current** — If she records or changes a decision elsewhere, the
   trail here updates to match, without her switching pages.

## Acceptance Criteria

> From Aisyah's perspective. UI styling is out of scope for these scenarios and is
> described in prose above where relevant.

### Scenario: Viewing the cross-source insights

```gherkin
Given Aisyah has connected her Discussion Paper to its sources
  And the AI has reasoned across every connected source at once
When she opens the "What you might have missed" view
Then she sees an explanation that the AI reads across all connected sources at once
  And she sees that the insights shown are hypotheses to verify, not asserted facts
  And she sees a list of insights she would likely miss reading source-by-source
```

### Scenario: An insight names the sources it reasoned across

```gherkin
Given Aisyah is viewing the insights
When she reads the cross-source implication about her bias stance and data stance
Then she sees the plain-language explanation that paragraph 3.5 and paragraph 4.6 point to the same missing pre-deployment data bias assessment
  And she sees the line "Reasoned across: OECD 1.2 · NIST MEASURE 2.11 · BCBS 239"
```

### Scenario: Every insight is labelled as a hypothesis to verify, not a fact

```gherkin
Given Aisyah is viewing the insights
When she reads any insight
Then it is presented as an AI-generated hypothesis for her to verify
  And it names the sources it reasoned across
  And it is never presented as a confirmed fact or an automatic change to her draft
```

### Scenario: An insight that quotes an exact passage marks it verified or illustrative

```gherkin
Given Aisyah is viewing an insight that quotes an exact passage from a source
When she reads that quoted passage
Then the passage is shown with its clause or paragraph number and its source
  And the passage is marked either verified against the source or illustrative and not yet verified
  And an illustrative passage is visibly distinct from a verified one
```

### Scenario Outline: The four insight categories are surfaced with their reasoning and confidence

```gherkin
Given Aisyah is viewing the insights
When she reads the insight labelled "<category>"
Then she sees the explanation "<explanation>"
  And she sees the sources it reasoned across "<sources>"
  And she sees a confidence band of "<confidence>"

Examples:
  | category                  | explanation                                                                                           | sources                                       | confidence |
  | Cross-source implication  | Your bias stance (3.5) and your data stance (4.6) point to the same missing control                   | OECD 1.2 · NIST MEASURE 2.11 · BCBS 239       | High       |
  | Silent gap                | No paragraph addresses AI model concentration / third-party dependency                                | FSB (2024a) · BCBS Newsletter on AI/ML (2022) | Medium     |
  | Second-order link         | A live regulatory shift (EU AI Act GPAI rules) may reshape peer expectations before your DP finalises | EU AI Act (Regulation 2024/1689)              | Medium     |
  | Temporal self-consistency | This draft's stance diverges from the position BNM took in the prior version of the policy            | prior published version of the policy         | Low        |
```

### Scenario: A silent-gap insight surfaces a risk no paragraph in the draft addresses

```gherkin
Given Aisyah's Discussion Paper covers bias, hallucination, and data
When she reads the silent-gap insight
Then she sees that no paragraph addresses AI model concentration or third-party dependency
  And she sees that the FSB and BCBS both flag systemic concentration risk when many financial service providers rely on the same few foundation-model providers
  And she sees the line "Reasoned across: FSB (2024a) · BCBS Newsletter on AI/ML (2022)"
```

### Scenario: A second-order-link insight surfaces an emerging shift, not just a citation

```gherkin
Given Aisyah's Discussion Paper is still open for feedback
When she reads the second-order-link insight
Then she sees that the EU AI Act's general-purpose-AI transparency obligations are phasing in through 2025-26
  And she sees that this could shift what counts as an international benchmark before the paper becomes policy
  And she sees the line "Reasoned across: EU AI Act (Regulation 2024/1689)"
```

### Scenario: A temporal self-consistency insight surfaces a divergence from a prior version

```gherkin
Given Aisyah's draft addresses a position BNM has published on before
When she reads the temporal self-consistency insight
Then she sees that her draft's stance diverges from the position taken in the prior version of the policy
  And she sees the line naming the prior published version it reasoned against
  And it is presented as a hypothesis to verify, not an asserted fact
```

### Scenario: Each insight shows a confidence band the drafter can triage by

```gherkin
Given Aisyah is viewing the insights
When she reviews the list
Then each insight shows a confidence band of High, Medium, or Low
  And a High-confidence insight is still presented as a hypothesis she must verify, not a fact
  And she can use the confidence band to decide which insights to verify first
```

### Scenario: At least one insight is generated live in the demo, honestly labelled

```gherkin
Given Aisyah opens the insights view in the demo
When the cross-source implication is generated live across its connected sources
Then it is shown as freshly generated rather than replayed
  And any prepared insight is honestly labelled as prepared
  And a live insight that finds no support states so rather than inventing a cross-source claim
```

### Scenario: Setting aside an insight after considering it

```gherkin
Given Aisyah is viewing the second-order-link insight about the EU AI Act
  And she has decided it is worth tracking but not acting on now
When she sets the insight aside
Then the insight is marked as considered and set aside
  And the view does not change her draft or the decision trail on her behalf
```

### Scenario: Carrying a cross-source implication hands off to the grounded redraft assistant with context

```gherkin
Given Aisyah is viewing the cross-source implication about paragraphs 3.5 and 4.6
  And she wants to act on the missing pre-deployment data bias assessment
When she carries the insight into action
Then she is taken to the grounded redraft assistant, because the implication needs draft text written
  And paragraphs 3.5 and 4.6 and the sources the insight named (OECD 1.2, NIST MEASURE 2.11, BCBS 239) are pre-loaded there
  And no change is committed to her draft until she confirms a redraft in the grounded redraft assistant
```

### Scenario: Carrying a second-order link adds a watch-item rather than a draft change

```gherkin
Given Aisyah is viewing the second-order-link insight about the EU AI Act
When she carries the insight into action
Then it is added to a "track this" watch-item because there is nothing to redraft yet
  And her draft and decision trail are not changed
```

### Scenario: Viewing the decision trail with recorded entries

```gherkin
Given Aisyah has already recorded these guiding principles in her draft
  | paragraph | verdict   | source                                | quote status |
  | 3.5       | Consensus | OECD AI Principles 1.2                | verified     |
  | 4.6       | Conflict  | Personal Data Protection Act §129     | verified     |
When she views "Pulled into your draft so far"
Then she sees an entry for paragraph 3.5 with the verdict Consensus and its OECD source
  And she sees an entry for paragraph 4.6 with the verdict Conflict and its Personal Data Protection Act source
  And each entry shows the exact quoted passage it relies on with its verification status
```

### Scenario: Viewing the decision trail when nothing has been recorded yet

```gherkin
Given Aisyah has not recorded any guiding principle in her draft
When she views "Pulled into your draft so far"
Then she sees a message that nothing has been recorded yet
  And she sees guidance to open a connection from the workspace and act on it to build her research trail
  And no trail entries are shown
```

### Scenario: The trail reflects a decision recorded elsewhere without switching pages

```gherkin
Given Aisyah is viewing the insights and trail
  And the trail currently shows no entry for paragraph 3.5
When she records a guiding principle for paragraph 3.5 in the reconciliation view
Then the trail on the insights view updates to show the paragraph 3.5 entry
  And she did not have to leave or reload the insights view to see it
```

### Scenario: A trail entry shows an illustrative quote distinctly from a verified one

```gherkin
Given Aisyah has recorded these entries in her draft
  | paragraph | source                  | quote status |
  | 3.5       | OECD AI Principles 1.2  | verified     |
  | 5.2       | Basel III output floor  | illustrative |
When she views "Pulled into your draft so far"
Then the paragraph 3.5 entry marks its quote as verified against the source
  And the paragraph 5.2 entry marks its quote as illustrative and not yet verified
  And the illustrative entry is visibly distinct from the verified entry
```

## Business Rules & Constraints

- **Insights are hypotheses, never facts.** Every insight is presented as an AI-generated
  hypothesis for the drafter to verify. The view must never present an insight as a
  confirmed fact or apply it to the draft automatically.
- **Every insight names the sources it reasoned across.** Each insight shows a "Reasoned
  across" line listing the sources it synthesised (for example, "OECD 1.2 · NIST MEASURE
  2.11 · BCBS 239"). This is what distinguishes an insight — reasoning _over_ sources —
  from a verbatim-verified single-source connection.
- **Verbatim-citation guardrail applies to any quoted passage.** If an insight quotes an
  exact passage, it shows the passage with its clause or paragraph number and source. If no
  supporting passage exists, the tool says so ("No matching clause found") and never invents
  one.
- **Verbatim-integrity marking.** Any quoted passage — in an insight or a trail entry — is
  marked verified (checked word-for-word against the source) or illustrative (not yet
  verified); illustrative quotes are visibly distinct and are never presented as verified.
- **Four insight categories.** Insights fall into exactly four categories: cross-source
  implication, silent gap, second-order link, and temporal self-consistency (a divergence
  from a prior version). Each is clearly labelled.
- **Every insight carries a confidence band.** Each insight shows a High / Medium / Low
  confidence band the drafter can triage by. Confidence is a triage signal, not a
  probability of truth: even a High-confidence insight is a hypothesis she must verify, and
  confidence never converts inference into fact. (How the band is derived is deferred to
  technical refinement.)
- **AI proposes, human commits — carrying is a hand-off, not a commit.** The drafter decides
  what to act on. **Setting aside** marks the insight considered and changes nothing.
  **Carrying** navigates to the surface where action happens, pre-loaded with the insight's
  paragraphs and cited sources — a cross-source implication or silent gap carries into the
  **grounded redraft assistant** (there is text to draft); a second-order link becomes a **"track this"
  watch-item** (nothing to redraft yet). No insight card ever writes to the draft directly;
  the change is committed only when she confirms it downstream.
- **One shared state for the trail.** The trail displayed here reads from the one shared
  finding state that the reconciliation story writes. This view only displays the trail; it
  never creates or edits trail entries.
- **Live reflection.** When a decision is recorded or changed elsewhere, the trail on this
  view reflects it without the drafter switching or reloading the page.
- **Honest empty state.** When no guiding principle has been recorded, the trail shows a
  clear message and guidance to act on a connection from the workspace, not a blank space
  or fabricated entries.

## Success Metrics

- **Fewer missed connections (recall):** the insights surface cross-source implications,
  silent gaps, second-order links, and temporal divergences that an unaided drafter does not
  find in the same time — for example, the single missing pre-deployment data bias
  assessment linking paragraphs 3.5 and 4.6, and the absent model-concentration risk.
- **Zero unsupported claims:** every quoted passage in an insight or trail entry cites an
  existing passage verbatim; any quote that cannot be verified against its source is treated
  as a defect.
- **Honest labelling:** every insight is displayed as a hypothesis and names the sources it
  reasoned across; an insight shown as a fact, or without its "Reasoned across" sources, is a
  defect.
- **Trail fidelity:** the trail shown here matches the recorded decisions in the shared
  state at all times, including the empty state; a stale or divergent trail is a defect.

## Dependencies

- **The source-connection engine** produces the insights (the reasoning across sources) and
  the connections; this view displays the resulting insights.
- **The upload & reconciliation workspace** is where the drafter reaches this view and where
  the connected sources originate.
- **The connection reconciliation & decision trail story** owns creating trail entries in the
  one shared finding state; this view only displays that trail and its empty state.
- **The curated source library and the demo vehicle** — the Discussion Paper on AI in the
  Malaysian Financial Sector and its connected public references (OECD, NIST, BCBS 239, FSB,
  EU AI Act, and the Personal Data Protection Act) — supply the concrete sources the insights
  reason across.

## Open Questions

> Resolve before implementation. Non-blocking questions may be deferred with rationale.

- [x] ~~Who owns creating decision-trail entries?~~ — **Resolved:** the connection
      reconciliation story owns creating trail entries in the shared finding state; this
      story only displays the trail and its empty state, to avoid double-specifying trail
      creation.
- [x] ~~Should insights be presented as facts or hypotheses?~~ — **Resolved:** always as
      AI-generated hypotheses to verify, each naming the sources it reasoned across. This is
      the hard framing that distinguishes insights from verbatim-verified single-source
      connections.
- [ ] **Can a drafter dismiss an insight with a recorded reason, mirroring connection
      dismissal?** — **Deferred (non-blocking):** setting an insight aside is in scope;
      whether that captures a written reason (as connection dismissal does) can be settled
      during implementation without blocking the view.
- [x] ~~Does carrying an insight pre-select the exact paragraphs and sources, or only open
      the relevant place?~~ — **Resolved:** carrying **pre-loads** the insight's paragraphs
      and cited sources into the destination, and routes by category — a cross-source
      implication or silent gap into the **grounded redraft assistant**, a second-order link into a **"track
      this" watch-item**. Nothing is committed until the drafter confirms it there.
- [ ] **How is the confidence band (High / Medium / Low) derived?** — **Deferred to
      technical refinement (`/prd-refine`):** the product behaviour (a triage band shown on
      every insight, never converting inference to fact) is fixed here; the computation
      (model self-report, cross-source agreement, retrieval similarity, an LLM-judge pass, or
      a blend) is an implementation choice with trade-offs and is settled in refinement. The
      same band and derivation question apply to connection-verdict confidence.
- [ ] **Does setting an insight aside capture a written reason, mirroring connection
      dismissal?** — **Deferred (non-blocking):** setting aside is in scope; whether it
      records a reason can be settled during implementation without blocking the view.
