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

---

> **Technical refinement (added by `/prd-refine`; re-platformed to Next.js on 2026-07-11).**
> Everything above is the approved product content and is unchanged. This story reuses the
> **Shared Technical Spine** defined in `spec-upload-and-workspace.md` (the Next.js + React +
> Tailwind + shadcn/ui app under `web/`, the read-API/snapshot contract via `web/lib/data.ts`,
> and the Zustand store `web/lib/store.ts` accessed through a `useStore` hook); that spine is
> not repeated here. This is a **display + hand-off** surface: it renders a prepared drift
> queue and, from an affected clause, hands off to the reconciliation route — it does **not**
> record verdicts or write the decision trail (that is the reconciliation story's `verdicts` /
> `trail` slices). It owns only the minimal `driftSeen` slice. Because MVP1 demonstrates the
> Monitor over **two prepared, dated source-change events** (PDPA §129 amendment 2010→2024;
> the Basel III output-floor change), its drift data is a **prepared JSON snapshot**
> (`web/public/data/drift.json`), honestly labelled — not a live watcher.

## Functional Requirements

- **The drift queue renders from `web/public/data/drift.json` (snapshot), or a live route if
  `NEXT_PUBLIC_API_BASE` is set.** `web/app/monitor/page.tsx` reads the drift events through a
  new store reader `useStore.drift()`; in snapshot mode it `fetch()`es
  `web/public/data/drift.json` (default, deploy-safe), and only if `NEXT_PUBLIC_API_BASE` is
  set does it call the live drift route. Each event is one queue row; the queue is rendered
  from the data — counts and clause lists are never hard-coded.
- **Every drift item carries the prepared-event label, always visible.** Each queue row and
  its detail view show a persistent "Prepared, dated demonstration event — not a live feed"
  marker rendered from the item's `prepared_event: true` field. Nothing in the UI implies a
  continuously-running watcher. This honesty label is a **hard build requirement**, not
  decoration, and cannot be toggled off.
- **A queue row states the source, the change date, and the affected count.** e.g. "Personal
  Data Protection Act §129 amended (2024) — 3 clauses in your draft are now out of sync"
  and "Basel III output-floor standard finalised — 1 clause in your draft is now out of
  sync", each computed from `affected.length` in the item, never a literal.
- **Opening an item shows the plain-language what-changed + the verbatim changed passage.**
  The detail view renders the item's `what_changed` plain-language note and the `changed_passage`
  quoted verbatim (rendered by the shared `QuoteBlock` component), with its `verification`
  marker: `verified` → "✓ verified word-for-word against the source"; `pending_verification`
  → a labelled "pending verification — not yet confirmed word-for-word" placeholder. A
  `pending_verification` passage is shown **as-is**
  and is **never** upgraded to verified or approximated/paraphrased into the verbatim slot.
- **The affected-clause list renders each affected clause with reason + verbatim passage +
  marker.** For each entry in `affected`, the view shows the clause number (e.g. RMiT
  10.50(c)), the plain-language `reason` the change touches it, and the exact `changed_passage`
  it is out of sync with, carrying the same `verification` marker. The affected list is
  rendered exactly from the data — no clause is added, padded, or dropped by the page.
- **The ruled-out "not affected" list is always shown.** For each entry in `not_affected`,
  the view lists the clause number and (optionally) why it was checked and excluded, so the
  affected list is trustworthy. **No clause may appear in both lists** — the page asserts the
  two sets are disjoint on render and logs a defect if they overlap (they must never, per the
  data contract).
- **The topical-inference caveat is shown where applicable.** When an item has
  `topical_inference: true` (as in the PDPA §129 → RMiT case, where no RMiT clause literally
  cites the Act), the detail view shows a caveat: "No clause literally cites this source — the
  link is a topical inference to confirm." The caveat is informational: it **does not remove**
  any clause from the affected list.
- **The materiality reason is shown.** Each item renders its engine-supplied
  `materiality.reason` (human-readable) so Aisyah can see why the change was judged material
  enough to queue. The exact threshold is a deferred open question and is **not** shown as a
  number.
- **Opening an affected clause hands off to reconciliation.** Each affected clause has an
  "Open in reconciliation" affordance that navigates to `/connections/<connection_id>` (the
  reconciliation route) via a Next.js `<Link>`. This is a **plain route navigation, not an
  API call**, and the hand-off is where the verdict is judged and the trail written — the
  Monitor writes nothing.
- **The affected list is a prompt — it changes nothing in the draft.** Rendering or reading a
  drift item does not write any verdict, does not touch the `verdicts` / `trail` slices, and
  does not alter the draft. State only changes downstream, in the reconciliation view, after
  Aisyah opens a clause and acts.
- **A no-affected-clauses drift item states so cleanly.** When an item's `affected` is empty,
  the detail view shows "This source changed, but no clause in your draft is affected," lists
  the `not_affected` clauses that were checked, offers no hand-off, and lists no clause as
  affected.
- **Optional "mark as seen" is minimal and Monitor-owned.** If the page marks an item as seen,
  it appends the item's id to a new `driftSeen` slice (`["<drift_id>", …]`) via
  `useStore.markDriftSeen(id)`. This is the **only** slice the Monitor writes; it is cosmetic
  (dims a reviewed row) and changes nothing about the draft or the trail.

### Validation & Business Rules

- The verification marker shown for a passage must equal the item's `verification` field — the
  page may never upgrade `pending_verification` to `verified`. A mismatch is a defect (asserted
  in the walkthrough).
- The affected and not-affected clause sets must be disjoint; a clause present in both is a
  data defect the page surfaces rather than silently rendering.
- The hand-off route id is taken from the item's `affected[].connection_id`; an item whose
  affected entry has no resolvable `connection_id` renders the clause without a hand-off link
  (never a dead link), matching the reconciliation story's missing/stale handling.
- A `pending_verification` passage is rendered in a clearly-labelled placeholder slot, never in
  the verbatim-verified slot.

## Permissions & Security

- **Scope:** public. Every drift event derives from public sources (PDPA 2010 as amended 2024;
  the Basel III output-floor standard). No auth on the Monitor surface.
- **No restricted text in the snapshot.** The exporter that produces `drift.json` **skips
  any node with `access: "restricted"`** (the same carve-out the workspace snapshot exporter
  uses), so no confidential handbook text or "own past positions" land in the tracked
  `web/public/data/` path. Enforced by the confidentiality guard.
- **No new write routes.** The Monitor consumes read data only; the sole client-side write is
  the optional `driftSeen` slice in the Zustand store (persisted to `localStorage`). It never
  writes the `verdicts` / `trail` slices.
- **Input validation on the hand-off id.** The `connection_id` used for the
  `/connections/<id>` route is matched against known connection ids; an unknown/stale id lands
  on the reconciliation view's graceful "connection not available — back to workspace" message
  rather than a crash or blank page.

## API Design (consumed — no new engine routes for MVP1)

Because MVP1 demonstrates the Monitor over **prepared, dated events**, drift data is a
**static prepared snapshot** — this story defines **no new engine routes**. (A live drift
route is a roadmap item, gated behind `NEXT_PUBLIC_API_BASE` when it exists.) The Monitor
consumes:

- **`web/public/data/drift.json`** (new, owned here) — the prepared drift queue, produced by
  extending the snapshot exporter. `useStore.drift()` reads it (or a live route if
  `NEXT_PUBLIC_API_BASE` set).
- **`/connections/<connection_id>`** — the hand-off target route (reconciliation story). This
  is a **plain route navigation**, not an API call.

The `drift.json` shape, with a **concrete example carrying both prepared events**:

```json
{
  "generated_from": "prepared_events",
  "drift_events": [
    {
      "id": "drift-pdpa-129-2024",
      "prepared_event": true,
      "source": {
        "title": "Personal Data Protection Act 2010 (as amended 2024)",
        "section": "§129",
        "source_type": "act_law"
      },
      "change_date": "2024",
      "what_changed": "The whitelist regime was removed and replaced by a self-assessed test of a \"substantially similar law OR an adequate level of protection\"; the default was flipped; and \"data user\" was renamed \"data controller\".",
      "changed_passage": {
        "text": "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act; or (b) that place ensures an adequate level of protection…",
        "verification": "verified"
      },
      "materiality": {
        "reason": "A substantive rewrite of the cross-border transfer test, not a re-wording — the obligation itself changed."
      },
      "topical_inference": true,
      "topical_inference_note": "No RMiT clause literally cites the Personal Data Protection Act, so the link is a topical inference to confirm.",
      "affected": [
        {
          "clause_number": "RMiT 10.50(c)",
          "connection_id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129::rmit-10.50c",
          "reason": "Relies on the cross-border transfer test the amendment rewrote.",
          "changed_passage": {
            "text": "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act; or (b) that place ensures an adequate level of protection…",
            "verification": "verified"
          }
        },
        {
          "clause_number": "RMiT 10.50(j)",
          "connection_id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129::rmit-10.50j",
          "reason": "Relies on the cross-border transfer test the amendment rewrote.",
          "changed_passage": {
            "text": "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act; or (b) that place ensures an adequate level of protection…",
            "verification": "verified"
          }
        },
        {
          "clause_number": "RMiT 17.1",
          "connection_id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129::rmit-17.1",
          "reason": "Governs data handling the amendment's default-flip now affects.",
          "changed_passage": {
            "text": "A data controller may transfer any personal data of a data subject to any place outside Malaysia if— (a) there is in that place in force any law which is substantially similar to this Act; or (b) that place ensures an adequate level of protection…",
            "verification": "verified"
          }
        }
      ],
      "not_affected": [
        {
          "clause_number": "RMiT 8.1",
          "reason": "Governs board oversight, untouched by the transfer test."
        },
        {
          "clause_number": "RMiT 11.1",
          "reason": "Cloud outsourcing scope, not personal-data transfer."
        },
        {
          "clause_number": "RMiT 17.1(b)",
          "reason": "Sub-clause on encryption keys, not the transfer default."
        },
        {
          "clause_number": "RMiT 17.1(c)",
          "reason": "Sub-clause on retention, not the transfer default."
        }
      ]
    },
    {
      "id": "drift-basel-output-floor",
      "prepared_event": true,
      "source": {
        "title": "Basel III output-floor standard (BCBS)",
        "section": "Output floor",
        "source_type": "international_standard"
      },
      "change_date": "finalised",
      "what_changed": "The aggregate output floor is now set at 72.5% — a capital-treatment clause that relies on the earlier position is now out of sync.",
      "changed_passage": {
        "text": "The aggregate output floor is set at 72.5% of the risk-weighted assets calculated under the standardised approaches.",
        "verification": "pending_verification"
      },
      "materiality": {
        "reason": "A change to the numeric output floor a clause relies on — the capital treatment it assumes has moved."
      },
      "topical_inference": false,
      "affected": [
        {
          "clause_number": "RMiT capital-treatment clause",
          "connection_id": "ai-dp-2025:capital::bcbs-output-floor",
          "reason": "Relies on the earlier output-floor position the finalised standard supersedes.",
          "changed_passage": {
            "text": "The aggregate output floor is set at 72.5% of the risk-weighted assets calculated under the standardised approaches.",
            "verification": "pending_verification"
          }
        }
      ],
      "not_affected": []
    }
  ]
}
```

The minimal `useStore` readers/writers this story adds to the spine:

```ts
useStore.drift(); // → drift_events[] from web/public/data/drift.json (snapshot) or the live route if NEXT_PUBLIC_API_BASE set
useStore.markDriftSeen(id); // optional: appends <id> to the driftSeen slice (cosmetic; writes nothing about the draft)
```

## Data Model & Artifacts

No database. State lives in two places:

- **Static snapshot** (read-only, prepared): `web/public/data/drift.json` (shape above) —
  produced by extending `scripts/export_poc_snapshot.py` (or a sibling exporter, e.g.
  `export_drift_snapshot`), skipping any `access:"restricted"` node. It carries the `source`,
  `change_date`, `what_changed`, `changed_passage` (+ `verification`), `materiality.reason`,
  `topical_inference`, `affected[]` (each with `clause_number`, `connection_id`, `reason`,
  `changed_passage`), and `not_affected[]` fields.
- **Zustand store (mutable, per browser, persisted to `localStorage`):** the optional
  Monitor-owned `driftSeen` slice (`["<drift_id>", …]`), written only through
  `useStore.markDriftSeen`. The Monitor writes **no** other slice — verdicts and the trail
  belong to the reconciliation story.

## UI/Frontend Requirements

- **`web/app/monitor/page.tsx`** (new) — the drift surface:
  - **Drift queue list** — one row per `drift_events` entry: source title + change date +
    "N clauses out of sync" (computed) + the always-on prepared-event label.
  - **Drift-item detail** — on selecting a row: the `what_changed` plain-language note; the
    verbatim `changed_passage` with its verification marker via the shared `QuoteBlock` (or the
    labelled pending-verification placeholder); the **affected** list (each clause with reason,
    verbatim passage + marker, and an "Open in reconciliation" hand-off); the **not-affected**
    ruled-out list; the `materiality.reason`; the topical-inference caveat where
    `topical_inference` is true; and the persistent prepared-event label.
  - **Hand-off** — "Open in reconciliation" is a Next.js `<Link href="/connections/<connection_id>">`.
- **Shared components** (`web/components/`) — reuses `QuoteBlock` (from the workspace story)
  for the changed-passage verified/pending markers; no new shared component is introduced here.
- **`web/lib/store.ts`** (extend the spine) — add the `driftSeen` slice, `drift()`, and
  optional `markDriftSeen(id)`; the page reads them through the `useStore` hook like every
  other UI story.
- **States:** _Loading_ — skeleton rows while `drift.json` resolves. _Queue_ — the list
  of prepared drift events. _Item-detail_ — the opened item. _Pending-verification-passage_ —
  the Basel passage shown in a labelled placeholder, never as verified. _No-affected-clauses_ —
  "source changed, no clause affected," ruled-out list shown, no hand-off. _Prepared-event
  label always on_ — visible on every row and every detail view. _Error_ — a
  snapshot/route failure shows "couldn't load the drift queue — retry," never a blank page.

## Architecture Notes

- **New dependencies:** none beyond the shared spine (Next.js + React + Tailwind + shadcn/ui
  under `web/`; the reused `QuoteBlock` component and Zustand store). The exporter uses the
  standard library plus the existing `engine` package — no new Python deps.
- **Prepared-snapshot, not a live watcher.** MVP1 ships the two prepared events in
  `web/public/data/drift.json`; the **roadmap** is (a) a continuously-running watcher that
  polls the source web and pushes drift as it happens, and (b) the same drift machinery
  "pointed inward" at the drafter's own Word document. Neither is built here; the
  `NEXT_PUBLIC_API_BASE` seam in `web/lib/data.ts` leaves room for a live route without
  changing the page's render path.
- **Integration points:** reached from the Workbench; consumes the prepared snapshot via
  `useStore.drift()`; **hands off** to the reconciliation route (`/connections/<id>`); shares
  the spine store `web/lib/store.ts` and `components/`. The Monitor is upstream of
  reconciliation and writes nothing the reconciliation story reads.

## Exemplar Files

- `docs/poc/drafter-knowledge-graph/monitor.html` — the legacy drift page, kept as the
  **read-only UX reference** the `web/app/monitor/page.tsx` build follows (queue + item detail
  - hand-off); it is not extended as the live demo.
- `spec-upload-and-workspace.md` → "Shared Technical Spine", the `web/lib/store.ts` +
  `useStore` contract, the `QuoteBlock` component, and the `scripts/export_poc_snapshot.py`
  exporter (restricted-node skip) this story extends.
- `spec-connection-reconciliation.md` → the `/connections/<id>` route — the hand-off target
  and its missing/stale id handling this story links into.

## Implementation Plan

### Sub-tasks

**Task 1: `driftSeen` slice + `drift()` reader in `web/lib/store.ts`** — _small_

- Add the `driftSeen` slice, `drift()` (reads `web/public/data/drift.json` in snapshot mode
  via `web/lib/data.ts`, or a live route if `NEXT_PUBLIC_API_BASE` set), and the optional
  `markDriftSeen(id)` appending to the `driftSeen` slice. Depends on the spine store existing.
- Files: `web/lib/store.ts`
- SEQUENTIAL (depends on the workspace story's store scaffold)

**Task 2: Prepared `web/public/data/drift.json` snapshot + exporter extension** — _medium_

- Author the two prepared events (PDPA §129 with RMiT 10.50(c)/10.50(j)/17.1 affected and
  RMiT 8.1/11.1/17.1(b)/17.1(c) not-affected + topical-inference; Basel output-floor with one
  affected clause, passage `pending_verification`) and extend
  `scripts/export_poc_snapshot.py` to serialise them, skipping `access:"restricted"` nodes.
- Files: `web/public/data/drift.json` (new), `scripts/export_poc_snapshot.py` (extend),
  `engine/tests/test_export_poc_snapshot.py` (extend)
- INDEPENDENT (needs the engine artifacts, not the store)

**Task 3: `web/app/monitor/page.tsx` drift queue + item-detail renderer** — _large_

- Render the queue rows (source + date + computed count + prepared-event label); on selection
  render what-changed, verbatim passage + verification marker via the shared `QuoteBlock` (or
  pending placeholder), affected list (reason + passage + marker), not-affected list,
  materiality reason, and the topical-inference caveat; enforce disjoint affected/not-affected;
  render the no-affected-clauses state cleanly.
- Files: `web/app/monitor/page.tsx`, `web/components/*` (reuse `QuoteBlock`)
- SEQUENTIAL (depends on Tasks 1, 2)

**Task 4: Open-affected-clause hand-off to reconciliation** — _small_

- Wire each affected clause's "Open in reconciliation" to a Next.js `<Link>` to
  `/connections/<connection_id>`; validate the id (unknown → graceful reconciliation message,
  never a dead link); optional mark-as-seen dimming.
- Files: `web/app/monitor/page.tsx`, `web/lib/store.ts`
- SEQUENTIAL (depends on Task 3)

### Negative Constraints

- Do NOT build a live or continuously-running source watcher in MVP1 — drift is a prepared
  snapshot; the watcher is a labelled roadmap item.
- Do NOT record verdicts or write the `trail` / `verdicts` slices from the Monitor — hand off
  to the reconciliation view, which owns those slices.
- Do NOT approximate or paraphrase a `pending_verification` passage, and never present it as
  verified — show it in the labelled placeholder as-is.
- Do NOT pad the affected list — render exactly the clauses in the data; never add speculative
  links or drop a ruled-out clause.
- Do NOT extend the legacy `docs/poc/drafter-knowledge-graph/*.html` pages as the live demo —
  they are the read-only UX reference only.
- Do NOT imply a live feed anywhere in the UI — the prepared-event label is always on.

## Test Scenarios

**Test 1: The PDPA §129 item renders exactly the hand-verified affected and not-affected sets**

- Setup: `web/public/data/drift.json` with the `drift-pdpa-129-2024` event.
- Action: open the PDPA §129 item in `web/app/monitor/page.tsx`.
- Expected: the affected list shows exactly RMiT 10.50(c), 10.50(j), and 17.1 (each with its
  reason + verbatim passage); the not-affected list shows exactly RMiT 8.1, 11.1, 17.1(b),
  17.1(c); no clause appears in both lists; nothing outside the data is rendered.

**Test 2: The topical-inference caveat is present but removes no clause**

- Setup: the PDPA §129 item (`topical_inference: true`).
- Action: open the item.
- Expected: the caveat "no clause literally cites this source — a topical inference to confirm"
  is shown; the affected list still contains all three clauses (10.50(c), 10.50(j), 17.1) — the
  caveat is informational only.

**Test 3: The Basel passage is `pending_verification`, never verified or approximated**

- Setup: the `drift-basel-output-floor` event with `changed_passage.verification:
"pending_verification"`.
- Action: open the Basel item.
- Expected: the passage renders in the labelled "pending verification" placeholder, is **not**
  marked verified, and is shown as the raw source-candidate text — never a paraphrase presented
  as the verbatim source passage.

**Test 4: Material changes queue; a non-material edit does not (per the Scenario Outline)**

- Setup: `web/public/data/drift.json` contains the two material events (the transfer-test
  rewrite and the numeric output-floor change), each with a `materiality.reason`; a
  typographical/renumbering
  edit is **absent** from `drift_events` (never queued).
- Action: render the queue.
- Expected: both material events appear as rows with their materiality reason visible; the
  non-material edit produces no row.

**Test 5: A no-affected-clauses item renders cleanly with no hand-off**

- Setup: a drift event with `affected: []` and a populated `not_affected`.
- Action: open the item.
- Expected: "source changed, but no clause in your draft is affected" is shown; the ruled-out
  clauses are listed; no clause is listed as affected; no "Open in reconciliation" hand-off is
  offered.

**Test 6: Open-affected-clause navigates to `/connections/<id>` and the label is always on**

- Setup: the PDPA §129 item; RMiT 10.50(c) has `connection_id`
  `ai-dp-2025:4.6::pdpa-2010:PDPA 129::rmit-10.50c`.
- Action: use "Open in reconciliation" on RMiT 10.50(c).
- Expected: navigation targets the route `/connections/ai-dp-2025:4.6::pdpa-2010:PDPA 129::rmit-10.50c`
  (a plain `<Link>`, no API call); and the "prepared, dated demonstration event" label is visible on
  every queue row and every item detail throughout.

**Test 7: The exporter skips restricted nodes when producing `drift.json`**

- Setup: a fixture graph with one `access:"public"` PDPA node and one `access:"restricted"`
  handbook node.
- Action: run the drift-snapshot exporter.
- Expected: `web/public/data/drift.json` contains the public PDPA event; **no** field anywhere
  contains the restricted node's title or text.

## Verification

Run the `verifier` skill (Vitest/RTL for the Monitor surface; Python/`pytest` for the exporter
when it is extended for `drift.json`, Task 2).

### Backend Tests

- `engine/tests/test_export_poc_snapshot.py` (extend) — Test 7 (the drift-snapshot exporter
  emits the public event and skips `access:"restricted"` nodes; asserts `verification` markers,
  including the Basel `pending_verification`, pass through unchanged and un-upgraded).

### Component / Unit Tests (Vitest + React Testing Library — the gate)

- `web/app/monitor/monitor.test.tsx` — Tests 1–5: the PDPA §129 item renders exactly the
  hand-verified affected (RMiT 10.50(c), 10.50(j), 17.1) and not-affected (RMiT 8.1, 11.1,
  17.1(b), 17.1(c)) sets with **no overlap**; the topical-inference caveat is shown but removes
  no clause; the Basel `pending_verification` passage renders in the labelled placeholder and is
  **never** upgraded to verified or approximated; the always-on prepared-event label is present
  on every queue row and item detail.

### E2E Tests (Playwright — optional, non-blocking)

| Key Scenario                                           | Test file                 | Assigned sub-task |
| ------------------------------------------------------ | ------------------------- | ----------------- |
| Drift item → open affected clause → reconcile hand-off | `web/e2e/monitor.spec.ts` | Task 4            |

**Locator strategy:** `data-testid` on the drift rows (`drift-<id>`), the affected-clause
cards (`affected-<clause>`), and the "Open in reconciliation" link. Flagged non-blocking — a
red E2E never blocks the demo; the Vitest gate above is authoritative.

### Dev-server walkthrough

Run the Next.js dev server (`npm run dev` in `web/`) and walk through:

1. Open `/monitor` → the drift queue shows two prepared rows (PDPA §129 (2024); Basel
   output-floor), each with the always-on prepared-event label and a computed "N clauses out of
   sync" count. (Drift-item-appears + honest-labelling scenarios.)
2. Open the PDPA §129 item → the what-changed note (whitelist removed, default flipped, "data
   user" → "data controller"), the verified verbatim passage, and exactly RMiT 10.50(c),
   10.50(j), 17.1 affected — each with reason + passage. (What-changed + affected-list scenarios.)
3. Confirm the not-affected list shows RMiT 8.1, 11.1, 17.1(b), 17.1(c) and no clause overlaps
   the affected list. (Ruled-out / no-false-links scenario.)
4. Confirm the topical-inference caveat is shown and the affected list still has all three
   clauses. (Topical-inference scenario.)
5. Open the Basel item → the passage is in a "pending verification" placeholder, never marked
   verified or approximated; the single affected capital-treatment clause and its reason are
   shown. (Basel headline + verified-vs-pending scenarios.)
6. Use "Open in reconciliation" on RMiT 10.50(c) → lands on `/connections/…` for that
   connection. (Hand-off scenario.)
7. Confirm reading the item wrote no `verdicts` / `trail` slice and altered nothing in the
   draft. (Affected-list-is-a-prompt scenario.)
8. Confirm the prepared-event label is visible on every row and every item detail. (Honest
   "prepared single event" labelling scenario.)

## Open Questions (technical)

- [x] ~~Where does the drift data come from in MVP1?~~ — **Resolved:** a **prepared JSON
      snapshot** (`web/public/data/drift.json`) carrying the two dated events (PDPA §129
      amendment; Basel output-floor), produced by extending `scripts/export_poc_snapshot.py`
      and read through `useStore.drift()`. No new engine route in MVP1; a live drift route is
      gated behind `NEXT_PUBLIC_API_BASE` as a roadmap item.
- [x] ~~How is the Monitor's honesty labelling enforced?~~ — **Resolved:** each item carries a
      `prepared_event: true` field and the page renders an always-on "prepared, dated
      demonstration event — not a live feed" marker from it; it cannot be toggled off, matching
      the spine's "honesty labelling is a build requirement" rule.
- [ ] **What counts as a "material" source change worth queuing?** — **Deferred
      (non-blocking):** the snapshot shows each event's `materiality.reason`; the precise
      threshold separating substance from noise is settled with drafter validation and does not
      block this release. (Unchanged from the business Open Questions.)
- [ ] **How "live" must the drift beat look, and exactly where is the prepared-versus-live line
      drawn and labelled?** — **Deferred (non-blocking):** MVP1 ships the prepared snapshot with
      the always-on label; the exact prepared-versus-live framing (and any future live route
      behind `NEXT_PUBLIC_API_BASE`) is settled during implementation. (Unchanged.)
- [ ] **Is the proactive drift queue actually preferred over on-demand checking?** — **Deferred
      (non-blocking):** awaiting a drafter conversation; if drafters prefer their own cadence,
      the proactive queue drops to a labelled roadmap phase. (Unchanged.)
