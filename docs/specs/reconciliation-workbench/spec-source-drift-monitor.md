# Source Drift Monitor (prepared drift events)

**Ticket:** TBD

When one of the external sources Aisyah benchmarks against changes — a Basel standard is
finalised, a peer regulator updates its guidance, an act is amended — the tool comes to her
with a **drift item**: a plain statement of what materially changed, and the exact list of
clauses in her open draft that are now out of sync, each shown with the precise changed
passage quoted verbatim and a plain-language note of what changed. From a drift item she
opens any affected clause straight into the reconciliation view to resolve it. For the
COPA Hackathon 2026 demo this is demonstrated over **two prepared, dated source-change
events** (a Personal Data Protection Act §129 amendment and a Basel III output-floor change)
— clearly labelled as such — not a continuously-running watcher.

## User Story

As Aisyah R., a policy drafter who benchmarks Bank Negara Malaysia's rulebook against
international standards such as the Basel Committee's, I want the tool to tell me when a
source I rely on has changed and show me exactly which of my draft clauses are now out of
sync — with the exact changed wording quoted — so that I stop having to spot the deltas by
hand every time a benchmark moves, and can go straight to reconciling the clauses that
actually matter.

## Background & Context

**Current state:**

- When an external standard changes, no one announces the delta to the drafter. As a
  prudential drafter put it, _"BCBS never declares what changed — the drafter has to spot
  the deltas manually."_
- Today Aisyah learns a benchmark has moved only when she happens to re-read it, hears it
  in a meeting, or stumbles on it while researching something else. She then re-reads the
  old and new versions side by side to work out what actually changed, and hunts through
  her own draft by hand to find which clauses the change touches.
- She has already been through the Workbench for her draft: she uploaded it, saw the
  sources connected to each paragraph, and reconciled several connections into a decision
  trail (those steps belong to the upload & workspace and connection reconciliation
  features — not this one).

**Problem:**

- Delta-spotting is slow, manual, and easy to miss. A benchmark can move and the drafter
  not realise for weeks that a clause is now out of step with it.
- Even once she knows a source changed, mapping the change onto the _specific_ affected
  clauses is manual reading work — and it is where clauses silently fall out of sync.
- Only Bank Negara Malaysia sits where it can watch the whole web of sources against its
  own in-flight drafts; a regulated institution sees only published output. This proactive
  view is the tool's sharpest differentiation, and it directly serves the delta-detection
  pain named across the benchmarking departments.

## Target User & Persona

- **Who:** Aisyah R., a Bank Negara Malaysia policy drafter, especially in her
  benchmarking role tracking international standards such as those of the Basel Committee.
  She is the domain expert; the tool proposes, she decides.
- **Context:** She has an open draft in the Workbench. A source she benchmarks against has
  a dated change. She wants to know, without hunting, whether and where that change touches
  her draft.
- **Current workaround:** Finds out a benchmark moved by chance, then reads old-versus-new
  by hand and searches her own draft clause by clause to find what is affected.

## Goals

- Bring a changed source to Aisyah as a drift item, rather than making her discover it.
- For each drift item, state in plain language what materially changed, and list exactly
  which of her draft clauses are now out of sync — each with the precise changed passage
  quoted verbatim.
- Show which candidate clauses were considered and found **not** affected, so she can trust
  the affected list is not padded with false links.
- Let her open any affected clause straight into the reconciliation view to resolve it
  (align / deviate / gap) and justify the call.
- Treat the "these clauses are affected" list as a prompt to check — never an
  auto-applied truth. Aisyah confirms.
- Let her see why a change was judged material enough to queue.

## Non-Goals

- **A continuously-running source watcher.** For the demo the Monitor is shown over
  prepared, dated source-change events, clearly labelled as prepared. A service that
  continuously polls sources on the internet is the roadmap north star and is out of scope
  here.
- **Auto-detecting changes to the drafter's own draft.** This feature watches _external
  sources_ changing. It does **not** watch Aisyah's Word document for edits and re-run
  checking on its own — after she edits, she re-runs analysis herself via "Analyse this
  paragraph" (owned by the grounded redraft assistant feature). Auto-detecting draft edits is
  the same drift machinery "pointed inward" and is a labelled **roadmap** item, not MVP1.
- **The reconciliation act and the decision trail.** Opening an affected clause hands off
  to the reconciliation view; judging the verdict, acting on it, and recording it into the
  trail belong to the connection reconciliation feature, not this one.
- **How connections and changed passages are found.** Detecting the change and matching it
  to clauses is the connection engine's job; this feature is how the drafter _experiences_
  that result.
- **The grounded redraft assistant (Word write-back), and upload/workspace.** Out of scope — referenced,
  not re-specified.
- **Defining the exact materiality threshold.** This feature lets Aisyah see _why_ a change
  was judged material; the precise threshold that separates substance from noise is a known
  open question, deferred and informed by drafter validation.

## User Workflow

1. **A drift item arrives** — Aisyah opens the Workbench and sees a drift queue with a new
   item, for example: _"Basel III output-floor standard finalised — 1 clause in your draft
   is now out of sync."_ The item is clearly marked as a prepared, dated demo event, not a
   live feed.
2. **She opens the item** — It names the source and the date of the change, states in plain
   language what materially changed, and lists each affected draft clause. For each affected
   clause she sees the exact changed passage quoted verbatim (or clearly marked as pending
   verification if the wording has not yet been confirmed word-for-word).
3. **She sees what was ruled out** — Below the affected clauses, the item lists the clauses
   that were considered and found **not** affected, so she can see the affected list was not
   padded with speculative links.
4. **She checks why it was queued** — She can see the reason the change was judged material
   enough to reach her queue.
5. **She hands off to reconcile** — From an affected clause she opens it straight into the
   reconciliation view, where she resolves align / deviate / gap and justifies the call.
6. **The list is hers to confirm** — The affected list is a prompt: until she opens a clause
   and reconciles it, nothing about her draft has changed. The tool proposes; she commits.

## Acceptance Criteria

> Scenarios are written from Aisyah's perspective — what she sees and does. The primary
> worked example is the Personal Data Protection Act §129 amendment (2010 → 2024); the
> headline example is a Basel output-floor change; a Mandatory-Authority peer-regulator
> update is a third.

### Scenario: A drift item appears for a changed source

```gherkin
Given Aisyah has an open draft in the Workbench
  And the Personal Data Protection Act §129 was amended in 2024
When she opens the Workbench
Then she sees a drift item stating "Personal Data Protection Act §129 amended (2024) — 3 clauses in your draft are now out of sync"
  And the item shows the source name and the date of the change
  And the item is labelled as a prepared, dated demonstration event rather than a live feed
```

### Scenario: Opening a drift item shows what changed and the exact changed passage

```gherkin
Given a drift item exists for the Personal Data Protection Act §129 amendment
When Aisyah opens it
Then she sees a plain-language note that the whitelist regime was removed and replaced by a self-assessed test of a "substantially similar law OR an adequate level of protection", that the default was flipped, and that "data user" was renamed "data controller"
  And she sees the exact changed passage quoted verbatim from the amended section
  And the quoted passage is marked as verified word-for-word against the source
```

### Scenario: The drift item lists exactly which draft clauses are affected

```gherkin
Given Aisyah has opened the drift item for the Personal Data Protection Act §129 amendment
When she reviews the list of affected clauses
Then she sees the following clauses listed as affected, each with its own reason:

  | Affected clause                 | Reason the change touches it                                     |
  | RMiT 10.50(c)                   | Relies on the cross-border transfer test the amendment rewrote   |
  | RMiT 10.50(j)                   | Relies on the cross-border transfer test the amendment rewrote   |
  | RMiT 17.1                       | Governs data handling the amendment's default-flip now affects   |

  And each affected clause shows the exact changed passage it is out of sync with, quoted verbatim
```

### Scenario: The drift item shows the clauses considered and ruled out — no false links

```gherkin
Given Aisyah has opened the drift item for the Personal Data Protection Act §129 amendment
When she reviews the clauses the tool considered
Then she sees a "not affected" list naming the clauses that were checked and excluded, including RMiT 8.1, RMiT 11.1, RMiT 17.1(b) and RMiT 17.1(c)
  And no clause appears in both the affected and the not-affected lists
  And she can trust the affected list was not padded with clauses the change does not touch
```

### Scenario: The tool volunteers a caveat where the link is topical, not a literal citation

```gherkin
Given the drift item maps the Personal Data Protection Act §129 amendment to RMiT 10.50(c), 10.50(j) and 17.1
  And no RMiT clause literally cites the Personal Data Protection Act
When Aisyah reviews the affected clauses
Then she sees a caveat stating that no clause literally cites the Act, so the link is a topical inference she should confirm
  And the caveat does not remove the clauses from the affected list
```

### Scenario: A headline Basel drift item carries the changed passage

```gherkin
Given the Basel Committee finalised its output-floor standard setting an aggregate floor of 72.5%
  And Aisyah's draft contains a capital-treatment clause that relies on the earlier position
When she opens the drift item "Basel III output-floor standard finalised — 1 clause in your draft is now out of sync"
Then she sees a plain-language note that the aggregate output floor is now set at 72.5%
  And she sees the affected capital-treatment clause with its reason
  And if the exact Basel wording has not yet been verified word-for-word, the changed passage is clearly marked as pending verification rather than shown as verified
  And no approximated or paraphrased wording is presented as the verbatim source passage
```

### Scenario: Opening an affected clause hands off to the reconciliation view

```gherkin
Given Aisyah is viewing the drift item for the Personal Data Protection Act §129 amendment
  And RMiT 10.50(c) is listed as affected
When she opens RMiT 10.50(c) from the drift item
Then the clause opens in the reconciliation view alongside the changed source passage
  And she can there judge align / deviate / gap and justify the call
```

### Scenario: The affected list is a prompt, not an applied change

```gherkin
Given Aisyah has opened the drift item for the Personal Data Protection Act §129 amendment
  And it lists RMiT 10.50(c), 10.50(j) and 17.1 as affected
When she reads the affected list but has not yet opened any clause to reconcile it
Then none of the listed clauses has been altered in her draft
  And no verdict has been recorded for any of them
  And her draft changes only after she opens a clause and reconciles it herself
```

### Scenario: A material peer-regulator change is queued and Aisyah can see why

```gherkin
Given the Monetary Authority of Singapore updated its artificial-intelligence guidance
  And the update changes a substantive expectation rather than only re-wording
When Aisyah opens the resulting drift item "Monetary Authority of Singapore updated its AI guidance — 3 clauses in your draft diverge"
Then she sees the 3 affected clauses each with the changed passage quoted verbatim
  And she can see the reason the change was judged material enough to queue
```

### Scenario Outline: Material changes are queued; non-material edits are not

```gherkin
Given a watched source has an edit described as <change_description>
When the tool assesses whether the edit is material
Then the edit <queued_outcome>

Examples:
  | change_description                                                        | queued_outcome                                                   |
  | a substantive rewrite of the cross-border transfer test                   | is queued as a drift item, with the reason shown to Aisyah       |
  | a change to the numeric output floor a clause relies on                   | is queued as a drift item, with the reason shown to Aisyah       |
  | a typographical fix and renumbering that changes no obligation            | is not queued as a drift item                                    |
```

### Scenario: A source change with no affected clauses gives a clean result

```gherkin
Given a watched source changed
  And none of the clauses in Aisyah's open draft rely on the part that changed
When the tool assesses the change against her draft
Then she sees a drift item stating the source changed but that no clause in her draft is affected
  And no clause is falsely listed as affected
  And she is not sent to reconcile anything
```

### Scenario: The honest "prepared single event" labelling is always visible

```gherkin
Given Aisyah is viewing any drift item in the demo
When she reads the item
Then it is clearly labelled as a prepared, dated single source-change event
  And nothing implies the tool is continuously watching sources live
```

## Business Rules & Constraints

- **Prepared events, honestly labelled.** In this release the Monitor is demonstrated
  over two prepared, dated source-change events (PDPA §129 and the Basel output floor), each
  labelled as such. A
  continuously-running watcher is explicitly not part of this feature.
- **Verbatim-citation guardrail.** Every changed passage a drift item shows must be quoted
  exactly from the source, with the source and section identified. Where the exact wording
  has not yet been verified word-for-word (for example, the Basel output-floor passage
  before it is confirmed), it is shown clearly marked as pending verification — never
  approximated and never presented as verified.
- **Verified-versus-pending marking.** Every quoted changed passage is marked either
  verified (checked word-for-word against the source) or pending verification. A pending
  passage may never be presented as verified.
- **No false clause links.** A drift item lists only clauses the change genuinely touches,
  and shows the clauses it considered and ruled out. A clause that does not rely on the
  changed part must not appear as affected. If nothing is affected, the item says so.
- **AI proposes, human commits.** The affected-clause list is a prompt for Aisyah to check.
  Reading it changes nothing in her draft; her draft changes only when she opens a clause
  and reconciles it in the reconciliation view.
- **Materiality is visible; the threshold is open.** Every queued change carries a
  human-readable reason it was judged material. The precise threshold that separates
  material substance from noise is a deferred open question.
- **Topical inference is disclosed.** Where an affected clause does not literally cite the
  changed source (as with the Personal Data Protection Act §129 case), the drift item states
  that the link is a topical inference to confirm.
- **Hand-off, not duplication.** Opening an affected clause hands off to the reconciliation
  view; this feature does not itself record verdicts or maintain the decision trail.

## Success Metrics

- **Delta surfaced without manual diffing:** for the prepared event, Aisyah learns a
  benchmark changed and which clauses it touches from the drift item, without reading the
  old and new source versions side by side herself.
- **Correct linkage, zero false links:** on the prepared Personal Data Protection Act §129
  event, the affected list matches the hand-verified list (RMiT 10.50(c), 10.50(j), 17.1)
  exactly, and the not-affected list correctly excludes RMiT 8.1, 11.1, 17.1(b) and 17.1(c),
  with no clause falsely listed as affected.
- **Zero unsupported or approximated passages:** every changed passage shown is either
  verified verbatim against the source or clearly marked as pending verification; no
  approximated wording is presented as a source passage.
- **Clean hand-off:** from a drift item Aisyah can open an affected clause into the
  reconciliation view in the demo.

## Dependencies

- **Connection engine** — supplies the detected change and the mapping of the changed
  passage to affected and not-affected clauses. This feature presents that result.
- **Connection reconciliation & decision trail** — the hand-off target when Aisyah opens an
  affected clause to resolve and justify it.
- **Prepared drift event** — one dated source change with a hand-verified list of affected
  and not-affected clauses. The Personal Data Protection Act §129 (2010 → 2024) amendment
  is proven and available; the Basel output-floor change is the headline, whose exact
  wording ships verified verbatim or marked pending verification.
- **Open draft in the Workbench** — Aisyah must already have an open draft for a change to
  be assessed against.

## Rollout Considerations

- **Demo scope:** two prepared, dated drift events. The **Personal Data Protection Act §129
  amendment** is the proven mechanism (its linkage is green from a blind test and its
  passages are verified verbatim); the **Basel III output-floor** change is the headline that
  carries the IMF deviation-justification story (its wording ships verified verbatim or
  clearly marked pending verification). The pushed drift item sells "it comes to me" while
  the label makes clear these are prepared single events.
- **Honesty labelling (non-negotiable):** each drift item is visibly a prepared, dated event;
  nothing suggests a live watcher.
- **Roadmap slide:** (a) the continuously-running Monitor that watches the source web and
  pushes drift as it happens; and (b) the same drift machinery "pointed inward" —
  auto-detecting edits to the drafter's own Word document and re-running checking. Both are
  the next phase; this release proves the pattern on prepared source events with
  drafter-triggered re-analysis.

## Open Questions

- [x] ~~Is the Monitor built or roadmap-only for this release?~~ — **Resolved:**
      demonstrated over **two** prepared, dated source-change events — the Personal Data
      Protection Act §129 amendment (proven mechanism) and the Basel III output-floor change
      (headline / IMF story). The continuously-running watcher is the roadmap north star.
      Delta detection and clause linkage were proven green in a blind test on the PDPA §129
      amendment.
- [x] ~~Should a change to the drafter's own draft auto-trigger re-checking?~~ — **Resolved:**
      not in MVP1. This feature watches external sources; after the drafter edits her draft
      she re-runs analysis herself ("Analyse this paragraph"). Auto-detecting Word-document
      edits is the same drift machinery pointed inward and is a labelled roadmap item.
- [x] ~~Should the drift item show clauses it ruled out, not only the affected ones?~~ —
      **Resolved:** yes — showing the not-affected clauses is how Aisyah trusts the affected
      list is not padded; the proven green test explicitly listed the not-affected clauses.
- [ ] **What counts as a "material" source change worth queuing?** —
      **Deferred (non-blocking):** the feature shows the reason a change was queued; the
      precise threshold separating substance from noise will be settled with drafter
      validation and does not block this release.
- [ ] **How "live" must the drift beat look, and exactly where is the prepared-versus-live
      line drawn and labelled?** — **Deferred (non-blocking):** a prepared single event is
      honest and low-risk; the exact framing is settled during implementation.
- [x] ~~Can the Basel output-floor changed passage be verified verbatim before the demo?~~
      — **Resolved:** sourcing it is a build task that will be attempted; if it cannot be
      verified word-for-word in time, the drift item ships the passage clearly marked as
      pending verification — never approximated. This affects the Basel example's content,
      not the feature's behaviour.
- [ ] **Is the proactive drift queue actually preferred over on-demand checking?** —
      **Deferred (non-blocking):** awaiting a drafter conversation. If drafters prefer their
      own cadence, this drops to a labelled roadmap phase and the release is the reactive
      Workbench.
