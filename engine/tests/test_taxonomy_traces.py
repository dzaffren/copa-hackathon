"""Conformance tests for the committed connection-trace artifacts.

Builder 1 widened ``engine.connections`` so every finding carries a semantic
``label`` (one of five) plus an optional ``sentiment`` (only on ``differs-on``),
and ``_write_trace`` now records both fields. This module locks the three
on-disk ``data/artifacts/connection-trace-*.json`` backstops to that new schema:

- every entry in ``finder_output``, ``critic_output`` and ``validation`` carries
  a valid ``label`` and a ``sentiment`` that is non-null ONLY on ``differs-on``;
- the supported-finding counts and verbatim clause citations are undisturbed by
  the relabelling (the anti-hallucination guardrail is not weakened here); and
- the retired Conflict / Duplication / Gap vocabulary never reappears as a label.

These are pure file assertions — no network, no engine run. The artifacts are
located from ``engine.config.REPO_ROOT`` and read as UTF-8.
"""

import json
from pathlib import Path

import pytest

from engine.config import REPO_ROOT
from engine.connections import CONNECTION_LABELS, SENTIMENT_VALUES

ARTIFACTS_DIR = REPO_ROOT / "data" / "artifacts"

# The three committed pairwise traces, with their known supported-finding count
# (every one of these validation entries is ``supported: true``).
TRACE_FILES = {
    "connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json": 12,
    "connection-trace-rmit-v1-2023__rmit-v2-2025.json": 55,
    "connection-trace-rmit-v2-2026-draft__outsourcing-v1-2019.json": 16,
}

# The candidate-bearing sections of a trace that must all carry the new schema.
CANDIDATE_SECTIONS = ("finder_output", "critic_output", "validation")

# The label-only value ``sentiment`` may attach to; retired pre-taxonomy strings.
_SENTIMENT_LABEL = "differs-on"
_RETIRED_VOCABULARY = ("Conflict", "Duplication", "Gap")


def _load_trace(name: str) -> dict:
    return json.loads((ARTIFACTS_DIR / name).read_text(encoding="utf-8"))


def _all_candidates(trace: dict) -> list[dict]:
    return [item for section in CANDIDATE_SECTIONS for item in trace[section]]


@pytest.fixture(scope="module")
def traces() -> dict[str, dict]:
    return {name: _load_trace(name) for name in TRACE_FILES}


def test_every_candidate_has_a_valid_label(traces: dict[str, dict]) -> None:
    """Every finder/critic/validation entry carries a label drawn from exactly
    the five-value taxonomy — none is left null or off-vocabulary."""
    for name, trace in traces.items():
        for section in CANDIDATE_SECTIONS:
            for i, item in enumerate(trace[section]):
                label = item.get("label")
                assert label in CONNECTION_LABELS, (
                    f"{name} {section}[{i}] label {label!r} not in "
                    f"{list(CONNECTION_LABELS)}"
                )


def test_sentiment_only_on_differs_on(traces: dict[str, dict]) -> None:
    """``sentiment`` is non-null ONLY on ``differs-on`` (and then a valid value);
    for every other label it is null."""
    for name, trace in traces.items():
        for section in CANDIDATE_SECTIONS:
            for i, item in enumerate(trace[section]):
                label = item.get("label")
                sentiment = item.get("sentiment")
                if label == _SENTIMENT_LABEL:
                    if sentiment is not None:
                        assert sentiment in SENTIMENT_VALUES, (
                            f"{name} {section}[{i}] sentiment {sentiment!r} not "
                            f"in {list(SENTIMENT_VALUES)}"
                        )
                else:
                    assert sentiment is None, (
                        f"{name} {section}[{i}] label {label!r} must not carry "
                        f"a sentiment; got {sentiment!r}"
                    )


def test_supported_finding_counts_preserved(traces: dict[str, dict]) -> None:
    """The relabelling preserved every supported validation finding — the count
    is unchanged and each remains ``supported: true``."""
    for name, expected_count in TRACE_FILES.items():
        validation = traces[name]["validation"]
        assert len(validation) == expected_count, (
            f"{name} has {len(validation)} validation entries, "
            f"expected {expected_count}"
        )
        assert all(v["supported"] is True for v in validation), (
            f"{name} has a validation entry that is not supported: true"
        )


def test_citation_resolution_undisturbed(traces: dict[str, dict]) -> None:
    """Verbatim integrity: every cited clause on every supported validation
    finding still resolves — adding labels did not touch the citations."""
    for name, trace in traces.items():
        for i, entry in enumerate(trace["validation"]):
            for cited in entry["cited_clauses"]:
                assert cited["resolved"] is True, (
                    f"{name} validation[{i}] clause "
                    f"{cited['clause_number']!r} is no longer resolved"
                )


def test_no_retired_vocabulary_as_label(traces: dict[str, dict]) -> None:
    """The retired Conflict / Duplication / Gap taxonomy never reappears as a
    ``label`` value in any trace section."""
    for name, trace in traces.items():
        for section in CANDIDATE_SECTIONS:
            for i, item in enumerate(trace[section]):
                assert item.get("label") not in _RETIRED_VOCABULARY, (
                    f"{name} {section}[{i}] uses retired label "
                    f"{item.get('label')!r}"
                )


def test_demo_trace_showcases_conflict_and_goes_beyond() -> None:
    """The opres demo trace must exhibit the headline version-drift
    ``conflicts-with`` and at least one ``goes-beyond`` coverage finding."""
    validation = _load_trace(
        "connection-trace-opres-v1-2025-draft__open-finance-v1-2025-ed.json"
    )["validation"]
    labels = [entry["label"] for entry in validation]
    assert "conflicts-with" in labels, "opres trace lost its conflicts-with exhibit"
    assert "goes-beyond" in labels, "opres trace lost its goes-beyond exhibit"
