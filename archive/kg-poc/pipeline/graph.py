"""Stage 5 — entities + mentions → NetworkX MultiDiGraph.

Two node types (Document, Entity) and five edge types (mentions,
co-occurs, about, cites, same-as). Weights are tf-idf on mentions,
PMI on co-occurs. Entities with fewer than MENTION_COUNT_MIN mentions
are excluded from the graph (still present in entities.jsonl).

cites and same-as are v3 hooks — implemented but produce zero edges on
the BNM-only v1 corpus (no BCBS references / no BCBS Document nodes).
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional

import networkx as nx

from pipeline.config import DATA_DIR, MENTION_COUNT_MIN
from pipeline.corpus import DOCUMENTS, DocumentEntry
from pipeline.resolve import Entity, Mention

logger = logging.getLogger(__name__)


def _tfidf_edges(
    entities: list[Entity],
    mentions: list[Mention],
    documents: dict[str, DocumentEntry],
) -> list[tuple[str, str, float]]:
    """Compute tf-idf on (doc, entity) pairs.

    tf = raw count of mentions of entity in doc
    idf = log(N / df) where df = # docs containing the entity, N = # docs
    """
    n_docs = len(documents)
    counts: dict[tuple[str, str], int] = {}
    for m in mentions:
        counts[(m["doc_id"], m["entity_id"])] = counts.get((m["doc_id"], m["entity_id"]), 0) + 1

    df: dict[str, int] = {e["entity_id"]: len(e["docs_appearing_in"]) for e in entities}

    edges: list[tuple[str, str, float]] = []
    for (doc_id, entity_id), tf in counts.items():
        d = df.get(entity_id, 1)
        idf = math.log(n_docs / d) if d > 0 else 0.0
        edges.append((doc_id, entity_id, float(tf) * idf))
    return edges


def _pmi_edges(
    mentions: list[Mention],
    kept_entities: set[str],
) -> list[tuple[str, str, float]]:
    """Compute PMI over entity pairs that co-occur in the same chunk.

    Only entity pairs where both are in `kept_entities` (i.e. above
    mention_count threshold) contribute.
    """
    # chunk -> set(entity_ids)
    by_chunk: dict[str, set[str]] = {}
    for m in mentions:
        if m["entity_id"] not in kept_entities:
            continue
        by_chunk.setdefault(m["chunk_id"], set()).add(m["entity_id"])

    total_chunks = max(len(by_chunk), 1)
    single_count: dict[str, int] = {}
    pair_count: dict[tuple[str, str], int] = {}
    for chunk_id, ent_set in by_chunk.items():
        ents = sorted(ent_set)
        for e in ents:
            single_count[e] = single_count.get(e, 0) + 1
        for i, a in enumerate(ents):
            for b in ents[i + 1:]:
                pair_count[(a, b)] = pair_count.get((a, b), 0) + 1

    edges: list[tuple[str, str, float]] = []
    for (a, b), c_ab in pair_count.items():
        p_ab = c_ab / total_chunks
        p_a = single_count[a] / total_chunks
        p_b = single_count[b] / total_chunks
        if p_a > 0 and p_b > 0 and p_ab > 0:
            pmi = math.log(p_ab / (p_a * p_b))
            edges.append((a, b, pmi))
    return edges


def build_graph(
    entities: list[Entity],
    mentions: list[Mention],
    documents: dict[str, DocumentEntry],
    top_k_topics: int = 10,
) -> nx.MultiDiGraph:
    """Assemble the graph. Applies MENTION_COUNT_MIN filter."""
    g = nx.MultiDiGraph()

    # Document nodes
    for doc_id, entry in documents.items():
        g.add_node(
            doc_id,
            node_type="Document",
            doc_id=doc_id,
            doc_type=entry["doc_type"],
            title=entry["title"],
            jurisdiction=entry["jurisdiction"],
            issuer=entry["issuer"],
            issued_date=entry["issued_date"],
        )

    # Entity nodes (above threshold only)
    kept_entity_ids: set[str] = set()
    for e in entities:
        if e["mention_count"] < MENTION_COUNT_MIN:
            continue
        kept_entity_ids.add(e["entity_id"])
        g.add_node(
            e["entity_id"],
            node_type="Entity",
            entity_id=e["entity_id"],
            class_=e["class_"],
            canonical_label=e["canonical_label"],
            mention_count=e["mention_count"],
        )

    # mentions edges (tf-idf weight) — only for kept entities
    mentions_edges = [
        (d, e, w) for d, e, w in _tfidf_edges(entities, mentions, documents)
        if e in kept_entity_ids
    ]
    for d, e, w in mentions_edges:
        g.add_edge(d, e, edge_type="mentions", weight=w)

    # about edges: top-k Topic entities per document by mentions weight
    class_by_entity = {e["entity_id"]: e["class_"] for e in entities}
    per_doc: dict[str, list[tuple[str, float]]] = {}
    for d, e, w in mentions_edges:
        if class_by_entity.get(e) == "Topic":
            per_doc.setdefault(d, []).append((e, w))
    for doc_id, pairs in per_doc.items():
        pairs.sort(key=lambda x: x[1], reverse=True)
        for e, w in pairs[:top_k_topics]:
            g.add_edge(doc_id, e, edge_type="about", weight=w)

    # co-occurs edges (PMI)
    for a, b, pmi in _pmi_edges(mentions, kept_entity_ids):
        g.add_edge(a, b, edge_type="co-occurs", weight=pmi)

    # cites + same-as: v3 hooks — no work needed for BNM-only v1 corpus.
    # In v3 we'd:
    #   - cites: emit Document → Document when a Reference entity's canonical
    #     matches a Document's title/doc_id.
    #   - same-as: emit Reference-entity → Document when both exist.

    return g


def _graph_to_json(g: nx.MultiDiGraph) -> dict:
    """Serialise the graph as a plain dict (nodes + edges lists) for the
    readable JSON artifact. GraphML is the portable format.
    """
    return {
        "nodes": [{"id": n, **g.nodes[n]} for n in g.nodes],
        "edges": [
            {"source": u, "target": v, **d}
            for u, v, d in g.edges(data=True)
        ],
    }


def run_stage_5(
    entities_path: Path = DATA_DIR / "entities.jsonl",
    mentions_path: Path = DATA_DIR / "mentions.jsonl",
    output_dir: Path = DATA_DIR,
    documents: Optional[dict[str, DocumentEntry]] = None,
) -> tuple[Path, Path]:
    """Read entities + mentions, build the graph, write graphml + json."""
    if documents is None:
        documents = DOCUMENTS

    entities = [json.loads(line) for line in entities_path.read_text().splitlines() if line.strip()]
    mentions = [json.loads(line) for line in mentions_path.read_text().splitlines() if line.strip()]

    g = build_graph(entities, mentions, documents)

    output_dir.mkdir(parents=True, exist_ok=True)
    graphml_path = output_dir / "graph.graphml"
    json_path = output_dir / "graph.json"

    nx.write_graphml(g, graphml_path)
    json_path.write_text(json.dumps(_graph_to_json(g), indent=2))

    logger.info(
        "Stage 5: graph built (%d nodes, %d edges)",
        g.number_of_nodes(), g.number_of_edges(),
    )
    return graphml_path, json_path
