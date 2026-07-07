# Drafter Rulebook Workspace

**Ticket:** [#7](https://github.com/dzaffren/copa-hackathon/issues/7)

The drafter's home in Rulebook Radar: a single workspace that shows the whole
technology-risk policy cluster as an interactive map, where what a drafter can
_do_ with each policy depends on their role for that policy. From this one screen
a drafter sees every policy she edits, reviews, or can only read, understands
_why_ any two policies are connected, sees _why_ a policy version changed, and
can hand off to the supervisor view. It gives a policy drafter the at-a-glance
picture of the rulebook that today lives only in experienced staff's heads.

## User Story

As a policy drafter, I want to open one workspace that shows the whole policy
cluster and marks what I can edit, review, or only read — and explains why the
policies connect and why they changed — so that I can see how my work fits the
rest of the rulebook and act on the policies that are mine without hunting
through separate documents.

## Background & Context

**Current state:**

- The connections between Bank Negara Malaysia's policies — which rules overlap,
  depend on, or reference each other — live in the heads of experienced policy
  staff, not in any shared map.
- A drafter opens one policy document at a time. To understand how a revision
  relates to the rest of the rulebook, she must recall which other policies
  might be affected and open each separately.
- Why a clause changed, and which discussion papers or committee decisions drove
  the change, is hard to reconstruct months later.

**Problem:**

- Working document-by-document hides the cross-policy relationships that are the
  whole point of keeping the rulebook consistent. Acting on a ripple between two
  policies requires seeing more than one at once.
- Nothing tells a drafter, at a glance, which policies are hers to edit, which
  are hers to review, and which she may only read — so effort and access are
  ambiguous.
- The reasoning behind a change and the connection between two policies is
  undocumented, so knowledge is lost and consistency checks stay slow and
  memory-dependent.

## Target User & Persona

- **Who:** Aisyah R., a Bank Negara Malaysia policy drafter working in the
  technology-risk area.
- **Context:** She is assigned to revise two policies (Risk Management in
  Technology and Operational Resilience) and to review a third (Outsourcing).
  She opens the workspace whenever she starts or resumes work on the cluster.
- **Current workaround:** She keeps a mental list of related policies, opens each
  document separately, and relies on memory and colleagues to know what connects
  to what and who owns which document.

## Goals

- Give the drafter one workspace that always shows the whole cluster, never a
  single isolated document.
- Make each policy's role for _this_ drafter (edit / review / locked / read-only)
  immediately visible and enforce what she can do accordingly.
- Explain, on demand, _why_ any two policies are connected and _why_ a specific
  policy version changed — with real supporting documents, and with sensitive
  supporting documents visible as a trail but withheld in content.
- Make clear that reaching another cluster is a preview of a future capability,
  never implying analysis the tool cannot yet do.
- Provide a clean hand-off to the supervisor view from the same screen.

## Non-Goals

- **Running the ripple / consistency check.** Detecting conflicts, duplications,
  and gaps from a change belongs to the consistency ripple story, not this one.
- **Editing or redrafting policy text.** Opening a policy to edit or comment, and
  the copilot redraft, are covered by their own stories; this workspace only
  routes the drafter to the right action per policy.
- **Cross-cluster analysis.** Only a single labelled preview of a cross-cluster
  ripple is shown; full cross-cluster mapping is a future phase.
- **Approval decisions.** Approving a draft is a separate manager action and is
  not part of this workspace.

## User Workflow

1. **Open the workspace** — Aisyah opens Rulebook Radar and lands on her
   workspace. She sees the whole technology-risk cluster laid out as a connected
   map, a strip naming her and summarising her work ("2 to edit", "1 to review"),
   and a legend explaining what each policy's marking means.
2. **Scan her role across the cluster** — Without opening anything, she can tell
   which policies are marked editable by her, which are for her review, which are
   another team's in-progress work she cannot open, which are in force, which are
   superseded history, and which sit in another cluster.
3. **Inspect a policy** — She selects a policy and a detail panel shows its
   status, version, a short note, the list of policies it is linked to, and one
   clearly-labelled action appropriate to her role for that policy.
4. **Understand a connection** — She selects the link between two policies and the
   panel explains, in plain language and referencing the real clauses, why those
   two policies correlate.
5. **Understand a change** — On a policy she is revising, the panel shows a "Why
   this changed" trail: public supporting documents with their real titles and
   dates, and internal supporting documents shown as locked, content-withheld
   entries.
6. **Act or hand off** — She follows the action button to work on a policy that is
   hers, or uses "Switch to supervisor view" to move to the supervisor
   experience.

## Acceptance Criteria

> Scenarios are written from Aisyah's point of view. Visual treatments (rings,
> dashes) are described as observable labels; their exact styling lives in the
> UI/Frontend Requirements section.

### Background

```gherkin
Given I am Aisyah R., a policy drafter, signed in to Rulebook Radar
  And my workspace covers the technology-risk cluster with these policies
    | policy                            | version         | my role for it       | derived status         |
    | Risk Management in Technology     | v2 · 2026 draft | assigned — I edit    | in progress            |
    | Operational Resilience            | v2 · 2026 draft | assigned — I edit    | in progress            |
    | Outsourcing                       | v2 · 2026 draft | assigned — I review  | in progress            |
    | Management of Customer Information| v2 · 2026 draft | none — another team  | in progress (locked)   |
    | Business Continuity Management    | v1 · 2022       | none                 | in force               |
    | Recovery Planning                 | v1 · 2021       | none                 | in force               |
    | Risk Management in Technology     | v1 · 2020       | none                 | superseded             |
    | AML / CFT                         | in force        | none — other cluster | cross-cluster preview  |
```

### Scenario: Opening the workspace shows the whole cluster, not one document

```gherkin
Given I open Rulebook Radar
When my workspace loads
Then I see all seven policies of the technology-risk cluster on one map
  And I see a workspace strip naming me as "Aisyah R." with the role "policy drafter"
  And the strip shows "2 to edit" and "1 to review"
  And I never see the workspace scoped to a single policy
```

### Scenario: Each policy is marked with my role and status at a glance

```gherkin
Given my workspace has loaded
When I scan the map without opening anything
Then each policy is marked so I can tell my role and its status without clicking
  And a legend explains what each marking means
```

### Scenario Outline: The markings match my role and each policy's derived status

```gherkin
Given my workspace has loaded
When I look at <policy>
Then it is marked as "<marking>"

Examples:
  | policy                          | marking                          |
  | Risk Management in Technology v2| assigned — you edit              |
  | Operational Resilience v2       | assigned — you edit              |
  | Outsourcing v2                  | for your review — you comment    |
  | Management of Customer Information v2 | in progress · others (locked)  |
  | Business Continuity Management  | in force (read-only)             |
  | Risk Management in Technology v1| superseded (read-only history)   |
  | AML / CFT                       | other cluster (preview only)     |
```

### Scenario: Opening a policy I am assigned to edit

```gherkin
Given my workspace has loaded
When I select the Risk Management in Technology v2 draft
Then the detail panel shows its status "in progress", version "v2 · 2026 draft", and a short note
  And it lists the policies it is linked to, including Operational Resilience, Outsourcing, Business Continuity, and Management of Customer Information
  And I see a single action labelled "Review & edit"
```

### Scenario: Opening a policy I am assigned to review

```gherkin
Given my workspace has loaded
When I select the Outsourcing v2 draft
Then the detail panel shows a note saying it was drafted by Farid M. and that I am the assigned reviewer who can read and comment
  And the note states that approval is a separate manager action
  And I see a single action labelled "Open for review"
  And I am not offered any action that edits the policy text
```

### Scenario: A locked in-progress draft I have no role on cannot be opened

```gherkin
Given my workspace has loaded
When I select the Management of Customer Information v2 draft
Then the detail panel shows that it is another team's draft and read-only for me
  And the only action shown is labelled "Locked" and cannot be selected
```

### Scenario Outline: Read-only corpus policies offer no editing action

```gherkin
Given my workspace has loaded
When I select <policy>
Then the detail panel shows it as read-only
  And the only action shown is labelled "Read-only" and cannot be selected

Examples:
  | policy                              |
  | Business Continuity Management v1   |
  | Recovery Planning v1                |
  | Risk Management in Technology v1    |
```

### Scenario: Clicking a link explains why two policies are connected

```gherkin
Given my workspace has loaded
When I select the link between Risk Management in Technology and Outsourcing
Then the panel shows a "Why these are connected" explanation
  And the explanation states that a public-cloud arrangement is often also a material outsourcing
  And it references that RMiT clause 17 interacts with Outsourcing clause 12.1 as the core conflict in this cluster
```

### Scenario: A different link shows a different, real connection

```gherkin
Given my workspace has loaded
When I select the link between Risk Management in Technology and Operational Resilience
Then the panel shows a "Why these are connected" explanation about both policies governing the register of critical cloud and third-party services
  And it references RMiT clause 10 overlapping Operational Resilience clause 6.11
```

### Scenario: Viewing why a policy version changed, with a public supporting document shown

```gherkin
Given my workspace has loaded
When I select the Risk Management in Technology v2 draft
Then the detail panel includes a "Why this changed" trail
  And it lists the public supporting document "Operational Resilience — Discussion Paper" dated 19 Dec 2025 with its title shown
  And it lists the public supporting document "RMiT FAQs (updated)" dated 1 Jul 2026 with its title shown
  And each public supporting document is marked as public
```

### Scenario: An internal supporting document appears as a locked, content-withheld entry

```gherkin
Given I have selected the Risk Management in Technology v2 draft
  And its "Why this changed" trail is shown
When I look at the internal supporting document "JPP Committee minutes — cloud policy review"
Then it is listed so the trail is visible
  And it is marked as restricted and access-controlled
  And its content is not shown to me
```

### Scenario: Provenance appears in the detail panel, not as extra policies on the map

```gherkin
Given my workspace has loaded
When I look at the map of the cluster
Then supporting documents such as the discussion paper and the committee minutes do not appear as their own policies on the map
  And they only appear inside the "Why this changed" trail when I select a policy
```

### Scenario: The cross-cluster policy is a preview and cannot be opened

```gherkin
Given my workspace has loaded
When I select the AML / CFT policy
Then the detail panel states it is outside the technology-risk cluster
  And it explains that a change in RMiT touched it, so it surfaces as a preview
  And it states that full cross-cluster mapping is a future phase
  And the only action shown is labelled "Outside your cluster · preview only" and cannot be selected
```

### Scenario: Switching to the supervisor view

```gherkin
Given my workspace has loaded
When I select "Switch to supervisor view"
Then I am taken to the supervisor experience
```

### Scenario: Selecting a policy after viewing a connection returns to policy detail

```gherkin
Given I have selected the link between Risk Management in Technology and Outsourcing
  And the "Why these are connected" explanation is shown
When I then select the Operational Resilience v2 draft
Then the panel switches to show the Operational Resilience detail with its status, version, note, linked-to list, and action
  And the connection explanation is no longer shown
```

## Business Rules & Constraints

- **A session is a workspace, never one document.** The drafter always sees the
  whole technology-risk cluster plus the policies relevant to her; the workspace
  is never scoped to a single policy.
- **Role-based access per policy.** For each policy the drafter can only act
  according to her role: edit (assigned drafter), comment-only (assigned
  reviewer), locked (another team's in-progress draft), or read-only (in-force
  and superseded corpus documents). Approval is a separate manager action and is
  never offered here.
- **Status is derived, not entered.** A policy is "in progress" exactly when a
  live working draft exists for it; "in force" and "superseded" come from the
  published corpus. The workspace shows the derived status; nobody sets it by
  hand.
- **Real, verifiable connection and change explanations.** A connection
  explanation references the actual clauses that correlate (for example RMiT
  clause 17 and Outsourcing clause 12.1). A "Why this changed" trail lists real
  supporting documents (for example the Operational Resilience Discussion Paper
  dated 19 Dec 2025 and the RMiT FAQs updated 1 Jul 2026). Nothing asserts a
  clause or document that does not exist.
- **Confidentiality-aware provenance.** Public supporting documents are shown
  with real titles and dates. Internal supporting documents (for example JPP
  Committee minutes) are shown as locked, access-controlled entries: the trail is
  visible, the content is not.
- **Provenance lives in the detail panel.** Supporting documents are never added
  as their own policies on the map; they appear only inside the "Why this
  changed" trail.
- **Cross-cluster is preview-only.** Exactly one policy from another cluster
  (AML / CFT) appears as a clearly-labelled preview that cannot be opened, and the
  tool never implies it can analyse across clusters in this phase.

## UI/Frontend Requirements

> Observable visual states referenced by the scenarios above. Colours and exact
> styling are indicative for the demo, not contractual.

- **Workspace strip** across the top naming the drafter and role, with running
  counts ("2 to edit", "1 to review") and a "Switch to supervisor view" control.
- **The cluster map** with a legend. Each policy carries a visible state:
  - Assigned — you edit: a green ring around the policy.
  - For your review — you comment: a teal ring around the policy.
  - In progress · others (locked): shown without an edit/review ring.
  - In force: a read-only corpus treatment.
  - Superseded: a read-only history treatment, visually distinct from in force.
  - Other cluster: greyed with a dashed outline, clearly non-actionable.
- **Links between policies are selectable** and, when selected, are visually
  emphasised while the panel shows the connection explanation.
- **Detail panel** showing, for a selected policy: status label, version, note,
  "Linked to" list, the "Why this changed" trail where applicable, and exactly
  one role-appropriate action button (Review & edit / Open for review / Locked /
  Read-only / Outside your cluster · preview only). Locked, read-only, and preview
  actions are visibly disabled.

## Success Metrics

- A drafter can, within seconds of opening the workspace and without opening any
  document, correctly identify which policies she edits, reviews, and can only
  read across the whole cluster.
- 100% of connection explanations and "Why this changed" entries reference an
  existing clause or a real supporting document; any reference that cannot be
  verified against the source is treated as a defect.
- No drafter can open, edit, or comment on a policy for which they have no role
  (locked, read-only, or cross-cluster preview), in demo testing.
- The cross-cluster preview is understood by demo observers as "not yet built,"
  never as a working cross-cluster analysis.

## Dependencies

- **Knowledge-graph engine.** The workspace displays the cluster, its links, the
  connection explanations, and the provenance trails produced by the ingestion
  and knowledge-graph engine story.
- **Locked demo cluster and corpus.** The final set of technology-risk policies
  and their published versions must be confirmed so the map, statuses, and links
  are real.
- **Role assignments for the drafter.** The drafter's per-policy roles (edit for
  RMiT v2 and Operational Resilience v2; review for Outsourcing v2) must be known
  so the workspace can mark and enforce them.
- **Real provenance anchors.** The public supporting documents (Operational
  Resilience Discussion Paper dated 19 Dec 2025; RMiT FAQs updated 1 Jul 2026)
  and the internal locked entry (JPP Committee minutes — cloud policy review)
  must be available to populate the "Why this changed" trail.
- **Supervisor experience.** The "Switch to supervisor view" control routes into
  the supervisor submission-check story.

## Open Questions

- [x] ~~Should supporting documents appear as their own nodes on the map?~~ —
      **Resolved:** No. Provenance is shown only in the detail panel's "Why this
      changed" trail, to keep the map uncluttered.
- [x] ~~Should the cross-cluster policy be openable?~~ — **Resolved:** No. It is a
      single, clearly-labelled preview that cannot be opened; full cross-cluster
      mapping is a future phase.
- [ ] **Should the workspace surface an unread/updated indicator when a linked
      policy changes since the drafter last visited?** — **Deferred
      (non-blocking):** useful for continuity but not required for the demo; the
      workspace can show current state without change-since-last-visit tracking.
