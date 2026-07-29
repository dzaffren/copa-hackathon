# Backlog — Copilot Drafting Flow & Node Metadata

**Status:** captured ideas, not yet specced or approved · **Captured:** 29 Jul 2026 · **Demo:** 3 Aug 2026

These are loosely-specified product ideas raised in discussion and written down for the
owner to prioritise on return. Nothing here is a committed spec, and nothing has been
built. Each item below is graded against what already ships today so the review can tell
a genuine gap from a coat of paint on something that already works. Sizes and
demo-relevance calls are the author's honest estimate, not a plan.

---

## The drafting-lifecycle vision (merged)

Workflow A and Workflow B are two phrasings of the **same** arc: take a drafter from a
blank task node to a document ready to send out, with the Copilot carrying them through
staged commands. Merged, the stages are:

| Stage                  | Command(s)                                  | Intent                                                                                      |
| ---------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 0. Frame the task      | `/pull-node-metadata`, `/explore-task`      | Pull the node's regulatory profile (the 10 fields) and understand what the deliverable is.  |
| 1. Align understanding | `/brainstorming` + `/pull-context` (silent) | Copilot asks questions until "user understanding == AI understanding" before any drafting.  |
| 2. Skeleton            | `/skeleton`                                 | A wireframe: sections with objectives and key bullet points, not prose.                     |
| 3. Draft the content   | `/build`, `/write`                          | Populate the skeleton into a full deliverable (PD / DP / ED / FAQ / slides / deck).         |
| 4. Send off            | `/release`, `/deliver`                      | Route the draft to related departments and post-DD / post-Manager / post-Director sign-off. |

The command names are the user's own shorthand and are **not** proposed CLI verbs — treat
them as stage labels. A/B differ only in wording (A's `/pull-node-metadata`+`/build` vs
B's `/explore-task`+`/write`); they are not two products.

The user also noted, separately: **"Copilot — make it claude-like"** and a **fix**:
_"add node — define task type (PD, DP, FAQ...)"_.

---

## Backlog items (grounded)

| #   | Item                                                                                                                                                                                | What the user means                                             | Already exists? (grounded)                                                                                                                                                                                                                                                                                                                                            | Size | Dependencies                                                          | Demo by 3 Aug?                                    |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | --------------------------------------------------------------------- | ------------------------------------------------- |
| 1   | **10 node-metadata fields** (task_type, policy_owner, applicability, empowerment_framework, requirement, issuance_date, effective_date, keywords, legal_basis, ismp_classification) | Every node carries a regulatory-profile card.                   | **Mostly done.** 9 of the 10 are exactly `CONCEPT_FIELDS` in `engine/concepts.py`, rendered in `NodeDetailPanel.tsx`'s "Metadata" section. The 10th, `task_type`, is the workstream's `deliverable_type`. `ismp_classification` is `null` everywhere (no honest offline source).                                                                                      | S    | —                                                                     | Already in the app                                |
| 2   | **`/pull-node-metadata`** (populate the 10 fields from the document)                                                                                                                | On demand, fill the profile from the node's own doc.            | **Partially exists — offline only.** `scripts/enrich_node_metadata.py` already derives these from committed fixtures (verbatim clause quotes / structural values), the same offline-script→fixture→projection pattern used elsewhere. What's _new_ is doing it **live/in-app** for a freshly added document rather than as a pre-baked fixture.                       | M    | Add-node ingest (exists); clause index                                | Risky — the offline path demos today; live is new |
| 3   | **Add-node "define task type"** (PD, DP, FAQ...)                                                                                                                                    | When adding a node, pick what kind of deliverable it is.        | **Partially exists, at the wrong level + missing values.** `deliverable_type` (PD / ED / DP / Other) is captured at **workstream creation** (`NewWorkstreamPage.tsx`) and the focal node reflects it (`spec-focal-task-node.md`). `AddNodeDialog.tsx` captures the 8-type **structural** `node_type`, not a deliverable type. **FAQ and slides are not in the enum.** | S    | `DELIVERABLE_TYPE_OPTIONS` in `types.ts`                              | Only if scoped to "add FAQ/slides to the enum"    |
| 4   | **Copilot "make it claude-like"**                                                                                                                                                   | Make the Copilot feel like Claude — polished chat UX.           | **Exists and is already live.** `engine/copilot.py` is a real Azure-Claude call: streaming prose, citation guardrail, 7 intent presets (incl. FAQ, Engagement Deck, Peer Benchmarking), `@`-mention of accepted findings, insert-snippet-into-draft. "Claude-like" is UX polish (turn-taking, markdown, thinking, suggestions), not a rebuild.                        | S–M  | `CopilotTab.tsx`, `DraftingWorkspacePage.tsx`                         | Yes for cosmetic polish; scope it tightly         |
| 5   | **Findings / reviewed findings**                                                                                                                                                    | See AI findings; track which are reviewed.                      | **Done.** 7-status maker/checker flow (`ai_detected`→…→`approved`) in `engine/linkage_review.py`, `review-linkages` + `review-queue` UI.                                                                                                                                                                                                                              | —    | —                                                                     | Already in the app                                |
| 6   | **Recommendations — change based on reviewed findings**                                                                                                                             | Turn an _approved_ finding into a concrete proposed draft edit. | **New capability.** Today the link is manual: an accepted finding can be `@`-mentioned in the Copilot, which _may_ suggest text. There is no "finding → generated recommendation → apply to draft" object or flow. This is the genuinely new product idea in the batch.                                                                                               | L    | Findings review (exists), drafting editor (exists), Copilot grounding | No — larger bet                                   |
| 7   | **`/brainstorming` + `/pull-context`** (Q&A until understanding aligns)                                                                                                             | Copilot interviews the drafter before drafting.                 | **New.** No staged brainstorming/alignment mode exists; the Copilot is single-turn Q&A with no "keep asking until aligned" loop or silent context pull.                                                                                                                                                                                                               | M–L  | Copilot (exists)                                                      | No                                                |
| 8   | **`/skeleton`** (wireframe: sections + objectives + bullets)                                                                                                                        | Generate a document outline before prose.                       | **New.** No outline/skeleton generation today.                                                                                                                                                                                                                                                                                                                        | M    | Copilot, deliverable type                                             | No                                                |
| 9   | **`/build` · `/write`** (full deliverable draft)                                                                                                                                    | Generate the whole document from the skeleton.                  | **Partially exists as raw material.** The drafting workspace (`EditorPane.tsx`) + insert-snippet already lets the Copilot write _into_ a draft. A one-shot "write the whole PD/FAQ/deck" flow is new, and slides/decks have no editor surface at all.                                                                                                                 | L    | Items 7, 8; editor (exists)                                           | No — the large bet                                |
| 10  | **`/release` · `/deliver`** (send-off to depts, DD/M/D)                                                                                                                             | Route the finished draft onward for sign-off.                   | **New.** No departmental routing or approval-handoff beyond the internal maker/checker linkage review. No concept of "post-DD / post-Manager / post-Director".                                                                                                                                                                                                        | L    | Draft complete; org/routing model (none today)                        | No                                                |

---

## Quick wins vs bigger bets

**Quick wins (small AND plausibly demo-relevant):**

- **Item 1 already ships** — the 10-field metadata card is live; no work, just make sure the
  demo opens a node that has it populated (OpRes fixtures do; `ismp_classification` shows
  pending honestly).
- **Item 3, scoped down** — adding **FAQ** (and maybe slides/deck) to
  `DELIVERABLE_TYPE_OPTIONS` is a small, self-contained change if the story is "the enum is
  incomplete", not "per-node deliverable typing". Confirm which the user wants first.
- **Item 4, scoped down** — Copilot cosmetic polish (message layout, streaming feel,
  suggestion chips) is small and demos well, but only if defined as polish, not a rebuild.

**Bigger bets (large, not demo-relevant by 3 Aug):**

- **Item 6 — Recommendations from reviewed findings.** The one genuinely new product idea;
  worth a real spec after the demo.
- **Items 7–10 — the staged drafting lifecycle** (`/brainstorming` → `/skeleton` →
  `/write` → `/deliver`). This is a multi-story epic. The editor and Copilot are the raw
  materials, but the orchestration, outline generation, whole-doc drafting, non-prose
  deliverables (slides), and departmental routing are all net-new.

---

## Open questions for the user

1. **Is the staged drafting flow (items 7–10) for THIS demo or a future one?** The honest
   read is future — none of it exists and 3 Aug is close. Confirm so we don't half-build it.
2. **Item 2 — where does `/pull-node-metadata` source the 10 fields?** Offline enrichment
   already does this from fixtures. Is the ask a _live, on-demand_ pull for a newly-added
   document (new work), or just "surface what the offline script already produces" (done)?
3. **Item 3 — per-node task type, or just a bigger enum?** Do you want a deliverable type
   on _each added node_ (new concept — nodes carry structural `node_type` today), or simply
   FAQ/slides added to the existing **workstream-level** `deliverable_type` list?
4. **"Claude-like" (item 4) — what specifically?** The Copilot is already a live Claude call
   with streaming and citation guarding. Name the missing behaviours (thinking display?
   multi-turn memory? suggestion chips? tool use?) so this isn't an open-ended rebuild.
5. **Deliverables beyond PD/DP/ED/FAQ** — slides, engagement decks, feedback templates
   currently exist only as Copilot _intent presets_ (tone hints), with no editor surface.
   Are these real drafting targets, or just Copilot framing?
6. **`/deliver` routing** — there is no org/department or post-DD/M/D model in the repo
   today. Is departmental sign-off in scope, or is the internal maker/checker linkage
   review sufficient for now?
