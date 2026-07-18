"""Package-wide constants — MECE-7 classes, thresholds, paths.

No pipeline logic in this module. Everything here is a value; every
threshold is a load-bearing knob captured in one place so audit-driven
retuning changes only one file.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
ONTOLOGY_DIR = PACKAGE_ROOT / "ontology"

# The seven ontology classes in decision-cascade order (see spec §4).
MECE_7_CLASSES: tuple[str, ...] = (
    "RegulatoryBody",
    "Party",
    "Reference",
    "Instrument",
    "Requirement",
    "Topic",
    "Process",
)

# GLiNER confidence below this → dropped to spans_dropped.jsonl, never kept.
GLINER_CONFIDENCE_THRESHOLD: float = 0.7

# Entities with fewer mentions are excluded from the graph (kept in
# entities.jsonl).
MENTION_COUNT_MIN: int = 2

# Chunk length above this triggers a warning — probable sentencizer miss.
CHUNK_LEN_WARN: int = 500
