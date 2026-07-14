"""Serialise the engine's built artifacts into the Next.js app's static snapshot.

Spec: docs/specs/reconciliation-workbench/spec-upload-and-workspace.md → "API Design"
(New (owned here): the static snapshot exporter). The deployed frontend
(`web/`) reads a bundled JSON snapshot from `web/public/data/` by default, so the
demo runs with no backend. This script produces that snapshot from the immutable
build artifacts, mirroring the engine read-API response shapes byte-for-byte:

    reads  data/artifacts/{clause-index,graph,verdicts}.json
    writes web/public/data/paragraphs.json
           web/public/data/connections/{number}.json   (one per analysed paragraph)
    skips  any graph node with access == "restricted"   (confidentiality hard rule)

The exporter is intentionally thin and deterministic — no network, no model. The
render/join logic (public-node filtering, verbatim-quote join, connection
rendering, and the per-paragraph / paragraphs-index payloads) now lives in
`engine.read_model`, which the read API (`engine.api`) ALSO uses — so the static
snapshot and the live API can never diverge. This script is a thin writer around
that shared model: it loads the three artifacts, delegates to `engine.read_model`,
and writes the JSON files.

Because the AI DP's real verdict artifacts are produced by the engine story
(spec-source-connection-engine.md, Tasks 4-6) and may not exist yet, this script
tolerates missing/empty artifacts and simply writes an empty snapshot — it never
fabricates a connection. Until the engine emits them, the committed demo snapshot
under web/public/data/ is the curated prepared analysis the demo uses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.clauses import ClauseIndex
from engine.read_model import (
    render_paragraph_connections,
    render_paragraphs_index,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "data" / "artifacts"
SNAPSHOT_DIR = REPO_ROOT / "web" / "public" / "data"

# The one demo vehicle (working id; see engine spec open question on the final id).
DEFAULT_DOCUMENT_ID = "ai-dp-2025"


def _load(path: Path, default: Any) -> Any:
    """Load a JSON artifact, tolerating its absence (fresh checkout / pre-engine)."""
    if not path.exists():
        return default
    return json.loads(path.read_text())


def build_snapshot(
    clause_index: dict[str, Any],
    graph: dict[str, Any],
    verdicts: dict[str, Any],
    document_id: str = DEFAULT_DOCUMENT_ID,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Pure builder → (paragraphs.json payload, {paragraph_number: connections.json}).

    Delegates entirely to `engine.read_model` so the snapshot mirrors the live
    read API byte-for-byte. `clause_index` arrives as a raw JSON dict (the loaded
    `clause-index.json`); it is wrapped in a `ClauseIndex` (dropping any non-dict
    value, preserving the old tolerance) so the shared render model — which reads
    the index through `ClauseIndex` — can consume it. Kept side-effect-free so
    tests can assert on the shapes without touching disk.
    """
    index = (
        clause_index
        if isinstance(clause_index, ClauseIndex)
        else ClauseIndex(
            {k: v for k, v in clause_index.items() if isinstance(v, dict)}
        )
    )

    paragraphs_payload = render_paragraphs_index(document_id, index, verdicts, graph)

    # One connections file per ANALYSED paragraph — the same payload the live
    # `GET …/{number}/connections` route serves (via the same render model).
    connections_files: dict[str, dict[str, Any]] = {}
    for paragraph in paragraphs_payload["paragraphs"]:
        if paragraph["state"] != "analysed":
            continue
        payload = render_paragraph_connections(
            document_id, paragraph["number"], verdicts, graph, index
        )
        if payload is not None:  # analysed paragraphs always resolve their entry
            connections_files[paragraph["number"]] = payload

    return paragraphs_payload, connections_files


class EmptySnapshotError(RuntimeError):
    """Refusing to overwrite an existing non-empty snapshot with an empty one."""


def _existing_is_nonempty(snapshot_dir: Path) -> bool:
    """True if a committed snapshot with real paragraphs already lives here."""
    existing = snapshot_dir / "paragraphs.json"
    if not existing.exists():
        return False
    try:
        return bool(json.loads(existing.read_text()).get("paragraphs"))
    except (ValueError, OSError):
        return False


def export(
    artifacts_dir: Path = ARTIFACTS_DIR,
    snapshot_dir: Path = SNAPSHOT_DIR,
    document_id: str = DEFAULT_DOCUMENT_ID,
    force: bool = False,
) -> dict[str, Any]:
    """Read artifacts, build the snapshot, and write it under `snapshot_dir`.

    Safety: if the build would produce an EMPTY snapshot (e.g. the engine has
    not yet emitted `verdicts.json`) but a non-empty snapshot is already
    committed — the hand-authored demo data — refuse rather than clobber it,
    unless `force=True`. This stops a premature run from wiping the demo.
    """
    clause_index = _load(artifacts_dir / "clause-index.json", {})
    graph = _load(artifacts_dir / "graph.json", {"nodes": [], "edges": []})
    verdicts = _load(artifacts_dir / "verdicts.json", {})

    paragraphs_payload, connections_files = build_snapshot(
        clause_index, graph, verdicts, document_id
    )

    if (
        not force
        and not paragraphs_payload["paragraphs"]
        and _existing_is_nonempty(snapshot_dir)
    ):
        raise EmptySnapshotError(
            f"Build produced an empty snapshot but {snapshot_dir} already holds a "
            f"non-empty one (likely the hand-authored demo data). The engine's "
            f"verdicts.json is probably not built yet. Re-run with force=True to "
            f"overwrite anyway."
        )

    (snapshot_dir / "connections").mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "paragraphs.json").write_text(
        json.dumps(paragraphs_payload, indent=2, ensure_ascii=False) + "\n"
    )
    for number, payload in connections_files.items():
        (snapshot_dir / "connections" / f"{number}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        )

    return paragraphs_payload


if __name__ == "__main__":  # pragma: no cover
    import sys

    force = "--force" in sys.argv[1:]
    try:
        result = export(force=force)
    except EmptySnapshotError as exc:
        print(f"Skipped: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(
        f"Wrote snapshot for {result['document_id']}: "
        f"{result['total_paragraphs']} paragraphs → {SNAPSHOT_DIR}"
    )
