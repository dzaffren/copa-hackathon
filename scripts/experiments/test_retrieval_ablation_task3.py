"""Tests for Task 3 of Arm G: _build_suppression and _finder_coverage_whole_doc.

These tests exercise only the observable surface specified by Task 3:
1. _build_suppression(retrieval_candidates, same_topic_findings) returns a dict
   with 'covered_pairs' and 'covered_topics' fields.
2. A retrieval candidate whose source_anchor_id does not appear in any surviving
   finding's source_clauses does NOT contribute to the suppression set.
3. _finder_coverage_whole_doc builds a user message with both doc blocks + the
   suppression block, calls call_chat with COVERAGE_FINDER_SYSTEM_PROMPT, and
   returns the parsed list.
4. When covered_topics is empty, no 'TOPICS ALREADY COVERED' block appears in
   the user message.

No network access: call_chat is patched via unittest.mock.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.experiments.retrieval_ablation as ra

# ---------------------------------------------------------------------------
# Helpers / fixtures
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


_ANCHORS = [
    _make_anchor("A1", "doc-a", "A requires explicit consent from data subjects."),
    _make_anchor("A2", "doc-a", "A requires authentication of users."),
    _make_anchor("B1", "doc-b", "B requires user consent for data processing."),
    _make_anchor("B2", "doc-b", "B requires multi-factor authentication."),
]

_INDEX = _FakeAnchorIndex(_ANCHORS)

# Retrieval candidates with axis metadata
_CANDIDATES = [
    {
        "source_anchor_id": "A1",
        "target_anchor_id": "B1",
        "matched_axis_source": "consent-management",
        "matched_axis_target": "user-consent",
        "similarity": 0.85,
        "signal": "cosine",
    },
    {
        "source_anchor_id": "A2",
        "target_anchor_id": "B2",
        "matched_axis_source": "authentication",
        "matched_axis_target": "identity-verification",
        "similarity": 0.80,
        "signal": "cosine",
    },
]


# ---------------------------------------------------------------------------
# Criterion 1: _build_suppression returns correct dict shape
# ---------------------------------------------------------------------------


def test_build_suppression_returns_dict_with_required_keys():
    """_build_suppression must return a dict with 'covered_pairs' and 'covered_topics'."""
    # Findings where A1 produced a same-topic finding
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    assert isinstance(result, dict), "result must be a dict"
    assert "covered_pairs" in result, "result must have 'covered_pairs'"
    assert "covered_topics" in result, "result must have 'covered_topics'"


def test_build_suppression_covered_pairs_are_strings():
    """covered_pairs must be a list of 'A × B' strings."""
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    assert isinstance(result["covered_pairs"], list)
    for item in result["covered_pairs"]:
        assert isinstance(
            item, str
        ), f"covered_pairs items must be strings, got {type(item)}"
        assert (
            " × " in item
        ), f"covered_pairs items must use ' × ' separator, got {item!r}"


def test_build_suppression_covered_pairs_contain_matched_anchor_pair():
    """The A1×B1 candidate that produced a finding must appear in covered_pairs."""
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    assert (
        "A1 × B1" in result["covered_pairs"]
    ), f"Expected 'A1 × B1' in covered_pairs, got {result['covered_pairs']}"


def test_build_suppression_covered_topics_sorted():
    """covered_topics must be a sorted list of unique axis strings."""
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    assert isinstance(result["covered_topics"], list)
    assert result["covered_topics"] == sorted(
        result["covered_topics"]
    ), "covered_topics must be sorted"


def test_build_suppression_covered_topics_includes_axes_of_matched_candidates():
    """covered_topics must include matched_axis_source + matched_axis_target for matched pairs."""
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    # A1 is in source_clauses of the finding — candidate A1×B1 should be covered
    # Its axes are "consent-management" and "user-consent"
    assert (
        "consent-management" in result["covered_topics"]
    ), f"Expected 'consent-management' in covered_topics, got {result['covered_topics']}"
    assert (
        "user-consent" in result["covered_topics"]
    ), f"Expected 'user-consent' in covered_topics, got {result['covered_topics']}"


# ---------------------------------------------------------------------------
# Criterion 2: candidates with no surviving finding do NOT contribute
# ---------------------------------------------------------------------------


def test_build_suppression_unmatched_candidate_excluded():
    """A candidate whose source_anchor_id appears in no finding's source_clauses is excluded."""
    # Only finding is for A1, not A2
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    # A2×B2 should NOT be in covered_pairs (no finding for A2)
    assert (
        "A2 × B2" not in result["covered_pairs"]
    ), f"A2×B2 should not be covered, got {result['covered_pairs']}"
    # authentication / identity-verification axes should NOT be covered
    assert (
        "authentication" not in result["covered_topics"]
    ), f"'authentication' should not be in covered_topics when A2 produced no finding"
    assert (
        "identity-verification" not in result["covered_topics"]
    ), f"'identity-verification' should not be in covered_topics when A2 produced no finding"


def test_build_suppression_empty_findings_returns_empty_sets():
    """If there are no surviving findings, both covered_pairs and covered_topics must be empty."""
    result = ra._build_suppression(_CANDIDATES, [])
    assert (
        result["covered_pairs"] == []
    ), f"Expected empty list, got {result['covered_pairs']}"
    assert (
        result["covered_topics"] == []
    ), f"Expected empty list, got {result['covered_topics']}"


def test_build_suppression_empty_candidates_returns_empty_sets():
    """If there are no retrieval candidates, both fields must be empty."""
    findings = [
        {
            "summary": "Both require consent",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        }
    ]
    result = ra._build_suppression([], findings)
    assert result["covered_pairs"] == []
    assert result["covered_topics"] == []


def test_build_suppression_multiple_findings_same_candidate_deduplicated():
    """Multiple findings referencing the same candidate must not cause duplicate topics."""
    findings = [
        {
            "summary": "Consent finding 1",
            "label": "aligns-with",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        },
        {
            "summary": "Consent finding 2",
            "label": "differs-on",
            "source_clauses": ["A1"],
            "target_clauses": ["B1"],
        },
    ]
    result = ra._build_suppression(_CANDIDATES, findings)
    # covered_topics must be unique (no duplicates)
    assert len(result["covered_topics"]) == len(
        set(result["covered_topics"])
    ), "covered_topics must not contain duplicates"
    # covered_pairs must be unique
    assert len(result["covered_pairs"]) == len(
        set(result["covered_pairs"])
    ), "covered_pairs must not contain duplicates"


# ---------------------------------------------------------------------------
# Criterion 3: _finder_coverage_whole_doc calls call_chat with COVERAGE_FINDER_SYSTEM_PROMPT
# ---------------------------------------------------------------------------


def test_finder_coverage_whole_doc_uses_coverage_system_prompt():
    """_finder_coverage_whole_doc must call call_chat with COVERAGE_FINDER_SYSTEM_PROMPT."""
    captured_system = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_system.append(system_prompt)
        return "[]"

    suppression = {"covered_pairs": [], "covered_topics": []}
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    assert len(captured_system) == 1
    assert (
        captured_system[0] == ra.COVERAGE_FINDER_SYSTEM_PROMPT
    ), "Must use COVERAGE_FINDER_SYSTEM_PROMPT, not FINDER_SYSTEM_PROMPT"


def test_finder_coverage_whole_doc_includes_doc_a_block():
    """User message must include doc-a's anchor content."""
    captured_user = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_user.append(user)
        return "[]"

    suppression = {"covered_pairs": [], "covered_topics": []}
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    assert len(captured_user) == 1
    # Must include doc-a's anchors
    assert "doc-a" in captured_user[0], "User message must contain doc-a reference"
    assert (
        "A requires explicit consent" in captured_user[0]
    ), "User message must contain doc-a anchor text"


def test_finder_coverage_whole_doc_includes_doc_b_block():
    """User message must include doc-b's anchor content."""
    captured_user = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_user.append(user)
        return "[]"

    suppression = {"covered_pairs": [], "covered_topics": []}
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    assert "doc-b" in captured_user[0], "User message must contain doc-b reference"
    assert (
        "B requires user consent" in captured_user[0]
    ), "User message must contain doc-b anchor text"


def test_finder_coverage_whole_doc_returns_list():
    """_finder_coverage_whole_doc must return a list."""
    with patch.object(ra, "call_chat", return_value="[]"):
        result = ra._finder_coverage_whole_doc(
            _INDEX, "doc-a", "doc-b", {"covered_pairs": [], "covered_topics": []}
        )
    assert isinstance(result, list)


def test_finder_coverage_whole_doc_returns_parsed_findings():
    """_finder_coverage_whole_doc must return the parsed JSON list from call_chat."""
    fake_response = '[{"summary": "test", "label": "silent-on", "source_clauses": [], "target_clauses": ["B1"], "scope_note": "x"}]'

    with patch.object(ra, "call_chat", return_value=fake_response):
        result = ra._finder_coverage_whole_doc(
            _INDEX, "doc-a", "doc-b", {"covered_pairs": [], "covered_topics": []}
        )

    assert len(result) == 1
    assert result[0]["label"] == "silent-on"


def test_finder_coverage_whole_doc_raises_on_non_list_response():
    """_finder_coverage_whole_doc must raise LLMResponseError if response is not a list."""
    from engine.llm import LLMResponseError

    # Return a JSON object instead of an array
    with patch.object(ra, "call_chat", return_value='{"summary": "not a list"}'):
        with pytest.raises(LLMResponseError):
            ra._finder_coverage_whole_doc(
                _INDEX, "doc-a", "doc-b", {"covered_pairs": [], "covered_topics": []}
            )


def test_finder_coverage_whole_doc_uses_max_tokens_16384():
    """_finder_coverage_whole_doc must call call_chat with max_tokens=16384."""
    captured_kwargs = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_kwargs.append({"max_tokens": max_tokens})
        return "[]"

    suppression = {"covered_pairs": [], "covered_topics": []}
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    assert (
        captured_kwargs[0]["max_tokens"] == 16384
    ), f"Expected max_tokens=16384, got {captured_kwargs[0]['max_tokens']}"


# ---------------------------------------------------------------------------
# Criterion 4: suppression block only appears when covered_topics is non-empty
# ---------------------------------------------------------------------------


def test_finder_coverage_whole_doc_suppression_block_when_topics_present():
    """When covered_topics is non-empty, user message must include TOPICS ALREADY COVERED block."""
    captured_user = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_user.append(user)
        return "[]"

    suppression = {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": ["consent-management", "user-consent"],
    }
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    assert (
        "TOPICS ALREADY COVERED" in captured_user[0]
    ), "User message must include 'TOPICS ALREADY COVERED' block when covered_topics is non-empty"
    assert (
        "consent-management" in captured_user[0]
    ), "User message must list the covered topics"
    assert (
        "user-consent" in captured_user[0]
    ), "User message must list the covered topics"


def test_finder_coverage_whole_doc_no_suppression_block_when_topics_empty():
    """When covered_topics is empty, user message must NOT include TOPICS ALREADY COVERED block."""
    captured_user = []

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        captured_user.append(user)
        return "[]"

    suppression = {"covered_pairs": [], "covered_topics": []}
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    assert (
        "TOPICS ALREADY COVERED" not in captured_user[0]
    ), "User message must NOT include 'TOPICS ALREADY COVERED' block when covered_topics is empty"


# ---------------------------------------------------------------------------
# Criterion 5: no critic call anywhere in coverage functions
# ---------------------------------------------------------------------------


def test_finder_coverage_whole_doc_does_not_call_critic():
    """_finder_coverage_whole_doc must NOT call _critic_per_pair or _critic_whole_doc."""
    call_count = [0]

    def fake_call_chat(deployment, system_prompt, user, max_tokens):
        call_count[0] += 1
        return "[]"

    suppression = {"covered_pairs": [], "covered_topics": []}
    with patch.object(ra, "call_chat", side_effect=fake_call_chat):
        with patch.object(ra, "_critic_per_pair") as mock_critic_pair:
            with patch.object(ra, "_critic_whole_doc") as mock_critic_whole:
                ra._finder_coverage_whole_doc(_INDEX, "doc-a", "doc-b", suppression)

    mock_critic_pair.assert_not_called()
    mock_critic_whole.assert_not_called()
    # Only ONE call_chat call (the finder, no critic)
    assert call_count[0] == 1, f"Expected exactly 1 call_chat call, got {call_count[0]}"
