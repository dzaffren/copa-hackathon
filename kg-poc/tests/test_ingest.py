from pathlib import Path
from typing import Any

import pytest

from pipeline.ingest import (
    UnreadableDocumentError,
    ingest_document,
    run_stage_1,
)


class StubResult:
    def __init__(self, text: str) -> None:
        self.text_content = text


class StubConverter:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping
        self.calls: list[str] = []

    def convert(self, path: str) -> StubResult:
        self.calls.append(path)
        return StubResult(self._mapping[path])


def test_ingest_document_returns_markdown_from_converter(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"pdf")
    converter = StubConverter({str(pdf): "# hello"})
    assert ingest_document(pdf, converter=converter) == "# hello"


def test_ingest_document_raises_on_empty_output(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"pdf")
    converter = StubConverter({str(pdf): "   \n\n  "})
    with pytest.raises(UnreadableDocumentError):
        ingest_document(pdf, converter=converter)


def test_ingest_document_raises_when_converter_raises(tmp_path: Path):
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"pdf")

    class Boom:
        def convert(self, path: str) -> Any:
            raise RuntimeError("bad pdf")

    with pytest.raises(UnreadableDocumentError):
        ingest_document(pdf, converter=Boom())


def test_run_stage_1_writes_markdown_per_doc(tmp_path: Path):
    pdf_a = tmp_path / "a.pdf"
    pdf_b = tmp_path / "b.pdf"
    pdf_a.write_bytes(b"a")
    pdf_b.write_bytes(b"b")

    documents = {
        "a": {"doc_id": "a", "source_path": pdf_a, "title": "A",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
        "b": {"doc_id": "b", "source_path": pdf_b, "title": "B",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
    }
    converter = StubConverter({str(pdf_a): "A body", str(pdf_b): "B body"})
    out_dir = tmp_path / "text"

    outputs = run_stage_1(documents=documents, output_dir=out_dir, converter=converter)

    assert outputs["a"].read_text() == "A body"
    assert outputs["b"].read_text() == "B body"
    assert outputs["a"].name == "a.md"
    assert outputs["b"].name == "b.md"
