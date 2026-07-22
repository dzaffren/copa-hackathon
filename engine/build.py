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

from engine.anchors import (
    Anchor,
    AnchorIndex,
    SegmenterRegistry,
    _REGISTRY as _DEFAULT_ANCHOR_REGISTRY,
    prose_segment,
    semi_structured_segment,
    structured_rules_segment,
    verify_substring,
)
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
        (ingest_debug_dir / f"{document_id}.md").write_text(markdown, encoding="utf-8")
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


# ---------------------------------------------------------------------------
# Task 7: anchor-index build pipeline.
#
# Reads `data/corpus/manifest.json`, dispatches each `in_mvp1: true` document
# through the doc_class-appropriate segmenter (registered on
# `engine.anchors._REGISTRY`), unions the anchors into one `AnchorIndex`, and
# writes `data/artifacts/anchor-index.json` as a list of Anchor dicts (the
# shape `AnchorIndex(json.loads(...))` consumes for a straight round-trip).
#
# Failure handling is loud-but-tolerant per the spec: a missing source_path is
# a WARNING + skip, a segmenter crash is an ERROR + skip. Only a
# verify_substring failure (an anchor whose text is NOT a substring of the
# source) aborts the build — that's the verbatim-citation guardrail the whole
# KG engine relies on and must never silently pass.


# Per-document_id override map for structured-rules documents whose manifest
# `document_id` cannot be derived to a POLICY_SHORT_NAMES key by the token
# heuristic below (e.g. `bnm-ai-financial-sector-dp` → `ai-dp`).
_STRUCTURED_RULES_KEY_OVERRIDE: dict[str, str] = {
    "bnm-ai-financial-sector-dp": "ai-dp",
    "bnm-operational-resilience-dp-dec2025": "opres",
    "bnm-rmit-nov25": "rmit",
    "bnm-rmit-june2023": "rmit",
    "bnm-outsourcing-2019": "outsourcing",
    "bnm-bcm-pd": "bcm",
    "bnm-recovery-planning-pd": "recovery-planning",
}


def _derive_structured_rules_key(document_id: str) -> Optional[str]:
    """Best-effort derivation of a POLICY_SHORT_NAMES key from a manifest
    document_id.

    The structured-rules segmenter expects its `document_id` argument to be a
    key in `engine.clauses.POLICY_SHORT_NAMES` (e.g. `"rmit"`, `"outsourcing"`).
    Manifest ids are richer (`"bnm-rmit-nov25"`, `"bnm-outsourcing-2019"`), so
    we first consult a hand-curated override table, then fall back to
    tokenising the manifest id and looking for a POLICY_SHORT_NAMES key that
    appears as a token — longest key first so `"recovery-planning"` beats
    `"recovery"` if both were registered. Returns `None` when no key matches;
    the caller logs and skips.
    """
    if document_id in POLICY_SHORT_NAMES:
        return document_id
    if document_id in _STRUCTURED_RULES_KEY_OVERRIDE:
        return _STRUCTURED_RULES_KEY_OVERRIDE[document_id]
    tokens = document_id.replace("_", "-").split("-")
    token_set = set(tokens)
    for key in sorted(POLICY_SHORT_NAMES, key=len, reverse=True):
        # Match either the whole key as a token, or the key as a hyphenated
        # substring of the id — covers `"recovery-planning"` inside
        # `"bnm-recovery-planning-pd"`.
        if key in token_set:
            return key
        if key in document_id and "-" in key:
            return key
    return None


# Per-document_id shortname overrides for the 25 MVP1 manifest entries — used
# when two documents from the same issuer would otherwise collide on an issuer
# prefix (e.g. both BIS papers producing "BIS 1"). Keyed by manifest
# `document_id`; entries without an override fall back to the issuer mapping.
_SHORTNAME_BY_DOCUMENT_ID: dict[str, str] = {
    "bis-d575-digitalisation": "BIS d575",
    "bis-pap168-open-finance": "BIS Pap168",
    "hkma-open-api-framework-2018": "HKMA OpenAPI",
    "hkma-open-api-next-phase": "HKMA OpenAPI NextPhase",
    "mas-abs-api-playbook": "ABS-MAS Playbook",
    "cma-open-banking-roadmap-may2020": "CMA Roadmap",
    "cma-retail-banking-final-report-summary": "CMA Retail Banking",
    "bnm-open-api-bulletin": "BNM OpenAPI Bulletin",
}

# A tiny mapping from manifest issuer to a shortname used as the anchor_id
# prefix for semi-structured / prose segmenters when no per-document override
# applies. Keyed by manifest `issuer`.
_SHORTNAME_BY_ISSUER: dict[str, str] = {
    "MAS": "MAS",
    "Bank of England": "BoE",
    "BCBS": "BCBS",
    "BIS": "BIS",
    "HKMA": "HKMA",
    "CMA": "CMA",
    "BNM": "BNM",
}


def _derive_shortname(entry: dict[str, Any]) -> str:
    """Return the anchor_id prefix for a semi-structured / prose entry.

    Preference order: explicit `shortname` on the manifest entry →
    per-document_id override → derived from issuer → `document_id` (fallback).
    Never returns an empty string.
    """
    explicit = entry.get("shortname")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    document_id = entry.get("document_id", "")
    if document_id in _SHORTNAME_BY_DOCUMENT_ID:
        return _SHORTNAME_BY_DOCUMENT_ID[document_id]
    issuer = entry.get("issuer")
    if isinstance(issuer, str) and issuer in _SHORTNAME_BY_ISSUER:
        return _SHORTNAME_BY_ISSUER[issuer]
    return document_id


def build_anchor_index(
    manifest_path: Path,
    artifacts_dir: Path,
    ingest_fn: IngestFn = ingest_document,
    repo_root: Optional[Path] = None,
    segmenter_registry: Optional[SegmenterRegistry] = None,
    require_source_exists: bool = True,
) -> AnchorIndex:
    """Read the corpus manifest, segment every in_mvp1 document, write
    `anchor-index.json`, and return the constructed `AnchorIndex`.

    Args:
        manifest_path: path to `data/corpus/manifest.json`.
        artifacts_dir: directory to write `anchor-index.json` into.
        ingest_fn: PDF-to-markdown seam (defaults to
            `engine.ingest.ingest_document`; tests inject a stub).
        repo_root: root against which each entry's `source_path` is resolved.
            Defaults to `manifest_path.parent.parent.parent` — i.e. the repo
            containing `data/corpus/manifest.json`.
        segmenter_registry: dispatch table for `doc_class -> segmenter fn`.
            Defaults to the module-level registry in `engine.anchors`.
        require_source_exists: when True (production default), missing source
            files are WARNed and skipped; when False, `ingest_fn` is called
            unconditionally (useful for stubbed-ingest tests).

    Returns the freshly-built AnchorIndex. Also writes the JSON artifact.
    """
    registry = (
        segmenter_registry
        if segmenter_registry is not None
        else _DEFAULT_ANCHOR_REGISTRY
    )
    resolved_root = (
        repo_root
        if repo_root is not None
        else manifest_path.resolve().parent.parent.parent
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("documents", [])

    all_anchors: list[Anchor] = []
    seen_ids: set[str] = set()
    kept = 0
    skipped = 0
    for entry in entries:
        document_id = entry.get("document_id", "<unknown>")
        if not entry.get("in_mvp1"):
            logger.info("skipping %s: in_mvp1=false", document_id)
            skipped += 1
            continue

        source_path = resolved_root / entry["source_path"]
        if require_source_exists and not source_path.exists():
            logger.warning(
                "skipping %s: source_path %s not on disk",
                document_id,
                source_path,
            )
            skipped += 1
            continue

        doc_class = entry["doc_class"]
        segmenter_fn = registry.get(doc_class)
        if segmenter_fn is None:
            logger.error(
                "skipping %s: no segmenter registered for doc_class %r",
                document_id,
                doc_class,
            )
            skipped += 1
            continue

        try:
            markdown = ingest_fn(source_path)
        except Exception as exc:  # pragma: no cover - ingest error is per-doc
            logger.error("skipping %s: ingest failed (%s)", document_id, exc)
            skipped += 1
            continue

        # Build the call the segmenter expects for its doc_class. Only the
        # structured-rules strategy is picky about its `document_id` argument
        # (must be a POLICY_SHORT_NAMES key); the semi-structured / prose
        # strategies accept the manifest id as-is plus a shortname kwarg.
        # A caller-supplied registry always wins — tests inject custom
        # segmenters to exercise the guardrail; production routes through the
        # default registry via the doc_class-specific helpers below.
        try:
            if segmenter_registry is not None:
                anchors = segmenter_fn(document_id, markdown)
            elif doc_class == "structured-rules":
                key = _derive_structured_rules_key(document_id)
                if key is None:
                    logger.error(
                        "skipping %s: no POLICY_SHORT_NAMES key can be derived "
                        "(add one to engine.clauses.POLICY_SHORT_NAMES or use a "
                        "different doc_class)",
                        document_id,
                    )
                    skipped += 1
                    continue
                anchors = structured_rules_segment(key, markdown)
                # Re-tag document_id back to the manifest id so callers can
                # look up anchors by the same id the manifest declares.
                for anchor in anchors:
                    anchor["document_id"] = document_id
            elif doc_class == "semi-structured":
                shortname = _derive_shortname(entry)
                anchors = semi_structured_segment(
                    document_id, markdown, shortname=shortname
                )
            elif doc_class == "prose":
                shortname = _derive_shortname(entry)
                anchors = prose_segment(document_id, markdown, shortname=shortname)
            else:
                # Unknown class handled by an ad-hoc registered segmenter.
                anchors = segmenter_fn(document_id, markdown)
        except Exception as exc:
            # Anchor-text-not-found bubbles up — that's the guardrail. All
            # other segmenter errors are per-doc failures: log + skip.
            from engine.anchors import AnchorTextNotFoundError

            if isinstance(exc, AnchorTextNotFoundError):
                raise
            logger.error(
                "skipping %s: segmenter (%s) crashed: %s",
                document_id,
                doc_class,
                exc,
            )
            skipped += 1
            continue

        # Belt-and-braces substring check — every registered strategy already
        # calls verify_substring internally, but a custom test registry might
        # not, so we re-verify here. Cheap: substring test is O(n).
        for anchor in anchors:
            verify_substring(anchor, markdown)

        # Two manifest entries can legitimately share a shortname (e.g. two
        # RMiT versions both mapping to "rmit"): the second run's clause IDs
        # collide with the first. Drop the collisions with a WARNING rather
        # than let `AnchorIndex(...)` raise — the first winner is the earlier
        # manifest entry, which matches the manifest's insertion order.
        deduped: list[Anchor] = []
        for anchor in anchors:
            aid = anchor["anchor_id"]
            if aid in seen_ids:
                logger.warning(
                    "dropping duplicate anchor_id %r from %s (already emitted "
                    "by an earlier manifest entry — likely two documents share "
                    "a shortname; disambiguate via shortname or per-document override)",
                    aid,
                    document_id,
                )
                continue
            seen_ids.add(aid)
            deduped.append(anchor)

        all_anchors.extend(deduped)
        kept += 1

    index = AnchorIndex(all_anchors)

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifacts_dir / "anchor-index.json"
    # List-of-anchors shape — the ctor consumes this directly on reload.
    out_path.write_text(
        json.dumps(index.all(), indent=2, sort_keys=False),
        encoding="utf-8",
    )
    logger.info(
        "Wrote %d anchors from %d documents (skipped %d) to %s",
        len(index),
        kept,
        skipped,
        out_path,
    )
    return index


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
    parser.add_argument(
        "--with-anchors",
        action="store_true",
        help=(
            "In addition to (or instead of) the legacy clause-index build, "
            "read data/corpus/manifest.json and produce "
            "data/artifacts/anchor-index.json."
        ),
    )
    parser.add_argument(
        "--anchors-only",
        action="store_true",
        help=(
            "Only run the anchor-index build; skip the legacy clause-index / "
            "graph / verdicts pipeline entirely."
        ),
    )
    args = parser.parse_args()

    if args.merge and not args.docs:
        parser.error(
            "--merge only makes sense with --docs (a full build has nothing to merge into)"
        )

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

    artifacts_dir = REPO_ROOT / "data" / "artifacts"

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

    if not args.anchors_only:
        draft_registry_path = REPO_ROOT / "data" / "draft_registry.json"
        draft_registry = json.loads(draft_registry_path.read_text())

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
            reference_documents=cast(dict[str, dict[str, Any]], reference_documents),
            reference_edges=reference_edges,
        )

        if args.merge:
            try:
                added = _merge_clause_index(build_dir, output_dir)
            except ValueError as exc:
                # A refused merge is a normal outcome the operator has to act on
                # (rebuild fully, or drop the already-indexed document), not a
                # crash. The built artifacts stay in scratch; nothing was written.
                raise SystemExit(
                    f"{exc}\n(nothing was written to {output_dir})"
                ) from None
            logger.info(
                "merged %d clause(s) into %s (graph.json left alone — a subset "
                "graph is not mergeable)",
                added,
                output_dir / "clause-index.json",
            )
        logger.info("build complete → %s", output_dir)

    if args.with_anchors or args.anchors_only:
        manifest_path = REPO_ROOT / "data" / "corpus" / "manifest.json"
        build_anchor_index(
            manifest_path=manifest_path,
            artifacts_dir=artifacts_dir,
        )
        logger.info("anchor-index build complete → %s", artifacts_dir)


if __name__ == "__main__":
    main()
