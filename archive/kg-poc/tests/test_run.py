import json
from pathlib import Path
from typing import Any

import pytest

from pipeline.run import run_all


class StubMarkItDownResult:
    def __init__(self, text: str) -> None:
        self.text_content = text


class StubMarkItDown:
    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def convert(self, path: str) -> StubMarkItDownResult:
        return StubMarkItDownResult(self._mapping[path])


class StubGliner:
    """Returns one high-confidence gliner span per chunk, matching the word
    "recovery" if present."""

    def predict_entities(self, text: str, labels: list[str]) -> list[dict]:
        idx = text.find("recovery")
        if idx == -1:
            return []
        return [{
            "start": idx, "end": idx + len("recovery"),
            "text": "recovery",
            "label": "activity or process",
            "score": 0.85,
        }]


def test_end_to_end_smoke(tmp_path: Path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    pdf_a = corpus_dir / "a.pdf"
    pdf_b = corpus_dir / "b.pdf"
    pdf_a.write_bytes(b"a")
    pdf_b.write_bytes(b"b")

    text_a = (
        "The board shall ensure recovery of critical systems. "
        "BNM issued RMiT in 2025. "
        "Cloud services require notification. "
        "Recovery is critical."
    )
    text_b = (
        "The board approves outsourcing. "
        "Bank Negara Malaysia oversees. "
        "Cloud is a key topic. "
        "Recovery testing is mandatory."
    )
    converter = StubMarkItDown({str(pdf_a): text_a, str(pdf_b): text_b})

    documents = {
        "a": {"doc_id": "a", "source_path": pdf_a, "title": "Doc A",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
        "b": {"doc_id": "b", "source_path": pdf_b, "title": "Doc B",
              "doc_type": "PD", "jurisdiction": "MY", "issuer": "BNM",
              "issued_date": "2025-01-01"},
    }

    output = tmp_path / "out"
    run_all(
        documents=documents,
        output_dir=output,
        converter=converter,
        gliner=StubGliner(),
    )

    # Every stage's artifact exists
    assert (output / "text" / "a.md").exists()
    assert (output / "text" / "b.md").exists()
    assert (output / "chunks.jsonl").exists()
    assert (output / "spans.jsonl").exists()
    assert (output / "entities.jsonl").exists()
    assert (output / "mentions.jsonl").exists()
    assert (output / "graph.graphml").exists()
    assert (output / "graph.json").exists()
    assert (output / "analysis.md").exists()
    assert (output / "graph.html").exists()

    # Verbatim invariant — every span slices back byte-exactly
    spans = [json.loads(l) for l in (output / "spans.jsonl").read_text().splitlines()]
    text_by_doc = {
        "a": (output / "text" / "a.md").read_text(),
        "b": (output / "text" / "b.md").read_text(),
    }
    for s in spans:
        source = text_by_doc[s["doc_id"]]
        assert source[s["char_start"]:s["char_end"]] == s["surface"], (
            f"broken provenance for span {s}"
        )
