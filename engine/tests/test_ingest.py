"""Tests for engine.ingest — MarkItDown PDF/DOCX -> clean markdown conversion.

Covers Acceptance Criteria:
  1. Clean ingestion of a corpus PDF returns non-empty, readable markdown.
  2. Garbled-source document (real RMiT PDF) ingests cleanly (Test 3 fixture).
  3. UnreadableDocumentError on empty conversion (Test 11 fixture).
"""

import re
from pathlib import Path

import pytest

from engine.ingest import UnreadableDocumentError, ingest_document

CORPUS_DIR = Path(__file__).resolve().parents[2] / "data" / "corpus"
OUTSOURCING_PDF = CORPUS_DIR / "PD_Outsourcing_20191023.pdf"
RMIT_PDF = CORPUS_DIR / "pd-rmit-nov25.pdf"


def test_ingest_returns_non_empty_readable_markdown():
    text = ingest_document(OUTSOURCING_PDF)

    assert isinstance(text, str)
    assert text.strip() != ""


def test_ingest_rmit_pdf_produces_clean_readable_text_not_garbled():
    """RMiT's custom font encoding produces gibberish under naive extraction
    (validated in the discovery brief's dry-run). MarkItDown must still
    produce clean, readable ASCII text with clause numbers intact."""
    text = ingest_document(RMIT_PDF)

    # No replacement characters from botched decoding.
    assert "�" not in text

    # Readable-ASCII heuristic: letters should dominate non-whitespace chars.
    non_whitespace = re.sub(r"\s", "", text)
    letters = re.findall(r"[A-Za-z]", text)
    letter_ratio = len(letters) / len(non_whitespace)
    assert letter_ratio > 0.5

    # Clause numbers survive conversion.
    assert "17.1" in text
    assert "17.2" in text


def test_ingest_raises_unreadable_document_error_on_corrupt_input(tmp_path):
    """A corrupt/unreadable file (random bytes with a .pdf extension) must
    raise UnreadableDocumentError rather than return garbled or empty text.
    This is the fixture Test 11 (submission rejection) relies on."""
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"\x00\x01\x02not a real pdf\xff\xfe")

    with pytest.raises(UnreadableDocumentError):
        ingest_document(corrupt_pdf)
