#!/usr/bin/env python3
"""Retrieval-strategy ablation runner (docs/specs/workstream-brain/experiment-retrieval-ablation.md).

Runs one arm on one pair, writes findings + trace + metadata to
`experiments/retrieval-ablation/{arm}/{pair}/`. Arms:

- **B**: AnchorIndex → finder(all anchors) → critic → validate (whole-doc pairwise)
- **C**: axes → cosine-only retrieval → per-pair finder → critic → validate
- **D**: axes → BM25+cosine+glossary hybrid → per-pair finder → critic → validate

All three share the same finder/critic prompts (in engine/connections.py); the
difference is how many candidate pairs the finder sees per call.

Usage:
    python scripts/experiments/retrieval_ablation.py --arm B --pair bis-ed
    python scripts/experiments/retrieval_ablation.py --arm C --pair hkma-ed
    python scripts/experiments/retrieval_ablation.py --arm all --pair all
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.anchors import Anchor, AnchorIndex  # noqa: E402
from engine.clauses import ClauseIndex  # noqa: E402
from engine.config import FINDER_CRITIC_DEPLOYMENT  # noqa: E402
from engine.connections import (  # noqa: E402
    CRITIC_SYSTEM_PROMPT,
    FINDER_SYSTEM_PROMPT,
    _validate_candidates,
)
from engine.llm import LLMResponseError, call_chat, parse_json_response  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Coverage-stage system prompt — local to this runner, NOT in engine/connections.py.
#
# Restricts finder output to ONLY `silent-on` and `goes-beyond` labels.
# Embeds the COVERAGE-SUMMARY RULE and the explicit "both sides" guardrail.
# Reuses the same CITATION RULE and JSON-array output contract as FINDER_SYSTEM_PROMPT.
# Sentiment is intentionally omitted — coverage labels never carry sentiment
# per the five-label taxonomy.
# ---------------------------------------------------------------------------

COVERAGE_FINDER_SYSTEM_PROMPT = (
    "You are a policy analyst identifying COVERAGE GAPS between two Bank Negara Malaysia "
    "policy documents. Your task is to find sub-topics where exactly one side has a "
    "provision and the other side is entirely silent.\n\n"
    "LABEL RESTRICTION (strict): you MUST emit ONLY findings with label `silent-on` or "
    "`goes-beyond`. Never emit `aligns-with`, `differs-on`, or `conflicts-with` — those "
    "are for a separate same-topic pass. If no genuine coverage gap exists, return an "
    "empty array.\n\n"
    "DIRECTION CONVENTION (fixed): document A is 'we/ours'; document B is 'they/theirs'.\n"
    "  - goes-beyond: OUR side (document A) covers a sub-topic; THEIR side (document B) "
    "has no provision for it anywhere in the document.\n"
    "  - silent-on: OUR side (document A) has no provision for a sub-topic; THEIR side "
    "(document B) covers it.\n\n"
    "COVERAGE-SUMMARY RULE: every finding summary MUST do all three of the following:\n"
    "  1. Name the shared regulatory topic that both documents sit under (e.g. 'open API "
    "security', 'consent management', 'third-party access').\n"
    "  2. State what the COVERING side specifically requires or addresses on that sub-topic.\n"
    "  3. State precisely what the OTHER side does NOT address — name the specific "
    "obligation or sub-point that is absent, not just 'does not cover this'.\n\n"
    "GUARDRAIL: If both sides take a position on this topic — even if different — that is "
    "NOT a coverage finding. Do not emit it. Only emit a finding when one side genuinely "
    "has no provision for the sub-point. A stricter rule on one side is NOT a gap; it is "
    "a 'differs-on' finding and belongs in the same-topic pass.\n\n"
    "OBJECT SHAPE:\n"
    '  {"summary": "...", "label": "silent-on|goes-beyond",\n'
    '   "source_clauses": [...], "target_clauses": [...], "scope_note": "..."}\n\n'
    "For `goes-beyond`: `source_clauses` is non-empty (A covers it); `target_clauses` is "
    "empty, or holds the nearest B clause cited only to confirm it does not address this "
    "sub-point.\n"
    "For `silent-on`: `target_clauses` is non-empty (B covers it); `source_clauses` is "
    "empty, or holds the nearest A clause cited only to confirm it does not address this "
    "sub-point.\n\n"
    "Do NOT include a `sentiment` field — coverage labels never carry sentiment.\n\n"
    "CITATION RULE (strict): every clause_number in `source_clauses` and `target_clauses` "
    "MUST be copied EXACTLY from the clause lists provided. Never invent, guess, reformat, "
    "or paraphrase a clause number. Do not cite a clause that is not in the lists.\n\n"
    "Return ONLY a JSON array of these objects — no prose, no markdown, no commentary. "
    "Return an empty array `[]` if there are no genuine coverage gaps."
)

ANCHOR_INDEX_PATH = REPO_ROOT / "data" / "artifacts" / "anchor-index.json"
AXES_DIR = REPO_ROOT / "experiments"
RESULTS_DIR = REPO_ROOT / "experiments" / "retrieval-ablation"
GLOSSARY_PATH = REPO_ROOT / "data" / "glossary.json"

# Pairs — short_id → (doc_a_id, doc_b_id). Convention: doc_a = ED (our side),
# doc_b = peer (their side), consistent with the direction convention.
PAIRS: dict[str, tuple[str, str]] = {
    "bis-ed": ("bnm-open-finance-ed-2025", "bis-pap168-open-finance"),
    "hkma-ed": ("bnm-open-finance-ed-2025", "hkma-open-api-framework-2018"),
    "rmit-ed": ("bnm-open-finance-ed-2025", "bnm-rmit-nov25"),
}


# ---------------------------------------------------------------------------
# AnchorIndex-shim ClauseIndex so we can reuse engine.connections._validate_candidates
# and format helpers without touching them. _validate_candidates expects a
# ClauseIndex — we wrap an AnchorIndex to expose the same .get(number) semantics.
# ---------------------------------------------------------------------------


class _AnchorAsClauseIndex:
    """Wrap AnchorIndex to satisfy the ClauseIndex-shape API._validate_candidates uses.

    The two methods `_validate_candidates` touches are `.get(number)` and reading
    entry["text"]. AnchorIndex.get returns an Anchor with 'text', so the wrapper
    just delegates.
    """

    def __init__(self, anchor_index: AnchorIndex) -> None:
        self._ai = anchor_index

    def get(self, number: str, version: Optional[str] = None):
        return self._ai.get(number)

    def entries_for_document(self, document_id: str):
        return self._ai.by_document(document_id)


# ---------------------------------------------------------------------------
# Axis + glossary loaders
# ---------------------------------------------------------------------------


def _load_axes(document_id: str) -> dict[str, list[str]]:
    """anchor_id → list of axes."""
    path = AXES_DIR / f"axes-{document_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"no axes cache at {path} — run extract_axes.py first")
    cache = json.loads(path.read_text(encoding="utf-8"))
    return {entry["anchor_id"]: entry["axes"] for entry in cache["anchors"]}


def _load_glossary() -> dict[str, list[str]]:
    """canonical_axis → aliases (case-insensitive lookup at query time)."""
    if not GLOSSARY_PATH.exists():
        logger.warning(
            "no glossary at %s — Arm D will effectively degrade to Arm C", GLOSSARY_PATH
        )
        return {}
    g = json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    aliases: dict[str, list[str]] = {}
    for entry in g.get("entries", []):
        canonical = entry["canonical"].lower()
        variants = [entry["canonical"]] + entry.get("aliases", [])
        aliases[canonical] = variants
        for alias in entry.get("aliases", []):
            aliases[alias.lower()] = variants
    return aliases


def _expand_axis(axis: str, glossary: dict[str, list[str]]) -> list[str]:
    """Given an axis, return itself plus any glossary aliases (case-insensitive)."""
    hits = glossary.get(axis.lower())
    if hits is None:
        return [axis]
    return list(set([axis] + hits))


# ---------------------------------------------------------------------------
# Retrieval implementations
# ---------------------------------------------------------------------------


_BEDROCK_CLIENT = None


def _get_bedrock_client():
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

    `input_type` should be `search_document` for corpus-side texts and
    `search_query` for retrieval-side queries — Cohere's asymmetric embedding
    trained this way, and using the same type on both sides degrades quality.

    Cohere embed-v4 accepts up to 96 texts per call; we chunk automatically.
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
    """BM25 scores for `query` against each corpus text. Returns unnormalised scores."""
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning(
            "rank_bm25 not installed — BM25 hits will all be zero (Arm D degrades to Arm C)"
        )
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
    """Arm C: cosine over axis embeddings, per-A-anchor top-K, global cap.

    Symmetric to Arms E/F's tuned shape: for each SOURCE ANCHOR (not each
    axis), aggregate cosine scores across all its axes against each B anchor
    (max across axis pairings), keep top-K target anchors per source above
    `floor`, then apply a global top-N cap. Cheaper and yields comparably-
    scaled candidate counts.
    """
    ids_b = list(axes_b.keys())
    b_flat_axes: list[str] = []
    b_axis_owner: list[str] = []
    for aid in ids_b:
        for ax in axes_b[aid]:
            b_flat_axes.append(ax)
            b_axis_owner.append(aid)

    logger.info("embedding %d B-side axes as search_document...", len(b_flat_axes))
    b_embeds = _embed_batch(b_flat_axes, input_type="search_document")

    all_a_axes = [ax for aid, axs in axes_a.items() for ax in axs]
    a_axis_owner = [aid for aid, axs in axes_a.items() for _ in axs]
    logger.info("embedding %d A-side axes as search_query...", len(all_a_axes))
    a_embeds = _embed_batch(all_a_axes, input_type="search_query")

    # Index B-axis positions by anchor
    b_axis_idx_by_anchor: dict[str, list[int]] = {}
    for j, aid in enumerate(b_axis_owner):
        b_axis_idx_by_anchor.setdefault(aid, []).append(j)

    # Compute a_axis embeddings by their source anchor
    a_axis_by_anchor: dict[str, list[tuple[str, list[float]]]] = {}
    for a_axis, aid, emb in zip(all_a_axes, a_axis_owner, a_embeds):
        a_axis_by_anchor.setdefault(aid, []).append((a_axis, emb))

    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for a_id, axis_embeds in a_axis_by_anchor.items():
        # For each A anchor: aggregate cosine against each B anchor (best
        # (a_axis, b_axis) pairing)
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
    # Global cap by cosine similarity
    ranked = sorted(candidates.values(), key=lambda c: -c["similarity"])
    return ranked[:global_max_pairs]


def retrieve_hybrid(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    glossary: dict[str, list[str]],
    top_k_per_anchor: int = 2,
    rrf_k: int = 60,
    global_max_pairs: int = 60,
) -> list[dict[str, Any]]:
    """Arm D: BM25 + cosine + glossary, per-A-anchor top-K, global cap.

    Same shape as Arms C/E/F for comparability: aggregate at the source-anchor
    level. For each source anchor, for each of its axes, compute BM25 ranks
    (against glossary-expanded query) and cosine ranks (against axis embedding)
    over all B-side axes, then fuse via reciprocal-rank. Per (source, target)
    anchor pair, keep the best-fusion axis pairing. Take top-K target anchors
    per source, then apply a global cap on total pairs.
    """
    ids_b = list(axes_b.keys())
    b_flat_axes: list[str] = []
    b_axis_owner: list[str] = []
    for aid in ids_b:
        for ax in axes_b[aid]:
            b_flat_axes.append(ax)
            b_axis_owner.append(aid)

    logger.info("embedding %d B-side axes as search_document...", len(b_flat_axes))
    b_embeds = _embed_batch(b_flat_axes, input_type="search_document")

    all_a_axes = [ax for aid, axs in axes_a.items() for ax in axs]
    a_axis_owner = [aid for aid, axs in axes_a.items() for _ in axs]
    logger.info("embedding %d A-side axes as search_query...", len(all_a_axes))
    a_embeds = _embed_batch(all_a_axes, input_type="search_query")

    # Group A-side axes by their source anchor (axis text + embedding)
    a_axis_by_anchor: dict[str, list[tuple[str, list[float]]]] = {}
    for a_axis, aid, emb in zip(all_a_axes, a_axis_owner, a_embeds):
        a_axis_by_anchor.setdefault(aid, []).append((a_axis, emb))

    # Precompute B-axis indices grouped by their target anchor
    b_axis_idx_by_anchor: dict[str, list[int]] = {}
    for j, aid in enumerate(b_axis_owner):
        b_axis_idx_by_anchor.setdefault(aid, []).append(j)

    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for a_id, axis_embeds in a_axis_by_anchor.items():
        # b_scores[b_id] = (best_fusion, best_cosine, best_bm25, a_axis, b_axis, glossary_hits)
        b_scores: dict[str, tuple[float, float, float, str, str, Any]] = {}
        for a_axis, a_embed in axis_embeds:
            expanded = _expand_axis(a_axis, glossary)
            combined_query = " ".join(expanded)
            glossary_hits = expanded[1:] if len(expanded) > 1 else None

            # Cosine ranks over all B-side axes
            cosine_scores_flat = [_cosine(a_embed, b_emb) for b_emb in b_embeds]
            cosine_order = sorted(
                range(len(cosine_scores_flat)),
                key=lambda j: -cosine_scores_flat[j],
            )
            cosine_rank = {j: r for r, j in enumerate(cosine_order)}

            # BM25 ranks (on the expanded query) over all B-side axes
            bm25_scores_flat = _bm25_hits(combined_query, b_flat_axes)
            bm25_order = sorted(
                range(len(bm25_scores_flat)),
                key=lambda j: -bm25_scores_flat[j],
            )
            bm25_rank = {j: r for r, j in enumerate(bm25_order)}

            # For each B anchor, find its best-fusion axis
            for b_id, idxs in b_axis_idx_by_anchor.items():
                best_j = max(
                    idxs,
                    key=lambda j: 1.0 / (rrf_k + cosine_rank[j])
                    + 1.0 / (rrf_k + bm25_rank[j]),
                )
                fusion = 1.0 / (rrf_k + cosine_rank[best_j]) + 1.0 / (
                    rrf_k + bm25_rank[best_j]
                )
                existing = b_scores.get(b_id)
                if existing is None or existing[0] < fusion:
                    b_scores[b_id] = (
                        fusion,
                        cosine_scores_flat[best_j],
                        float(bm25_scores_flat[best_j]),
                        a_axis,
                        b_flat_axes[best_j],
                        glossary_hits,
                    )

        # Keep top-K B anchors per source anchor by fusion score
        top = sorted(b_scores.items(), key=lambda kv: -kv[1][0])[:top_k_per_anchor]
        for b_id, (fusion, cos, bm25, a_axis, b_axis, glossary_hits) in top:
            key = (a_id, b_id)
            signal = "hybrid+glossary" if glossary_hits else "hybrid"
            candidates[key] = {
                "source_anchor_id": a_id,
                "target_anchor_id": b_id,
                "matched_axis_source": a_axis,
                "matched_axis_target": b_axis,
                "similarity": cos,
                "bm25_score": bm25,
                "fusion_score": fusion,
                "glossary_expansion": glossary_hits,
                "signal": signal,
            }

    # Global cap by fusion score
    ranked = sorted(candidates.values(), key=lambda c: -c["fusion_score"])
    return ranked[:global_max_pairs]


def _bm25_retrieve_per_anchor(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    expand_query: Any = None,
    top_k_per_anchor: int = 3,
    score_floor: float = 5.0,
    global_max_pairs: int = 60,
) -> list[dict[str, Any]]:
    """Shared BM25 retrieval — used by Arms E and F.

    For each SOURCE ANCHOR (not each axis): run BM25 for each of its axes
    against side B's axes, aggregate scores at the target-anchor level (max
    across B's axes and across the source's axes), take top-K target anchors
    per source anchor above `score_floor`, and record the strongest matching
    (source_axis, target_axis) pair.

    `expand_query` is optional and, if provided, transforms a source axis
    into a query string (e.g. axis + glossary aliases). If None, the axis is
    used verbatim.

    Returns candidate pairs deduplicated to unique (source_anchor, target_anchor).
    """
    ids_b = list(axes_b.keys())
    b_flat_axes: list[str] = []
    b_axis_owner: list[str] = []
    for aid in ids_b:
        for ax in axes_b[aid]:
            b_flat_axes.append(ax)
            b_axis_owner.append(aid)

    # Group B-side axis indices by anchor id
    b_axis_idx_by_anchor: dict[str, list[int]] = {}
    for j, aid in enumerate(b_axis_owner):
        b_axis_idx_by_anchor.setdefault(aid, []).append(j)

    candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for a_id, a_axes in axes_a.items():
        # For each source anchor, aggregate BM25 scores against every B anchor.
        # b_scores[b_id] = (best_score, best_source_axis, best_target_axis, glossary_expansion)
        b_scores: dict[str, tuple[float, str, str, Any]] = {}
        for a_axis in a_axes:
            expanded = expand_query(a_axis) if expand_query else [a_axis]
            query_str = " ".join(expanded)
            scores = _bm25_hits(query_str, b_flat_axes)
            # For each B anchor, take its best-scoring axis
            for b_id, idxs in b_axis_idx_by_anchor.items():
                best_j = max(idxs, key=lambda j: scores[j])
                best_score = float(scores[best_j])
                if best_score < score_floor:
                    continue
                existing = b_scores.get(b_id)
                if existing is None or existing[0] < best_score:
                    b_scores[b_id] = (
                        best_score,
                        a_axis,
                        b_flat_axes[best_j],
                        expanded[1:] if len(expanded) > 1 else None,
                    )
        # Keep top-K B anchors for this source anchor
        top = sorted(b_scores.items(), key=lambda kv: -kv[1][0])[:top_k_per_anchor]
        for b_id, (score, a_axis, b_axis, glossary_hits) in top:
            key = (a_id, b_id)
            signal = "bm25+glossary" if glossary_hits else "bm25"
            candidates[key] = {
                "source_anchor_id": a_id,
                "target_anchor_id": b_id,
                "matched_axis_source": a_axis,
                "matched_axis_target": b_axis,
                "bm25_score": score,
                "glossary_expansion": glossary_hits,
                "signal": signal,
            }
    # Global cap by score: keep top N overall, prioritising glossary hits at
    # equal score so glossary's incremental value can be measured.
    ranked = sorted(
        candidates.values(),
        key=lambda c: (c["bm25_score"], 1 if c.get("glossary_expansion") else 0),
        reverse=True,
    )
    return ranked[:global_max_pairs]


def retrieve_bm25_only(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    top_k_per_anchor: int = 2,
    score_floor: float = 5.0,
    global_max_pairs: int = 60,
) -> list[dict[str, Any]]:
    """Arm E: BM25 retrieval only. No embeddings, no glossary."""
    return _bm25_retrieve_per_anchor(
        axes_a,
        axes_b,
        expand_query=None,
        top_k_per_anchor=top_k_per_anchor,
        score_floor=score_floor,
        global_max_pairs=global_max_pairs,
    )


def retrieve_bm25_glossary(
    axes_a: dict[str, list[str]],
    axes_b: dict[str, list[str]],
    glossary: dict[str, list[str]],
    top_k_per_anchor: int = 2,
    score_floor: float = 5.0,
    global_max_pairs: int = 60,
) -> list[dict[str, Any]]:
    """Arm F: BM25 with glossary alias expansion. No embeddings."""
    return _bm25_retrieve_per_anchor(
        axes_a,
        axes_b,
        expand_query=lambda axis: _expand_axis(axis, glossary),
        top_k_per_anchor=top_k_per_anchor,
        score_floor=score_floor,
        global_max_pairs=global_max_pairs,
    )


# ---------------------------------------------------------------------------
# Finder + critic — reuse engine.connections prompts with per-pair or whole-doc user prompts
# ---------------------------------------------------------------------------


def _format_anchor_block(anchor: Anchor) -> str:
    return f"{anchor['anchor_id']}: {anchor['text']}"


def _format_doc_block(anchor_index: AnchorIndex, document_id: str) -> str:
    """List every anchor of a document. Used by Arm B."""
    lines = [f"Document: {document_id}"]
    for a in anchor_index.by_document(document_id):
        lines.append(_format_anchor_block(a))
    return "\n\n".join(lines)


def _finder_whole_doc(anchor_index: AnchorIndex, doc_a: str, doc_b: str) -> list[dict]:
    """Arm B: send both docs' full anchor lists in one prompt."""
    user = (
        _format_doc_block(anchor_index, doc_a)
        + "\n\n"
        + _format_doc_block(anchor_index, doc_b)
    )
    raw = call_chat(
        FINDER_CRITIC_DEPLOYMENT, FINDER_SYSTEM_PROMPT, user, max_tokens=16384
    )
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


def _critic_whole_doc(
    anchor_index: AnchorIndex, doc_a: str, doc_b: str, candidates: list[dict]
) -> list[dict]:
    context = (
        _format_doc_block(anchor_index, doc_a)
        + "\n\n"
        + _format_doc_block(anchor_index, doc_b)
    )
    user = (
        f"{context}\n\nFinder candidate connections (JSON):\n{json.dumps(candidates)}"
    )
    raw = call_chat(
        FINDER_CRITIC_DEPLOYMENT, CRITIC_SYSTEM_PROMPT, user, max_tokens=16384
    )
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


_SAME_TOPIC_RESTRICTION = (
    "RESTRICTION: emit ONLY aligns-with, differs-on, or conflicts-with findings. "
    "If this pair is one-sided (coverage asymmetry), emit an empty array — "
    "the coverage pass handles those."
)


def _finder_per_pair(
    anchor_index: AnchorIndex, pair: dict[str, Any], labels: str = "all"
) -> list[dict]:
    """Arms C/D/E/F/G-same-topic: judge one candidate pair.

    Returns 0 or 1 finding candidates using FINDER_SYSTEM_PROMPT.

    Args:
        anchor_index: the anchor index for resolving anchor ids.
        pair: a candidate pair dict with source_anchor_id / target_anchor_id.
        labels: when ``"same-topic"``, prepends a restriction to the user
            message so the model emits ONLY aligns-with / differs-on /
            conflicts-with and skips one-sided coverage pairs (those are
            handled by the coverage whole-doc pass in Arm G). When ``"all"``
            (the default), behaviour is identical to before this parameter
            was added — no restriction, all five labels permitted.
    """
    a_anchor = anchor_index.get(pair["source_anchor_id"])
    b_anchor = anchor_index.get(pair["target_anchor_id"])
    if a_anchor is None or b_anchor is None:
        return []
    base_user = (
        f"Document A ({a_anchor['document_id']}):\n"
        f"{_format_anchor_block(a_anchor)}\n\n"
        f"Document B ({b_anchor['document_id']}):\n"
        f"{_format_anchor_block(b_anchor)}\n\n"
        f"These two anchors were retrieved as candidates because they may share the axis: "
        f"'{pair.get('matched_axis_source')}' ↔ '{pair.get('matched_axis_target')}'.\n"
        f"Judge whether they genuinely relate. If yes, emit one connection object. If no, emit an empty array."
    )
    if labels == "same-topic":
        user = _SAME_TOPIC_RESTRICTION + "\n\n" + base_user
    else:
        user = base_user
    raw = call_chat(
        FINDER_CRITIC_DEPLOYMENT, FINDER_SYSTEM_PROMPT, user, max_tokens=2048
    )
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


def _critic_per_pair(
    anchor_index: AnchorIndex, pair: dict[str, Any], finder_output: list[dict]
) -> list[dict]:
    if not finder_output:
        return []
    a_anchor = anchor_index.get(pair["source_anchor_id"])
    b_anchor = anchor_index.get(pair["target_anchor_id"])
    if a_anchor is None or b_anchor is None:
        return finder_output
    user = (
        f"Document A anchor: {_format_anchor_block(a_anchor)}\n\n"
        f"Document B anchor: {_format_anchor_block(b_anchor)}\n\n"
        f"Finder's candidate:\n{json.dumps(finder_output)}\n\n"
        f"Refute or refine this candidate; drop it if it does not hold; refine its scope_note if needed."
    )
    raw = call_chat(
        FINDER_CRITIC_DEPLOYMENT, CRITIC_SYSTEM_PROMPT, user, max_tokens=2048
    )
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


def _build_suppression(
    retrieval_candidates: list[dict],
    same_topic_findings: list[dict],
) -> dict:
    """Build the suppression set from retrieval candidates and surviving same-topic findings.

    A retrieval candidate "produced a finding" if its source_anchor_id appears in the
    source_clauses list of any surviving same-topic finding.  Only those candidates
    contribute to the suppression set.

    Returns:
        {
            "covered_pairs": sorted list of "source × target" strings,
            "covered_topics": sorted list of unique matched_axis_source +
                              matched_axis_target values from matched candidates,
        }
    """
    # Build set of source anchor ids that appear in any surviving finding's source_clauses
    covered_sources: set[str] = set()
    for finding in same_topic_findings:
        for clause in finding.get("source_clauses", []):
            covered_sources.add(clause)

    # Filter retrieval candidates to those whose source_anchor_id produced a finding
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


def _finder_coverage_whole_doc(
    anchor_index: AnchorIndex, doc_a: str, doc_b: str, suppression: dict
) -> list[dict]:
    """Coverage stage: send both docs' full anchor lists in one prompt.

    Uses COVERAGE_FINDER_SYSTEM_PROMPT (silent-on / goes-beyond only).
    Appends a suppression block listing topics already covered by the
    same-topic pass, so the model does not re-report them as coverage gaps.
    The suppression block is omitted entirely when covered_topics is empty.

    No critic call — the coverage stage intentionally excludes the critic.
    """
    user = (
        _format_doc_block(anchor_index, doc_a)
        + "\n\n"
        + _format_doc_block(anchor_index, doc_b)
    )
    covered_topics = suppression.get("covered_topics", [])
    if covered_topics:
        user += (
            "\n\nTOPICS ALREADY COVERED ON BOTH SIDES"
            " — do NOT report these as coverage gaps:\n"
            + "\n".join(f"  - {t}" for t in covered_topics)
        )
    raw = call_chat(
        FINDER_CRITIC_DEPLOYMENT, COVERAGE_FINDER_SYSTEM_PROMPT, user, max_tokens=16384
    )
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


# ---------------------------------------------------------------------------
# Suppression builder + coverage whole-doc finder (Arm G stages 3 & 4)
# ---------------------------------------------------------------------------


def _build_suppression(
    retrieval_candidates: list[dict], same_topic_findings: list[dict]
) -> dict:
    """Build the suppression dict from same-topic stage outputs.

    Args:
        retrieval_candidates: pair dicts from retrieve_cosine_only /
            retrieve_bm25_only.  Each has at least
            ``source_anchor_id``, ``target_anchor_id``,
            ``matched_axis_source``, and ``matched_axis_target``.
        same_topic_findings: raw finder output (post-critic).  Each
            dict has ``source_clauses: [str, ...]`` and
            ``target_clauses: [str, ...]`` where the strings are
            anchor IDs.

    Returns:
        {
            "covered_pairs":  sorted list of "A × B" strings,
            "covered_topics": sorted list of unique axis strings,
        }
    """
    # Step 1 — collect the A-side anchor IDs that produced a surviving finding.
    active_source_ids: set[str] = set()
    for finding in same_topic_findings:
        source_clauses = finding.get("source_clauses", [])
        if source_clauses:
            active_source_ids.add(source_clauses[0])

    # Step 2 — walk retrieval candidates; only those whose source produced a
    # finding contribute to the suppression set.
    covered_pairs: set[tuple[str, str]] = set()
    covered_topics: set[str] = set()
    for candidate in retrieval_candidates:
        src = candidate["source_anchor_id"]
        if src not in active_source_ids:
            continue
        tgt = candidate["target_anchor_id"]
        covered_pairs.add((src, tgt))
        covered_topics.add(candidate["matched_axis_source"])
        covered_topics.add(candidate["matched_axis_target"])

    return {
        "covered_pairs": sorted(f"{a} × {b}" for a, b in covered_pairs),
        "covered_topics": sorted(covered_topics),
    }


def _finder_coverage_whole_doc(
    anchor_index: AnchorIndex,
    doc_a: str,
    doc_b: str,
    suppression: dict,
) -> list[dict]:
    """Arm G Stage 4: whole-document coverage finder.

    Sends both documents' full anchor lists in one prompt together with
    the suppression block (if non-empty), using COVERAGE_FINDER_SYSTEM_PROMPT
    so the model emits ONLY ``silent-on`` / ``goes-beyond`` findings.

    No critic call — returns the raw parsed list from the LLM.

    Args:
        anchor_index: provides all anchors for both documents.
        doc_a: document-A identifier (the "our side").
        doc_b: document-B identifier (the "their side").
        suppression: output of ``_build_suppression``; its
            ``covered_topics`` list is appended to the user message
            when non-empty so the model skips already-covered topics.

    Returns:
        A list of raw finding dicts (label restricted to
        ``silent-on`` / ``goes-beyond`` by the system prompt).

    Raises:
        LLMResponseError: if the LLM response cannot be parsed as a
            JSON list.
    """
    user = (
        _format_doc_block(anchor_index, doc_a)
        + "\n\n"
        + _format_doc_block(anchor_index, doc_b)
    )
    if suppression.get("covered_topics"):
        topics_block = "\n".join(f"  - {t}" for t in suppression["covered_topics"])
        user += (
            f"\n\nTOPICS ALREADY COVERED ON BOTH SIDES — do NOT report these as coverage gaps:\n"
            f"{topics_block}"
        )
    raw = call_chat(
        FINDER_CRITIC_DEPLOYMENT, COVERAGE_FINDER_SYSTEM_PROMPT, user, max_tokens=16384
    )
    parsed = parse_json_response(raw)
    if not isinstance(parsed, list):
        raise LLMResponseError(f"expected list, got {type(parsed).__name__}")
    return parsed


# ---------------------------------------------------------------------------
# Arm runners
# ---------------------------------------------------------------------------


def run_arm_b(anchor_index: AnchorIndex, doc_a: str, doc_b: str) -> dict[str, Any]:
    """Whole-doc pairwise: 2 LLM calls per pair."""
    start = time.time()
    finder_output = _finder_whole_doc(anchor_index, doc_a, doc_b)
    critic_output = _critic_whole_doc(anchor_index, doc_a, doc_b, finder_output)
    clause_shim = _AnchorAsClauseIndex(anchor_index)
    supported, unsupported, validation = _validate_candidates(
        critic_output, clause_shim
    )
    return {
        "arm": "B",
        "wall_clock_seconds": round(time.time() - start, 1),
        "finder_output": finder_output,
        "critic_output": critic_output,
        "supported": supported,
        "unsupported": unsupported,
        "validation": validation,
        "retrieval_candidates": None,
    }


def run_arm_c(anchor_index: AnchorIndex, doc_a: str, doc_b: str) -> dict[str, Any]:
    """Cosine-only retrieval + per-pair finder+critic."""
    start = time.time()
    axes_a = _load_axes(doc_a)
    axes_b = _load_axes(doc_b)
    candidates = retrieve_cosine_only(axes_a, axes_b)
    logger.info("Arm C: retrieved %d candidate pairs", len(candidates))

    all_finder_raw: list[dict] = []
    all_critic_raw: list[dict] = []
    for i, pair in enumerate(candidates, start=1):
        logger.info(
            "[%d/%d] Arm C finder+critic on %s × %s (cos=%.2f)",
            i,
            len(candidates),
            pair["source_anchor_id"],
            pair["target_anchor_id"],
            pair["similarity"],
        )
        try:
            f_out = _finder_per_pair(anchor_index, pair)
            all_finder_raw.extend(f_out)
            c_out = _critic_per_pair(anchor_index, pair, f_out)
            all_critic_raw.extend(c_out)
        except LLMResponseError as exc:
            logger.warning(
                "skipping pair (%s, %s): %s",
                pair["source_anchor_id"],
                pair["target_anchor_id"],
                exc,
            )

    clause_shim = _AnchorAsClauseIndex(anchor_index)
    supported, unsupported, validation = _validate_candidates(
        all_critic_raw, clause_shim
    )
    return {
        "arm": "C",
        "wall_clock_seconds": round(time.time() - start, 1),
        "finder_output": all_finder_raw,
        "critic_output": all_critic_raw,
        "supported": supported,
        "unsupported": unsupported,
        "validation": validation,
        "retrieval_candidates": candidates,
    }


def run_arm_d(anchor_index: AnchorIndex, doc_a: str, doc_b: str) -> dict[str, Any]:
    """Hybrid BM25+cosine+glossary retrieval + per-pair finder+critic."""
    start = time.time()
    axes_a = _load_axes(doc_a)
    axes_b = _load_axes(doc_b)
    glossary = _load_glossary()
    candidates = retrieve_hybrid(axes_a, axes_b, glossary)
    logger.info("Arm D: retrieved %d candidate pairs", len(candidates))

    all_finder_raw: list[dict] = []
    all_critic_raw: list[dict] = []
    for i, pair in enumerate(candidates, start=1):
        logger.info(
            "[%d/%d] Arm D finder+critic on %s × %s (fusion=%.4f%s)",
            i,
            len(candidates),
            pair["source_anchor_id"],
            pair["target_anchor_id"],
            pair.get("fusion_score", 0),
            " +glossary" if pair.get("glossary_expansion") else "",
        )
        try:
            f_out = _finder_per_pair(anchor_index, pair)
            all_finder_raw.extend(f_out)
            c_out = _critic_per_pair(anchor_index, pair, f_out)
            all_critic_raw.extend(c_out)
        except LLMResponseError as exc:
            logger.warning("skipping pair: %s", exc)

    clause_shim = _AnchorAsClauseIndex(anchor_index)
    supported, unsupported, validation = _validate_candidates(
        all_critic_raw, clause_shim
    )
    return {
        "arm": "D",
        "wall_clock_seconds": round(time.time() - start, 1),
        "finder_output": all_finder_raw,
        "critic_output": all_critic_raw,
        "supported": supported,
        "unsupported": unsupported,
        "validation": validation,
        "retrieval_candidates": candidates,
    }


def run_arm_e(anchor_index: AnchorIndex, doc_a: str, doc_b: str) -> dict[str, Any]:
    """BM25-only retrieval + per-pair finder+critic. No embeddings, no glossary."""
    start = time.time()
    axes_a = _load_axes(doc_a)
    axes_b = _load_axes(doc_b)
    candidates = retrieve_bm25_only(axes_a, axes_b)
    logger.info("Arm E: retrieved %d candidate pairs", len(candidates))

    all_finder_raw: list[dict] = []
    all_critic_raw: list[dict] = []
    for i, pair in enumerate(candidates, start=1):
        logger.info(
            "[%d/%d] Arm E finder+critic on %s × %s (bm25=%.2f)",
            i,
            len(candidates),
            pair["source_anchor_id"],
            pair["target_anchor_id"],
            pair["bm25_score"],
        )
        try:
            f_out = _finder_per_pair(anchor_index, pair)
            all_finder_raw.extend(f_out)
            c_out = _critic_per_pair(anchor_index, pair, f_out)
            all_critic_raw.extend(c_out)
        except LLMResponseError as exc:
            logger.warning(
                "skipping pair (%s, %s): %s",
                pair["source_anchor_id"],
                pair["target_anchor_id"],
                exc,
            )

    clause_shim = _AnchorAsClauseIndex(anchor_index)
    supported, unsupported, validation = _validate_candidates(
        all_critic_raw, clause_shim
    )
    return {
        "arm": "E",
        "wall_clock_seconds": round(time.time() - start, 1),
        "finder_output": all_finder_raw,
        "critic_output": all_critic_raw,
        "supported": supported,
        "unsupported": unsupported,
        "validation": validation,
        "retrieval_candidates": candidates,
    }


def run_arm_f(anchor_index: AnchorIndex, doc_a: str, doc_b: str) -> dict[str, Any]:
    """BM25 + glossary retrieval + per-pair finder+critic. No embeddings."""
    start = time.time()
    axes_a = _load_axes(doc_a)
    axes_b = _load_axes(doc_b)
    glossary = _load_glossary()
    candidates = retrieve_bm25_glossary(axes_a, axes_b, glossary)
    logger.info("Arm F: retrieved %d candidate pairs", len(candidates))

    all_finder_raw: list[dict] = []
    all_critic_raw: list[dict] = []
    for i, pair in enumerate(candidates, start=1):
        logger.info(
            "[%d/%d] Arm F finder+critic on %s × %s (bm25=%.2f%s)",
            i,
            len(candidates),
            pair["source_anchor_id"],
            pair["target_anchor_id"],
            pair["bm25_score"],
            " +glossary" if pair.get("glossary_expansion") else "",
        )
        try:
            f_out = _finder_per_pair(anchor_index, pair)
            all_finder_raw.extend(f_out)
            c_out = _critic_per_pair(anchor_index, pair, f_out)
            all_critic_raw.extend(c_out)
        except LLMResponseError as exc:
            logger.warning(
                "skipping pair (%s, %s): %s",
                pair["source_anchor_id"],
                pair["target_anchor_id"],
                exc,
            )

    clause_shim = _AnchorAsClauseIndex(anchor_index)
    supported, unsupported, validation = _validate_candidates(
        all_critic_raw, clause_shim
    )
    return {
        "arm": "F",
        "wall_clock_seconds": round(time.time() - start, 1),
        "finder_output": all_finder_raw,
        "critic_output": all_critic_raw,
        "supported": supported,
        "unsupported": unsupported,
        "validation": validation,
        "retrieval_candidates": candidates,
    }


def run_arm_g(
    anchor_index: AnchorIndex, doc_a: str, doc_b: str, signal: str = "cosine"
) -> dict[str, Any]:
    """Arm G: composite coverage-aware flow.

    Stage 1: same-topic retrieval (cosine or BM25).
    Stage 2: per-pair finder restricted to aligns-with/differs-on/conflicts-with (no critic).
    Stage 3: build suppression list from Stage 2 survivors.
    Stage 4: whole-doc coverage finder (silent-on/goes-beyond only, no critic).
    Stage 5: merge + validate via _validate_candidates.
    """
    start = time.time()

    # Stage 1 — retrieval
    axes_a = _load_axes(doc_a)
    axes_b = _load_axes(doc_b)
    if signal == "bm25":
        candidates = retrieve_bm25_only(axes_a, axes_b)
    else:
        candidates = retrieve_cosine_only(axes_a, axes_b)
    logger.info("Arm G: %d retrieval candidates (signal=%s)", len(candidates), signal)

    # Stage 2 — same-topic finder only (no critic)
    all_same_topic_raw: list[dict] = []
    for i, pair in enumerate(candidates, start=1):
        logger.info(
            "[%d/%d] Arm G same-topic finder on %s × %s",
            i,
            len(candidates),
            pair["source_anchor_id"],
            pair["target_anchor_id"],
        )
        try:
            f_out = _finder_per_pair(anchor_index, pair, labels="same-topic")
            all_same_topic_raw.extend(f_out)
        except LLMResponseError as exc:
            logger.warning(
                "skipping pair (%s, %s): %s",
                pair["source_anchor_id"],
                pair["target_anchor_id"],
                exc,
            )

    # Stage 3 — suppression list
    suppression = _build_suppression(candidates, all_same_topic_raw)
    logger.info(
        "Arm G: suppression — %d topics, %d pairs",
        len(suppression["covered_topics"]),
        len(suppression["covered_pairs"]),
    )

    # Stage 4 — coverage whole-doc finder (no critic)
    logger.info("Arm G: running coverage whole-doc pass on %s × %s", doc_a, doc_b)
    try:
        coverage_raw = _finder_coverage_whole_doc(
            anchor_index, doc_a, doc_b, suppression
        )
    except LLMResponseError as exc:
        logger.warning("coverage whole-doc finder failed: %s", exc)
        coverage_raw = []

    # Stage 5 — merge + validate
    merged = all_same_topic_raw + coverage_raw
    clause_shim = _AnchorAsClauseIndex(anchor_index)
    supported, unsupported, validation = _validate_candidates(merged, clause_shim)

    return {
        "arm": "G",
        "wall_clock_seconds": round(time.time() - start, 1),
        "finder_output": all_same_topic_raw,
        "critic_output": [],  # no critic; kept for shape consistency with other arms
        "supported": supported,
        "unsupported": unsupported,
        "validation": validation,
        "retrieval_candidates": candidates,
        "suppression": suppression,
        "coverage_finder_output": coverage_raw,
    }


ARM_RUNNERS = {
    "B": run_arm_b,
    "C": run_arm_c,
    "D": run_arm_d,
    "E": run_arm_e,
    "F": run_arm_f,
    "G": run_arm_g,
}


# ---------------------------------------------------------------------------
# Coverage quality helpers — used by run_one to annotate metadata.json
# ---------------------------------------------------------------------------


def _is_single_sided(finding: dict) -> bool:
    """Return True if the finding has exactly one non-empty clause side.

    - goes-beyond: source_clauses non-empty AND target_clauses empty.
    - silent-on: source_clauses empty AND target_clauses non-empty.
    - Anything else: False.
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
    """Return True if this coverage finding overlaps with the suppression set.

    True when:
    - Any covered_topic (case-insensitive) appears as a substring in the
      finding's summary, OR
    - Any cited anchor (source or target) appears in the covered_pairs string.
    """
    covered_topics = [t.lower() for t in suppression.get("covered_topics", [])]
    summary_lower = (finding.get("summary") or "").lower()
    if any(t in summary_lower for t in covered_topics if t):
        return True
    # Also check if any cited anchor appears in covered_pairs
    covered_pairs_str = " ".join(suppression.get("covered_pairs", []))
    all_clauses = (finding.get("source_clauses") or []) + (
        finding.get("target_clauses") or []
    )
    return any(clause in covered_pairs_str for clause in all_clauses if clause)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def run_one(
    arm: str, pair: str, anchor_index: AnchorIndex, signal: str = "cosine"
) -> None:
    if pair not in PAIRS:
        raise SystemExit(f"unknown pair {pair!r}; known: {list(PAIRS)}")
    if arm not in ARM_RUNNERS:
        raise SystemExit(f"unknown arm {arm!r}; known: {list(ARM_RUNNERS)}")
    doc_a, doc_b = PAIRS[pair]
    logger.info("=== Arm %s on %s (%s × %s) ===", arm, pair, doc_a, doc_b)
    result = (
        ARM_RUNNERS[arm](anchor_index, doc_a, doc_b, signal)
        if arm == "G"
        else ARM_RUNNERS[arm](anchor_index, doc_a, doc_b)
    )

    out_dir = RESULTS_DIR / arm / pair
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "findings.json").write_text(
        json.dumps(
            {"connections": result["supported"], "unsupported": result["unsupported"]},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out_dir / "trace.json").write_text(
        json.dumps(
            {
                "arm": arm,
                "pair": pair,
                "doc_a": doc_a,
                "doc_b": doc_b,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": FINDER_CRITIC_DEPLOYMENT,
                "wall_clock_seconds": result["wall_clock_seconds"],
                "finder_output": result["finder_output"],
                "critic_output": result["critic_output"],
                "validation": result["validation"],
                "retrieval_candidates": result["retrieval_candidates"],
                "suppression": result.get("suppression"),
                "coverage_finder_output": result.get("coverage_finder_output"),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (out_dir / "metadata.json").write_text(
        json.dumps(
            {
                "arm": arm,
                "pair": pair,
                "supported_count": len(result["supported"]),
                "unsupported_count": len(result["unsupported"]),
                "wall_clock_seconds": result["wall_clock_seconds"],
                "retrieval_candidate_count": (
                    len(result["retrieval_candidates"])
                    if result["retrieval_candidates"] is not None
                    else None
                ),
                "same_topic_finding_count": (
                    len(result.get("finder_output") or [])
                    if "coverage_finder_output" in result
                    else 0
                ),
                "coverage_finding_count": len(
                    result.get("coverage_finder_output") or []
                ),
                "coverage_quality_notes": [
                    {
                        "summary": f.get("summary", ""),
                        "label": f.get("label"),
                        "single_sided": _is_single_sided(f),
                        "redundant": _is_redundant(f, result.get("suppression") or {}),
                    }
                    for f in (result.get("coverage_finder_output") or [])
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info(
        "Arm %s / %s → %d supported / %d unsupported in %.1fs → %s",
        arm,
        pair,
        len(result["supported"]),
        len(result["unsupported"]),
        result["wall_clock_seconds"],
        out_dir,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", required=True, help="B, C, D, E, F, G, or all")
    parser.add_argument("--pair", required=True, help="bis-ed, hkma-ed, or all")
    parser.add_argument(
        "--signal",
        choices=["cosine", "bm25"],
        default="cosine",
        help="retrieval signal for Arm G (default: cosine)",
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

    arms = list(ARM_RUNNERS) if args.arm == "all" else [args.arm]
    pairs = list(PAIRS) if args.pair == "all" else [args.pair]

    for arm in arms:
        for pair in pairs:
            try:
                run_one(arm, pair, anchor_index, signal=args.signal)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Arm %s / %s failed: %s", arm, pair, exc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
