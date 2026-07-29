"""Unit tests for Arm G's phrasing enforcement and blank-anchor skip.

Covers the code layer behind
`docs/specs/plain-language-finding-explanations/spec.md`: the finder prompts ASK
for a plain short summary, but a live A/B measured roughly 1-in-3 summaries still
over cap, so `enforce_phrasing` makes the cap deterministic. The governing
constraint is that a finding is NEVER dropped for phrasing — losing a real
linkage over cosmetics would be a correctness regression.

Also covers the blank-anchor skip in stage 1: 14 anchors in the demo workstream
carry empty text, and sending those to the extraction model produced prose
("I don't see the anchor text") that burned all three retries, 3 wasted calls
each, before being dropped from retrieval anyway.

No network: the extraction test injects a call-counting fake deployment via
monkeypatched `_extract_axes_for_anchor`.
"""

import pytest

from engine import arm_g


# --- enforce_phrasing -------------------------------------------------------


def test_summary_within_cap_is_untouched() -> None:
    findings = [{"summary": "The draft requires board oversight; the BIS paper does not."}]
    out, actions = arm_g.enforce_phrasing(findings)
    assert out[0]["summary"] == findings[0]["summary"]
    assert actions == []


def test_over_cap_summary_is_reduced_to_first_sentence() -> None:
    long_summary = (
        "The draft requires a tested exit plan for every critical provider. "
        "The BCBS principles expect dependency management but stop short of "
        "requiring any tested exit plan per provider anywhere in the text."
    )
    out, actions = arm_g.enforce_phrasing([{"summary": long_summary}])
    assert out[0]["summary"] == (
        "The draft requires a tested exit plan for every critical provider."
    )
    assert len(actions) == 1
    assert actions[0]["action"] == "reduced_to_first_sentence"
    assert actions[0]["field"] == "summary"
    assert actions[0]["words_after"] <= arm_g.SUMMARY_MAX_WORDS
    assert actions[0]["words_before"] > arm_g.SUMMARY_MAX_WORDS


def test_unrescuable_summary_is_kept_not_mangled() -> None:
    """A single over-long sentence has no first-sentence rescue: keep it whole.

    Truncating mid-sentence would produce a worse artifact than an honest
    over-cap report, and dropping the finding would lose a real linkage.
    """
    one_sentence = " ".join(["word"] * 40)
    out, actions = arm_g.enforce_phrasing([{"summary": one_sentence}])
    assert out[0]["summary"] == one_sentence
    assert len(actions) == 1
    assert actions[0]["action"] == "over_cap_kept"
    assert actions[0]["words_before"] == actions[0]["words_after"] == 40


def test_findings_are_never_dropped_for_phrasing() -> None:
    findings = [
        {"summary": "Short and fine."},
        {"summary": " ".join(["word"] * 50)},
        {"summary": "First sentence is fine. " + " ".join(["word"] * 40)},
    ]
    out, _ = arm_g.enforce_phrasing(findings)
    assert len(out) == len(findings)


def test_scope_note_has_its_own_larger_cap() -> None:
    """A 25-word scope_note is within its 30-word cap even though it exceeds
    the 20-word summary cap."""
    note = " ".join(["word"] * 25)
    out, actions = arm_g.enforce_phrasing([{"summary": "Fine.", "scope_note": note}])
    assert out[0]["scope_note"] == note
    assert actions == []


def test_over_cap_scope_note_is_reduced() -> None:
    note = (
        "The BIS paper has no provision assigning oversight duties to a board. "
        + " ".join(["padding"] * 40)
    )
    out, actions = arm_g.enforce_phrasing([{"summary": "Fine.", "scope_note": note}])
    assert out[0]["scope_note"] == (
        "The BIS paper has no provision assigning oversight duties to a board."
    )
    assert actions[0]["field"] == "scope_note"


@pytest.mark.parametrize("blank", [None, "", "   ", "\n"])
def test_blank_or_missing_fields_are_ignored(blank) -> None:
    out, actions = arm_g.enforce_phrasing([{"summary": "Fine.", "scope_note": blank}])
    assert actions == []
    assert out[0]["scope_note"] == blank


def test_other_fields_are_preserved() -> None:
    finding = {
        "summary": " ".join(["word"] * 30),
        "label": "differs-on",
        "sentiment": "tighten",
        "source_clauses": ["OpRes PD 4.7"],
        "target_clauses": ["BCBS OpRes Principle 7"],
    }
    out, _ = arm_g.enforce_phrasing([finding])
    for key in ("label", "sentiment", "source_clauses", "target_clauses"):
        assert out[0][key] == finding[key]


def test_input_findings_are_not_mutated() -> None:
    original = {"summary": "A fine first sentence. " + " ".join(["word"] * 40)}
    snapshot = dict(original)
    arm_g.enforce_phrasing([original])
    assert original == snapshot


# --- blank-anchor skip in stage 1 -------------------------------------------


class _FakeIndex:
    """Minimal AnchorIndex stand-in: only `by_document` is touched here."""

    def __init__(self, anchors: list[dict]) -> None:
        self._anchors = anchors

    def by_document(self, document_id: str) -> list[dict]:
        return self._anchors


def test_blank_anchors_cost_no_extraction_calls(tmp_path, monkeypatch) -> None:
    anchors = [
        {"anchor_id": "doc 1", "text": "A financial institution shall do a thing."},
        {"anchor_id": "doc 2", "text": ""},
        {"anchor_id": "doc 3", "text": "   "},
        {"anchor_id": "doc 4", "text": "Another substantive clause of policy text."},
    ]
    calls: list[str] = []

    def _fake_extract(anchor, deployment):
        calls.append(anchor["anchor_id"])
        return ["some axis"]

    monkeypatch.setattr(arm_g, "_extract_axes_for_anchor", _fake_extract)

    axes = arm_g.extract_axes_for_document(
        _FakeIndex(anchors), "doc", axes_dir=tmp_path
    )

    # Only the two non-blank anchors reached the model.
    assert calls == ["doc 1", "doc 4"]
    # Blank anchors are absent from the result rather than present-and-empty.
    assert set(axes) == {"doc 1", "doc 4"}
