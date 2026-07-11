import json
from pathlib import Path

from pipeline.resolve import (
    Entity,
    Mention,
    build_alias_map,
    entity_id_for,
    normalise_surface,
    run_stage_4,
)


def test_normalise_lowercases():
    assert normalise_surface("BOARD") == "board"


def test_normalise_strips_leading_article():
    assert normalise_surface("The board") == "board"
    assert normalise_surface("the RTO") == "rto"


def test_normalise_strips_trailing_plural_s():
    assert normalise_surface("boards") == "board"


def test_normalise_preserves_acronym_trailing_s():
    """All-uppercase acronyms keep their trailing s (BCBS, TPSPs)."""
    assert normalise_surface("BCBS") == "bcbs"
    assert normalise_surface("TPSPs") == "tpsps"


def test_normalise_preserves_multi_word():
    assert normalise_surface("Bank Negara Malaysia") == "bank negara malaysia"


def test_entity_id_is_stable():
    assert entity_id_for("Party", "board") == "party:board"
    assert entity_id_for("RegulatoryBody", "BNM") == "regulatorybody:bnm"


def test_build_alias_map_keys_by_class():
    seeds = [
        {"canonical": "BNM", "class_": "RegulatoryBody",
         "aliases": ["Bank Negara Malaysia"],
         "left_forbidden": [], "right_forbidden": []},
        {"canonical": "board", "class_": "Party", "aliases": ["the board"],
         "left_forbidden": [], "right_forbidden": []},
    ]
    m = build_alias_map(seeds)
    assert m[("bank negara malaysia", "RegulatoryBody")] == "BNM"
    assert m[("bnm", "RegulatoryBody")] == "BNM"
    assert m[("board", "Party")] == "board"


def test_same_string_same_class_merges(tmp_path: Path):
    spans_path = tmp_path / "spans.jsonl"
    spans = [
        {"doc_id": "a", "chunk_id": "a:0000", "char_start": 0, "char_end": 5,
         "surface": "board", "class_": "Party", "source": "gazetteer",
         "confidence": 1.0},
        {"doc_id": "a", "chunk_id": "a:0001", "char_start": 20, "char_end": 25,
         "surface": "Board", "class_": "Party", "source": "gliner",
         "confidence": 0.9},
        {"doc_id": "b", "chunk_id": "b:0000", "char_start": 0, "char_end": 5,
         "surface": "boards", "class_": "Party", "source": "gliner",
         "confidence": 0.8},
    ]
    with spans_path.open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s) + "\n")

    ent_path, men_path = run_stage_4(
        spans_path=spans_path, seeds=[], output_dir=tmp_path
    )
    entities = [json.loads(l) for l in ent_path.read_text().splitlines()]
    mentions = [json.loads(l) for l in men_path.read_text().splitlines()]

    assert len(entities) == 1
    assert entities[0]["entity_id"] == "party:board"
    assert entities[0]["mention_count"] == 3
    assert sorted(entities[0]["docs_appearing_in"]) == ["a", "b"]
    assert len(mentions) == 3
    assert all(m["entity_id"] == "party:board" for m in mentions)


def test_same_string_different_class_stays_separate(tmp_path: Path):
    spans_path = tmp_path / "spans.jsonl"
    spans = [
        {"doc_id": "a", "chunk_id": "a:0000", "char_start": 0, "char_end": 4,
         "surface": "BCBS", "class_": "RegulatoryBody", "source": "gazetteer",
         "confidence": 1.0},
        {"doc_id": "a", "chunk_id": "a:0001", "char_start": 10, "char_end": 14,
         "surface": "BCBS", "class_": "Reference", "source": "gazetteer",
         "confidence": 1.0},
    ]
    with spans_path.open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s) + "\n")

    ent_path, _ = run_stage_4(
        spans_path=spans_path, seeds=[], output_dir=tmp_path
    )
    entities = [json.loads(l) for l in ent_path.read_text().splitlines()]
    ids = {e["entity_id"] for e in entities}
    # BCBS is an acronym → normalisation preserves the trailing 's'.
    assert ids == {"regulatorybody:bcbs", "reference:bcbs"}


def test_alias_collapses_to_canonical(tmp_path: Path):
    spans_path = tmp_path / "spans.jsonl"
    spans = [
        {"doc_id": "a", "chunk_id": "a:0000", "char_start": 0, "char_end": 4,
         "surface": "BNM", "class_": "RegulatoryBody", "source": "gazetteer",
         "confidence": 1.0},
        {"doc_id": "a", "chunk_id": "a:0001", "char_start": 10, "char_end": 30,
         "surface": "Bank Negara Malaysia", "class_": "RegulatoryBody",
         "source": "gliner", "confidence": 0.9},
    ]
    with spans_path.open("w") as fh:
        for s in spans:
            fh.write(json.dumps(s) + "\n")

    seeds = [
        {"canonical": "BNM", "class_": "RegulatoryBody",
         "aliases": ["Bank Negara Malaysia"],
         "left_forbidden": [], "right_forbidden": []},
    ]
    ent_path, men_path = run_stage_4(
        spans_path=spans_path, seeds=seeds, output_dir=tmp_path
    )
    entities = [json.loads(l) for l in ent_path.read_text().splitlines()]
    assert len(entities) == 1
    assert entities[0]["canonical_label"] == "BNM"
    assert entities[0]["mention_count"] == 2
