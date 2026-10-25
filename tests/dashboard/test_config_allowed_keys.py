"""The dashboard config editor must accept every top-level key the bot's config files use."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dashboard.routers.admin import _CONFIG_ALLOWED_KEYS, _mask_secrets

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("name", ["base", "llm", "memory", "music"])
def test_every_top_level_key_of_a_config_file_can_be_saved(name: str) -> None:
    template = yaml.safe_load((ROOT / "base_configs" / f"{name}.yaml").read_text(encoding="utf-8")) or {}

    rejected = set(template) - _CONFIG_ALLOWED_KEYS[name]

    assert not rejected, f"The dashboard answers HTTP 400 when {name}.yaml is saved with: {sorted(rejected)}"


def test_the_documented_openai_endpoints_key_can_be_saved() -> None:
    assert "openai_endpoints" in _CONFIG_ALLOWED_KEYS["llm"]


def test_the_name_of_an_environment_variable_is_not_masked_as_a_secret() -> None:
    config = {
        "openai_endpoints": {"steak": {"base_url": "https://llm.example.invalid/v1", "api_key_env": "STEAK_LLM_API_KEY"}},
        "qdrant_api_key": "abcd1234efgh5678",
    }

    _mask_secrets(config)

    assert config["openai_endpoints"]["steak"]["api_key_env"] == "STEAK_LLM_API_KEY"
    assert config["qdrant_api_key"] == "abcd****5678"
