# Consistency Ripple Check & Impact Report

**Ticket:** [#8](https://github.com/dzaffren/copa-hackathon/issues/8)

When a policy drafter revises a clause, Rulebook Radar traces the ripple across
every linked policy in the cluster and produces a plain-language impact report of
Conflict, Duplication, and Gap findings — each one quoting the exact clause it is
based on. The drafter can act on every finding (accept the suggested fix or dismiss
it with a recorded reason) and, once all findings are resolved, submit the now-
consistent draft to their reviewer and approving manager. This turns a slow, memory-
dependent cross-policy consistency check into a fast, cited, and closeable task.

## User Story

As a policy drafter, I want to see the ripple my clause change creates across the
rest of the rulebook — each finding citing the exact clause it relies on — and act on
each finding until the draft is consistent, so that I can revise a policy without
silently contradicting, duplicating, or leaving a gap against another policy, and hand
a clean draft to review.

## Background & Context

**Current state:**

- When a drafter revises one policy, checking that it stays consistent with the rest
  of the rulebook is a manual, memory-dependent task. The drafter has to recall which
  other policies might be affected and read each one.
- The connections between policies — which rules overlap, depend on, or reference each
  other — live in the heads of experienced staff, not in any shared map.
- There is no structured way to record that a possible clash was reviewed and either
  fixed or consciously set aside.

**Problem:**

- A revised clause can silently contradict, duplicate, or leave a gap against another
  policy, and the clash may only surface much later — after the change is in force.
- The check is slow and error-prone, and depends on individual expertise that is hard
  to scale, hand over, or reconstruct months later.
- Even when a drafter suspects a clash, verifying it means re-reading long documents to
  find the exact clause involved.

## Target User & Persona

- **Who:** A policy drafter (for example, Aisyah) assigned to edit one or more policies
  in the technology-risk cluster (such as RMiT and Operational Resilience).
- **Context:** She encounters this need at the moment she revises a clause in a live
  working draft and needs to know what her change breaks elsewhere before she hands the
  draft to review.
- **Current workaround:** She recalls from memory which other policies might be affected,
  opens and re-reads each one, and manually judges whether her change clashes — with no
  cited trail and no record of what she checked.

## Goals

- Automatically trace a clause change across every linked policy in the cluster and
  surface where it creates a Conflict, a Duplication, or a Gap.
- Make every finding independently verifiable in seconds by quoting the exact clause it
  is based on — and, for a Gap where no clause exists, say so explicitly and name the
  nearest related clause rather than invent one.
- Let the drafter act on every finding — accept the suggested fix or dismiss it with a
  recorded reason — and reach a clean, submittable draft.
- Give an at-a-glance summary (open-finding count and a breakdown by type) that updates
  live as findings are resolved.

## Non-Goals

- **Producing or applying the redrafted clause text.** The suggested fix is described in
  plain language here; generating and writing the actual replacement text into the living
  draft belongs to the Drafting copilot story. This report only reflects the resolved
  state that flows back from an applied redraft.
- **The reviewer and manager experience after submission.** This story ends at "submit"
  and the notification being sent; the review, commenting, and approval steps belong to
  the Reviewer & approval workflow story.
- **The graph visualisation and edge explanations.** Seeing and navigating the cluster
  graph belongs to the Drafter rulebook workspace story.
- **Cross-cluster ripple.** Findings are traced within the single technology-risk cluster
  only.

## User Workflow

1. **Revise a clause** — Aisyah edits a clause in a policy she is assigned to (for
   example, moving RMiT clause 17 from prior consultation to notify-within-14-days). The
   tool detects the edit and offers to analyse the ripple.
2. **See the impact report** — She opens the report. It names the policies it scanned and
   lists each finding: a type (Conflict, Duplication, or Gap), the affected policy, a
   plain-language summary, the exact clause it cites, a suggested fix, and an AI-confidence
   indicator. A summary shows the open-finding count and chips by type.
3. **Verify each finding** — For each finding she reads the quoted clause to confirm the
   issue is real. For a Gap, she sees "No matching clause found" and the nearest related
   clause, so she trusts nothing was invented.
4. **Act on each finding** — She accepts the suggested fix (which resolves the finding) or
   dismisses it, recording a reason. The open count and chips update as she goes.
5. **Submit** — When no findings remain open, the report shows "Submit draft to reviewer /
   manager." She submits; her reviewer and approving manager are notified and she sees
   confirmation.

## Acceptance Criteria

### Scenario: Revising a clause produces a cited ripple report

```gherkin
Given Aisyah is the assigned drafter for RMiT and Operational Resilience
  And RMiT and Outsourcing (2019) are linked policies in the technology-risk cluster
When she revises RMiT clause 17 from prior consultation to "notify the Bank within 14 days"
  And she runs the ripple check
Then she sees an impact report titled for RMiT clause 17
  And the report states it scanned the 4 linked policies
  And she sees three findings: one Conflict, one Duplication, and one Gap
  And each finding shows a plain-language summary, a cited source, a suggested fix, and an AI-confidence indicator
```

### Scenario: The report opens on an already-made change

```gherkin
Given Aisyah has previously revised RMiT clause 17 and the change is saved in the draft
When she opens the impact report for that draft without making a new edit
Then she sees the same ripple findings for the saved change
  And she can act on each finding as normal
```

### Scenario: Every finding cites its exact clause verbatim

```gherkin
Given the ripple report for the RMiT clause 17 change is open
When Aisyah reads the Conflict finding against Outsourcing (2019)
Then the cited source reads: Outsourcing 12.1: "A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement."
  And the summary explains that RMiT's new "notify within 14 days" is out of step with 12.1's prior-written-approval where a cloud service is also a material outsourcing
  And the AI confidence for this finding shows 93%
```

### Scenario: A Gap finding states no clause exists rather than inventing one

```gherkin
Given the ripple report for the RMiT clause 17 change is open
When Aisyah reads the Gap finding
Then the cited source reads: "No matching clause found in the draft. Nearest: 17.1(a) currently requires a comprehensive risk assessment per para 10.50 and Appendix 10 — but only in the consultation path being removed."
  And the suggested fix is to add a clause requiring the 10.50 / Appendix 10 risk assessment before notification
  And the AI confidence for this finding shows 74%
  And no fabricated clause number or wording is presented as a citation
```

### Scenario Outline: The three finding types each carry a summary, verbatim citation, fix, and confidence

```gherkin
Given the ripple report for the RMiT clause 17 change is open
When Aisyah reads the <type> finding
Then it is labelled "<type>"
  And it names the affected policy "<policy>"
  And it quotes the exact clause "<citation>"
  And it shows an AI confidence of <confidence>

Examples:
  | type        | policy                        | citation                                                                                                                                                                                                            | confidence |
  | Conflict    | Outsourcing (2019)            | Outsourcing 12.1: "A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement."                                                                     | 93%        |
  | Duplication | RMiT 17.1 vs 17.2 (same doc)  | RMiT 17.2: "...submitting the notification together with the necessary updates to all the information required under paragraph 17.1..."                                                                              | 82%        |
  | Gap         | RMiT clause 17 (draft)        | No matching clause found in the draft. Nearest: 17.1(a) currently requires a comprehensive risk assessment per para 10.50 and Appendix 10 — but only in the consultation path being removed.                         | 74%        |
```

### Scenario: A lighter change produces a single finding

```gherkin
Given Aisyah is the assigned drafter for Operational Resilience
When she revises Operational Resilience clause 6.11 (the register of critical services)
  And she runs the ripple check
Then she sees exactly one finding, a Duplication against RMiT's cloud services requirement
  And the cited source reads: Operational Resilience 6.11: "The institution shall maintain a register of all cloud and third-party technology services supporting critical operations."
  And the suggested fix is to reference RMiT as the single source of truth for the register instead of restating it
  And the AI confidence for this finding shows 86%
```

### Scenario: Accepting a suggested fix resolves the finding

```gherkin
Given the RMiT clause 17 report shows 3 open findings
When Aisyah accepts the suggested fix for the Duplication finding
Then that finding is marked accepted
  And its accept and dismiss actions are no longer available
  And the open-finding count changes from 3 to 2
```

### Scenario: Dismissing a finding requires a recorded reason

```gherkin
Given the RMiT clause 17 report shows an open Conflict finding
When Aisyah chooses to dismiss the Conflict finding
Then she is asked to record a reason before the dismissal is accepted
  And when she submits the dismissal without a reason she is told a reason is required and the finding stays open
  And when she records the reason "Prior-approval path for material cloud outsourcing is being handled separately in the Outsourcing revision" and confirms
  Then the finding is marked dismissed
  And its recorded reason is kept as part of the audit trail
```

### Scenario: A dismissed finding counts toward resolution

```gherkin
Given the RMiT clause 17 report has one open finding remaining, a Conflict
When Aisyah dismisses the Conflict with a recorded reason
Then no findings remain open
  And the report shows the "Submit draft to reviewer / manager" action
```

### Scenario: The open count and type chips update as findings are resolved

```gherkin
Given the RMiT clause 17 report shows 3 open findings
  And the summary chips read "1 Conflict · 1 Duplication · 1 Gap"
When Aisyah accepts the fix for the Conflict finding
Then the open-finding count shows 2
  And the summary chips read "1 Duplication · 1 Gap"
When she then accepts the fix for the Duplication finding
Then the open-finding count shows 1
  And the summary chips read "1 Gap"
```

### Scenario: A finding resolved by an applied copilot redraft comes back resolved

```gherkin
Given the RMiT clause 17 report shows an open Conflict finding against Outsourcing (2019)
  And Aisyah opens the drafting copilot and applies a redraft that reconciles that conflict
When she returns to the impact report
Then the Conflict finding is marked resolved
  And the open-finding count reflects one fewer open finding
```

### Scenario: Submitting is blocked while findings are still open

```gherkin
Given the RMiT clause 17 report shows 1 or more open findings
When Aisyah looks for a way to submit the draft
Then the "Submit draft to reviewer / manager" action is not available
  And she can see how many findings remain open
```

### Scenario: Submitting once all findings are resolved notifies the reviewer and manager

```gherkin
Given the RMiT clause 17 report has all three findings resolved (accepted or dismissed)
  And the "Submit draft to reviewer / manager" action is available
When Aisyah submits the draft
Then she sees confirmation that the draft was submitted for review
  And her assigned reviewer (Farid M.) is notified
  And her approving manager is notified
```

### Scenario: A submitted draft cannot be submitted again

```gherkin
Given Aisyah has already submitted the RMiT clause 17 draft for review
When she views the impact report again
Then the submit action is no longer available
  And she sees that the draft has already been submitted for review
```

## Business Rules & Constraints

- **Verbatim-citation guardrail (hard rule).** Every finding must quote the exact clause
  text it is based on, with its clause number (for example, Outsourcing 12.1 or RMiT
  17.2). For a Gap where no supporting clause exists, the finding must state "No matching
  clause found" and name the nearest related clause — it must never present an invented
  clause as a citation.
- **AI proposes, human commits.** Findings and their suggested fixes are suggestions only.
  A finding is resolved only when the drafter accepts the fix or dismisses it; the tool
  never resolves a finding on its own.
- **Dismissal requires a recorded reason.** A finding cannot be dismissed without the
  drafter recording a reason, which is kept for the audit trail. A dismissal attempted
  without a reason is rejected and the finding stays open.
- **Dismissed counts as resolved for submission.** For the purpose of reaching the submit
  step, a dismissed finding counts the same as an accepted one; "resolved" means accepted
  or dismissed.
- **Submit is gated on zero open findings.** The "Submit draft to reviewer / manager"
  action is available only when no findings remain open. While any finding is open, submit
  is unavailable.
- **Doc-aware depth.** The number of findings reflects the change: a deep change (RMiT
  clause 17) yields several findings (a Conflict, a Duplication, and a Gap), while a lighter
  change (Operational Resilience clause 6.11) yields a single finding.
- **Each finding carries a fixed shape.** Type (Conflict, Duplication, or Gap), affected
  policy, plain-language summary, cited source, suggested fix, and an AI-confidence
  indicator.
- **Summary reflects only open findings.** The open-finding count and the type chips count
  only findings that are still open, and update immediately as findings are resolved.
- **Submit is a one-time action per draft.** Once a draft is submitted for review, it
  cannot be submitted again from this report.

## Success Metrics

- **Faster consistency review (MW10 KR3):** a drafter completes one real cross-policy
  consistency review at least 15% faster with the ripple report than by manually re-reading
  linked policies, on the same change.
- **Fewer missed clashes:** on a labelled set of known conflicts, duplications, and gaps
  for a given change, the report surfaces a higher proportion of the real issues than an
  unaided drafter finds in the same time.
- **Zero unsupported claims:** 100% of findings quote an existing clause verbatim, and every
  Gap with no clause says so explicitly; any citation that cannot be verified against the
  source document is treated as a defect.
- **Loop closure:** in the demo, a drafter can go from a saved clause change through resolving
  every finding to a submitted draft with the reviewer and manager notified.

## Dependencies

- **Knowledge-graph engine.** The linked-policy map and clause index that decide which
  policies are scanned and supply the exact clause text for citations.
- **Drafter rulebook workspace.** Establishes the drafter's assigned documents and role, and
  is where the clause change is made.
- **Drafting copilot with live write-back.** Supplies the resolved state that flows back into
  this report when a redraft is applied.
- **Reviewer & approval workflow.** Receives the submitted draft and the reviewer/manager
  notifications once this report reaches "submit."
- **Locked demo cluster.** The confirmed set of technology-risk policies (RMiT, Operational
  Resilience, Outsourcing, and the other linked policies) whose ripple is traced.

## Open Questions

- [x] ~~Should the tool flag only conflicts, or also duplications and gaps?~~ — **Resolved:**
      flag all three (Conflict, Duplication, Gap); gaps were found reliably in testing and are
      the most valuable.
- [x] ~~Can the drafter reach "submit" by dismissing findings, not only fixing them?~~ —
      **Resolved:** yes; a dismissed finding counts as resolved for submission, but a dismissal
      must record a reason for the audit trail.
- [x] ~~When should the ripple check run?~~ — **Resolved:** the intended behaviour is
      edit-then-analyse — the tool reacts when the drafter makes an edit. The report can also be
      re-opened on an already-saved change.
- [ ] Should low-confidence findings (for example, below a set threshold) be visually
      separated or collapsed by default, or always shown in full? — **Deferred (non-blocking):**
      all findings are shown with their confidence indicator for the demo; presentation tuning can
      follow once drafters give feedback.

---

## Engine contract (forward reference)

> Not a full technical refinement of this story — that happens when #8 is run
> through `prd-refine`. This section records how the finding shape maps onto the
> [knowledge-graph engine](spec-knowledge-graph-engine.md) so the two specs stay
> consistent. The engine (#6) is the source of truth for these fields.

Each finding in this report is derived from a **graph edge** produced by the
engine, plus the clause text fetched by number. The mapping:

| Impact-report field                              | Engine source (from `graph.json` / clause index)                                                                                                            |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Type (Conflict / Duplication / Gap)              | **Classified by this story (#8)** from the edge — the engine emits raw clause-anchored connections and does **not** classify (per #6 Negative Constraints). |
| Affected policy                                  | Edge `target` node (or `source` for same-doc duplications)                                                                                                  |
| Plain-language summary                           | Edge `reason` (engine-supplied), refined for the finding                                                                                                    |
| Cited source (verbatim clause)                   | `GET /clauses/{n}` for each clause in `source_clauses` / `target_clauses`                                                                                   |
| **AI confidence indicator** (e.g. 93%, 82%, 74%) | Edge **`confidence`** field (0.0–1.0) — `llm-found` edges carry the model score this indicator displays; `structural`/`curated` edges are `1.0`             |
| Suggested fix                                    | Generated by #8 (and applied via the copilot, #9)                                                                                                           |

**Confidence source of truth.** The percentages shown in this spec's Acceptance
Criteria (Conflict 93%, Duplication 82%, Gap 74%) are the human-readable form of
the engine's `confidence` field on the corresponding edge. They are illustrative
demo values; the engine supplies the actual score per edge and #8 renders it —
neither spec invents a separate confidence number.

**Gap findings and the guardrail.** A Gap has no supporting clause by definition.
It is **not** a low-confidence edge — the engine reports the absence honestly
("No matching clause found" + nearest related clause via the citation validator),
and #8 presents that as the Gap's cited source. Confidence grades _supported_
connections; it never rescues or represents an unsupported one.

**Retrieval.** #8 reads the graph (edges + anchoring clause numbers) first, then
hydrates only the clauses a finding cites via `GET /clauses/{n}` — the
hierarchical pattern in the engine spec, never dumping the whole cluster into the
report.
