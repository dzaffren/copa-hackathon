"""Guards for the build CLI and the demo-prep scripts.

Why this exists: `scripts/run_finder_trace.py` sat broken for days. #38 removed
`_load_clause_index` from `engine.api`, the script's import died with it, and
nothing failed — no test imports the scripts, so the only way to find out was to
run the thing. The script is how traces get recorded, so the model-driven half of
the pipeline was unrunnable and the suite was green.

These are cheap: importing a module proves its imports resolve. They will not
catch a logic bug, but they catch a whole file quietly ceasing to exist.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from engine.build import _merge_clause_index
from engine.config import REPO_ROOT

SCRIPTS = REPO_ROOT / "scripts"


def _import_script(name: str):
    """Import a script by path, the way running it would."""
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader, f"cannot load scripts/{name}.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # ImportError here = the script is broken
    return module


# --- the scripts still import ----------------------------------------------


@pytest.mark.parametrize(
    "name", ["run_finder_trace", "project_cross_workstream_findings"]
)
def test_script_imports(name: str) -> None:
    """A dead import in a script is invisible until someone runs it."""
    module = _import_script(name)
    assert callable(module.main)


def test_run_finder_trace_uses_the_clause_module_not_the_api() -> None:
    """The loader lives in engine.clauses now.

    The API deliberately never reads the clause index — workstream findings
    carry their own verbatim text — so importing a loader from engine.api is
    what broke last time and should not come back.
    """
    source = (SCRIPTS / "run_finder_trace.py").read_text(encoding="utf-8")
    assert "from engine.clauses import load_clause_index" in source
    assert "_load_clause_index" not in source


# --- the clause index loader ------------------------------------------------


def test_load_clause_index_reads_the_committed_artifacts() -> None:
    from engine.clauses import load_clause_index

    index = load_clause_index(REPO_ROOT / "data" / "artifacts")
    assert index.get("RMiT 9.4") is not None
    assert index.entries_for_document("open-finance-v1-2025-ed")


def test_load_clause_index_tolerates_a_missing_artifact(tmp_path) -> None:
    """A fresh checkout must be able to import without a build having run."""
    from engine.clauses import load_clause_index

    assert load_clause_index(tmp_path).get("RMiT 9.4") is None


# --- --merge ----------------------------------------------------------------


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_merge_is_additive(tmp_path) -> None:
    built, target = tmp_path / "built", tmp_path / "target"
    _write(built / "clause-index.json", {"New 1.1": {"text": "a"}})
    _write(target / "clause-index.json", {"Old 1.1": {"text": "b"}})

    added = _merge_clause_index(built, target)

    merged = json.loads((target / "clause-index.json").read_text(encoding="utf-8"))
    assert added == 1
    assert sorted(merged) == ["New 1.1", "Old 1.1"]


def test_merge_refuses_to_overwrite_an_existing_clause(tmp_path) -> None:
    """The #34 failure, made impossible.

    Letting the newer build win would silently rewrite clauses that committed
    traces already cite. A collision is a real conflict, so it is reported.
    """
    built, target = tmp_path / "built", tmp_path / "target"
    _write(built / "clause-index.json", {"Old 1.1": {"text": "OVERWRITE"}})
    _write(target / "clause-index.json", {"Old 1.1": {"text": "original"}})

    with pytest.raises(ValueError, match="refuses to overwrite"):
        _merge_clause_index(built, target)

    kept = json.loads((target / "clause-index.json").read_text(encoding="utf-8"))
    assert kept["Old 1.1"]["text"] == "original", "target must survive a refusal"


def test_merge_into_a_missing_target_just_writes_it(tmp_path) -> None:
    built, target = tmp_path / "built", tmp_path / "nope"
    _write(built / "clause-index.json", {"New 1.1": {"text": "a"}})

    assert _merge_clause_index(built, target) == 1
    assert (target / "clause-index.json").exists()


def test_merge_leaves_graph_json_alone(tmp_path) -> None:
    """A subset graph is not a subset of the full graph — its edges were
    validated against a partial document set, so grafting it in would produce a
    graph that never existed."""
    built, target = tmp_path / "built", tmp_path / "target"
    _write(built / "clause-index.json", {"New 1.1": {"text": "a"}})
    _write(built / "graph.json", {"nodes": ["subset"], "edges": []})
    _write(target / "clause-index.json", {"Old 1.1": {"text": "b"}})
    _write(target / "graph.json", {"nodes": ["full"], "edges": []})

    _merge_clause_index(built, target)

    graph = json.loads((target / "graph.json").read_text(encoding="utf-8"))
    assert graph["nodes"] == ["full"]


# --- enrich_node_metadata must not erase what it did not derive -------------
# The script writes through `concepts.save_concepts`, which fills every one of
# the nine CONCEPT_FIELDS — so passing only the two fields it derives blanked
# the other seven. That destroyed hand-authored profile content (of-ed-2025 lost
# its applicability, issuance date, six keywords and legal basis) while printing
# "enriched", and those values exist only in git. The script has no CLI and is
# hardcoded to the real data/workstreams, so there is no safe dry run either;
# these guard the merge at the one seam that takes a directory.


def _enrich_fixture(tmp_path: Path, profile: dict) -> dict:
    """Run the script's per-workstream pass over a one-node workstream that
    already has `profile` on disk, and return the profile afterwards."""
    ws = tmp_path / "ws-1"
    _write(
        ws / "graph.json",
        {
            "nodes": [
                {
                    "id": "n1",
                    "node_type": "task",
                    "title": "Some PD",
                    "owner": {"id": "ar", "name": "Aisyah R."},
                }
            ],
            "edges": [],
        },
    )
    _write(ws / "workstream.json", {"id": "ws-1", "name": "WS 1"})
    _write(ws / "concepts" / "n1.json", profile)

    _import_script("enrich_node_metadata")._enrich_workstream(tmp_path, "ws-1")

    return json.loads((ws / "concepts" / "n1.json").read_text(encoding="utf-8"))


def test_enrich_preserves_fields_it_does_not_derive(tmp_path) -> None:
    """The regression: a re-run must not blank hand-authored profile content."""
    after = _enrich_fixture(
        tmp_path,
        {
            "policy_owner": "Jarod N.",
            "applicability": "Licensed banks and eligible data providers",
            "issuance_date": "2025-11-18",
            "keywords": ["open finance", "consent"],
            "legal_basis": ["FSA 2013"],
        },
    )

    assert after["applicability"] == "Licensed banks and eligible data providers"
    assert after["issuance_date"] == "2025-11-18"
    assert after["keywords"] == ["open finance", "consent"]
    assert after["legal_basis"] == ["FSA 2013"]


def test_enrich_still_writes_the_fields_it_does_derive(tmp_path) -> None:
    """Preserving the rest must not stop it doing its job: `policy_owner` comes
    off the node, so a stale one is corrected."""
    after = _enrich_fixture(tmp_path, {"policy_owner": "Someone Else"})

    assert after["policy_owner"] == "Aisyah R."


def test_enrich_is_idempotent(tmp_path) -> None:
    """Running twice changes nothing the second time — the property that was
    false before, and the cheapest way to notice it breaking again."""
    profile = {
        "policy_owner": "Aisyah R.",
        "applicability": "Licensed banks",
        "keywords": ["resilience"],
    }
    once = _enrich_fixture(tmp_path, profile)
    twice = _enrich_fixture(tmp_path, once)

    assert once == twice
