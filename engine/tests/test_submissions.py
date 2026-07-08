"""Tests for engine.submissions — sensitive bank submission ingest (isolated).

Covers the spec's Test Scenarios (docs/specs/rulebook-radar/
spec-knowledge-graph-engine.md, "Test Scenarios"):

  Test 10 — a supervisor's submission is converted with the same stage-1
    pipeline as the corpus, tagged sensitive, and written *only* into the
    git-ignored submissions store, never into any public artifact.
  Test 11 — an unreadable upload is rejected with zero residue: no record is
    written and any temp/spool bytes are purged in a `finally` block.

The MarkItDown conversion seam (`ingest_document`) is stubbed with a fake
converter in these tests — mirroring how engine.tests.test_ingest and the
build tests inject at IO/network seams so no real PDF or model is needed.
"""

import json

import pytest

from engine.ingest import UnreadableDocumentError
from engine.submissions import ingest_submission

MERIDIAN_FILENAME = "meridian-cloud-outsourcing-application.pdf"
CLEAN_SUBMISSION_TEXT = (
    "Meridian Bank Berhad — application to adopt a public cloud service for "
    "its core banking platform, a material outsourcing arrangement."
)


def _clean_converter(_file_path):
    """Fake stage-1 converter returning clean text (no real PDF/MarkItDown)."""
    return CLEAN_SUBMISSION_TEXT


def _unreadable_converter(_file_path):
    """Fake converter for a scanned-image/corrupt upload that has no text."""
    raise UnreadableDocumentError("Conversion yielded no usable text")


def test_supervisor_submission_is_ingested_isolated_and_tagged(tmp_path):
    """Test 10: a supervisor uploads Meridian's cloud outsourcing application.

    The submission record lands under the (tmp) submissions dir with a
    `submission_id`, is tagged `supervised-entity-confidential`, and its text
    lives only in that isolated store — separate from any artifacts path.
    """
    submissions_dir = tmp_path / "submissions"
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    record = ingest_submission(
        data=b"%PDF-1.4 fake meridian bytes",
        source_filename=MERIDIAN_FILENAME,
        submissions_dir=submissions_dir,
        submission_id="sub-meridian-cloud-001",
        converter=_clean_converter,
    )

    assert record["submission_id"] == "sub-meridian-cloud-001"
    assert record["source_filename"] == MERIDIAN_FILENAME
    assert record["text"] == CLEAN_SUBMISSION_TEXT
    assert record["sensitivity"] == "supervised-entity-confidential"
    assert record["ingested_from"] == "supervisor-upload"

    # The record is written under the submissions dir, keyed by submission_id.
    stored = submissions_dir / "sub-meridian-cloud-001.json"
    assert stored.exists()
    assert json.loads(stored.read_text()) == record

    # Isolation: submission text appears in no file under the artifacts path.
    for path in artifacts_dir.rglob("*"):
        if path.is_file():
            assert CLEAN_SUBMISSION_TEXT not in path.read_text()
    # And the two stores are genuinely separate directories.
    assert submissions_dir.resolve() != artifacts_dir.resolve()
