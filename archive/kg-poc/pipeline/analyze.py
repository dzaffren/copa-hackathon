"""Stage 6 — graph → analysis.md + figures.

Pure NetworkX analytics: degree, betweenness, PageRank on Entity nodes;
per-doc top-k by mentions tf-idf; pairwise Jaccard similarity on doc
entity sets. Louvain community detection deferred to a v2 tweak (adds
python-louvain dep and drives a filtered "communities" figure) — kept out
of v1 to minimise deps.
"""

import logging
from pathlib import Path

import networkx as nx

from pipeline.config import DATA_DIR

logger = logging.getLogger(__name__)


def _document_nodes(g: nx.MultiDiGraph) -> list[str]:
    return [n for n, d in g.nodes(data=True) if d.get("node_type") == "Document"]


def _entity_nodes(g: nx.MultiDiGraph) -> list[str]:
    return [n for n, d in g.nodes(data=True) if d.get("node_type") == "Entity"]


def per_doc_top_entities(
    g: nx.MultiDiGraph, doc_id: str, k: int = 10
) -> list[tuple[str, float]]:
    """Top-k outgoing `mentions` edges for a document, by weight desc."""
    weighted: list[tuple[str, float]] = []
    for _, v, data in g.out_edges(doc_id, data=True):
        if data.get("edge_type") == "mentions":
            weighted.append((v, float(data.get("weight", 0.0))))
    weighted.sort(key=lambda x: x[1], reverse=True)
    return weighted[:k]


def _entity_set_per_doc(g: nx.MultiDiGraph) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for d in _document_nodes(g):
        result[d] = {
            v for _, v, data in g.out_edges(d, data=True)
            if data.get("edge_type") == "mentions"
        }
    return result


def doc_similarity_jaccard(
    g: nx.MultiDiGraph,
) -> list[tuple[str, str, float]]:
    """Pairwise Jaccard similarity on each doc's entity set (mentions)."""
    per_doc = _entity_set_per_doc(g)
    docs = sorted(per_doc.keys())
    out: list[tuple[str, str, float]] = []
    for i, a in enumerate(docs):
        for b in docs[i + 1:]:
            union = per_doc[a] | per_doc[b]
            if not union:
                out.append((a, b, 0.0))
                continue
            j = len(per_doc[a] & per_doc[b]) / len(union)
            out.append((a, b, j))
    return out


def entity_centrality(g: nx.MultiDiGraph) -> dict[str, dict[str, float]]:
    """Degree, betweenness, PageRank per Entity node.

    Computed on the underlying simple digraph (edge-type-agnostic) — for a
    POC that's fine; a v2 tweak could weight by edge type.
    """
    simple = nx.DiGraph()
    for u, v in g.edges():
        simple.add_edge(u, v)
    if simple.number_of_nodes() == 0:
        return {}

    deg = dict(simple.degree())
    bet = nx.betweenness_centrality(simple) if simple.number_of_nodes() > 1 else {}
    pr = nx.pagerank(simple) if simple.number_of_nodes() > 0 else {}

    result: dict[str, dict[str, float]] = {}
    for n in _entity_nodes(g):
        result[n] = {
            "degree": float(deg.get(n, 0)),
            "betweenness": float(bet.get(n, 0.0)),
            "pagerank": float(pr.get(n, 0.0)),
        }
    return result


def _render_top_entities_table(
    g: nx.MultiDiGraph, k: int = 10
) -> str:
    lines = ["## Per-document top entities (tf-idf)\n"]
    for d in _document_nodes(g):
        lines.append(f"### {d}\n")
        lines.append("| entity | weight |")
        lines.append("| --- | --- |")
        for e, w in per_doc_top_entities(g, d, k=k):
            lines.append(f"| {e} | {w:.3f} |")
        lines.append("")
    return "\n".join(lines)


def _render_centrality_table(g: nx.MultiDiGraph, k: int = 20) -> str:
    c = entity_centrality(g)
    lines = ["## Top entity centrality\n",
             "| entity | degree | betweenness | pagerank |",
             "| --- | --- | --- | --- |"]
    top = sorted(c.items(), key=lambda x: x[1]["pagerank"], reverse=True)[:k]
    for e, s in top:
        lines.append(
            f"| {e} | {s['degree']:.0f} | {s['betweenness']:.4f} | {s['pagerank']:.4f} |"
        )
    return "\n".join(lines)


def _render_similarity_table(g: nx.MultiDiGraph) -> str:
    lines = ["## Document similarity (Jaccard on entity sets)\n",
             "| doc A | doc B | jaccard |",
             "| --- | --- | --- |"]
    sims = sorted(doc_similarity_jaccard(g), key=lambda x: x[2], reverse=True)
    for a, b, s in sims:
        lines.append(f"| {a} | {b} | {s:.3f} |")
    return "\n".join(lines)


def run_stage_6(
    graph_path: Path = DATA_DIR / "graph.graphml",
    output_dir: Path = DATA_DIR,
) -> Path:
    """Render the analysis markdown from the built graph."""
    g = nx.read_graphml(graph_path)
    # read_graphml returns a MultiDiGraph iff written with keys=True; be
    # defensive and coerce.
    if not isinstance(g, nx.MultiDiGraph):
        g = nx.MultiDiGraph(g)

    output_dir.mkdir(parents=True, exist_ok=True)
    body = [
        "# KG POC — analysis\n",
        f"- nodes: {g.number_of_nodes()}",
        f"- edges: {g.number_of_edges()}",
        "",
        _render_top_entities_table(g),
        "",
        _render_centrality_table(g),
        "",
        _render_similarity_table(g),
    ]
    out = output_dir / "analysis.md"
    out.write_text("\n".join(body))
    logger.info("Stage 6: analysis written to %s", out)
    return out
