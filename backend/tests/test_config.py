from __future__ import annotations

import os

import pytest

from app.config import _pick_provider, load_env_file

KEYS = ("LLM_PROVIDER", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENAI_MODEL", "DEMO_ONLY_VAR")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in KEYS:
        monkeypatch.delenv(key, raising=False)


def test_defaults_to_offline_without_any_key():
    assert _pick_provider() == "offline"


def test_anthropic_key_selects_claude(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert _pick_provider() == "anthropic"


def test_openai_needs_both_key_and_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    assert _pick_provider() == "offline"
    monkeypatch.setenv("OPENAI_MODEL", "some-model")
    assert _pick_provider() == "openai"


def test_explicit_provider_wins(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("LLM_PROVIDER", "Offline")
    assert _pick_provider() == "offline"


def test_env_file_is_parsed_and_never_overrides_real_variables(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# comment\n\nDEMO_ONLY_VAR=\"from file\"\nANTHROPIC_API_KEY=\nOPENAI_MODEL='m1'\nnot a line\n"
    )
    monkeypatch.setenv("OPENAI_MODEL", "from-shell")
    load_env_file(env)
    assert os.environ["DEMO_ONLY_VAR"] == "from file"
    assert os.environ["OPENAI_MODEL"] == "from-shell"
    assert "ANTHROPIC_API_KEY" not in os.environ
    os.environ.pop("DEMO_ONLY_VAR")


def test_missing_env_file_is_fine(tmp_path):
    load_env_file(tmp_path / "nope.env")
