import json
from pathlib import Path
from typing import Any

import pytest

from pipeline.chunk import Chunk, chunk_document, run_stage_2


class FakeSpan:
    def __init__(self, start_char: int, end_char: int, text: str) -> None:
        self.start_char = start_char
        self.end_char = end_char
        self.text = text


class FakeDoc:
    def __init__(self, sents: list[FakeSpan]) -> None:
        self.sents = sents


class FakeNLP:
    """Splits on '. ' — good enough for testing offset roundtrip."""

    def __call__(self, text: str) -> FakeDoc:
        sents: list[FakeSpan] = []
        pos = 0
        for part in text.split(". "):
            if not part:
                pos += 2
                continue
            end = pos + len(part)
            # include the trailing ". " for all but the last sentence
            if end < len(text):
                sents.append(FakeSpan(pos, end + 2, text[pos:end + 2]))
                pos = end + 2
            else:
                sents.append(FakeSpan(pos, end, text[pos:end]))
                pos = end
        return FakeDoc(sents)


def test_chunk_offsets_slice_back_to_text():
    text = "The board shall ensure. Recovery is critical. RTO must be defined."
    chunks = chunk_document("doc", text, nlp=FakeNLP())
    for chunk in chunks:
        assert text[chunk["char_start"]:chunk["char_end"]] == chunk["text"]


def test_chunk_ids_are_stable_and_zero_padded():
    text = "One. Two. Three."
    chunks = chunk_document("mydoc", text, nlp=FakeNLP())
    assert chunks[0]["chunk_id"] == "mydoc:0000"
    assert chunks[1]["chunk_id"] == "mydoc:0001"
    assert chunks[2]["chunk_id"] == "mydoc:0002"


def test_chunk_document_carries_doc_id():
    chunks = chunk_document("abc", "One.", nlp=FakeNLP())
    assert chunks[0]["doc_id"] == "abc"


def test_run_stage_2_writes_jsonl(tmp_path: Path):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    (text_dir / "a.md").write_text("Alpha. Beta.")
    (text_dir / "b.md").write_text("Gamma.")
    out = tmp_path / "chunks.jsonl"

    result = run_stage_2(text_dir=text_dir, output_path=out, nlp=FakeNLP())
    assert result == out
    lines = out.read_text().splitlines()
    parsed = [json.loads(line) for line in lines]
    doc_ids = {c["doc_id"] for c in parsed}
    assert doc_ids == {"a", "b"}
    # every chunk still round-trips
    text_a = (text_dir / "a.md").read_text()
    a_chunks = [c for c in parsed if c["doc_id"] == "a"]
    for c in a_chunks:
        assert text_a[c["char_start"]:c["char_end"]] == c["text"]


def test_run_stage_2_warns_on_oversize_chunks(tmp_path: Path, caplog):
    text_dir = tmp_path / "text"
    text_dir.mkdir()
    long_sentence = "x" * 600
    (text_dir / "big.md").write_text(long_sentence)
    out = tmp_path / "chunks.jsonl"

    with caplog.at_level("WARNING"):
        run_stage_2(text_dir=text_dir, output_path=out, nlp=FakeNLP())
    assert any("oversize chunk" in rec.message.lower() for rec in caplog.records)
