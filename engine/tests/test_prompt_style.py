"""The shared house-style constraints must reach every live prompt.

Mirrors `test_connections.py::test_prompts_describe_taxonomy_and_direction`: the
point is not to test the model, it is to stop the three prompts drifting apart
again. Before `engine.prompt_style` existed, the em-dash ban lived in three
prompts in three slightly different sentences.

Design: `docs/superpowers/specs/2026-07-31-shared-prompt-constraints-design.md`.
"""

import pytest

from engine import arm_g, copilot
from engine.prompt_style import (
    ACTION_TITLES_RULE,
    EVIDENCE_DISCIPLINE_RULE,
    GOVERNING_THOUGHT_RULE,
    HOUSE_CONSTRAINTS,
    NO_INTERNAL_LABELS_RULE,
)

# The Copilot prompt is built per turn, so it is rendered once here with
# throwaway grounding; only the style block is under test.
COPILOT_PROMPT = copilot._system_prompt("OpRes PD v0.3", "PD", "(no clauses)")

FINDER_PROMPTS = (
    arm_g.SAME_TOPIC_FINDER_SYSTEM_PROMPT,
    arm_g.COVERAGE_FINDER_SYSTEM_PROMPT,
)
ALL_PROMPTS = FINDER_PROMPTS + (COPILOT_PROMPT,)


@pytest.mark.parametrize("prompt", ALL_PROMPTS)
def test_every_live_prompt_carries_the_shared_constraints(prompt):
    """Governing thought and the house constraints apply to both surfaces."""
    assert GOVERNING_THOUGHT_RULE in prompt
    assert HOUSE_CONSTRAINTS in prompt


@pytest.mark.parametrize("prompt", FINDER_PROMPTS)
def test_finder_prompts_forbid_naming_the_sides_by_letter(prompt):
    """Regression guard, 31 Jul 2026. A live A/B run showed `Document A` /
    `Document B` leaking into 10 of 15 drafter-visible scope_notes once the
    evidence-discipline rule landed next to the DIRECTION CONVENTION line, which
    is where that vocabulary comes from. The convention itself must stay (the
    side-guard depends on it), so the prompt has to say both things."""
    assert NO_INTERNAL_LABELS_RULE in prompt
    # The direction convention it coexists with is still present.
    assert "we/ours" in prompt and "they/theirs" in prompt


@pytest.mark.parametrize("prompt", FINDER_PROMPTS)
def test_finder_prompts_carry_evidence_discipline_and_mece(prompt):
    """Evidence discipline is finder-specific: it constrains `summary` against
    the clause arrays that carry the finding's evidence. MECE is stated per
    surface (per batch for same-topic, per document for coverage), so assert the
    keyword rather than a shared sentence."""
    assert EVIDENCE_DISCIPLINE_RULE in prompt
    assert "MECE" in prompt


def test_action_titles_are_copilot_only():
    """A finding object has no heading, so the action-titles rule belongs only to
    the prose surface. Asserted both ways so neither drifts."""
    assert ACTION_TITLES_RULE in COPILOT_PROMPT
    for prompt in FINDER_PROMPTS:
        assert ACTION_TITLES_RULE not in prompt


@pytest.mark.parametrize("prompt", ALL_PROMPTS)
def test_the_em_dash_ban_is_stated_exactly_once(prompt):
    """The regression this module exists to prevent: the ban used to be restated
    per prompt, so the wordings drifted. It now arrives only via
    HOUSE_CONSTRAINTS."""
    assert prompt.count("Do NOT use em dashes") == 1


@pytest.mark.parametrize("prompt", FINDER_PROMPTS)
def test_finder_prompts_keep_their_word_caps(prompt):
    """The prompt-side half of the caps enforced in code by `enforce_phrasing`.
    The shared constraints extend the plain-language spec; they do not replace
    it."""
    assert f"at most {arm_g.SUMMARY_MAX_WORDS} words" in prompt
    assert f"at most {arm_g.SCOPE_NOTE_MAX_WORDS} words" in prompt


@pytest.mark.parametrize("prompt", ALL_PROMPTS)
def test_the_citation_rules_survive_the_style_block(prompt):
    """Guards the design doc's stated risk: a long style block sharing prompt
    space with the strict citation rules must not displace them."""
    assert "invent" in prompt


def test_prompt_style_holds_no_engine_imports():
    """`prompt_style` is text only, so it can never join an import cycle."""
    from pathlib import Path

    source = Path(arm_g.__file__).with_name("prompt_style.py").read_text(
        encoding="utf-8"
    )
    body = source.split('"""', 2)[-1]  # skip the module docstring
    assert "import" not in body
