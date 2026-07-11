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
# # 01 — Explore the corpus
#
# Token counts, per-doc length, doc-type mix. Run after `python -m pipeline.run --stage=1`.

# %%
from pathlib import Path

import pandas as pd

from pipeline.config import DATA_DIR
from pipeline.corpus import DOCUMENTS

# %%
rows = []
for doc_id, entry in DOCUMENTS.items():
    md_path = DATA_DIR / "text" / f"{doc_id}.md"
    if md_path.exists():
        text = md_path.read_text()
        rows.append({
            "doc_id": doc_id,
            "title": entry["title"],
            "doc_type": entry["doc_type"],
            "chars": len(text),
            "words": len(text.split()),
        })
df = pd.DataFrame(rows).sort_values("chars", ascending=False)
df
