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

---

> **Technical refinement (added by `/prd-refine`; re-platformed to Next.js on 2026-07-11).**
> Everything above is the approved product content and is unchanged. This story is a UI
> surface; it reuses the **Shared Technical Spine** defined in
> `spec-upload-and-workspace.md` (the Next.js + React + Tailwind + shadcn/ui app under
> `web/`, the read-API/snapshot contract via `web/lib/data.ts`, and the Zustand store
> `web/lib/store.ts` accessed through a `useStore` hook). That spine is not repeated here.
> This story **owns** two store slices — `watch` (the "track this" watch-items) and
> `setAside` (insights considered and set aside) — and **reads** the `trail` slice (the
> decision trail, written by the connection-reconciliation story) **display-only**: it never
> writes to `trail`, per its own Non-Goals.

## Functional Requirements

- **Insights are rendered from the snapshot/API, never generated here.**
  `web/app/insights/page.tsx` reads the engine-produced insight set through
  `useStore.insights()` — in snapshot mode this is `web/public/data/insights.json` (see
  [API Design](#api-design-consumed--owned-by-the-engine-story)); when
  `NEXT_PUBLIC_API_BASE` is set it is `GET …/insights`. This view only **displays** insights;
  it does not reason across sources or compose insight wording (owned by the engine story).
- **The four categories render distinctly.** Each insight carries a `category` of
  `cross_source_implication`, `silent_gap`, `second_order_link`, or
  `temporal_self_consistency`. The renderer maps each to its human label
  ("Cross-source implication", "Silent gap", "Second-order link", "Temporal
  self-consistency") and a distinct category chip. An unknown category renders a neutral
  "insight" chip rather than throwing.
- **Hypothesis labelling is always-on, from data.** Every insight card renders a fixed
  "AI-generated hypothesis to verify" banner and never a "confirmed"/"fact" affordance —
  this is structural, not a per-record flag, so the engine cannot accidentally emit a
  fact-labelled insight. A High-confidence insight renders the same hypothesis banner as a
  Low-confidence one.
- **"Reasoned across" source list per insight.** Each card renders the `reasoned_across`
  array as a middot-joined line — for example "Reasoned across: OECD 1.2 · NIST MEASURE
  2.11 · BCBS 239". An insight with an empty `reasoned_across` is a defect surfaced in the
  verification walkthrough; the renderer shows "Reasoned across: (none)" rather than
  omitting the line, so the omission is visible, not hidden.
- **Confidence band is displayed, never computed.** The card renders the payload's
  `confidence` (`High` / `Medium` / `Low`) as a triage chip. The view performs **no**
  derivation — the band is resolved deterministically by the engine (see
  [Open Questions (technical)](#open-questions-technical)). The band is a triage signal
  only; the hypothesis banner is shown regardless of band, so a High band never converts
  inference to fact.
- **Verbatim-integrity marking on any quoted passage.** When an insight carries an optional
  `quote:{clause_number, text, verification}`, the card renders the exact `text` with its
  `clause_number` and source, marked by its `verification` value (`verified` → "✓ verbatim
  — verified against source", `illustrative` → "◦ illustrative — not yet verified",
  `pending_extraction` → labelled "pending extraction" placeholder). The marker is rendered
  from the field and is **never** upgraded to `verified`. An insight with no supporting
  passage (`quote:null`) shows "No matching clause found" rather than a fabricated quote.
- **Carry-routing is a pure function of category (`actFor`-style).** Carrying an insight
  routes by `category`, mirroring the reconciliation story's `actFor(verdict)` discipline:
  | Category                                                                           | Carry destination                                                     |
  | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
  | `cross_source_implication`                                                         | `/assistant` route — pre-loaded (paragraphs + `reasoned_across` srcs) |
  | `silent_gap`                                                                       | `/assistant` route — pre-loaded (paragraphs + `reasoned_across` srcs) |
  | `second_order_link`                                                                | a `watch`-slice "track this" watch-item (nothing to redraft yet)      |
  | `temporal_self_consistency`                                                        | `/assistant` route — pre-loaded (divergence + prior-version source)   |
  | The destination is derived from `category`, so a nonsensical route is structurally |
  | impossible. Carrying to the assistant navigates to the `/assistant` route with the |
  | insight's paragraphs and cited sources as query params (for example                |
  | `/assistant?insight=<id>&paras=3.5,4.6&sources=oecd-ai,nist-airmf,bcbs239`); the   |
  | redraft is committed only when the drafter confirms it on `/assistant`. **No carry |
  | writes to the draft or to the `trail` slice from this card.**                      |
- **Set-aside writes the `setAside` slice.** Setting an insight aside appends its `id` to the
  `setAside` slice via `useStore.setAside(id)`, marks the card "considered · set aside",
  and changes neither the draft nor the trail. Re-setting-aside the same id is a no-op.
- **Trail display is read-only from the `trail` slice.** The "Pulled into your draft so far"
  panel renders `useStore.trail()` (the reconciliation story's `trail` slice) — each entry
  with its paragraph, verdict, source, and its `quote` marked by its `verification` value.
  This view **never** writes `trail`. When `trail` is empty, the panel shows the honest
  empty state: "Nothing recorded yet — open a connection from the workspace and act on it
  to build your research trail," and lists no fabricated entries.
- **Live reflection via the store.** Because the trail is read through the spine's Zustand
  store (`web/lib/store.ts`), the trail panel re-renders reactively when the reconciliation
  view commits a decision — and Zustand's `persist` cross-tab `storage` sync propagates it
  to another open tab — without a reload or a page switch. Setting aside or watching an
  insight likewise re-renders any other open insights page live.
- **At least one live, honestly-labelled insight.** An insight with `origin:"live"` renders
  a "freshly generated" marker; `origin:"prepared"` renders a "prepared" marker. A live
  insight that the engine returns with `no_support:true` renders "No cross-source support
  found — no insight is asserted here" rather than an invented cross-source claim (mirrors
  the workspace's "No matching clause found" guardrail).

### Validation & Business Rules

- The `confidence` chip shown must equal the payload's `confidence` field; a page may never
  compute or upgrade it. A mismatch is a defect asserted in the verification walkthrough.
- A quote's `verification` marker shown must equal the payload's `verification` field —
  `illustrative`/`pending_extraction` is never upgraded to `verified`.
- If set-aside or a watch-item capture free text (see the deferred question), it is trimmed
  and length-capped (≤1000 chars); whitespace-only is treated as empty.
- The trail panel is strictly read-only — no code path in `web/app/insights/page.tsx` writes
  the `trail` slice.

## Permissions & Security

- **Scope:** public. Every insight, quote, and trail entry derives from public BNM documents
  and public references already in the snapshot; the read routes are public; no auth on the
  insights surface.
- **No restricted-node text:** the snapshot exporter skips any node with
  `access:"restricted"` (spine carve-out), so no restricted source text can reach
  `web/public/data/insights.json` or the trail. This view renders only what the snapshot
  contains.
- **Free-text input caps:** the only free-text this story could capture is an optional
  set-aside/watch reason (deferred question); if implemented it is trimmed and capped at
  ≤1000 chars and stored verbatim in the persisted store (`localStorage`) — no server, no
  injection surface beyond the drafter's own browser.
- **No new write routes:** all mutations (the `watch` and `setAside` slices) are client-side
  through the `useStore` hook; the engine stays read-only.

## API Design (consumed — owned by the engine story)

Defines **no new routes**. This story consumes the engine's read API (or its static
snapshot) and adds only client-side helpers to the spine's Zustand store
(`web/lib/store.ts`).

- `GET /documents/{document_id}/insights` (engine-owned) → the insight set. In snapshot mode
  the exporter writes the same shape to `web/public/data/insights.json`.

Proposed `data/insights.json` shape (mirrors `GET …/insights`), with a cross-source
implication (verified quote), a silent gap (no supporting passage), and a live
second-order link:

```json
{
  "document_id": "ai-dp-2025",
  "insights": [
    {
      "id": "ins:xsrc:3.5-4.6:bias-data",
      "category": "cross_source_implication",
      "explanation": "Your bias stance (3.5) and your data stance (4.6) point to the same missing pre-deployment data bias assessment.",
      "paragraphs": ["3.5", "4.6"],
      "reasoned_across": ["OECD 1.2", "NIST MEASURE 2.11", "BCBS 239"],
      "confidence": "High",
      "origin": "live",
      "no_support": false,
      "quote": {
        "clause_number": "NIST MEASURE 2.11",
        "text": "Fairness and bias — as evaluated by internal and external assessors — are evaluated and results are documented.",
        "verification": "verified"
      }
    },
    {
      "id": "ins:gap:model-concentration",
      "category": "silent_gap",
      "explanation": "No paragraph addresses AI model concentration / third-party dependency; FSB and BCBS both flag systemic concentration risk when many providers rely on the same few foundation-model providers.",
      "paragraphs": [],
      "reasoned_across": ["FSB (2024a)", "BCBS Newsletter on AI/ML (2022)"],
      "confidence": "Medium",
      "origin": "prepared",
      "no_support": false,
      "quote": null
    },
    {
      "id": "ins:2nd:eu-ai-act-gpai",
      "category": "second_order_link",
      "explanation": "A live regulatory shift (EU AI Act GPAI transparency rules, phasing in through 2025-26) may reshape peer expectations before your DP finalises.",
      "paragraphs": [],
      "reasoned_across": ["EU AI Act (Regulation 2024/1689)"],
      "confidence": "Medium",
      "origin": "prepared",
      "no_support": false,
      "quote": null
    }
  ]
}
```

New helpers this story adds to the spine's Zustand store (`web/lib/store.ts`), accessed via
the `useStore` hook:

```ts
useStore.insights(); // → snapshot data/insights.json (or GET …/insights when NEXT_PUBLIC_API_BASE set)
useStore.watch(insight); // append {insight_id, source, added_at} to the watch slice (idempotent)
useStore.setAside(insightId); // append insightId to the setAside slice (idempotent)
useStore.trail(); // → trail slice (READ-ONLY here; owned/written by reconciliation)
```

Example `watch`-slice entry after carrying the EU AI Act second-order link:

```json
{
  "insight_id": "ins:2nd:eu-ai-act-gpai",
  "source": "EU AI Act (Regulation 2024/1689)",
  "added_at": "2026-07-12T09:41:00Z"
}
```

Example `setAside` slice after setting the same insight aside instead:

```json
["ins:2nd:eu-ai-act-gpai"]
```

## Data Model & Artifacts

No database. State lives in three places, only two of which this story writes:

- **Static snapshot** (read-only, produced by the spine's exporter):
  `web/public/data/insights.json` (shape above). Immutable per build; public content only
  (restricted nodes skipped).
- **Zustand store (mutable, per browser, persisted to `localStorage`; this story):** the
  `watch` slice = `[ {insight_id, source, added_at} ]` and the `setAside` slice =
  `["<insight_id>", …]`. All access goes through the `useStore` hook in `web/lib/store.ts`
  (`useStore.watch`, `useStore.setAside`).
- **`trail` slice (read-only here):** the decision trail; the connection-reconciliation story
  owns all writes. This story reads it via `useStore.trail()` for the "Pulled into your draft
  so far" panel and its empty state — never writes it.

Both writable slices survive reload and reflect across pages/tabs via the spine's Zustand
`persist` cross-tab sync.

## UI/Frontend Requirements

- **`web/app/insights/page.tsx`** (new) — the "What you might have missed" view; reuses the
  shared `web/components/` (`QuoteBlock`, `VerdictBadge`, `SourceTypeDot`) established by the
  workspace story:
  - An always-on header stating the AI read across every connected source at once and that
    what follows are hypotheses to verify, not facts.
  - An **insight list**, each card showing: category chip; confidence chip (from data);
    plain-language `explanation`; a "Reasoned across:" line from `reasoned_across`; an
    optional verbatim `quote` (via `QuoteBlock`) with its `verification` marker (or "No
    matching clause found"); an `origin` marker (freshly generated / prepared); and, for a
    live no-support case, the honest "no cross-source support found" message.
  - Per-card **carry** control (routes by category to the `/assistant` route pre-loaded via
    query params, or adds a `watch`-slice item) and **set-aside** control (writes the
    `setAside` slice).
  - A **"Pulled into your draft so far"** trail panel rendering `useStore.trail()` read-only
    — each entry with paragraph, verdict, source, and its verification-marked quote — with
    the honest empty state when the `trail` slice is empty.
- **States:** _Loading_ — skeleton cards while the snapshot/API resolves. _Insight list_ —
  cards rendered as above. _Carried_ — card marked "carried" (to assistant or watch-list).
  _Set-aside_ — card marked "considered · set aside." _Empty-trail_ — the honest
  nothing-recorded message + guidance. _Live-generated insight_ — the "freshly generated"
  marker. _No-support_ — "no cross-source support found." _Error_ — snapshot/API failure
  shows "couldn't load the insights — retry," never a blank page or fabricated card.

## Architecture Notes

- **New dependencies:** none beyond the shared spine (Next.js + React + Tailwind + shadcn/ui
  - Zustand, all under `web/`); this story adds no package of its own.
- **Integration points:** reached from the workspace ("What you might have missed"); extends
  the spine's store (`web/lib/store.ts`) with `insights`, `watch`, `setAside`; carries a
  cross-source implication / silent gap / temporal divergence into the `/assistant` route
  (pre-loaded via query params) and a second-order link into the `watch` slice; reads the
  reconciliation story's `trail` slice via `useStore.trail()` for the trail panel.
- **Shared-state discipline:** all mutation goes through the `useStore` hook so every open
  page/component re-renders reactively (and Zustand's `persist` cross-tab sync propagates to
  other tabs) — the honest MVP1 realisation of "one shared state." This story is a **reader**
  of the `trail` slice, so its live trail updates come from the reconciliation story's
  writes, not its own.

## Exemplar Files

- `docs/poc/drafter-knowledge-graph/insights.html` — the legacy insights view and its
  trail-display handling is the read-only **UX reference** for the category-rendering +
  carry-routing logic that `web/app/insights/page.tsx` re-implements.
- `spec-upload-and-workspace.md` → "Shared Technical Spine" and its `web/lib/store.ts`
  contract — the store this story extends (and the `NEXT_PUBLIC_API_BASE`/snapshot pattern
  via `web/lib/data.ts` for `web/public/data/insights.json`).
- `spec-connection-reconciliation.md` → its `trail`-slice entry shape and `useStore.trail()`
  helper — the exact trail shape this view renders read-only.

## Implementation Plan

### Sub-tasks

**Task 1: Add `watch`/`setAside` slices + `insights()` reader to `web/lib/store.ts`** — _medium_

- Add `insights()` (snapshot `web/public/data/insights.json` via `web/lib/data.ts` or
  `GET …/insights`), `watch(insight)`, `setAside(insightId)` (both idempotent); confirm
  `trail()` is a read-only selector here. Depends on the spine store existing.
- Files: `web/lib/store.ts`
- SEQUENTIAL (depends on the workspace story's `web/lib/store.ts` scaffold)

**Task 2: Snapshot exporter emits `insights.json`** — _small_

- Extend `scripts/export_poc_snapshot.py` to serialise the engine's insight set into
  `web/public/data/insights.json`, skipping `access:"restricted"` nodes; add a shape/skip
  test.
- Files: `scripts/export_poc_snapshot.py`, `engine/tests/test_export_poc_snapshot.py`
- INDEPENDENT (needs the engine artifacts, not the store)

**Task 3: Insight list renderer — categories, confidence, reasoned-across, quotes** — _large_

- Render the four categories, the from-data confidence chip, the always-on hypothesis
  banner, the "Reasoned across" line, the optional verbatim quote (via the shared
  `QuoteBlock`) with its verification marker (and "No matching clause found"), and the
  `origin` / no-support markers.
- Files: `web/app/insights/page.tsx`, `web/components/*`
- SEQUENTIAL (depends on Task 1)

**Task 4: Carry-routing, set-aside, and the read-only trail panel** — _medium_

- Category-derived carry (`/assistant` pre-load via query params / the `watch` slice),
  set-aside (the `setAside` slice), and the "Pulled into your draft so far" panel rendering
  `useStore.trail()` read-only with the honest empty state; idempotent watch/set-aside; live
  reflection.
- Files: `web/app/insights/page.tsx`, `web/lib/store.ts`
- SEQUENTIAL (depends on Task 3)

### Negative Constraints

- Do NOT write to the `trail` slice — the trail is read-only here; the reconciliation story
  owns its writes.
- Do NOT commit an insight to the draft from the card — carrying is a hand-off (pre-load the
  `/assistant` route or add a `watch`-slice item), never a draft change.
- Do NOT hard-code the confidence band or a "verified" marker — every band and verification
  marker renders from the data.
- Do NOT invent engine routes — this story consumes `GET …/insights` /
  `web/public/data/insights.json` and adds no new server routes; all mutation is client-side
  through the persisted Zustand store.
- Do NOT extend the legacy `docs/poc/drafter-knowledge-graph/*.html` pages as the live demo —
  they are the read-only UX reference only.

## Test Scenarios

**Test 1: The four categories render distinctly with their confidence chips from data**

- Setup: `insights.json` with `ins:xsrc:3.5-4.6:bias-data` (`cross_source_implication`,
  `High`), `ins:gap:model-concentration` (`silent_gap`, `Medium`),
  `ins:2nd:eu-ai-act-gpai` (`second_order_link`, `Medium`), and a
  `temporal_self_consistency` insight (`Low`).
- Action: render `<InsightsPage>` (RTL).
- Expected: four distinct category chips; each confidence chip equals its payload
  `confidence`; every card shows the always-on "hypothesis to verify" banner regardless of
  band — the High-confidence card is not shown as a fact.

**Test 2: A quoted passage renders its verification marker unchanged; no-passage says so**

- Setup: `ins:xsrc:3.5-4.6:bias-data` with a `verified` NIST MEASURE 2.11 quote;
  `ins:gap:model-concentration` with `quote:null`.
- Action: render both cards.
- Expected: the cross-source card shows "✓ verbatim — verified" with the NIST clause number;
  the silent-gap card shows "No matching clause found" — neither upgraded, no fabricated
  quote for the null case.

**Test 3: Carry routing is category-derived (assistant vs watch)**

- Setup: the `cross_source_implication` (3.5/4.6) and the `second_order_link` (EU AI Act)
  insights.
- Action: carry the cross-source implication, then carry the second-order link.
- Expected: the implication navigates to
  `/assistant?insight=ins:xsrc:3.5-4.6:bias-data&paras=3.5,4.6&sources=...` (pre-loaded)
  and writes nothing to the `trail` slice; the second-order link appends
  `{insight_id:"ins:2nd:eu-ai-act-gpai", source:"EU AI Act (Regulation 2024/1689)", added_at}`
  to the `watch` slice and does not navigate to the assistant; neither changes the draft or
  the trail.

**Test 4: Set-aside writes the `setAside` slice (idempotent), touches nothing else**

- Setup: the `ins:2nd:eu-ai-act-gpai` insight.
- Action: set it aside, then set it aside again.
- Expected: the `setAside` slice `== ["ins:2nd:eu-ai-act-gpai"]` after both actions (no
  duplicate); the card reads "considered · set aside"; the `trail` slice and any draft state
  are unchanged.

**Test 5: The trail panel renders the `trail` slice read-only, incl. the honest empty state and live reflection**

- Setup A (empty): the `trail` slice absent/empty.
- Setup B (populated then live): the `trail` slice gains an OECD/3.5 `verified`
  guiding-principle entry (a store update) while the page is open.
- Action: render `<InsightsPage>` with A; then simulate B.
- Expected: A shows "Nothing recorded yet — open a connection from the workspace…" and no
  entries; B re-renders the 3.5 entry (paragraph, verdict `Consensus`, OECD source, ✓
  verified quote) without a reload; `web/app/insights/page.tsx` never wrote the `trail`
  slice.

**Test 6: A live insight with no support states so rather than inventing a claim**

- Setup: an insight with `origin:"live"` and `no_support:true`.
- Action: render it.
- Expected: the card shows the "freshly generated" marker and "No cross-source support found
  — no insight is asserted here"; no fabricated `explanation` quote or `reasoned_across`
  claim is shown.

## Verification

Run the `verifier` skill (Python/pytest for the exporter change; Vitest/RTL for the insights
frontend).

### Backend Tests

- `engine/tests/test_export_poc_snapshot.py` (extended) — asserts `web/public/data/insights.json`
  is emitted with the shape above, that `verification`/`confidence` fields pass through
  unchanged, and that no `access:"restricted"` node text reaches the file.

### Component / Unit Tests (Vitest + React Testing Library — the gate)

- `web/lib/store.test.ts` — Tests 3–4 (category-derived carry into `watch` / `/assistant`,
  set-aside idempotency into `setAside`) plus that `trail()` is read-only (no store path
  from this page writes `trail`).
- `web/app/insights/page.test.tsx` — Test 1: the always-on "hypothesis to verify" label
  renders on every card regardless of band, and each confidence chip equals its payload
  `confidence` field (data-driven, never computed or upgraded).

### E2E Tests (Playwright — optional, non-blocking)

| Key Scenario                                              | Test file                  | Assigned sub-task |
| --------------------------------------------------------- | -------------------------- | ----------------- |
| Insight → carry a cross-source implication → `/assistant` | `web/e2e/insights.spec.ts` | Task 4            |

**Locator strategy:** `data-testid` on the insight cards (`insight-<id>`), the carry/set-aside
controls, and the trail entries. Flagged non-blocking — a red E2E never blocks the demo; the
Vitest gate above is authoritative.

### Dev-server walkthrough

Run the app locally (`npm run dev` in `web/`) and walk through, mapping each Acceptance
Criteria scenario:

1. Open `/insights` → header states "reads across all connected sources at once" and
   "hypotheses to verify, not facts"; an insight list is shown. (Viewing-the-insights +
   every-insight-a-hypothesis scenarios.)
2. Read the cross-source implication → its explanation about 3.5/4.6 and the line "Reasoned
   across: OECD 1.2 · NIST MEASURE 2.11 · BCBS 239". (Names-the-sources scenario.)
3. Read a quoted insight → clause number + source + verified/illustrative marker distinct;
   read the silent-gap → "No matching clause found." (Verified/illustrative + verbatim
   scenarios.)
4. Scan the list → each card shows a High/Medium/Low confidence chip and the same hypothesis
   banner regardless of band. (Four-categories Outline + confidence-triage scenarios.)
5. Confirm one insight shows "freshly generated" and any prepared one is labelled
   "prepared"; a live no-support insight says so. (Live-insight scenario.)
6. Carry the cross-source implication → navigates to `/assistant` pre-loaded, no draft
   change; carry the EU AI Act second-order link → `watch`-slice item, no navigation. (Carry
   hand-off scenarios.)
7. Set aside the EU AI Act insight → "considered · set aside," draft and trail unchanged.
   (Set-aside scenario.)
8. With the `trail` slice empty → honest empty-trail message; record a 3.5 decision in the
   reconciliation view → the trail panel updates here without a reload; confirm a verified
   entry vs an illustrative entry render distinctly. (Trail-with-entries, empty-trail,
   live-reflection, and illustrative-trail scenarios.)

## Open Questions (technical)

- [x] ~~How is the confidence band (High / Medium / Low) derived?~~ — **Resolved (was
      deferred to `/prd-refine`):** the band is **not** derived in this view — it is resolved
      **deterministically by the engine** in `engine/verdicts.py` (the same module that
      resolves connection-verdict confidence) and carried on each insight's `confidence`
      field through the snapshot/API. This view **displays** the band as a triage chip and
      never computes or upgrades it; the always-on hypothesis banner means a High band never
      converts inference to fact. This resolves the same band-derivation question the
      reconciliation story flagged for connection-verdict confidence.
- [x] ~~What shape does the engine's insight set take for the snapshot?~~ — **Resolved:** the
      exporter writes `web/public/data/insights.json` with the `{id, category, explanation,
paragraphs, reasoned_across, confidence, origin, no_support, quote?}` shape above, mirroring
      `GET …/insights`; `NEXT_PUBLIC_API_BASE` (via `web/lib/data.ts`) switches between the
      snapshot (default, deploy-safe) and the live engine.
- [ ] Should carrying a `silent_gap` pre-load the `/assistant` route with a blank target
      paragraph (no existing paragraph addresses it) or open a "new paragraph" affordance? —
      **Deferred (non-blocking):** MVP1 pre-loads the assistant with the `reasoned_across`
      sources and an empty paragraph target; a dedicated "draft a new paragraph" entry point
      is an enhancement that does not block this view.
