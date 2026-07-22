"""FastAPI read service for Workstream Brain.

A thin, read-only HTTP service over the per-workstream fixture store in
`data/workstreams/`: one directory per workstream holding a `graph.json`
(documents as nodes, structural edges between them) and a `findings/` folder of
per-edge linkage arrays. It needs **no** model access and no credentials — the
routes are projections over files held in memory.

The service is constructed by `create_app(...)`, which takes its dependencies as
injectable arguments (the workstreams dir, the clause-index `artifacts_dir`, and
the `find_connections_fn` finder seam), so tests build an app against fixture
dirs — and stub the finder — with no network and nothing on disk to prepare. A
module-level `app` for `uvicorn engine.api:app` defaults to `data/workstreams`.

Scope note: this used to also serve the superseded reconciliation-workbench read
path — clause/graph/node/paragraph routes over `data/artifacts/`, a live
`POST /connections/find`, and role-gated submission upload. All of that was
removed when Workstream Brain became the end state. `engine.clauses` and
`engine.connections` (the clause index and the five-label finder→critic loop)
remain — they are the current engine, exercised by `scripts/run_finder_trace.py`
and the taxonomy tests, and are simply not mounted as HTTP routes today.

Confidentiality (hard rule): every route here is public — the workstream
fixtures derive from public BNM documents.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from engine.clauses import load_clause_index
from engine.connections import find_connections as _default_find_connections
from engine.copilot import copilot_reply as _default_copilot_reply
from engine.config import REPO_ROOT
from engine import (
    concepts,
    copilot,
    cross_intel,
    directory,
    drafts,
    findings,
    linkage_review,
    tasks,
    workstreams,
)

# The Workstream Brain fixture store (Task 1): one directory per workstream, each
# holding a `graph.json` (`{"nodes": [...], "edges": [...]}`) and a `findings/`
# folder of `{edge_id}.json` connection arrays. Injectable so tests point it at a
# tmp/fixture dir; the module-level `app` defaults it to `data/workstreams`.
WORKSTREAMS_DIR = REPO_ROOT / "data" / "workstreams"

# The store for edges whose endpoints live in DIFFERENT workstreams. Not a
# workstream itself: it carries no `workstream.json`, so `list_workstreams()`
# skips it and it never shows up in the sidebar. Its `graph.json` uses the
# ordinary node/edge shape, which is what lets the existing review route serve
# cross-workstream findings without a line of new code. See
# data/workstreams/_cross/README.md.
CROSS_STORE = "_cross"


def _cross_side(
    edge: dict[str, Any], workstream_id: str
) -> Optional[tuple[str, str]]:
    """Orient a cross-link relative to `workstream_id` → `(near_id, far_id)`.

    Returns None when the edge does not touch this workstream. A link is stored
    once, in one direction (the direction its findings were written from), so
    each side has to read it from its own end.
    """
    if edge.get("source_workstream_id") == workstream_id:
        return edge["source"], edge["target"]
    if edge.get("target_workstream_id") == workstream_id:
        return edge["target"], edge["source"]
    return None


def _workstream_name(workstreams_dir: Path, workstream_id: Optional[str]) -> Optional[str]:
    """The far workstream's display name, for "…in Open Finance ED · 2025"."""
    if workstream_id is None:
        return None
    meta = workstreams.load_workstream(workstreams_dir, workstream_id)
    return meta.get("name") if meta else None


def _cross_link_findings_summary(
    workstreams_dir: Path, edge_id: str
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """An edge's findings plus a tally by label. Shared by the per-workstream
    and aggregate cross-links routes so the two never drift on how a link's
    findings are read or counted."""
    try:
        edge_findings = findings.load(workstreams_dir, CROSS_STORE, edge_id)
    except findings.FindingsNotAnalysedError:
        edge_findings = []
    labels: dict[str, int] = {}
    for finding in edge_findings:
        label = finding.get("label")
        labels[label] = labels.get(label, 0) + 1
    return edge_findings, labels


def _all_cross_links(workstreams_dir: Path) -> list[dict[str, Any]]:
    """Every cross-workstream link in the corpus, once each — not relative to
    an asking workstream (the edge's own source side is `near`, target side is
    `far`). Backs the aggregate `GET /api/cross-links` route (Overlap Alerts);
    the per-workstream route below still reorients near/far relative to the
    workstream asked about.
    """
    cross = workstreams.load_graph(workstreams_dir, CROSS_STORE)
    if cross is None:
        return []

    nodes_by_id = {n["id"]: n for n in cross.get("nodes", [])}

    def _side(node_id: str) -> dict[str, Any]:
        node = nodes_by_id.get(node_id, {})
        workstream_id = node.get("workstream_id")
        return {
            "node_id": node_id,
            "title": node.get("title"),
            "workstream_id": workstream_id,
            "workstream_name": _workstream_name(workstreams_dir, workstream_id),
        }

    links: list[dict[str, Any]] = []
    for edge in cross.get("edges", []):
        edge_findings, labels = _cross_link_findings_summary(workstreams_dir, edge["id"])
        near, far = _side(edge["source"]), _side(edge["target"])
        links.append(
            {
                "id": edge["id"],
                "edge_type": edge.get("edge_type"),
                "near": near,
                "far": far,
                "findings_count": len(edge_findings),
                "labels": labels,
                "counts": findings.counts(edge_findings),
                **_cross_intel_block(
                    workstreams_dir,
                    near["workstream_id"],
                    near["node_id"],
                    far["workstream_id"],
                    far["node_id"],
                    labels,
                    edge,
                ),
            }
        )
    return links


def _cross_intel_block(
    workstreams_dir: Path,
    near_workstream_id: Optional[str],
    near_node_id: str,
    far_workstream_id: Optional[str],
    far_node_id: str,
    labels: dict[str, int],
    edge: dict[str, Any],
) -> dict[str, Any]:
    """The Cross-Workstream Intelligence enrichment shared by every cross-link
    surface: what the two documents share, why the overlap was flagged, and how
    the linkage labels roll up to a classification + risk level. Loads each
    side's concept metadata (absent → empty, so a signal simply does not fire).
    """
    near_concepts = (
        concepts.load_concepts(workstreams_dir, near_workstream_id, near_node_id)
        if near_workstream_id
        else None
    ) or {}
    far_concepts = (
        concepts.load_concepts(workstreams_dir, far_workstream_id, far_node_id)
        if far_workstream_id
        else None
    ) or {}
    shared = cross_intel.shared_attributes(near_concepts, far_concepts)
    classification, risk_level = cross_intel.classify(labels)
    return {
        "classification": classification,
        "risk_level": risk_level,
        "detected_at": edge.get("detected_at"),
        "shared_attributes": shared,
        "reasons": cross_intel.reasons(shared, labels),
    }


def _cross_profile(
    workstreams_dir: Path, node: dict[str, Any], workstream_id: Optional[str]
) -> dict[str, Any]:
    """One side of a relationship-detail: the document plus its regulatory
    profile (concept metadata), for the intelligence panel and comparison view.
    """
    node_concepts = (
        concepts.load_concepts(workstreams_dir, workstream_id, node["id"])
        if workstream_id
        else None
    )
    return {
        "node_id": node["id"],
        "title": node.get("title"),
        "node_type": node.get("node_type"),
        "issuer": node.get("issuer"),
        "short_type": node.get("short_type"),
        "description": node.get("description"),
        "workstream_id": workstream_id,
        "workstream_name": _workstream_name(workstreams_dir, workstream_id),
        "concepts": (
            {"status": "available", **node_concepts}
            if node_concepts is not None
            else {"status": "placeholder", "message": "Concept extraction not enabled in MVP1"}
        ),
    }


def _linkage_review_rows(
    workstreams_dir: Path, workstream_id: str, edge_id: str
) -> list[dict[str, Any]]:
    """Every linkage on an edge, each with its finding summary + maker-checker
    record (defaulted to ai_detected when never acted on). Shared by the
    per-edge linkage-review route and the aggregate Review Queue."""
    try:
        edge_findings = findings.load(workstreams_dir, workstream_id, edge_id)
    except findings.FindingsNotAnalysedError:
        return []
    records = linkage_review.load_edge(workstreams_dir, workstream_id, edge_id)
    rows: list[dict[str, Any]] = []
    for finding in edge_findings:
        fid = finding["id"]
        record = records.get(fid) or linkage_review.default_record()
        rows.append(
            {
                "finding_id": fid,
                "summary": finding.get("summary"),
                "label": finding.get("label"),
                "sentiment": finding.get("sentiment"),
                "review": record,
            }
        )
    return rows


def _review_queue_items(workstreams_dir: Path) -> list[dict[str, Any]]:
    """The Review Queue's working set: every cross-workstream linkage with its
    maker-checker status and the two workstreams it spans. Cross-workstream
    overlaps are the linkages that most need a human before FPWG, so the queue
    is built over the `_cross` store."""
    cross = workstreams.load_graph(workstreams_dir, CROSS_STORE)
    if cross is None:
        return []
    nodes_by_id = {n["id"]: n for n in cross.get("nodes", [])}

    def _side(node_id: str) -> dict[str, Any]:
        node = nodes_by_id.get(node_id, {})
        ws_id = node.get("workstream_id")
        return {
            "node_id": node_id,
            "title": node.get("title"),
            "workstream_id": ws_id,
            "workstream_name": _workstream_name(workstreams_dir, ws_id),
        }

    items: list[dict[str, Any]] = []
    for edge in cross.get("edges", []):
        near, far = _side(edge["source"]), _side(edge["target"])
        for row in _linkage_review_rows(workstreams_dir, CROSS_STORE, edge["id"]):
            items.append(
                {
                    "workstream_id": CROSS_STORE,
                    "edge_id": edge["id"],
                    "finding_id": row["finding_id"],
                    "summary": row["summary"],
                    "label": row["label"],
                    "sentiment": row["sentiment"],
                    "near": near,
                    "far": far,
                    "status": row["review"]["status"],
                    "maker": row["review"]["maker"],
                    "checker": row["review"]["checker"],
                    "created_at": row["review"]["created_at"],
                    "checked_at": row["review"]["checked_at"],
                }
            )
    return items

def _ws_error(
    status_code: int, code: str, message: str, field: Optional[str] = None
) -> JSONResponse:
    """Error body for the Workstream Brain routes: `{code, message}` (Task 1
    contract), plus an optional `field` (e.g. which endpoint of an edge lacks
    an ingested document) included only when given."""
    content: dict[str, Any] = {"code": code, "message": message}
    if field is not None:
        content["field"] = field
    return JSONResponse(status_code=status_code, content=content)


def _load_workstream_graph(
    workstreams_dir: Path, workstream_id: str
) -> Optional[dict[str, Any]]:
    """Load a workstream's `graph.json`, or `None` when the workstream dir or its
    `graph.json` is missing (→ the route reports 404 WORKSTREAM_NOT_FOUND)."""
    graph_path = workstreams_dir / workstream_id / "graph.json"
    if not graph_path.exists():
        return None
    return json.loads(graph_path.read_text(encoding="utf-8"))


def create_app(
    workstreams_dir: Union[str, Path] = WORKSTREAMS_DIR,
    artifacts_dir: Union[str, Path] = REPO_ROOT / "data" / "artifacts",
    find_connections_fn: Any = _default_find_connections,
    copilot_reply_fn: Any = _default_copilot_reply,
) -> FastAPI:
    """Construct the Workstream Brain read API against injected dependencies.

    Args:
        workstreams_dir: the Workstream Brain fixture store (one dir per
            workstream with a `graph.json` + `findings/{edge_id}.json`);
            injectable so tests point it at a fixture/tmp dir. Defaults to
            `data/workstreams`.
        artifacts_dir: where the clause index (`engine.clauses.load_clause_index`)
            is read from for live analysis. Defaults to `data/artifacts`.
        find_connections_fn: the finder called by the `analyze` route —
            `(doc_a_id, doc_b_id, clause_index) -> {"connections": [...],
            "unsupported": [...]}`. Injectable so tests stub the model; no
            live model call happens in CI. Defaults to
            `engine.connections.find_connections`.
        copilot_reply_fn: the live call behind the `copilot` route — see
            `engine.copilot.copilot_reply`'s signature. Injectable so tests
            stub the model; no live model call happens in CI. Defaults to
            `engine.copilot.copilot_reply`.

    Returns:
        A configured `FastAPI` app. No network, credentials, or build artifacts
        are required — every route is a projection over `workstreams_dir`.
    """
    app = FastAPI(title="Workstream Brain — read API")

    # CORS: allow the Vite dev server and common local ports to reach the API.
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    workstreams_dir = Path(workstreams_dir)

    # --- Workstream Brain — Task Screen routes (Task 1) --------------------
    # Read-only projections over a per-workstream `graph.json` + `findings/`
    # fixture store. A neighbour is "analysed" iff its edge has a findings file;
    # `findings_count` is that file's length. `draft_empty` is derived from the
    # task node's `clause_count` so it tracks the actual draft state. Error body
    # is `{code, message}` (see `_ws_error`) — the Task Screen contract.

    def _edge_findings_path(workstream_id: str, edge_id: str) -> Path:
        return workstreams_dir / workstream_id / "findings" / f"{edge_id}.json"

    @app.get("/api/workstreams/{workstream_id}/tasks/{node_id}")
    def get_workstream_task(workstream_id: str, node_id: str) -> Any:
        try:
            ws_graph = _load_workstream_graph(workstreams_dir, workstream_id)
            if ws_graph is None:
                return _ws_error(
                    404,
                    "WORKSTREAM_NOT_FOUND",
                    f"Workstream {workstream_id} not found",
                )

            nodes_by_id = {n["id"]: n for n in ws_graph.get("nodes", [])}
            node = nodes_by_id.get(node_id)
            if node is None:
                return _ws_error(
                    404,
                    "NODE_NOT_FOUND",
                    f"Node {node_id} not found in workstream {workstream_id}",
                )
            if node.get("node_type") != "task":
                return _ws_error(
                    400,
                    "NOT_A_TASK",
                    f"Node {node_id} is of type {node.get('node_type')}, "
                    "not task",
                )

            # Neighbours = edges out of this task node, in graph.json order.
            neighbours = []
            for edge in ws_graph.get("edges", []):
                if edge.get("source") != node_id:
                    continue
                target = nodes_by_id.get(edge["target"], {})
                findings_path = _edge_findings_path(workstream_id, edge["id"])
                analysed = findings_path.exists()
                findings_count = (
                    len(json.loads(findings_path.read_text(encoding="utf-8")))
                    if analysed
                    else 0
                )
                neighbours.append(
                    {
                        "node_id": edge["target"],
                        "title": target.get("title", edge["target"]),
                        "node_type": target.get("node_type"),
                        "edge_type": edge.get("edge_type"),
                        "edge_id": edge["id"],
                        "analysed": analysed,
                        "findings_count": findings_count,
                    }
                )

            clause_count = node.get("clause_count", 0)
            task = {
                "id": node["id"],
                "title": node.get("title"),
                "source_name": node.get("source_name"),
                "format": node.get("format"),
                "description": node.get("description"),
                "status": node.get("status"),
                "owner": node.get("owner"),
                "reviewers": node.get("reviewers", []),
                "clause_count": clause_count,
                "last_edited_at": node.get("last_edited_at"),
            }
            workflow = tasks.load_workflow(
                workstreams_dir, workstream_id, node_id, node.get("status")
            )
            return {
                "task": task,
                "workflow": workflow,
                "neighbours": neighbours,
                "draft_empty": clause_count == 0,
            }
        except Exception:  # noqa: BLE001 — contract: any load error → 500
            return _ws_error(
                500,
                "INTERNAL_ERROR",
                f"Failed to load task {node_id} in workstream {workstream_id}",
            )

    @app.patch("/api/workstreams/{workstream_id}/tasks/{node_id}/workflow")
    async def patch_task_workflow(
        workstream_id: str, node_id: str, request: Request
    ) -> Any:
        """Move a task through Maker-Checker — Draft -> Pending Review -> Approved.

        Mirrors `patch_finding_review_state`'s shape: validate the target
        state, persist via `engine.tasks`, return the updated record. The
        `actor_id` is whoever performed the transition — recorded as `checker`
        on Pending Review, `approved_by` on Approved.
        """
        ws_graph = _load_workstream_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        nodes_by_id = {n["id"]: n for n in ws_graph.get("nodes", [])}
        node = nodes_by_id.get(node_id)
        if node is None:
            return _ws_error(
                404,
                "NODE_NOT_FOUND",
                f"Node {node_id} not found in workstream {workstream_id}",
            )
        if node.get("node_type") != "task":
            return _ws_error(
                400,
                "NOT_A_TASK",
                f"Node {node_id} is of type {node.get('node_type')}, not task",
            )

        body = await request.json()
        status = body.get("status") if isinstance(body, dict) else None
        if status not in tasks.WORKFLOW_STATES:
            return _ws_error(
                400,
                "INVALID_WORKFLOW_STATE",
                f"status must be one of {sorted(tasks.WORKFLOW_STATES)}, "
                f"got {status!r}",
            )

        actor_id = body.get("actor_id") if isinstance(body, dict) else None
        actor = directory.person(actor_id) if isinstance(actor_id, str) else None
        if actor is None:
            return _ws_error(
                400, "INVALID_ACTOR", f"actor_id {actor_id!r} is not in the directory"
            )

        workflow = tasks.set_workflow(
            workstreams_dir, workstream_id, node_id, node.get("status"), status, actor
        )
        return {"workflow": workflow}

    @app.get("/api/workstreams/{workstream_id}/edges/{edge_id}/findings")
    def get_workstream_edge_findings(workstream_id: str, edge_id: str) -> Any:
        ws_graph = _load_workstream_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404,
                "WORKSTREAM_NOT_FOUND",
                f"Workstream {workstream_id} not found",
            )
        edge_ids = {e["id"] for e in ws_graph.get("edges", [])}
        if edge_id not in edge_ids:
            return _ws_error(
                404,
                "EDGE_NOT_FOUND",
                f"Edge {edge_id} not found in workstream {workstream_id}",
            )
        findings_path = _edge_findings_path(workstream_id, edge_id)
        if not findings_path.exists():
            return []
        return json.loads(findings_path.read_text(encoding="utf-8"))

    # --- Workstream Brain — Graph Screen routes (spec-workstream-graph) -----
    # The drafter's hero screen: a canvas of the workstream's primary draft +
    # its anchors. Same `{code, message}` error body and derived-`analysed`
    # convention as the Task Screen routes above. Node/edge shapes stay on the
    # on-disk `node_type`/`edge_type` vocabulary; the schema helpers live in
    # `engine/workstreams.py`.

    @app.get("/api/workstreams")
    def list_workstreams_route() -> Any:
        return {"workstreams": workstreams.list_workstreams(workstreams_dir)}

    @app.get("/api/reviewers")
    def list_reviewers_route() -> Any:
        """The colleagues the current user may nominate — the directory minus
        themselves. Static: there is no staff directory in MVP1."""
        return {"reviewers": directory.selectable_reviewers()}

    @app.post("/api/workstreams", status_code=201)
    async def create_workstream_route(request: Request) -> Any:
        """Scaffold a new workstream and return it.

        This is the only route in the service that WRITES a new directory under
        `data/workstreams/` — a tracked path. On the demo host that means
        creating a workstream dirties the working tree; that is the fixture
        store doubling as the database, and is a property of the whole design
        rather than of this route.
        """
        body = await request.json() if await request.body() else {}
        if not isinstance(body, dict):
            return _ws_error(400, "NAME_REQUIRED", "Give the workstream a name.")

        invalid = workstreams.validate_workstream_create(body)
        if invalid:
            code, message, field = invalid
            return JSONResponse(
                status_code=400, content={"code": code, "message": message, "field": field}
            )

        reviewers, bad_id = directory.resolve_reviewers(body.get("reviewer_ids"))
        if reviewers is None:
            return JSONResponse(
                status_code=400,
                content={
                    "code": "INVALID_REVIEWER_ID",
                    "message": f"{bad_id!r} is not a colleague you can nominate.",
                    "field": "reviewer_ids",
                },
            )

        stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        try:
            record = workstreams.create_workstream(
                workstreams_dir, body, directory.owner(), reviewers, stamp
            )
        except OSError:
            return _ws_error(
                500, "WORKSTREAM_WRITE_FAILED", "Could not write the new workstream."
            )
        return record

    @app.get("/api/cross-links")
    def get_all_cross_links() -> Any:
        """Every cross-workstream link in the corpus, regardless of workstream.

        Backs the Home dashboard's Overlap Alerts card and the Institution
        Map's banner — a proactive, always-visible surface for exactly the
        drift this product exists to catch, so an overlap like BCM <->
        Recovery Planning is seen before FPWG rather than after. Same link
        shape as the per-workstream route below, just not scoped to one
        workstream's point of view.
        """
        return {"links": _all_cross_links(workstreams_dir)}

    @app.get("/api/workstreams/{workstream_id}/cross-links")
    def get_cross_links(workstream_id: str) -> Any:
        """Linkages from this workstream's documents into another workstream's.

        Cross-workstream drift is the thing this product exists to catch: two
        teams draft in parallel, each anchoring to different versions of the same
        policy, and nobody notices until publication. An edge between them
        belongs to neither workstream's `graph.json`, so it lives in the `_cross`
        store (see `data/workstreams/_cross/README.md`).

        Returns the far side of each link plus a label tally, so a caller can
        render "12 linkages · 4 differ" without fetching every finding. The
        findings themselves are read through the ordinary review route, which
        serves `_cross` unchanged.
        """
        if workstreams.load_graph(workstreams_dir, workstream_id) is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        cross = workstreams.load_graph(workstreams_dir, CROSS_STORE)
        if cross is None:
            return {"links": []}  # no cross store on disk — nothing to report

        nodes_by_id = {n["id"]: n for n in cross.get("nodes", [])}
        links: list[dict[str, Any]] = []
        for edge in cross.get("edges", []):
            near_side = _cross_side(edge, workstream_id)
            if near_side is None:
                continue  # this link does not touch the workstream being asked about
            near_id, far_id = near_side
            edge_findings, labels = _cross_link_findings_summary(
                workstreams_dir, edge["id"]
            )

            far_node = nodes_by_id.get(far_id, {})
            near_node = nodes_by_id.get(near_id, {})
            links.append(
                {
                    "id": edge["id"],
                    "edge_type": edge.get("edge_type"),
                    "near": {
                        "node_id": near_id,
                        "title": near_node.get("title"),
                        "workstream_id": workstream_id,
                    },
                    "far": {
                        "node_id": far_id,
                        "title": far_node.get("title"),
                        "workstream_id": far_node.get("workstream_id"),
                        "workstream_name": _workstream_name(
                            workstreams_dir, far_node.get("workstream_id")
                        ),
                    },
                    "findings_count": len(edge_findings),
                    "labels": labels,
                    "counts": findings.counts(edge_findings),
                    **_cross_intel_block(
                        workstreams_dir,
                        workstream_id,
                        near_id,
                        far_node.get("workstream_id"),
                        far_id,
                        labels,
                        edge,
                    ),
                }
            )
        return {"links": links}

    @app.get("/api/cross-links/{edge_id}")
    def get_cross_link_detail(edge_id: str) -> Any:
        """One cross-workstream relationship in full: both documents' regulatory
        profiles, what they share, why it was flagged, the label rollup, and the
        verbatim clause evidence on every linkage.

        Backs the Cross-Workstream Intelligence relationship panel — the answer
        to "which other workstream overlaps mine, and why", with the evidence to
        act on it. Source side is `near`, target side is `far` (the same
        orientation the review route serves the edge in).
        """
        cross = workstreams.load_graph(workstreams_dir, CROSS_STORE)
        edge = (
            next((e for e in cross.get("edges", []) if e["id"] == edge_id), None)
            if cross
            else None
        )
        if edge is None:
            return _ws_error(
                404, "CROSS_LINK_NOT_FOUND", f"Cross-workstream link {edge_id} not found"
            )
        nodes_by_id = {n["id"]: n for n in cross.get("nodes", [])}
        near_node = nodes_by_id.get(edge["source"], {"id": edge["source"]})
        far_node = nodes_by_id.get(edge["target"], {"id": edge["target"]})
        near_ws = near_node.get("workstream_id") or edge.get("source_workstream_id")
        far_ws = far_node.get("workstream_id") or edge.get("target_workstream_id")

        edge_findings, labels = _cross_link_findings_summary(workstreams_dir, edge_id)
        intel = _cross_intel_block(
            workstreams_dir, near_ws, near_node["id"], far_ws, far_node["id"], labels, edge
        )
        return {
            "id": edge_id,
            "edge_type": edge.get("edge_type"),
            "detected_at": intel["detected_at"],
            "classification": intel["classification"],
            "risk_level": intel["risk_level"],
            "near": _cross_profile(workstreams_dir, near_node, near_ws),
            "far": _cross_profile(workstreams_dir, far_node, far_ws),
            "shared_attributes": intel["shared_attributes"],
            "reasons": intel["reasons"],
            "labels": labels,
            "counts": findings.counts(edge_findings),
            "findings": edge_findings,
        }

    @app.get("/api/review-queue")
    def get_review_queue() -> Any:
        """Every cross-workstream linkage that may need a human, with its
        Maker-Checker status. Backs the Review Queue — the backlog a team clears
        before a workstream reaches FPWG."""
        items = _review_queue_items(workstreams_dir)
        return {
            "items": items,
            "counts_by_status": linkage_review.counts_by_status(
                [{"status": it["status"]} for it in items]
            ),
        }

    @app.get("/api/workstreams/{workstream_id}/edges/{edge_id}/linkage-review")
    def get_linkage_review(workstream_id: str, edge_id: str) -> Any:
        """The Maker-Checker record for every linkage on an edge (defaulted to
        ai_detected when never acted on)."""
        if workstreams.load_graph(workstreams_dir, workstream_id) is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        return {
            "edge_id": edge_id,
            "linkages": _linkage_review_rows(workstreams_dir, workstream_id, edge_id),
        }

    @app.patch(
        "/api/workstreams/{workstream_id}/edges/{edge_id}/findings/{finding_id}/linkage-review"
    )
    def patch_linkage_review(
        workstream_id: str, edge_id: str, finding_id: str, body: dict[str, Any]
    ) -> Any:
        """Apply a Maker-Checker action to one linkage.

        Body: `{action, actor_id, comment?}`. Validates the actor against the
        directory and the finding against the edge, then runs the state-machine
        transition (which enforces valid transitions + the maker≠checker rule).
        """
        action = body.get("action")
        actor_id = body.get("actor_id")
        comment = body.get("comment")

        actor = directory.person(actor_id) if isinstance(actor_id, str) else None
        if actor is None:
            return _ws_error(400, "UNKNOWN_ACTOR", f"Unknown actor '{actor_id}'")

        try:
            edge_findings = findings.load(workstreams_dir, workstream_id, edge_id)
        except findings.FindingsNotAnalysedError:
            return _ws_error(
                400, "EDGE_NOT_ANALYSED", f"Edge {edge_id} has not been analysed yet"
            )
        if not any(f["id"] == finding_id for f in edge_findings):
            return _ws_error(
                404, "FINDING_NOT_FOUND", f"Finding {finding_id} not found on {edge_id}"
            )

        try:
            record = linkage_review.apply_action(
                workstreams_dir,
                workstream_id,
                edge_id,
                finding_id,
                action,
                actor,
                comment if isinstance(comment, str) and comment.strip() else None,
            )
        except linkage_review.LinkageReviewError as exc:
            return _ws_error(400, exc.code, exc.message)
        return {"finding_id": finding_id, "review": record}

    @app.get("/api/workstreams/{workstream_id}/graph")
    def get_workstream_graph(workstream_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        ws_meta = workstreams.load_workstream(workstreams_dir, workstream_id)
        task_id = workstreams.primary_task_id(ws_meta, ws_graph)
        nodes, edges = workstreams.primary_subgraph(ws_graph, task_id)
        out_nodes = [
            {
                "id": n["id"],
                "node_type": n.get("node_type"),
                "title": n.get("title"),
                "issuer": n.get("issuer"),
                "short_type": n.get("short_type"),
            }
            for n in nodes
        ]
        out_edges = []
        for e in edges:
            findings = workstreams.load_findings(workstreams_dir, workstream_id, e["id"])
            out_edges.append(
                {
                    "id": e["id"],
                    "source": e["source"],
                    "target": e["target"],
                    "edge_type": e.get("edge_type"),
                    "analysed": findings is not None,
                    "findings_count": len(findings) if findings else 0,
                }
            )
        return {
            "workstream_id": workstream_id,
            "primary_task_id": task_id,
            "nodes": out_nodes,
            "edges": out_edges,
        }

    @app.get("/api/workstreams/{workstream_id}/nodes/{node_id}")
    def get_workstream_node_detail(workstream_id: str, node_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        all_by_id = {n["id"]: n for n in ws_graph.get("nodes", [])}
        node = all_by_id.get(node_id)
        if node is None:
            return _ws_error(
                404,
                "NODE_NOT_FOUND",
                f"Node {node_id} not found in workstream {workstream_id}",
            )
        ws_meta = workstreams.load_workstream(workstreams_dir, workstream_id)
        task_id = workstreams.primary_task_id(ws_meta, ws_graph)
        sub_nodes, sub_edges = workstreams.primary_subgraph(ws_graph, task_id)
        sub_ids = {n["id"] for n in sub_nodes}
        # A node shown on the canvas takes its neighbours from the primary
        # subgraph (so an anchor shared with a sibling draft still lists only
        # this draft); a node outside it falls back to the whole graph.
        edge_scope = sub_edges if node_id in sub_ids else ws_graph.get("edges", [])
        first_order = [
            {
                "id": nid,
                "node_type": all_by_id[nid].get("node_type"),
                "title": all_by_id[nid].get("title"),
            }
            for nid in workstreams.neighbour_ids(edge_scope, node_id)
            if nid in all_by_id
        ]
        node_concepts = concepts.load_concepts(workstreams_dir, workstream_id, node_id)
        return {
            "id": node["id"],
            "node_type": node.get("node_type"),
            "title": node.get("title"),
            "issuer": node.get("issuer"),
            "short_type": node.get("short_type"),
            "description": node.get("description"),
            "source_url": node.get("source_url"),
            "ismp_classification": node.get("ismp_classification"),
            "pursuant_to": node.get("pursuant_to"),
            "first_order_neighbours": first_order,
            "second_order_neighbours": {"status": "placeholder", "message": "N/A in demo"},
            "recent_activity": node.get("recent_activity", []),
            "concepts": (
                {"status": "available", **node_concepts}
                if node_concepts is not None
                else {
                    "status": "placeholder",
                    "message": "Concept extraction not enabled in MVP1",
                }
            ),
        }

    @app.get("/api/workstreams/{workstream_id}/edges/{edge_id}")
    def get_workstream_edge_detail(workstream_id: str, edge_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        edge = next(
            (e for e in ws_graph.get("edges", []) if e["id"] == edge_id), None
        )
        if edge is None:
            return _ws_error(
                404,
                "EDGE_NOT_FOUND",
                f"Edge {edge_id} not found in workstream {workstream_id}",
            )
        by_id = {n["id"]: n for n in ws_graph.get("nodes", [])}
        src = by_id.get(edge["source"], {})
        tgt = by_id.get(edge["target"], {})
        findings = workstreams.load_findings(workstreams_dir, workstream_id, edge_id)
        return {
            "id": edge_id,
            "source": {
                "id": edge["source"],
                "title": src.get("title", edge["source"]),
                "node_type": src.get("node_type"),
                "document_id": src.get("document_id"),
            },
            "target": {
                "id": edge["target"],
                "title": tgt.get("title", edge["target"]),
                "node_type": tgt.get("node_type"),
                "document_id": tgt.get("document_id"),
            },
            "edge_type": edge.get("edge_type"),
            "status": "analysed" if findings is not None else "not_analysed",
            "findings": findings or [],
            # Analysable only when BOTH endpoints resolve to ingested documents
            # AND those documents differ — a doc compared against itself yields
            # no linkages (e.g. the OpRes draft node and OpRes DP node both map
            # to opres-v1-2025-draft).
            "analysable": bool(
                src.get("document_id")
                and tgt.get("document_id")
                and src.get("document_id") != tgt.get("document_id")
            ),
        }

    @app.post("/api/workstreams/{workstream_id}/nodes")
    async def create_workstream_node(workstream_id: str, request: Request) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        body = await request.json()
        if not isinstance(body, dict):
            return _ws_error(400, "EDGE_REQUIRED", "Request body must be an object")
        problem = workstreams.validate_node_create(body)
        if problem is not None:
            return _ws_error(*problem)
        node_ids = {n["id"] for n in ws_graph.get("nodes", [])}
        for edge in body["edges"]:
            if edge["target_node_id"] not in node_ids:
                return _ws_error(
                    400,
                    "INVALID_EDGE_TARGET",
                    f"Edge target {edge['target_node_id']} is not an existing node",
                )
        new_node, created = workstreams.add_node(ws_graph, body)
        workstreams.save_graph(workstreams_dir, workstream_id, ws_graph)
        return JSONResponse(
            status_code=201,
            content={
                "id": new_node["id"],
                "node_type": new_node["node_type"],
                "title": new_node["title"],
                "created_edges": [{**edge, "analysed": False} for edge in created],
            },
        )

    @app.post("/api/workstreams/{workstream_id}/edges/{edge_id}/analyze")
    def analyze_workstream_edge(workstream_id: str, edge_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        edge = next(
            (e for e in ws_graph.get("edges", []) if e["id"] == edge_id), None
        )
        if edge is None:
            return _ws_error(
                404,
                "EDGE_NOT_FOUND",
                f"Edge {edge_id} not found in workstream {workstream_id}",
            )
        by_id = {n["id"]: n for n in ws_graph.get("nodes", [])}
        src_doc = by_id.get(edge["source"], {}).get("document_id")
        tgt_doc = by_id.get(edge["target"], {}).get("document_id")
        # The source (task) node is doc_a ("ours") so silent-on / goes-beyond
        # read in the drafter's direction (task node is always the edge source).
        if not src_doc:
            return _ws_error(
                409, "NOT_ANALYSABLE",
                f"Node {edge['source']} has no ingested document to analyse.",
                field="source",
            )
        if not tgt_doc:
            return _ws_error(
                409, "NOT_ANALYSABLE",
                f"Node {edge['target']} has no ingested document to analyse.",
                field="target",
            )
        if src_doc == tgt_doc:
            # Both endpoints resolve to the same document (e.g. the OpRes draft
            # node and the OpRes DP node both map to opres-v1-2025-draft). A doc
            # compared against itself yields no linkages, so refuse rather than
            # write an empty findings file.
            return _ws_error(
                409, "NOT_ANALYSABLE",
                f"Both endpoints resolve to the same document ({src_doc}); "
                f"there is nothing to compare.",
            )
        clause_index = load_clause_index(artifacts_dir)
        try:
            result = find_connections_fn(src_doc, tgt_doc, clause_index)
        except Exception as exc:  # live model / creds / network failure
            return _ws_error(
                502, "ANALYZE_FAILED",
                f"Live analysis failed: {exc}",
            )
        findings = workstreams.connections_to_findings(result)
        # Only persist a non-empty result. Writing an empty findings file would
        # one-way-flip the edge to "analysed" (analysed is derived from file
        # presence) with zero linkages and no path back — so a no-linkage run
        # leaves the edge unanalysed and re-analysable.
        if not findings:
            return {
                "id": edge_id,
                "status": "no_linkages_found",
                "findings": [],
                "findings_count": 0,
            }
        workstreams.save_findings(workstreams_dir, workstream_id, edge_id, findings)
        return {
            "id": edge_id,
            "status": "analysed",
            "findings": findings,
            "findings_count": len(findings),
        }

    # --- Workstream Brain — Review Linkages routes -------------------------
    # The pairwise clause reader. Clause text is served from each finding's own
    # `source_clauses` / `target_clauses` records, NOT re-parsed from a clause
    # index: `data/artifacts/clause-index.json` covers only the RMiT documents,
    # so OpRes / BCBS / HKMA / FSB / FSA have no index to read. Quoting the
    # finding's own stored text keeps the verbatim guarantee intact — a finding
    # can never cite text its record does not contain.

    def _review_node(ws_graph: dict[str, Any], node_id: str) -> dict[str, Any]:
        node = next(
            (n for n in ws_graph.get("nodes", []) if n["id"] == node_id), {}
        )
        return {
            "id": node_id,
            "title": node.get("title"),
            "node_type": node.get("node_type"),
        }

    def _clause_pane(findings: list[dict[str, Any]], side: str) -> list[dict[str, Any]]:
        """The pane's clause cards: every clause cited by any finding on this
        side, de-duplicated by clause number, in first-cited order.

        A `goes-beyond` / `silent-on` finding may cite nothing on one side; it
        simply contributes no card there.
        """
        pane: list[dict[str, Any]] = []
        seen: set[str] = set()
        for finding in findings:
            for clause in finding.get(f"{side}_clauses") or []:
                number = clause.get("clause_number")
                if number is None or number in seen:
                    continue
                seen.add(number)
                pane.append({"clause_number": number, "text": clause.get("text")})
        return pane

    @app.get("/api/workstreams/{workstream_id}/edges/{edge_id}/review")
    def get_edge_review(workstream_id: str, edge_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        edge = next((e for e in ws_graph.get("edges", []) if e["id"] == edge_id), None)
        if edge is None:
            return _ws_error(
                404,
                "EDGE_NOT_FOUND",
                f"Edge {edge_id} not found in workstream {workstream_id}",
            )
        try:
            edge_findings = findings.load(workstreams_dir, workstream_id, edge_id)
        except findings.FindingsNotAnalysedError:
            # Distinct from "analysed, zero findings": the edge has never been
            # run, so the screen prompts Analyze rather than showing an empty
            # reader. `analysed` is derived from findings-file presence.
            return _ws_error(
                400,
                "EDGE_NOT_ANALYSED",
                f"Edge {edge_id} has not been analysed yet",
            )
        return {
            "edge": {
                "id": edge_id,
                "edge_type": edge.get("edge_type"),
                "source_node": _review_node(ws_graph, edge["source"]),
                "target_node": _review_node(ws_graph, edge["target"]),
            },
            "source_clauses": _clause_pane(edge_findings, "source"),
            "target_clauses": _clause_pane(edge_findings, "target"),
            "findings": edge_findings,
            "counts": findings.counts(edge_findings),
        }

    @app.patch(
        "/api/workstreams/{workstream_id}/edges/{edge_id}/findings/{finding_id}"
    )
    async def patch_finding_review_state(
        workstream_id: str, edge_id: str, finding_id: str, request: Request
    ) -> Any:
        body = await request.json()
        state = body.get("review_state") if isinstance(body, dict) else None
        if state not in findings.REVIEW_STATES:
            return _ws_error(
                400,
                "INVALID_REVIEW_STATE",
                f"review_state must be one of {sorted(findings.REVIEW_STATES)}, "
                f"got {state!r}",
            )
        try:
            updated = findings.set_review_state(
                workstreams_dir, workstream_id, edge_id, finding_id, state
            )
        except findings.FindingsNotAnalysedError:
            return _ws_error(
                400, "EDGE_NOT_ANALYSED", f"Edge {edge_id} has not been analysed yet"
            )
        except findings.FindingNotFoundError:
            return _ws_error(
                404, "FINDING_NOT_FOUND", f"Finding {finding_id} not found on {edge_id}"
            )
        all_findings = findings.load(workstreams_dir, workstream_id, edge_id)
        return {"finding": updated, "counts": findings.counts(all_findings)}

    # --- Workstream Brain — Drafting Workspace routes ----------------------
    # The editor plus its three-tab context panel. Same `{code, message}` error
    # body as above. The Copilot is a live Azure AI Foundry Claude call (see
    # `engine/copilot.py`) with a deterministic citation guardrail — every
    # citation it returns is re-quoted from already-verbatim clause/finding
    # text, never trusted from the model's own echo.

    def _task_node(
        ws_graph: dict[str, Any], workstream_id: str, node_id: str
    ) -> Union[dict[str, Any], JSONResponse]:
        """The node, or the error response for "not a task"/"not found"."""
        node = next(
            (n for n in ws_graph.get("nodes", []) if n["id"] == node_id), None
        )
        if node is None or node.get("node_type") != "task":
            # One code for both: the workspace is only ever reached from a task,
            # so a caller asking for a draft of an anchor node and a caller
            # asking for a draft of nothing are equally out of contract.
            return _ws_error(
                404,
                "TASK_NOT_FOUND",
                f"Node {node_id} is not a task node in workstream {workstream_id}"
                if node is not None
                else f"Task {node_id} not found in workstream {workstream_id}",
            )
        return node

    def _linkage_card(
        finding: dict[str, Any], edge: dict[str, Any], ws_graph: dict[str, Any]
    ) -> dict[str, Any]:
        """Project a finding onto the side panel's card shape.

        Only `clause_number`s travel, not clause text: the cards are references
        into the reader, and the drafter clicks through to the review screen for
        the full quotation. Nothing here is a citation, so nothing here can
        misquote.
        """
        source_clauses = finding.get("source_clauses") or []
        target_clauses = finding.get("target_clauses") or []
        return {
            "id": finding["id"],
            "label": finding.get("label"),
            "sentiment": finding.get("sentiment"),
            "summary": finding.get("summary"),
            "edge_id": edge["id"],
            "left": _review_node(ws_graph, edge["source"]),
            "right": _review_node(ws_graph, edge["target"]),
            "source_clause_number": (
                source_clauses[0].get("clause_number") if source_clauses else None
            ),
            "target_clause_number": (
                target_clauses[0].get("clause_number") if target_clauses else None
            ),
        }

    @app.get("/api/workstreams/{workstream_id}/tasks/{node_id}/reviewed-linkages")
    def get_reviewed_linkages(workstream_id: str, node_id: str) -> Any:
        """Accepted findings across every edge incident to the task.

        Filtered server-side, per the spec's negative constraint: the Reviewed
        tab must not receive dismissed findings and filter them away in the
        browser.
        """
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        node = _task_node(ws_graph, workstream_id, node_id)
        if isinstance(node, JSONResponse):
            return node

        cards: list[dict[str, Any]] = []
        for edge in ws_graph.get("edges", []):
            if node_id not in (edge.get("source"), edge.get("target")):
                continue
            try:
                edge_findings = findings.load(workstreams_dir, workstream_id, edge["id"])
            except findings.FindingsNotAnalysedError:
                continue  # unanalysed edge — nothing to have accepted yet
            cards.extend(
                _linkage_card(f, edge, ws_graph)
                for f in edge_findings
                if f["review_state"] == "accepted"
            )
        return {"findings": cards}

    @app.get("/api/workstreams/{workstream_id}/tasks/{node_id}/related-linkages")
    def get_related_linkages(workstream_id: str, node_id: str, hops: int = 1) -> Any:
        """Findings on edges between the task's neighbours themselves.

        Peer context: what the anchors already say about each other, useful when
        the draft is silent on a concept the neighbours have settled. Bounded at
        exactly 1 hop — `hops` is validated rather than ignored so a caller who
        asks for 2 learns it is unsupported instead of silently getting 1.
        """
        if hops != 1:
            return _ws_error(
                400, "HOPS_OUT_OF_RANGE", f"Only hops=1 is supported, got {hops}"
            )
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        node = _task_node(ws_graph, workstream_id, node_id)
        if isinstance(node, JSONResponse):
            return node

        all_edges = ws_graph.get("edges", [])
        neighbours = set(workstreams.neighbour_ids(all_edges, node_id))
        peer_edges = workstreams.edges_between(all_edges, neighbours, exclude_node=node_id)

        cards: list[dict[str, Any]] = []
        for edge in peer_edges:
            try:
                edge_findings = findings.load(workstreams_dir, workstream_id, edge["id"])
            except findings.FindingsNotAnalysedError:
                continue
            cards.extend(_linkage_card(f, edge, ws_graph) for f in edge_findings)
        return {"findings": cards}

    @app.get("/api/workstreams/{workstream_id}/tasks/{node_id}/draft")
    def get_draft(workstream_id: str, node_id: str) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        node = _task_node(ws_graph, workstream_id, node_id)
        if isinstance(node, JSONResponse):
            return node
        return drafts.load(workstreams_dir, workstream_id, node_id)

    @app.put("/api/workstreams/{workstream_id}/tasks/{node_id}/draft")
    async def put_draft(workstream_id: str, node_id: str, request: Request) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        node = _task_node(ws_graph, workstream_id, node_id)
        if isinstance(node, JSONResponse):
            return node
        body = await request.json()
        content_html = body.get("content_html") if isinstance(body, dict) else None
        if not isinstance(content_html, str):
            return _ws_error(
                400, "INVALID_HTML", "content_html must be a string"
            )
        try:
            return drafts.save(workstreams_dir, workstream_id, node_id, content_html)
        except drafts.DraftTooLargeError:
            return _ws_error(
                413,
                "DRAFT_TOO_LARGE",
                f"Draft exceeds {drafts.MAX_DRAFT_BYTES} bytes after sanitization",
            )
        except drafts.DraftEmptyError:
            return _ws_error(
                400,
                "INVALID_HTML",
                "Nothing survived sanitization — no allowed content in payload",
            )

    @app.post("/api/workstreams/{workstream_id}/tasks/{node_id}/copilot")
    async def post_copilot(workstream_id: str, node_id: str, request: Request) -> Any:
        ws_graph = workstreams.load_graph(workstreams_dir, workstream_id)
        if ws_graph is None:
            return _ws_error(
                404, "WORKSTREAM_NOT_FOUND", f"Workstream {workstream_id} not found"
            )
        node = _task_node(ws_graph, workstream_id, node_id)
        if isinstance(node, JSONResponse):
            return node
        body = await request.json() if await request.body() else {}
        if not isinstance(body, dict):
            body = {}
        intent = body.get("intent")
        if intent not in copilot.INTENTS:
            return _ws_error(
                400,
                "INVALID_INTENT",
                f"intent must be one of {list(copilot.INTENTS)}, got {intent!r}",
            )
        message = body.get("message")
        if not isinstance(message, str) or not message.strip():
            return _ws_error(
                400, "MESSAGE_REQUIRED", "message must be a non-empty string"
            )
        # The server holds no conversation state (the chat is deliberately not
        # persisted across sessions) — the client sends the full prior history
        # on every call.
        history = body.get("history") or []
        if not isinstance(history, list):
            history = []
        referenced_finding_ids = body.get("referenced_finding_ids") or []
        if not isinstance(referenced_finding_ids, list):
            referenced_finding_ids = []

        clause_index = load_clause_index(artifacts_dir)
        try:
            reply = copilot_reply_fn(
                node=node,
                intent=intent,
                history=history,
                message=message,
                referenced_finding_ids=referenced_finding_ids,
                clause_index=clause_index,
                workstreams_dir=workstreams_dir,
                workstream_id=workstream_id,
            )
        except Exception as exc:  # live model / creds / network failure
            return _ws_error(
                502, "COPILOT_FAILED", f"Live Copilot call failed: {exc}"
            )
        return {"reply": reply}

    return app


def _build_default_app() -> FastAPI:
    """Construct the real app for `uvicorn engine.api:app`.

    Needs nothing on disk to start: a missing/empty `data/workstreams/` simply
    means the routes report 404 WORKSTREAM_NOT_FOUND rather than crashing.
    """
    return create_app()


app = _build_default_app()
