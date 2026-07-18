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


import json
from pathlib import Path

from pipeline.extract import (
    extract_gliner_spans,
    mask_chunk_text,
    run_stage_3,
)


class FakeGliner:
    """Injectable stub matching the GLiNER predict_entities signature."""

    def __init__(self, canned: dict[str, list[dict]]) -> None:
        # canned maps chunk text (after masking) → predictions
        self._canned = canned
        self.calls: list[str] = []

    def predict_entities(self, text: str, labels: list[str]) -> list[dict]:
        self.calls.append(text)
        return self._canned.get(text, [])


def test_mask_chunk_text_replaces_gazetteer_hits_with_spaces():
    chunk_text = "The board shall ensure recovery."
    span = {
        "char_start": 4, "char_end": 9,  # "board"
        "surface": "board", "class_": "Party", "source": "gazetteer",
        "confidence": 1.0, "doc_id": "d", "chunk_id": "d:0000",
    }
    masked = mask_chunk_text(chunk_text, chunk_char_start=0, gazetteer_spans_in_chunk=[span])
    assert len(masked) == len(chunk_text)
    assert masked[4:9] == "     "
    assert masked.startswith("The       shall")


def test_extract_gliner_spans_returns_kept_and_dropped():
    chunks = [_chunk("d", "d:0000", 0, "Board ensures recovery.")]
    canned = {
        "Board ensures recovery.": [
            {"start": 0, "end": 5, "text": "Board",
             "label": "regulated actor or third party", "score": 0.9},
            {"start": 15, "end": 23, "text": "recovery",
             "label": "activity or process", "score": 0.4},  # below 0.7
        ]
    }
    gliner = FakeGliner(canned)
    kept, dropped = extract_gliner_spans(chunks, gazetteer_spans=[], gliner=gliner)
    assert len(kept) == 1
    assert kept[0]["surface"] == "Board"
    assert kept[0]["class_"] == "Party"
    assert kept[0]["source"] == "gliner"
    assert kept[0]["confidence"] == 0.9
    assert len(dropped) == 1
    assert dropped[0]["surface"] == "recovery"
    assert dropped[0]["confidence"] == 0.4


def test_extract_gliner_offsets_are_absolute_within_markdown():
    chunks = [_chunk("d", "d:0000", 100, "The board ensures.")]
    canned = {
        "The board ensures.": [
            {"start": 4, "end": 9, "text": "board",
             "label": "regulated actor or third party", "score": 0.9},
        ]
    }
    kept, _ = extract_gliner_spans(chunks, gazetteer_spans=[], gliner=FakeGliner(canned))
    assert kept[0]["char_start"] == 104
    assert kept[0]["char_end"] == 109


def test_run_stage_3_writes_spans_and_dropped(tmp_path: Path):
    chunks_path = tmp_path / "chunks.jsonl"
    chunks = [_chunk("d", "d:0000", 0, "The board ensures recovery.")]
    with chunks_path.open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(c) + "\n")

    seeds = [
        {"canonical": "board", "class_": "Party", "aliases": [],
         "left_forbidden": [], "right_forbidden": []},
    ]
    canned = {
        # gazetteer masks "board" → "     ", so GLiNER sees this exact string
        "The       ensures recovery.": [
            {"start": 18, "end": 26, "text": "recovery",
             "label": "activity or process", "score": 0.85},
            {"start": 18, "end": 26, "text": "recovery",
             "label": "domain topic", "score": 0.5},
        ]
    }
    gliner = FakeGliner(canned)
    out_dir = tmp_path / "out"

    kept_path, dropped_path = run_stage_3(
        chunks_path=chunks_path,
        seeds=seeds,
        output_dir=out_dir,
        gliner=gliner,
    )

    kept = [json.loads(l) for l in kept_path.read_text().splitlines()]
    dropped = [json.loads(l) for l in dropped_path.read_text().splitlines()]

    # gazetteer hit for "board" + one gliner span above threshold
    surfaces_kept = {s["surface"] for s in kept}
    assert "board" in surfaces_kept
    assert "recovery" in surfaces_kept
    # one gliner span below threshold
    assert len(dropped) == 1
    assert dropped[0]["surface"] == "recovery"
