# 🧠 Workstream Brain

**AI for BNM cross-workstream policy drafting — COPA Hackathon 2026 (Bank Negara Malaysia).**

Workstream Brain maps every document a policy workstream depends on — BNM
peers, BCBS mother-docs from bis.org, national acts, and industry input — as a
**knowledge graph**, and surfaces AI-found linkages between clause pairs
labelled with a five-way semantic taxonomy: `aligns-with`, `differs-on`,
`conflicts-with`, `silent-on`, `goes-beyond`. Each finding **quotes the exact
clause** it relies on. Cross-jurisdiction pairs run through an axis-first
retrieval pipeline so that "same axis, different terminology" comparisons —
Malaysia's conforming loans ≡ England's Level C loans — are discoverable
without an LLM having to spot the equivalence from raw text.

> **One-line pitch defence:** a chatbot answers _"what does the rule say"_;
> Workstream Brain answers _"what do peer regulators, BCBS mother-docs, and
> your own past drafts say about the exact axis you're drafting on — and where
> do they tighten, loosen, conflict, or stay silent?"_ — the cross-workstream
> memory job a chatbot can't do.

Built entirely on **public** policy documents and demonstrated on a
cross-jurisdiction credit-risk cluster: BNM Operational Resilience DP + UK Bank
of England Chapter 3 + HKMA CA-G-1 + Singapore MAS Notice 637 + BCBS
mother-docs (CRE, OPE, BCP).

## Why it matters

Aligned to **BP2026 Must-Win 10** (AI roadmap for supervision), whose Key Result 3
targets _">15% efficiency across 10 supervisory processes from staff usage of AI
tools."_ It also supports **MW9** (process efficiency) and **MW6** (a coherent,
non-contradictory rulebook), and the broader SET2027 goals of a Trusted
Institution / Credible Regulator and Engaged Employees.

## Core guardrail — verbatim citation

Every finding, checklist line, and copilot answer **quotes the exact clause or
passage** it relies on, with its anchor ID resolved to real content in the
`AnchorIndex`. If no supporting clause exists, the tool says so explicitly
("No matching clause found") rather than assert an unsupported claim. The
anti-hallucination guardrail is enforced by deterministic code — the LLM
proposes labels; the citation validator commits.

## Engine architecture — role-specialised agentic RAG

Pairwise comparison runs through a fixed pipeline of five stages, four of which
use LLMs with distinct single-purpose roles:

1. **Anchor segmentation** — three strategies (structured-rules regex,
   semi-structured heading walker, prose semantic chunker) turn PDFs from
   different jurisdictions into a common `AnchorIndex`.
2. **Axis extraction (LLM)** — each anchor gets 1–5 short topic phrases in
   canonical regulatory language, deliberately abstracted away from the
   source's jurisdiction-specific terminology.
3. **Hybrid retrieval (deterministic)** — BM25 + cosine over axis embeddings +
   glossary alias expansion proposes candidate anchor pairs across documents.
4. **Finder → Critic (LLMs)** — judges one candidate pair at a time, emits a
   semantic label with optional sentiment on `differs-on`.
5. **Citation validator (deterministic)** — resolves every cited `anchor_id`
   against `AnchorIndex`; anything unresolved is dropped, never fabricated.

This is agentic RAG in the sense used by the
[Legal Document RAG pattern (Medium)](https://medium.com/enterprise-rag/legal-document-rag-multi-graph-multi-agent-recursive-retrieval-through-legal-clauses-c90e073e0052) —
a pipeline of role-specialised LLM stages coordinated by a deterministic
orchestrator, not a free-form multi-agent conversation. Full detail lives in
[`docs/specs/workstream-brain/`](docs/specs/workstream-brain/).

## Repository layout

```
docs/
├── discovery/workstream-brain-mvp1/
│   └── brief.md                    # Opportunity solution tree + validated experiment
├── poc/workstream-brain/           # Clickable HTML prototype (read-only UX reference)
├── specs/workstream-brain/         # Live epic — Workstream Brain MVP1
│   ├── spec.md                            # Epic overview
│   ├── spec-engine-taxonomy.md            # Five-label semantic taxonomy (technical)
│   ├── spec-engine-anchor-segmentation.md # Multi-strategy AnchorIndex (technical)
│   ├── spec-engine-retrieval-pipeline.md  # Axis extraction + hybrid retrieval (technical)
│   ├── spec-workstream-graph.md           # Hero screen
│   ├── spec-review-linkages.md            # Finding review
│   ├── spec-task-screen.md                # Pairwise comparison
│   ├── spec-drafting-workspace.md         # 3-tab side panel + editor
│   └── spec-new-workstream.md             # Workstream creation
├── specs/rulebook-radar/           # RETIRED — historical only
└── specs/reconciliation-workbench/ # RETIRED — historical only

engine/                             # Python 3.12 + FastAPI backend
├── api.py                          # HTTP surface (POST /connections/find etc.)
├── anchors.py                      # (planned) AnchorIndex + segmenters
├── axes.py                         # (planned) Stage A — axis extraction
├── retrieval.py                    # (planned) Stage B — hybrid retriever
├── connections.py                  # Finder → Critic loop (five-label taxonomy)
└── ...

data/
├── corpus/manifest.json            # Source-of-truth document manifest
├── corpus/{bnm,bcbs,temp/...}/     # Public source PDFs
└── artifacts/                      # Build outputs (anchor index, traces, axes)

archive/                            # Retired: Next.js `web/` app + kg-poc prototype
```

## Tech stack

- **Backend:** Python 3.12 + FastAPI, entrypoint `engine/api.py`. Runs offline
  in demo mode by replaying committed `data/artifacts/connection-trace-*.json`
  files; live builds use Azure OpenAI (GPT-4o) + Azure Document Intelligence.
- **Frontend:** **Vite + React 18 + TypeScript + Tailwind + shadcn/ui**,
  planned under `frontend/src/features/{feature}/` per the user-facing specs.
  React Router v6, TanStack Query, react-hook-form + zod. The `frontend/`
  directory is created by the user-facing story builds.
- **Retired stack:** the Next.js app under `archive/web/` backed the earlier
  Reconciliation Workbench epic and is not part of MVP1.

## Status

- **Discovery:** complete — 12 supported linkages found on the OpRes DP × Open
  Finance ED pair, zero unsupported. Cross-jurisdiction assumption
  (axis-first retrieval) is being validated during build week.
- **POC:** clickable HTML prototype at `docs/poc/workstream-brain/` covers all
  six screens end-to-end.
- **Specs:** epic + three engine specs (taxonomy, anchor segmentation,
  retrieval pipeline) + five user-facing story specs — all technically refined
  and ready to build.
- **Deadline:** hackathon deadline **3 August 2026**; MVP1 demoable by
  2026-07-31 to leave a rehearsal buffer.

## Note on confidential material

Internal BNM reference documents used during discovery are **excluded** from this
repository (see `.gitignore`). Everything published here is built on public
policy documents from BNM, MAS, HKMA, the Bank of England, and BCBS.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the git strategy (GitHub Flow,
Conventional Commits, PR process). AI agents pick up the rules automatically from
[`CLAUDE.md`](CLAUDE.md).

## License

No license is set yet. Hackathon output may be subject to BNM's own IP and
publication policy, so licensing is **to be confirmed** internally before reuse.
Until then, treat this as "all rights reserved" by default.
