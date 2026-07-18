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
# # 02 — Ontology coverage
#
# Spans per class, per doc. Run after `python -m pipeline.run --stage=3`.

# %%
import json
from collections import Counter

import pandas as pd

from pipeline.config import DATA_DIR

# %%
spans = [json.loads(l) for l in (DATA_DIR / "spans.jsonl").read_text().splitlines() if l.strip()]
print(f"total spans: {len(spans)}")

# %%
class_counts = Counter(s["class_"] for s in spans)
class_counts

# %%
by_doc_class = Counter((s["doc_id"], s["class_"]) for s in spans)
pd.DataFrame(
    [{"doc_id": k[0], "class": k[1], "count": v} for k, v in by_doc_class.items()]
).pivot_table(index="doc_id", columns="class", values="count", fill_value=0)

# %%
source_counts = Counter(s["source"] for s in spans)
source_counts

# %% [markdown]
# ### Dropped spans (below GLINER threshold)
# %%
dropped = [json.loads(l) for l in (DATA_DIR / "spans_dropped.jsonl").read_text().splitlines() if l.strip()]
print(f"dropped spans: {len(dropped)}")
Counter(s["class_"] for s in dropped)
