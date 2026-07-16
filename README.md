# 🧠 Workstream Brain

**AI for policy consistency — COPA Hackathon 2026 (Bank Negara Malaysia).**

A BNM policy team drafts a Discussion Paper, an Exposure Draft, or a Policy
Document over months, against a shifting web of anchors: BCBS standards, peer
regulators, acts of law, industry feedback, and BNM's own published policies.
Today the map of how those anchors relate to the draft lives in one senior
policymaker's head.

**Workstream Brain makes that map explicit.** Each workstream becomes a knowledge
graph: documents are nodes, joined by structural edges (`supersedes`,
`references`, `contributes-to`, `parallel-to`). The engine reads clause pairs
across a draft and its anchors and proposes **linkages** — each one labelled,
each one quoting the exact clause it relies on. The drafter reviews, accepts, or
corrects. The demo climax is **cross-workstream drift**: two workstreams running
in parallel that touch the same concept and don't yet know it.

> **Pitch defence:** a chatbot answers _"what does the rule say"_. Workstream
> Brain answers _"what does my draft disagree with, and where's the proof"_ —
> and it survives the policymaker rotating out.

Built entirely on **public** documents. Demonstrated on two real workstreams in
parallel: **Operational Resilience** (continuation) and **Open Finance** (ED
response).

## Why it matters

The strategic frame is **institutional continuity** — cross-workstream drift that
today exists only as expert judgement becomes explicit, cited, and inspectable, so
the map survives when the policymaker rotates, retires, or is on leave.

Anchored on **BP2026 Must-Win 10** (AI for supervision) — KR2 (AI-driven business
process reengineering) and KR3 (_">15% efficiency across 10 supervisory processes"_)
— and **MW6** (a coherent, non-contradictory rulebook), supporting BNM's SET2027
Trusted Institution / Credible Regulator narrative and IMF FSAP readiness.

## The five-label taxonomy

Every finding carries exactly one label. This is the vocabulary — not
Conflict/Duplication/Gap, which was retired in an earlier iteration:

| Label            | Meaning                                                              |
| ---------------- | -------------------------------------------------------------------- |
| `aligns-with`    | The draft and the source say the same thing.                         |
| `differs-on`     | Both address it, but differ. Carries a `tighten`/`loosen` sentiment. |
| `conflicts-with` | They cannot both be complied with.                                   |
| `silent-on`      | The source addresses something the draft does not.                   |
| `goes-beyond`    | The draft addresses something the source does not.                   |

## Core guardrail — verbatim citation

Every finding **quotes the exact clause** it relies on, with its clause number. If
no supporting clause exists, the tool says **"No matching clause found"** rather
than assert an unsupported claim.

**"Verbatim" applies to citations, not to equivalence.** BNM never copy-pastes from
BCBS; the tool never claims two paraphrases are equivalent — it cites both sides
exactly and labels the relationship.

This anti-hallucination rule was validated on real documents: a blind LLM test
independently found the genuine cross-policy conflict (Outsourcing 12.1
"approve-before" vs. RMiT 17.1 amended to "notify-after"), with every cited clause
checking out verbatim. A later experiment on the OpRes × Open Finance pair found
12 supported cross-workstream linkages and zero unsupported.

## Repository layout

**Live code:**

```
engine/          FastAPI read service, clause index, finder→critic linkage loop
frontend/        Workstream Brain app (Vite + React 18 + TanStack Query)  ← UI work lands here
data/
├── corpus/      Parsed BNM policy PDFs (public)
├── references/  External standards — Basel, MAS TRM, PDPA (public)
├── workstreams/ Workstream fixtures: opres-v2, outsourcing-v2, rmit-v2-2025
└── artifacts/   Built clause index + graph + recorded linkage traces
kg-poc/          Standalone ontology/NER pipeline spike (isolated; nothing imports it)
scripts/         Trace runner, snapshot exporter
```

**Docs:** `docs/discovery/` (briefs per iteration) · `docs/specs/workstream-brain/`
(current epic) · `docs/adr/` (decisions) · `docs/learnings/` (repo conventions —
read `INDEX.md` first) · `docs/poc/workstream-brain/` (clickable UX reference).

**Earlier iterations, kept as read-only reference — do not build from these:**
`docs/poc/{policy-consistency-ai,drafter-knowledge-graph}/` and
`docs/specs/{rulebook-radar,reconciliation-workbench}/`. Their **code** is gone: the
reconciliation-workbench Next.js app (`web/`), the verdict/submission/paragraph read
path, and their HTTP routes were removed on 16 Jul 2026 when Workstream Brain became
the end state. A spec referencing them describes a repo that no longer exists.

> **Confidential:** `docs/references/` is git-ignored and internal — never commit
> anything under it. Note this is _not_ `data/references/`, which is public and
> tracked.

## Run it

**Engine** (no Azure credentials needed — every model call site is an injectable
seam, stubbed in tests):

```bash
uv venv .venv && uv pip install pytest python-dotenv fastapi httpx \
  python-multipart uvicorn anthropic azure-ai-inference bleach 'markitdown[pdf,docx]'
PYTHONPATH=. .venv/bin/python -m pytest engine/tests -q   # 255 tests
PYTHONPATH=. .venv/bin/uvicorn engine.api:app --reload    # serves :8000
```

**Frontend:**

```bash
cd frontend
npm ci
npm test          # vitest — 93 tests
npm run dev       # vite dev server
```

Point the app at a live engine with `VITE_API_BASE` (see `frontend/.env.example`);
unset, it uses the bundled fixtures.

## Rebuilding from the corpus

**You do not need this to run or demo the app.** The app is a projection over
`data/workstreams/`, which is committed; `create_app()` has no model seam, so the
service cannot reach a model even if you wanted it to. Everything above runs with
no credentials and no build.

The corpus pipeline is separate, and only joins the app at one point:

```
data/corpus/*.pdf                                  10 registered documents
  └─ python -m engine.build                     →  data/artifacts/clause-index.json
       └─ scripts/run_finder_trace.py A B       →  data/artifacts/connection-trace-A__B.json
            └─ scripts/project_cross_workstream_findings.py
                                                →  data/workstreams/_cross/findings/*.json
```

> **A `--docs` build REPLACES the clause index.** It writes only what it built, so
> a subset run silently drops every other document's clauses. That is not
> hypothetical — it took the index from 7 documents to 2, orphaned two recorded
> traces, and the whole test suite stayed green
> ([the learning](docs/learnings/blocker-engine-build-silently-narrows-artifacts.md)).
> Use `--merge`, which adds instead and refuses any clause-number collision.

```bash
# Safe: add two documents to the existing index (offline, no Azure needed)
PYTHONPATH=. .venv/bin/python -m engine.build \
  --docs opres-v1-2025-draft open-finance-v1-2025-ed --merge

# Inspect a build before it touches anything committed
PYTHONPATH=. .venv/bin/python -m engine.build --docs rmit-v2-2025 --output-dir /tmp/probe
```

A **full** 10-document build needs Azure Document Intelligence credentials in
`.env` — offline it fails on the legacy tech-risk PDFs (`GraphBuildError`, BCM
9.17), because the default extractor scrambles their multi-column layout. The
modern PDFs build offline fine. Re-running the finder (`run_finder_trace.py`)
needs Azure Claude credentials — it is the only step that makes live model calls.

Extraction quality is not uniform, and it matters: DI-built RMiT has 1 hollow
clause in 608, while the offline OpRes DP has 21 in 71 (present, but with empty
text). `engine/tests/test_artifact_integrity.py` pins those counts in both
directions, so a DI rebuild has to lock its gains in rather than leave a standing
excuse.

## View the prototype

**🔗 Live demo:** https://dzaffren.github.io/copa-hackathon/

The clickable prototype is self-contained HTML — open any page directly:

```bash
open docs/poc/workstream-brain/index.html
```

It is the **UX reference** the `frontend/` build follows, not the product itself.

## Status

- **Discovery:** complete — riskiest assumption retired (12 supported linkages
  found on the OpRes × Open Finance pair, zero unsupported).
- **Engine:** clause index, five-label finder→critic loop, workstream routes. Green.
- **Frontend:** workstream graph (hero) and task screen shipped; drafting
  workspace, review linkages, and new-workstream screens specced.
- **Deferred:** the institution map (management-facing zoom-out view) and the
  separate supervisor persona.
- **Scope:** at least two real workstreams in parallel — cross-workstream linkage
  is the demo climax, not a preview.

## Note on confidential material

Internal BNM reference documents used during discovery are **excluded** from this
repository (see `.gitignore`). Everything published here is built on public
documents.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the git strategy (GitHub Flow,
Conventional Commits, PR process). AI agents pick up the rules automatically from
[`CLAUDE.md`](CLAUDE.md).

## License

No license is set yet. Hackathon output may be subject to BNM's own IP and
publication policy, so licensing is **to be confirmed** internally before reuse.
Until then, treat this as "all rights reserved" by default.
