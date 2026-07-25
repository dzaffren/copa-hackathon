"""Tests for engine.config — CURATED_SEED_EDGES shape invariant and the
Arm G three-tier model deployment vars.

Covers Task 3's requirement that every curated seed edge carries a
non-empty reason and at least one clause anchor on each side (the shape
`engine.graph.build_graph` validates against the real ClauseIndex at build
time; this test only checks the static shape config.py ships, not that the
clause numbers resolve in the real corpus).

The Arm G tests reload `engine.config` under a monkeypatched environment,
because the deployment names are read from `os.environ` at import time. A
fixture restores the real environment and reloads once more at teardown so
these reloads never leak into other tests.
"""

import importlib

import pytest

import engine.config as config
from engine.config import CURATED_SEED_EDGES


@pytest.fixture
def reload_config(monkeypatch):
    """Reload engine.config under the test's monkeypatched env, then restore.

    The monkeypatch fixture unwinds the env changes at teardown; we reload
    once more afterwards so the module-level deployment names reflect the
    real environment again and don't pollute other tests.
    """

    def _reload():
        importlib.reload(config)
        return config

    yield _reload
    monkeypatch.undo()
    importlib.reload(config)


def test_every_curated_seed_edge_has_reason_and_clause_anchors_on_both_sides():
    for edge in CURATED_SEED_EDGES:
        assert edge[
            "reason"
        ], f"edge {edge['source_policy_id']} -> {edge['target_policy_id']} has no reason"
        assert edge["source_clauses"], (
            f"edge {edge['source_policy_id']} -> {edge['target_policy_id']} "
            f"has no source_clauses"
        )
        assert edge["target_clauses"], (
            f"edge {edge['source_policy_id']} -> {edge['target_policy_id']} "
            f"has no target_clauses"
        )


def test_extraction_deployment_default(reload_config, monkeypatch):
    monkeypatch.delenv("AZURE_FOUNDRY_EXTRACTION_DEPLOYMENT", raising=False)
    cfg = reload_config()
    assert cfg.EXTRACTION_DEPLOYMENT == "claude-haiku-4-5"


def test_extraction_deployment_from_env(reload_config, monkeypatch):
    monkeypatch.setenv("AZURE_FOUNDRY_EXTRACTION_DEPLOYMENT", "custom-extractor")
    cfg = reload_config()
    assert cfg.EXTRACTION_DEPLOYMENT == "custom-extractor"


def test_reasoning_deployment_default(reload_config, monkeypatch):
    monkeypatch.delenv("AZURE_FOUNDRY_REASONING_DEPLOYMENT", raising=False)
    cfg = reload_config()
    assert cfg.REASONING_DEPLOYMENT == "claude-sonnet-5"


def test_reasoning_deployment_from_env(reload_config, monkeypatch):
    monkeypatch.setenv("AZURE_FOUNDRY_REASONING_DEPLOYMENT", "custom-reasoner")
    cfg = reload_config()
    assert cfg.REASONING_DEPLOYMENT == "custom-reasoner"


def test_both_new_deployments_from_env(reload_config, monkeypatch):
    monkeypatch.setenv("AZURE_FOUNDRY_EXTRACTION_DEPLOYMENT", "custom-extractor")
    monkeypatch.setenv("AZURE_FOUNDRY_REASONING_DEPLOYMENT", "custom-reasoner")
    cfg = reload_config()
    assert cfg.EXTRACTION_DEPLOYMENT == "custom-extractor"
    assert cfg.REASONING_DEPLOYMENT == "custom-reasoner"


def test_existing_deployments_unaffected_by_new_vars(reload_config, monkeypatch):
    monkeypatch.setenv("AZURE_FOUNDRY_EXTRACTION_DEPLOYMENT", "custom-extractor")
    monkeypatch.setenv("AZURE_FOUNDRY_REASONING_DEPLOYMENT", "custom-reasoner")
    monkeypatch.delenv("AZURE_FOUNDRY_PARSER_DEPLOYMENT", raising=False)
    monkeypatch.delenv("AZURE_FOUNDRY_FINDER_CRITIC_DEPLOYMENT", raising=False)
    monkeypatch.delenv("AZURE_FOUNDRY_COPILOT_DEPLOYMENT", raising=False)
    cfg = reload_config()
    assert cfg.PARSER_DEPLOYMENT == "claude-sonnet-5"
    assert cfg.FINDER_CRITIC_DEPLOYMENT == "claude-opus-4-8"
    assert cfg.COPILOT_DEPLOYMENT == "claude-sonnet-5"
