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

The exporter is intentionally thin and deterministic — no network, no model. It
joins three inputs:

  * verdicts.json  — per-connection records (verdict, rationale, confidence,
                     branch, verification, source ref, and blocked-source status).
                     This is the spine of a connection.
  * clause-index   — the ONLY source of verbatim quote text and paragraph text
                     (fetched by clause number; never model-authored).
  * graph nodes    — source metadata (title, source_type, access). A node marked
                     access == "restricted" is dropped entirely: neither its text
                     nor its title reaches the tracked snapshot path.

Because the AI DP's real verdict artifacts are produced by the engine story
(spec-source-connection-engine.md, Tasks 4-6) and may not exist yet, this script
tolerates missing/empty artifacts and simply writes an empty snapshot — it never
fabricates a connection. Until the engine emits them, the committed demo snapshot
under web/public/data/ is the curated prepared analysis the demo uses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

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


def _public_nodes(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index graph nodes by id, DROPPING any with access == "restricted".

    This is the confidentiality guarantee: a restricted node (e.g. the internal
    handbook) is excluded here, so neither its title nor any derived text can
    appear in the tracked snapshot. Preview nodes are kept (they are public) but
    carry no verbatim passage from the engine, so they simply never gain a quote.
    """
    return {
        node["id"]: node
        for node in graph.get("nodes", [])
        if node.get("access") != "restricted"
    }


def _quote_for(
    clause_number: Optional[str],
    verification: str,
    clause_index: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Build a quote block, fetching verbatim text from the clause index by number.

    Never returns model-authored text. `pending_extraction` yields text: null
    (a labelled placeholder downstream); a clause number absent from the index
    also yields null text rather than an invented string.
    """
    if clause_number is None:
        return None
    if verification == "pending_extraction":
        return {"clause_number": clause_number, "text": None, "verification": "pending_extraction"}
    entry = clause_index.get(clause_number)
    text = entry.get("text") if isinstance(entry, dict) else None
    return {"clause_number": clause_number, "text": text, "verification": verification}


def _connection_from_verdict(
    record: dict[str, Any],
    nodes: dict[str, dict[str, Any]],
    clause_index: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Turn one verdicts.json record into a read-API connection object.

    Returns None when the record's source node is restricted/absent (dropped),
    so restricted connections never surface.
    """
    source_id = record.get("source_document_id")
    node = nodes.get(source_id)
    if node is None:
        return None  # restricted (dropped from `nodes`) or unknown → omit entirely

    source: dict[str, Any] = {
        "document_id": source_id,
        "title": node.get("title", source_id),
        "source_type": node.get("source_type", "international_standard"),
    }
    if "stance" in record:
        source["stance"] = record["stance"]

    base = {"id": record["id"], "branch": record.get("branch", "uncited"), "source": source}

    # A blocked (un-retrieved) source: no verdict, no quote.
    if record.get("status") == "could_not_retrieve":
        return {
            **base,
            "status": "could_not_retrieve",
            "reason": record.get("reason", "This source could not be retrieved automatically."),
            "verdict": None,
            "quote": None,
        }

    return {
        **base,
        "verdict": record["verdict"],
        "verdict_status": "proposed",
        "confidence": record.get("confidence", "Medium"),
        "rationale": record.get("rationale", ""),
        "quote": _quote_for(
            record.get("clause_number"),
            record.get("verification", "illustrative"),
            clause_index,
        ),
    }


def build_snapshot(
    clause_index: dict[str, Any],
    graph: dict[str, Any],
    verdicts: dict[str, Any],
    document_id: str = DEFAULT_DOCUMENT_ID,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Pure builder → (paragraphs.json payload, {paragraph_number: connections.json}).

    Kept side-effect-free so tests can assert on the shapes without touching disk.
    """
    nodes = _public_nodes(graph)

    # Paragraphs of the vehicle document are clause-index entries for its policy.
    para_entries = {
        entry["clause_number"]: entry
        for entry in clause_index.values()
        if isinstance(entry, dict) and entry.get("document_id") == document_id
    }

    # Group verdict records by the paragraph they touch.
    by_paragraph: dict[str, list[dict[str, Any]]] = {}
    for record in verdicts.values():
        para = record.get("paragraph")
        if para is None:
            continue
        by_paragraph.setdefault(para, []).append(record)

    connections_files: dict[str, dict[str, Any]] = {}
    paragraphs: list[dict[str, Any]] = []

    for clause_number, entry in sorted(para_entries.items()):
        # A clause number like "AIDP 3.5" → the bare paragraph number "3.5".
        number = clause_number.split(" ", 1)[-1]
        title = entry.get("heading") or ""
        records = by_paragraph.get(number, [])

        conns = [
            c
            for c in (_connection_from_verdict(r, nodes, clause_index) for r in records)
            if c is not None
        ]
        state = "analysed" if number in by_paragraph else "not_analysed"

        paragraphs.append(
            {
                "number": number,
                "title": title,
                "text": entry.get("text", ""),
                "state": state,
                "connection_count": len(conns),
            }
        )

        if state == "analysed":
            connections_files[number] = {
                "paragraph": {"number": number, "title": title, "text": entry.get("text", "")},
                "state": "analysed",
                "no_matching_source": len(conns) == 0,
                "connections": conns,
            }

    paragraphs_payload = {
        "document_id": document_id,
        "total_paragraphs": len(paragraphs),
        "paragraphs": paragraphs,
    }
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
