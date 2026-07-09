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


class _FakeResult:
    def __init__(self, text: str) -> None:
        self.text_content = text


class _FakeConverter:
    def __init__(self, text: str) -> None:
        self._text = text
        self.converted: list[str] = []

    def convert(self, path: str) -> _FakeResult:
        self.converted.append(path)
        return _FakeResult(self._text)


def test_ingest_uses_injected_converter_no_network():
    """An explicit converter overrides the built-in one — tests need no
    Azure/MarkItDown network path."""
    fake = _FakeConverter("clean clause text")

    text = ingest_document("/some/doc.pdf", converter=fake)

    assert text == "clean clause text"
    assert fake.converted == ["/some/doc.pdf"]


def test_build_converter_uses_document_intelligence_when_configured(monkeypatch):
    """When the DI endpoint + key are set, the converter is built with the
    docintel backend; unset → plain MarkItDown. No network: we capture the
    kwargs MarkItDown is constructed with."""
    import engine.ingest as ingest

    captured: dict = {}

    class _SpyMarkItDown:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(ingest, "MarkItDown", _SpyMarkItDown)

    # Configured → docintel_endpoint passed through.
    ingest._build_converter("https://di.example/", "secret-key")
    assert captured.get("docintel_endpoint") == "https://di.example/"
    assert "docintel_credential" in captured

    # Unset → plain MarkItDown, no docintel kwargs.
    captured.clear()
    ingest._build_converter(None, None)
    assert "docintel_endpoint" not in captured


def test_ingest_raises_unreadable_document_error_on_corrupt_input(tmp_path):
    """A corrupt/unreadable file (random bytes with a .pdf extension) must
    raise UnreadableDocumentError rather than return garbled or empty text.
    This is the fixture Test 11 (submission rejection) relies on."""
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"\x00\x01\x02not a real pdf\xff\xfe")

    with pytest.raises(UnreadableDocumentError):
        ingest_document(corrupt_pdf)
