"""Shared writing constraints for every prompt that explains something to the
drafter.

One source of truth for the house style, so the finder prompts
(`engine.arm_g`) and the Copilot chat prompt (`engine.copilot`) cannot drift
apart again. Before this module the em-dash ban existed in three prompts in
three slightly different sentences.

Design: `docs/superpowers/specs/2026-07-31-shared-prompt-constraints-design.md`.
Extends the word caps in `docs/specs/plain-language-finding-explanations/spec.md`,
which are unchanged and still enforced in code by `arm_g.enforce_phrasing` — the
prompt asks, the code enforces, and neither layer is trusted alone.

Text only: no functions and no imports from elsewhere in `engine/`, so this can
never participate in an import cycle.

Which surface uses what:

- `GOVERNING_THOUGHT_RULE` + `HOUSE_CONSTRAINTS` — both surfaces.
- `ACTION_TITLES_RULE` — Copilot only; a finding object has no headings.
- `EVIDENCE_DISCIPLINE_RULE` — the finders only; the Copilot's equivalent is its
  citation rule, backed by `copilot._validate_reply`.

Deliberately NOT adopted from the consulting template that prompted this work:
the SCQ section scaffold, the issue tree, "group into 3 pillars", the
business-strategy frameworks (Five Forces / 3Cs / 4Ps), and the
roadmap/risks step. Reasons are recorded in the design doc; the short version is
that the complaint was answers being too long, and a five-section deck per reply
makes them longer.
"""

# The pyramid principle, stated so it applies to a prose reply and to a finding's
# `summary` field alike. On the Copilot surface the "single claim" is the first
# sentence of the reply; on the finder surface it is the `summary` itself.
GOVERNING_THOUGHT_RULE: str = (
    "GOVERNING THOUGHT (strict): lead with the answer. State the single claim "
    "you are making first, in one sentence, before any supporting detail. Never "
    "build up to a conclusion, and never open with preamble, a restatement of "
    "the question, or a description of what you are about to do."
)

# MECE + tone + no-fluff. Kept deliberately short: it shares prompt space with
# the strict citation rules, and a long style block dilutes them.
HOUSE_CONSTRAINTS: str = (
    "HOUSE CONSTRAINTS (strict):\n"
    "- MECE: when you break something into parts, the parts must not overlap "
    "and must not leave a gap. Never make the same point twice in different "
    "words, and never omit a part the drafter needs.\n"
    "- Tone: professional, objective, concise. Avoid jargon where simple "
    "language says the same thing.\n"
    "- No fluff: every sentence must carry a claim or the evidence for one. Cut "
    "any sentence that carries neither.\n"
    "- Do NOT use em dashes. Use commas, colons, semicolons, or separate "
    "sentences instead."
)

# Copilot only: a finding object has no heading to write.
ACTION_TITLES_RULE: str = (
    "ACTION TITLES: a heading must state the insight, not the topic. Write "
    '"Outsourcing 12.1 requires a tested exit plan; the draft does not", never '
    '"Exit planning". If a heading could sit above any other section without '
    "changing meaning, it is a topic label and needs rewriting."
)

# Finders only: the finding already carries its evidence in the clause arrays,
# so the useful constraint is that the claim and the evidence must match. This is
# also the backstop for the overclaiming risk that GOVERNING_THOUGHT_RULE and
# ACTION_TITLES_RULE introduce by asking for a sharper claim.
EVIDENCE_DISCIPLINE_RULE: str = (
    "EVIDENCE DISCIPLINE (strict): the `summary` must be provable from the "
    "cited clauses alone. If your claim depends on a fact that is not in the "
    "text of the clauses you cite, either cite the clause that carries that "
    "fact or weaken the claim until the cited text supports it. Never state a "
    "sharper claim than the quoted clauses can prove."
)

# 'Document A' / 'Document B' are internal prompt mechanics: the DIRECTION
# CONVENTION line has to name them so the side-guard is unambiguous, but the
# drafter has no idea which document is which. An A/B run on 31 Jul 2026 measured
# this leak at 10 of 15 scope_notes once EVIDENCE_DISCIPLINE_RULE landed next to
# the direction convention, against 0 before. `test_prompt_style.py` and
# `test_demo_finding_phrasing.py` both assert against it now.
NO_INTERNAL_LABELS_RULE: str = (
    "NEVER NAME THE SIDES BY LETTER: `Document A`, `Document B`, `A-side`, and "
    "`B-side` are internal labels for you only. The drafter never sees which "
    "document is which, so those words are meaningless to them. In `summary` and "
    "`scope_note`, always refer to a document the way a drafter would: `we` / "
    "`our document` / `the draft` for the A side, and for the B side either its "
    "own short name (for example `the BIS paper`, `the HKMA framework`, `RMiT`) "
    "or `they` / `their document`."
)
