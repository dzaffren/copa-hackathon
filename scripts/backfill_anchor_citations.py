#!/usr/bin/env python3
"""One-off backfill: rename retired clause-citation fields on the committed
`data/artifacts/connection-trace-*.json` traces to the widened anchor-citation
shape introduced by Task 6 of `spec-engine-anchor-segmentation.md`.

The transform is pure JSON — no LLM calls, deterministic, idempotent. The
retired fields and their new names:

- `connections[]` per entry:
    `source_clauses: [{clause_number, text}]`
        -> `source_anchors: [{anchor_id, anchor_label, text, doc_class}]`
    `target_clauses: [{clause_number, text}]`
        -> `target_anchors: [{anchor_id, anchor_label, text, doc_class}]`
  For every migrated citation, `anchor_id = anchor_label = clause_number` and
  `doc_class = "structured-rules"` (all three real traces come from the BNM
  structured-rules corpus).

- `unsupported[]` per entry: no citation fields to migrate — pass through.

- `finder_output[]` / `critic_output[]` per entry (the model's raw candidate
  dicts): `source_clauses` / `target_clauses` are LIST-OF-STRINGS (anchor IDs);
  the keys rename to `source_anchors` / `target_anchors`, the string values are
  identical.

- `validation[]` per entry:
    `cited_clauses: [{clause_number, resolved}]`
        -> `cited_anchors: [{anchor_id, resolved}]`
  where `anchor_id = clause_number`.

Idempotency check: if the first `connections[0]` / `finder_output[0]` /
`validation[0]` entry already carries the widened field, the file is treated
as already-migrated and left untouched.

Optional guardrail: if `data/artifacts/anchor-index.json` exists (Task 7's
output) the script loads it and asserts every migrated `anchor_id` resolves.
Non-resolving ids get logged as warnings; the rename still happens (the shape
change is what matters — resolution mismatches are a follow-up).

Usage:
    python scripts/backfill_anchor_citations.py             # rewrites all 3 traces
    python scripts/backfill_anchor_citations.py --dry-run   # prints changes, writes nothing
    python scripts/backfill_anchor_citations.py <path>      # rewrites one trace
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("backfill_anchor_citations")

# The three real traces the script is designed to migrate. The `main()` no-arg
# path iterates exactly these.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ARTIFACTS_DIR = _REPO_ROOT / "data" / "artifacts"
_TRACE_GLOB = "connection-trace-*.json"
_ANCHOR_INDEX_PATH = _ARTIFACTS_DIR / "anchor-index.json"

# The `doc_class` label stamped onto every migrated citation. All three real
# traces are pairs of BNM policy documents — structured-rules segmentation.
_DEFAULT_DOC_CLASS = "structured-rules"


# ---------------------------------------------------------------------------
# Anchor-index loading (optional guardrail).
# ---------------------------------------------------------------------------


def load_anchor_index(path: Path = _ANCHOR_INDEX_PATH) -> Optional[dict[str, Any]]:
    """Return a `{anchor_id: anchor}` map, or `None` if the anchor index has
    not been built yet (Task 7 may not have landed).

    The on-disk shape is a flat list of `Anchor` records; we key them by
    `anchor_id` for O(1) lookups during resolution warnings.
    """
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    # Support two plausible shapes: a list of anchors, or a dict already keyed
    # by anchor_id. The final Task 7 shape isn't frozen at Task 8 write-time.
    if isinstance(raw, list):
        return {anchor["anchor_id"]: anchor for anchor in raw}
    if isinstance(raw, dict):
        return raw
    raise ValueError(
        f"Unrecognised anchor-index shape in {path}: expected list or dict, "
        f"got {type(raw).__name__}"
    )


# ---------------------------------------------------------------------------
# Idempotency detection.
# ---------------------------------------------------------------------------


def _already_migrated(trace: dict[str, Any]) -> bool:
    """Sniff the trace for the widened field names on the first entry of any
    citation-bearing section. If found, the trace is already migrated and the
    script short-circuits."""
    for section in ("connections", "finder_output", "critic_output"):
        entries = trace.get(section)
        if entries and isinstance(entries, list):
            first = entries[0]
            if "source_anchors" in first or "target_anchors" in first:
                return True
    validation = trace.get("validation")
    if validation and isinstance(validation, list):
        if "cited_anchors" in validation[0]:
            return True
    return False


# ---------------------------------------------------------------------------
# Per-section migrators.
# ---------------------------------------------------------------------------


def _migrate_raw_candidate_entry(entry: dict[str, Any]) -> None:
    """Rename `source_clauses` / `target_clauses` (list of string anchor IDs)
    on a finder/critic raw candidate entry to `source_anchors` /
    `target_anchors`. In-place."""
    if "source_clauses" in entry:
        entry["source_anchors"] = entry.pop("source_clauses")
    if "target_clauses" in entry:
        entry["target_anchors"] = entry.pop("target_clauses")


def _migrate_connection_entry(entry: dict[str, Any]) -> None:
    """Rename `source_clauses` / `target_clauses` (list of
    `{clause_number, text}`) on a supported-connection entry to `source_anchors`
    / `target_anchors` (list of `{anchor_id, anchor_label, text, doc_class}`).
    In-place."""
    for old, new in (
        ("source_clauses", "source_anchors"),
        ("target_clauses", "target_anchors"),
    ):
        if old not in entry:
            continue
        old_citations = entry.pop(old)
        entry[new] = [
            {
                "anchor_id": cite["clause_number"],
                "anchor_label": cite["clause_number"],
                "text": cite["text"],
                "doc_class": _DEFAULT_DOC_CLASS,
            }
            for cite in old_citations
        ]


def _migrate_validation_entry(entry: dict[str, Any]) -> None:
    """Rename `cited_clauses: [{clause_number, resolved}]` to
    `cited_anchors: [{anchor_id, resolved}]`. In-place."""
    if "cited_clauses" not in entry:
        return
    old_cited = entry.pop("cited_clauses")
    entry["cited_anchors"] = [
        {"anchor_id": cite["clause_number"], "resolved": cite["resolved"]}
        for cite in old_cited
    ]


# ---------------------------------------------------------------------------
# Top-level file migration.
# ---------------------------------------------------------------------------


def _collect_anchor_ids(trace: dict[str, Any]) -> list[str]:
    """Enumerate every anchor_id referenced by the migrated trace, for the
    optional anchor-index resolution guardrail. Duplicates are kept — the
    warning log is per-reference, not per-unique-id."""
    ids: list[str] = []
    for entry in trace.get("connections", []) or []:
        for side in ("source_anchors", "target_anchors"):
            for cite in entry.get(side, []) or []:
                ids.append(cite["anchor_id"])
    for section in ("finder_output", "critic_output"):
        for entry in trace.get(section, []) or []:
            for side in ("source_anchors", "target_anchors"):
                for aid in entry.get(side, []) or []:
                    ids.append(aid)
    for entry in trace.get("validation", []) or []:
        for cite in entry.get("cited_anchors", []) or []:
            ids.append(cite["anchor_id"])
    return ids


def _warn_unresolved(anchor_ids: list[str], anchor_index: dict[str, Any]) -> None:
    """Log a warning per anchor_id that does NOT resolve in the anchor index.
    The rename still lands — resolution mismatches are a follow-up, not a
    rollback trigger."""
    seen: set[str] = set()
    for aid in anchor_ids:
        if aid in seen:
            continue
        seen.add(aid)
        if aid not in anchor_index:
            logger.warning("anchor_id %r does not resolve in anchor-index.json", aid)


def migrate_file(
    path: Path,
    anchor_index: Optional[dict[str, Any]],
    dry_run: bool,
) -> bool:
    """Migrate one trace file in place. Returns True if the file was rewritten
    (or would be, in dry-run mode); False if it was already migrated.

    `anchor_index` is the optional `{anchor_id: anchor}` map for the resolution
    guardrail; pass `None` if `data/artifacts/anchor-index.json` doesn't exist
    (the resolution check is then skipped, and a note is logged).
    """
    trace = json.loads(path.read_text(encoding="utf-8"))

    if _already_migrated(trace):
        logger.info("%s: already migrated, skipping", path.name)
        return False

    for entry in trace.get("connections", []) or []:
        _migrate_connection_entry(entry)
    for section in ("finder_output", "critic_output"):
        for entry in trace.get(section, []) or []:
            _migrate_raw_candidate_entry(entry)
    for entry in trace.get("validation", []) or []:
        _migrate_validation_entry(entry)

    if anchor_index is None:
        logger.info(
            "%s: anchor-index.json not found — resolution check skipped", path.name
        )
    else:
        _warn_unresolved(_collect_anchor_ids(trace), anchor_index)

    if dry_run:
        logger.info("%s: dry-run — no write", path.name)
        return True

    path.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    logger.info("%s: migrated", path.name)
    return True


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _resolve_targets(paths: list[str]) -> list[Path]:
    if not paths:
        return sorted(_ARTIFACTS_DIR.glob(_TRACE_GLOB))
    return [Path(p) for p in paths]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect changes but do not write any file.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Optional explicit trace paths. If omitted, every "
            "data/artifacts/connection-trace-*.json is migrated."
        ),
    )
    args = parser.parse_args(argv)

    _configure_logging()

    anchor_index = load_anchor_index()
    targets = _resolve_targets(args.paths)

    if not targets:
        logger.warning("no traces found under %s", _ARTIFACTS_DIR)
        return 0

    for path in targets:
        migrate_file(path, anchor_index=anchor_index, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
