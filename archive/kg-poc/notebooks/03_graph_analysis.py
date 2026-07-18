# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
# ---

# %% [markdown]
# # 03 — Graph analysis
#
# Load the graph, compute centrality, similarity, open the HTML viz.
# Run after `uv run python -m pipeline.run --stage=all`.

# %%
import networkx as nx

from pipeline.analyze import (
    doc_similarity_jaccard,
    entity_centrality,
    per_doc_top_entities,
)
from pipeline.config import DATA_DIR

# %%
g = nx.read_graphml(DATA_DIR / "graph.graphml")
if not isinstance(g, nx.MultiDiGraph):
    g = nx.MultiDiGraph(g)
print(f"nodes: {g.number_of_nodes()}, edges: {g.number_of_edges()}")

# %% [markdown]
# ## Top entities per document

# %%
for d in sorted([n for n, data in g.nodes(data=True) if data.get("node_type") == "Document"]):
    print(f"\n### {d}")
    for e, w in per_doc_top_entities(g, d, k=10):
        print(f"  {w:6.2f}  {e}")

# %% [markdown]
# ## Doc-pair Jaccard similarity

# %%
for a, b, s in sorted(doc_similarity_jaccard(g), key=lambda x: x[2], reverse=True):
    print(f"  {s:.3f}  {a} ~ {b}")

# %% [markdown]
# ## Top entity centrality (PageRank)

# %%
c = entity_centrality(g)
for e, s in sorted(c.items(), key=lambda x: x[1]["pagerank"], reverse=True)[:30]:
    print(f"  pr={s['pagerank']:.4f} deg={s['degree']:.0f}  {e}")
