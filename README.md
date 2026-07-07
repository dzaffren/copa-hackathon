# 🛰️ Rulebook Radar

**AI for policy consistency — COPA Hackathon 2026 (Bank Negara Malaysia).**

Rulebook Radar maps a cluster of BNM's own published policy documents as a
connected **knowledge graph** and uses it to keep the rulebook consistent. When a
policy drafter revises a policy, it traces the ripple across every linked policy
and flags where the change creates a **Conflict**, a **Duplication**, or a
**Gap** — each finding quoting the exact clause it is based on. The same graph
serves a **supervisor**, who uploads a bank's application and receives a cited
checklist of every requirement it must meet across the linked policies, flagging
what is missing.

> **One-line pitch defence:** a chatbot answers _"what does the rule say"_;
> Rulebook Radar answers _"what breaks if the rule changes"_ and _"what's missing
> from this submission"_ — the consistency / supervision job a chatbot can't do.

Built entirely on **public** BNM policy documents and demonstrated on the
technology-risk cluster (RMiT · Operational Resilience · Outsourcing · Business
Continuity · Cyber Risk).

## Why it matters

Aligned to **BP2026 Must-Win 10** (AI roadmap for supervision), whose Key Result 3
targets _">15% efficiency across 10 supervisory processes from staff usage of AI
tools."_ It also supports **MW9** (process efficiency) and **MW6** (a coherent,
non-contradictory rulebook), and the broader SET2027 goals of a Trusted
Institution / Credible Regulator and Engaged Employees.

## Two users, one knowledge graph

| Persona                             | Task                        | What the tool does                                                                                                                                                                                                   |
| ----------------------------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Policy drafter**                  | Revising a policy           | Maps the cluster, traces the ripple of a change, flags Conflict / Duplication / Gap findings, and offers a grounded drafting copilot that writes accepted redrafts back into the living document as tracked changes. |
| **Supervisor (Jabatan Penyeliaan)** | Assessing a bank submission | Reads an uploaded application, assembles every applicable requirement _across_ policies, and marks each Met / Missing / Unclear — so nothing slips through.                                                          |

**The graph is the engine, not always the interface:** the drafter operates the
graph directly; the supervisor consumes its output as a checklist and sees the
graph only on demand ("why is this required?").

## Core guardrail — verbatim citation

Every finding, checklist line, and copilot answer **quotes the exact clause** it
relies on, with its clause number. If no supporting clause exists, the tool says
so explicitly ("No matching clause found") rather than assert an unsupported
claim. This anti-hallucination rule was validated in a blind LLM test on the real
RMiT and Outsourcing documents — it independently found the genuine cross-policy
conflict (Outsourcing 12.1 "approve-before" vs. RMiT 17.1 amended to
"notify-after") and every cited clause checked out verbatim.

## Repository layout

```
docs/
├── discovery/policy-consistency-ai/
│   └── brief.md            # Opportunity solution tree + validated LLM experiment
├── poc/policy-consistency-ai/
│   ├── index.html          # Role-aware workspace knowledge graph (drafter)
│   ├── review.html         # RMiT change — side-by-side review
│   ├── review-opres.html   # Operational Resilience change
│   ├── review-outsourcing.html  # Reviewer (comment-only) view
│   ├── impact.html         # Ripple report: Conflict / Duplication / Gap findings
│   ├── chat.html           # Drafting copilot + live document viewer
│   └── supervisor.html     # Upload → cited Met/Missing/Unclear checklist → decide
└── specs/rulebook-radar/
    ├── spec.md                          # Epic overview (shared rules, journey, metrics)
    ├── spec-knowledge-graph-engine.md   # Ingestion + clause index + graph (technical)
    ├── spec-drafter-workspace.md        # Role-aware workspace
    ├── spec-ripple-impact-report.md     # Consistency ripple check
    ├── spec-drafting-copilot.md         # Copilot with live write-back
    ├── spec-supervisor-check.md         # Submission completeness & compliance check
    └── spec-reviewer-approval.md        # Reviewer & approval workflow
```

## View the prototype

**🔗 Live demo:** https://dzaffren.github.io/copa-hackathon/

The POC is a self-contained, clickable HTML prototype (Tailwind via CDN — no build
step). Open any page directly in a browser, starting with the drafter workspace:

```bash
open docs/poc/policy-consistency-ai/index.html
```

Or serve the folder locally:

```bash
python3 -m http.server --directory docs/poc/policy-consistency-ai 8000
# then visit http://localhost:8000/index.html
```

## Status

- **Discovery:** complete — opportunity selected, riskiest assumption retired via a
  green LLM experiment on real documents.
- **POC:** clickable prototype covering both personas, both loops closed.
- **PRD:** epic + 6 vertically-sliced story specs, ready for technical refinement.
- **Scope:** MVP1 is a single cluster (technology-risk); cross-cluster ripple is a
  labelled "what's next" preview, not built.

## Note on confidential material

Internal BNM reference documents used during discovery are **excluded** from this
repository (see `.gitignore`). Everything published here is built on public policy
documents.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the git strategy (GitHub Flow,
Conventional Commits, PR process). AI agents pick up the rules automatically from
[`CLAUDE.md`](CLAUDE.md).

## License

No license is set yet. Hackathon output may be subject to BNM's own IP and
publication policy, so licensing is **to be confirmed** internally before reuse.
Until then, treat this as "all rights reserved" by default.
