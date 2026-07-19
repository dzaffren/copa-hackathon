"""Tests for `scripts/backfill_anchor_citations.py` — the one-off JSON rename
script that migrates `data/artifacts/connection-trace-*.json` from the retired
clause-based citation shape to the widened anchor-based citation shape.

The script is pure JSON transform: no LLM calls, deterministic, idempotent.
Every test operates on a hand-crafted trace fixture in `tmp_path` — the real
`data/artifacts/*.json` files are NEVER touched by the test suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the `scripts/` directory importable so we can call the backfill helpers
# directly (as functions) — the CLI is exercised via `subprocess` in the
# dry-run test only.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import backfill_anchor_citations as backfill  # noqa: E402


def _write_trace(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_trace(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixtures for retired-shape traces. These mirror the three real files on disk
# (finder_output + critic_output + validation only), plus a fabricated
# `connections[]` / `unsupported[]` shape so we cover the widened Connection
# citation form (`[{clause_number, text}]`) too.
# ---------------------------------------------------------------------------


def _retired_trace_finder_critic_validation() -> dict:
    return {
        "model_id": "claude-opus-4-8",
        "timestamp": "2026-07-11T00:00:00+00:00",
        "document_ids": ["doc-a", "doc-b"],
        "finder_output": [
            {
                "summary": "candidate one",
                "label": "aligns-with",
                "sentiment": None,
                "source_clauses": ["Open Finance 7.6(b)"],
                "target_clauses": ["Operational Resilience 4.3"],
            },
        ],
        "critic_output": [
            {
                "summary": "critic one",
                "label": "differs-on",
                "sentiment": "tighten",
                "source_clauses": ["Open Finance 12.5"],
                "target_clauses": ["Operational Resilience 2.9(e)"],
                "scope_note": "note text",
            },
        ],
        "validation": [
            {
                "summary": "validation one",
                "label": "aligns-with",
                "sentiment": None,
                "cited_clauses": [
                    {"clause_number": "Open Finance 7.6(b)", "resolved": True},
                    {"clause_number": "Operational Resilience 4.3", "resolved": True},
                ],
                "supported": True,
            },
        ],
    }


def _retired_trace_with_connections_and_unsupported() -> dict:
    return {
        "model_id": "claude-opus-4-8",
        "timestamp": "2026-07-11T00:00:00+00:00",
        "document_ids": ["doc-a", "doc-b"],
        "connections": [
            {
                "summary": "supported finding",
                "label": "aligns-with",
                "sentiment": None,
                "source_clauses": [
                    {"clause_number": "Open Finance 7.6(b)", "text": "verbatim A"},
                ],
                "target_clauses": [
                    {
                        "clause_number": "Operational Resilience 4.3",
                        "text": "verbatim B",
                    },
                ],
                "scope_note": "why",
                "supported": True,
            },
        ],
        "unsupported": [
            {
                "summary": "dropped candidate",
                "label": None,
                "sentiment": None,
                "message": "No matching clause found",
                "supported": False,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_backfill_renames_source_clauses_to_source_anchors(tmp_path: Path) -> None:
    """The `connections[]` per-entry `source_clauses`/`target_clauses` (list of
    `{clause_number, text}`) get renamed to `source_anchors`/`target_anchors`
    (list of `{anchor_id, anchor_label, text, doc_class}`)."""
    trace = _retired_trace_with_connections_and_unsupported()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)

    migrated = _read_trace(trace_path)
    conn = migrated["connections"][0]

    assert "source_clauses" not in conn
    assert "target_clauses" not in conn
    assert conn["source_anchors"] == [
        {
            "anchor_id": "Open Finance 7.6(b)",
            "anchor_label": "Open Finance 7.6(b)",
            "text": "verbatim A",
            "doc_class": "structured-rules",
        }
    ]
    assert conn["target_anchors"] == [
        {
            "anchor_id": "Operational Resilience 4.3",
            "anchor_label": "Operational Resilience 4.3",
            "text": "verbatim B",
            "doc_class": "structured-rules",
        }
    ]


def test_backfill_renames_cited_clauses_to_cited_anchors(tmp_path: Path) -> None:
    """`validation[]` `cited_clauses: [{clause_number, resolved}]` migrates to
    `cited_anchors: [{anchor_id, resolved}]`."""
    trace = _retired_trace_finder_critic_validation()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)

    migrated = _read_trace(trace_path)
    entry = migrated["validation"][0]

    assert "cited_clauses" not in entry
    assert entry["cited_anchors"] == [
        {"anchor_id": "Open Finance 7.6(b)", "resolved": True},
        {"anchor_id": "Operational Resilience 4.3", "resolved": True},
    ]


def test_backfill_is_idempotent(tmp_path: Path) -> None:
    """Running the migration twice produces byte-identical output — the second
    pass detects the widened shape and short-circuits."""
    trace = _retired_trace_finder_critic_validation()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)
    once = trace_path.read_text(encoding="utf-8")

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)
    twice = trace_path.read_text(encoding="utf-8")

    assert once == twice


def test_backfill_dry_run_does_not_write(tmp_path: Path) -> None:
    """`--dry-run` (i.e. `dry_run=True`) leaves the file unchanged on disk."""
    trace = _retired_trace_finder_critic_validation()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)
    before = trace_path.read_text(encoding="utf-8")

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=True)

    after = trace_path.read_text(encoding="utf-8")
    assert before == after


def test_backfill_handles_missing_anchor_index_gracefully(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """When `anchor-index.json` is absent, the script still migrates the file
    and logs that the resolution check was skipped."""
    trace = _retired_trace_finder_critic_validation()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    # `anchor_index=None` models the "no anchor-index.json on disk" case.
    with caplog.at_level("INFO"):
        backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)

    migrated = _read_trace(trace_path)
    assert "source_anchors" in migrated["finder_output"][0]
    # A note about the skipped check landed in the log.
    assert any(
        "skipped" in record.message.lower()
        or "no anchor-index" in record.message.lower()
        for record in caplog.records
    )


def test_backfill_preserves_summary_label_sentiment_scope_note(tmp_path: Path) -> None:
    """The rename touches ONLY citation fields — every other field on every
    entry round-trips unchanged."""
    trace = _retired_trace_with_connections_and_unsupported()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)
    migrated = _read_trace(trace_path)

    conn = migrated["connections"][0]
    assert conn["summary"] == "supported finding"
    assert conn["label"] == "aligns-with"
    assert conn["sentiment"] is None
    assert conn["scope_note"] == "why"
    assert conn["supported"] is True
    assert migrated["model_id"] == "claude-opus-4-8"
    assert migrated["document_ids"] == ["doc-a", "doc-b"]


def test_backfill_preserves_unsupported_entries(tmp_path: Path) -> None:
    """`unsupported[]` carries no citation fields; every entry passes through
    unchanged."""
    trace = _retired_trace_with_connections_and_unsupported()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)
    migrated = _read_trace(trace_path)

    assert migrated["unsupported"] == trace["unsupported"]


def test_backfill_preserves_finder_and_critic_output_raw(tmp_path: Path) -> None:
    """`finder_output` / `critic_output` hold the model's raw candidates —
    `source_clauses`/`target_clauses` are LIST-OF-STRINGS (anchor IDs), not
    list-of-dicts. The migration renames the keys and keeps the string values
    identical."""
    trace = _retired_trace_finder_critic_validation()
    trace_path = tmp_path / "connection-trace-example.json"
    _write_trace(trace_path, trace)

    backfill.migrate_file(trace_path, anchor_index=None, dry_run=False)
    migrated = _read_trace(trace_path)

    finder = migrated["finder_output"][0]
    assert "source_clauses" not in finder
    assert "target_clauses" not in finder
    assert finder["source_anchors"] == ["Open Finance 7.6(b)"]
    assert finder["target_anchors"] == ["Operational Resilience 4.3"]

    critic = migrated["critic_output"][0]
    assert "source_clauses" not in critic
    assert "target_clauses" not in critic
    assert critic["source_anchors"] == ["Open Finance 12.5"]
    assert critic["target_anchors"] == ["Operational Resilience 2.9(e)"]
    # Non-citation fields untouched.
    assert critic["scope_note"] == "note text"
    assert critic["sentiment"] == "tighten"
