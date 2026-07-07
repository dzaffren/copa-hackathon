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
