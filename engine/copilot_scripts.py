"""Scripted Drafting Copilot replies (drafting workspace, MVP1).

There is no model behind the Copilot and there is not meant to be one: the demo
replays a fixed conversation per intent preset. `create_app()` takes no model
seam, so this module is the whole of the Copilot's "intelligence".

**Every clause quoted here is verbatim and checkable.** That is not decoration —
it is the product rule this repo exists to demonstrate, and the Copilot is the
easiest place in the product to break it, because a scripted reply looks equally
plausible whether or not the clause says what the script claims. So:

- `RMIT_9_4_QUOTE` is asserted against `data/artifacts/clause-index.json` by
  `engine/tests/test_copilot_scripts.py`. Edit the quote to something RMiT does
  not say and the suite fails. That test is deliberately not skippable.
- Every other clause quoted is copied from the `opres-v2` findings fixtures,
  which carry their own verbatim text.

A note on why this cites **RMiT 9.4** and not RMiT 17.1, which the spec asked
for: RMiT 17.1 is about consulting the Bank before first-time adoption of public
cloud for critical systems. It says nothing about accountability, so the spec's
scripted line ("the technology-risk accountability framework set out in RMiT
§17.1") misattributes a real clause — the exact failure the verbatim rule
exists to catch. RMiT 9.4 is the actual accountable-officer clause, and it makes
the §6.3 finding a truer `goes-beyond`: RMiT designates a CISO scoped to the
*technology risk management function*, while the draft's §6.3 reaches the whole
operational resilience domain.
"""

from typing import Any, Optional

# The seven intent presets. Cosmetic in MVP1 beyond keying into this map: they
# signal the surface area the tool will eventually cover.
INTENTS: tuple[str, ...] = (
    "PD",
    "DP",
    "ED",
    "FAQ",
    "Engagement Deck",
    "Feedback Template for Industry",
    "Peer Benchmarking",
)

# RMiT 9.4, first sentence, verbatim from data/artifacts/clause-index.json.
#
# Two liberties are taken, both mechanical and neither touching a word: the
# source PDF's hard line-wraps are collapsed to single spaces, and the footnote
# marker the parser rendered as the LaTeX fragment `$^ { 1 3 }$` (footnote 13,
# which glosses the job title) is dropped. `test_rmit_9_4_quote_is_verbatim`
# applies the same normalisation to the indexed clause and compares, so this
# string cannot drift away from what RMiT actually says.
RMIT_9_4_QUOTE: str = (
    "A financial institution must designate a Chief Information Security "
    "(CISO) by whatever name called, to be responsible for the technology "
    "risk management function of the financial institution."
)

# Operational Resilience 5.3, verbatim from the opres-v2 findings fixtures
# (findings/e-opres_v0_3--hkma_spm_or2.json, source_clauses[0]).
OPRES_5_3_QUOTE: str = (
    "A financial institution shall conduct scenario testing of its "
    "operational resilience arrangements at least annually."
)

# HKMA SPM OR-2 5.2, verbatim from the same finding's target_clauses[0].
HKMA_5_2_QUOTE: str = (
    "An authorized institution should conduct scenario testing at least "
    "once every two years."
)

# The phrase the product shows instead of an invented quotation. Kept as a
# constant so the Copilot, the review screen, and any future surface agree.
NO_MATCHING_CLAUSE: str = "No matching clause found"

COPILOT_SCRIPTS: dict[str, list[dict[str, Any]]] = {
    "PD": [
        {
            "role": "copilot",
            "text": (
                "Hi Aisyah — I've loaded your accepted linkages and the OpRes DP "
                "feedback register. The draft has no §6.3 yet. Want me to draft the "
                "accountable-officer preamble that goes beyond RMiT?"
            ),
        },
        {
            "role": "copilot",
            "text": (
                "Here is a neutral §6.3 preamble. It is grounded in RMiT 9.4, which "
                "designates a CISO responsible for the technology risk management "
                "function — the draft reaches further, to the whole operational "
                "resilience domain, which is what makes this a goes-beyond rather "
                "than an alignment."
            ),
            "citations": [{"clause_number": "RMiT 9.4", "text": RMIT_9_4_QUOTE}],
            "snippet_html": (
                "<h2>PART E — ACCOUNTABILITY</h2>\n"
                "<p><strong>6.3</strong> A financial institution shall designate a "
                "single accountable officer for operational resilience, who shall be "
                "responsible for the end-to-end delivery of critical operations and "
                "shall report directly to the chief executive officer.</p>\n"
                "<p><strong>6.4</strong> The officer designated under paragraph 6.3 "
                "may be the same person designated as Chief Information Security "
                "Officer under the Risk Management in Technology policy document, "
                "provided that the financial institution can demonstrate that the "
                "wider operational resilience mandate is discharged with sufficient "
                "authority, independence and resources.</p>"
            ),
        },
    ],
    "DP": [
        {
            "role": "copilot",
            "text": (
                "Discussion Paper mode. I can draft the question set for §5.3 "
                "(scenario testing cadence) framed against the HKMA biennial "
                "baseline — the draft pins annual, HKMA asks for at least once "
                "every two years, so the question to industry is whether the "
                "tighter cadence is proportionate."
            ),
            "citations": [
                {"clause_number": "Operational Resilience 5.3", "text": OPRES_5_3_QUOTE},
                {"clause_number": "HKMA SPM OR-2 5.2", "text": HKMA_5_2_QUOTE},
            ],
        },
    ],
    "ED": [
        {
            "role": "copilot",
            "text": (
                "Exposure Draft mode. I'll keep the tone consultative and surface "
                "the differs-on finding on §5.3 so respondents can see the "
                "rationale for departing from the HKMA baseline rather than "
                "guessing at it."
            ),
            "citations": [
                {"clause_number": "Operational Resilience 5.3", "text": OPRES_5_3_QUOTE},
            ],
        },
    ],
    "FAQ": [
        {
            "role": "copilot",
            "text": (
                "FAQ mode. Suggested question: “Does the operational resilience "
                "accountable officer replace or supplement the RMiT CISO?” — the "
                "answer turns on RMiT 9.4, which scopes the CISO to the technology "
                "risk management function."
            ),
            "citations": [{"clause_number": "RMiT 9.4", "text": RMIT_9_4_QUOTE}],
        },
    ],
    "Engagement Deck": [
        {
            "role": "copilot",
            "text": (
                "Engagement deck mode. Want a 3-slide skeleton for the ABM "
                "briefing? I'd lead with the scenario-testing cadence change, "
                "since that is the one that costs them money."
            ),
        },
    ],
    "Feedback Template for Industry": [
        {
            "role": "copilot",
            "text": (
                "Feedback template mode. I can prep the response grid keyed on "
                "§5.3 (cadence) and the proposed §6.3 (accountable officer) — the "
                "two paragraphs most likely to draw comment."
            ),
        },
    ],
    "Peer Benchmarking": [
        {
            "role": "copilot",
            "text": (
                "Peer benchmarking mode. On the scenario-testing cadence question "
                "I have HKMA SPM OR-2 loaded, which asks for testing at least once "
                "every two years against the draft's annual requirement. MAS TRM "
                "and APRA CPS 230 are not in this workstream, so I cannot quote "
                "them — add them as nodes and I will."
            ),
            "citations": [{"clause_number": "HKMA SPM OR-2 5.2", "text": HKMA_5_2_QUOTE}],
        },
    ],
}


def reply_for(intent: str, turn: int) -> Optional[dict[str, Any]]:
    """The scripted reply for `intent` at conversation position `turn`.

    Returns `None` for an unknown intent. When the script for a known intent runs
    out, the last reply repeats rather than erroring — the demo should never dead
    end on a stray extra Send, and repeating a real, cited answer is safer than
    improvising an uncited one.
    """
    script = COPILOT_SCRIPTS.get(intent)
    if not script:
        return None
    return dict(script[min(turn, len(script) - 1)])
