# Rulebook Radar — Overview

**Discovery Brief:** docs/discovery/policy-consistency-ai/brief.md

## Summary

Rulebook Radar is an AI tool that maps a cluster of Bank Negara Malaysia's own
policy documents as a connected knowledge graph and uses it to keep the rulebook
consistent. When a policy drafter revises a policy, it traces the ripple across
every linked policy and flags where the change creates a Conflict, a Duplication,
or a Gap — each finding quoting the exact clause it is based on. The same
knowledge graph serves a supervisor, who uploads a bank's application and receives
a cited checklist of every requirement the submission must meet across the linked
policies, flagging what is missing. The tool is built entirely on BNM's published
policy documents and demonstrated on the technology-risk cluster for the COPA
Hackathon 2026 (3 August 2026).

## Background & Context

**Current state:**

- The connections between BNM's policies — which rules overlap, depend on, or
  reference each other — live in the heads of experienced policy staff, not in
  any shared map.
- When a drafter revises one policy, checking that it stays consistent with the
  rest of the rulebook is a manual, memory-dependent task: the drafter has to
  recall which other policies might be affected and read each one.
- When a supervisor assesses a bank's application (for example, a cloud
  outsourcing arrangement), they must remember and assemble every relevant
  requirement scattered across multiple policies, then check the submission
  against each by hand.

**Problem:**

- Consistency checks are slow and error-prone. A revised clause can silently
  contradict, duplicate, or leave a gap against another policy, and the clash may
  only surface much later.
- For supervision, the dangerous failure is a _missed_ requirement — a required
  control the assessor forgot to check for, letting a compliance gap slip through.
- Both tasks depend on individual expertise that is hard to scale, hand over, or
  reconstruct months later.

This directly targets **BP2026 Must-Win 10** (AI roadmap for supervision), whose
Key Result 3 is ">15% efficiency across 10 supervisory processes from staff usage
of AI tools." It also supports **MW9** (process efficiency) and **MW6** (a
coherent, non-contradictory rulebook), and the broader SET2027 goals of a Trusted
Institution / Credible Regulator and Engaged Employees.

## Goals

- Give a drafter a live, at-a-glance map of how a policy connects to the rest of
  the rulebook, and automatically surface where a change breaks consistency.
- Ensure every AI finding and answer quotes the exact clause it relies on, so a
  human can verify it in seconds and never has to trust an unsupported claim.
- Let a supervisor upload a bank submission and get a complete, cited checklist of
  what every relevant policy requires — with the missing items flagged — without
  having to know which policies apply.
- Close both loops: let the drafter _act_ on findings (fix and resubmit) and the
  supervisor _decide_ (approve or return to the bank), not merely diagnose.
- Demonstrate a measurable efficiency gain and fewer missed issues on a real
  cluster of BNM policies by the hackathon.

## Non-Goals

- **Cross-cluster mapping.** MVP1 covers a single cluster (technology-risk). The
  graph shows one greyed, clearly-labelled "preview" node representing a ripple
  reaching another cluster, but full cross-cluster analysis is a future phase.
- **The whole rulebook.** The demo is scoped to a cluster of 5–10 related
  policies, not every BNM policy.
- **Silent AI edits.** The copilot never finalises policy text on its own; every
  change is proposed for a human to accept or reject.
- **Replacing human judgement.** The tool surfaces and cites findings; drafters,
  reviewers, managers, and supervisors make every decision.

## Story Index

Epic tracking issue: [#5](https://github.com/dzaffren/copa-hackathon/issues/5).

| Ticket                                                      | Story                                                 | Spec                                                             | Type        | Status      | Dependencies                  |
| ----------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------- | ----------- | ----------- | ----------------------------- |
| [#6](https://github.com/dzaffren/copa-hackathon/issues/6)   | Policy ingestion & rulebook knowledge-graph engine    | [spec-knowledge-graph-engine.md](spec-knowledge-graph-engine.md) | Technical   | Not Started | —                             |
| [#7](https://github.com/dzaffren/copa-hackathon/issues/7)   | Drafter rulebook workspace                            | [spec-drafter-workspace.md](spec-drafter-workspace.md)           | User-facing | Not Started | #6 Engine                     |
| [#8](https://github.com/dzaffren/copa-hackathon/issues/8)   | Consistency ripple check & impact report              | [spec-ripple-impact-report.md](spec-ripple-impact-report.md)     | User-facing | Not Started | #6 Engine; #7 Workspace       |
| [#9](https://github.com/dzaffren/copa-hackathon/issues/9)   | Drafting copilot with live write-back                 | [spec-drafting-copilot.md](spec-drafting-copilot.md)             | User-facing | Not Started | #6 Engine; #8 Ripple check    |
| [#10](https://github.com/dzaffren/copa-hackathon/issues/10) | Supervisor submission completeness & compliance check | [spec-supervisor-check.md](spec-supervisor-check.md)             | User-facing | Not Started | #6 Engine                     |
| [#11](https://github.com/dzaffren/copa-hackathon/issues/11) | Reviewer & approval workflow                          | [spec-reviewer-approval.md](spec-reviewer-approval.md)           | User-facing | Not Started | #7 Workspace; #8 Ripple check |

## Shared Business Rules

- **Verbatim-citation guardrail (hard rule).** Every finding, checklist line, and
  copilot answer must quote the exact clause text it is based on, with its clause
  number. If no supporting clause exists, the tool must say so explicitly (for
  example, "No matching clause found") rather than assert an unsupported claim.
  This is the anti-hallucination measure and applies to every story.
- **AI proposes, human commits.** The tool may suggest, redraft, classify, and
  flag, but it never finalises policy text or makes an approval/return decision on
  its own. A human always accepts, rejects, or decides.
- **The graph is the engine, not always the interface.** The drafter operates the
  graph directly; the supervisor consumes its output as a checklist and only sees
  the graph on demand ("why is this required?"). The same underlying map serves
  both.
- **Role-based access per document.** A user sees the whole cluster (read) but can
  only act according to their role for each document: edit (assigned drafter),
  comment (assigned reviewer), or read-only (locked in-progress drafts, in-force,
  and superseded documents). Approval is a separate manager action.
- **A session is a workspace, not a single document.** The user always sees the
  full cluster plus the documents relevant to them, because acting on a
  cross-policy ripple requires seeing more than one document at once.
- **Node status is derived, not invented.** A document is "In progress" exactly
  when a live working draft exists for it; "In force" and "Superseded" come from
  the published corpus.
- **Public vs. sensitive data.** The drafter experience runs entirely on published
  (public) policy documents. The supervisor experience ingests a bank's submission
  — sensitive supervised-entity data — which carries heavier access-control and
  data-governance requirements. For the hackathon demo the submission is sample
  data.

## User Journey Map

> Rulebook Radar serves two personas on one shared knowledge graph. The journey
> below shows both, connected by the graph they have in common.

**Drafter path**

1. **Open the workspace** — Aisyah, a policy drafter, opens Rulebook Radar and
   sees the whole technology-risk cluster as a graph: which policies she can edit
   (RMiT, Operational Resilience), which she reviews, and which are locked or in
   force. She clicks a link between two policies to understand _why_ they are
   connected. _(Story: Drafter rulebook workspace)_
2. **Make a change and see the ripple** — She revises RMiT clause 17 (moving
   first-time cloud adoption from prior consultation to notify-within-14-days).
   The tool traces the ripple and produces an impact report: a Conflict with the
   Outsourcing policy, a Duplication within RMiT, and a Gap where a risk-assessment
   control was dropped — each quoting the exact clause. _(Story: Consistency ripple
   check & impact report)_
3. **Fix it with the copilot** — She opens the drafting copilot, asks it to "grill
   my draft," and accepts a redraft that reconciles the conflict. The accepted text
   is written into the living document as a tracked change for her to accept, and
   the matching finding is marked resolved. _(Story: Drafting copilot with live
   write-back)_
4. **Submit for review** — When all findings are resolved, the impact report offers
   "Submit draft to reviewer / manager." She submits; her reviewer and approving
   manager are notified. _(Story: Consistency ripple check & impact report →
   Reviewer & approval workflow)_
5. **Review and approve** — Farid, the assigned reviewer, opens the draft, adds
   comments (he cannot edit the text), and completes his review, routing it back to
   the drafter. A manager gives the separate approval. _(Story: Reviewer & approval
   workflow)_

**Supervisor path (same graph, different task)**

6. **Upload a submission** — In the supervision workspace, an officer in Jabatan
   Penyeliaan uploads Meridian Bank's cloud outsourcing application. _(Story:
   Supervisor submission completeness & compliance check)_
7. **Get a cited checklist** — The tool reads the submission, classifies it (public
   cloud · critical system · material outsourcing), and — using the same graph —
   assembles every requirement that applies across RMiT and Outsourcing, marking
   each Met / Missing / Unclear with the exact clause and where in the submission it
   looked. _(Story: Supervisor submission completeness & compliance check)_
8. **Decide** — Because two requirements are missing, approval is blocked. The
   officer clicks "Return to bank," which drafts a return letter auto-populated from
   the gaps (each citing its clause), and sends it. When a clean resubmission meets
   every requirement, the approve path becomes available. _(Story: Supervisor
   submission completeness & compliance check)_

## Success Metrics

- **Time efficiency (MW10 KR3):** a drafter or supervisor completes one real
  policy-consistency review / submission-completeness check **at least 15% faster**
  with Rulebook Radar than without it, measured as before/after time-to-complete on
  the same task across a small set of tasks.
- **Fewer missed issues (completeness / recall):** on a labelled set of known
  conflicts and known requirements, the tool surfaces a **higher proportion of the
  real issues** than an unaided human reviewer finds in the same time — with special
  attention to recall for supervision (missing a required control is the dangerous
  failure).
- **Zero unsupported claims:** 100% of findings, checklist lines, and copilot
  answers quote an existing clause verbatim; any citation that cannot be verified
  against the source document is treated as a defect.
- **End-to-end loop completion:** both personas can complete their full loop in the
  demo — drafter (change → findings → fix → submit) and supervisor (upload →
  checklist → return or approve).

## Dependencies

- **Locked demo cluster (confirmed):** a 6-document technology-risk cluster — RMiT
  - Outsourcing + Business Continuity Management + Operational Resilience + Recovery
    Planning + Management of Customer Information — plus a greyed AML/CFT cross-cluster
    preview. All real published BNM documents. (No standalone "Cyber Risk" policy —
    cyber lives inside RMiT — so it is not a node.)
- **Published policy documents:** the corpus of current, published BNM policy PDFs
  for the chosen cluster (all public via bnm.gov.my).
- **Sample bank submission:** a representative cloud outsourcing application (sample
  / mock data) for the supervisor demo, plus a second "clean" version so the approve
  path can be shown.
- **Living working-document location:** an agreed place where an in-progress policy
  draft lives and can be edited with tracked changes (for the drafter write-back
  loop).
- **Confirmed pain (validation):** confirmation from drafter and supervision
  (Jabatan Penyeliaan) contacts that these tasks are real and slow today, plus a
  baseline time for the efficiency measurement.

## Rollout Strategy

- **Delivery order:** build the knowledge-graph engine first (everything depends on
  it), then the drafter workspace, then the ripple/impact report, then the copilot;
  the supervisor check can proceed in parallel once the engine exists; the reviewer/
  approval workflow closes the drafter loop last.
- **Demo scope:** one cluster, two personas, both loops closed end-to-end.
- **Roadmap slide:** the cross-cluster "preview" node doubles as the "what's next"
  story for the pitch — MVP1 proves the pattern on one cluster; expansion to the
  full rulebook and cross-cluster ripple is the next phase.

## Open Questions

> Resolve before or during implementation. Non-blocking questions may be deferred
> with rationale.

- [x] ~~Should the tool flag only conflicts, or also duplications and gaps?~~ —
      **Resolved:** flag all three (Conflict / Duplication / Gap). The POC and the
      validated experiment both cover all three; gaps are the most impressive and were
      found reliably in testing.
- [x] ~~How should the "ripple" be presented to a non-technical judge?~~ —
      **Resolved:** both — a visual graph for the drafter and judges, and a
      plain-language, cited impact report / checklist for the frontline task.
- [x] ~~Does the copilot write back to the live document, or only suggest text?~~ —
      **Resolved:** it writes the accepted redraft into the living document as a tracked
      change (AI proposes, human commits).
- [x] ~~Should the drafter be able to reach "submit" by dismissing findings, not
      only fixing them?~~ — **Resolved:** yes, a finding may be dismissed rather than
      fixed, but a dismissal must record a reason for the audit trail; a dismissed
      finding counts as resolved for the purpose of submitting.
- [ ] **How is the ">15% efficiency" baseline captured for the demo?** —
      **Status:** awaiting a measured baseline time from drafter / supervision contacts
      (discovery action item 5). ← Needed for the Impact pitch; does not block build.
- [ ] **What is the exact final cluster (which 5–10 policies)?** — **Status:**
      awaiting confirmation from contacts (discovery action item 2). ← Blocks final
      content, not the architecture.
- [ ] **What governance applies to the uploaded bank submission in a real
      deployment?** — **Deferred (non-blocking):** the demo uses sample data; real
      access-control and data-governance design is a post-hackathon concern, but must be
      named explicitly in the pitch.
