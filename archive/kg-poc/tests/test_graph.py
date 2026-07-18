import json
import math
from pathlib import Path

import networkx as nx

from pipeline.graph import build_graph, run_stage_5


def _entity(entity_id: str, class_: str, canonical: str, count: int, docs: list[str]) -> dict:
    return {
        "entity_id": entity_id, "class_": class_,
        "canonical_label": canonical, "aliases": [],
        "mention_count": count, "docs_appearing_in": docs,
    }


def _mention(entity_id: str, doc_id: str, chunk_id: str) -> dict:
    return {
        "entity_id": entity_id, "doc_id": doc_id,
        "chunk_id": chunk_id, "char_start": 0, "char_end": 5,
    }


def _document(doc_id: str) -> dict:
    from pathlib import Path
    return {
        "doc_id": doc_id, "source_path": Path(f"/tmp/{doc_id}.pdf"),
        "title": doc_id.upper(), "doc_type": "PD",
        "jurisdiction": "MY", "issuer": "BNM",
        "issued_date": "2025-01-01",
    }


def test_document_nodes_have_node_type_and_attrs():
    entities = [_entity("party:board", "Party", "board", 5, ["a", "b"])]
    mentions = [_mention("party:board", "a", "a:0000"),
                _mention("party:board", "a", "a:0001"),
                _mention("party:board", "b", "b:0000")]
    docs = {"a": _document("a"), "b": _document("b")}
    g = build_graph(entities, mentions, docs)
    assert g.nodes["a"]["node_type"] == "Document"
    assert g.nodes["a"]["issuer"] == "BNM"


def test_entity_nodes_below_mention_min_are_excluded():
    entities = [
        _entity("party:board", "Party", "board", 5, ["a"]),
        _entity("topic:foo", "Topic", "foo", 1, ["a"]),  # below MENTION_COUNT_MIN
    ]
    mentions = [_mention("party:board", "a", "a:0000")] * 5 + [
        _mention("topic:foo", "a", "a:0001")
    ]
    docs = {"a": _document("a")}
    g = build_graph(entities, mentions, docs)
    assert "party:board" in g.nodes
    assert "topic:foo" not in g.nodes


def test_mentions_edge_weight_is_tfidf():
    """tf-idf: rare terms weighted higher than common ones."""
    entities = [
        _entity("topic:common", "Topic", "common", 4, ["a", "b"]),
        _entity("topic:rare", "Topic", "rare", 2, ["a"]),
    ]
    mentions = (
        [_mention("topic:common", "a", f"a:{i:04d}") for i in range(2)]
        + [_mention("topic:common", "b", f"b:{i:04d}") for i in range(2)]
        + [_mention("topic:rare", "a", f"a:{i+10:04d}") for i in range(2)]
    )
    docs = {"a": _document("a"), "b": _document("b")}
    g = build_graph(entities, mentions, docs)

    common_edge = g.get_edge_data("a", "topic:common")
    rare_edge = g.get_edge_data("a", "topic:rare")
    # Multi-edges: find the "mentions" one
    common_w = next(d["weight"] for _, d in common_edge.items() if d["edge_type"] == "mentions")
    rare_w = next(d["weight"] for _, d in rare_edge.items() if d["edge_type"] == "mentions")
    # rare (in 1 of 2 docs) has higher idf than common (in 2 of 2)
    assert rare_w > common_w


def test_about_edges_are_only_topic_class():
    entities = [
        _entity("topic:cloud", "Topic", "cloud", 5, ["a"]),
        _entity("party:board", "Party", "board", 5, ["a"]),
    ]
    mentions = (
        [_mention("topic:cloud", "a", f"a:{i:04d}") for i in range(5)]
        + [_mention("party:board", "a", f"a:{i+10:04d}") for i in range(5)]
    )
    docs = {"a": _document("a")}
    g = build_graph(entities, mentions, docs)

    about_targets = {v for u, v, d in g.edges(data=True) if d["edge_type"] == "about" and u == "a"}
    assert about_targets == {"topic:cloud"}


def test_co_occurs_edges_only_between_entities_sharing_a_chunk():
    entities = [
        _entity("party:board", "Party", "board", 3, ["a"]),
        _entity("topic:cloud", "Topic", "cloud", 3, ["a"]),
        _entity("topic:credit", "Topic", "credit", 2, ["a"]),
    ]
    mentions = [
        _mention("party:board", "a", "a:0000"),
        _mention("topic:cloud", "a", "a:0000"),   # same chunk as board
        _mention("party:board", "a", "a:0001"),
        _mention("topic:cloud", "a", "a:0001"),
        _mention("party:board", "a", "a:0002"),
        _mention("topic:cloud", "a", "a:0002"),
        _mention("topic:credit", "a", "a:9999"),  # own chunk
        _mention("topic:credit", "a", "a:9998"),
    ]
    docs = {"a": _document("a")}
    g = build_graph(entities, mentions, docs)

    co_pairs = {
        tuple(sorted([u, v]))
        for u, v, d in g.edges(data=True)
        if d["edge_type"] == "co-occurs"
    }
    assert ("party:board", "topic:cloud") in co_pairs
    assert ("party:board", "topic:credit") not in co_pairs


def test_run_stage_5_writes_graphml_and_json(tmp_path: Path):
    entities_p = tmp_path / "entities.jsonl"
    mentions_p = tmp_path / "mentions.jsonl"
    with entities_p.open("w") as fh:
        fh.write(json.dumps(_entity("party:board", "Party", "board", 2, ["a"])) + "\n")
    with mentions_p.open("w") as fh:
        fh.write(json.dumps(_mention("party:board", "a", "a:0000")) + "\n")
        fh.write(json.dumps(_mention("party:board", "a", "a:0001")) + "\n")
    docs = {"a": _document("a")}

    gm, gj = run_stage_5(
        entities_path=entities_p,
        mentions_path=mentions_p,
        output_dir=tmp_path,
        documents=docs,
    )
    assert gm.exists()
    assert gj.exists()
    assert "nodes" in json.loads(gj.read_text())
