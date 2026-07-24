"""Tests for Task 4 of Arm G: run_arm_g composite + CLI + trace/metadata wiring.

Acceptance criteria tested here:
1. run_arm_g exists, calls retrieve_cosine_only when signal=="cosine" and
   retrieve_bm25_only when signal=="bm25".
2. run_arm_g calls _finder_per_pair(..., labels="same-topic") for each retrieval
   candidate and never calls any critic.
3. run_arm_g calls _build_suppression then _finder_coverage_whole_doc.
4. run_arm_g merges same-topic + coverage raw output and runs _validate_candidates once.
5. run_arm_g returns a dict with all required keys: arm, wall_clock_seconds,
   finder_output, critic_output (empty list), supported, unsupported, validation,
   retrieval_candidates, suppression, coverage_finder_output.
6. ARM_RUNNERS contains key "G".
7. run_one writes suppression and coverage_finder_output to trace.json.
8. run_one writes same_topic_finding_count and coverage_finding_count to metadata.json.
9. --arm all dispatches to all arms including G.
10. --signal bm25 causes run_arm_g to use BM25 retrieval.

No network access: all LLM and retrieval calls are patched via unittest.mock.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

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

_FAKE_CANDIDATES = [
    {
        "source_anchor_id": "A1",
        "target_anchor_id": "B1",
        "matched_axis_source": "consent-management",
        "matched_axis_target": "user-consent",
        "similarity": 0.85,
        "signal": "cosine",
    },
]

_FAKE_AXES = {
    "A1": ["consent-management"],
    "A2": ["authentication"],
}

_FINDER_FINDING = {
    "summary": "Both require consent",
    "label": "aligns-with",
    "source_clauses": ["A1"],
    "target_clauses": ["B1"],
    "scope_note": "same topic",
}

_COVERAGE_FINDING = {
    "summary": "A requires consent revocation; B silent",
    "label": "goes-beyond",
    "source_clauses": ["A1"],
    "target_clauses": [],
    "scope_note": "coverage gap",
}


def _make_validated_output():
    """Return a typical _validate_candidates output triple."""
    supported = [_FINDER_FINDING]
    unsupported = []
    validation = {"resolved": 1, "unresolved": 0, "errors": []}
    return supported, unsupported, validation


# ---------------------------------------------------------------------------
# Criterion 1 + 10: run_arm_g calls correct retrieval function based on signal
# ---------------------------------------------------------------------------


def test_run_arm_g_uses_cosine_by_default():
    """run_arm_g must call retrieve_cosine_only when signal=='cosine' (the default)."""
    cosine_called = []

    def fake_retrieve_cosine(axes_a, axes_b):
        cosine_called.append(True)
        return _FAKE_CANDIDATES

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", side_effect=fake_retrieve_cosine),
        patch.object(
            ra, "retrieve_bm25_only", side_effect=AssertionError("should not be called")
        ),
        patch.object(ra, "_finder_per_pair", return_value=[]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b", signal="cosine")

    assert cosine_called, "retrieve_cosine_only must be called when signal=='cosine'"


def test_run_arm_g_uses_bm25_when_signal_bm25():
    """run_arm_g must call retrieve_bm25_only when signal=='bm25'."""
    bm25_called = []

    def fake_retrieve_bm25(axes_a, axes_b):
        bm25_called.append(True)
        return _FAKE_CANDIDATES

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(
            ra,
            "retrieve_cosine_only",
            side_effect=AssertionError("should not be called"),
        ),
        patch.object(ra, "retrieve_bm25_only", side_effect=fake_retrieve_bm25),
        patch.object(ra, "_finder_per_pair", return_value=[]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b", signal="bm25")

    assert bm25_called, "retrieve_bm25_only must be called when signal=='bm25'"


# ---------------------------------------------------------------------------
# Criterion 2: run_arm_g calls _finder_per_pair with labels="same-topic" and no critic
# ---------------------------------------------------------------------------


def test_run_arm_g_calls_finder_per_pair_with_same_topic_labels():
    """run_arm_g must call _finder_per_pair with labels='same-topic' for each candidate."""
    finder_calls = []

    def fake_finder_per_pair(anchor_index, pair, labels="all"):
        finder_calls.append({"pair": pair, "labels": labels})
        return [_FINDER_FINDING]

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", side_effect=fake_finder_per_pair),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert len(finder_calls) == len(
        _FAKE_CANDIDATES
    ), f"Expected {len(_FAKE_CANDIDATES)} finder calls, got {len(finder_calls)}"
    for fc in finder_calls:
        assert (
            fc["labels"] == "same-topic"
        ), f"Expected labels='same-topic', got labels={fc['labels']!r}"


def test_run_arm_g_never_calls_critic_per_pair():
    """run_arm_g must NOT call _critic_per_pair."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(ra, "_critic_per_pair") as mock_critic_pair,
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    mock_critic_pair.assert_not_called()


def test_run_arm_g_never_calls_critic_whole_doc():
    """run_arm_g must NOT call _critic_whole_doc."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(ra, "_critic_whole_doc") as mock_critic_whole,
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    mock_critic_whole.assert_not_called()


# ---------------------------------------------------------------------------
# Criterion 3: run_arm_g calls _build_suppression then _finder_coverage_whole_doc
# ---------------------------------------------------------------------------


def test_run_arm_g_calls_build_suppression():
    """run_arm_g must call _build_suppression with the retrieval candidates and finder output."""
    suppression_calls = []

    def fake_build_suppression(retrieval_candidates, same_topic_findings):
        suppression_calls.append(
            {
                "candidates": retrieval_candidates,
                "findings": same_topic_findings,
            }
        )
        return {"covered_pairs": [], "covered_topics": []}

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(ra, "_build_suppression", side_effect=fake_build_suppression),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert len(suppression_calls) == 1, "Must call _build_suppression exactly once"
    # Verify candidates passed
    assert suppression_calls[0]["candidates"] == _FAKE_CANDIDATES


def test_run_arm_g_calls_finder_coverage_whole_doc():
    """run_arm_g must call _finder_coverage_whole_doc with the suppression dict."""
    coverage_calls = []

    fake_suppression = {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": ["consent-management"],
    }

    def fake_coverage(anchor_index, doc_a, doc_b, suppression):
        coverage_calls.append(
            {
                "doc_a": doc_a,
                "doc_b": doc_b,
                "suppression": suppression,
            }
        )
        return [_COVERAGE_FINDING]

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(ra, "_build_suppression", return_value=fake_suppression),
        patch.object(ra, "_finder_coverage_whole_doc", side_effect=fake_coverage),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert len(coverage_calls) == 1, "Must call _finder_coverage_whole_doc exactly once"
    assert coverage_calls[0]["doc_a"] == "doc-a"
    assert coverage_calls[0]["doc_b"] == "doc-b"
    assert coverage_calls[0]["suppression"] == fake_suppression


# ---------------------------------------------------------------------------
# Criterion 4: run_arm_g merges outputs and calls _validate_candidates once
# ---------------------------------------------------------------------------


def test_run_arm_g_merges_same_topic_and_coverage_findings():
    """run_arm_g must merge same-topic and coverage findings before validating."""
    validate_calls = []

    def fake_validate(merged, clause_shim):
        validate_calls.append({"merged": merged})
        return _make_validated_output()

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(
            ra, "_finder_coverage_whole_doc", return_value=[_COVERAGE_FINDING]
        ),
        patch.object(ra, "_validate_candidates", side_effect=fake_validate),
    ):
        ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert len(validate_calls) == 1, "_validate_candidates must be called exactly once"
    merged = validate_calls[0]["merged"]
    # Must include both same-topic finding and coverage finding
    assert _FINDER_FINDING in merged, "Same-topic finding must be in merged list"
    assert _COVERAGE_FINDING in merged, "Coverage finding must be in merged list"


# ---------------------------------------------------------------------------
# Criterion 5: run_arm_g returns dict with all required keys
# ---------------------------------------------------------------------------


def test_run_arm_g_returns_required_keys():
    """run_arm_g must return a dict with all required keys."""
    required_keys = {
        "arm",
        "wall_clock_seconds",
        "finder_output",
        "critic_output",
        "supported",
        "unsupported",
        "validation",
        "retrieval_candidates",
        "suppression",
        "coverage_finder_output",
    }

    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(
            ra, "_finder_coverage_whole_doc", return_value=[_COVERAGE_FINDING]
        ),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        result = ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    missing = required_keys - set(result.keys())
    assert not missing, f"run_arm_g result missing keys: {missing}"


def test_run_arm_g_arm_key_is_G():
    """run_arm_g result must have arm == 'G'."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        result = ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert result["arm"] == "G", f"Expected arm='G', got arm={result['arm']!r}"


def test_run_arm_g_critic_output_is_empty_list():
    """run_arm_g result must have critic_output == [] (no critic)."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        result = ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert (
        result["critic_output"] == []
    ), f"critic_output must be empty list (no critic); got {result['critic_output']!r}"


def test_run_arm_g_retrieval_candidates_contains_stage1_output():
    """run_arm_g must store stage-1 candidates in result['retrieval_candidates']."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        result = ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert result["retrieval_candidates"] == _FAKE_CANDIDATES


def test_run_arm_g_finder_output_contains_same_topic_raw():
    """run_arm_g must store raw same-topic finder output in result['finder_output']."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[_FINDER_FINDING]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(ra, "_finder_coverage_whole_doc", return_value=[]),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        result = ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert (
        _FINDER_FINDING in result["finder_output"]
    ), "finder_output must contain same-topic finder raw output"


def test_run_arm_g_coverage_finder_output_key_present():
    """run_arm_g must store coverage_finder_output from stage 4."""
    with (
        patch.object(ra, "_load_axes", return_value=_FAKE_AXES),
        patch.object(ra, "retrieve_cosine_only", return_value=_FAKE_CANDIDATES),
        patch.object(ra, "_finder_per_pair", return_value=[]),
        patch.object(
            ra,
            "_build_suppression",
            return_value={"covered_pairs": [], "covered_topics": []},
        ),
        patch.object(
            ra, "_finder_coverage_whole_doc", return_value=[_COVERAGE_FINDING]
        ),
        patch.object(ra, "_validate_candidates", return_value=_make_validated_output()),
    ):
        result = ra.run_arm_g(_INDEX, "doc-a", "doc-b")

    assert result["coverage_finder_output"] == [_COVERAGE_FINDING]


# ---------------------------------------------------------------------------
# Criterion 6: ARM_RUNNERS contains key "G"
# ---------------------------------------------------------------------------


def test_arm_runners_contains_g():
    """ARM_RUNNERS must contain key 'G'."""
    assert (
        "G" in ra.ARM_RUNNERS
    ), f"ARM_RUNNERS must have key 'G'; current keys: {list(ra.ARM_RUNNERS)}"


def test_arm_runners_g_is_run_arm_g():
    """ARM_RUNNERS['G'] must be run_arm_g."""
    assert (
        ra.ARM_RUNNERS["G"] is ra.run_arm_g
    ), "ARM_RUNNERS['G'] must point to run_arm_g"


def test_arm_runners_existing_entries_unchanged():
    """ARM_RUNNERS must still contain all prior arms B/C/D/E/F."""
    for arm in ["B", "C", "D", "E", "F"]:
        assert arm in ra.ARM_RUNNERS, f"ARM_RUNNERS must still contain key '{arm}'"


# ---------------------------------------------------------------------------
# Criterion 7: run_one writes suppression and coverage_finder_output to trace.json
# ---------------------------------------------------------------------------


def _run_one_with_fake_result(result: dict, pair: str = "bis-ed") -> dict:
    """Run run_one with a patched ARM_RUNNERS result; return the written trace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)

        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(
                ra, "ARM_RUNNERS", {"G": lambda ai, da, db, sig="cosine": result}
            ),
            patch.object(ra, "PAIRS", {pair: ("doc-a", "doc-b")}),
        ):
            # _validate_candidates already ran inside run_arm_g; result has supported, etc.
            ra.run_one("G", pair, _INDEX, signal="cosine")

        trace_path = results_dir / "G" / pair / "trace.json"
        return json.loads(trace_path.read_text(encoding="utf-8"))


def _run_one_get_metadata(result: dict, pair: str = "bis-ed") -> dict:
    """Run run_one; return the written metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)

        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(
                ra, "ARM_RUNNERS", {"G": lambda ai, da, db, sig="cosine": result}
            ),
            patch.object(ra, "PAIRS", {pair: ("doc-a", "doc-b")}),
        ):
            ra.run_one("G", pair, _INDEX, signal="cosine")

        meta_path = results_dir / "G" / pair / "metadata.json"
        return json.loads(meta_path.read_text(encoding="utf-8"))


_FULL_ARM_G_RESULT = {
    "arm": "G",
    "wall_clock_seconds": 1.5,
    "finder_output": [_FINDER_FINDING],
    "critic_output": [],
    "supported": [_FINDER_FINDING],
    "unsupported": [],
    "validation": {"resolved": 1, "unresolved": 0, "errors": []},
    "retrieval_candidates": _FAKE_CANDIDATES,
    "suppression": {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": ["consent-management"],
    },
    "coverage_finder_output": [_COVERAGE_FINDING],
}


def test_run_one_writes_suppression_to_trace():
    """run_one must write 'suppression' field into trace.json."""
    trace = _run_one_with_fake_result(_FULL_ARM_G_RESULT)
    assert (
        "suppression" in trace
    ), f"trace.json must contain 'suppression' key; got keys: {list(trace)}"
    assert trace["suppression"] == _FULL_ARM_G_RESULT["suppression"]


def test_run_one_writes_coverage_finder_output_to_trace():
    """run_one must write 'coverage_finder_output' field into trace.json."""
    trace = _run_one_with_fake_result(_FULL_ARM_G_RESULT)
    assert (
        "coverage_finder_output" in trace
    ), f"trace.json must contain 'coverage_finder_output' key; got keys: {list(trace)}"
    assert (
        trace["coverage_finder_output"] == _FULL_ARM_G_RESULT["coverage_finder_output"]
    )


def test_run_one_trace_suppression_is_none_for_non_g_arms():
    """For non-G arms (no suppression key in result), trace.json suppression must be None."""
    non_g_result = {
        "arm": "C",
        "wall_clock_seconds": 1.0,
        "finder_output": [_FINDER_FINDING],
        "critic_output": [_FINDER_FINDING],
        "supported": [_FINDER_FINDING],
        "unsupported": [],
        "validation": {"resolved": 1, "unresolved": 0, "errors": []},
        "retrieval_candidates": _FAKE_CANDIDATES,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(ra, "ARM_RUNNERS", {"C": lambda ai, da, db: non_g_result}),
            patch.object(ra, "PAIRS", {"bis-ed": ("doc-a", "doc-b")}),
        ):
            ra.run_one("C", "bis-ed", _INDEX)

        trace = json.loads(
            (results_dir / "C" / "bis-ed" / "trace.json").read_text(encoding="utf-8")
        )

    assert "suppression" in trace, "trace.json must contain 'suppression' key"
    assert (
        trace["suppression"] is None
    ), f"suppression must be None for non-G arms; got {trace['suppression']!r}"
    assert (
        trace["coverage_finder_output"] is None
    ), f"coverage_finder_output must be None for non-G arms; got {trace['coverage_finder_output']!r}"


# ---------------------------------------------------------------------------
# Criterion 8: run_one writes same_topic_finding_count and coverage_finding_count to metadata.json
# ---------------------------------------------------------------------------


def test_run_one_writes_same_topic_finding_count_to_metadata():
    """run_one must write 'same_topic_finding_count' into metadata.json."""
    meta = _run_one_get_metadata(_FULL_ARM_G_RESULT)
    assert (
        "same_topic_finding_count" in meta
    ), f"metadata.json must contain 'same_topic_finding_count'; got keys: {list(meta)}"
    # finder_output has 1 item
    assert (
        meta["same_topic_finding_count"] == 1
    ), f"Expected same_topic_finding_count=1, got {meta['same_topic_finding_count']}"


def test_run_one_writes_coverage_finding_count_to_metadata():
    """run_one must write 'coverage_finding_count' into metadata.json."""
    meta = _run_one_get_metadata(_FULL_ARM_G_RESULT)
    assert (
        "coverage_finding_count" in meta
    ), f"metadata.json must contain 'coverage_finding_count'; got keys: {list(meta)}"
    # coverage_finder_output has 1 item
    assert (
        meta["coverage_finding_count"] == 1
    ), f"Expected coverage_finding_count=1, got {meta['coverage_finding_count']}"


def test_run_one_metadata_counts_zero_for_non_g_arms():
    """For non-G arms, same_topic_finding_count and coverage_finding_count must be 0."""
    non_g_result = {
        "arm": "C",
        "wall_clock_seconds": 1.0,
        "finder_output": [_FINDER_FINDING],
        "critic_output": [_FINDER_FINDING],
        "supported": [_FINDER_FINDING],
        "unsupported": [],
        "validation": {"resolved": 1, "unresolved": 0, "errors": []},
        "retrieval_candidates": _FAKE_CANDIDATES,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(ra, "ARM_RUNNERS", {"C": lambda ai, da, db: non_g_result}),
            patch.object(ra, "PAIRS", {"bis-ed": ("doc-a", "doc-b")}),
        ):
            ra.run_one("C", "bis-ed", _INDEX)

        meta = json.loads(
            (results_dir / "C" / "bis-ed" / "metadata.json").read_text(encoding="utf-8")
        )

    assert (
        meta["same_topic_finding_count"] == 0
    ), f"Expected 0 for non-G arm, got {meta['same_topic_finding_count']}"
    assert (
        meta["coverage_finding_count"] == 0
    ), f"Expected 0 for non-G arm, got {meta['coverage_finding_count']}"


# ---------------------------------------------------------------------------
# Criterion 9: --arm all dispatches to all arms including G
# ---------------------------------------------------------------------------


def test_arm_all_includes_g():
    """When --arm all is passed, arms list must include 'G'."""
    # Simulate what main() does: list(ARM_RUNNERS) when args.arm == 'all'
    # The spec says: arms = list(ARM_RUNNERS) if args.arm == "all" else [args.arm]
    # So check that ARM_RUNNERS includes 'G' and the logic would dispatch to all
    arms_when_all = list(ra.ARM_RUNNERS)
    assert (
        "G" in arms_when_all
    ), f"'G' must be in list(ARM_RUNNERS) for --arm all to include it; got {arms_when_all}"


def test_arm_all_includes_all_expected_arms():
    """When --arm all, all arms B/C/D/E/F/G must be dispatched."""
    expected = {"B", "C", "D", "E", "F", "G"}
    arms_when_all = set(ra.ARM_RUNNERS)
    missing = expected - arms_when_all
    assert not missing, f"ARM_RUNNERS is missing arms: {missing}"


# ---------------------------------------------------------------------------
# Criterion 10 (redundant with criterion 1, but explicit about --signal bm25)
# Verify signal parameter passes through run_one → run_arm_g
# ---------------------------------------------------------------------------


def test_run_one_passes_signal_to_arm_g():
    """run_one(arm='G', signal='bm25') must pass signal='bm25' to run_arm_g."""
    received_signal = []

    def fake_run_arm_g(anchor_index, doc_a, doc_b, signal="cosine"):
        received_signal.append(signal)
        return _FULL_ARM_G_RESULT

    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(ra, "ARM_RUNNERS", {"G": fake_run_arm_g}),
            patch.object(ra, "PAIRS", {"bis-ed": ("doc-a", "doc-b")}),
        ):
            ra.run_one("G", "bis-ed", _INDEX, signal="bm25")

    assert received_signal == [
        "bm25"
    ], f"run_one must pass signal='bm25' to run_arm_g; got {received_signal}"


def test_run_one_default_signal_is_cosine():
    """run_one without signal arg must default to signal='cosine'."""
    received_signal = []

    def fake_run_arm_g(anchor_index, doc_a, doc_b, signal="cosine"):
        received_signal.append(signal)
        return _FULL_ARM_G_RESULT

    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(ra, "ARM_RUNNERS", {"G": fake_run_arm_g}),
            patch.object(ra, "PAIRS", {"bis-ed": ("doc-a", "doc-b")}),
        ):
            # No signal arg — should default to cosine
            ra.run_one("G", "bis-ed", _INDEX)

    assert received_signal == [
        "cosine"
    ], f"run_one default signal must be 'cosine'; got {received_signal}"


def test_run_one_non_g_arm_does_not_pass_signal():
    """run_one with a non-G arm must call the runner without signal kwarg."""
    received_args = []

    def fake_run_arm_c(anchor_index, doc_a, doc_b):
        received_args.append(True)
        return {
            "arm": "C",
            "wall_clock_seconds": 1.0,
            "finder_output": [],
            "critic_output": [],
            "supported": [],
            "unsupported": [],
            "validation": {},
            "retrieval_candidates": [],
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(ra, "ARM_RUNNERS", {"C": fake_run_arm_c}),
            patch.object(ra, "PAIRS", {"bis-ed": ("doc-a", "doc-b")}),
        ):
            ra.run_one("C", "bis-ed", _INDEX, signal="bm25")

    assert received_args, "run_arm_c must still be called for arm='C'"
