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
from typing import Any, Optional

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


def _load_axes_cache(document_id: str, axes_dir: Optional[Path] = None) -> dict:
    """Load a document's axes cache, or an empty scaffold when none exists.

    `axes_dir` defaults to the module-level `AXES_DIR` so the experiment runner
    and `scripts/run_finder_trace.py` keep their existing location; the
    Workstream Brain routes pass the per-workstream `axes/` dir instead.
    """
    path = (axes_dir or AXES_DIR) / f"axes-{document_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "document_id": document_id,
        "model": EXTRACTION_DEPLOYMENT,
        "anchors": [],
    }


def _write_axes_cache(
    document_id: str, cache: dict, axes_dir: Optional[Path] = None
) -> None:
    target = axes_dir or AXES_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"axes-{document_id}.json"
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
    axes_dir: Optional[Path] = None,
) -> dict[str, list[str]]:
    """Stage 1: extract per-anchor axes for one document, honouring the cache.

    A cache entry is a HIT only when BOTH its ``text_hash`` matches the current
    anchor text AND its ``axis_cap`` matches the current cap — a change in
    either forces re-extraction. The refreshed cache is written back to disk.

    ``axes_dir`` selects where that cache lives; it defaults to the module-level
    ``AXES_DIR`` (the experiment location) and the Workstream Brain routes pass
    the per-workstream ``axes/`` dir so a workstream's cache travels with it.

    Returns ``{anchor_id: [axis, ...]}`` for every anchor in the document.
    """
    anchors = anchor_index.by_document(document_id)
    cache = _load_axes_cache(document_id, axes_dir)
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
    _write_axes_cache(document_id, cache, axes_dir)
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
# Cosine (default, validated) over axis embeddings via Azure OpenAI's
# text-embedding-3-small deployment (same AZURE_FOUNDRY_API_KEY as the chat
# deployments); BM25 (fallback) is pure Python, zero cost. `retrieve_hybrid` is
# NOT ported (spec constraint). When cosine is requested but the embeddings
# endpoint is unavailable/errors, `retrieve` falls back to BM25 automatically.
# ---------------------------------------------------------------------------


_EMBED_CLIENT = None


def _get_embed_client() -> Any:
    """Lazy-init the Azure OpenAI client for embeddings, sharing the Foundry key."""
    global _EMBED_CLIENT
    if _EMBED_CLIENT is None:
        from openai import AzureOpenAI

        from engine.config import (
            AZURE_FOUNDRY_API_KEY,
            EMBEDDING_API_VERSION,
            EMBEDDING_ENDPOINT,
        )

        if not EMBEDDING_ENDPOINT or not AZURE_FOUNDRY_API_KEY:
            raise RuntimeError(
                "AZURE_FOUNDRY_ENDPOINT/AZURE_EMBEDDING_ENDPOINT and "
                "AZURE_FOUNDRY_API_KEY must be set to embed"
            )
        _EMBED_CLIENT = AzureOpenAI(
            api_key=AZURE_FOUNDRY_API_KEY,
            azure_endpoint=EMBEDDING_ENDPOINT,
            api_version=EMBEDDING_API_VERSION,
        )
    return _EMBED_CLIENT


def _embed_batch(
    texts: list[str],
    input_type: str = "search_document",
    output_dimension: int = 1536,
) -> list[list[float]]:
    """Embed a batch of texts via Azure OpenAI's text-embedding-3-small deployment.

    ``input_type`` is accepted for call-site compatibility with the previous
    Cohere path but ignored — text-embedding-3-small is symmetric, so query and
    document texts use the same embedding. Batched in chunks of 96 per call.
    """
    from engine.config import EMBEDDING_DEPLOYMENT

    client = _get_embed_client()
    all_embeddings: list[list[float]] = []
    for chunk_start in range(0, len(texts), 96):
        chunk = texts[chunk_start : chunk_start + 96]
        resp = client.embeddings.create(
            model=EMBEDDING_DEPLOYMENT,
            input=chunk,
            dimensions=output_dimension,
        )
        all_embeddings.extend(item.embedding for item in resp.data)
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

# The three agreement-type labels the same-topic stage may carry. Coverage
# labels (silent-on / goes-beyond) are the whole-doc pass's job and are rejected
# if the finder leaks one into this stage.
SAME_TOPIC_LABELS = ("aligns-with", "differs-on", "conflicts-with")

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
    "SUMMARY PHRASING RULE (strict): write `summary` as ONE plain sentence, at "
    "most 20 words, in everyday professional English a policy drafter grasps on "
    "the first read. State plainly what OUR side does and what THEIR side does; "
    "do not merely restate the label (never write bare phrasing like 'these "
    "align' or 'these differ'). Use a specialist regulatory term only if it "
    "appears in the cited clause text; otherwise use a plain equivalent. Do not "
    "use em dashes. Put any qualifying nuance in `scope_note` (one plain "
    "sentence, at most 30 words), never stacked into the summary.\n\n"
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
    # Taxonomy validation: the same-topic stage may carry ONLY the three
    # agreement-type labels. A coverage label (silent-on / goes-beyond) leaking
    # out of this stage is rejected here — coverage is the whole-doc pass's job.
    return [finding for finding in parsed if finding.get("label") in SAME_TOPIC_LABELS]


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


# ---------------------------------------------------------------------------
# Stage 4 — suppression build [no model]. Ported verbatim from the experiment.
#
# A retrieval candidate contributes to suppression only when its A-side anchor
# produced a surviving same-topic finding (appears in that finding's
# source_clauses). Those candidates' matched axes become covered_topics and
# their anchor pair becomes a covered_pair.
# ---------------------------------------------------------------------------


def _build_suppression(
    retrieval_candidates: list[dict], same_topic_findings: list[dict]
) -> dict:
    """Build the suppression dict from same-topic stage outputs.

    Returns ``{"covered_pairs": ["A × B", ...], "covered_topics": [axis, ...]}``,
    both sorted and de-duplicated.
    """
    covered_sources: set[str] = set()
    for finding in same_topic_findings:
        for clause in finding.get("source_clauses", []):
            covered_sources.add(clause)

    covered_pairs: set[tuple[str, str]] = set()
    covered_topics: set[str] = set()
    for candidate in retrieval_candidates:
        src = candidate.get("source_anchor_id", "")
        tgt = candidate.get("target_anchor_id", "")
        if src in covered_sources:
            covered_pairs.add((src, tgt))
            axis_src = candidate.get("matched_axis_source")
            axis_tgt = candidate.get("matched_axis_target")
            if axis_src:
                covered_topics.add(axis_src)
            if axis_tgt:
                covered_topics.add(axis_tgt)

    return {
        "covered_pairs": sorted(f"{a} × {b}" for a, b in covered_pairs),
        "covered_topics": sorted(covered_topics),
    }


# ---------------------------------------------------------------------------
# Stage 5 — whole-doc coverage finder [FINDER_CRITIC_DEPLOYMENT]. ONE call, no
# critic. silent-on / goes-beyond only, with the three-part COVERAGE-SUMMARY
# RULE and the "both sides take a position = not a coverage finding" guardrail.
# COVERAGE_FINDER_SYSTEM_PROMPT ported from the experiment runner.
# ---------------------------------------------------------------------------

COVERAGE_FINDER_SYSTEM_PROMPT = (
    "You are a policy analyst identifying COVERAGE GAPS between two Bank Negara "
    "Malaysia policy documents. Your task is to find sub-topics where exactly "
    "one side has a provision and the other side is entirely silent.\n\n"
    "LABEL RESTRICTION (strict): you MUST emit ONLY findings with label "
    "`silent-on` or `goes-beyond`. Never emit `aligns-with`, `differs-on`, or "
    "`conflicts-with` — those are for a separate same-topic pass. If no genuine "
    "coverage gap exists, return an empty array.\n\n"
    "DIRECTION CONVENTION (fixed): document A is 'we/ours'; document B is "
    "'they/theirs'.\n"
    "  - goes-beyond: OUR side (document A) covers a sub-topic; THEIR side "
    "(document B) has no provision for it anywhere in the document.\n"
    "  - silent-on: OUR side (document A) has no provision for a sub-topic; "
    "THEIR side (document B) covers it.\n\n"
    "COVERAGE-SUMMARY RULE: keep the `summary` short and readable, and put the "
    "detail in `scope_note`. Do NOT stack multiple points into the summary.\n"
    "  - `summary`: ONE plain sentence, at most 20 words, in everyday "
    "professional English a policy drafter grasps on the first read. Name the "
    "shared regulatory topic and state plainly which side covers it and which "
    "side is silent (e.g. 'The draft requires a tested exit plan per provider; "
    "the BCBS principles do not.'). Do not merely restate the label. Do not use "
    "em dashes.\n"
    "  - `scope_note`: ONE plain sentence, at most 30 words, naming the specific "
    "obligation or sub-point the silent side does NOT address — not just 'does "
    "not cover this'. This is where the precise detail belongs.\n"
    "  - Use a specialist regulatory term only if it appears in the cited clause "
    "text; otherwise use a plain equivalent.\n\n"
    "GUARDRAIL: If both sides take a position on this topic — even if different "
    "— that is NOT a coverage finding. Do not emit it. Only emit a finding when "
    "one side genuinely has no provision for the sub-point. A stricter rule on "
    "one side is NOT a gap; it is a 'differs-on' finding and belongs in the "
    "same-topic pass.\n\n"
    "OBJECT SHAPE:\n"
    '  {"summary": "...", "label": "silent-on|goes-beyond",\n'
    '   "source_clauses": [...], "target_clauses": [...], "scope_note": "..."}\n\n'
    "For `goes-beyond`: `source_clauses` is non-empty (A covers it); "
    "`target_clauses` is empty, or holds the nearest B clause cited only to "
    "confirm it does not address this sub-point.\n"
    "For `silent-on`: `target_clauses` is non-empty (B covers it); "
    "`source_clauses` is empty, or holds the nearest A clause cited only to "
    "confirm it does not address this sub-point.\n\n"
    "Do NOT include a `sentiment` field — coverage labels never carry "
    "sentiment.\n\n"
    "CITATION RULE (strict): every clause_number in `source_clauses` and "
    "`target_clauses` MUST be copied EXACTLY from the clause lists provided. "
    "Never invent, guess, reformat, or paraphrase a clause number. Do not cite "
    "a clause that is not in the lists.\n\n"
    "Return ONLY a JSON array of these objects — no prose, no markdown, no "
    "commentary. Return an empty array `[]` if there are no genuine coverage "
    "gaps."
)


def _format_doc_block(anchor_index: AnchorIndex, document_id: str) -> str:
    """List every anchor of a document as ``{anchor_id}: {text}`` lines."""
    lines = [f"Document: {document_id}"]
    for a in anchor_index.by_document(document_id):
        lines.append(_format_anchor_line(a))
    return "\n\n".join(lines)


def finder_coverage_whole_doc(
    anchor_index: AnchorIndex,
    doc_a: str,
    doc_b: str,
    suppression: dict,
    deployment: str = FINDER_CRITIC_DEPLOYMENT,
) -> list[dict]:
    """Stage 5: whole-document coverage finder — ONE call, no critic.

    Sends both documents' full anchor lists in one prompt with
    ``COVERAGE_FINDER_SYSTEM_PROMPT`` (silent-on / goes-beyond only). Appends the
    suppression block listing already-covered topics when non-empty so the model
    does not re-report them. Raises ``LLMResponseError`` on a non-list reply.
    """
    user = (
        _format_doc_block(anchor_index, doc_a)
        + "\n\n"
        + _format_doc_block(anchor_index, doc_b)
    )
    covered_topics = suppression.get("covered_topics", [])
    if covered_topics:
        user += (
            "\n\nTOPICS ALREADY COVERED ON BOTH SIDES — do NOT report these as "
            "coverage gaps:\n" + "\n".join(f"  - {t}" for t in covered_topics)
        )
    raw = call_chat(deployment, COVERAGE_FINDER_SYSTEM_PROMPT, user, max_tokens=16384)
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


def _is_single_sided(finding: dict) -> bool:
    """True if the coverage finding has exactly one non-empty clause side.

    - goes-beyond: source_clauses non-empty AND target_clauses empty.
    - silent-on: source_clauses empty AND target_clauses non-empty.
    - anything else: False.
    """
    src = finding.get("source_clauses") or []
    tgt = finding.get("target_clauses") or []
    label = finding.get("label")
    if label == "goes-beyond":
        return bool(src) and not bool(tgt)
    if label == "silent-on":
        return not bool(src) and bool(tgt)
    return False


def _is_redundant(finding: dict, suppression: dict) -> bool:
    """True if this coverage finding overlaps the suppression set.

    True when any covered_topic (case-insensitive) is a substring of the
    finding's summary, OR any cited anchor appears in the covered_pairs strings.
    """
    covered_topics = [t.lower() for t in suppression.get("covered_topics", [])]
    summary_lower = (finding.get("summary") or "").lower()
    if any(t in summary_lower for t in covered_topics if t):
        return True
    covered_pairs_str = " ".join(suppression.get("covered_pairs", []))
    all_clauses = (finding.get("source_clauses") or []) + (
        finding.get("target_clauses") or []
    )
    return any(clause in covered_pairs_str for clause in all_clauses if clause)


# ---------------------------------------------------------------------------
# Stage 6 — merge + reformat + validate [no model].
#
# The deterministic citation reformatter runs ONLY on a cited id that fails the
# exact index lookup. It applies reversible, unambiguous transforms in order and
# returns (normalized_id, transform_name) on success or None (→ demote). NO
# fuzzy / substring / semantic matching — an id that only partially resembles a
# real anchor is NOT rescued. Then engine.connections._validate_candidates
# splits into connections / unsupported, reused UNCHANGED via the ClauseIndex shim.
# ---------------------------------------------------------------------------


def _document_prefix(document_id: str, index: AnchorIndex) -> Optional[str]:
    """Derive the document's anchor-id prefix from the index, not hardcoded.

    ``index.by_document(document_id)[0]["anchor_id"].rsplit(" ", 1)[0]`` — e.g.
    ``"RMiT 2.1"`` → ``"RMiT"``. Returns ``None`` when the document has no
    anchors (nothing to derive a prefix from).
    """
    anchors = index.by_document(document_id)
    if not anchors:
        return None
    first_id = anchors[0]["anchor_id"]
    parts = first_id.rsplit(" ", 1)
    if len(parts) < 2:
        return None
    return parts[0]


def _reformat_citation(
    cited: str, document_id: str, index: AnchorIndex
) -> Optional[tuple[str, str]]:
    """Deterministically recover punctuation/prefix drift on a failed citation.

    Runs ONLY on a cited id that already failed the exact index lookup. Applies
    reversible transforms in order:

    1. ``strip_trailing_punct`` — ``cited.rstrip(" .:;,")``; re-check the index.
    2. ``restore_prefix`` — if the stripped id does not start with the
       document's derived prefix, prepend it; re-check the index.

    Returns ``(normalized_id, transform_name)`` on success, or ``None`` (→ demote
    to unsupported). NO fuzzy / substring / semantic matching.
    """
    stripped = cited.rstrip(" .:;,")
    if stripped != cited and index.get(stripped) is not None:
        return stripped, "strip_trailing_punct"

    prefix = _document_prefix(document_id, index)
    if prefix and not stripped.startswith(prefix + " "):
        restored = f"{prefix} {stripped}"
        if index.get(restored) is not None:
            return restored, "restore_prefix"

    return None


def _reformat_side(
    numbers: list[str],
    document_id: str,
    index: AnchorIndex,
    rewrites: list[dict],
) -> list[str]:
    """Reformat every cited id on one side (source or target) that fails an
    exact lookup. Resolving rewrites are applied and recorded in ``rewrites``;
    unresolvable ids are left as-is so ``_validate_candidates`` demotes them."""
    out: list[str] = []
    for number in numbers:
        if index.get(number) is not None:
            out.append(number)
            continue
        recovered = _reformat_citation(number, document_id, index)
        if recovered is None:
            out.append(number)
            continue
        normalized, transform = recovered
        rewrites.append(
            {
                "cited_raw": number,
                "cited_normalized": normalized,
                "transform": transform,
            }
        )
        out.append(normalized)
    return out


def merge_reformat_validate(
    same_topic_raw: list[dict],
    coverage_raw: list[dict],
    anchor_index: AnchorIndex,
    doc_a: str,
    doc_b: str,
) -> tuple[list, list, list, list[dict]]:
    """Stage 6: reformat drifted citations, then validate the merged findings.

    Source clauses are reformatted against ``doc_a``'s prefix, target clauses
    against ``doc_b``'s. After reformatting, ``_validate_candidates`` (reused
    unchanged, via the ClauseIndex shim) splits everything into connections /
    unsupported.

    Returns ``(connections, unsupported, validation, citation_rewrites)``.
    """
    rewrites: list[dict] = []
    merged: list[dict] = []
    for finding in same_topic_raw + coverage_raw:
        rewritten = dict(finding)
        rewritten["source_clauses"] = _reformat_side(
            finding.get("source_clauses", []) or [], doc_a, anchor_index, rewrites
        )
        rewritten["target_clauses"] = _reformat_side(
            finding.get("target_clauses", []) or [], doc_b, anchor_index, rewrites
        )
        merged.append(rewritten)

    clause_shim = _AnchorAsClauseIndex(anchor_index)
    connections, unsupported, validation = _validate_candidates(merged, clause_shim)
    return connections, unsupported, validation, rewrites


# ---------------------------------------------------------------------------
# Orchestration — run all six stages in order and return the result dict.
# ---------------------------------------------------------------------------


def run_arm_g(
    anchor_index: AnchorIndex,
    doc_a: str,
    doc_b: str,
    signal: str = "cosine",
    axes_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Run the six-stage Arm G pipeline and return a result dict.

    Args:
        anchor_index: the built anchor index for both documents.
        doc_a: document-A identifier (the "our side").
        doc_b: document-B identifier (the "their side").
        signal: retrieval method — ``"cosine"`` (default, auto-falls-back to
            BM25 when embeddings are unavailable) or ``"bm25"`` (forced).
        axes_dir: where stage 1's axis cache lives. Defaults to ``AXES_DIR``;
            the workstream analyze route passes that workstream's ``axes/`` dir
            so a cache warmed by "Extract concepts" is reused here.

    Returns a dict with ``connections``, ``unsupported``, and a ``trace``
    sub-dict holding ``retrieval_candidates``, ``same_topic_finder_output``,
    ``suppression``, ``coverage_finder_output`` (each entry carrying computed
    ``single_sided`` / ``redundant``), ``validation``, ``citation_rewrites``,
    ``counts`` and ``wall_clock_seconds``. Connections keep ``scope_note``. No
    ``metadata.json`` concept — the route (Story 3) decides file writing.
    """
    start = time.time()

    # Stage 1 — axis extraction (small model, cached).
    axes_a = extract_axes_for_document(anchor_index, doc_a, axes_dir=axes_dir)
    axes_b = extract_axes_for_document(anchor_index, doc_b, axes_dir=axes_dir)

    # Stage 2 — same-topic retrieval (no model).
    candidates = retrieve(axes_a, axes_b, signal=signal)

    # Stage 3 — batched same-topic finder (mid-tier model, no critic).
    same_topic_raw = finder_same_topic_batched(anchor_index, candidates)

    # Stage 4 — suppression build (no model).
    suppression = _build_suppression(candidates, same_topic_raw)

    # Stage 5 — whole-doc coverage finder (large model, one call, no critic).
    try:
        coverage_raw = finder_coverage_whole_doc(
            anchor_index, doc_a, doc_b, suppression
        )
    except LLMResponseError as exc:
        logger.warning("coverage whole-doc finder failed: %s", exc)
        coverage_raw = []

    # Stage 6 — merge + reformat + validate (no model).
    connections, unsupported, validation, rewrites = merge_reformat_validate(
        same_topic_raw, coverage_raw, anchor_index, doc_a, doc_b
    )

    coverage_output = [
        {
            **finding,
            "single_sided": _is_single_sided(finding),
            "redundant": _is_redundant(finding, suppression),
        }
        for finding in coverage_raw
    ]

    return {
        "connections": connections,
        "unsupported": unsupported,
        "trace": {
            "retrieval_candidates": candidates,
            "same_topic_finder_output": same_topic_raw,
            "suppression": suppression,
            "coverage_finder_output": coverage_output,
            "validation": validation,
            "citation_rewrites": rewrites,
            "counts": {
                "supported": len(connections),
                "unsupported": len(unsupported),
                "same_topic_finding": len(same_topic_raw),
                "coverage_finding": len(coverage_raw),
            },
            "wall_clock_seconds": round(time.time() - start, 1),
        },
    }
