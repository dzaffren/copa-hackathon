# Reviewer & Approval Workflow

**Ticket:** TBD

After a policy drafter submits a consistency-checked draft, this feature lets the
assigned reviewer read the draft, leave clause-anchored comments (but never change
the text), and complete their review to route it back to the drafter for revision.
Approval is kept as a separate manager action that a plain reviewer cannot perform.
This closes the drafter's loop — the previously dead-end submission now returns to
the drafter with real feedback, and separation of duties is enforced so no one
approves work they were only asked to review.

## User Story

As a **reviewer** assigned to a policy draft, I want to read the draft, comment on
specific clauses, and send my review back to the drafter, so that the drafter gets
clear, clause-grounded feedback and knows the document is ready for revision.

As a **manager (approver)**, I want the sole ability to approve a reviewed draft,
so that no draft advances without a separation-of-duties sign-off distinct from the
reviewing step.

## Background & Context

**Current state:**

- When a drafter finishes reconciling findings, the impact report offers "Submit
  draft to reviewer / manager." The drafter's assigned reviewer and approving
  manager are notified that a draft is waiting.
- The reviewer can open the submitted draft in the workspace and see it marked as
  assigned to them for review, alongside the rest of the technology-risk cluster.

**Problem:**

- Submitting a draft was previously a dead-end: there was no way for the reviewer
  to feed comments back, so the drafter never received actionable feedback inside
  the tool and the loop had to be closed by email or memory.
- Nothing enforced separation of duties, so there was a risk of a reviewer (or the
  original drafter) approving a document they should only have been reading, which
  undermines the trust the rulebook depends on.

## Target User & Persona

- **Who (primary):** an experienced policy staff member assigned as the reviewer of
  a specific draft — for example, Farid M. reviewing Aisyah R.'s RMiT v2 draft.
- **Who (secondary):** a policy manager with approver authority who gives the
  separate sign-off.
- **Context:** the reviewer opens Rulebook Radar after being notified that a draft
  was submitted to them. They already see the whole cluster; the submitted draft
  now carries a "for your review" role for them.
- **Current workaround:** reviewers today read the draft outside the tool and send
  comments by email or in a separate document, with no shared record tying a
  comment to the exact clause or to the AI finding that prompted it.

## Goals

- Let the assigned reviewer read a submitted draft and comment on it without ever
  being able to alter the policy text.
- Let every reviewer comment reference the exact clause it is about and any related
  policy clause, with the same verbatim citation used everywhere in the tool.
- Let the reviewer complete their review in one action that routes their comments
  back to the drafter and moves the document to "in revision," notifying the drafter.
- Enforce that approval is a separate manager action, unavailable to a plain
  reviewer and never available to the person who drafted the document.

## Non-Goals

- Editing or redrafting the policy text — that belongs to the drafter workspace and
  drafting copilot stories.
- Re-running the consistency ripple check — that belongs to the impact report story.
- The drafter's act of submitting the draft — that is the closing step of the
  impact report story; this story begins once the draft has been submitted.
- The supervisor's approve/return decision on a bank submission — that is a
  different persona and a separate story.

## User Workflow

1. **Open a submitted draft** — Farid is notified that Aisyah submitted RMiT v2 for
   his review. In the workspace he sees the RMiT v2 node marked "for your review."
   He opens it and sees the draft alongside the clauses Rulebook Radar flagged,
   each quoting its exact source clause.
2. **Read, not edit** — Farid reads the draft. The policy text is read-only for him;
   there is no way to change a word. A clear note tells him he is reviewing, not
   editing, and that approval is a manager action.
3. **Comment on a clause** — Farid leaves a comment on RMiT clause 17.1, and his
   comment references clause 17.1 and the related Outsourcing clause 12.1 that the
   tool flagged, quoting both verbatim.
4. **Complete the review** — Farid clicks "Complete review — send comments to
   drafter." The document moves to "in revision," his comments are routed to Aisyah,
   and Aisyah is notified that her draft has been returned with feedback.
5. **Approval stays with a manager** — Farid sees the Approve action is not available
   to him. Later, the approving manager opens the same draft and performs the
   separate approval; the manager cannot approve a draft they themselves drafted.

## Acceptance Criteria

### Scenario: Assigned reviewer opens a submitted draft

```gherkin
Given Aisyah R. has submitted her RMiT v2 draft for review
  And I am Farid M., the reviewer assigned to that draft
When I open the RMiT v2 draft from my workspace
Then I see the draft marked "for your review"
  And I see it is drafted by Aisyah R. with me as the assigned reviewer
  And I see the clauses Rulebook Radar flagged, each quoting the exact clause it is based on
```

### Scenario: Reviewer cannot edit the policy text

```gherkin
Given I am Farid M. reviewing Aisyah's RMiT v2 draft
When I view the draft text of clause 17.1
Then the policy text is read-only to me
  And I have no way to change, add, or delete any of the draft's wording
  And I see a note that I am reviewing, not editing, and that changing the text is the drafter's job
```

### Scenario: Reviewer adds a clause-grounded comment

```gherkin
Given I am Farid M. reviewing Aisyah's RMiT v2 draft
  And Rulebook Radar has flagged RMiT clause 17.1 against Outsourcing clause 12.1
When I add the comment "Agree with the flag — 17.1's 14-day notification should be reconciled with Outsourcing 12.1's prior written approval before this goes forward" on clause 17.1
Then my comment is saved against clause 17.1
  And my comment references clause 17.1 and the related Outsourcing clause 12.1
  And both referenced clauses are shown quoted verbatim with their clause numbers
  And my comment is shown attributed to me as the reviewer
```

### Scenario: A reviewer comment that references a clause with no matching related clause

```gherkin
Given I am Farid M. reviewing Aisyah's RMiT v2 draft
  And Rulebook Radar reports a Gap because the pre-adoption risk assessment control was dropped
When I add a comment on that gap noting the missing control
Then my comment is saved against the gap finding
  And where no related clause exists to cite, the tool states "No matching clause found" rather than inventing one
```

### Scenario: Reviewer completes the review and routes it back to the drafter

```gherkin
Given I am Farid M. reviewing Aisyah's RMiT v2 draft
  And I have left at least one comment
When I choose "Complete review — send comments to drafter"
Then the document state changes from "submitted for review" to "in revision"
  And my comments are routed to the drafter, Aisyah R.
  And Aisyah R. is notified that her RMiT v2 draft has been returned for revision
  And I see confirmation that my review was completed and sent to the drafter
```

### Scenario: Drafter receives the returned draft and comments

```gherkin
Given Farid M. has completed his review of Aisyah's RMiT v2 draft
When I am Aisyah R. and I open my workspace
Then I see my RMiT v2 draft marked "in revision"
  And I see Farid M.'s comments attached to the clauses he commented on
  And each comment shows the clause it refers to quoted verbatim
```

### Scenario: A plain reviewer cannot approve

```gherkin
Given I am Farid M., a reviewer with no approver authority
  And I am reviewing Aisyah's RMiT v2 draft
When I look for a way to approve the draft
Then the Approve action is not available to me
  And I see that approval is a separate manager action
```

### Scenario: A manager performs the separate approval

```gherkin
Given Farid M. has completed his review of Aisyah's RMiT v2 draft
  And I am a manager with approver authority who did not draft this document
When I open the RMiT v2 draft
Then the Approve action is available to me
  And when I approve it the draft is recorded as approved with me as the approver
```

### Scenario: A manager cannot approve their own drafted document (separation of duties)

```gherkin
Given I am a manager with approver authority
  And I am the drafter of the RMiT v2 draft
When I open the RMiT v2 draft
Then the Approve action is not available to me for this draft
  And I see that I cannot approve a document I drafted
```

### Scenario Outline: What each role can do on a draft assigned to them

```gherkin
Given I am opening a draft in the workspace
  And my role on that draft is <role>
When I view the draft
Then editing the policy text is <can_edit>
  And commenting on clauses is <can_comment>
  And the Approve action is <can_approve>

Examples:
  | role                          | can_edit       | can_comment    | can_approve      |
  | assigned drafter              | available      | available      | not available    |
  | assigned reviewer             | not available  | available      | not available    |
  | manager (approver, not drafter) | not available | available      | available        |
```

## Business Rules & Constraints

- **Reviewer is comment-only.** An assigned reviewer can read the draft and comment
  on clauses but can never change, add, or delete the policy text. Editing is the
  assigned drafter's right alone.
- **Approval is a separate manager action.** A plain reviewer never sees an active
  Approve action; only a manager with approver authority can approve a reviewed draft.
- **Separation of duties on approval.** A user cannot approve a document they drafted,
  even if they hold approver authority — reviewing and drafting are always separate
  from approving that same draft.
- **Completing a review routes state and notifications.** Completing a review moves
  the document from "submitted for review" to "in revision," delivers the reviewer's
  comments to the drafter, and notifies the drafter. The reviewer completes their
  loop; they do not decide the draft's fate.
- **Grounded comments (verbatim-citation guardrail).** Every reviewer comment that
  references a clause quotes that clause and any related clause verbatim, with clause
  numbers. Where no supporting clause exists, the tool states "No matching clause
  found" rather than asserting an unsupported claim.
- **Workspace scope.** The reviewer sees the whole technology-risk cluster for
  context but can only comment on the document assigned to them for review; other
  in-progress drafts remain read-only to them.
- **AI proposes, human commits.** Every action in this workflow — commenting,
  completing the review, approving — is a human decision. The tool only routes the
  document state and the notifications.

## Success Metrics

- **Loop closed:** in the demo, a reviewer can complete a review and the drafter
  receives the returned draft with comments, with no step handled outside the tool.
- **Separation of duties holds:** in every attempt, a plain reviewer and a drafter
  are prevented from approving, and only a non-drafting manager can approve.
- **Grounded feedback:** 100% of reviewer comments that reference a clause show that
  clause quoted verbatim, or state "No matching clause found" when none applies.

## Dependencies

- **Drafter rulebook workspace** — supplies the role-per-document model ("for your
  review" role) and the cluster the reviewer sees.
- **Consistency ripple check & impact report** — supplies the "Submit draft to
  reviewer / manager" step that puts a draft into the "submitted for review" state
  and notifies the reviewer and manager; this story begins from that state.
- **Confirmed reviewer and approver assignments** — each draft must have an assigned
  reviewer and a designated approving manager for the routing and separation-of-duties
  rules to work (for the demo: Aisyah R. drafts RMiT v2, Farid M. reviews, a manager
  approves).

## Open Questions

- [x] ~~Should the reviewer be able to edit the policy text?~~ — **Resolved:** no.
      Reviewers comment only; editing is the assigned drafter's right. This is a hard
      role-based-access rule from the epic.
- [x] ~~Can a reviewer also approve?~~ — **Resolved:** no. Approval is a separate
      manager action and is unavailable to a plain reviewer, and no one may approve a
      document they drafted.
- [ ] **Should completing a review require at least one comment, or can a reviewer
      complete with no comments (a clean pass back)?** — **Deferred (non-blocking):**
      the demo shows a review with comments; whether an empty-comment completion is
      allowed can be decided without changing the routing behaviour.
