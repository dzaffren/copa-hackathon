"""A/B the finder prompts' phrasing: old prompt vs new plain-language prompt.

Verification helper for `docs/specs/plain-language-finding-explanations/spec.md`
(NOT part of the build, NOT a test). The spec's fixture rewrite is guarded by
`engine/tests/test_demo_finding_phrasing.py`, but the *prompt* edits in
`engine.arm_g` only take effect on a live analysis, so nothing offline can prove
they work. This script fires both prompt versions at the same document pair and
prints the summaries side by side so a human can judge readability.

SAFETY: this NEVER writes to `data/workstreams/`. It calls the finder stages
directly (never the `analyze` HTTP route, which persists via `save_findings` and
would overwrite the committed demo findings). Nothing is saved; results only
print.

COST: a live model call per same-topic batch, per arm. Stage 1 axis extraction
reads the workstream's committed `axes/` cache, so it is free. Keep `--pairs`
small: 8 pairs is one batch per arm.

Usage:
    .venv/bin/python scripts/verify_phrasing_ab.py
    .venv/bin/python scripts/verify_phrasing_ab.py --pairs 16
    .venv/bin/python scripts/verify_phrasing_ab.py --coverage   # + coverage arm
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import arm_g, ws_anchors  # noqa: E402
from engine.config import REPO_ROOT  # noqa: E402

WORKSTREAM_ID = "open-finance-pd-2026"
# The smallest pair in the demo workstream: ED (49 anchors) x BIS (124).
DOC_A = "bis-papers-168"
DOC_B = "ed-open-finance-2025"

WORKSTREAMS_DIR = REPO_ROOT / "data" / "workstreams"
AXES_DIR = WORKSTREAMS_DIR / WORKSTREAM_ID / "axes"

SUMMARY_CAP = 20
SCOPE_NOTE_CAP = 30

# The pre-change prompts, quoted from the commit that introduced the plain
# language rules (5e2d2bd^). Kept inline so the A/B baseline does not depend on
# git history being reachable at run time.
OLD_SAME_TOPIC_TAIL = (
    "BATCH-UNION MEMBERSHIP: you may relate ANY A-side anchor in this batch to "
    "ANY B-side anchor in this batch — you are not limited to a fixed pairing. "
    "Emit one finding object per genuine relationship you find.\n\n"
)

OLD_COVERAGE_SUMMARY_RULE = (
    "COVERAGE-SUMMARY RULE: every finding summary MUST do all three of the "
    "following:\n"
    "  1. Name the shared regulatory topic that both documents sit under (e.g. "
    "'open API security', 'consent management', 'third-party access').\n"
    "  2. State what the COVERING side specifically requires or addresses on "
    "that sub-topic.\n"
    "  3. State precisely what the OTHER side does NOT address — name the "
    "specific obligation or sub-point that is absent, not just 'does not cover "
    "this'.\n\n"
)


def _old_same_topic_prompt() -> str:
    """The new prompt with the plain-language block stripped back out."""
    new = arm_g.SAME_TOPIC_FINDER_SYSTEM_PROMPT
    marker = "SUMMARY PHRASING RULE (strict):"
    head, _, rest = new.partition(marker)
    if not rest:
        raise SystemExit("could not locate the phrasing rule; is arm_g.py current?")
    # Drop everything from the marker to the end of that paragraph.
    _, _, tail = rest.partition("never stacked into the summary.\n\n")
    return head + tail


def _old_coverage_prompt() -> str:
    """The new coverage prompt with the old three-part rule restored."""
    new = arm_g.COVERAGE_FINDER_SYSTEM_PROMPT
    marker = "COVERAGE-SUMMARY RULE:"
    head, _, rest = new.partition(marker)
    if not rest:
        raise SystemExit("could not locate the coverage rule; is arm_g.py current?")
    _, _, tail = rest.partition("otherwise use a plain equivalent.\n\n")
    return head + OLD_COVERAGE_SUMMARY_RULE + tail


def _words(text: str | None) -> int:
    return len((text or "").split())


def _report(arm: str, findings: list[dict]) -> None:
    print(f"\n{'=' * 72}\n{arm}  ({len(findings)} findings)\n{'=' * 72}")
    if not findings:
        print("  (no findings returned)")
        return
    summary_words = [_words(f.get("summary")) for f in findings]
    over = [w for w in summary_words if w > SUMMARY_CAP]
    for f in findings:
        w = _words(f.get("summary"))
        flag = "  <-- OVER CAP" if w > SUMMARY_CAP else ""
        print(f"\n  [{f.get('label')} {w}w]{flag} {f.get('summary')}")
        if f.get("scope_note"):
            print(f"      scope ({_words(f['scope_note'])}w): {f['scope_note']}")
    print(
        f"\n  -- summary words: max {max(summary_words)}, "
        f"mean {round(statistics.mean(summary_words), 1)}, "
        f"over cap {len(over)}/{len(summary_words)}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pairs",
        type=int,
        default=8,
        help="retrieval candidate pairs to judge per arm (8 = one batch)",
    )
    ap.add_argument(
        "--coverage",
        action="store_true",
        help="also A/B the whole-doc coverage finder (one large call per arm)",
    )
    args = ap.parse_args()

    print(f"Workstream: {WORKSTREAM_ID}\nPair: {DOC_A} (A) x {DOC_B} (B)")
    print("NOTE: nothing is written to data/workstreams/; results only print.\n")

    index = ws_anchors.build_index(WORKSTREAMS_DIR, WORKSTREAM_ID)

    # Stage 1 — free: reads the committed axes cache.
    axes_a = arm_g.extract_axes_for_document(index, DOC_A, axes_dir=AXES_DIR)
    axes_b = arm_g.extract_axes_for_document(index, DOC_B, axes_dir=AXES_DIR)
    print(f"axes: {len(axes_a)} A-side, {len(axes_b)} B-side (from cache)")

    # Stage 2 — free (no model, unless cosine embeddings are reachable).
    candidates = arm_g.retrieve(axes_a, axes_b)[: args.pairs]
    print(f"retrieval candidates: {len(candidates)}")

    original = arm_g.SAME_TOPIC_FINDER_SYSTEM_PROMPT
    try:
        arm_g.SAME_TOPIC_FINDER_SYSTEM_PROMPT = _old_same_topic_prompt()
        before = arm_g.finder_same_topic_batched(index, candidates)
    finally:
        arm_g.SAME_TOPIC_FINDER_SYSTEM_PROMPT = original
    _report("BEFORE — same-topic finder, no phrasing rule", before)

    after = arm_g.finder_same_topic_batched(index, candidates)
    _report("AFTER — same-topic finder, plain-language rule", after)

    if args.coverage:
        suppression = arm_g._build_suppression(candidates, after)
        original_cov = arm_g.COVERAGE_FINDER_SYSTEM_PROMPT
        try:
            arm_g.COVERAGE_FINDER_SYSTEM_PROMPT = _old_coverage_prompt()
            cov_before = arm_g.finder_coverage_whole_doc(
                index, DOC_A, DOC_B, suppression
            )
        finally:
            arm_g.COVERAGE_FINDER_SYSTEM_PROMPT = original_cov
        _report("BEFORE — coverage finder, three-part stacked rule", cov_before)

        cov_after = arm_g.finder_coverage_whole_doc(index, DOC_A, DOC_B, suppression)
        _report("AFTER — coverage finder, short summary + scope note", cov_after)

    print(
        "\nRead the two arms above and judge: did you understand each AFTER "
        "summary on the first read?\nThat judgment, not the word count, is the "
        "spec's success metric."
    )


if __name__ == "__main__":
    main()
