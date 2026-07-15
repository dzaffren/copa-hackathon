"""The Copilot's citations must be checkable, not merely plausible.

A scripted reply is the easiest place in this product to break the verbatim rule:
it reads exactly as convincingly whether or not the clause says what the script
claims. The spec's own draft script demonstrated the failure — it had RMiT §17.1
supplying "the technology-risk accountability framework", when RMiT 17.1 is about
consulting the Bank before first-time public-cloud adoption.

So `test_rmit_9_4_quote_is_verbatim` re-resolves the quote against the built
clause index rather than trusting it. It is deliberately NOT skipped when the
index is missing: docs/learnings/blocker-engine-build-silently-narrows-artifacts
records that a rebuild without Azure Document Intelligence silently shrinks
`data/artifacts/` and orphans committed traces, and that the suite stayed green
through it precisely because no test ever re-resolved a citation. This one does.
"""

import json
import re

import pytest

from engine import copilot_scripts
from engine.config import REPO_ROOT

CLAUSE_INDEX = REPO_ROOT / "data" / "artifacts" / "clause-index.json"


def _normalise(text: str) -> str:
    """Collapse the source PDF's hard wraps and drop the parser's footnote
    artifacts, without touching a word.

    `$^ { 1 3 }$` is how the extractor renders footnote 13's superscript marker;
    `resources 14.` is footnote 14 landing inline. Both are artifacts of the PDF
    parse, not part of the clause, so neither side of the comparison should carry
    them.
    """
    text = re.sub(r"\$\^\s*\{[^}]*\}\s*\$", "", text)
    text = re.sub(r"\s+(\d{1,2})\.", r".", text)
    return " ".join(text.split())


def test_rmit_9_4_quote_is_verbatim() -> None:
    """The PD script's RMiT 9.4 quote matches the parsed clause, word for word."""
    assert CLAUSE_INDEX.exists(), (
        f"{CLAUSE_INDEX} is missing — the Copilot's RMiT citation cannot be "
        "verified. Do not skip this: an unverifiable citation is the failure "
        "this test exists to catch."
    )
    index = json.loads(CLAUSE_INDEX.read_text(encoding="utf-8"))
    assert "RMiT 9.4" in index, (
        "RMiT 9.4 is absent from the clause index. If a rebuild narrowed "
        "data/artifacts/, restore it — do not weaken this assertion."
    )
    indexed = _normalise(index["RMiT 9.4"]["_full_text"])
    quoted = _normalise(copilot_scripts.RMIT_9_4_QUOTE)
    assert indexed.startswith(quoted), (
        "The Copilot's RMiT 9.4 quote is not verbatim.\n"
        f"  script: {quoted}\n"
        f"  actual: {indexed[:len(quoted) + 40]}"
    )


def test_rmit_9_4_is_about_accountability_not_cloud_consultation() -> None:
    """Guards the specific misattribution the spec shipped with.

    If someone 'restores' the spec's wording and points the accountable-officer
    narrative back at RMiT 17.1, this fails.
    """
    index = json.loads(CLAUSE_INDEX.read_text(encoding="utf-8"))
    assert "designate" in index["RMiT 9.4"]["_full_text"]
    assert "public cloud" in index["RMiT 17.1"]["_full_text"]
    pd_script = json.dumps(copilot_scripts.COPILOT_SCRIPTS["PD"])
    assert "17.1" not in pd_script


def test_every_intent_has_a_script() -> None:
    assert set(copilot_scripts.COPILOT_SCRIPTS) == set(copilot_scripts.INTENTS)
    assert len(copilot_scripts.INTENTS) == 7


def test_every_citation_carries_a_clause_number_and_text() -> None:
    """No citation may be a bare assertion."""
    for intent, script in copilot_scripts.COPILOT_SCRIPTS.items():
        for turn in script:
            for citation in turn.get("citations", []):
                assert citation.get("clause_number"), f"{intent}: citation has no number"
                assert citation.get("text", "").strip(), (
                    f"{intent}: citation {citation.get('clause_number')} quotes nothing"
                )


@pytest.mark.parametrize(
    "quote_name, edge_file, side",
    [
        ("OPRES_5_3_QUOTE", "e-opres_v0_3--hkma_spm_or2.json", "source_clauses"),
        ("HKMA_5_2_QUOTE", "e-opres_v0_3--hkma_spm_or2.json", "target_clauses"),
    ],
)
def test_fixture_quotes_match_the_findings_they_came_from(
    quote_name: str, edge_file: str, side: str
) -> None:
    """The non-RMiT quotes are re-resolved too, against the findings fixtures
    that are their source of truth."""
    path = REPO_ROOT / "data" / "workstreams" / "opres-v2" / "findings" / edge_file
    findings = json.loads(path.read_text(encoding="utf-8"))
    texts = {c["text"] for f in findings for c in (f.get(side) or [])}
    assert getattr(copilot_scripts, quote_name) in texts


def test_reply_for_unknown_intent_is_none() -> None:
    assert copilot_scripts.reply_for("Haiku", 0) is None


def test_reply_for_repeats_last_turn_rather_than_running_out() -> None:
    """A stray extra Send must not dead-end the demo, and must not improvise."""
    last = copilot_scripts.reply_for("PD", 1)
    assert copilot_scripts.reply_for("PD", 99) == last


def test_pd_script_proposes_6_3_because_the_draft_has_none() -> None:
    """The snippet's whole premise: §6.3 does not exist in the draft yet."""
    draft = json.loads(
        (
            REPO_ROOT / "data" / "workstreams" / "opres-v2" / "drafts" / "opres-pd-v0-3.json"
        ).read_text(encoding="utf-8")
    )
    assert "<strong>6.3</strong>" not in draft["content_html"]
    assert "<strong>6.3</strong>" in copilot_scripts.COPILOT_SCRIPTS["PD"][1]["snippet_html"]
