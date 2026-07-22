#!/usr/bin/env python3
"""Extract per-anchor axes for the retrieval-ablation experiment.

For each anchor in the specified documents, an LLM call produces 1-5 short
"axes" — canonical regulatory topic phrases describing what the anchor is
*about*, abstracted away from jurisdiction-specific terminology. Cached to
disk so Arms C and D re-use the same axes without re-hitting the LLM.

Design: retrieval-ablation experiment spec — Stage A per anchor.

Output shape per document:
    experiments/axes-{document_id}.json = {
        "document_id": ...,
        "model": ...,
        "generated_at": ISO timestamp,
        "anchors": [
            {"anchor_id": ..., "text_hash": ..., "axes": [str, ...]},
            ...
        ]
    }

Usage:
    python scripts/experiments/extract_axes.py \\
        --docs bnm-open-finance-ed-2025 hkma-open-api-framework-2018 bis-pap168-open-finance
"""

import argparse
import hashlib
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.anchors import Anchor, AnchorIndex  # noqa: E402
from engine.config import FINDER_CRITIC_DEPLOYMENT  # noqa: E402
from engine.llm import LLMResponseError, call_chat, parse_json_response  # noqa: E402

logger = logging.getLogger(__name__)

ANCHOR_INDEX_PATH = REPO_ROOT / "data" / "artifacts" / "anchor-index.json"
AXES_DIR = REPO_ROOT / "experiments"

_AXIS_SYSTEM_PROMPT = (
    "You are an expert regulatory-policy analyst. Given one clause or "
    "passage from a policy document, list 1-5 short 'axes' that describe "
    "*what topics this passage speaks to*.\n\n"
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
    """SHA256 of anchor text — for cache-invalidation when text changes."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _load_axes_cache(document_id: str) -> dict:
    """Load existing axes cache for a document, or return an empty scaffold."""
    path = AXES_DIR / f"axes-{document_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "document_id": document_id,
        "model": FINDER_CRITIC_DEPLOYMENT,
        "generated_at": None,
        "anchors": [],
    }


def _write_axes_cache(document_id: str, cache: dict) -> None:
    AXES_DIR.mkdir(parents=True, exist_ok=True)
    path = AXES_DIR / f"axes-{document_id}.json"
    cache["generated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def extract_axes_for_anchor(anchor: Anchor) -> list[str]:
    """Call the LLM once for one anchor. Return 1-5 axis strings."""
    user = f"Anchor text:\n\n{anchor['text']}"
    for attempt in range(1, 4):
        raw = call_chat(
            FINDER_CRITIC_DEPLOYMENT, _AXIS_SYSTEM_PROMPT, user, max_tokens=1024
        )
        try:
            axes = parse_json_response(raw)
            if not isinstance(axes, list) or not all(isinstance(a, str) for a in axes):
                raise LLMResponseError(f"expected list[str], got {type(axes).__name__}")
            if not axes:
                raise LLMResponseError("empty axes list")
            if len(axes) > 5:
                axes = axes[:5]
            return axes
        except LLMResponseError as exc:
            logger.warning(
                "axis extraction attempt %d/3 failed for %s: %s",
                attempt,
                anchor["anchor_id"],
                exc,
            )
    raise LLMResponseError(
        f"axis extraction failed after 3 attempts for {anchor['anchor_id']}"
    )


def extract_axes_for_document(anchor_index: AnchorIndex, document_id: str) -> None:
    """Extract axes for every anchor in a document, honouring the cache."""
    anchors = anchor_index.by_document(document_id)
    if not anchors:
        logger.error("no anchors found for document_id=%s", document_id)
        return

    cache = _load_axes_cache(document_id)
    cached_by_id = {entry["anchor_id"]: entry for entry in cache["anchors"]}

    new_entries: list[dict] = []
    hits = misses = 0

    for i, anchor in enumerate(anchors, start=1):
        anchor_id = anchor["anchor_id"]
        text_hash = _text_hash(anchor["text"])
        existing = cached_by_id.get(anchor_id)
        if existing and existing.get("text_hash") == text_hash:
            new_entries.append(existing)
            hits += 1
            continue

        logger.info(
            "[%d/%d] extracting axes for %s (%d chars)",
            i,
            len(anchors),
            anchor_id,
            len(anchor["text"]),
        )
        try:
            axes = extract_axes_for_anchor(anchor)
        except LLMResponseError as exc:
            logger.error("axis extraction failed for %s: %s", anchor_id, exc)
            continue

        new_entries.append(
            {"anchor_id": anchor_id, "text_hash": text_hash, "axes": axes}
        )
        misses += 1

    cache["anchors"] = new_entries
    _write_axes_cache(document_id, cache)
    logger.info(
        "%s: %d anchors, %d cache hits, %d LLM calls, wrote %s",
        document_id,
        len(anchors),
        hits,
        misses,
        AXES_DIR / f"axes-{document_id}.json",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs",
        nargs="+",
        required=True,
        help="document_ids to extract axes for",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not ANCHOR_INDEX_PATH.exists():
        logger.error("anchor-index.json not found at %s", ANCHOR_INDEX_PATH)
        return 1

    raw = json.loads(ANCHOR_INDEX_PATH.read_text(encoding="utf-8"))
    anchor_index = AnchorIndex(raw)

    for doc_id in args.docs:
        try:
            extract_axes_for_document(anchor_index, doc_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("failed on document %s: %s", doc_id, exc)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
