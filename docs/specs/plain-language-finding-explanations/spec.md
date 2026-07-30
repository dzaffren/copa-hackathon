# Plain-Language Finding & Copilot Explanations

**Ticket:** TBD

Findings and copilot answers currently explain themselves in dense, formal
regulatory prose that the drafter often has to re-read several times to
understand. This feature rewrites how those explanations are phrased — clear,
plain language that names what each side actually does — so a drafter grasps a
finding on first read, while the verbatim clause quotation stays exactly as
strict as it is today.

## User Story

As Aisyah, the BNM policy drafter, I want each finding and copilot answer to
explain itself in plain language I understand on the first read, so that I can
decide whether to accept or dismiss a linkage without decoding jargon or reading
the same sentence three times.

## Background & Context

**Current state:**

- Every finding shows a one-line **summary** and, sometimes, an italic
  **scope note** beneath it. Both are written by the analysis that finds the
  linkage.
- The copilot panel answers the drafter's questions in a "formal
  policy-document register" — deliberately dense, central-bank tone.
- The summary for a coverage finding (one side silent on a topic) is forced to
  pack three separate points into a single line: the shared topic, what the
  covering side requires, and exactly what the other side omits.

**Problem:**

- Explanations read as "gibberish" on first pass — the drafter reports having to
  read a finding multiple times and still not understanding it.
- Formal register and stacked clauses hide the one thing the drafter needs: what
  does each document actually say, and how do they relate.
- The demo is driven by findings committed with each workstream (build-and-
  persist), so unclear phrasing is what an audience sees live, not just a
  future-run risk.

## Target User & Persona

- **Who:** Aisyah R., the policy drafter, reviewing AI-found linkages on the
  task screen and asking the copilot for help while drafting.
- **Context:** She scans a queue of findings (aligns-with / differs-on /
  conflicts-with / silent-on / goes-beyond) against her working draft and must
  quickly judge each one. She also reads copilot replies while writing.
- **Current workaround:** She re-reads each explanation, mentally translates the
  jargon, and cross-checks the quoted clauses herself to work out what the
  finding is really claiming.

## Goals

- Every finding explanation is understandable on the first read by a policy
  professional, without re-reading.
- The explanation states, in plain terms, what each side does — not just a
  restatement of the finding's label.
- Necessary regulatory nuance is preserved, but carried in a short secondary
  clause rather than crammed into one dense line.
- Copilot answers adopt the same plain, direct register.
- The demo-visible committed findings are rewritten to meet the same bar.

## Non-Goals

- **No change to the five-label taxonomy** or to sentiment (tighten / loosen /
  neutral on differs-on only). This is about phrasing, not classification.
- **No relaxation of the verbatim-citation rule.** Quoted clause text and clause
  numbers stay exact; "No matching clause found" stays the only fallback.
- **No rewriting of the quoted clause text itself** — the source clauses are
  regulatory text and are shown verbatim; only the explanation around them
  changes.
- **No visual redesign** of the finding card or copilot panel.
- Rewriting the phrasing of findings in workstreams that are not part of the
  MVP1 demo pair is deferred (see Scope boundaries).

## User Workflow

1. **Reviewing linkages** — Aisyah opens the task screen and sees a queue of
   findings against her OpRes PD working draft.
2. **Reading a finding** — she reads the one-line summary. In one short sentence,
   plain words, it tells her what her draft does and what the other document does
   on the same topic.
3. **Checking the nuance** — where a caveat matters, a short scope note adds the
   one qualifying point, still in plain language.
4. **Deciding** — she accepts or dismisses without re-reading, because the claim
   and the two cited clauses line up clearly.
5. **Asking the copilot** — when she asks the copilot a question, the answer
   comes back direct and readable, in the same plain register, with citations
   intact.

## Acceptance Criteria

### Scenario: A same-topic finding names both sides in plain language

```gherkin
Given a finding links Aisyah's draft clause "OpRes PD 2.1" to "BCBS OpRes Principle 1"
  And the finding's label is "aligns-with"
When Aisyah reads the finding's summary line
Then the summary is a single sentence in everyday professional English
  And it says in plain terms what her draft requires and what the other document requires
  And it does not merely restate the label word "aligns-with"
  And the two clause references are still shown exactly, unchanged
```

### Scenario: A coverage finding no longer stacks three points into one line

```gherkin
Given a finding is labelled "goes-beyond"
  And Aisyah's draft "OpRes PD 4.7" mandates a tested exit plan per critical third party
  And the other document is silent on that specific obligation
When Aisyah reads the finding
Then the summary states, in one plain sentence, that her draft goes beyond the other document on this point
  And the specific point the other side omits is carried in a short scope note, not crammed into the summary
  And she understands the gap without re-reading
```

### Scenario: Regulatory jargon is only used when it comes from the cited clause

```gherkin
Given a finding's cited clauses do not contain the phrase "operational resilience posture"
When the explanation is written
Then the summary and scope note do not introduce that phrase
  And any specialist term that does appear is one that is present in the quoted clause text
```

### Scenario: Explanations stay within a readable length

```gherkin
Given any finding is displayed
When Aisyah reads its summary and scope note
Then the summary is no longer than one short sentence within the length cap
  And the scope note, when present, is one short qualifying sentence within its own cap
  And neither runs long enough to wrap into a dense paragraph on the card
```

### Scenario Outline: Each label reads clearly and names the relationship

```gherkin
Given a finding carries the label <label>
When Aisyah reads its summary
Then the summary describes <relationship> in plain terms naming both sides where both are cited

Examples:
  | label          | relationship                                                        |
  | aligns-with    | the two clauses agree or one adopts the other                        |
  | differs-on     | same topic, different position, with the tighten/loosen sense plain  |
  | conflicts-with | the two clauses cannot both be followed                              |
  | silent-on      | the other document covers a point her draft does not                 |
  | goes-beyond    | her draft covers a point the other document does not                 |
```

### Scenario: The verbatim-citation guarantee is unchanged

```gherkin
Given a finding or copilot answer makes a claim about what a regulation says
When Aisyah reads it
Then every such claim is backed by a clause quoted exactly, with its clause number
  And where no clause supports a claim, the text says "No matching clause found" rather than inventing one
```

### Scenario: Copilot answers adopt the plain register

```gherkin
Given Aisyah asks the copilot a question about her draft
When the copilot replies
Then the answer is written in direct, plain professional English
  And it avoids dense formal phrasing that obscures the point
  And its citations and any proposed draft text are unchanged in accuracy
```

### Scenario: Demo-visible committed findings meet the same bar

```gherkin
Given the Operational Resilience and Open Finance demo workstreams are loaded
When Aisyah opens their finding queues
Then every displayed finding's summary and scope note read clearly on first pass
  And none requires re-reading to understand what each side does
```

## Business Rules & Constraints

- **One idea per summary.** The summary is a single sentence stating the
  relationship in plain terms. A coverage finding's "what the other side omits"
  detail moves to the scope note; it is not stacked into the summary.
- **Name both sides plainly.** When a finding cites a clause on each side, the
  explanation says what each document does — not a bare label restatement such
  as "these differ".
- **Jargon only from the clause.** Specialist regulatory phrasing may appear in
  an explanation only if that phrasing is present in the quoted clause text.
  Otherwise use plain equivalents.
- **Length caps.** Summary: one sentence, at most 20 words. Scope note: at most
  one sentence, at most 30 words. Text exceeding the cap is rejected as
  low-quality phrasing.
- **Nuance goes in the scope note.** A qualifying caveat that genuinely matters
  is kept, phrased plainly, in the scope note — never dropped for brevity, never
  forced into the summary.
- **Citation rule stands.** Clause quotation, clause numbers, and the "No
  matching clause found" fallback are unchanged. Nothing here licenses inventing,
  paraphrasing, or dropping a citation.

### Scope boundaries

- **In scope:** the phrasing of finding summaries and scope notes (future
  generated and demo-visible committed ones), and the plain register of copilot
  answers.
- **In scope for the fixture rewrite:** findings shown in the two MVP1 demo
  workstreams (Operational Resilience + Open Finance) and their cross-workstream
  linkages.
- **Out of scope:** committed findings in non-demo workstreams (rewrite deferred,
  lower priority); the finding card and copilot panel visual design; the linkage-
  finding logic, labels, and citations themselves.

## Success Metrics

- A reviewer reading a sample of demo findings cold rates each as "understood on
  first read" — target: at least 9 of every 10 sampled findings.
- Zero findings in the demo workstreams whose summary exceeds the length cap or
  introduces jargon absent from the cited clauses.
- No regression in citation correctness: every claim in the sampled findings and
  copilot answers is still backed by an exact quoted clause (or the explicit "No
  matching clause found").
- Aisyah (or the standing-in reviewer) no longer reports needing to re-read
  findings to understand them.

## Dependencies

- The existing five-label taxonomy and the verbatim-citation product rule — this
  feature must preserve both.
- The demo build-and-persist approach: because the demo shows committed findings,
  the fixture rewrite must ship alongside the phrasing change to be visible on
  the day.

## Open Questions

- [x] ~~Which explanatory text is in scope?~~ — **Resolved:** finding summary
      line, scope note, and copilot answers.
- [x] ~~Fix only the generator, or also the committed demo findings?~~ —
      **Resolved:** both; the demo shows committed findings, so unclear phrasing must
      be fixed there too.
- [x] ~~What reading standard?~~ — **Resolved:** plain language that keeps genuine
      nuance, with the nuance carried in a short scope note rather than a dense
      summary.
- [x] ~~Exact length caps?~~ — **Resolved:** summary ≤ 20 words (one sentence);
      scope note ≤ 30 words (one sentence). Revisit only if a real finding cannot be
      stated clearly within them.
- [ ] Should the copilot's "formal policy-document register" instruction be fully
      replaced by the plain register, or kept for proposed draft _clause text_ while
      the conversational answer goes plain? — **Deferred (non-blocking):** the answer
      prose goes plain regardless; whether proposed draft snippets keep a formal
      register can be tuned during implementation without changing scope.

```

```
