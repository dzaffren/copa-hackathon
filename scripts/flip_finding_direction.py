"""One-time fix: re-label findings written with the drafter's side inverted.

`POST .../edges/{edge_id}/analyze` used to pass the edge SOURCE to the finder as
document A ("we/ours"), on the belief that the task node is always the edge
source. On `open-finance-pd-2026` every anchor points INTO the ED node the PD
consolidates, so A was the peer regulator and B was BNM's own draft — exactly
backwards. The finder then wrote correct prose against a wrong premise, so the
coverage labels came out inverted:

    silent-on  <-> goes-beyond      (which side has no provision)

`aligns-with`, `conflicts-with` and `differs-on` are symmetric and left alone.
Summaries are left alone too: they name the documents explicitly ("RMiT
requires ...; the draft has no ..."), so they already read correctly and only the
label disagreed with them.

`sentiment` (tighten/loosen) is deliberately NOT flipped here even though it is
direction-sensitive. The stored values turned out NOT to be uniformly inverted —
the finder had assigned some of them as though the draft were already "ours" — so
a blanket flip corrected some and corrupted the rest. The eight affected values
were instead set by hand from each finding's own summary and cited clauses. If
this script is ever reused on another workstream, audit sentiment the same way
rather than flipping it.

Clause arrays are NOT touched. They are stored in edge orientation and were
already consistent with it, which is what the review panes assume.

ONE-SHOT — already applied to `open-finance-pd-2026` on 1 Aug 2026. It is NOT
idempotent: inversion is detected from edge geometry ("is ours the source?"),
which cannot distinguish findings still carrying the old labels from findings this
script has already corrected. Running it twice re-inverts them. Kept in the tree
as the record of what was changed, and for a workstream seeded from a pre-fix
analyze run; pass `--i-know-this-is-one-shot` to actually write.

Run from the repo root:

    python -m scripts.flip_finding_direction              # report only
    python -m scripts.flip_finding_direction --write --i-know-this-is-one-shot
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from engine import workstreams

LABEL_FLIP = {"silent-on": "goes-beyond", "goes-beyond": "silent-on"}


def _inverted_edges(root: Path, workstream_id: str) -> dict[str, tuple[str, str]]:
    """The analysed edges of a workstream whose stored findings were written with
    "ours" on the wrong side, mapped to `(ours_node, theirs_node)`.

    An edge is inverted exactly when the drafter's side is NOT the edge source,
    since that is the assumption the old route made.
    """
    graph = workstreams.load_graph(root, workstream_id)
    if graph is None:
        return {}
    meta = workstreams.load_workstream(root, workstream_id)
    task_id = workstreams.primary_task_id(meta, graph)
    out: dict[str, tuple[str, str]] = {}
    for edge in graph.get("edges", []):
        if not workstreams.edge_is_analysed(root, workstream_id, edge["id"]):
            continue
        ours, theirs = workstreams.analysis_direction(graph, edge, task_id)
        if ours != edge["source"]:
            out[edge["id"]] = (ours, theirs)
    return out


def _reverse_finding(finding: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """A copy of `finding` with its coverage label flipped, plus whether anything
    changed. `sentiment` is left alone — see the module docstring."""
    fixed = dict(finding)
    label = finding.get("label")
    if label not in LABEL_FLIP:
        return fixed, False
    fixed["label"] = LABEL_FLIP[label]
    return fixed, True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="apply the fix")
    parser.add_argument(
        "--i-know-this-is-one-shot",
        action="store_true",
        dest="acknowledged",
        help="required with --write: re-running re-inverts already-fixed findings",
    )
    parser.add_argument(
        "--workstreams-dir", default="data/workstreams", type=Path
    )
    parser.add_argument(
        "--workstream",
        action="append",
        dest="workstream_ids",
        help="limit to a workstream id (repeatable); default is all on disk",
    )
    args = parser.parse_args(argv)

    if args.write and not args.acknowledged:
        parser.error(
            "--write needs --i-know-this-is-one-shot: this script is not "
            "idempotent and was already applied to open-finance-pd-2026."
        )

    root: Path = args.workstreams_dir
    ids = args.workstream_ids or sorted(
        p.name for p in root.iterdir() if (p / "graph.json").is_file()
    )

    total = 0
    for workstream_id in ids:
        for edge_id, (ours, _theirs) in _inverted_edges(root, workstream_id).items():
            findings = workstreams.load_findings(root, workstream_id, edge_id)
            fixed = []
            touched = 0
            for finding in findings:
                new_finding, changed = _reverse_finding(finding)
                touched += int(changed)
                fixed.append(new_finding)
            if not touched:
                continue
            total += touched
            print(
                f"{workstream_id}/{edge_id}: {touched} of {len(findings)} "
                f"re-labelled (ours = {ours})"
            )
            if args.write:
                workstreams.save_findings(root, workstream_id, edge_id, fixed)

    print(f"{'Re-labelled' if args.write else 'Would re-label'} {total} findings")
    if not args.write:
        print("Dry run — pass --write to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
