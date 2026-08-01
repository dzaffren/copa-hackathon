# View source PDF from the Review Linkages panes

**Status:** approved 1 Aug 2026
**Screen:** Review Linkages (`frontend/src/features/review-linkages/`) — the
document-vs-document clause reader.

## Problem

The Review Linkages screen puts two documents side by side: the left pane holds
the clauses cited on the edge's `source` node, the right pane the `target`'s.
Each pane card carries the verbatim clause text the engine returned. What the
drafter cannot do from here is check that text against the published document it
came from — the pane is the only view of the source, and there is no way out to
the PDF.

Aisyah needs that check before she accepts a finding. Today it means leaving the
app and finding the file by hand.

## Scope

Add a "Source PDF" button to the top-right corner of both panes. It opens the
document's PDF in a new browser tab. Nothing else on the screen changes.

**Out of scope, noted while reading the code:** `ReviewLinkagesPage` hardcodes
`subtitle="working draft"` on the left pane. That is an `opres-v2`-era
assumption — `open-finance-pd-2026` points its edges _into_ the ED node, so the
left pane is frequently a published document, not the draft. Real, but a
separate change.

## Data

The workstream fixtures carry no PDF pointer today: every node in
`open-finance-pd-2026/graph.json` has `source_url: null`, and
`data/corpus/manifest.json` keys its documents by ids disjoint from the graph's,
so there is no existing join to lean on.

Add a `source_pdf` field to the five document nodes in
`data/workstreams/open-finance-pd-2026/graph.json` — a path **relative to
`data/corpus/`**, resolved by the engine. The PDFs are already on disk and
tracked, so no bytes are duplicated and the feature works offline on demo day.

| node                      | `source_pdf`                             |
| ------------------------- | ---------------------------------------- |
| `ed-open-finance-2025`    | `open-finance/ED_Open_Finance_2025.pdf`  |
| `rmit-2025`               | `open-finance/pd-rmit-nov25.pdf`         |
| `hkma-open-api-framework` | `open-finance/hkma-20180718e5a2.pdf`     |
| `bis-papers-168`          | `open-finance/bispap168.pdf`             |
| `abs-mas-api-playbook`    | `open-finance/mas-ABSMASAPIPlaybook.pdf` |

The task node (`open-finance-pd-2026-pd`) gets no field — there is no published
PDF of a working draft.

The three retired fixtures (`opres-v2`, `rmit-v2-2025`, `open-finance-ed`) get
no field either, per the retired-fixtures rule. The button is absent for them,
which is correct: they are regression checks, not demo surfaces.

## Engine

`create_app` gains a `corpus_dir: Union[str, Path] = REPO_ROOT / "data" /
"corpus"` argument, matching the existing `workstreams_dir` / `artifacts_dir`
seams so tests point it at a tmp dir.

**New route:** `GET /api/workstreams/{workstream_id}/nodes/{node_id}/source-pdf`

Reads `source_pdf` off the node, resolves it under `corpus_dir`, and returns a
`FileResponse` with `media_type="application/pdf"` and an inline
`Content-Disposition` filename so the browser's viewer renders it rather than
downloading it.

A path that escapes `corpus_dir` is refused (`resolve()` +
`Path.is_relative_to`). The field is fixture data today, but the route must not
become a general file-read primitive over the repo.

Errors use the established `{code, message}` body (`_ws_error`):

| condition                         | status | code                   |
| --------------------------------- | ------ | ---------------------- |
| unknown workstream                | 404    | `WORKSTREAM_NOT_FOUND` |
| unknown node                      | 404    | `NODE_NOT_FOUND`       |
| node has no `source_pdf`          | 404    | `SOURCE_PDF_NOT_FOUND` |
| `source_pdf` set but file missing | 404    | `SOURCE_PDF_NOT_FOUND` |
| `source_pdf` escapes `corpus_dir` | 404    | `SOURCE_PDF_NOT_FOUND` |

The escape case returns the same code as a missing file deliberately — the
response should not confirm what lies outside the corpus root.

**Changed route:** `GET .../edges/{edge_id}/review` adds `has_source_pdf: bool`
to each of `edge.source_node` and `edge.target_node`, so the screen knows
whether to render the button without a second round trip.

This is added **inline in `get_edge_review`, not in `_review_node`** —
`_review_node` has three other callers (`_linkage_card`,
`get_pairwise_findings`, and via those `get_reviewed_linkages` /
`get_related_linkages`), and none of them needs the field. Impact analysis rates
a `_review_node` change HIGH; keeping the addition local makes the blast radius
zero.

## Frontend

`ClausePane` takes one new optional prop:

```ts
/** The engine route serving this document's published PDF. When set, the pane
 *  header offers a button that opens it in a new tab. */
sourcePdfUrl?: string | null;
```

When set, the `<header>` becomes a flex row: the existing title/subtitle block
on the left, and a right-aligned `Button variant="ghost" size="sm"` reading
`<ExternalLink /> Source PDF`. It opens the URL with
`window.open(url, "_blank", "noopener,noreferrer")`.

When absent, the header renders exactly as it does now — so the `opres-v2`
tests, which have no `source_pdf`, are untouched.

`ReviewLinkagesPage` derives each URL from the review response's
`has_source_pdf` flags and passes them down.

Native-tab rendering, not an in-app dialog: the browser's PDF viewer brings
search, page navigation, and zoom for free, adds no dependency, and leaves the
review screen's three-column layout intact.

## Tests

**Engine** (`engine/tests/test_api_review.py` plus a new
`test_api_source_pdf.py`):

- the route serves the file bytes with `content-type: application/pdf`
- 404 `SOURCE_PDF_NOT_FOUND` for a node carrying no `source_pdf`
- 404 `SOURCE_PDF_NOT_FOUND` for a `source_pdf` that escapes `corpus_dir`
  (`../../../etc/passwd`), and the file is not served
- 404 `NODE_NOT_FOUND` / `WORKSTREAM_NOT_FOUND` on bad ids
- `GET /review` reports `has_source_pdf` on both nodes — true for a node with
  the field, false for the task node

**Frontend** (`ReviewLinkagesPage.test.tsx`):

- the button renders in both panes and targets the correct node's route
- the button is absent when `has_source_pdf` is false

The MSW handler and the `ReviewEdgeNode` type gain the field.
