"""FastAPI read service over the built artifacts (spec Task 6 / "API Design").

Design (see docs/specs/rulebook-radar/spec-knowledge-graph-engine.md, "API
Design" and "System architecture"): a thin, read-only HTTP service over the
two immutable build artifacts (`clause-index.json`, `graph.json`) plus the
pairwise connection-finder and the isolated submission store. It serves every
consuming story (#7-#11); it needs **no** model access (that is build-time
only) and holds the graph in memory (the corpus is tiny).

The service is constructed by `create_app(...)`, a factory that takes every
external dependency as an injectable argument — the loaded `ClauseIndex`, the
graph dict, the submissions dir, the finder/critic seams, the trace output
dir, and the submission converter. This is the testable seam: tests build an
app against hand-made fixtures with no network, no credentials, and no real
artifacts on disk (see engine/tests/test_api.py). A module-level `app` for
`uvicorn engine.api:app` lazily loads the real artifacts from
`data/artifacts/`, tolerating their absence in a fresh checkout.

Confidentiality (hard rule): the clause/graph/node/connection routes are
public (all derived from public BNM documents); the two submission routes are
role-gated (`X-Role: supervisor`) and touch only the git-ignored submissions
store — no submission text ever reaches the public artifacts.
"""

import json
from pathlib import Path
from typing import Any, Callable, Optional, Union
from urllib.parse import unquote

from fastapi import FastAPI, Header, Request, UploadFile
from fastapi.responses import JSONResponse

from engine.clauses import (
    ClauseEntry,
    ClauseIndex,
    ClauseVersionNotFoundError,
)
from engine.connections import CriticFn, FinderFn, find_connections
from engine.ingest import UnreadableDocumentError, ingest_document
from engine.submissions import SUBMISSIONS_DIR, ingest_submission

# Supported submission upload MIME types (spec Permissions & Security / API
# Design): PDF and DOCX only; anything else is 415 UNSUPPORTED_FORMAT.
_PDF_MIME = "application/pdf"
_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_SUPPORTED_SUBMISSION_MIMES = {_PDF_MIME, _DOCX_MIME}

# The public-facing clause-index fields (the frozen contract) — the private
# `_full_text` slice used to compose a parent's view is never exposed; the
# composed view is returned under `full_text` instead.
_CLAUSE_PUBLIC_FIELDS = (
    "clause_number",
    "text",
    "policy_id",
    "document_id",
    "source",
    "heading",
    "parent",
    "children",
    "superseded_versions",
)


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    """Build the spec's uniform error body `{error, message}` at `status_code`."""
    return JSONResponse(
        status_code=status_code, content={"error": code, "message": message}
    )


def _public_clause(entry: ClauseEntry, full_text: Optional[str]) -> dict[str, Any]:
    """Project a `ClauseEntry` onto the public API shape.

    Drops the private `_full_text` field and, for a parent with children, adds
    the composed `full_text` (spec `GET /clauses/{n}` 200 shapes). A leaf/
    sub-item (no children) never carries `full_text`.
    """
    body: dict[str, Any] = {
        field: entry[field]  # type: ignore[literal-required]
        for field in _CLAUSE_PUBLIC_FIELDS
        if field in entry
    }
    if entry.get("children") and full_text is not None:
        body["full_text"] = full_text
    return body


def create_app(
    clause_index: ClauseIndex,
    graph: dict[str, Any],
    submissions_dir: Union[str, Path] = SUBMISSIONS_DIR,
    finder_fn: Optional[FinderFn] = None,
    critic_fn: Optional[CriticFn] = None,
    trace_output_dir: Optional[Path] = None,
    submission_converter: Callable[[Path], str] = ingest_document,
) -> FastAPI:
    """Construct the read API against injected dependencies.

    Args:
        clause_index: the loaded `ClauseIndex` (verbatim clause lookup).
        graph: the loaded `graph.json` dict (`{"nodes": [...], "edges": [...]}`).
        submissions_dir: the isolated, git-ignored submission store; injectable
            so tests point it at a tmp dir.
        finder_fn / critic_fn: the stage-4 agent seams passed straight through
            to `engine.connections.find_connections`. Left `None` in the real
            app (the defaults call Azure at request time — the ripple story #8
            supplies credentials); tests inject stubs so no network is touched.
        trace_output_dir: where `find_connections` writes its
            `connection-trace-*.json`; tests pass a tmp dir so nothing lands in
            the tracked `data/artifacts/`.
        submission_converter: the stage-1 conversion seam for submission
            ingest; default `ingest_document` (MarkItDown). Tests stub it.

    Returns:
        A configured `FastAPI` app. No network or credentials are required to
        build it — the model seams are only exercised on `POST /connections/find`
        and only with whatever `finder_fn`/`critic_fn` are supplied.
    """
    app = FastAPI(title="Rulebook Radar — read API")

    submissions_dir = Path(submissions_dir)
    known_document_ids = {node["id"] for node in graph.get("nodes", [])}

    @app.get("/clauses/{clause_number:path}")
    def get_clause(clause_number: str, version: Optional[str] = None) -> Any:
        # `clause_number` arrives URL-encoded (e.g. "Outsourcing%2012.1");
        # Starlette decodes path params, but decode defensively for `:path`.
        clause_number = unquote(clause_number)
        try:
            entry = clause_index.get(clause_number, version=version)
        except ClauseVersionNotFoundError:
            return _error(
                404,
                "CLAUSE_VERSION_NOT_FOUND",
                f"No version '{version}' for clause '{clause_number}'",
            )

        if entry is None:
            return _error(
                404,
                "CLAUSE_NOT_FOUND",
                f"No matching clause found for '{clause_number}'",
            )

        full_text = clause_index.full_text(clause_number, version=version)
        return _public_clause(entry, full_text)

    @app.get("/graph")
    def get_graph() -> Any:
        return graph

    @app.get("/nodes/{node_id}")
    def get_node(node_id: str) -> Any:
        matches = [n for n in graph.get("nodes", []) if n["id"] == node_id]
        if not matches:
            return _error(
                404, "NODE_NOT_FOUND", f"No node with id '{node_id}'"
            )
        node = matches[0]
        incident = [
            {"target": e["target"], "type": e["type"], "reason": e["reason"]}
            for e in graph.get("edges", [])
            if e["source"] == node_id
        ]
        return {
            "id": node["id"],
            "title": node["title"],
            "status": node["status"],
            "edges": incident,
        }

    @app.post("/connections/find")
    async def post_connections_find(request: Request) -> Any:
        body = await request.json()
        document_ids = body.get("document_ids") if isinstance(body, dict) else None

        if not isinstance(document_ids, list) or len(document_ids) != 2:
            return _error(
                400,
                "INVALID_DOCUMENT_IDS",
                "document_ids must contain exactly two known document ids",
            )
        for document_id in document_ids:
            if document_id not in known_document_ids:
                return _error(
                    400,
                    "INVALID_DOCUMENT_IDS",
                    f"Unknown document id '{document_id}'",
                )

        doc_a, doc_b = document_ids
        result = find_connections(
            doc_a,
            doc_b,
            clause_index,
            finder_fn=finder_fn,
            critic_fn=critic_fn,
            output_dir=trace_output_dir,
        )
        return result

    @app.post("/submissions")
    async def post_submission(
        file: UploadFile, x_role: Optional[str] = Header(default=None)
    ) -> Any:
        # CRITICAL ORDER: role FIRST (403), then MIME (415), then ingest (422).
        # No submission bytes are spooled before the authorised+valid-MIME
        # ingest, so the reject paths persist zero residue.
        if x_role != "supervisor":
            return _error(
                403,
                "SUBMISSION_ACCESS_DENIED",
                "Supervisor role required to ingest submissions",
            )
        if file.content_type not in _SUPPORTED_SUBMISSION_MIMES:
            return _error(
                415,
                "UNSUPPORTED_FORMAT",
                "Only PDF and DOCX submissions are supported",
            )

        data = await file.read()
        try:
            record = ingest_submission(
                data,
                file.filename or "submission",
                submissions_dir=submissions_dir,
                converter=submission_converter,
            )
        except UnreadableDocumentError:
            return _error(
                422,
                "UNREADABLE_DOCUMENT",
                "The document could not be read; no text was stored",
            )
        return JSONResponse(
            status_code=201,
            content={
                "submission_id": record["submission_id"],
                "sensitivity": record["sensitivity"],
            },
        )

    @app.get("/submissions/{submission_id}")
    def get_submission(
        submission_id: str, x_role: Optional[str] = Header(default=None)
    ) -> Any:
        if x_role != "supervisor":
            return _error(
                403,
                "SUBMISSION_ACCESS_DENIED",
                "Supervisor role required to ingest submissions",
            )
        record_path = submissions_dir / f"{submission_id}.json"
        if not record_path.exists():
            return _error(
                404,
                "SUBMISSION_NOT_FOUND",
                f"No submission with id '{submission_id}'",
            )
        return json.loads(record_path.read_text())

    return app


def _load_clause_index(artifacts_dir: Path) -> ClauseIndex:
    """Load `clause-index.json` (the primary index) into a `ClauseIndex`.

    Tolerates a missing artifact in a fresh checkout — returns an empty index
    so the app still starts (the endpoints then report `CLAUSE_NOT_FOUND` for
    everything, rather than crashing at import/startup).
    """
    path = artifacts_dir / "clause-index.json"
    if not path.exists():
        return ClauseIndex({})
    primary: dict[str, ClauseEntry] = json.loads(path.read_text())
    return ClauseIndex(primary)


def _load_graph(artifacts_dir: Path) -> dict[str, Any]:
    """Load `graph.json`, tolerating its absence in a fresh checkout."""
    path = artifacts_dir / "graph.json"
    if not path.exists():
        return {"nodes": [], "edges": []}
    return json.loads(path.read_text())


def _build_default_app() -> FastAPI:
    """Lazily construct the real app from `data/artifacts/` for uvicorn.

    Never fails at import if the artifacts are absent — loads an empty index /
    graph instead, so `uvicorn engine.api:app` starts on a fresh checkout.
    """
    from engine.config import REPO_ROOT

    artifacts_dir = REPO_ROOT / "data" / "artifacts"
    return create_app(
        clause_index=_load_clause_index(artifacts_dir),
        graph=_load_graph(artifacts_dir),
    )


app = _build_default_app()
