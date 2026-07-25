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


# ---------------------------------------------------------------------------
# Stage 2 — same-topic retrieval [no model].
#
# Cosine (default, validated) over axis embeddings via the Bedrock Cohere embed
# call; BM25 (fallback) is pure Python, zero cost. `retrieve_hybrid` is NOT
# ported (spec constraint). When cosine is requested but the embeddings endpoint
# is unavailable/errors, `retrieve` falls back to BM25 automatically.
# ---------------------------------------------------------------------------


_BEDROCK_CLIENT = None


def _get_bedrock_client() -> Any:
    """Lazy-init the Bedrock runtime client using the .env AWS creds."""
    global _BEDROCK_CLIENT
    if _BEDROCK_CLIENT is None:
        import os

        try:
            from dotenv import load_dotenv

            load_dotenv(REPO_ROOT / ".env")
        except ImportError:
            pass
        import boto3

        region = os.environ.get("AWS_REGION") or os.environ.get("REGION")
        _BEDROCK_CLIENT = boto3.client("bedrock-runtime", region_name=region)
    return _BEDROCK_CLIENT


def _embed_batch(
    texts: list[str],
    input_type: str = "search_document",
    output_dimension: int = 1024,
    model_id: str = "global.cohere.embed-v4:0",
) -> list[list[float]]:
    """Embed a batch of texts via Bedrock's Cohere embed-v4 inference profile.

    ``input_type`` should be ``search_document`` for corpus-side texts and
    ``search_query`` for retrieval-side queries — Cohere's asymmetric embedding
    trained this way. Cohere embed-v4 accepts up to 96 texts per call; chunked
    automatically.
    """
    import json as _json

    client = _get_bedrock_client()
    all_embeddings: list[list[float]] = []
    for chunk_start in range(0, len(texts), 96):
        chunk = texts[chunk_start : chunk_start + 96]
        resp = client.invoke_model(
            modelId=model_id,
            body=_json.dumps(
                {
                    "texts": chunk,
                    "input_type": input_type,
                    "embedding_types": ["float"],
                    "output_dimension": output_dimension,
                }
            ),
        )
        body = _json.loads(resp["body"].read())
        all_embeddings.extend(body["embeddings"]["float"])
    return all_embeddings


def _cosine(a: list[float], b: list[float]) -> float:
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _bm25_hits(query: str, corpus_texts: list[str]) -> list[float]:
    """BM25 scores for ``query`` against each corpus text (unnormalised)."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 not installed — BM25 hits will all be zero")
        return [0.0] * len(corpus_texts)

    tokenised = [re.findall(r"\w+", t.lower()) for t in corpus_texts]
    bm25 = BM25Okapi(tokenised)
    q_tokens = re.findall(r"\w+", query.lower())
    return bm25.get_scores(q_tokens).tolist()


def retrieve_cosine_only(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    top_k_per_anchor: int = 2,
    floor: float = 0.55,
    global_max_pairs: int = 60,
) -> list[dict[str, Any]]:
    """Cosine over axis embeddings, per-A-anchor top-K, global cap.

    For each SOURCE ANCHOR, aggregate cosine scores across all its axes against
    each B anchor (max across axis pairings), keep the top-K target anchors per
    source above ``floor``, then apply a global top-N cap.
    """
    ids_b = list(axes_b.keys())
    b_flat_axes: list[str] = []
    b_axis_owner: list[str] = []
    for aid in ids_b:
        for ax in axes_b[aid]:
            b_flat_axes.append(ax)
            b_axis_owner.append(aid)

    b_embeds = _embed_batch(b_flat_axes, input_type="search_document")

    all_a_axes = [ax for aid, axs in axes_a.items() for ax in axs]
    a_axis_owner = [aid for aid, axs in axes_a.items() for _ in axs]
    a_embeds = _embed_batch(all_a_axes, input_type="search_query")

    b_axis_idx_by_anchor: dict[str, list[int]] = {}
    for j, aid in enumerate(b_axis_owner):
        b_axis_idx_by_anchor.setdefault(aid, []).append(j)

    a_axis_by_anchor: dict[str, list[tuple[str, list[float]]]] = {}
    for a_axis, aid, emb in zip(all_a_axes, a_axis_owner, a_embeds):
        a_axis_by_anchor.setdefault(aid, []).append((a_axis, emb))

    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for a_id, axis_embeds in a_axis_by_anchor.items():
        b_scores: dict[str, tuple[float, str, str]] = {}
        for a_axis, a_emb in axis_embeds:
            for b_id, idxs in b_axis_idx_by_anchor.items():
                best = max(idxs, key=lambda j: _cosine(a_emb, b_embeds[j]))
                sim = _cosine(a_emb, b_embeds[best])
                if sim < floor:
                    continue
                existing = b_scores.get(b_id)
                if existing is None or existing[0] < sim:
                    b_scores[b_id] = (sim, a_axis, b_flat_axes[best])
        top = sorted(b_scores.items(), key=lambda kv: -kv[1][0])[:top_k_per_anchor]
        for b_id, (sim, a_axis, b_axis) in top:
            candidates[(a_id, b_id)] = {
                "source_anchor_id": a_id,
                "target_anchor_id": b_id,
                "matched_axis_source": a_axis,
                "matched_axis_target": b_axis,
                "similarity": sim,
                "signal": "cosine",
            }
    ranked = sorted(candidates.values(), key=lambda c: -c["similarity"])
    return ranked[:global_max_pairs]


def retrieve_bm25_only(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    top_k_per_anchor: int = 2,
    score_floor: float = 5.0,
    global_max_pairs: int = 60,
) -> list[dict[str, Any]]:
    """BM25 retrieval only — no embeddings, no glossary (the pure-Python fallback).

    For each SOURCE ANCHOR, run BM25 for each of its axes against side B's axes,
    aggregate at the target-anchor level, keep top-K target anchors per source
    above ``score_floor``, then apply a global cap.
    """
    ids_b = list(axes_b.keys())
    b_flat_axes: list[str] = []
    b_axis_owner: list[str] = []
    for aid in ids_b:
        for ax in axes_b[aid]:
            b_flat_axes.append(ax)
            b_axis_owner.append(aid)

    b_axis_idx_by_anchor: dict[str, list[int]] = {}
    for j, aid in enumerate(b_axis_owner):
        b_axis_idx_by_anchor.setdefault(aid, []).append(j)

    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for a_id, a_axes in axes_a.items():
        b_scores: dict[str, tuple[float, str, str]] = {}
        for a_axis in a_axes:
            scores = _bm25_hits(a_axis, b_flat_axes)
            for b_id, idxs in b_axis_idx_by_anchor.items():
                best_j = max(idxs, key=lambda j: scores[j])
                best_score = float(scores[best_j])
                if best_score < score_floor:
                    continue
                existing = b_scores.get(b_id)
                if existing is None or existing[0] < best_score:
                    b_scores[b_id] = (best_score, a_axis, b_flat_axes[best_j])
        top = sorted(b_scores.items(), key=lambda kv: -kv[1][0])[:top_k_per_anchor]
        for b_id, (score, a_axis, b_axis) in top:
            candidates[(a_id, b_id)] = {
                "source_anchor_id": a_id,
                "target_anchor_id": b_id,
                "matched_axis_source": a_axis,
                "matched_axis_target": b_axis,
                "bm25_score": score,
                "signal": "bm25",
            }
    ranked = sorted(candidates.values(), key=lambda c: -c["bm25_score"])
    return ranked[:global_max_pairs]


def retrieve(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    signal: str = "cosine",
) -> list[dict[str, Any]]:
    """Stage 2: select the retrieval method.

    ``signal="bm25"`` forces BM25. ``signal="cosine"`` (default) uses cosine over
    axis embeddings but automatically falls back to BM25 when the embeddings
    endpoint is unavailable or errors — so the pipeline stays runnable without
    embeddings (a recall/quality trade, never a failure).
    """
    if signal == "bm25":
        return retrieve_bm25_only(axes_a, axes_b)
    try:
        return retrieve_cosine_only(axes_a, axes_b)
    except Exception as exc:  # noqa: BLE001 - any embedding failure → BM25 fallback
        logger.warning("cosine retrieval unavailable (%s) — falling back to BM25", exc)
        return retrieve_bm25_only(axes_a, axes_b)


# ---------------------------------------------------------------------------
# Stage 3 — batched same-topic finder [REASONING_DEPLOYMENT].
#
# Replaces the experiment's per-pair loop with batched (size 8) union-membership
# calls. The finder sees the UNION of all anchors in the batch, partitioned by
# side; a finding may cite ANY A-side anchor against ANY B-side anchor in the
# batch. Labels restricted to the three agreement types (prompt-enforced). A
# prompt SIDE-GUARD (not a schema enum) requires source_clauses to be A-side ids
# only, target_clauses B-side only. A batch that fails to parse is retried ONCE,
# then skipped with every pair id logged (recall loss, never a correctness fault).
# ---------------------------------------------------------------------------

SAME_TOPIC_FINDER_SYSTEM_PROMPT = (
    "You are a policy analyst finding SAME-TOPIC connections between two Bank "
    "Negara Malaysia policy documents. You are given a batch of anchors from "
    "each side, listed separately: an A-side list and a B-side list. Each anchor "
    "is `{anchor_id}: {text}`.\n\n"
    "DIRECTION CONVENTION (fixed): document A is 'we/ours'; document B is "
    "'they/theirs'.\n\n"
    "LABEL RESTRICTION (strict): emit ONLY findings with label `aligns-with`, "
    "`differs-on`, or `conflicts-with`. NEVER emit `silent-on` or `goes-beyond` "
    "— coverage asymmetries are handled by a separate whole-document pass. If a "
    "pair is one-sided, skip it (do not emit a finding).\n"
    "  - aligns-with: same topic; the two clauses agree, or one adopts the other "
    "without narrowing or widening.\n"
    "  - differs-on: same topic, different position. MAY carry a sentiment of "
    "exactly one of tighten / loosen / neutral (tighten = our position is "
    "stricter, loosen = more permissive, neutral = different but neither). Omit "
    "sentiment for every other label.\n"
    "  - conflicts-with: the two cannot both be followed (incompatible).\n\n"
    "BATCH-UNION MEMBERSHIP: you may relate ANY A-side anchor in this batch to "
    "ANY B-side anchor in this batch — you are not limited to a fixed pairing. "
    "Emit one finding object per genuine relationship you find.\n\n"
    "SIDE-GUARD (strict): `source_clauses` MUST contain ONLY anchor IDs from the "
    "A-side list; `target_clauses` MUST contain ONLY anchor IDs from the B-side "
    "list. Never place a B-side id in source_clauses or an A-side id in "
    "target_clauses.\n\n"
    "OBJECT SHAPE:\n"
    '  {"summary": "...",\n'
    '   "label": "aligns-with|differs-on|conflicts-with",\n'
    '   "sentiment": "tighten|loosen|neutral" (ONLY on differs-on; omit '
    "otherwise),\n"
    '   "source_clauses": [<A-side anchor_id>, ...],\n'
    '   "target_clauses": [<B-side anchor_id>, ...],\n'
    '   "scope_note": "..." (optional)}\n\n'
    "CITATION RULE (strict): every anchor_id in `source_clauses` and "
    "`target_clauses` MUST be copied EXACTLY from the lists provided. Never "
    "invent, guess, reformat, or paraphrase an anchor id.\n\n"
    "Return ONLY a JSON array of these objects — no prose, no markdown. Return an "
    "empty array `[]` if there are no same-topic connections in this batch."
)


def _format_anchor_line(anchor: Anchor) -> str:
    return f"{anchor['anchor_id']}: {anchor['text']}"


def _batch_union_sides(
    anchor_index: AnchorIndex, batch: list[dict]
) -> tuple[list[str], list[str]]:
    """Return the de-duplicated A-side and B-side anchor ids in a batch, in
    first-seen order (only ids that resolve in the index are kept)."""
    a_ids: list[str] = []
    b_ids: list[str] = []
    for pair in batch:
        src = pair["source_anchor_id"]
        tgt = pair["target_anchor_id"]
        if src not in a_ids and anchor_index.get(src) is not None:
            a_ids.append(src)
        if tgt not in b_ids and anchor_index.get(tgt) is not None:
            b_ids.append(tgt)
    return a_ids, b_ids


def _finder_same_topic_batch(
    anchor_index: AnchorIndex, batch: list[dict], deployment: str
) -> list[dict]:
    """Call the mid-tier finder ONCE over a batch's anchor union.

    Builds the A-side / B-side anchor lists and sends them with
    ``SAME_TOPIC_FINDER_SYSTEM_PROMPT``. Raises ``LLMResponseError`` on an
    unparseable reply — the caller handles retry-once-then-skip.
    """
    a_ids, b_ids = _batch_union_sides(anchor_index, batch)
    a_block = "\n".join(
        _format_anchor_line(anchor_index.get(aid)) for aid in a_ids  # type: ignore[arg-type]
    )
    b_block = "\n".join(
        _format_anchor_line(anchor_index.get(bid)) for bid in b_ids  # type: ignore[arg-type]
    )
    user = (
        "A-side anchors (document A — 'we/ours'):\n"
        f"{a_block}\n\n"
        "B-side anchors (document B — 'they/theirs'):\n"
        f"{b_block}\n\n"
        "Find every same-topic connection between an A-side anchor and a B-side "
        "anchor."
    )
    raw = call_chat(deployment, SAME_TOPIC_FINDER_SYSTEM_PROMPT, user, max_tokens=8192)
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


def finder_same_topic_batched(
    anchor_index: AnchorIndex,
    candidates: list[dict],
    deployment: str = REASONING_DEPLOYMENT,
    batch_size: int = BATCH_SIZE,
) -> list[dict]:
    """Stage 3: run the same-topic finder over candidate pairs in batches.

    Chunks ``candidates`` into batches of ``batch_size`` and calls the finder
    once per batch. A batch whose call fails (unparseable / timeout /
    ``LLMResponseError``) is retried ONCE; a second failure skips the batch and
    logs every pair id it held, then the pipeline continues.
    """
    findings: list[dict] = []
    for start in range(0, len(candidates), batch_size):
        batch = candidates[start : start + batch_size]
        try:
            findings.extend(_finder_same_topic_batch(anchor_index, batch, deployment))
            continue
        except Exception as first_exc:  # noqa: BLE001
            logger.warning("same-topic batch failed once, retrying: %s", first_exc)
        try:
            findings.extend(_finder_same_topic_batch(anchor_index, batch, deployment))
        except Exception as second_exc:  # noqa: BLE001
            pair_ids = [
                f"{p['source_anchor_id']} × {p['target_anchor_id']}" for p in batch
            ]
            logger.warning(
                "same-topic batch skipped after retry (%s); dropped pairs: %s",
                second_exc,
                pair_ids,
            )
    return findings
