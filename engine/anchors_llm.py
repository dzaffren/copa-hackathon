"""LLM-boundary segmenter — the non-BNM lane.

The model emits ONLY boundaries + labels ({anchor_label, starts_with, parent});
deterministic code locates each starts_with in the source, slices the verbatim
text between consecutive anchors, and verify_substring gates it. The model never
produces citation text. Reuses engine.clauses._find_anchor_positions (which
matches whitespace-insensitively but slices from the raw source, so text stays
byte-for-byte verbatim).

The model call is behind the injectable boundary_fn seam; tests inject a stub so
no network/credentials are needed (mirrors engine.connections finder_fn).
"""
from __future__ import annotations

from typing import Callable, Optional

from engine.anchors import Anchor, verify_substring
from engine.clauses import _find_anchor_positions
from engine.config import FINDER_CRITIC_DEPLOYMENT
from engine.llm import call_chat, parse_json_response

# (document_id, source_markdown, doc_class) -> [{anchor_label, starts_with, parent}]
BoundaryFn = Callable[[str, str, str], list[dict]]

BOUNDARY_SYSTEM_PROMPT = (
    "You segment a legal/regulatory document into its structural units. "
    "Return a JSON array; each element is "
    '{"anchor_label": <the unit locator EXACTLY as printed, e.g. "Article 12(3)" '
    'or "Principle 4">, "starts_with": <the first few words of the unit\'s BODY '
    "text, copied verbatim, NO label prefix>, \"parent\": <the parent locator or "
    "null>}. "
    "Copy anchor_label verbatim from the heading — never invent or renumber. "
    "starts_with must be a verbatim quote of the body so it can be located in the "
    "source. Do not include preamble, page numbers, or dates as units."
)


def _default_boundary_fn(
    document_id: str, source_markdown: str, doc_class: str
) -> list[dict]:
    user = (
        f"doc_class: {doc_class}\ndocument_id: {document_id}\n\n"
        f"Document markdown:\n{source_markdown}"
    )
    raw = call_chat(FINDER_CRITIC_DEPLOYMENT, BOUNDARY_SYSTEM_PROMPT, user,
                    max_tokens=16384)
    data = parse_json_response(raw)
    if not isinstance(data, list):
        raise ValueError("boundary model did not return a JSON array")
    return data


def _drop(report: Optional[list[dict]], document_id: str, unit: dict,
          reason: str) -> None:
    if report is None:
        return
    report.append({
        "document_id": document_id,
        "anchor_label": unit.get("anchor_label"),
        "reason": reason,
        "starts_with": unit.get("starts_with"),
    })


def llm_boundary_segment(
    document_id: str,
    source_markdown: str,
    *,
    doc_class: str,
    shortname: str,
    boundary_fn: Optional[BoundaryFn] = None,
    dropped_report: Optional[list[dict]] = None,
) -> list[Anchor]:
    """Segment via model-emitted boundaries + deterministic verbatim slicing.

    anchor_id is "{shortname} {anchor_label}" (e.g. "EU AI Act Article 12(3)").
    A unit whose starts_with is empty, not found, or ambiguous is dropped (into
    dropped_report if supplied), never emitted. Every returned anchor is
    re-checked with verify_substring.
    """
    fn = boundary_fn if boundary_fn is not None else _default_boundary_fn
    units = fn(document_id, source_markdown, doc_class)

    # Resolve each unit to a start offset first, so we can slice between anchors.
    resolved: list[tuple[dict, int]] = []
    for unit in units:
        snippet = (unit.get("starts_with") or "").strip()
        if not snippet:
            _drop(dropped_report, document_id, unit, "empty_starts_with")
            continue
        positions = _find_anchor_positions(source_markdown, snippet)
        if not positions:
            _drop(dropped_report, document_id, unit, "not_found")
            continue
        if len(positions) > 1:
            _drop(dropped_report, document_id, unit, "ambiguous")
            continue
        resolved.append((unit, positions[0]))

    resolved.sort(key=lambda pair: pair[1])
    anchors: list[Anchor] = []
    for i, (unit, start) in enumerate(resolved):
        end = resolved[i + 1][1] if i + 1 < len(resolved) else len(source_markdown)
        text = source_markdown[start:end].strip()
        if not text:
            _drop(dropped_report, document_id, unit, "empty_text")
            continue
        label = unit["anchor_label"]
        parent = unit.get("parent")
        anchor: Anchor = {
            "anchor_id": f"{shortname} {label}",
            "anchor_label": label,
            "text": text,
            "doc_class": doc_class,
            "document_id": document_id,
            "heading_path": [],
            "page_span": None,
            "parent_anchor": f"{shortname} {parent}" if parent else None,
        }
        verify_substring(anchor, source_markdown)  # defensive re-check
        anchors.append(anchor)
    return anchors
