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

from engine.anchors import Anchor, AnchorIndex
from engine.clauses import (
    POLICY_SHORT_NAMES,
    ClauseEntry,
    ClauseIndex,
    ClauseVersionNotFoundError,
)
from engine.connections import CriticFn, FinderFn, find_connections
from engine.ingest import UnreadableDocumentError, ingest_document
from engine.read_model import (
    paragraph_entry,
    public_nodes,
    render_connection,
    render_paragraph_connections,
    render_paragraphs_index,
)
from engine.submissions import SUBMISSIONS_DIR, ingest_submission
from engine.verdicts import VerdictFn, propose_verdicts

# The live two-branch analysis seam for `POST …/analyse`: given a document id, a
# paragraph number, the paragraph's verbatim text, and the clause index, it
# returns branch-tagged candidate specs (shaped like
# `engine.config.AI_DP_CONNECTIONS`) which the verdict stage then classifies.
# Real callers wire `engine.connections.analyse_paragraph` (which reaches the
# model at request time); tests inject a stub, so no network is touched. This is
# the ONE route that opts into a live model call — the rest of the API is
# model-free (served from the build artifacts held in memory).
AnalyseFn = Callable[[str, str, str, ClauseIndex], list[dict[str, Any]]]

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
    verdicts: Optional[dict[str, Any]] = None,
    analyse_fn: Optional[AnalyseFn] = None,
    verdict_fn: Optional[VerdictFn] = None,
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
        verdicts: the loaded `verdicts.json` dict (per-connection verdict
            records keyed by connection id) that the paragraph routes join onto
            the graph + clause index at read time. Defaults to `{}` (a fresh
            checkout with no verdicts built yet → every paragraph `not_analysed`).
        analyse_fn: the live two-branch analysis seam for `POST …/analyse`. Left
            `None` in the real app until credentials are wired — a `None` seam
            makes the route report `503 ANALYSE_UNAVAILABLE`, so the pre-baked
            paragraphs are unaffected. Tests inject a stub.
        verdict_fn: injectable verdict seam passed to `propose_verdicts` on the
            live analyse path; `None` in the demo (candidates carry frozen
            verdicts). Tests stub it.

    Returns:
        A configured `FastAPI` app. No network or credentials are required to
        build it — the model seams are only exercised on `POST /connections/find`
        and `POST …/analyse`, and only with whatever seams are supplied.
    """
    app = FastAPI(title="Rulebook Radar — read API")

    submissions_dir = Path(submissions_dir)
    known_document_ids = {node["id"] for node in graph.get("nodes", [])}
    verdicts = verdicts or {}
    # Bridge the loaded ClauseIndex into an AnchorIndex so
    # `find_connections` (which now expects the anchor-shaped index) can
    # consume the same clause data. The build pipeline (Task 7) will later
    # produce a native anchor-index.json and replace this bridge; until then
    # every clause entry maps to a structured-rules Anchor byte-identically.
    anchor_index = _anchor_index_from_clause_index(clause_index)

    # The curated source library (branch ②) is the graph's public reference
    # nodes — the un-cited sources a live `POST …/analyse` matches a paragraph
    # against. An app built with none (an empty library) reports `409
    # SOURCE_LIBRARY_EMPTY` rather than pretending a live analysis could run.
    # Restricted node-only references (the handbook) are excluded — they carry
    # no ingested passage and are never analysable.
    curated_source_ids = [
        node["id"]
        for node in graph.get("nodes", [])
        if node.get("kind") == "reference" and node.get("access") != "restricted"
    ]

    def _is_known_document(document_id: str) -> bool:
        """A document is "known" if it has a graph node OR any clause-index
        entry — either is enough to address its paragraphs / report 404 for."""
        if document_id in known_document_ids:
            return True
        return bool(clause_index.entries_for_document(document_id))

    def _analysed_paragraph_numbers() -> set[str]:
        """The set of paragraph numbers that already have a verdict record —
        i.e. paragraphs the build (or a prior `analyse`) has analysed."""
        return {
            record["paragraph"]
            for record in verdicts.values()
            if record.get("paragraph") is not None
        }

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
            return _error(404, "NODE_NOT_FOUND", f"No node with id '{node_id}'")
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
            anchor_index,
            finder_fn=finder_fn,
            critic_fn=critic_fn,
            output_dir=trace_output_dir,
        )
        return result

    @app.get("/documents/{document_id}/paragraphs")
    def get_paragraphs(document_id: str) -> Any:
        # The uploaded document's paragraphs + per-paragraph analysis state
        # (drives the workspace canvas + badges). Model-free — served from the
        # clause index (paragraph text) joined onto verdicts.json (state +
        # rendered connection count, restricted nodes excluded).
        if not _is_known_document(document_id):
            return _error(
                404, "DOCUMENT_NOT_FOUND", f"No document with id '{document_id}'"
            )
        return render_paragraphs_index(document_id, clause_index, verdicts, graph)

    @app.get("/documents/{document_id}/paragraphs/{number}/connections")
    def get_paragraph_connections(document_id: str, number: str) -> Any:
        # Everything a downstream UI needs to render the right rail for one
        # paragraph. Model-free — verdicts + graph + clause-index join only.
        # Restricted sources never surface (dropped by `public_nodes`); every
        # quote comes verbatim from the clause index (or is null for a blocked /
        # pending-extraction source — never approximated).
        if not _is_known_document(document_id):
            return _error(
                404, "DOCUMENT_NOT_FOUND", f"No document with id '{document_id}'"
            )
        payload = render_paragraph_connections(
            document_id, number, verdicts, graph, clause_index
        )
        if payload is None:
            return _error(
                404,
                "PARAGRAPH_NOT_FOUND",
                f"No paragraph '{number}' in document '{document_id}'",
            )
        return payload

    @app.post("/documents/{document_id}/paragraphs/{number}/analyse")
    def analyse_paragraph_route(
        document_id: str, number: str, force: bool = False
    ) -> Any:
        # The ONE route that reaches the model at request time (live "Analyse
        # this paragraph"). It runs branch-①+② over a not-yet-analysed paragraph
        # and returns the SAME shape as `GET …/connections`. Everything else in
        # the API is model-free, so a live hiccup here degrades to `503` and
        # leaves the pre-baked paragraphs untouched.
        if not _is_known_document(document_id):
            return _error(
                404, "DOCUMENT_NOT_FOUND", f"No document with id '{document_id}'"
            )
        # The paragraph must exist as a clause of the document, even if it has
        # never been analysed (a `not_analysed` paragraph is still analysable).
        entry = paragraph_entry(clause_index, document_id, number)
        if entry is None:
            return _error(
                404,
                "PARAGRAPH_NOT_FOUND",
                f"No paragraph '{number}' in document '{document_id}'",
            )
        # Already analysed → re-analysis is an explicit opt-in (`?force=true`),
        # so the demo's frozen showcase paragraphs are not silently recomputed.
        if number in _analysed_paragraph_numbers() and not force:
            return _error(
                400,
                "INVALID_ANALYSE_REQUEST",
                f"Paragraph '{number}' is already analysed; re-analysis "
                f"requires ?force=true",
            )
        # No curated library configured → nothing for branch ② to match against.
        if not curated_source_ids:
            return _error(
                409,
                "SOURCE_LIBRARY_EMPTY",
                "No curated source library is loaded; cannot analyse",
            )
        # No live seam wired (or a mid-pitch Azure hiccup) → graceful 503; the
        # pre-analysed paragraphs served by `GET …/connections` are unaffected.
        if analyse_fn is None:
            return _error(
                503,
                "ANALYSE_UNAVAILABLE",
                "Live analysis is temporarily unavailable; pre-analysed "
                "paragraphs are unaffected",
            )

        paragraph_text = entry.get("text", "")
        try:
            candidates = analyse_fn(document_id, number, paragraph_text, clause_index)
            # Classify the branch-①+② candidates into verdict records (the same
            # deterministic guardrail as the build), then render each through the
            # shared read model. This is kept INSIDE the try so a live
            # verdict-stage failure (a model hiccup, or a verdict outside the
            # five values) degrades to the SAME graceful 503 as a finder failure
            # — never a raw 500 — honouring the documented backstop.
            records = propose_verdicts(candidates, clause_index, verdict_fn=verdict_fn)
            nodes = public_nodes(graph)
            connections = [
                connection
                for connection in (
                    render_connection(record, nodes, clause_index)
                    for record in records.values()
                )
                if connection is not None
            ]
        except Exception:  # noqa: BLE001 — any live failure degrades to 503
            return _error(
                503,
                "ANALYSE_UNAVAILABLE",
                "Live analysis is temporarily unavailable; pre-analysed "
                "paragraphs are unaffected",
            )

        # An empty result is `no_matching_source: true` (a 200 success, NOT an
        # error) — never a fabricated connection.
        return {
            "paragraph": {
                "number": number,
                "title": entry.get("heading") or "",
                "text": paragraph_text,
            },
            "state": "analysed",
            "no_matching_source": len(connections) == 0,
            "connections": connections,
        }

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


def _anchor_index_from_clause_index(clause_index: ClauseIndex) -> AnchorIndex:
    """Bridge a loaded `ClauseIndex` into an `AnchorIndex`.

    Every primary clause entry becomes an `Anchor` under
    `doc_class="structured-rules"`, using the canonical
    `"{PolicyShortName} {clause_number}"` id (already the shape
    `ClauseIndex` keys itself by, so the mapping is a straight lift).
    Verbatim text is preserved byte-for-byte from the clause entry.

    This is the temporary bridge that lets `find_connections` (which now
    expects an `AnchorIndex`) run on top of the legacy `clause-index.json`
    artifact. The build-pipeline story (Task 7 in the anchor-segmentation
    spec) will produce a native `anchor-index.json`, and this helper will
    be replaced by a direct load at that point.
    """
    anchors: list[Anchor] = []
    for entry in clause_index._primary.values():
        anchor_id = entry["clause_number"]
        anchors.append(
            {
                "anchor_id": anchor_id,
                "anchor_label": anchor_id,
                "text": entry["text"],
                "doc_class": "structured-rules",
                "document_id": entry["document_id"],
                "heading_path": [],
                "page_span": None,
                "parent_anchor": None,
            }
        )
    return AnchorIndex(anchors)


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


def _load_verdicts(artifacts_dir: Path) -> dict[str, Any]:
    """Load `verdicts.json`, tolerating its absence in a fresh checkout.

    Mirrors `_load_graph`: a missing artifact (the verdict stage not built yet)
    yields `{}`, so the paragraph routes still start and simply report every
    paragraph as `not_analysed` rather than crashing at startup.
    """
    path = artifacts_dir / "verdicts.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _build_default_app() -> FastAPI:
    """Lazily construct the real app from `data/artifacts/` for uvicorn.

    Never fails at import if the artifacts are absent — loads an empty index /
    graph / verdicts instead, so `uvicorn engine.api:app` starts on a fresh
    checkout.
    """
    from engine.config import REPO_ROOT

    artifacts_dir = REPO_ROOT / "data" / "artifacts"
    return create_app(
        clause_index=_load_clause_index(artifacts_dir),
        graph=_load_graph(artifacts_dir),
        verdicts=_load_verdicts(artifacts_dir),
    )


app = _build_default_app()
