# Rulebook Radar — Agent Guide

AI for BNM policy consistency (COPA Hackathon 2026, Must-Win 10). A knowledge-graph
tool that flags Conflict / Duplication / Gap findings when a policy changes
(drafter) and checks a bank submission for missing requirements (supervisor).
Docs-only repo today: discovery brief, a clickable HTML POC, and PRD specs.

## Git strategy (follow exactly)

Full guideline: [`CONTRIBUTING.md`](CONTRIBUTING.md). Enforceable rules:

- **Never commit to `main` directly.** Branch, then open a PR. Model is GitHub Flow.
- Branch names: `type/short-kebab` (`feat/`, `fix/`, `docs/`, `chore/`, `refactor/`).
- Commits use **Conventional Commits**: `type(scope): imperative summary` (≤72 chars).
  Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `style`.
- One logical change per commit; explain **why** in the body when non-obvious.
- Prefer **squash merge**; delete the branch after merge.
- **Only commit or push when the user explicitly asks.**

## Confidentiality (hard rule)

This repo is **public**. `docs/references/` holds internal BNM documents and is
git-ignored — **never** add, commit, or push anything sensitive to a tracked path.
Before any commit, verify nothing under `docs/references/` is staged.

## Product rule — verbatim citation

Every finding, checklist line, and copilot answer must **quote the exact clause**
it relies on, with its clause number. If no clause supports a claim, state "No
matching clause found" — never invent one. Preserve this in any spec or POC edit.

## Repository layout

- `docs/discovery/` — discovery brief (opportunity solution tree, LLM experiment)
- `docs/poc/policy-consistency-ai/` — clickable prototype; open `index.html`
- `docs/specs/rulebook-radar/` — epic overview (`spec.md`) + 6 story specs
- `docs/references/` — **git-ignored**, internal, local only

## Conventions

- Specs are non-technical and grounded in real clauses (RMiT 17.1/17.2,
  Outsourcing 12.1, OpRes 6.11). Keep personas consistent: Aisyah R. drafts RMiT v2
  and Operational Resilience v2 and reviews Outsourcing v2; Farid M. drafts
  Outsourcing v2 and reviews Aisyah's RMiT v2; a manager approves.
- POC pages are self-contained HTML using Tailwind via CDN — no build step.
- MVP1 scope is a single cluster (technology-risk); cross-cluster ripple is a
  labelled "what's next" preview, not built.
