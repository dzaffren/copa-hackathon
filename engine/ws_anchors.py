"""Per-node anchor store (the chunked-document side-file).

Mirrors `engine/findings.py`: where findings live per-edge at
`findings/{edge_id}.json`, a chunked document's anchors live per-node at
`anchors/{node_id}.json` — a bare JSON list of `engine.anchors.Anchor`
records. Adding a document node segments its markdown once and writes the
result here; analysis later unions every node's anchors into one
`AnchorIndex` via `build_index`.

Absence means "not segmented yet" — `load` raises `AnchorsNotSegmentedError`
rather than returning `[]`, the same way `findings.load` distinguishes an
unanalysed edge from an analysed-but-empty one. The verbatim guarantee is
upstream: `engine.anchors.segment` verifies every anchor's `text` is a literal
substring of the source before it is ever handed here, so this module only
persists and reloads — it never slices or rewrites text.
"""

import json
from pathlib import Path
from typing import Union

from engine.anchors import Anchor, AnchorIndex


class AnchorsNotSegmentedError(Exception):
    """The node has no anchors file — its document has not been segmented yet."""


def anchors_path(
    workstreams_dir: Union[str, Path], workstream_id: str, node_id: str
) -> Path:
    return Path(workstreams_dir) / workstream_id / "anchors" / f"{node_id}.json"


def load(
    workstreams_dir: Union[str, Path], workstream_id: str, node_id: str
) -> list[Anchor]:
    """Read a node's anchors. Raises `AnchorsNotSegmentedError` when the file
    is absent — an un-segmented node is a different condition from a segmented
    one with zero anchors (which never persists; see the create-node route)."""
    path = anchors_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        raise AnchorsNotSegmentedError(node_id)
    return json.loads(path.read_text(encoding="utf-8"))


def save(
    workstreams_dir: Union[str, Path],
    workstream_id: str,
    node_id: str,
    anchors: list[Anchor],
) -> None:
    """Persist a node's anchors. UTF-8 always — anchor text carries Unicode
    (§, en-dashes, U+2212); the platform default mangles it on Windows."""
    path = anchors_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(anchors, indent=2, ensure_ascii=False), encoding="utf-8")


def build_index(workstreams_dir: Union[str, Path], workstream_id: str) -> AnchorIndex:
    """Union every `anchors/*.json` in the workstream into one `AnchorIndex`.

    Anchors are read in sorted filename order for a stable insertion order. A
    duplicate `anchor_id` across two nodes' files raises `ValueError` from
    `AnchorIndex.__init__` — a loud failure rather than silently dropping one.
    An absent `anchors/` dir yields an empty index.
    """
    anchors_dir = Path(workstreams_dir) / workstream_id / "anchors"
    all_anchors: list[Anchor] = []
    if anchors_dir.exists():
        for path in sorted(anchors_dir.glob("*.json")):
            all_anchors.extend(json.loads(path.read_text(encoding="utf-8")))
    return AnchorIndex(all_anchors)
