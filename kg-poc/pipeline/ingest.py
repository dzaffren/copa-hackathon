"""Stage 1 — PDF → clean markdown.

Uses MarkItDown; when AZURE_DOCINTEL_ENDPOINT + AZURE_DOCINTEL_API_KEY are
set, routes PDFs through Azure Document Intelligence (prebuilt-layout) for
correct multi-column reading order — BNM PDFs mis-order otherwise. Direct
port of engine/ingest.py's pattern, standalone in this package (no cross-
package import).
"""

import os
from pathlib import Path
from typing import Any, Optional

from pipeline.config import DATA_DIR
from pipeline.corpus import DOCUMENTS

_DOCINTEL_ENDPOINT = os.environ.get("AZURE_DOCINTEL_ENDPOINT")
_DOCINTEL_API_KEY = os.environ.get("AZURE_DOCINTEL_API_KEY")
_DOCINTEL_API_VERSION = os.environ.get("AZURE_DOCINTEL_API_VERSION", "2024-11-30")


class UnreadableDocumentError(Exception):
    """PDF conversion yielded empty text or the converter itself failed."""


def _build_default_converter() -> Any:
    """Construct a MarkItDown converter, optionally with Azure Document
    Intelligence when credentials are set.
    """
    from markitdown import MarkItDown

    if _DOCINTEL_ENDPOINT and _DOCINTEL_API_KEY:
        from azure.core.credentials import AzureKeyCredential

        return MarkItDown(
            docintel_endpoint=_DOCINTEL_ENDPOINT,
            docintel_credential=AzureKeyCredential(_DOCINTEL_API_KEY),
            docintel_api_version=_DOCINTEL_API_VERSION,
        )
    return MarkItDown()


def ingest_document(
    source_path: Path,
    converter: Optional[Any] = None,
) -> str:
    """Convert a single PDF to markdown. Raises on empty/failed output.

    `converter` is any object with a `.convert(path_str) -> obj` method where
    `obj.text_content` is a str. Tests inject a stub; production leaves it
    None so the default MarkItDown converter is built.
    """
    if converter is None:
        converter = _build_default_converter()

    try:
        result = converter.convert(str(source_path))
    except Exception as exc:
        raise UnreadableDocumentError(
            f"Conversion of {source_path} failed: {exc}"
        ) from exc

    text = getattr(result, "text_content", None)
    if text is None or text.strip() == "":
        raise UnreadableDocumentError(
            f"Conversion of {source_path} yielded no usable text"
        )
    return text


def run_stage_1(
    documents: dict = DOCUMENTS,
    output_dir: Path = DATA_DIR / "text",
    converter: Optional[Any] = None,
) -> dict[str, Path]:
    """Ingest every document, write `{doc_id}.md` under `output_dir`.

    Two-pass: convert all documents first, then write files only if every
    conversion succeeded. Fails loudly on the first unreadable document with
    zero on-disk residue from this run.
    """
    # Pass 1: convert everything in memory. If any doc fails, this raises
    # before any file is written.
    results: dict[str, str] = {}
    for doc_id, entry in documents.items():
        results[doc_id] = ingest_document(entry["source_path"], converter=converter)

    # Pass 2: only reached if every conversion succeeded — now materialise.
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    for doc_id, markdown in results.items():
        out_path = output_dir / f"{doc_id}.md"
        out_path.write_text(markdown)
        outputs[doc_id] = out_path
    return outputs
