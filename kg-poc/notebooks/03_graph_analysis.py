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

# %%
import json

import networkx as nx

from pipeline.analyze import (
    doc_similarity_jaccard,
    entity_centrality,
    per_doc_top_entities,
)
from pipeline.config import DATA_DIR

# %%
