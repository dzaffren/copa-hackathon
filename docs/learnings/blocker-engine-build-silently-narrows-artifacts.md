---
name: engine-build-silently-narrows-artifacts
description: A rebuild without Azure DI silently narrows data/artifacts/ and orphans committed traces — no test catches it; do not naive-restore from an old revision
type: blocker
captured: 2026-07-16
source: drift audit of the committed artifacts after the workstream-brain build
---

**`python -m engine.build` overwrites `data/artifacts/` in place, and a run without
Azure Document Intelligence silently produces a NARROWER index rather than failing.**

This already happened. `c0c2fab` (PR #34, "Feat/kg poc skeleton" — a commit about an
unrelated spike) rebuilt the artifacts:

|                      | before (`56cc8b1`, 9 Jul) | after (`c0c2fab`, 14 Jul) |
| -------------------- | ------------------------- | ------------------------- |
| clause-index entries | 1,035                     | 608                       |
| documents            | 7                         | **2** (RMiT only)         |
| graph.json           | 7 nodes / 7 edges         | **2 nodes / 1 edge**      |

Document IDs were also **renamed**: `rmit-v2-2026-draft`→`rmit-v2-2025`,
`rmit-v1-2020`→`rmit-v1-2023`. `outsourcing-v1-2019`, `bcm-v1-2022`,
`opres-v1-2025-draft`, `customer-info-v1-2025` and `recovery-planning-v1-2021`
vanished from the index entirely.

**Consequences, measured against the current index:**

- The OpRes × Open Finance trace resolves **0 of 49** cited clauses — that trace is
  the evidence that retired the discovery brief's riskiest assumption (12 supported
  linkages, zero unsupported).
- The RMiT × Outsourcing trace resolves **28 of 62**. The hero conflict
  (Outsourcing 12.1 "approve-before" vs RMiT 17.1 "notify-after") cannot be
  re-derived — `outsourcing-v1-2019` is not in the index.
- Only `connection-trace-rmit-v1-2023__rmit-v2-2025.json` still resolves (286/286).

**Why nothing caught it:** `engine/tests/test_taxonomy_traces.py` says of itself
_"These are pure file assertions — no network, no engine run."_ It validates each
trace's internal schema and its recorded `resolved: true` flags; it never
cross-checks a citation against the clause index. The full suite is **green** (196
passed) with the artifacts in this state. There was also no CI running any test at
all until `test.yml` was added — so the narrowing shipped unobserved.

**Why:** MarkItDown hardcodes an old preview api-version that GA Document
Intelligence rejects with a 404, which it then _silently swallows, falling back to
the default extractor_ (see `engine/ingest.py:114-118`). The default extractor
scrambles multi-column BNM PDFs, so clauses fail to anchor and drop out. The build
does not fail — it just yields less. See [[convention-offline-build-needs-docintel]].

**How to apply:**

1. **Do not run `python -m engine.build` (or `--docs`) without Azure DI configured.**
   It writes `data/artifacts/` in place with no backup.
2. **If you do rebuild, diff before committing:** compare entry count and the
   `document_id` value set against `git show HEAD:data/artifacts/clause-index.json`.
   A drop is a failure, not a result.
3. **Do NOT naive-restore from `56cc8b1`.** The old and new indexes have _disjoint_
   RMiT document IDs, so restoring fixes the two broken traces and breaks the one
   that currently works. It is a trade, not a fix. A correct restore needs a DI-backed
   rebuild covering both ID generations.
4. **It does not block workstream-brain.** The app reads `data/workstreams/` (fixtures
   - `canned_analysis`) and never touches `data/artifacts/`. Since the 16 Jul legacy
     removal, the only remaining consumers of `data/artifacts/` are
     `engine/tests/test_taxonomy_traces.py` (trace conformance) and
     `scripts/run_finder_trace.py` (which writes new traces). See
     [[convention-workstream-brain-opres-v2-conventions]] and
     [[convention-frontend-app-is-frontend-dir]].
5. **`verdicts.json` is gone for good.** It never existed on disk, and the code that
   read it (`read_model.py`, the legacy API routes, `scripts/export_poc_snapshot.py`)
   plus the stage that wrote it (`build.py` stage 4b, via the deleted `verdicts.py`)
   were all removed on 16 Jul. `engine.build` now writes `clause-index.json` +
   `graph.json` only.

**Open decision:** whether the 2-document index is intentional scope-shedding (the
demo no longer needs the legacy cluster) or an accidental clobber. If intentional,
the two orphaned traces should be labelled historical record. If accidental, it needs
a DI-backed rebuild. Unresolved as of 16 Jul 2026.
