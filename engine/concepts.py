"""Per-node concept metadata (the Node Detail panel's Concepts disclosure).

The node-detail route has always rendered a "Concepts" section with a fixed
placeholder — `{"status": "placeholder", "message": "Concept extraction not
enabled in MVP1"}` — because nothing populated it. This module is the read
side of the fix: a per-node side-file, written offline by
`scripts/enrich_node_metadata.py`, mirroring the `findings/{edge_id}.json`
convention (`engine/findings.py`) so `graph.json` diffs stay small and
reviewable.

Absence is the common, expected case — most nodes have not been enriched, and
that is not an error. `load_concepts` returns `None` in that case, and the
caller falls back to the placeholder exactly like an unanalysed edge falls
back to "not analysed" rather than erroring (`findings.FindingsNotAnalysedError`).

Every field here is either a verbatim quote from a clause the node's own
document contains, or a value already carried structurally on the node
(`owner`) — never invented. A field the enrichment script could not honestly
derive is `null`, not guessed.
"""

import json
from pathlib import Path
from typing import Any, Optional

# The regulatory-profile concept fields. The first seven are the original set;
# `legal_basis` and `ismp_classification` were added for Cross-Workstream
# Intelligence, where a *shared* Act or classification is one of the strongest
# early signals that two workstreams overlap. Both are additive — a node whose
# side-file omits them still loads (missing keys read back as `None`).
#
# Honesty rules (unchanged): every populated value is either a verbatim clause
# quote from the node's own document (`empowerment_framework`), a value already
# carried structurally on the node (`policy_owner`, `issuance_date`), or a
# structured reference already documented elsewhere in the corpus
# (`legal_basis` — the same kind of value `pursuant_to` already holds on a
# node). A field that cannot be honestly derived is `null`, not guessed.
# `ismp_classification` in particular has NO offline source (its authority is
# CAS's RH publication form, which the repo does not hold) and is therefore
# `null` everywhere today — the field exists so the UI can render "pending"
# rather than hide the concept.
CONCEPT_FIELDS: tuple[str, ...] = (
    "policy_owner",
    "applicability",
    "empowerment_framework",
    "requirement",
    "issuance_date",
    "effective_date",
    "keywords",
    "legal_basis",
    "ismp_classification",
)


def concepts_path(workstreams_dir: Path, workstream_id: str, node_id: str) -> Path:
    return workstreams_dir / workstream_id / "concepts" / f"{node_id}.json"


def load_concepts(
    workstreams_dir: Path, workstream_id: str, node_id: str
) -> Optional[dict[str, Any]]:
    """The enriched concept fields for a node, or `None` when not yet enriched."""
    path = concepts_path(workstreams_dir, workstream_id, node_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_concepts(
    workstreams_dir: Path,
    workstream_id: str,
    node_id: str,
    fields: dict[str, Any],
) -> None:
    """Persist a node's concept fields. UTF-8 always (clause text carries
    Unicode — §, en-dashes — that the Windows platform default cannot write).
    """
    path = concepts_path(workstreams_dir, workstream_id, node_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {field: fields.get(field) for field in CONCEPT_FIELDS}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
