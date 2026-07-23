"""BNM structured-rules segmenter, adapted to the Anchor shape.

Wraps engine.clauses.segment_clauses (the deterministic regex parser, offline,
no model) so it emits Anchor records with doc_class="structured-rules". The
anchor_id is the canonical clause_number ("RMiT 10.1"), so BNM anchors keep the
exact keys today's clause_number-keyed traces and tests rely on — no regression.
"""
from __future__ import annotations

from typing import Optional

from engine.anchors import Anchor
from engine.clauses import segment_clauses


def structured_rules_segment(
    document_id: str,
    source_markdown: str,
    *,
    policy_id: str,
    source: str,
    dropped_report: Optional[list[dict]] = None,
) -> list[Anchor]:
    entries = segment_clauses(
        source_markdown, document_id, policy_id, source,
        dropped_report=dropped_report,
    )
    anchors: list[Anchor] = []
    for clause_number, entry in entries.items():
        # entry["parent"] is ALREADY the canonical clause_number form (e.g.
        # "RMiT 10.1"), not a bare number — segment_clauses/_assemble_entries
        # canonicalizes it internally (engine/clauses.py:452-454) before
        # storing it on the entry. This is asserted by the existing suite
        # (engine/tests/test_clauses.py: `child_a["parent"] == "RMiT 17.1"`,
        # `index.get("RMiT 1.1(a)")["parent"] == "RMiT 1.1"`). So parent_anchor
        # already matches the canonical anchor_id form a future consumer can
        # resolve via AnchorIndex.get(parent_anchor) — no re-canonicalization
        # needed here (re-canonicalizing would double the shortname prefix,
        # e.g. "RMiT RMiT 10.1").
        parent_anchor = entry.get("parent")
        anchors.append({
            "anchor_id": clause_number,
            "anchor_label": clause_number,
            "text": entry["text"],
            "doc_class": "structured-rules",
            "document_id": document_id,
            "heading_path": [entry["heading"]] if entry.get("heading") else [],
            "page_span": None,
            "parent_anchor": parent_anchor,
        })
    return anchors
