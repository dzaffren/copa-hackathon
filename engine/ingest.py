"""PDF/DOCX -> clean markdown conversion.

Uses Microsoft's MarkItDown library, which correctly handles the custom font
encodings found in BNM's published PDFs (naive extractors such as pdftotext
or PyPDF produce gibberish on these documents — validated in the discovery
brief's dry-run). Do not substitute a naive extractor here.

**Reading order.** The default MarkItDown extractor reads glyphs geometrically
and mis-orders multi-column BNM pages — list labels get stranded from their
text, clause bodies are lost, page headers inject mid-clause (measured: up to
6.6% stranded labels in the Outsourcing PD). When
``AZURE_DOCINTEL_ENDPOINT`` + ``AZURE_DOCINTEL_API_KEY`` are set, PDFs are
routed through **Azure AI Document Intelligence** (`prebuilt-layout`), which
reconstructs the logical reading order so the downstream anchor-slice parser
receives clean, correctly-ordered text. The output is still verbatim source
text — Document Intelligence transcribes layout, it does not summarise — so the
verbatim-citation guarantee is preserved. Without the credentials the default
extractor is used unchanged (no Azure dependency in CI / offline).
"""

from pathlib import Path
from typing import Any, Optional, Union

from markitdown import MarkItDown
from markitdown._exceptions import MarkItDownException

from engine.config import DOCINTEL_API_KEY, DOCINTEL_ENDPOINT


class UnreadableDocumentError(Exception):
    """Raised when document conversion yields no usable text."""


def _build_converter(
    docintel_endpoint: Optional[str],
    docintel_api_key: Optional[str],
) -> MarkItDown:
    """Construct a MarkItDown converter.

    When both the Document Intelligence endpoint and key are provided, register
    the DI (`prebuilt-layout`) converter at the top of the stack so PDFs use it;
    otherwise return a plain MarkItDown that uses the default extractor.
    """
    if docintel_endpoint and docintel_api_key:
        from azure.core.credentials import AzureKeyCredential

        return MarkItDown(
            docintel_endpoint=docintel_endpoint,
            docintel_credential=AzureKeyCredential(docintel_api_key),
        )
    return MarkItDown()


def ingest_document(
    file_path: Union[str, Path],
    converter: Optional[Any] = None,
) -> str:
    """Convert a PDF or DOCX file to clean markdown text.

    Uses Azure AI Document Intelligence when configured (see module docstring),
    else the default MarkItDown extractor. Pass an explicit ``converter``
    (anything with a ``.convert(str) -> result`` method) to override — tests
    inject a stub so no network/credentials are needed.

    Raises:
        UnreadableDocumentError: if conversion yields empty or
            whitespace-only output, or if the file cannot be converted
            at all (e.g. corrupt/unrecognisable input).
    """
    if converter is None:
        converter = _build_converter(DOCINTEL_ENDPOINT, DOCINTEL_API_KEY)

    try:
        result = converter.convert(str(file_path))
    except MarkItDownException as exc:
        raise UnreadableDocumentError(
            f"Conversion of '{file_path}' failed: {exc}"
        ) from exc

    text = result.text_content

    if text is None or text.strip() == "":
        raise UnreadableDocumentError(
            f"Conversion of '{file_path}' yielded no usable text"
        )

    return text
