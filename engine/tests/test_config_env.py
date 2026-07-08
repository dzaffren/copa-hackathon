"""Tests for engine.config `.env` loading and deployment defaults.

Covers the Task D requirement that `engine.config` imports cleanly with no
`.env` present (the CI condition) and that the deployment names fall back to
the confirmed defaults when the corresponding env vars are unset. These tests
must not depend on a real `.env` file existing.
"""

import importlib


def test_config_imports_and_defaults_without_env(monkeypatch):
    # Simulate the CI condition: no deployment env vars exported. load_dotenv
    # no-ops when repo-root .env is absent, so the module-level defaults apply.
    monkeypatch.delenv("AZURE_FOUNDRY_PARSER_DEPLOYMENT", raising=False)
    monkeypatch.delenv("AZURE_FOUNDRY_FINDER_CRITIC_DEPLOYMENT", raising=False)

    import engine.config as config

    config = importlib.reload(config)

    assert config.PARSER_DEPLOYMENT == "claude-sonnet-5"
    assert config.FINDER_CRITIC_DEPLOYMENT == "claude-opus-4-8"
