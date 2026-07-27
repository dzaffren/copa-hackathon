# Build a Workstream From Scratch — Overview

**Discovery Brief:** docs/discovery/workstream-brain/brief.md

## Summary

This epic lets a policy drafter build a complete policy workstream live in the
Workstream Brain app — create the workstream, add source documents, have each
document broken into citable passages, extract its concepts, connect documents
to one another, and run linkage analysis — with every result saved durably so a
workstream built ahead of time survives to the demo. It replaces the reliance on
pre-seeded example workstreams with a genuine build-it-yourself flow for the
COPA Hackathon 2026 demo (3 Aug 2026).

## Background & Context

**Current state:**

- Creating a workstream produces an empty canvas — there is no starting focal
  node to attach documents to, so the drafter lands on a blank graph.
- The "Add node" form accepts a title, description, source link and connections,
  but an added document is never broken into citable passages and its concepts
  are never derived — so a freshly added document cannot be analysed.
- Connections between documents can only be declared while adding a _new_ node;
  there is no way to connect two documents that already exist on the canvas.
- Linkage analysis works only for documents that were prepared in advance by an
  offline build step, not for documents a drafter adds through the app.
- The demo runs on pre-seeded example workstreams that are now outdated.

**Problem:**

- A drafter cannot assemble a real workstream themselves — the tool can only
  display workstreams prepared for it in advance.
- Because added documents are never processed, the headline capability of the
  product (surfacing labelled linkages between documents, quoted verbatim) is
  unreachable for anything the drafter adds.
- For the hackathon, the team wants to build the demo workstreams live in the
  product beforehand and have them persist — the outdated seeded examples are
  being removed, so the build-it-yourself flow must fully stand in for them.

## Goals

- Let a drafter create a workstream that opens with a ready focal working-draft
  node at its centre.
- Let a drafter add a source document, choose how it should be broken into
  passages, and have that happen immediately on adding it.
- Let a drafter extract a document's concepts on demand and see them on the node.
- Let a drafter connect any two existing documents on the canvas.
- Let a drafter run linkage analysis on any connection between two documents they
  built, and see findings.
- Ensure everything produced — passages, concepts, connections, findings — is
  saved durably so a workstream built before the demo is intact during it.

## Non-Goals

- **Cross-workstream linkages.** Connecting and analysing documents that belong
  to _two different_ workstreams (the eventual demo climax) is deferred to a
  separate spec. This epic covers connections and analysis **within a single
  workstream** only.
- **Automatic detection of a document's structure.** The drafter chooses the
  breaking-up method when adding a document; the tool does not guess it.
- **Background processing.** Concept extraction runs when the drafter asks for
  it and completes before returning; there is no queue, no progress that
  continues after the drafter navigates away.
- **Editing or re-uploading a document's file after it has been added.**
- **The management-facing institution map**, which remains a follow-on epic.

## Story Index

| Ticket | Story                                           | Spec                                                                         | Type        | Status      | Dependencies          |
| ------ | ----------------------------------------------- | ---------------------------------------------------------------------------- | ----------- | ----------- | --------------------- |
| TBD    | Focal working-draft node on workstream creation | [spec-focal-task-node.md](spec-focal-task-node.md)                           | User-facing | Not Started | —                     |
| TBD    | Add a document and break it into passages       | [spec-add-node-chunking.md](spec-add-node-chunking.md)                       | User-facing | Not Started | Focal node            |
| TBD    | Extract concepts and view node detail           | [spec-extract-concepts-node-detail.md](spec-extract-concepts-node-detail.md) | User-facing | Not Started | Add-document          |
| TBD    | Connect two existing documents                  | [spec-add-edge.md](spec-add-edge.md)                                         | User-facing | Not Started | Focal node            |
| TBD    | Analyse a linkage on a self-built workstream    | [spec-live-analysis.md](spec-live-analysis.md)                               | Technical   | Not Started | Add-document, Connect |

## Shared Business Rules

- **Verbatim citation.** Every passage a document is broken into is an exact,
  word-for-word slice of that document — never reworded or summarised. Every
  finding quotes the exact passages it relies on. If nothing supports a claim,
  the tool says so rather than inventing a quote.
- **One connection is required to add a document.** A new document must be
  connected to at least one document already on the canvas when it is added.
- **The focal node is the anchor.** The workstream's focal working-draft node is
  the centre of the graph; connections to it read from the focal node outward.
- **Durable, portable results.** Everything produced for a workstream — its
  passages, concepts, connections and findings — is stored with that workstream
  so it can be prepared ahead of time and is present, unchanged, during the demo.
- **Breaking-up methods.** A document is broken into passages by one of three
  drafter-chosen methods: _structured-rules_ (for numbered Bank Negara Malaysia
  policy documents), _semi-structured_ (headings and numbered paragraphs), or
  _prose_ (flowing text). The drafter picks one when adding the document.
- **Concepts are the document's extracted topics.** A node's "Concepts" are the
  short topic phrases derived from its passages. A node's "Metadata" is a fixed
  set of regulatory profile fields, shown as "N/A" for now.
- **Same-workstream only.** A connection joins two documents in the same
  workstream. Analysis needs two _different_ documents, each already broken into
  passages.

## User Journey Map

1. **Create the workstream** — The drafter names a new workstream, gives a short
   description, picks its deliverable type and target delivery, and creates it.
   The workstream opens with a single focal working-draft node at the centre of
   an otherwise empty canvas. _(Story: Focal working-draft node)_
2. **Add the first document** — The drafter clicks "Add node", enters a title
   and description, attaches a PDF, chooses how it should be broken up, and
   connects it to the focal node. On adding, the document is immediately broken
   into passages and appears on the canvas. _(Story: Add a document)_
3. **Extract its concepts** — Opening the new node, the drafter sees its
   neighbours and a recent-activity trail ("node created", "chunking completed").
   They click "Extract concepts"; after a short wait the node's concept pills
   appear and "axes extracted" joins the activity trail. Below the activity, a
   "Metadata" section lists the regulatory profile fields as "N/A". _(Story:
   Extract concepts and view node detail)_
4. **Add more documents and connect them** — The drafter adds further documents
   the same way, and uses "Add edge" on any node to connect two documents that
   are already on the canvas. _(Story: Connect two existing documents)_
5. **Analyse a linkage** — The drafter clicks a connection between two documents
   and runs "Analyze linkage". The tool finds linkages between the two documents'
   passages and presents them as findings, each quoting the exact passages it
   relies on. _(Story: Analyse a linkage)_
6. **Completion** — The drafter has a fully built workstream — documents broken
   into passages, concepts extracted, connections drawn, and findings surfaced —
   all saved so it can be built before the demo and shown intact on the day.

## Success Metrics

- A drafter can build a workstream end to end — create, add at least two
  documents, connect them, and produce findings — entirely within the app,
  without any pre-seeded data.
- 100% of findings quote a real passage from the cited document; no invented
  quotes.
- A workstream built before the demo is fully intact and re-openable during the
  demo, with all passages, concepts, connections and findings present.
- Adding a document returns the drafter to the canvas quickly (breaking-up is
  effectively immediate); concept extraction completes within a single wait
  without the drafter leaving the page.

## Dependencies

- Access to the language model used for concept extraction and linkage analysis
  during preparation and demo.
- The three document breaking-up methods already exist in the product and are
  reused unchanged.
- Removal of the outdated seeded example workstreams (in progress) so the
  build-it-yourself flow is the sole path.

## Rollout Strategy

- Deliver the focal node first (every other story attaches to it), then adding
  documents, then extract-concepts / node detail and connecting documents (which
  can proceed in parallel), then live analysis last (it depends on documents
  being broken into passages and connected).
- The team pre-builds the demo workstreams once the flow is complete and commits
  the resulting workstream data so it is fixed for the demo.

## Open Questions

- [x] ~~Should added documents share one library of passages or keep each
      workstream's separate?~~ — **Resolved:** Each workstream keeps its own
      passages, concepts and findings, stored with that workstream, so preparing one
      workstream never disturbs another and everything travels together to the demo.
- [x] ~~Should breaking up a document be automatic or chosen?~~ — **Resolved:**
      The drafter chooses one of the three methods when adding the document, to avoid
      documents being broken up incorrectly.
- [x] ~~Should concept extraction run in the background?~~ — **Resolved:** No.
      Breaking up happens immediately on add; concept extraction is a separate,
      explicit button that completes before returning. This keeps the flow simple
      with no background machinery for the hackathon.
- [x] ~~Must analysis wait for concepts to be extracted first?~~ — **Resolved:**
      No. Analysis will extract whatever it needs itself and reuses concepts already
      extracted, so it never repeats work. The "Extract concepts" button simply lets
      the drafter see concepts earlier.
- [x] ~~Does the focal node need its own document?~~ — **Resolved:** No. The
      focal node starts empty; documents are added as separate nodes that connect to
      it.
- [x] ~~Does connecting and analysis need to span two workstreams?~~ —
      **Resolved:** Not in this epic. Cross-workstream connection and analysis is a
      separate spec.
