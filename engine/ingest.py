"""PDF/DOCX -> clean markdown conversion.

Uses Microsoft's MarkItDown library, which correctly handles the custom font
encodings found in BNM's published PDFs (naive extractors such as pdftotext
or PyPDF produce gibberish on these documents — validated in the discovery
brief's dry-run). Do not substitute a naive extractor here.
"""

from pathlib import Path
from typing import Union

from markitdown import MarkItDown
from markitdown._exceptions import MarkItDownException


class UnreadableDocumentError(Exception):
    """Raised when document conversion yields no usable text."""


def ingest_document(file_path: Union[str, Path]) -> str:
    """Convert a PDF or DOCX file to clean markdown text.

    Raises:
        UnreadableDocumentError: if conversion yields empty or
            whitespace-only output, or if the file cannot be converted
            at all (e.g. corrupt/unrecognisable input).
    """
    converter = MarkItDown()

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
