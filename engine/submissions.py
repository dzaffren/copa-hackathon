"""Sensitive bank submission ingest — isolated store, zero-residue.

Design (see docs/specs/rulebook-radar/spec-knowledge-graph-engine.md,
"Sequence — supervisor submission ingest (isolated)" and "Zero-residue
guarantee"): a supervisor's uploaded submission is converted with the *same*
stage-1 MarkItDown pipeline as the public corpus (`engine.ingest`), then held
under heavier governance — written **only** into the git-ignored
`data/submissions/` store, tagged `supervised-entity-confidential`, and never
written into `clause-index.json`, `graph.json`, or any tracked path.

Two invariants are load-bearing here:

1. **Reuse stage-1 conversion.** This module does not re-implement extraction;
   it calls `engine.ingest.ingest_document`, which uses MarkItDown and raises
   `UnreadableDocumentError` on empty/failed conversion. No naive extractor.

2. **Zero residue on every exit.** The upload is materialised into an
   explicitly-cleaned temp path so MarkItDown (which takes a file path) can
   read it; that temp file is removed in a `finally` block on *every* exit —
   success, unreadable-reject, or any error. On a reject path no submission
   bytes persist at all; a successful ingest keeps the file only under the
   submissions dir.

The role gate (`X-Role: supervisor`) and the MIME-type gate (PDF/DOCX only)
live in the API layer (Task 6), not here — this module accepts raw bytes plus
the original filename, the cleanest seam for the API to call after it has
enforced those gates.
"""

import json
import re
import tempfile
import uuid
from pathlib import Path
from typing import Callable, Optional, TypedDict, Union

from engine.config import REPO_ROOT
from engine.ingest import ingest_document

# The single isolated, git-ignored store for sensitive submissions (see
# .gitignore: `data/submissions/`). Never a tracked/artifact path.
SUBMISSIONS_DIR = REPO_ROOT / "data" / "submissions"

SENSITIVITY = "supervised-entity-confidential"
INGESTED_FROM = "supervisor-upload"


class SubmissionRecord(TypedDict):
    submission_id: str
    source_filename: str
    text: str
    sensitivity: str
    ingested_from: str


def _submission_id_from_filename(source_filename: str) -> str:
    """Derive a stable-ish, human-readable submission id from a filename.

    Slugs the filename stem so a re-upload of the same file is stably keyed
    (helpful for deterministic tests); falls back to a uuid when the stem
    slugs to nothing.
    """
    stem = Path(source_filename).stem
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    if not slug:
        slug = uuid.uuid4().hex
    return f"sub-{slug}"


def ingest_submission(
    data: bytes,
    source_filename: str,
    submissions_dir: Union[str, Path] = SUBMISSIONS_DIR,
    submission_id: Optional[str] = None,
    converter: Callable[[Path], str] = ingest_document,
    temp_dir: Optional[Union[str, Path]] = None,
) -> SubmissionRecord:
    """Ingest a bank submission into the isolated, git-ignored store.

    Converts `data` with the stage-1 pipeline (`converter`, default the
    MarkItDown `ingest_document`) and, on success, writes a submission record
    as JSON under `submissions_dir` keyed by `submission_id`.

    Args:
        data: raw uploaded file bytes (the API layer supplies these after its
            role + MIME gates).
        source_filename: the uploaded file's original name (recorded verbatim).
        submissions_dir: the isolated store; injectable so tests write to a
            tmp dir. Defaults to `data/submissions/` under the repo root.
        submission_id: optional explicit id; when omitted it is derived
            deterministically from `source_filename` (stable for tests).
        converter: the stage-1 conversion seam; default `ingest_document`.
            Injectable so tests stub the MarkItDown/IO seam.
        temp_dir: where the upload is briefly materialised for conversion;
            injectable so a test can assert zero residue there afterward.

    Returns:
        The written `SubmissionRecord`.

    Raises:
        UnreadableDocumentError: propagated from the converter when the upload
            yields no usable text. Nothing is written and no bytes persist —
            the temp file is purged in the `finally` block.
    """
    submissions_dir = Path(submissions_dir)
    if submission_id is None:
        submission_id = _submission_id_from_filename(source_filename)

    suffix = Path(source_filename).suffix
    temp_dir_path = Path(temp_dir) if temp_dir is not None else None
    if temp_dir_path is not None:
        temp_dir_path.mkdir(parents=True, exist_ok=True)

    # Materialise the upload into an explicitly-cleaned temp path so the
    # path-based stage-1 converter can read it. The path is tracked so the
    # `finally` block can purge it on *every* exit — see the module docstring's
    # zero-residue invariant.
    fd, temp_name = tempfile.mkstemp(
        suffix=suffix, dir=temp_dir_path
    )
    temp_path = Path(temp_name)
    try:
        with open(fd, "wb") as handle:
            handle.write(data)

        # Reuse stage-1 conversion; raises UnreadableDocumentError on empty
        # output — propagated so the API maps it to 422 UNREADABLE_DOCUMENT.
        # Nothing is written before this line, so a reject persists zero bytes.
        text = converter(temp_path)

        record: SubmissionRecord = {
            "submission_id": submission_id,
            "source_filename": source_filename,
            "text": text,
            "sensitivity": SENSITIVITY,
            "ingested_from": INGESTED_FROM,
        }

        submissions_dir.mkdir(parents=True, exist_ok=True)
        (submissions_dir / f"{submission_id}.json").write_text(
            json.dumps(record, indent=2)
        )
        return record
    finally:
        # Zero-residue: purge the temp copy on every exit (success, reject,
        # or any error). The only surviving copy of the submission is the
        # record under `submissions_dir`, and only on the success path.
        temp_path.unlink(missing_ok=True)
