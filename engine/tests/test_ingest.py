"""Tests for engine.ingest — MarkItDown PDF/DOCX -> clean markdown conversion.

Covers Acceptance Criteria:
  1. Clean ingestion of a corpus PDF returns non-empty, readable markdown.
  2. Garbled-source document (real RMiT PDF) ingests cleanly (Test 3 fixture).
  3. UnreadableDocumentError on empty conversion (Test 11 fixture).
"""

import re
from pathlib import Path

import httpx
import pytest

import engine.ingest as ingest
from engine.ingest import (
    UnreadableDocumentError,
    ingest_document,
    ingest_from_url,
    normalise_glyph_artifacts,
)

CORPUS_DIR = Path(__file__).resolve().parents[2] / "data" / "corpus"
OUTSOURCING_PDF = CORPUS_DIR / "sample" / "PD_Outsourcing_20191023.pdf"
RMIT_PDF = CORPUS_DIR / "open-finance" / "pd-rmit-nov25.pdf"
AI_DP_PDF = CORPUS_DIR / "sample" / "dp_ai_financial_sector.pdf"


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


# --- Glyph-artifact normalisation (AI DP "AI"-glyph mis-reads) --------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        # short LaTeX math-mode wrappers around the mangled glyph
        ("$A l$ models could exacerbate biases", "AI models could exacerbate biases"),
        ("adoption of $\\mathrm { A l }$ in finance", "adoption of AI in finance"),
        ("risks of $\\mathrm { A l } .$", "risks of AI."),
        ("footnote $A l ^ { 2 } ,$ here", "footnote AI, here"),
        # bare mis-cased tokens
        ("A major challenge of Al revolves", "A major challenge of AI revolves"),
        ('GenAl "hallucinations" arise', 'GenAI "hallucinations" arise'),
        (
            "Al-driven decisions do not discriminate",
            "AI-driven decisions do not discriminate",
        ),
        ("leading Fls with the majority", "leading FIs with the majority"),
    ],
)
def test_normalise_fixes_patterned_ai_glyph_artifacts(raw, expected):
    assert normalise_glyph_artifacts(raw) == expected


@pytest.mark.parametrize(
    "safe",
    [
        "sample of $\\left( n = 1 0 2 \\right)$ firms",  # real survey figure
        "concern score of $1 0 0$",  # numeric datum
        "the word Also appears here",  # real word starting 'Al'
        "an Alert was raised",  # real word
        "additional guidance",  # 'al' mid-word untouched
    ],
)
def test_normalise_leaves_real_content_untouched(safe):
    assert normalise_glyph_artifacts(safe) == safe


def test_normalise_does_not_eat_long_or_unterminated_math_spans():
    """A long `$...$` run (or a dangling delimiter wrapping real prose) must be
    left byte-for-byte intact — the guard prevents swallowing real content."""
    long_span = (
        "$ Leading adopters refer to the top quintile of FSPs by reported AI projects $"
    )
    assert normalise_glyph_artifacts(long_span) == long_span


def test_normalise_is_idempotent():
    once = normalise_glyph_artifacts("$A l$ and Al and GenAl")
    twice = normalise_glyph_artifacts(once)
    assert once == "AI and AI and GenAI"
    assert twice == once


# --- URL download + ingest (ingest_from_url) --------------------------------
#
# All HTTP is mocked by monkeypatching `httpx.get` to return (or raise from)
# real `httpx.Response`/`httpx.HTTPError` objects, and the conversion is stubbed
# with `_FakeConverter` — so these tests touch neither the network nor MarkItDown.


def _stub_get(monkeypatch, response=None, exc=None):
    """Point `engine.ingest.httpx.get` at a fake, capturing the requested URL."""
    seen: dict[str, str] = {}

    def fake_get(url, **kwargs):
        seen["url"] = url
        if exc is not None:
            raise exc
        return response

    monkeypatch.setattr(ingest.httpx, "get", fake_get)
    return seen


def test_ingest_from_url_downloads_then_converts(monkeypatch):
    """A 200 response is written to a tempfile and handed to the converter,
    whose text is returned. The tempfile carries the URL's inferred suffix."""
    url = "https://example.test/policy/doc.pdf"
    response = httpx.Response(
        200, request=httpx.Request("GET", url), content=b"%PDF-fake-bytes"
    )
    seen = _stub_get(monkeypatch, response=response)
    fake = _FakeConverter("clean clause text")

    text = ingest_from_url(url, converter=fake)

    assert text == "clean clause text"
    assert seen["url"] == url
    # ingest_document was called with the downloaded tempfile, suffixed .pdf.
    assert len(fake.converted) == 1
    assert fake.converted[0].endswith(".pdf")


def test_ingest_from_url_infers_docx_suffix(monkeypatch):
    """A `.docx` URL lands on a `.docx` tempfile so MarkItDown dispatches to the
    DOCX reader rather than the default `.pdf`."""
    url = "https://example.test/guidance.docx"
    response = httpx.Response(
        200, request=httpx.Request("GET", url), content=b"PK\x03\x04fake-docx"
    )
    _stub_get(monkeypatch, response=response)
    fake = _FakeConverter("docx clause text")

    text = ingest_from_url(url, converter=fake)

    assert text == "docx clause text"
    assert fake.converted[0].endswith(".docx")


def test_ingest_from_url_defaults_to_pdf_suffix_when_url_has_no_extension(
    monkeypatch,
):
    """A URL with no file extension defaults to `.pdf`."""
    url = "https://example.test/download?id=42"
    response = httpx.Response(
        200, request=httpx.Request("GET", url), content=b"%PDF-fake"
    )
    _stub_get(monkeypatch, response=response)
    fake = _FakeConverter("text")

    ingest_from_url(url, converter=fake)

    assert fake.converted[0].endswith(".pdf")


def test_ingest_from_url_raises_on_non_200(monkeypatch):
    """A non-200 (here 404) surfaces as UnreadableDocumentError, not a raw
    httpx error — the API turns this into a 422 for the client."""
    url = "https://example.test/missing.pdf"
    response = httpx.Response(404, request=httpx.Request("GET", url))
    _stub_get(monkeypatch, response=response)

    with pytest.raises(UnreadableDocumentError):
        ingest_from_url(url, converter=_FakeConverter("unused"))


def test_ingest_from_url_raises_on_network_error(monkeypatch):
    """A transport-level failure (connection refused, DNS, timeout) is wrapped
    as UnreadableDocumentError too."""
    url = "https://unreachable.test/doc.pdf"
    _stub_get(monkeypatch, exc=httpx.ConnectError("connection refused"))

    with pytest.raises(UnreadableDocumentError):
        ingest_from_url(url, converter=_FakeConverter("unused"))


def test_ingest_from_url_propagates_empty_conversion_error(monkeypatch):
    """A successful download whose conversion yields no text still raises
    UnreadableDocumentError (propagated from ingest_document)."""
    url = "https://example.test/blank.pdf"
    response = httpx.Response(
        200, request=httpx.Request("GET", url), content=b"%PDF-fake"
    )
    _stub_get(monkeypatch, response=response)

    with pytest.raises(UnreadableDocumentError):
        ingest_from_url(url, converter=_FakeConverter("   "))


@pytest.mark.skipif(not AI_DP_PDF.exists(), reason="AI DP corpus PDF not present")
def test_ai_dp_showcase_paragraphs_are_clean_after_normalisation():
    """The demo deep-quotes paragraphs 3.5 and 3.11; after normalisation their
    text must contain 'AI'/'GenAI' and none of the '$A l$' / 'Al' / 'GenAl'
    artifacts, so a 'verified' quote is faithful to the source PDF."""
    text = normalise_glyph_artifacts(ingest_document(AI_DP_PDF))

    i35 = text.find("A major challenge of AI revolves")
    assert i35 != -1, "3.5 opening should read 'AI', not 'Al'"
    seg35 = text[i35 : i35 + 200]
    assert "$" not in seg35
    assert not re.search(r"(?<![A-Za-z])Al(?![A-Za-z])", seg35)

    assert "GenAI" in text
    assert "GenAl" not in text
