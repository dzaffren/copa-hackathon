"""Tests for Task 2 of Arm G: COVERAGE_FINDER_SYSTEM_PROMPT constant and
labels parameter on _finder_per_pair.

These tests exercise only the observable surface specified by Task 2:
1. COVERAGE_FINDER_SYSTEM_PROMPT exists, is a non-empty string, contains the
   required terms, and embeds the COVERAGE-SUMMARY RULE.
2. _finder_per_pair(anchor_index, pair) with no labels arg calls the LLM with
   FINDER_SYSTEM_PROMPT (unchanged behaviour).
3. _finder_per_pair(anchor_index, pair, labels="same-topic") prepends the
   restriction clause to the user message.

No network access: call_chat is patched via unittest.mock.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make sure the repo root is on the path so the script can import engine.*
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.experiments.retrieval_ablation as ra

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_anchor(anchor_id: str, document_id: str, text: str) -> dict:
    return {"anchor_id": anchor_id, "document_id": document_id, "text": text}


class _FakeAnchorIndex:
    """Minimal AnchorIndex stub for testing."""

    def __init__(self, anchors: list[dict]) -> None:
        self._by_id = {a["anchor_id"]: a for a in anchors}

    def get(self, anchor_id: str):
        return self._by_id.get(anchor_id)

    def by_document(self, document_id: str):
        return [a for a in self._by_id.values() if a["document_id"] == document_id]


_PAIR = {
    "source_anchor_id": "A1",
    "target_anchor_id": "B1",
    "matched_axis_source": "consent",
    "matched_axis_target": "consent-management",
}

_INDEX = _FakeAnchorIndex(
    [
        _make_anchor("A1", "doc-a", "A requires explicit consent from users."),
        _make_anchor("B1", "doc-b", "B requires user consent for data processing."),
    ]
)


# ---------------------------------------------------------------------------
# Criterion 1: COVERAGE_FINDER_SYSTEM_PROMPT exists and has required content
# ---------------------------------------------------------------------------


def test_coverage_finder_system_prompt_exists():
    assert hasattr(ra, "COVERAGE_FINDER_SYSTEM_PROMPT")
    assert isinstance(ra.COVERAGE_FINDER_SYSTEM_PROMPT, str)
    assert len(ra.COVERAGE_FINDER_SYSTEM_PROMPT) > 0


def test_coverage_finder_system_prompt_restricts_to_coverage_labels():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    assert "silent-on" in prompt
    assert "goes-beyond" in prompt
    # Must NOT permit the three same-topic labels
    # (they should be listed as forbidden, not as options)
    # The prompt must explicitly state only silent-on / goes-beyond are allowed
    assert "aligns-with" not in prompt or (
        # It may mention them as labels to EXCLUDE; ensure the restriction is clear
        "ONLY" in prompt
        or "never" in prompt.lower()
        or "restrict" in prompt.lower()
    )


def test_coverage_finder_system_prompt_coverage_summary_rule():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    # COVERAGE-SUMMARY RULE: three numbered requirements
    # (1) name the shared regulatory topic both documents sit under
    assert "shared" in prompt.lower() or "topic" in prompt.lower()
    # (2) state what the covering side specifically requires
    assert "covering" in prompt.lower() or "requires" in prompt.lower()
    # (3) state precisely what the other side does NOT address
    assert "does not address" in prompt.lower() or "does NOT address" in prompt


def test_coverage_finder_system_prompt_guardrail_both_sides():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    # Explicit guardrail: if both sides take a position, do NOT emit a coverage finding
    assert "both sides" in prompt.lower() or "both side" in prompt.lower()


def test_coverage_finder_system_prompt_citation_rule():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    # Must include the same citation rule as FINDER_SYSTEM_PROMPT
    assert "CITATION RULE" in prompt or "citation rule" in prompt.lower()
    assert "Never invent" in prompt or "never invent" in prompt.lower()


def test_coverage_finder_system_prompt_json_array_contract():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    assert "JSON array" in prompt or "json array" in prompt.lower()
    assert "silent-on" in prompt
    assert "goes-beyond" in prompt


def test_coverage_finder_system_prompt_no_sentiment():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    # Sentiment must be omitted per taxonomy (coverage labels never carry sentiment)
    # The prompt should not instruct the model to emit sentiment
    # It may mention it to say it must be omitted
    lower = prompt.lower()
    # A valid approach: the prompt says to omit sentiment, or simply doesn't instruct
    # the model to include it. We check there's no instruction to ADD sentiment.
    assert (
        "tighten" not in lower and "loosen" not in lower
    ), "Coverage prompt must not instruct model to emit tighten/loosen sentiment"


def test_coverage_finder_system_prompt_object_shape():
    prompt = ra.COVERAGE_FINDER_SYSTEM_PROMPT
    # Object shape must include summary, label, source_clauses, target_clauses, scope_note
    assert "summary" in prompt
    assert "source_clauses" in prompt
    assert "target_clauses" in prompt
    assert "scope_note" in prompt


# ---------------------------------------------------------------------------
# Criterion 2: _finder_per_pair default (labels="all") is unchanged
# ---------------------------------------------------------------------------


def test_finder_per_pair_default_uses_finder_system_prompt():
    """Default call (no labels arg) must use FINDER_SYSTEM_PROMPT, not the coverage one."""
    captured_system = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_system.append(system_prompt)
        return "[]"

    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_per_pair(_INDEX, _PAIR)

    assert len(captured_system) == 1
    assert captured_system[0] == ra.FINDER_SYSTEM_PROMPT


def test_finder_per_pair_labels_all_uses_finder_system_prompt():
    """Explicit labels='all' must also use FINDER_SYSTEM_PROMPT."""
    captured_system = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_system.append(system_prompt)
        return "[]"

    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_per_pair(_INDEX, _PAIR, labels="all")

    assert len(captured_system) == 1
    assert captured_system[0] == ra.FINDER_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Criterion 3: labels="same-topic" adds restriction to user message
# ---------------------------------------------------------------------------

_RESTRICTION = (
    "RESTRICTION: emit ONLY aligns-with, differs-on, or conflicts-with findings. "
    "If this pair is one-sided (coverage asymmetry), emit an empty array — "
    "the coverage pass handles those."
)


def test_finder_per_pair_same_topic_prepends_restriction():
    """labels='same-topic' must prepend the restriction clause to the user message."""
    captured_user = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_user.append(user)
        return "[]"

    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_per_pair(_INDEX, _PAIR, labels="same-topic")

    assert len(captured_user) == 1
    assert captured_user[0].startswith(_RESTRICTION), (
        f"Expected user message to start with restriction.\n"
        f"Got: {captured_user[0][:200]!r}"
    )


def test_finder_per_pair_same_topic_still_uses_finder_system_prompt():
    """labels='same-topic' must still use FINDER_SYSTEM_PROMPT (not coverage prompt)."""
    captured_system = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_system.append(system_prompt)
        return "[]"

    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_per_pair(_INDEX, _PAIR, labels="same-topic")

    assert captured_system[0] == ra.FINDER_SYSTEM_PROMPT


def test_finder_per_pair_default_does_not_include_restriction():
    """Default call must NOT include the restriction in the user message."""
    captured_user = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_user.append(user)
        return "[]"

    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_per_pair(_INDEX, _PAIR)

    assert (
        _RESTRICTION not in captured_user[0]
    ), "Default call must not include the same-topic restriction"
