"""Shared connection render / verbatim-quote-join model (spec Task 6).

Design (see docs/specs/reconciliation-workbench/spec-source-connection-engine.md,
"API Design"): the read API (`engine.api`) and the static snapshot exporter
(`scripts.export_poc_snapshot`) must render a `verdicts.json` record into the
SAME connection object, join the SAME verbatim quote text, and drop the SAME
restricted nodes — byte-for-byte. This module is that single implementation, so
the two consumers can never diverge. It was lifted out of the exporter's private
helpers (`_public_nodes` / `_quote_for` / `_connection_from_verdict`); the
exporter now delegates here.

It joins three inputs, exactly as the exporter did:

  * verdicts.json  — per-connection records (verdict, rationale, confidence,
                     branch, verification, source ref, blocked-source status) —
                     the spine of a connection.
  * clause index   — the ONLY source of verbatim quote text and paragraph text
                     (fetched by clause number; never model-authored).
  * graph nodes    — source metadata (title, source_type, access). A node marked
                     `access == "restricted"` is dropped entirely: neither its
                     text nor its title reaches a rendered payload.

Everything here is pure and deterministic — no network, no model. The verbatim
guarantee holds by construction: quote text always comes back through the clause
index by number, and a `pending_extraction` / absent clause yields `text: null`,
never an approximated string.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional, cast

from engine.clauses import ClauseIndex


def public_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index graph nodes by id, DROPPING any with `access == "restricted"`.

    The confidentiality guarantee: a restricted node (e.g. the internal
    handbook) is excluded here, so neither its title nor any derived text can
    appear in a rendered payload. Preview nodes are kept (they are public) but
    carry no verbatim passage, so they simply never gain a quote. (== the
    exporter's former `_public_nodes`.)
    """
    return {
        node["id"]: node
        for node in graph.get("nodes", [])
        if node.get("access") != "restricted"
    }


def quote_for(
    clause_number: Optional[str],
    verification: str,
    clause_index: ClauseIndex,
) -> Optional[dict[str, Any]]:
    """Build a quote block, fetching verbatim text from the clause index by number.

    Never returns model-authored text. `pending_extraction` yields `text: null`
    (a labelled placeholder downstream); a clause number absent from the index
    also yields `text: null` rather than an invented string. (== the exporter's
    former `_quote_for`.)
    """
    if clause_number is None:
        return None
    if verification == "pending_extraction":
        return {
            "clause_number": clause_number,
            "text": None,
            "verification": "pending_extraction",
        }
    entry = clause_index.get(clause_number)
    text = entry.get("text") if isinstance(entry, dict) else None
    return {"clause_number": clause_number, "text": text, "verification": verification}


def render_connection(
    record: Mapping[str, Any],
    nodes: dict[str, dict[str, Any]],
    clause_index: ClauseIndex,
) -> Optional[dict[str, Any]]:
    """Turn one verdicts.json record into a read-API connection object.

    Returns `None` when the record's source node is restricted/absent (dropped
    from `nodes`), so restricted connections never surface. A blocked
    (`could_not_retrieve`) source renders with `verdict: null` and `quote: null`
    — never a fabricated verdict or quote. (== the exporter's former
    `_connection_from_verdict`.)
    """
    source_id = record.get("source_document_id")
    node = nodes.get(source_id) if source_id is not None else None
    if node is None:
        return None  # restricted (dropped from `nodes`), missing, or unknown → omit

    source: dict[str, Any] = {
        "document_id": source_id,
        "title": node.get("title", source_id),
        "source_type": node.get("source_type", "international_standard"),
    }
    if "stance" in record:
        source["stance"] = record["stance"]

    base = {
        "id": record["id"],
        "branch": record.get("branch", "uncited"),
        "source": source,
    }

    # A blocked (un-retrieved) source: no verdict, no quote.
    if record.get("status") == "could_not_retrieve":
        return {
            **base,
            "status": "could_not_retrieve",
            "reason": record.get(
                "reason", "This source could not be retrieved automatically."
            ),
            "verdict": None,
            "quote": None,
        }

    return {
        **base,
        "verdict": record["verdict"],
        "verdict_status": "proposed",
        "confidence": record.get("confidence", "Medium"),
        "rationale": record.get("rationale", ""),
        "quote": quote_for(
            record.get("clause_number"),
            record.get("verification", "illustrative"),
            clause_index,
        ),
    }


def _group_by_paragraph(
    verdicts: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Group verdict records by the paragraph number they touch."""
    by_paragraph: dict[str, list[dict[str, Any]]] = {}
    for record in verdicts.values():
        para = record.get("paragraph")
        if para is None:
            continue
        by_paragraph.setdefault(para, []).append(record)
    return by_paragraph


def _paragraph_number(clause_number: str) -> str:
    """The bare paragraph number for a clause key (e.g. `"AI-DP 3.5"` → `"3.5"`)."""
    return clause_number.split(" ", 1)[-1]


def _paragraph_sort_key(clause_number: str) -> list[tuple[int, Any]]:
    """Numeric-aware sort key for a paragraph number so the workspace canvas
    renders 3.2 before 3.11 and 5.9 before 5.10 (a plain string sort misorders
    these). Each dotted component sorts numerically when it is all digits, and
    lexically otherwise, with numeric parts ordered before non-numeric ones."""
    parts = _paragraph_number(clause_number).split(".")
    return [(0, int(p)) if p.isdigit() else (1, p) for p in parts]


def paragraph_entry(
    clause_index: ClauseIndex, document_id: str, paragraph_number: str
) -> Optional[dict[str, Any]]:
    """Find the vehicle document's clause-index entry for one paragraph number.

    A paragraph of the vehicle document is a clause-index entry whose
    `document_id` matches and whose bare number (`clause_number.split(" ", 1)[-1]`)
    equals `paragraph_number`. Returns `None` if no such paragraph exists — the
    signal the API turns into `404 PARAGRAPH_NOT_FOUND`.
    """
    for entry in clause_index.entries_for_document(document_id):
        if _paragraph_number(entry["clause_number"]) == paragraph_number:
            return cast(dict[str, Any], entry)
    return None


def render_paragraph_connections(
    document_id: str,
    paragraph_number: str,
    verdicts: dict[str, Any],
    graph: dict[str, Any],
    clause_index: ClauseIndex,
) -> Optional[dict[str, Any]]:
    """Build the full `GET …/{number}/connections` payload for one paragraph.

    Shape: `{paragraph: {number, title, text}, state, no_matching_source,
    connections: [...]}`. `title`/`text` come from the paragraph's clause-index
    entry (verbatim); `state` is `"analysed"` when the paragraph has any verdict
    record, else `"not_analysed"`; `no_matching_source` is true only for an
    analysed paragraph whose rendered connection set is empty (distinct from
    `not_analysed`). Returns `None` when the paragraph clause is not found.
    """
    entry = paragraph_entry(clause_index, document_id, paragraph_number)
    if entry is None:
        return None

    nodes = public_nodes(graph)
    by_paragraph = _group_by_paragraph(verdicts)
    records = by_paragraph.get(paragraph_number, [])
    connections = [
        connection
        for connection in (
            render_connection(record, nodes, clause_index) for record in records
        )
        if connection is not None
    ]
    state = "analysed" if paragraph_number in by_paragraph else "not_analysed"

    return {
        "paragraph": {
            "number": paragraph_number,
            "title": entry.get("heading") or "",
            "text": entry.get("text", ""),
        },
        "state": state,
        "no_matching_source": state == "analysed" and len(connections) == 0,
        "connections": connections,
    }


def render_paragraphs_index(
    document_id: str,
    clause_index: ClauseIndex,
    verdicts: dict[str, Any],
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Build the `GET …/paragraphs` payload — the document's paragraphs + state.

    Shape: `{document_id, total_paragraphs, paragraphs: [{number, title, text,
    state, connection_count}]}`. Paragraphs are the clause-index entries for
    `document_id`, sorted by clause number; `state` is `"analysed"` when the
    paragraph number has any verdict record; `connection_count` is the RENDERED
    (non-dropped, restricted-excluded) connection count — so it needs `graph`
    (the exporter's `_public_nodes` drop must be reflected in the count the
    workspace badges render).
    """
    nodes = public_nodes(graph)
    by_paragraph = _group_by_paragraph(verdicts)

    entries = sorted(
        clause_index.entries_for_document(document_id),
        key=lambda entry: _paragraph_sort_key(entry["clause_number"]),
    )
    paragraphs: list[dict[str, Any]] = []
    for entry in entries:
        number = _paragraph_number(entry["clause_number"])
        records = by_paragraph.get(number, [])
        connections = [
            connection
            for connection in (
                render_connection(record, nodes, clause_index) for record in records
            )
            if connection is not None
        ]
        paragraphs.append(
            {
                "number": number,
                "title": entry.get("heading") or "",
                "text": entry.get("text", ""),
                "state": "analysed" if number in by_paragraph else "not_analysed",
                "connection_count": len(connections),
            }
        )

    return {
        "document_id": document_id,
        "total_paragraphs": len(paragraphs),
        "paragraphs": paragraphs,
    }
