# Drafting Copilot with Live Write-Back

**Ticket:** TBD

A grounded drafting assistant that a policy drafter uses to understand and fix
the consistency findings on their draft. It answers questions about the rulebook,
proposes redrafted clause wording that fixes a clash, and — on request — pushes
back on the drafter's own wording with pointed challenges. Every answer quotes the
exact clause it relies on. When the drafter accepts a redraft, the copilot writes
it into the living working document as a tracked change (the old wording struck
through, the new wording inserted) for a human to accept or reject; the copilot
never finalises policy text on its own. Applying a redraft marks the matching
consistency finding resolved and offers to re-run the consistency check, closing
the drafter's fix loop.

## User Story

As a policy drafter, I want a grounded copilot that answers my questions about the
rulebook, redrafts a problem clause to fix a consistency finding, and challenges my
own wording — always quoting the exact clause it relies on — and that writes an
accepted redraft into my living working document as a tracked change for me to
accept or reject, so that I can fix cross-policy clashes quickly and confidently
without ever trusting an unsupported claim or letting the tool change the policy
text on its own.

## Background & Context

**Current state:**

- When a consistency check flags that a revised clause clashes with another policy,
  the drafter must work out the fix by hand: re-read the affected clauses, reason
  about how to reconcile them, and manually retype the corrected wording into the
  working document.
- Any help a general assistant might give is untethered from the actual rulebook —
  it can assert a rule that does not exist, or paraphrase a clause inaccurately,
  which is unsafe for policy text.
- There is no fast way for the drafter to have their own proposed wording
  challenged before they commit to it, so weak drafts survive until review.

**Problem:**

- Turning a flagged clash into corrected, defensible clause wording is slow and
  memory-dependent, and re-reading the source clauses to get the fix right takes as
  long as finding the clash did.
- An assistant that cannot be trusted to quote the real rule is worse than no
  assistant — a plausible but invented clause can slip into a policy.
- Manually copying corrected text between a helper and the working document is
  error-prone and loses the trail of what changed and why.

## Target User & Persona

- **Who:** A policy drafter (for example, Aisyah) assigned to edit one or more
  policies in the technology-risk cluster, such as the RMiT draft and the
  Operational Resilience draft.
- **Context:** She reaches the copilot from the impact report after a consistency
  check flags a clash on the clause she just revised. She wants to understand the
  clash, get corrected wording she can stand behind, and get it into the working
  document without retyping.
- **Current workaround:** She re-reads the clashing clauses by hand, reasons out a
  fix, retypes it into the working document, and relies on memory (not a cited
  trail) that the fix actually satisfies the other policy.

## Goals

- Give the drafter three grounded ways to work a finding: ask a question about the
  rulebook or the clash, request a redrafted clause that fixes it, and have the
  copilot grill her own draft with pointed challenges.
- Guarantee every answer quotes the exact clause(s) it relies on, and that a
  question with no supporting clause returns an explicit "no clause supports this"
  rather than an invented one.
- Write an accepted redraft into the living working document as a tracked change —
  old wording struck through, new wording inserted — for a human to accept or
  reject, with a visible saving-then-synced indicator.
- Close the fix loop: applying a redraft marks the matching consistency finding
  resolved and offers a link back to re-run the consistency check.
- Keep the copilot scoped to the document the drafter currently has open and
  grounded in that document's cluster.

## Non-Goals

- **Producing the consistency findings themselves.** Detecting the Conflict,
  Duplication, and Gap and listing them belongs to the Consistency ripple check &
  impact report story. This copilot consumes those findings and reports back that
  one is resolved.
- **The final accept/reject of the tracked change.** The copilot inserts the
  tracked change; a human accepting or rejecting it inside the working document is
  a human action the copilot does not perform. This story guarantees the change is
  inserted as a proposal only.
- **Submitting the draft for review, or the reviewer/manager experience.**
  Reaching "submit" and the review workflow belong to other stories.
- **The graph visualisation and edge explanations.** Navigating the cluster graph
  belongs to the Drafter rulebook workspace story.
- **Cross-cluster grounding.** The copilot is grounded only in the single
  technology-risk cluster of the open document.

## User Workflow

1. **Open the copilot on a draft** — From the impact report for the clause she
   revised, Aisyah opens the copilot. It greets her, confirms which draft it is
   connected to (for example, the RMiT draft) and that it is grounded in that
   cluster, and shows quick-prompt chips: ask about the clash, redraft the clause,
   and grill my draft. A live document viewer sits beside the chat showing the
   current clause.
2. **Ask about the clash** — She asks what conflicts with her clause. The copilot
   explains the clash in plain language and quotes the exact clause it relies on.
3. **Request a redraft** — She asks the copilot to redraft the clause. It proposes
   new wording that fixes the clash and cites the clauses the redraft is grounded
   on, with an option to apply it to the draft.
4. **Grill the draft (optional)** — She asks the copilot to grill her draft. It
   pushes back with pointed challenges, each tied to a real clause, and offers to
   redraft to address them.
5. **Accept the redraft** — She applies the redraft. The copilot writes it into the
   living working document as a tracked change — the old wording struck through and
   the new wording inserted for a human to accept or reject — showing a saving
   indicator that settles to synced. It confirms nothing is committed without a
   human.
6. **Loop closes** — The copilot tells her the matching consistency finding is now
   marked resolved and offers a link to re-run the consistency check.

## Acceptance Criteria

### Scenario: Asking about a conflict returns a plain-language answer with a verbatim citation

```gherkin
Given Aisyah has the RMiT draft open in the copilot
  And clause 17.1 currently reads "A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud for critical systems."
When she asks whether anything conflicts with clause 17.1
Then the copilot answers that there is a conflict with the Outsourcing policy, which still requires the Bank's prior written approval
  And it quotes the exact clause: Outsourcing 12.1: "A financial institution must obtain the Bank's written approval before entering into a new material outsourcing arrangement."
  And it explains in plain language that a public cloud for a critical system is often also a material outsourcing, so RMiT's "notify within 14 days" is out of step with 12.1's "approve before"
```

### Scenario: Requesting a redraft returns proposed wording with the grounding clauses cited

```gherkin
Given Aisyah has the RMiT draft open in the copilot
  And clause 17.1 has the flagged conflict with Outsourcing 12.1
When she asks the copilot to redraft the clause
Then the copilot proposes the wording "A financial institution shall, prior to the first-time adoption of a public cloud for critical systems, complete the risk assessment required under paragraph 10.50 and Appendix 10, and shall notify the Bank within 14 days of adoption. Where the cloud service is also a material outsourcing arrangement, paragraph 12.1 of the Outsourcing policy continues to apply."
  And it states the redraft is grounded on RMiT 17.1, RMiT 10.50, and Outsourcing 12.1
  And it offers an action to apply the redraft to the draft
```

### Scenario: Grilling the draft returns pointed challenges each tied to a real clause

```gherkin
Given Aisyah has the RMiT draft open in the copilot
  And clause 17.1 currently reads "A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud for critical systems."
When she asks the copilot to grill her draft
Then the copilot pushes back with the challenge that notification may not satisfy Outsourcing 12.1, which still demands prior written approval for a material outsourcing
  And it challenges that the draft dropped the pre-adoption checkpoint that the old wording gave the Bank to raise concerns before go-live
  And it challenges that the 10.50 and Appendix 10 risk assessment is no longer required first
  And it offers to redraft to address the challenges
```

### Scenario: Accepting a redraft writes it into the living working document as a tracked change

```gherkin
Given the copilot has proposed the RMiT clause 17.1 redraft
When Aisyah applies the redraft to the draft
Then the living working document shows the old wording "A financial institution shall notify the Bank within 14 days of the first-time adoption of a public cloud for critical systems." struck through
  And it shows the new wording "A financial institution shall, prior to the first-time adoption of a public cloud for critical systems, complete the risk assessment required under paragraph 10.50 and Appendix 10, and shall notify the Bank within 14 days of adoption. Where the cloud service is also a material outsourcing arrangement, paragraph 12.1 of the Outsourcing policy continues to apply." inserted for a human to accept or reject
  And the copilot confirms the change was inserted as a tracked change and that nothing is committed without a human
```

### Scenario: The write-back shows a saving indicator that settles to synced

```gherkin
Given the copilot has proposed the RMiT clause 17.1 redraft
When Aisyah applies the redraft to the draft
Then she sees a saving indicator while the change is written to the living working document
  And once the write completes the indicator settles to synced
```

### Scenario: Applying a redraft marks the matching finding resolved and offers to re-run the check

```gherkin
Given the impact report shows an open Conflict finding for RMiT clause 17.1 against the Outsourcing policy
When Aisyah applies the RMiT clause 17.1 redraft in the copilot
Then the copilot tells her the matching consistency finding is now marked resolved
  And it offers a link to re-run the consistency check
  And when she returns to the impact report the Conflict finding is shown resolved
```

### Scenario: The copilot never commits the change on its own

```gherkin
Given Aisyah has applied the RMiT clause 17.1 redraft
  And it appears in the living working document as the old wording struck through and the new wording inserted
When she reviews the living working document
Then the change is still a proposed tracked change awaiting a human decision
  And the copilot has not finalised the clause text on its own
  And it is up to her to accept or reject the tracked change in the document
```

### Scenario: An ask with no supporting clause returns "no clause supports this" rather than inventing one

```gherkin
Given Aisyah has the RMiT draft open in the copilot
When she asks whether any clause sets a maximum contract length for a cloud provider
  And no clause in the cluster addresses a maximum contract length
Then the copilot answers that no clause in the rulebook supports this
  And it does not present any invented clause number or wording as a citation
```

### Scenario Outline: Every answer quotes the exact clause it relies on

```gherkin
Given Aisyah has the RMiT draft open in the copilot
When she uses the "<mode>" quick prompt
Then the copilot's answer quotes at least one exact clause from the cluster
  And the answer names the clause it relies on as "<grounded on>"

Examples:
  | mode              | grounded on                          |
  | ask about conflict | Outsourcing 12.1                     |
  | redraft the clause | RMiT 17.1, RMiT 10.50, Outsourcing 12.1 |
  | grill my draft     | Outsourcing 12.1, RMiT 17.1, RMiT 10.50 |
```

### Scenario: Switching to a different draft re-grounds the copilot on that document

```gherkin
Given Aisyah has the Operational Resilience draft open in the copilot
  And clause 6.11 currently reads "The institution shall maintain a register of all cloud and third-party technology services supporting critical operations."
When she asks the copilot whether clause 6.11 duplicates RMiT
Then the copilot answers that clause 6.11 duplicates a register requirement RMiT already owns
  And when she asks it to redraft the clause it proposes wording that references RMiT clause 10 as the single source of truth for the register
  And it states the redraft is grounded on Operational Resilience 6.11 and RMiT clause 10
```

### Scenario: Accepting a redraft on the Operational Resilience draft writes back to that document

```gherkin
Given the copilot has the Operational Resilience draft open
  And it has proposed the clause 6.11 redraft that references RMiT clause 10 as the single source of truth
When Aisyah applies the redraft to the draft
Then the living working document shown is the Operational Resilience draft, not the RMiT draft
  And it shows the old clause 6.11 wording struck through and the new wording inserted for a human to accept or reject
  And the copilot confirms the matching duplication finding is now marked resolved and offers to re-run the check
```

### Scenario: The copilot only grounds in and writes to the currently open draft

```gherkin
Given Aisyah has the RMiT draft open in the copilot
When she asks the copilot to redraft the clause and applies the redraft
Then only the RMiT draft is changed
  And the Operational Resilience draft is not changed
  And the copilot's citations are drawn from the technology-risk cluster the RMiT draft belongs to
```

## Business Rules & Constraints

- **Verbatim-citation guardrail (hard rule).** Every ask, redraft, and grill
  response must quote the exact clause text it relies on, with its clause number
  (for example, Outsourcing 12.1 or RMiT 17.1). A redraft must name the clauses it
  is grounded on. If no clause supports an answer, the copilot must say so
  explicitly (for example, "No clause in the rulebook supports this") and must
  never present an invented clause number or wording as a citation.
- **AI proposes, human commits.** The copilot may answer, propose a redraft, and
  insert it as a tracked change, but it never finalises policy text. An accepted
  redraft appears as the old wording struck through and the new wording inserted,
  awaiting a human to accept or reject it in the living working document. Nothing
  is committed without a human.
- **The living working document is the single source of truth.** The copilot reads
  from and writes to the living working document directly; there is no separate
  in-tool draft and no export step. The tracked change appears in that document.
- **Write-back shows sync state.** Applying a redraft shows a saving indicator
  while the change is written and settles to synced once complete, so the drafter
  can see the write happened.
- **Applying a redraft closes the loop.** Applying a redraft marks the matching
  consistency finding resolved (shared with the impact report) and the copilot
  offers a link to re-run the consistency check.
- **Doc-aware grounding.** The copilot is scoped to the currently open draft and
  grounded in that draft's cluster. Switching between the RMiT draft and the
  Operational Resilience draft re-grounds the copilot and re-targets the write-back
  to the open draft. Applying a redraft changes only the open draft.
- **Three grounded modes.** The copilot offers ask (answer questions about the
  rulebook or the clash), redraft (propose corrected wording that fixes the issue),
  and grill (push back on the drafter's own wording with pointed challenges), each
  surfaced as a quick-prompt chip and each subject to the citation guardrail.

## Success Metrics

- **Faster fixes (MW10 KR3):** a drafter turns a flagged clash into corrected,
  cited clause wording written into the working document at least 15% faster with
  the copilot than by re-reading the clauses and retyping the fix by hand.
- **Zero unsupported claims:** 100% of ask, redraft, and grill responses quote an
  existing clause verbatim, and every answer with no supporting clause says so
  explicitly; any citation that cannot be verified against the source document is
  treated as a defect.
- **Nothing auto-committed:** 100% of accepted redrafts appear as tracked changes
  awaiting a human decision; no clause is ever finalised by the copilot.
- **Loop closure:** in the demo, a drafter can go from a flagged finding, through a
  redraft written into the working document, to the matching finding shown resolved
  and an offer to re-run the check.

## Dependencies

- **Knowledge-graph engine.** Supplies the exact clause text the copilot quotes and
  the cluster grounding for the open draft.
- **Consistency ripple check & impact report.** Supplies the findings the copilot
  helps fix and holds the shared resolved state the copilot updates when a redraft
  is applied.
- **Drafter rulebook workspace.** Establishes which draft the drafter has open and
  their edit role for it.
- **Living working-document location.** An agreed place where the in-progress draft
  lives and can be edited with tracked changes, so the copilot can write an accepted
  redraft back into it.
- **Locked demo cluster.** The confirmed set of technology-risk policies (RMiT,
  Operational Resilience, Outsourcing, and the other linked policies) the copilot is
  grounded in.

## Open Questions

- [x] ~~Does the copilot write back to the live document, or only suggest text?~~ —
      **Resolved:** it writes the accepted redraft into the living working document
      as a tracked change (AI proposes, human commits).
- [x] ~~Should every copilot answer be forced to cite a clause?~~ — **Resolved:**
      yes; the verbatim-citation guardrail applies to every ask, redraft, and grill
      response, and an answer with no supporting clause must say so rather than
      invent one.
- [x] ~~Is the copilot scoped to one document or the whole cluster?~~ —
      **Resolved:** it is doc-aware — grounded in the currently open draft's cluster
      and writing back only to that open draft — while still able to cite clauses
      from other policies in the same cluster.
- [ ] Should the copilot allow the drafter to lightly edit a proposed redraft before
      applying it, or only accept it as-is? — **Deferred (non-blocking):** the demo
      applies the proposed wording as-is; inline editing before apply can follow once
      drafters give feedback, and does not change the write-back or citation rules.
