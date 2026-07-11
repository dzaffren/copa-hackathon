from typing import Any

import pytest

from pipeline.chunk import Chunk
from pipeline.extract import Span, extract_gazetteer_spans


def _chunk(doc_id: str, chunk_id: str, char_start: int, text: str) -> Chunk:
    return {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "char_start": char_start,
        "char_end": char_start + len(text),
        "text": text,
    }


def test_gazetteer_finds_seed_canonical():
    chunks = [_chunk("d", "d:0000", 100, "The board shall ensure recovery.")]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert len(spans) == 1
    s = spans[0]
    assert s["surface"] == "board"
    assert s["class_"] == "Party"
    assert s["source"] == "gazetteer"
    assert s["confidence"] == 1.0
    # absolute offsets within the parent markdown, not the chunk
    assert s["char_start"] == 104
    assert s["char_end"] == 109


def test_gazetteer_finds_aliases():
    chunks = [_chunk("d", "d:0000", 0, "The Bank Negara Malaysia issued RMiT.")]
    seeds = [
        {"canonical": "BNM", "class_": "RegulatoryBody",
         "aliases": ["Bank Negara Malaysia"],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert len(spans) == 1
    assert spans[0]["surface"] == "Bank Negara Malaysia"
    assert spans[0]["class_"] == "RegulatoryBody"


def test_gazetteer_does_not_match_substring():
    """`board` in `cardboard` must NOT match — whole-token only."""
    chunks = [_chunk("d", "d:0000", 0, "The cardboard box was full.")]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert spans == []


def test_gazetteer_class_collision_produces_two_spans():
    """Same surface, two different classes → both spans emitted; resolver
    keeps them distinct."""
    chunks = [_chunk("d", "d:0000", 0, "BCBS issued guidance.")]
    seeds = [
        {"canonical": "BCBS", "class_": "RegulatoryBody", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
        {"canonical": "BCBS", "class_": "Reference", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    classes = {s["class_"] for s in spans}
    assert classes == {"RegulatoryBody", "Reference"}


def test_gazetteer_respects_left_forbidden():
    chunks = [_chunk("d", "d:0000", 0, "The Basel Committee met.")]
    seeds = [
        {"canonical": "Committee", "class_": "Party", "aliases": [],
         "left_forbidden": ["Basel"], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert spans == []


def test_gazetteer_respects_right_forbidden():
    chunks = [_chunk("d", "d:0000", 0, "The board of directors met.")]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": ["of"]},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    assert spans == []


def test_gazetteer_absolute_offsets_slice_back(tmp_path):
    """The invariant: markdown[span.char_start:span.char_end] == span.surface."""
    markdown = "The board shall ensure recovery. The RTO is critical."
    chunks = [_chunk("d", "d:0000", 0, markdown)]
    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
        {"canonical": "RTO", "class_": "Requirement", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    spans = extract_gazetteer_spans(chunks, seeds)
    for s in spans:
        assert markdown[s["char_start"]:s["char_end"]] == s["surface"]
