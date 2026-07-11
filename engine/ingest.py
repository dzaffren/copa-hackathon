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

import re
from pathlib import Path
from typing import Any, Optional, Union

from markitdown import MarkItDown
from markitdown._exceptions import MarkItDownException

from engine.config import (
    DOCINTEL_API_KEY,
    DOCINTEL_API_VERSION,
    DOCINTEL_ENDPOINT,
)


class UnreadableDocumentError(Exception):
    """Raised when document conversion yields no usable text."""


# --- Glyph-artifact normalisation (spec-source-connection-engine.md, Task 1) ---
#
# The AI Discussion Paper's stylised "AI" logotype is misread by the extractor
# in a few PATTERNED ways (measured on data/corpus/dp_ai_financial_sector.pdf):
#   - short LaTeX "math-mode" wrappers around the glyph: `$A l$`,
#     `$\mathrm { A l }$`, `$\mathrm { A l } .$`, `$A l ^ { 2 } ,$`
#   - a bare mis-cased token: standalone `Al` (→ `AI`), `GenAl` (→ `GenAI`),
#     `Al-driven` (→ `AI-driven`), and the `Fls`/`Fl` mis-read of `FIs`/`FI`.
#
# `normalise_glyph_artifacts` fixes ONLY these provably-safe, self-contained
# patterns so the fix is faithful to the source (the PDF says "AI"; the extractor
# broke it) — which STRENGTHENS the verbatim guarantee rather than weakening it.
#
# It deliberately does NOT touch:
#   - numeric/data math like `$(n = 102)$`, `$100$`, `$59$` (real survey figures);
#   - long or UNTERMINATED `$...$` spans (the extractor leaves some `$` dangling
#     around whole paragraphs 4.8–5.10 and the references table) — stripping those
#     safely is a separate, larger job and is out of scope here.
# A guard skips any `$...$` run longer than _MAX_MATH_FIX so a dangling delimiter
# can never swallow real content.

_MAX_MATH_FIX = 24  # chars inside `$...$` we are willing to rewrite; longer = leave alone

# Short `$...$` runs that are the mangled "AI" glyph → "AI". Anchored to the exact
# observed forms so nothing else matches. Any trailing sentence punctuation that
# sat inside the `$...$` (e.g. `$\mathrm { A l } .$`) is CAPTURED and preserved —
# never silently dropped (that would corrupt the verbatim source text).
_MATH_AI_RE = re.compile(
    r"\$\s*(?:\\mathrm\s*\{\s*)?A\s*l\s*\}?\s*(?:\^\s*\{[^}]*\}\s*)?([.,]?)\s*\$"
)

# Bare mis-cased tokens. `\bAl\b` etc. — word-boundary anchored so we never touch
# real words like "Also", "Alert", "also", or a name ending in "-al".
_BARE_FIXES = (
    (re.compile(r"\bGenAl\b"), "GenAI"),
    (re.compile(r"\bAl-(?=[a-z])"), "AI-"),   # "Al-driven" → "AI-driven"
    (re.compile(r"\bAl\b"), "AI"),
    (re.compile(r"\bFls\b"), "FIs"),
)


def normalise_glyph_artifacts(text: str) -> str:
    """Repair the patterned "AI"-glyph mis-reads in extracted markdown.

    Fixes only the narrow, self-contained artifacts documented above; leaves
    numeric math, long spans, and unterminated ``$...$`` regions untouched.
    Idempotent: running it twice yields the same result.
    """

    def _replace_math(match: "re.Match[str]") -> str:
        inner = match.group(0)
        # Safety: never rewrite a long `$...$` run (could be a dangling delimiter
        # wrapping real content); leave it exactly as-is.
        if len(inner) > _MAX_MATH_FIX:
            return inner
        # Preserve any trailing sentence punctuation that was inside the wrapper.
        return "AI" + match.group(1)

    text = _MATH_AI_RE.sub(_replace_math, text)
    for pattern, replacement in _BARE_FIXES:
        text = pattern.sub(replacement, text)
    return text


def _build_converter(
    docintel_endpoint: Optional[str],
    docintel_api_key: Optional[str],
    docintel_api_version: str = DOCINTEL_API_VERSION,
) -> MarkItDown:
    """Construct a MarkItDown converter.

    When both the Document Intelligence endpoint and key are provided, register
    the DI (`prebuilt-layout`) converter at the top of the stack so PDFs use it;
    otherwise return a plain MarkItDown that uses the default extractor.

    The ``docintel_api_version`` override is load-bearing: MarkItDown hardcodes
    an old preview api-version that GA DI resources reject with a 404 (which
    MarkItDown then silently swallows, falling back to the default extractor —
    masking the misconfiguration). Passing the GA version makes DI actually run.
    """
    if docintel_endpoint and docintel_api_key:
        from azure.core.credentials import AzureKeyCredential

        return MarkItDown(
            docintel_endpoint=docintel_endpoint,
            docintel_credential=AzureKeyCredential(docintel_api_key),
            docintel_api_version=docintel_api_version,
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
