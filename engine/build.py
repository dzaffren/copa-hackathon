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
from pathlib import Path
from typing import Any, Callable, Optional, Union, cast

from engine.clauses import (
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
            "edges referencing an excluded policy are dropped for the run."
        ),
    )
    args = parser.parse_args()

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

    run_build(
        documents=cast(dict[str, dict[str, Any]], documents),
        curated_edges=curated_edges,
        draft_registry=draft_registry,
        output_dir=REPO_ROOT / "data" / "artifacts",
        reference_documents=cast(
            dict[str, dict[str, Any]], reference_documents
        ),
        reference_edges=reference_edges,
    )
    logger.info("build complete → %s", REPO_ROOT / "data" / "artifacts")


if __name__ == "__main__":
    main()
