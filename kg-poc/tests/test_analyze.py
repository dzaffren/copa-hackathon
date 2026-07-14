import json
from pathlib import Path

import networkx as nx

from pipeline.analyze import (
    doc_similarity_jaccard,
    entity_centrality,
    per_doc_top_entities,
    run_stage_6,
)


def _minimal_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_node("a", node_type="Document", doc_id="a", title="A",
               doc_type="PD", jurisdiction="MY", issuer="BNM",
               issued_date="2025-01-01")
    g.add_node("b", node_type="Document", doc_id="b", title="B",
               doc_type="PD", jurisdiction="MY", issuer="BNM",
               issued_date="2025-01-01")
    g.add_node("topic:cloud", node_type="Entity", entity_id="topic:cloud",
               class_="Topic", canonical_label="cloud", mention_count=5)
    g.add_node("topic:credit", node_type="Entity", entity_id="topic:credit",
               class_="Topic", canonical_label="credit", mention_count=3)
    g.add_edge("a", "topic:cloud", edge_type="mentions", weight=2.5)
    g.add_edge("a", "topic:credit", edge_type="mentions", weight=1.0)
    g.add_edge("b", "topic:cloud", edge_type="mentions", weight=1.5)
    return g


def test_per_doc_top_entities_ranks_by_weight():
    g = _minimal_graph()
    top = per_doc_top_entities(g, "a", k=2)
    assert top[0][0] == "topic:cloud"
    assert top[1][0] == "topic:credit"


def test_doc_similarity_jaccard_on_shared_entities():
    g = _minimal_graph()
    sims = dict(((min(u, v), max(u, v)), s) for u, v, s in doc_similarity_jaccard(g))
    # a: {cloud, credit}; b: {cloud} → J = 1/2
    assert sims[("a", "b")] == 0.5


def test_entity_centrality_shape():
    g = _minimal_graph()
    c = entity_centrality(g)
    assert "topic:cloud" in c
    assert set(c["topic:cloud"].keys()) == {"degree", "betweenness", "pagerank"}


def test_run_stage_6_writes_markdown(tmp_path: Path):
    g = _minimal_graph()
    gm = tmp_path / "graph.graphml"
    nx.write_graphml(g, gm)
    report = run_stage_6(graph_path=gm, output_dir=tmp_path)
    assert report.exists()
    body = report.read_text()
    assert "# KG POC — analysis" in body
    assert "topic:cloud" in body
