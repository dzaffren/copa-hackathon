"""CLI entrypoint wiring stages 1-3: ingest -> segment clauses -> build graph.

Run as ``python -m engine.build``. Reads the locked demo cluster from
`engine.config.DOCUMENTS`, converts each document to clean markdown (stage 1,
`engine.ingest.ingest_document`), segments it into a clause index (stage 2,
`engine.clauses.segment_clauses` + `merge_clause_indexes`), then assembles the
knowledge graph (stage 3, `engine.graph.build_graph`) and writes the artifacts
to `data/artifacts/` (`clause-index.json`, `graph.json`, and the
human-review `dropped-clauses.json`).

Stage 2 is now the **deterministic** rule-primary segmenter (`segment_clauses`)
— it finds clause boundaries directly by regex over the clean markdown and
needs no LLM or credentials, so a full build runs offline and produces
byte-stable artifacts (freeze-as-fixtures). `run_build` still exposes
`ingest_fn`/`segment_fn` as injectable seams for tests (matching the no-network
discipline in engine/tests/), and stage 1 (MarkItDown + Azure Document
Intelligence) is the only part that reaches the network, at ingest time.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional, Union, cast

from engine.anchors import AnchorIndex, verify_substring
from engine.anchors_bnm import structured_rules_segment
from engine.anchors_llm import BoundaryFn, llm_boundary_segment
from engine.clauses import (
    POLICY_SHORT_NAMES,
    ClauseEntry,
    ClauseIndex,
    build_reference_clause,
    merge_clause_indexes,
    segment_clauses,
)
from engine.graph import build_graph
from engine.ingest import ingest_document, normalise_glyph_artifacts

logger = logging.getLogger(__name__)

IngestFn = Callable[[Union[str, Path]], str]
# Stage 2 seam: (markdown, document_id, policy_id, source, dropped_report)
# -> per-document clause entries. Defaults to the deterministic segmenter.
SegmentFn = Callable[..., dict[str, ClauseEntry]]


def run_build(
    documents: dict[str, dict[str, Any]],
    curated_edges: list[dict[str, Any]],
    draft_registry: dict[str, Any],
    output_dir: Path,
    ingest_fn: IngestFn = ingest_document,
    segment_fn: SegmentFn = segment_clauses,
    reference_documents: Optional[dict[str, dict[str, Any]]] = None,
    reference_edges: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Run stages 1-3 and write `clause-index.json` + `graph.json`.

    Args:
        documents: the document manifest, shaped like `engine.config.DOCUMENTS`.
        curated_edges: shaped like `engine.config.CURATED_SEED_EDGES`.
        draft_registry: `{"live_drafts": [policy_id, ...]}`.
        output_dir: directory to write the two artifacts into (created if
            it does not exist).
        ingest_fn: stage 1 — converts a source path to markdown. Defaults
            to `engine.ingest.ingest_document`; tests inject a stub.
        segment_fn: stage 2 — deterministically segments a document's clean
            markdown into clause entries. Defaults to
            `engine.clauses.segment_clauses` (rule-primary, network-free — no
            Azure Foundry credentials needed); tests may inject a stub.
    """
    # The last document declared for a policy_id is its current version —
    # the version_lineage/status rules in graph.py rely on this same
    # ordering, so stage 2 uses it too when picking the primary-index winner.
    current_document_id_by_policy: dict[str, str] = {}
    for document_id, doc in documents.items():
        current_document_id_by_policy[doc["policy_id"]] = document_id

    document_entries: list[tuple[str, dict]] = []
    # "Flag for human review": every anchor the parser cannot place is collected
    # here (rather than only logged) and written to dropped-clauses.json, so a
    # reviewer sees exactly which clauses fell out and why.
    dropped_report: list[dict[str, Any]] = []
    for n, (document_id, doc) in enumerate(documents.items(), start=1):
        logger.info(
            "[%d/%d] ingesting %s (%s)",
            n,
            len(documents),
            document_id,
            doc["source_path"],
        )
        markdown = ingest_fn(doc["source_path"])
        # DP-specific glyph repair, gated on the manifest flag: the vehicle
        # document's stylised "AI" logotype is mis-read as "Al"/"$A l$"/"GenAl";
        # `normalise_glyph_artifacts` fixes only those self-contained patterns and
        # runs BEFORE segmentation, so every sliced clause text is the corrected,
        # verbatim source. It is NOT applied globally — the bare Al→AI rule must
        # not touch other corpus PDFs (see engine/config.py `normalise_glyphs`).
        if doc.get("normalise_glyphs"):
            markdown = normalise_glyph_artifacts(markdown)
        # Diagnostic: dump the raw ingested markdown so we can inspect exactly
        # what stage-1 (Document Intelligence / MarkItDown) produced for each
        # document — the ground truth for any "clause X is missing" question
        # (is it garbled, renumbered, or absent from the source text?). Written
        # under _ingest/ so it is clearly a debug artifact, not part of the
        # frozen contract.
        ingest_debug_dir = output_dir / "_ingest"
        ingest_debug_dir.mkdir(parents=True, exist_ok=True)
        # Explicit UTF-8: the vehicle DP's markdown contains non-cp1252 glyphs
        # (e.g. the Unicode minus U+2212), which the platform-default encoding on
        # Windows cannot write. All artifact writes must be UTF-8 for the offline
        # build to run cross-platform.
        (ingest_debug_dir / f"{document_id}.md").write_text(
            markdown, encoding="utf-8"
        )
        logger.info("[%d/%d] parsing clauses for %s", n, len(documents), document_id)
        entries = segment_fn(
            markdown,
            document_id,
            doc["policy_id"],
            doc["source"],
            dropped_report=dropped_report,
        )
        logger.info(
            "[%d/%d] %s → %d clauses", n, len(documents), document_id, len(entries)
        )
        document_entries.append((document_id, entries))

    entries_by_policy: dict[str, list[tuple[str, dict]]] = {}
    for document_id, entries in document_entries:
        policy_id = documents[document_id]["policy_id"]
        entries_by_policy.setdefault(policy_id, []).append((document_id, entries))

    primary: dict[str, Any] = {}
    versions: dict[str, dict] = {}
    for policy_id, entries_for_policy in entries_by_policy.items():
        policy_primary, policy_versions = merge_clause_indexes(
            entries_for_policy,
            current_document_id=current_document_id_by_policy[policy_id],
        )
        primary.update(policy_primary)
        versions.update(policy_versions)

    # External reference passages (#26): each PUBLIC reference contributes ONE
    # verbatim clause (keyed like "PDPA 129") into the same index; restricted
    # (handbook) and preview (trend) references have no passage and are node-only
    # — nothing is ingested for them, so there is no confidential text to serve.
    # A reference clause is looked up by GET /clauses/{n} identically to a policy
    # clause.
    reference_documents = reference_documents or {}
    for ref_id, ref in reference_documents.items():
        # A reference may carry a single `passage`/`anchor`/`heading` (the #26
        # form) OR a `passages` list of {anchor, heading, passage} for a source
        # cited at more than one clause (e.g. BCBS 239 at P3 and P4) — one graph
        # node, several verbatim clauses. Node-only references (restricted
        # handbook, preview trend, blocked sources) carry neither and are skipped.
        if "passages" in ref:
            passage_specs = ref["passages"]
        elif "passage" in ref:
            passage_specs = [
                {
                    "anchor": ref["anchor"],
                    "heading": ref.get("heading"),
                    "passage": ref["passage"],
                }
            ]
        else:
            continue  # node-only — nothing ingested
        for spec in passage_specs:
            ref_clause = build_reference_clause(
                document_id=ref_id,
                policy_id=ref["policy_id"],
                anchor=spec["anchor"],
                heading=spec.get("heading"),
                text=spec["passage"],
            )
            for clause_number, entry in ref_clause.items():
                primary[clause_number] = entry
                versions.setdefault(clause_number, {})[ref_id] = entry

    clause_index = ClauseIndex(primary, versions)

    # Persist the clause index (and the human-review drop list) BEFORE building
    # the graph. Parsing and graph-assembly are separate concerns: a graph-config
    # error (e.g. a curated edge citing a clause that does not resolve) must not
    # discard the successfully-parsed clauses — they are needed both downstream
    # and to look up the real clause numbers when correcting such a config error.
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "clause-index.json").write_text(
        json.dumps(primary, indent=2, sort_keys=True)
    )
    # The human-review flag list: which anchors the parser dropped and why.
    # Sorted for a deterministic, diffable artifact (freeze-as-fixtures).
    dropped_report.sort(
        key=lambda d: (d.get("document_id") or "", d.get("clause_number") or "")
    )
    (output_dir / "dropped-clauses.json").write_text(
        json.dumps(dropped_report, indent=2)
    )
    logger.info(
        "%d clause(s) parsed → %s; %d dropped for review → %s",
        len(primary),
        output_dir / "clause-index.json",
        len(dropped_report),
        output_dir / "dropped-clauses.json",
    )

    graph = build_graph(
        documents={**documents, **reference_documents},
        curated_edges=curated_edges,
        clause_index=clause_index,
        draft_registry=draft_registry,
        reference_edges=reference_edges,
    )
    (output_dir / "graph.json").write_text(json.dumps(graph, indent=2))

    # Stage 4b (verdict pass) was removed with the reconciliation-workbench read
    # path: it wrote `verdicts.json`, whose only consumers were `engine.read_model`
    # and `scripts/export_poc_snapshot.py`. Both are gone, and the artifact was
    # never committed. The five-label taxonomy that replaced it lives in
    # `engine.connections` and is recorded via `scripts/run_finder_trace.py`.



def build_anchor_index(
    documents: dict[str, dict[str, Any]],
    *,
    ingest_fn: IngestFn = ingest_document,
    boundary_fn: Optional[BoundaryFn] = None,
    output_dir: Optional[Path] = None,
) -> AnchorIndex:
    """Segment every document via its declared segmenter_class strategy into a
    single AnchorIndex, running verify_substring on every anchor, and (if
    output_dir) write anchor-index.json. BNM docs (segmenter_class ==
    "structured-rules") use the deterministic lane; legislative/framework/prose
    docs use the LLM-boundary lane.
    """
    all_anchors = []
    for document_id, doc in documents.items():
        markdown = ingest_fn(doc["source_path"])
        segmenter_class = doc["segmenter_class"]
        if segmenter_class == "structured-rules":
            anchors = structured_rules_segment(
                document_id, markdown,
                policy_id=doc["policy_id"], source=str(doc["source_path"]))
        else:
            shortname = doc.get("shortname") or POLICY_SHORT_NAMES.get(
                doc["policy_id"], doc["policy_id"])
            anchors = llm_boundary_segment(
                document_id, markdown, doc_class=segmenter_class,
                shortname=shortname, boundary_fn=boundary_fn)
        for anchor in anchors:
            verify_substring(anchor, markdown)
        all_anchors.extend(anchors)

    index = AnchorIndex(all_anchors)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "anchor-index.json").write_text(
            json.dumps(all_anchors, indent=2, ensure_ascii=False),
            encoding="utf-8")
    return index


def _merge_clause_index(built_dir: Path, target_dir: Path) -> int:
    """Merge a freshly-built clause index INTO an existing one. Returns the count added.

    Refuses on any key collision rather than picking a winner. Two documents
    claiming the same clause number is either a real conflict (the same policy
    rebuilt — use a full build) or a namespace bug; silently letting the newer
    one win is how a "recovery" quietly rewrites clauses that other committed
    traces already cite.

    Only `clause-index.json` merges. `graph.json` is left alone deliberately: a
    subset graph is not a subset of the full graph — its edges were validated
    against a partial document set — so grafting it in would produce a graph
    that never existed.
    """
    built_path = built_dir / "clause-index.json"
    target_path = target_dir / "clause-index.json"
    built = json.loads(built_path.read_text(encoding="utf-8"))
    if not target_path.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(built, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return len(built)

    existing = json.loads(target_path.read_text(encoding="utf-8"))
    collisions = sorted(set(existing) & set(built))
    if collisions:
        raise ValueError(
            f"--merge refuses to overwrite {len(collisions)} existing clause(s): "
            f"{collisions[:5]}{' …' if len(collisions) > 5 else ''}. These documents "
            f"are already indexed; a rebuild of them needs a full build, not a merge."
        )
    merged = {k: v for k, v in sorted({**existing, **built}.items())}
    target_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return len(built)


def main() -> None:
    import argparse

    from engine.config import (
        CURATED_SEED_EDGES,
        DOCUMENTS,
        REFERENCE_DOCUMENTS,
        REFERENCE_SEED_EDGES,
        REPO_ROOT,
    )

    parser = argparse.ArgumentParser(
        description="Build the clause index + knowledge graph from the corpus."
    )
    parser.add_argument(
        "--docs",
        nargs="+",
        metavar="DOCUMENT_ID",
        help=(
            "Build only these document ids (space-separated). Useful for "
            "testing one document end-to-end before the full corpus. Curated "
            "edges referencing an excluded policy are dropped for the run. "
            "WARNING: on its own this REPLACES the clause index with just "
            "these documents — pass --merge to add them instead."
        ),
    )
    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        help=(
            "Write artifacts here instead of data/artifacts/. Use a scratch "
            "directory to inspect a build before it touches the committed one."
        ),
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help=(
            "Merge the built clause index INTO the existing one instead of "
            "replacing it, and refuse if any clause number would be "
            "overwritten. Use with --docs: a subset build otherwise drops "
            "every document it did not build."
        ),
    )
    args = parser.parse_args()

    if args.merge and not args.docs:
        parser.error("--merge only makes sense with --docs (a full build has nothing to merge into)")

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    documents: dict[str, Any] = dict(DOCUMENTS)
    curated_edges: list[dict[str, Any]] = list(
        cast(list[dict[str, Any]], CURATED_SEED_EDGES)
    )
    reference_documents: dict[str, Any] = dict(REFERENCE_DOCUMENTS)
    reference_edges: list[dict[str, Any]] = list(
        cast(list[dict[str, Any]], REFERENCE_SEED_EDGES)
    )

    if args.docs:
        unknown = [d for d in args.docs if d not in documents]
        if unknown:
            parser.error(f"unknown document id(s): {unknown}")
        documents = {d: documents[d] for d in args.docs}
        # Drop curated edges whose endpoints reference an excluded policy, so
        # a partial build doesn't KeyError / fail graph validation on absent
        # documents. The full-corpus run keeps every curated edge.
        kept_policies = {doc["policy_id"] for doc in documents.values()}
        curated_edges = [
            e
            for e in curated_edges
            if e["source_policy_id"] in kept_policies
            and e["target_policy_id"] in kept_policies
        ]
        logger.info("building subset: %s", ", ".join(documents))
        # A subset build omits the external references — their edges originate
        # from the rmit draft and would dangle if rmit or a target is excluded.
        reference_documents = {}
        reference_edges = []

    draft_registry_path = REPO_ROOT / "data" / "draft_registry.json"
    draft_registry = json.loads(draft_registry_path.read_text())

    default_dir = REPO_ROOT / "data" / "artifacts"
    output_dir = Path(args.output_dir) if args.output_dir else default_dir

    # A subset build writes only what it built. Writing that straight over
    # data/artifacts/ silently deletes every other document's clauses — which
    # is precisely what #34 did (7 documents → 2, two traces orphaned, suite
    # still green). Warn on the way in; --merge is the safe path.
    if args.docs and not args.merge and output_dir == default_dir:
        logger.warning(
            "REPLACING %s with a %d-document subset — every other document's "
            "clauses will be dropped. Pass --merge to add instead, or "
            "--output-dir to write elsewhere. See "
            "docs/learnings/blocker-engine-build-silently-narrows-artifacts.md",
            output_dir,
            len(documents),
        )

    build_dir = output_dir
    if args.merge:
        # Build into scratch first, then merge, so a failed build cannot leave
        # the committed index half-written.
        merge_scratch = tempfile.mkdtemp(prefix="engine-build-merge-")
        build_dir = Path(merge_scratch)

    run_build(
        documents=cast(dict[str, dict[str, Any]], documents),
        curated_edges=curated_edges,
        draft_registry=draft_registry,
        output_dir=build_dir,
        reference_documents=cast(
            dict[str, dict[str, Any]], reference_documents
        ),
        reference_edges=reference_edges,
    )

    if args.merge:
        try:
            added = _merge_clause_index(build_dir, output_dir)
        except ValueError as exc:
            # A refused merge is a normal outcome the operator has to act on
            # (rebuild fully, or drop the already-indexed document), not a
            # crash. The built artifacts stay in scratch; nothing was written.
            raise SystemExit(f"{exc}\n(nothing was written to {output_dir})") from None
        logger.info(
            "merged %d clause(s) into %s (graph.json left alone — a subset "
            "graph is not mergeable)",
            added,
            output_dir / "clause-index.json",
        )
    logger.info("build complete → %s", output_dir)


if __name__ == "__main__":
    main()
