# Supervisor Submission Completeness & Compliance Check

**Ticket:** [#10](https://github.com/dzaffren/copa-hackathon/issues/10)

A supervision officer uploads a bank's application (for example, a cloud
outsourcing arrangement) and Rulebook Radar automatically assembles every
requirement that applies across all the linked policies and checks the
submission against each one, marking it Met, Missing, or Unclear with the exact
clause cited. The officer never has to remember which policies apply — the tool
does that — and can act on the result by approving the application or returning
it to the bank with an auto-drafted list of what is missing. This closes the
dangerous gap in supervision today: a required control that nobody remembered to
check for.

## User Story

As a Jabatan Penyeliaan (supervision) officer, I want to upload a bank's
application and receive a complete, cited checklist of every requirement it must
meet across all the relevant policies — with the missing items flagged — so that
I can decide whether to approve or return the application without risking a
missed requirement.

## Background & Context

**Current state:**

- When a bank submits a cloud or outsourcing application, per the Outsourcing
  policy clause 12.6 it comes to Jabatan Penyeliaan for assessment.
- The officer must remember and assemble every relevant requirement scattered
  across multiple policies (for example the technology-risk policy and the
  outsourcing policy), then read the submission and check it against each one by
  hand.
- Which policies apply, and which clauses within them, lives in the officer's
  own experience — there is no shared map that assembles the full requirement
  set for a given kind of arrangement.

**Problem:**

- The dangerous failure in supervision is a _missed_ requirement: a required
  control the officer forgot to look for, letting a compliance gap slip through
  into an approved arrangement.
- Assembling the requirement set by memory does not scale, is hard to hand over
  to a colleague, and is impossible to reconstruct months later when someone
  asks why an application was approved or returned.
- Even when a gap is spotted, turning it into a return letter to the bank is a
  separate, manual drafting task.

## Target User & Persona

- **Who:** An officer in Jabatan Penyeliaan (the supervision department)
  assessing a bank's application, such as a cloud outsourcing arrangement for a
  critical banking system.
- **Context:** The officer receives a bank's application and must confirm it
  meets every requirement across all the policies that apply before it can be
  approved, then either approve it or return it to the bank for the missing
  items.
- **Current workaround:** The officer recalls the applicable policies from
  experience, reads each one, and manually checks the submission clause by
  clause, then hand-writes any return letter.

## Goals

- Let the officer start from a single upload of the bank's application and get a
  complete, cross-policy requirement checklist automatically — without choosing
  which policies apply.
- Mark every requirement Met, Missing, or Unclear, each line quoting its exact
  clause and stating what evidence was or was not found in the submission.
- Prevent approval while any requirement is Missing or Unclear, so a gap cannot
  be signed off by accident.
- Let the officer act: return the application to the bank with an auto-drafted,
  fully-cited list of the missing items, or approve it once everything is met.
- Make the "why is this required?" reasoning available on demand so the officer
  can trust and defend each line without being shown the underlying map by
  default.

## Non-Goals

- The graph visualisation itself. The officer consumes the graph's output as a
  checklist and only sees the reasoning trace on demand; operating the graph
  directly belongs to the drafter workspace story.
- Building or maintaining the rulebook knowledge graph and the classification of
  arrangements. That is owned by the knowledge-graph engine story; this story
  consumes it.
- Real-world access control and data governance for the uploaded bank
  submission. The submission is sensitive supervised-entity data; for the
  hackathon demo it is sample data, and the production governance design is
  deferred.

## User Workflow

1. **Open the supervision workspace** — The officer opens Rulebook Radar's
   supervision view and sees an upload area inviting them to submit the bank's
   application.
2. **Upload the application** — The officer uploads the bank's application
   document (a PDF or Word file). The tool shows an analyse sequence: reading and
   extracting the submission, classifying the arrangement, matching it against
   the rulebook, assembling the applicable requirement set, and checking each
   requirement.
3. **Read the checklist** — The tool reveals a summary of the classified
   submission, a score of the form "requirements met out of total", and a
   checklist of every applicable requirement. Each line shows its status (Met,
   Missing, or Unclear), the exact clause it is based on, and a plain-language
   note.
4. **Drill into a line** — For any line the officer can open "Why is this
   required?" to see the reasoning that put the requirement on the checklist, and
   "Show evidence" to see where in the submission the tool looked or confirmation
   that the item is genuinely absent.
5. **Decide** — While any requirement is Missing or Unclear, the Approve action
   is unavailable. The officer clicks "Return to bank — request missing items",
   which drafts a return letter auto-populated from the gaps, each item citing
   its clause, then sends it. When a clean resubmission meets every requirement,
   the Approve action becomes available and the officer approves the application.

## Acceptance Criteria

> Scenarios are written from the supervision officer's perspective. The primary
> worked example is Meridian Bank Berhad's public cloud application for core
> banking, which scores 4 of 7 requirements met.

### Scenario: Uploading a submission triggers the analyse sequence

```gherkin
Given I am a supervision officer in the supervision workspace
  And I see an area to upload a bank's application
When I upload Meridian Bank Berhad's cloud outsourcing application
Then I see an analyse sequence progress through, in order:
  | step                                                            |
  | Reading the submission and extracting key facts                 |
  | Classifying the arrangement                                     |
  | Matching against the rulebook                                   |
  | Assembling the applicable requirement set                       |
  | Checking each requirement against the submission                |
  And when the sequence completes I see the compliance checklist
```

### Scenario: The arrangement is classified and the requirement set is assembled across multiple policies automatically

```gherkin
Given I have uploaded Meridian Bank Berhad's application for public cloud core banking
When the analysis completes
Then I see the submission classified as "public cloud, critical system, material outsourcing"
  And I see a note that both the technology-risk policy and the outsourcing policy apply
  And I did not have to choose which policies apply
  And the checklist contains requirements drawn from more than one policy, including:
    | clause             |
    | Outsourcing 12.1   |
    | Outsourcing 12.3(e)|
    | Outsourcing 11.2   |
    | RMiT 17.1          |
```

### Scenario: The score reflects how many requirements are met

```gherkin
Given the checklist for Meridian Bank Berhad's application has been assembled
  And it contains 7 requirements
  And 4 of them are Met
When I view the submission summary
Then I see a score of "4 / 7 requirements met"
```

### Scenario: A Met line cites its clause and shows where the evidence was found

```gherkin
Given the checklist for Meridian Bank Berhad's application is displayed
When I look at the requirement for Outsourcing 12.3(e)
Then it is marked "Met"
  And it cites clause Outsourcing 12.3(e)
  And it states that the cloud deployment model, data nature, and storage and back-up locations were disclosed
When I open "Show evidence" on that requirement
Then I see where in the submission the tool looked, including:
  | detail                                            |
  | deployment model recorded as public cloud         |
  | primary region Singapore, back-up Kuala Lumpur    |
  | data described as customer and transaction records|
```

### Scenario: A Missing line reports that nothing was found

```gherkin
Given the checklist for Meridian Bank Berhad's application is displayed
When I look at the requirement for RMiT 17.1(b)
Then it is marked "Missing"
  And it cites clause RMiT 17.1(b)
  And it states that a senior-management, board, and information-security readiness confirmation was required but not found
When I open "Show evidence" on that requirement
Then I see confirmation that the tool searched the submission for the readiness confirmation and none was present
```

### Scenario: A Missing line explains a requirement that is mandatory because of the submission's own contents

```gherkin
Given the checklist for Meridian Bank Berhad's application is displayed
When I look at the requirement for RMiT 17.1(c)
Then it is marked "Missing"
  And it cites clause RMiT 17.1(c)
  And it states that an independent third-party pre-implementation review was not attached
  And it explains this is mandatory because the submission confirms customer data is processed
```

### Scenario: An Unclear line reports partial evidence

```gherkin
Given the checklist for Meridian Bank Berhad's application is displayed
When I look at the requirement for the comprehensive cloud risk assessment under RMiT 17.1(a), 10.50 and Appendix 10
Then it is marked "Unclear"
  And it cites clauses RMiT 17.1(a), 10.50 and Appendix 10
  And it states that a risk assessment was attached but does not map to the Appendix 10 control set
When I open "Show evidence" on that requirement
Then I see that the attached risk assessment was found but 6 of 14 control areas are not evidenced against Appendix 10
```

### Scenario Outline: Each checklist line shows its status, cited clause, and note

```gherkin
Given the checklist for Meridian Bank Berhad's application is displayed
When I look at the requirement cited to <clause>
Then it is marked "<status>"
  And it cites clause <clause>
  And it shows a plain-language note describing what was checked

Examples:
  | clause                                | status  |
  | Outsourcing 12.1                      | Met     |
  | Outsourcing 12.3(e)                   | Met     |
  | RMiT 17.1                             | Met     |
  | Outsourcing 11.2                      | Met     |
  | RMiT 17.1(a), 10.50 and Appendix 10   | Unclear |
  | RMiT 17.1(b)                          | Missing |
  | RMiT 17.1(c)                          | Missing |
```

### Scenario: "Why is this required?" reveals the reasoning behind a requirement on demand

```gherkin
Given the checklist for Meridian Bank Berhad's application is displayed
  And the checklist does not show the rulebook map by default
When I open "Why is this required?" on the requirement for Outsourcing 12.1
Then I see an explanation that the requirement is on the checklist because the arrangement is a material outsourcing, which brings the outsourcing policy into scope
  And the explanation is available only when I choose to open it
```

### Scenario: Approval is blocked while any requirement is Missing or Unclear

```gherkin
Given the checklist for Meridian Bank Berhad's application shows 2 Missing and 1 Unclear requirement
When I view the decision options
Then the Approve action is unavailable
  And I see a message that approval is blocked until the outstanding requirements are resolved
```

### Scenario: Returning to the bank generates a cited gap letter

```gherkin
Given the checklist for Meridian Bank Berhad's application has outstanding requirements
When I click "Return to bank — request missing items"
Then a draft return letter is generated addressed to Meridian Bank Berhad
  And the letter lists every requirement that is not met, each citing its clause, including:
    | item                                                                              | clause                              |
    | comprehensive cloud risk assessment mapped to the Appendix 10 control set         | RMiT 17.1(a), 10.50 and Appendix 10 |
    | senior-management, board and information-security readiness confirmation          | RMiT 17.1(b)                        |
    | independent third-party pre-implementation review                                 | RMiT 17.1(c)                        |
  And the letter states that the application cannot be approved in its current form
```

### Scenario: Sending the return letter updates the application status and notifies the requester

```gherkin
Given a draft return letter for Meridian Bank Berhad's application has been generated
When I click "Send to bank"
Then I see confirmation that the letter has been sent
  And the application is marked "Returned — awaiting bank"
  And the requester is notified
  And the send action is no longer available for this letter
```

### Scenario: A clean resubmission meets every requirement and approval becomes available

```gherkin
Given Meridian Bank Berhad submits a revised application that includes:
  | added evidence                                                                    | clause                              |
  | a cloud risk assessment mapped to the Appendix 10 control set                     | RMiT 17.1(a), 10.50 and Appendix 10 |
  | a signed senior-management and board readiness confirmation                       | RMiT 17.1(b)                        |
  | an independent third-party pre-implementation review report                       | RMiT 17.1(c)                        |
When I upload the revised application and the analysis completes
Then every requirement on the checklist is marked "Met"
  And I see a score of "7 / 7 requirements met"
  And the Approve action is available
When I approve the application
Then the application is recorded as approved
```

### Scenario: The tool never asserts a requirement without citing a clause

```gherkin
Given a checklist has been assembled for any uploaded submission
When I read any line on the checklist
Then it quotes the exact clause it is based on
  And for a Missing or Unclear line it states what evidence was or was not found
  And no line asserts a requirement or a finding without a supporting clause
```

## Business Rules & Constraints

- **Full requirement set, always listed.** The checklist must list every
  applicable requirement across all the policies in scope, not only the ones the
  officer might recall. A missed requirement (a false negative) is the dangerous
  failure in supervision, so completeness of the list takes priority.
- **Verbatim-citation guardrail.** Every checklist line must quote the exact
  clause it is based on, with its clause number. A Missing or Unclear line must
  state what evidence was searched for and was or was not found, rather than
  assert an unsupported conclusion.
- **Three statuses only.** Each requirement is Met, Missing, or Unclear.
  "Unclear" is used when partial evidence exists but full coverage cannot be
  confirmed — for example, a risk assessment is attached but does not map to the
  required control set (6 of 14 control areas unevidenced).
- **Conditional requirements.** A requirement may be mandatory because of the
  submission's own contents. For example, an independent third-party
  pre-implementation review (RMiT 17.1(c)) is mandatory here because the
  submission confirms customer data is processed.
- **Approval gate.** The Approve action is unavailable while any requirement is
  Missing or Unclear. It becomes available only when every requirement is Met.
- **AI proposes, human commits.** The tool assembles the checklist and flags the
  gaps; the officer makes the approve or return decision. The tool never approves
  or returns an application on its own.
- **Return letter is auto-populated and cited.** The return letter lists every
  outstanding requirement, each citing its clause, and is drafted by the tool for
  the officer to send. Sending it marks the application "Returned — awaiting
  bank" and notifies the requester.
- **Sensitive data.** The uploaded bank submission is sensitive
  supervised-entity data and carries heavier governance than the public policy
  documents. For the demo the submission is sample data.

## Success Metrics

- **Recall (fewer missed requirements):** on a labelled set of applications with
  known applicable requirements, the tool surfaces a higher proportion of the
  real requirements than an unaided officer finds in the same time, with special
  attention to requirements the officer would otherwise miss.
- **Time efficiency:** an officer completes one submission-completeness check at
  least 15% faster with Rulebook Radar than without it, measured before and after
  on the same task.
- **Zero unsupported claims:** 100% of checklist lines quote an existing clause
  verbatim; any citation that cannot be verified against the source policy is
  treated as a defect.
- **Loop completion:** the officer can complete the full loop end to end in the
  demo — upload, checklist, and either return-to-bank or approve on a clean
  resubmission.

## Dependencies

- **Knowledge-graph engine:** provides the assembled requirement set for a
  classified arrangement and the clause citations. This story consumes it.
- **Sample bank submission:** the Meridian Bank Berhad public cloud application
  (sample data) scoring 4 of 7, plus a clean resubmission that meets all 7 so the
  approve path can be demonstrated.
- **Classification of the arrangement:** the ability to classify an uploaded
  submission (for example, public cloud, critical system, material outsourcing)
  so the correct requirement set is assembled.
- **Notification channel to the requester:** so that sending a return letter can
  notify the requester and mark the application as returned.

## Open Questions

- [x] ~~Should approval be allowed while requirements are Unclear?~~ —
      **Resolved:** No. Approval is blocked while any requirement is Missing _or_
      Unclear; only an all-Met checklist enables Approve. An Unclear requirement is
      treated as unresolved.
- [x] ~~How is the approved end-state demonstrated when the sample submission has
      gaps?~~ — **Resolved:** A second, clean resubmission that meets every
      requirement is provided so the approve path is visible in the demo.
- [ ] What governance applies to the uploaded bank submission in a real
      deployment? — **Deferred (non-blocking):** the demo uses sample data; the
      production access-control and data-governance design is a post-hackathon
      concern and must be named explicitly in the pitch.
- [ ] Can an officer override an Unclear line to Met after manual verification
      (with a recorded reason)? — **Deferred (non-blocking):** the demo relies on the
      bank resubmitting evidence; a manual-override-with-audit path can be added
      later without changing the core flow.
