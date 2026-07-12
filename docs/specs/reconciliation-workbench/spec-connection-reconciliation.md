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

---

> **Technical refinement (added by `/prd-refine`; re-platformed to Next.js on 2026-07-11).**
> Everything above is the approved product content and is unchanged. This story is the
> **second** UI surface; it reuses the **Shared Technical Spine** defined in
> `spec-upload-and-workspace.md` (the Next.js + React + Tailwind + shadcn/ui app under `web/`,
> the read-API/snapshot contract via `web/lib/data.ts`, and the Zustand store
> `web/lib/store.ts` used via a `useStore` hook). That spine is not repeated here. This story
> **owns** two store slices — the **`verdicts`** slice (the in-force verdict per connection)
> and the **`trail`** slice (the decision trail) — which the insights and grounded-redraft
> stories read.

## Functional Requirements

- **The connection view reads one connection from the shared spine.** `web/app/connections/[id]/page.tsx`
  opens on the `[id]` route param and renders the paragraph text (left) beside the connected
  source (right) from `useStore.connectionsFor(paragraph)` — the same snapshot/API payload the
  workspace uses. It never re-fetches or re-derives the verdict; the engine's proposed
  verdict is the starting point.
- **Verdict lifecycle: proposed → in-force → committed.** The engine payload carries
  `verdict` + `verdict_status:"proposed"`. The view shows the proposal, then the drafter
  **confirms** (in-force = proposed) or **overrides** (in-force = her choice). The in-force
  verdict is written to the `verdicts` slice under `connection_id` only when the act is
  committed — never the AI's unconfirmed proposal. The four canonical verdicts (Consensus /
  Conflict / Gap / Duplicate / Partial) plus the **Deviates nuance** (a flag on a Gap, not a
  badge) are the only permitted in-force values.
- **The offered act is a pure function of the in-force verdict** (`actFor(verdict)`), and it
  re-computes live when the drafter overrides:
  | In-force verdict                                                                             | Offered act                                  | `note_type`         | trail relationship  |
  | -------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------- | ------------------- |
  | Consensus                                                                                    | Pull in as guiding principle                 | `guiding_principle` | cited in            |
  | Duplicate                                                                                    | Anchor to this rule                          | `cross_reference`   | cross-referenced in |
  | Gap                                                                                          | Note as a gap to address                     | `gap`               | flagged on          |
  | Conflict                                                                                     | Flag conflict for resolution                 | `conflict`          | flagged on          |
  | Partial                                                                                      | Note what to reconcile                       | `partial`           | flagged on          |
  | Gap → Deviates                                                                               | Note as a deliberate deviation (needs "why") | `deviation`         | flagged on          |
  | "Pull in as guiding principle" is **never** rendered when the in-force verdict is Conflict — |
  | the act list is derived, so a nonsensical act is structurally impossible, not merely hidden. |
- **Justification gate.** Committing a **Deviates** override or **any act on a Partial**
  requires a non-empty "why this call" note; the commit button stays disabled and the field
  is flagged until a reason is entered. The note is stored on the trail entry.
- **Dismissal gate.** Dismissing a connection as "not relevant" requires a non-empty reason;
  an empty reason blocks the dismissal. A dismissal writes the `verdicts` slice entry for that
  `connection_id` as `{status:"dismissed", reason}` and counts as resolved for submission
  (read by the grounded-redraft story), but does **not** create a `trail` entry (the trail
  records only references that shaped the text; dismissals live in the audit log — the
  `verdicts`-slice record is that log).
- **Committing an act appends a verbatim-cited trail entry** to the `trail` slice:
  `{connection_id, paragraph, verdict, source, quote:{clause_number, text, verification},
note_type, why?}`. The `quote` is copied from the connection payload unchanged — including
  its `verification` marker (`verified` / `illustrative` / `pending_extraction`), which carries
  through to the trail entry and may never be upgraded.
- **Done state and idempotency.** A connection with a record in the `verdicts` slice renders as
  "Done" with its note echoed onto the paragraph and does **not** re-offer the act.
  Re-committing the same connection is a no-op (no duplicate trail entry).
- **Live shared state.** Committing writes through `useStore`, whose `persist` middleware
  fires the cross-tab `storage` event so the workspace (connection reads resolved) and the
  insights trail update live without a reload.
- **No supporting passage / pending extraction.** When the connection payload has
  `quote:null` or `verification:"pending_extraction"`, the quote area renders "No matching
  clause found" or a labelled "pending extraction" placeholder respectively — never a
  fabricated or approximated passage. A connection may still be dismissed but cannot be
  "pulled in" as a verified principle.
- **Missing/stale connection.** If the `[id]` route param resolves to no known connection
  (unknown, stale, or `could_not_retrieve`), the view renders an explanatory message and a
  "Back to workspace" link — never a crash, blank page, or fabricated connection.

### Validation & Business Rules

- The "why this call" and dismissal reason fields are trimmed and length-capped (≤1000
  chars); whitespace-only is treated as empty and blocks the commit/dismissal.
- The in-force verdict written to the `verdicts` slice must be one of the six permitted
  values; any other value is a defect.
- A trail entry's `verification` must equal the source connection's `verification` — no
  upgrade path exists in the writer.

## Permissions & Security

- **Scope:** public — the connection view renders only public source passages already in the
  snapshot; no auth. No restricted-node text is ever reachable (the exporter skips it).
- **Input validation:** the `[id]` route param is matched against known connection ids; the
  reason/why fields are the only free-text inputs and are capped and stored verbatim in the
  Zustand store (persisted to `localStorage`) — no server, no injection surface beyond the
  drafter's own browser.
- **No new write routes** — all verdict/trail state is client-side in the `verdicts` and
  `trail` store slices.

## API Design (consumed — owned by the engine story)

Defines **no new engine routes**. Reads the same `GET …/paragraphs/{n}/connections` payload as
the workspace (via `useStore.connectionsFor`). All verdict/trail mutations are writes into the
Zustand store (persisted to `localStorage`) through `web/lib/store.ts`; the new `useStore`
helpers this story adds to `web/lib/store.ts`:

```ts
useStore.verdictFor(connId); // → {status, verdict?, reason?, why?} | proposed-from-payload
useStore.commitAct(connId, { verdict, note_type, why }); // writes verdicts slice + appends trail slice
useStore.dismiss(connId, reason); // writes verdicts slice {status:"dismissed", reason}
useStore.trail(); // → trail slice array (read by insights)
useStore.isResolved(connId); // committed act OR dismissal (read by grounded-redraft submit gate)
```

Example `trail`-slice entry after pulling in OECD on 3.5:

```json
{
  "connection_id": "ai-dp-2025:3.5::oecd:OECD 1.2",
  "paragraph": "3.5",
  "verdict": "Consensus",
  "source": "OECD AI Principles 1.2",
  "quote": {
    "clause_number": "OECD 1.2",
    "text": "AI actors should implement mechanisms and safeguards, such as capacity for human agency and oversight, including to address risks arising from uses outside of intended purpose.",
    "verification": "verified"
  },
  "note_type": "guiding_principle",
  "why": null
}
```

Example `verdicts`-slice entries (a committed conflict flag and a dismissal):

```json
{
  "ai-dp-2025:4.6::pdpa-2010:PDPA 129": {
    "status": "confirmed",
    "verdict": "Conflict"
  },
  "ai-dp-2025:3.11::some-offtopic": {
    "status": "dismissed",
    "reason": "Covers market-conduct reporting, not hallucination controls."
  }
}
```

## Data Model & Artifacts

No database. This story writes two named slices of the Zustand store (persisted to
`localStorage` via `persist`) through `web/lib/store.ts`:

- **`verdicts`** — `{ "<connection_id>": {status:"confirmed"|"dismissed", verdict?, reason?} }`.
  The in-force verdict and the audit record of considered-and-set-aside connections.
- **`trail`** — the append-only decision trail (shape above). Read by the cross-source
  insights view ("Pulled into your draft so far") and attached as the justification pack at
  submission (grounded-redraft story).

Both survive reload and reflect across pages via the spine's `persist` cross-tab
`storage`-event sync.

## UI/Frontend Requirements

- **`web/app/connections/[id]/page.tsx`** (new) — the paragraph-beside-source connection view:
  source-type label, proposed-verdict badge with confirm/override control, verbatim quote
  with its verification marker (or "No matching clause found" / "pending extraction"), the
  AI's plain-language read, the derived act control, the dismissal control, and — on a
  resolved connection — the "Done" state with the echoed note. It reuses the shared
  `web/components/` primitives from the workspace story (`VerdictBadge`, `QuoteBlock`,
  `SourceTypeDot`, etc.). A "Decision trail" panel (or a link to the insights view that renders
  the `trail` slice) shows accumulated entries.
- **User interactions:** confirm verdict → act unchanged; override verdict → act re-derives;
  commit act → "Done" + trail entry + live reflection; dismiss (with reason) → resolved, no
  trail entry; revisit resolved connection → "Done", no re-offer.
- **States:** _Proposed_ — verdict badge + confirm/override. _Justification-required_ —
  commit disabled until "why" entered (Deviates/Partial). _Dismiss_ — reason required.
  _Done_ — resolved, note echoed, act not re-offered. _No passage_ — "No matching clause
  found." _Pending extraction_ — labelled placeholder. _Missing/stale_ — explanatory message
  - back-to-workspace.

## Architecture Notes

- **New dependencies:** none beyond the shared `web/` stack (Next.js + React + Tailwind +
  shadcn/ui + Zustand) established by the workspace story.
- **Integration points:** reached via "Open connection & act" from the workspace at the route
  `/connections/<id>`; extends `web/lib/store.ts` (spine) with the verdict/trail helpers above;
  the `verdicts`/`trail` slices are read by the insights view (trail display) and the
  grounded-redraft view (submission gate). The tracked note this story records is what the
  grounded-redraft story later turns into body-text.
- **Shared-state discipline:** all mutation goes through `useStore` so `persist` fires the
  cross-tab `storage` event and every open page re-renders — the honest MVP1 realisation of
  "one shared state."

## Exemplar Files

- `docs/poc/drafter-knowledge-graph/connections.html` — the legacy connection view is the
  read-only **UX reference** for the derived-act + trail-entry layout, not the build target.
- `spec-upload-and-workspace.md` → "Shared Technical Spine" and its `web/lib/store.ts` /
  `web/lib/data.ts` contract — the migrated store and read seam this story extends.
- `engine/api.py` `GET …/connections` shape — the connection payload (verdict, quote,
  verification) this view consumes unchanged.

## Implementation Plan

### Sub-tasks

**Task 1: Verdict/trail slices + helpers in `web/lib/store.ts`** — _medium_

- Add the `verdicts` and `trail` slices plus `verdictFor`, `commitAct`, `dismiss`, `trail`,
  `isResolved`; rely on `persist` for the cross-tab re-render. Depends on the spine
  `web/lib/store.ts` scaffold existing.
- Files: `web/lib/store.ts`
- SEQUENTIAL (depends on the workspace story's store scaffold)

**Task 2: Connection view — proposal, confirm/override, derived act** — _large_

- Render paragraph-beside-source; confirm/override control; `actFor(verdict)` derivation;
  quote with verification marker / no-passage / pending-extraction states.
- Files: `web/app/connections/[id]/page.tsx`
- SEQUENTIAL (depends on Task 1)

**Task 3: Commit, justification gate, dismissal gate, Done state** — _medium_

- Commit writes the `verdicts` + `trail` slices; enforce "why" for Deviates/Partial and reason
  for dismissal; render Done + echoed note; idempotent re-commit.
- Files: `web/app/connections/[id]/page.tsx`, `web/lib/store.ts`
- SEQUENTIAL (depends on Task 2)

**Task 4: Decision-trail render + missing-connection handling** — _small_

- Render `trail`-slice entries with their verification markers; graceful missing/stale-`[id]`
  message with a route back to the workspace.
- Files: `web/app/connections/[id]/page.tsx`
- SEQUENTIAL (depends on Task 3)

### Negative Constraints

- Do NOT write a verdict to the `verdicts` slice before the drafter confirms/overrides — no
  auto-commit of the AI proposal.
- Do NOT render "Pull in as guiding principle" for a Conflict, or any act not returned by
  `actFor(verdict)`.
- Do NOT upgrade an `illustrative`/`pending_extraction` quote to `verified` in the trail
  entry.
- Do NOT create a trail entry for a dismissal (dismissals live in the `verdicts` slice only).
- Do NOT add engine write routes or a server store.
- Do NOT extend the legacy `*.html` pages — they are the read-only UX reference.

## Test Scenarios

**Test 1: Override re-derives the offered act**

- Setup: render `<ConnectionPage>` (RTL) at route `/connections/ai-dp-2025:3.5::nist:NIST
MEASURE 2.11`, payload verdict `Gap`, offered act "Note as a gap to address."
- Action: override the in-force verdict to `Consensus`.
- Expected: the offered act becomes "Pull in as guiding principle"; the `verdicts` slice is
  still unwritten (nothing committed yet).

**Test 2: Conflict never offers "pull in as principle"**

- Setup: render `<ConnectionPage>` at the route for the PDPA §129 conflict on 4.6, in-force
  verdict `Conflict`.
- Action: read the act control.
- Expected: only "Flag conflict for resolution" is offered; "Pull in as guiding principle" is
  absent from the derived act list.

**Test 3: Deviates commit is blocked without a "why" note**

- Setup: override the Basel output-floor Gap to `Deviates`.
- Action: attempt to commit with an empty "why this call" field.
- Expected: commit disabled; nothing written to the `verdicts`/`trail` slices; entering a
  reason enables commit and writes the trail entry with `note_type:"deviation"` and the `why`
  text.

**Test 4: Committing appends a verbatim trail entry with its verification marker preserved**

- Setup: render `<ConnectionPage>` at the route for OECD Consensus on 3.5 (payload
  `verification:"verified"`); and the BNM Fair Treatment Duplicate on 3.5
  (`verification:"illustrative"`).
- Action: pull in OECD as a guiding principle; anchor the BNM duplicate.
- Expected: two `trail`-slice entries; OECD entry `verification:"verified"`, BNM entry
  `verification:"illustrative"` — neither upgraded; each `quote.text` equals the payload
  byte-for-byte.

**Test 5: Dismissal requires a reason, resolves without a trail entry**

- Setup: an off-topic connection on 3.11.
- Action: dismiss with empty reason (blocked), then with a reason.
- Expected: empty reason blocks; a reason writes the `verdicts` slice entry
  `{status:"dismissed",reason}` for that id; `useStore.isResolved(id)` is true; the `trail`
  slice gains no entry; the workspace shows the connection resolved.

**Test 6: Resolved connection revisits as Done, idempotent**

- Setup: OECD on 3.5 already pulled in.
- Action: re-render `<ConnectionPage>` at that connection's route; attempt to commit again.
- Expected: renders "Done" with the echoed note, does not re-offer the act, and creates no
  second `trail`-slice entry.

**Test 7: Missing/stale connection routes back to the workspace**

- Setup: render `<ConnectionPage>` at route `/connections/ai-dp-2025:9.9::nonexistent`.
- Action: load the view.
- Expected: an explanatory "connection not available" message and a "Back to workspace" link;
  no crash, blank page, or fabricated connection.

## Verification

Run the `verifier` skill (Vitest/RTL for the frontend; no backend changes in this story
unless a snapshot fixture is extended for the demo connections).

### Component / Unit Tests (Vitest + React Testing Library — the gate)

- `web/lib/store.test.ts` — Tests 1–6: `actFor(verdict)` derivation and override re-derivation
  (Tests 1–2), the justification gate for Deviates/Partial (Test 3), `commitAct` appending a
  verbatim trail entry with its `verification` marker preserved and never upgraded (Test 4),
  `dismiss` requiring a reason and resolving without a trail entry (Test 5), and Done-state
  idempotency (Test 6).
- `web/app/connections/*.test.tsx` — a component test rendering `<ConnectionPage>` for the
  proposal → confirm/override → derived-act states, the verified vs illustrative vs
  pending-extraction / "No matching clause found" quote states, and the missing/stale-`[id]`
  routing back to the workspace (Test 7).

### E2E Tests (Playwright — optional, non-blocking)

| Key Scenario                                                | Test file                        | Assigned sub-task |
| ----------------------------------------------------------- | -------------------------------- | ----------------- |
| Reconcile a connection (override → justify → commit → Done) | `web/e2e/reconciliation.spec.ts` | Task 3            |
| Dismiss an off-topic connection with a recorded reason      | `web/e2e/reconciliation.spec.ts` | Task 3            |

**Locator strategy:** `data-testid` on the verdict control (`verdict-<id>`), the act button
(`act-<id>`), and the trail entries (`trail-entry-<id>`). Flagged non-blocking — a red E2E
never blocks the demo; the Vitest gate above is authoritative.

### Next.js dev-server walkthrough

Run the Next.js dev server (`npm run dev` in `web/`) and walk through:

1. Open `/connections/<id>` for the OECD/3.5 Consensus → paragraph beside source, verified
   quote, proposed "Consensus", act "Pull in as guiding principle." (Opening + verified-quote
   scenarios.)
2. Override the NIST/3.5 Gap to Consensus → act changes to "Pull in as guiding principle."
   (Override-changes-act scenario.)
3. Open the PDPA §129/4.6 Conflict → only "Flag conflict for resolution" offered. (Cannot
   adopt a conflict as a principle.)
4. Override the Basel Gap to Deviates → commit blocked until "why" entered → trail entry
   carries the justification. (Deviates justification-gate scenarios.)
5. Dismiss an off-topic connection with/without a reason → reason required; dismissal resolves
   without a trail entry. (Dismissal scenarios.)
6. Pull in OECD (verified) and anchor the BNM duplicate (illustrative) → open the trail →
   verified vs illustrative markers distinct. (Trail + illustrative-carry-through scenarios.)
7. Return to the workspace → the acted connections read resolved without a reload; reopen a
   resolved connection → "Done", no re-offer. (Live-shared-state + revisit scenarios.)
8. Load a bad `/connections/<id>` → graceful back-to-workspace message. (Missing/stale
   scenario.)

## Open Questions (technical)

- [x] ~~Where do the in-force verdict and the decision trail live without a backend?~~ —
      **Resolved:** the Zustand store slices `verdicts` (in-force verdict + dismissal audit)
      and `trail` (append-only trail), written through `useStore` in `web/lib/store.ts`,
      persisted to `localStorage` via `persist`, and reflected live via `persist`'s cross-tab
      `storage` sync. The read seam is `web/lib/data.ts` selected by `NEXT_PUBLIC_API_BASE`.
- [x] ~~How is a nonsensical act (e.g. "adopt a conflict as a principle") prevented?~~ —
      **Resolved:** the offered act is a pure derivation `actFor(verdict)`; unlisted acts are
      structurally unrenderable, not merely hidden.
- [ ] Should a dismissal ever appear in the visible trail (not just the audit record)? —
      **Deferred (non-blocking):** MVP1 keeps dismissals in the `verdicts` slice only; a
      "considered & set aside" view is a roadmap item per the epic and does not block this
      story.
