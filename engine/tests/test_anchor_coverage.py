import json
import re
from pathlib import Path

import pytest

from engine.config import REPO_ROOT

FIXTURES = Path(__file__).parent / "fixtures" / "ground_truth"
ANCHOR_INDEX = REPO_ROOT / "data" / "artifacts" / "anchor-index.json"
GROUND_TRUTHS = sorted(FIXTURES.glob("*.json"))


@pytest.fixture(scope="module")
def index():
    assert ANCHOR_INDEX.exists(), f"{ANCHOR_INDEX} missing — run the live build"
    return json.loads(ANCHOR_INDEX.read_text(encoding="utf-8"))


@pytest.mark.parametrize("gt_path", GROUND_TRUTHS, ids=lambda p: p.stem)
def test_non_bnm_doc_meets_acceptance_bar(gt_path, index):
    gt = json.loads(gt_path.read_text(encoding="utf-8"))
    doc_anchors = [a for a in index if a["document_id"] == gt["document_id"]]
    labels = {a["anchor_label"] for a in doc_anchors}

    # (1) Coverage: representative locators are present.
    present = [loc for loc in gt["top_level_locators"] if loc in labels]
    coverage = len(present) / len(gt["top_level_locators"])
    assert coverage >= gt["coverage_floor"], (
        f"{gt['document_id']} coverage {coverage:.0%} < floor "
        f"{gt['coverage_floor']:.0%}; missing {set(gt['top_level_locators']) - labels}")

    # (2) Citable label: every label matches the locator pattern; none is garbage.
    label_re = re.compile(gt["label_pattern"])
    garbage_re = re.compile(gt["garbage_pattern"])
    for a in doc_anchors:
        assert label_re.search(a["anchor_label"]), (
            f"label {a['anchor_label']!r} does not match {gt['label_pattern']!r}")
        assert not garbage_re.search(a["anchor_label"]), (
            f"label {a['anchor_label']!r} matches garbage pattern")

    # (3) Verbatim is enforced at build time by verify_substring; re-assert the
    # anchor carries non-empty text.
    for a in doc_anchors:
        assert a["text"].strip()
