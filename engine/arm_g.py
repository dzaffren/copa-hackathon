"""Arm G composite coverage-aware finding pipeline (production engine module).

Ported and adapted from the experiment-validated runner
(`scripts/experiments/retrieval_ablation.py`, arm G). Six stages, three model
tiers, no critic anywhere:

    Stage 1  AXIS EXTRACTION            [EXTRACTION_DEPLOYMENT — small]
    Stage 2  SAME-TOPIC RETRIEVAL       [no model — cosine default / BM25 fallback]
    Stage 3  BATCHED SAME-TOPIC FINDER  [REASONING_DEPLOYMENT — mid-tier]
    Stage 4  SUPPRESSION BUILD          [no model]
    Stage 5  WHOLE-DOC COVERAGE FINDER  [FINDER_CRITIC_DEPLOYMENT — large]
    Stage 6  MERGE + REFORMAT + VALIDATE[no model]

`run_arm_g(anchor_index, doc_a, doc_b, signal="cosine")` runs all six and
returns a result dict Story 3 (route wiring) consumes. This module composes
existing engine pieces — `AnchorIndex` (`engine.anchors`), the citation
validator `_validate_candidates` and taxonomy enforcement (`engine.connections`,
reused UNCHANGED), and `call_chat` (`engine.llm`) — and ports the coverage
prompt + retrieval helpers from the experiment runner. The existing
`find_connections` path is untouched; Arm G is a new, parallel entry point.

Design decisions (see docs/specs/workstream-brain/spec-engine-arm-g-pipeline.md):

- **No critic** at any stage — the finder-only design was validated in the
  experiment.
- **Batched same-topic finder** (batch size 8) with batch-union membership:
  the finder sees the UNION of all anchors in a batch, partitioned by side, and
  may cite any A-side anchor against any B-side anchor in the batch. A prompt
  side-guard (NOT a schema enum) constrains source/target sides. Labels are
  restricted to the three agreement types by prompt. A batch that fails to parse
  is retried once, then skipped (recall loss, never a correctness fault).
- **Whole-doc coverage finder** — one call, silent-on / goes-beyond only, with
  the three-part COVERAGE-SUMMARY RULE and the "both sides take a position = not
  a coverage finding" guardrail. Topics resolved by the same-topic stage are
  suppressed from the coverage pass.
- **Deterministic citation reformatter** — recovers punctuation/prefix drift on
  a cited id that fails exact lookup (strip trailing punctuation; restore the
  document prefix). NO fuzzy / substring / semantic matching — an id that only
  partially resembles a real anchor demotes to unsupported, preserving the
  verbatim-citation guarantee. Every rewrite is recorded in `citation_rewrites`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from math import ceil
from pathlib import Path
from typing import Any, Callable, Optional

from engine.anchors import Anchor, AnchorIndex
from engine.config import (
    EXTRACTION_DEPLOYMENT,
    FINDER_CRITIC_DEPLOYMENT,
    REASONING_DEPLOYMENT,
    REPO_ROOT,
)
from engine.connections import _validate_candidates
from engine.llm import LLMResponseError, call_chat, parse_json_response

logger = logging.getLogger(__name__)

# Axis-cache directory. Config-driven default, acceptable for now (Open Question
# in the spec deferred the alongside-artifacts-vs-separate-dir decision).
AXES_DIR = REPO_ROOT / "experiments"

# Same-topic finder batch size (candidate pairs per REASONING_DEPLOYMENT call).
BATCH_SIZE = 8


# ---------------------------------------------------------------------------
# ClauseIndex shim — reuse engine.connections._validate_candidates unchanged.
#
# _validate_candidates expects a ClauseIndex; it only touches `.get(number)`.
# AnchorIndex.get(anchor_id) returns an Anchor carrying 'text', so the wrapper
# delegates. Ported from the experiment runner's _AnchorAsClauseIndex.
# ---------------------------------------------------------------------------


class _AnchorAsClauseIndex:
    """Wrap an ``AnchorIndex`` to satisfy the ``ClauseIndex`` shape
    ``_validate_candidates`` uses (only ``.get(number)`` is touched)."""

    def __init__(self, anchor_index: AnchorIndex) -> None:
        self._ai = anchor_index

    def get(self, number: str, version: Optional[str] = None) -> Optional[Anchor]:
        return self._ai.get(number)

    def entries_for_document(self, document_id: str) -> list[Anchor]:
        return self._ai.by_document(document_id)


# ---------------------------------------------------------------------------
# Stage 1 — axis extraction with scaled cap + disk cache keyed on text_hash AND cap.
# ---------------------------------------------------------------------------

_AXIS_SYSTEM_PROMPT = (
    "You are an expert regulatory-policy analyst. Given one clause or "
    "passage from a policy document, list 1-N short 'axes' that describe "
    "*what topics this passage speaks to*, where N is provided in the user "
    "message.\n\n"
    "Each axis is a short noun phrase (2-6 words) in canonical regulatory "
    "language, deliberately abstracted away from the specific terminology "
    "this document happens to use. The goal is that a semantically-equivalent "
    "passage in a different jurisdiction, using different terminology, would "
    "produce overlapping axes.\n\n"
    "Rules:\n"
    "- Axes must be topics (nouns), never positions (do NOT include "
    '"requires X annually" — instead say "scenario testing cadence").\n'
    "- Prefer generic regulatory language ('residential mortgage risk-weight "
    "tier') over jurisdiction-specific labels ('conforming loan classification').\n"
    "- Deduplicate — if two axes overlap 80%+, keep only the clearer one.\n"
    "- Return a JSON array of strings. No commentary, no markdown fences.\n\n"
    'Example input: "A financial institution shall conduct scenario testing '
    'of its operational resilience arrangements at least annually."\n'
    'Example output: ["scenario testing cadence", "operational resilience '
    'testing frequency", "annual testing requirement"]'
)


def _text_hash(text: str) -> str:
    """SHA256 of anchor text (first 16 hex chars) — cache invalidation key."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _axis_cap(text: str) -> int:
    """Axis cap that scales with anchor length: floor 5, ceiling 12."""
    return min(12, max(5, ceil(len(text) / 400)))


def _load_axes_cache(document_id: str) -> dict:
    """Load a document's axes cache, or an empty scaffold when none exists."""
    path = AXES_DIR / f"axes-{document_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "document_id": document_id,
        "model": EXTRACTION_DEPLOYMENT,
        "anchors": [],
    }


def _write_axes_cache(document_id: str, cache: dict) -> None:
    AXES_DIR.mkdir(parents=True, exist_ok=True)
    path = AXES_DIR / f"axes-{document_id}.json"
    path.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _extract_axes_for_anchor(anchor: Anchor, deployment: str) -> list[str]:
    """Call the small model once for one anchor; return 1-N axis strings.

    The cap scales with anchor length (see ``_axis_cap``). Retries up to three
    times on an unparseable reply, then raises ``LLMResponseError``.
    """
    cap = _axis_cap(anchor["text"])
    user = f"Anchor text (list {cap} axes):\n\n{anchor['text']}"
    last_error: Optional[LLMResponseError] = None
    for attempt in range(1, 4):
        raw = call_chat(deployment, _AXIS_SYSTEM_PROMPT, user, max_tokens=1024)
        try:
            axes = parse_json_response(raw)
            if not isinstance(axes, list) or not all(isinstance(a, str) for a in axes):
                raise LLMResponseError(f"expected list[str], got {type(axes).__name__}")
            if not axes:
                raise LLMResponseError("empty axes list")
            return axes[:cap]
        except LLMResponseError as exc:
            last_error = exc
            logger.warning(
                "axis extraction attempt %d/3 failed for %s: %s",
                attempt,
                anchor["anchor_id"],
                exc,
            )
    assert last_error is not None
    raise last_error


def extract_axes_for_document(
    anchor_index: AnchorIndex,
    document_id: str,
    deployment: str = EXTRACTION_DEPLOYMENT,
) -> dict[str, list[str]]:
    """Stage 1: extract per-anchor axes for one document, honouring the cache.

    A cache entry is a HIT only when BOTH its ``text_hash`` matches the current
    anchor text AND its ``axis_cap`` matches the current cap — a change in
    either forces re-extraction. The refreshed cache is written back to disk.

    Returns ``{anchor_id: [axis, ...]}`` for every anchor in the document.
    """
    anchors = anchor_index.by_document(document_id)
    cache = _load_axes_cache(document_id)
    cached_by_id = {entry["anchor_id"]: entry for entry in cache["anchors"]}

    new_entries: list[dict] = []
    axes_by_id: dict[str, list[str]] = {}
    hits = misses = 0

    for anchor in anchors:
        anchor_id = anchor["anchor_id"]
        text_hash = _text_hash(anchor["text"])
        cap = _axis_cap(anchor["text"])
        existing = cached_by_id.get(anchor_id)
        if (
            existing
            and existing.get("text_hash") == text_hash
            and existing.get("axis_cap") == cap
        ):
            new_entries.append(existing)
            axes_by_id[anchor_id] = existing["axes"]
            hits += 1
            continue

        try:
            axes = _extract_axes_for_anchor(anchor, deployment)
        except LLMResponseError as exc:
            logger.error("axis extraction failed for %s: %s", anchor_id, exc)
            continue

        entry = {
            "anchor_id": anchor_id,
            "text_hash": text_hash,
            "axis_cap": cap,
            "axes": axes,
        }
        new_entries.append(entry)
        axes_by_id[anchor_id] = axes
        misses += 1

    cache["anchors"] = new_entries
    cache["model"] = deployment
    _write_axes_cache(document_id, cache)
    logger.info(
        "%s: %d anchors, %d cache hits, %d extraction calls",
        document_id,
        len(anchors),
        hits,
        misses,
    )
    return axes_by_id
