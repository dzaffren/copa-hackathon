"""Tests for Task 5 of Arm G: coverage_quality_notes in metadata.json.

Acceptance criteria tested here:
1. metadata.json for an Arm G run contains 'coverage_quality_notes' as a list.
2. Each note has 'summary', 'label', 'single_sided', 'redundant'.
3. A goes-beyond finding with non-empty source_clauses and empty target_clauses
   has single_sided == True.
4. A silent-on finding with empty source_clauses and non-empty target_clauses
   has single_sided == True.
5. A finding whose summary contains a covered topic has redundant == True.
6. For non-G arms, coverage_quality_notes is [] in metadata.json.

No network access: all LLM and retrieval calls are patched via unittest.mock.
"""

import json
import sys
import tempfile
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

_GOES_BEYOND_FINDING = {
    "summary": "A requires consent revocation; B silent on revocation",
    "label": "goes-beyond",
    "source_clauses": ["A1"],
    "target_clauses": [],
    "scope_note": "coverage gap",
}

_SILENT_ON_FINDING = {
    "summary": "B requires multi-factor authentication; A silent on MFA",
    "label": "silent-on",
    "source_clauses": [],
    "target_clauses": ["B2"],
    "scope_note": "coverage gap",
}

_ALIGNS_WITH_FINDING = {
    "summary": "Both require consent",
    "label": "aligns-with",
    "source_clauses": ["A1"],
    "target_clauses": ["B1"],
    "scope_note": "same topic",
}


def _run_one_get_metadata(result: dict, pair: str = "bis-ed") -> dict:
    """Run run_one; return the written metadata."""
    arm = result["arm"]
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)

        if arm == "G":
            runner = {arm: lambda ai, da, db, sig="cosine": result}
        else:
            runner = {arm: lambda ai, da, db: result}

        with (
            patch.object(ra, "RESULTS_DIR", results_dir),
            patch.object(ra, "ARM_RUNNERS", runner),
            patch.object(ra, "PAIRS", {pair: ("doc-a", "doc-b")}),
        ):
            ra.run_one(arm, pair, _INDEX, signal="cosine")

        meta_path = results_dir / arm / pair / "metadata.json"
        return json.loads(meta_path.read_text(encoding="utf-8"))


_FULL_ARM_G_RESULT = {
    "arm": "G",
    "wall_clock_seconds": 1.5,
    "finder_output": [_ALIGNS_WITH_FINDING],
    "critic_output": [],
    "supported": [_ALIGNS_WITH_FINDING],
    "unsupported": [],
    "validation": {"resolved": 1, "unresolved": 0, "errors": []},
    "retrieval_candidates": [
        {
            "source_anchor_id": "A1",
            "target_anchor_id": "B1",
            "matched_axis_source": "consent-management",
            "matched_axis_target": "user-consent",
            "similarity": 0.85,
            "signal": "cosine",
        }
    ],
    "suppression": {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": ["consent-management"],
    },
    "coverage_finder_output": [_GOES_BEYOND_FINDING, _SILENT_ON_FINDING],
}


# ---------------------------------------------------------------------------
# Criterion 1: metadata.json for Arm G contains coverage_quality_notes as a list
# ---------------------------------------------------------------------------


def test_metadata_arm_g_contains_coverage_quality_notes():
    """metadata.json for an Arm G run must contain 'coverage_quality_notes' as a list."""
    meta = _run_one_get_metadata(_FULL_ARM_G_RESULT)
    assert (
        "coverage_quality_notes" in meta
    ), f"metadata.json must contain 'coverage_quality_notes'; got keys: {list(meta)}"
    assert isinstance(
        meta["coverage_quality_notes"], list
    ), f"coverage_quality_notes must be a list; got {type(meta['coverage_quality_notes']).__name__}"


def test_metadata_arm_g_coverage_quality_notes_length_matches_coverage_findings():
    """coverage_quality_notes length must equal the number of coverage_finder_output items."""
    meta = _run_one_get_metadata(_FULL_ARM_G_RESULT)
    expected_count = len(_FULL_ARM_G_RESULT["coverage_finder_output"])
    assert (
        len(meta["coverage_quality_notes"]) == expected_count
    ), f"Expected {expected_count} notes, got {len(meta['coverage_quality_notes'])}"


# ---------------------------------------------------------------------------
# Criterion 2: Each note has summary, label, single_sided, redundant
# ---------------------------------------------------------------------------


def test_metadata_coverage_quality_notes_have_required_keys():
    """Each note in coverage_quality_notes must have summary, label, single_sided, redundant."""
    meta = _run_one_get_metadata(_FULL_ARM_G_RESULT)
    required = {"summary", "label", "single_sided", "redundant"}
    for i, note in enumerate(meta["coverage_quality_notes"]):
        missing = required - set(note.keys())
        assert (
            not missing
        ), f"Note {i} is missing keys: {missing}; got keys: {list(note)}"


# ---------------------------------------------------------------------------
# Criterion 3: goes-beyond with non-empty source, empty target → single_sided True
# ---------------------------------------------------------------------------


def test_is_single_sided_goes_beyond_non_empty_source_empty_target():
    """_is_single_sided must return True for goes-beyond with source_clauses non-empty and target_clauses empty."""
    finding = {
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": [],
        "summary": "A covers revocation; B silent",
    }
    assert ra._is_single_sided(finding) is True


def test_metadata_goes_beyond_finding_has_single_sided_true():
    """A goes-beyond finding with non-empty source_clauses and empty target_clauses must have single_sided: true."""
    result = {
        **_FULL_ARM_G_RESULT,
        "coverage_finder_output": [_GOES_BEYOND_FINDING],
    }
    meta = _run_one_get_metadata(result)
    note = meta["coverage_quality_notes"][0]
    assert note["single_sided"] is True, (
        f"goes-beyond finding with non-empty source_clauses and empty target_clauses "
        f"must have single_sided=True; got {note['single_sided']!r}"
    )


def test_is_single_sided_goes_beyond_both_sides_not_single_sided():
    """_is_single_sided must return False for goes-beyond when both sides have clauses."""
    finding = {
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": ["B1"],
        "summary": "...",
    }
    assert ra._is_single_sided(finding) is False


# ---------------------------------------------------------------------------
# Criterion 4: silent-on with empty source, non-empty target → single_sided True
# ---------------------------------------------------------------------------


def test_is_single_sided_silent_on_empty_source_non_empty_target():
    """_is_single_sided must return True for silent-on with source_clauses empty and target_clauses non-empty."""
    finding = {
        "label": "silent-on",
        "source_clauses": [],
        "target_clauses": ["B2"],
        "summary": "B covers MFA; A silent",
    }
    assert ra._is_single_sided(finding) is True


def test_metadata_silent_on_finding_has_single_sided_true():
    """A silent-on finding with empty source_clauses and non-empty target_clauses must have single_sided: true."""
    result = {
        **_FULL_ARM_G_RESULT,
        "coverage_finder_output": [_SILENT_ON_FINDING],
    }
    meta = _run_one_get_metadata(result)
    note = meta["coverage_quality_notes"][0]
    assert note["single_sided"] is True, (
        f"silent-on finding with empty source_clauses and non-empty target_clauses "
        f"must have single_sided=True; got {note['single_sided']!r}"
    )


def test_is_single_sided_aligns_with_is_false():
    """_is_single_sided must return False for aligns-with regardless of clauses."""
    finding = {
        "label": "aligns-with",
        "source_clauses": ["A1"],
        "target_clauses": [],
        "summary": "...",
    }
    assert ra._is_single_sided(finding) is False


# ---------------------------------------------------------------------------
# Criterion 5: finding summary contains covered topic → redundant True
# ---------------------------------------------------------------------------


def test_is_redundant_summary_contains_covered_topic():
    """_is_redundant must return True when the finding summary contains a covered topic."""
    finding = {
        "summary": "A covers consent-management scope; B has no provision",
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": [],
    }
    suppression = {
        "covered_pairs": [],
        "covered_topics": ["consent-management"],
    }
    assert ra._is_redundant(finding, suppression) is True


def test_is_redundant_summary_topic_case_insensitive():
    """_is_redundant topic match must be case-insensitive."""
    finding = {
        "summary": "A covers CONSENT-MANAGEMENT scope; B silent",
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": [],
    }
    suppression = {
        "covered_pairs": [],
        "covered_topics": ["consent-management"],
    }
    assert ra._is_redundant(finding, suppression) is True


def test_is_redundant_clause_in_covered_pairs():
    """_is_redundant must return True when any cited anchor appears in covered_pairs."""
    finding = {
        "summary": "some other topic",
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": [],
    }
    suppression = {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": [],
    }
    assert ra._is_redundant(finding, suppression) is True


def test_is_redundant_no_match_returns_false():
    """_is_redundant must return False when no topic or pair matches."""
    finding = {
        "summary": "B covers multi-factor authentication; A silent",
        "label": "silent-on",
        "source_clauses": [],
        "target_clauses": ["B2"],
    }
    suppression = {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": ["consent-management"],
    }
    assert ra._is_redundant(finding, suppression) is False


def test_metadata_coverage_note_redundant_true_when_topic_in_summary():
    """metadata.json note must have redundant=True when finding summary contains a covered topic."""
    # The goes-beyond finding summary contains "revocation"; covered topic is "revocation"
    finding_with_covered_topic = {
        "summary": "A requires consent revocation; B silent on revocation",
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": [],
        "scope_note": "coverage gap",
    }
    suppression = {
        "covered_pairs": [],
        "covered_topics": ["revocation"],
    }
    result = {
        **_FULL_ARM_G_RESULT,
        "coverage_finder_output": [finding_with_covered_topic],
        "suppression": suppression,
    }
    meta = _run_one_get_metadata(result)
    note = meta["coverage_quality_notes"][0]
    assert note["redundant"] is True, (
        f"note with summary containing a covered topic must have redundant=True; "
        f"got {note['redundant']!r}"
    )


# ---------------------------------------------------------------------------
# Criterion 6: For non-G arms, coverage_quality_notes is [] in metadata.json
# ---------------------------------------------------------------------------


def test_metadata_non_g_arm_coverage_quality_notes_is_empty_list():
    """For non-G arms, coverage_quality_notes must be [] in metadata.json."""
    non_g_result = {
        "arm": "C",
        "wall_clock_seconds": 1.0,
        "finder_output": [_ALIGNS_WITH_FINDING],
        "critic_output": [_ALIGNS_WITH_FINDING],
        "supported": [_ALIGNS_WITH_FINDING],
        "unsupported": [],
        "validation": {"resolved": 1, "unresolved": 0, "errors": []},
        "retrieval_candidates": [
            {
                "source_anchor_id": "A1",
                "target_anchor_id": "B1",
                "matched_axis_source": "consent-management",
                "matched_axis_target": "user-consent",
                "similarity": 0.85,
                "signal": "cosine",
            }
        ],
    }
    meta = _run_one_get_metadata(non_g_result)
    assert (
        "coverage_quality_notes" in meta
    ), f"metadata.json must contain 'coverage_quality_notes' even for non-G; got keys: {list(meta)}"
    assert meta["coverage_quality_notes"] == [], (
        f"For non-G arms, coverage_quality_notes must be []; "
        f"got {meta['coverage_quality_notes']!r}"
    )


# ---------------------------------------------------------------------------
# Additional unit tests for _is_single_sided and _is_redundant edge cases
# ---------------------------------------------------------------------------


def test_is_single_sided_goes_beyond_empty_source_returns_false():
    """_is_single_sided must return False for goes-beyond with empty source_clauses."""
    finding = {
        "label": "goes-beyond",
        "source_clauses": [],
        "target_clauses": [],
        "summary": "...",
    }
    assert ra._is_single_sided(finding) is False


def test_is_single_sided_silent_on_both_empty_returns_false():
    """_is_single_sided must return False for silent-on with both clause lists empty."""
    finding = {
        "label": "silent-on",
        "source_clauses": [],
        "target_clauses": [],
        "summary": "...",
    }
    assert ra._is_single_sided(finding) is False


def test_is_redundant_empty_suppression_returns_false():
    """_is_redundant must return False when suppression has no topics and no pairs."""
    finding = {
        "summary": "A covers consent-management; B silent",
        "label": "goes-beyond",
        "source_clauses": ["A1"],
        "target_clauses": [],
    }
    suppression: dict = {"covered_pairs": [], "covered_topics": []}
    assert ra._is_redundant(finding, suppression) is False


def test_is_redundant_empty_finding_clauses_no_match():
    """_is_redundant must not crash when finding has no clauses."""
    finding = {
        "summary": "some gap",
        "label": "silent-on",
        "source_clauses": [],
        "target_clauses": [],
    }
    suppression = {
        "covered_pairs": ["A1 × B1"],
        "covered_topics": ["consent"],
    }
    # No clauses to match, and summary doesn't contain "consent" exactly
    assert ra._is_redundant(finding, suppression) is False


def test_coverage_quality_notes_summary_copied_from_finding():
    """Each note's 'summary' must match the finding's summary."""
    result = {
        **_FULL_ARM_G_RESULT,
        "coverage_finder_output": [_GOES_BEYOND_FINDING],
    }
    meta = _run_one_get_metadata(result)
    note = meta["coverage_quality_notes"][0]
    assert note["summary"] == _GOES_BEYOND_FINDING["summary"], (
        f"note summary must match finding summary; "
        f"expected {_GOES_BEYOND_FINDING['summary']!r}, got {note['summary']!r}"
    )


def test_coverage_quality_notes_label_copied_from_finding():
    """Each note's 'label' must match the finding's label."""
    result = {
        **_FULL_ARM_G_RESULT,
        "coverage_finder_output": [_GOES_BEYOND_FINDING],
    }
    meta = _run_one_get_metadata(result)
    note = meta["coverage_quality_notes"][0]
    assert note["label"] == _GOES_BEYOND_FINDING["label"], (
        f"note label must match finding label; "
        f"expected {_GOES_BEYOND_FINDING['label']!r}, got {note['label']!r}"
    )
