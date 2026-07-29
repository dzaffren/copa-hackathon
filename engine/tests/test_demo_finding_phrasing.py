"""Readability guard for demo-visible finding phrasing.

The Project SELARAS demo shows *committed* findings (build-and-persist), so the
phrasing an audience reads is whatever sits in ``data/workstreams/*/findings/``,
not something a live model produces on the day. This module locks the
plain-language bar from
``docs/specs/plain-language-finding-explanations/spec.md`` onto every
demo-visible finding:

- ``summary`` is one short line, at most 20 words;
- ``scope_note``, when present, is at most 30 words;
- neither field uses an em dash (house style, mirrors the finder prompts).

Scope is exactly what the app surfaces: the non-hidden workstreams
(``engine.workstreams.list_workstreams`` honours the ``hidden`` flag) plus the
``_cross`` cross-workstream linkage store. Hidden fixtures are deferred per the
spec's scope boundary and are intentionally not asserted here.

Pure file assertions — no network, no engine run.
"""

import json
from pathlib import Path

import pytest

from engine.config import REPO_ROOT
from engine.workstreams import list_workstreams

WORKSTREAMS_DIR = REPO_ROOT / "data" / "workstreams"

SUMMARY_MAX_WORDS = 20
SCOPE_NOTE_MAX_WORDS = 30


def _word_count(text: str) -> int:
    return len(text.split())


def _demo_finding_files() -> list[Path]:
    """Every findings file the app can surface: non-hidden workstreams plus the
    ``_cross`` linkage store."""
    files: list[Path] = []
    for ws in list_workstreams(WORKSTREAMS_DIR):
        files.extend(sorted((WORKSTREAMS_DIR / ws["id"] / "findings").glob("*.json")))
    files.extend(sorted((WORKSTREAMS_DIR / "_cross" / "findings").glob("*.json")))
    return files


def _demo_findings() -> list[tuple[str, dict]]:
    """(source-file-name, finding) for every demo-visible finding."""
    out: list[tuple[str, dict]] = []
    for path in _demo_finding_files():
        for finding in json.loads(path.read_text(encoding="utf-8")):
            out.append((path.name, finding))
    return out


_FINDINGS = _demo_findings()


def test_demo_findings_exist() -> None:
    """Guard against the glob silently matching nothing (a green vacuous suite)."""
    assert _FINDINGS, "no demo-visible findings found — scope query is broken"


@pytest.mark.parametrize(
    "source, finding",
    _FINDINGS,
    ids=[f"{name}#{i}" for i, (name, _) in enumerate(_FINDINGS)],
)
def test_summary_is_short(source: str, finding: dict) -> None:
    summary = finding.get("summary") or ""
    assert (
        summary.strip()
    ), f"{source}: finding {finding.get('id')} has an empty summary"
    words = _word_count(summary)
    assert words <= SUMMARY_MAX_WORDS, (
        f"{source}: finding {finding.get('id')} summary is {words} words "
        f"(cap {SUMMARY_MAX_WORDS}): {summary!r}"
    )
    assert (
        "—" not in summary
    ), f"{source}: finding {finding.get('id')} summary uses an em dash: {summary!r}"


@pytest.mark.parametrize(
    "source, finding",
    _FINDINGS,
    ids=[f"{name}#{i}" for i, (name, _) in enumerate(_FINDINGS)],
)
def test_scope_note_is_short(source: str, finding: dict) -> None:
    scope_note = finding.get("scope_note")
    if not scope_note:
        return
    words = _word_count(scope_note)
    assert words <= SCOPE_NOTE_MAX_WORDS, (
        f"{source}: finding {finding.get('id')} scope_note is {words} words "
        f"(cap {SCOPE_NOTE_MAX_WORDS}): {scope_note!r}"
    )
    assert "—" not in scope_note, (
        f"{source}: finding {finding.get('id')} scope_note uses an em dash: "
        f"{scope_note!r}"
    )
