"""Tests for engine.verdicts — the stage-4b verdict pass.

No network: `verdict_fn` is stubbed (or the connection carries a frozen verdict),
and the `ClauseIndex` is hand-built from `build_reference_clause` — the same
no-network discipline as engine/tests/test_connections.py.
"""

import pytest

from engine.clauses import ClauseIndex, build_reference_clause
from engine.verdicts import (
    VerdictError,
    compute_confidence_band,
    propose_verdicts,
)

PDPA_TEXT = (
    "A data controller may transfer any personal data of a data subject to any "
    "place outside Malaysia if— (a) there is in that place in force any law "
    "which is substantially similar to this Act."
)
FSP_TEXT = (
    "The requirement to obtain informed consent is unworkable for models already "
    "trained on legacy datasets collected before AI use was contemplated."
)


def _index() -> ClauseIndex:
    """A ClauseIndex holding the source clauses the verdict tests cite verbatim
    (PDPA 129 + Industry FSP-3) and, deliberately, NOT 'Cyber 4.4'."""
    primary = {}
    versions: dict = {}
    refs = {
        **build_reference_clause("pdpa-2010", "pdpa", "129", "Section 129(2)", PDPA_TEXT),
        **build_reference_clause(
            "industry-fsp-3", "industry-fsp-3", "FSP-3", "FSP feedback", FSP_TEXT
        ),
    }
    for clause_number, entry in refs.items():
        primary[clause_number] = entry
        versions.setdefault(clause_number, {})[entry["document_id"]] = entry
    return ClauseIndex(primary, versions)


def test_verdict_stage_proposes_conflict_quote_fetched_verbatim():
    """Test 1 — verdict Conflict for 4.6 ↔ PDPA §129; the quote is fetched from
    the index by number (verbatim), never from the model's rationale."""
    index = _index()
    connection = {
        "id": "ai-dp-2025:4.6::pdpa-2010:PDPA 129",
        "paragraph": "4.6",
        "branch": "uncited",
        "source_document_id": "pdpa-2010",
        "clause_number": "PDPA 129",
        "confidence_score": 0.90,
        "verification": "verified",
    }

    def stub_verdict_fn(conn, clause_index):
        return {"verdict": "Conflict", "rationale": "cross-border transfer test"}

    records = propose_verdicts([connection], index, verdict_fn=stub_verdict_fn)
    record = records["ai-dp-2025:4.6::pdpa-2010:PDPA 129"]

    assert record["verdict"] == "Conflict"
    assert record["verdict_status"] == "proposed"
    assert record["confidence"] == "High"
    assert record["rationale"] == "cross-border transfer test"
    # The verbatim quote comes back through the index by clause_number — NOT the
    # stub's rationale text.
    assert index.get(record["clause_number"])["text"] == PDPA_TEXT
    assert PDPA_TEXT != record["rationale"]


def test_verdict_stage_proposes_partial_for_feedback_illustrative():
    """Test 2 — Partial verdict for the 3-FSP feedback on 4.6, Medium band,
    illustrative marker, stance carried through."""
    index = _index()
    connection = {
        "id": "ai-dp-2025:4.6::industry-fsp-3",
        "paragraph": "4.6",
        "branch": "feedback",
        "source_document_id": "industry-fsp-3",
        "clause_number": "Industry FSP-3",
        "confidence_score": 0.78,
        "verification": "illustrative",
        "stance": "partial",
    }

    def stub_verdict_fn(conn, clause_index):
        return {
            "verdict": "Partial",
            "rationale": (
                "agrees on responsible handling, rejects consent for legacy data"
            ),
        }

    records = propose_verdicts([connection], index, verdict_fn=stub_verdict_fn)
    record = records["ai-dp-2025:4.6::industry-fsp-3"]

    assert record["verdict"] == "Partial"
    assert record["confidence"] == "Medium"
    assert record["verification"] == "illustrative"
    assert record["stance"] == "partial"


def test_gap_vs_deviates_ambiguity_caps_confidence_at_medium():
    """Test 3 — a Gap-vs-Deviates-ambiguous connection is capped at Medium even
    when its score alone would band High; the cap never raises a Low band."""
    assert compute_confidence_band(0.9) == "High"
    assert compute_confidence_band(0.9, gap_deviates_ambiguous=True) == "Medium"
    # A critic scope_note also lowers High → Medium.
    assert compute_confidence_band(0.9, scope_note="affiliate exemption") == "Medium"
    # Boundaries: >= 0.85 → High; 0.70–0.85 → Medium; < 0.70 → Low.
    assert compute_confidence_band(0.85) == "High"
    assert compute_confidence_band(0.84) == "Medium"
    assert compute_confidence_band(0.70) == "Medium"
    assert compute_confidence_band(0.69) == "Low"
    # Ambiguity does not rescue a Low band.
    assert compute_confidence_band(0.6, gap_deviates_ambiguous=True) == "Low"


def test_unsupported_connection_gets_no_verdict_record():
    """Test 4 — a candidate citing a clause absent from the index ('Cyber 4.4')
    gets NO verdict record: a verdict presupposes a resolved, verbatim citation."""
    index = _index()
    connection = {
        "id": "ai-dp-2025:3.5::cyber",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "cyber-x",
        "clause_number": "Cyber 4.4",
        "verdict": "Gap",
        "confidence_score": 0.9,
        "verification": "verified",
    }

    records = propose_verdicts([connection], index)

    assert "ai-dp-2025:3.5::cyber" not in records
    assert records == {}


def test_blocked_source_gets_could_not_retrieve_record_no_verdict():
    """A blocked (un-retrievable) source yields an honest could_not_retrieve
    record — no verdict, no clause — never a fabrication."""
    index = _index()
    connection = {
        "id": "ai-dp-2025:3.5::mas-feat",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "mas-feat",
        "status": "could_not_retrieve",
        "reason": "MAS site blocks automated access.",
    }

    records = propose_verdicts([connection], index)
    record = records["ai-dp-2025:3.5::mas-feat"]

    assert record["status"] == "could_not_retrieve"
    assert record["verdict"] is None
    assert record["reason"] == "MAS site blocks automated access."
    assert record["clause_number"] is None


def test_pending_extraction_connection_kept_despite_unresolved_clause():
    """A real source whose passage is not yet extracted keeps its verdict record;
    the read layer renders its quote text as null (never an approximation)."""
    index = _index()  # has no "Basel RBC20"
    connection = {
        "id": "ai-dp-2025:4.6::basel",
        "paragraph": "4.6",
        "branch": "uncited",
        "source_document_id": "basel-osfi",
        "clause_number": "Basel RBC20",
        "verdict": "Consensus",
        "confidence_score": 0.86,
        "verification": "pending_extraction",
    }

    records = propose_verdicts([connection], index)
    record = records["ai-dp-2025:4.6::basel"]

    assert record["verdict"] == "Consensus"
    assert record["verification"] == "pending_extraction"
    assert record["clause_number"] == "Basel RBC20"


def test_invalid_verdict_value_raises():
    """A proposed verdict outside the five allowed values fails loudly."""
    index = _index()
    connection = {
        "id": "x",
        "paragraph": "4.6",
        "branch": "uncited",
        "source_document_id": "pdpa-2010",
        "clause_number": "PDPA 129",
        "verdict": "Nonsense",
        "confidence_score": 0.9,
    }

    with pytest.raises(VerdictError):
        propose_verdicts([connection], index)
