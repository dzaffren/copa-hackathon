"""Tests for scripts/export_poc_snapshot.py — the static snapshot exporter.

Spec: docs/specs/reconciliation-workbench/spec-upload-and-workspace.md → "Test
Scenarios" (Test 1: snapshot exporter mirrors the API shape and skips restricted
nodes). No network, no real artifacts: everything is hand-built fixtures written
into a tmp artifacts dir, mirroring engine/tests/test_build.py's tmp_path style.
"""

import json

import pytest

from scripts.export_poc_snapshot import EmptySnapshotError, build_snapshot, export

DOCUMENT_ID = "ai-dp-2025"

# clause-index entries: the DP's two showcase paragraphs + the verbatim reference
# passages the quotes are fetched from (quote text NEVER comes from the verdict record).
CLAUSE_INDEX = {
    "ai-dp-2025 3.5": {
        "clause_number": "ai-dp-2025 3.5",
        "document_id": DOCUMENT_ID,
        "heading": "Fair usage & bias",
        "text": "A major challenge of AI is the risk of unfair bias...",
    },
    "ai-dp-2025 3.2": {
        "clause_number": "ai-dp-2025 3.2",
        "document_id": DOCUMENT_ID,
        "heading": "Board & senior management oversight",
        "text": "The board and senior management...",
    },
    "OECD 1.2": {
        "clause_number": "OECD 1.2",
        "document_id": "oecd-ai",
        "text": (
            "AI actors should implement mechanisms and safeguards, such as capacity "
            "for human agency and oversight, including to address risks arising from "
            "uses outside of intended purpose."
        ),
    },
}

# graph nodes: one PUBLIC reference (OECD) and one RESTRICTED handbook that must
# never appear in the snapshot — neither its title nor any derived text.
GRAPH = {
    "nodes": [
        {
            "id": "oecd-ai",
            "title": "OECD AI Principles",
            "source_type": "international_standard",
            "access": "public",
        },
        {
            "id": "bnm-handbook",
            "title": "CONFIDENTIAL — internal supervisory handbook",
            "source_type": "internal_bnm",
            "access": "restricted",
        },
    ],
    "edges": [],
}

# verdicts.json: a Consensus on 3.5 citing the OECD passage (verified), plus a
# connection whose source is the restricted handbook (must be dropped).
VERDICTS = {
    "ai-dp-2025:3.5::oecd:OECD 1.2": {
        "id": "ai-dp-2025:3.5::oecd:OECD 1.2",
        "paragraph": "3.5",
        "branch": "cited",
        "source_document_id": "oecd-ai",
        "verdict": "Consensus",
        "confidence": "High",
        "rationale": "OECD backs the fairness stance and adds a human-agency mechanism 3.5 omits.",
        "clause_number": "OECD 1.2",
        "verification": "verified",
    },
    "ai-dp-2025:3.5::handbook:HB 1": {
        "id": "ai-dp-2025:3.5::handbook:HB 1",
        "paragraph": "3.5",
        "branch": "uncited",
        "source_document_id": "bnm-handbook",
        "verdict": "Duplicate",
        "confidence": "Low",
        "rationale": "internal position",
        "clause_number": "HB 1",
        "verification": "illustrative",
    },
}


def test_build_snapshot_mirrors_api_shape_and_skips_restricted_nodes():
    paragraphs, connections = build_snapshot(CLAUSE_INDEX, GRAPH, VERDICTS, DOCUMENT_ID)

    # Paragraphs payload shape.
    assert paragraphs["document_id"] == DOCUMENT_ID
    assert paragraphs["total_paragraphs"] == 2  # 3.5 (analysed) + 3.2 (not_analysed)
    by_number = {p["number"]: p for p in paragraphs["paragraphs"]}
    assert by_number["3.5"]["state"] == "analysed"
    assert by_number["3.2"]["state"] == "not_analysed"

    # 3.5 keeps the public OECD connection but DROPS the restricted-handbook one.
    conns = connections["3.5"]["connections"]
    assert len(conns) == 1
    assert by_number["3.5"]["connection_count"] == 1
    oecd = conns[0]
    assert oecd["source"]["document_id"] == "oecd-ai"
    assert oecd["verdict"] == "Consensus"
    assert oecd["verdict_status"] == "proposed"

    # Quote text is fetched verbatim from the clause index (not the verdict record),
    # and the verification marker passes through unchanged.
    assert oecd["quote"]["verification"] == "verified"
    assert oecd["quote"]["text"] == CLAUSE_INDEX["OECD 1.2"]["text"]

    # The restricted node's title/text must not appear ANYWHERE in the snapshot.
    blob = json.dumps([paragraphs, connections])
    assert "CONFIDENTIAL" not in blob
    assert "bnm-handbook" not in blob
    assert "HB 1" not in blob


def test_pending_extraction_never_emits_text():
    verdicts = {
        "ai-dp-2025:5.2::basel:Basel RBC20": {
            "id": "ai-dp-2025:5.2::basel:Basel RBC20",
            "paragraph": "5.2",
            "branch": "uncited",
            "source_document_id": "oecd-ai",  # any public node
            "verdict": "Gap",
            "clause_number": "Basel RBC20",
            "verification": "pending_extraction",
        }
    }
    clause_index = {
        "ai-dp-2025 5.2": {
            "clause_number": "ai-dp-2025 5.2",
            "document_id": DOCUMENT_ID,
            "heading": "Capital treatment",
            "text": "...",
        }
    }
    _, connections = build_snapshot(clause_index, GRAPH, verdicts, DOCUMENT_ID)
    quote = connections["5.2"]["connections"][0]["quote"]
    assert quote["verification"] == "pending_extraction"
    assert quote["text"] is None  # never an approximated string


def test_blocked_source_has_no_verdict_or_quote():
    verdicts = {
        "ai-dp-2025:3.5::mas-feat": {
            "id": "ai-dp-2025:3.5::mas-feat",
            "paragraph": "3.5",
            "branch": "uncited",
            "source_document_id": "mas-feat",
            "status": "could_not_retrieve",
            "reason": "The MAS site blocks automated access; upload the source to analyse.",
        }
    }
    nodes = {"nodes": [{"id": "mas-feat", "title": "MAS — FEAT Principles", "source_type": "peer_regulator", "access": "public"}], "edges": []}
    clause_index = {"ai-dp-2025 3.5": {"clause_number": "ai-dp-2025 3.5", "document_id": DOCUMENT_ID, "heading": "Fair usage & bias", "text": "..."}}
    _, connections = build_snapshot(clause_index, nodes, verdicts, DOCUMENT_ID)
    conn = connections["3.5"]["connections"][0]
    assert conn["status"] == "could_not_retrieve"
    assert conn["verdict"] is None
    assert conn["quote"] is None


def test_export_writes_files_and_tolerates_missing_artifacts(tmp_path):
    # Empty artifacts dir → no fabrication, just an empty snapshot that still writes.
    snapshot_dir = tmp_path / "web" / "public" / "data"
    result = export(artifacts_dir=tmp_path / "nope", snapshot_dir=snapshot_dir, document_id=DOCUMENT_ID)
    assert result["total_paragraphs"] == 0
    written = json.loads((snapshot_dir / "paragraphs.json").read_text())
    assert written["paragraphs"] == []
    assert (snapshot_dir / "connections").is_dir()


def test_export_refuses_to_clobber_a_nonempty_snapshot_with_an_empty_one(tmp_path):
    # An existing hand-authored demo snapshot must not be wiped by a premature
    # run (engine's verdicts.json not built yet → empty build).
    snapshot_dir = tmp_path / "web" / "public" / "data"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "paragraphs.json").write_text(
        json.dumps({"document_id": DOCUMENT_ID, "total_paragraphs": 1, "paragraphs": [{"number": "3.5"}]})
    )

    with pytest.raises(EmptySnapshotError):
        export(artifacts_dir=tmp_path / "nope", snapshot_dir=snapshot_dir, document_id=DOCUMENT_ID)

    # The demo snapshot is untouched.
    assert json.loads((snapshot_dir / "paragraphs.json").read_text())["total_paragraphs"] == 1

    # force=True overrides the guard.
    export(artifacts_dir=tmp_path / "nope", snapshot_dir=snapshot_dir, document_id=DOCUMENT_ID, force=True)
    assert json.loads((snapshot_dir / "paragraphs.json").read_text())["paragraphs"] == []
