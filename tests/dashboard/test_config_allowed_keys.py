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


class _JsonRequest:
    """Minimal stand-in for a FastAPI request carrying a JSON body."""

    def __init__(self, body: dict) -> None:
        self._body = body

    async def json(self) -> dict:
        """Returns the body the dashboard page would have sent."""
        return self._body


@pytest.mark.asyncio
async def test_saving_a_broken_endpoint_is_refused_and_leaves_the_file_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A typo saved here would otherwise stop the bot at its next start."""
    from fastapi import HTTPException

    from dashboard.routers import admin

    path = tmp_path / "llm.yaml"
    path.write_text("llm_call_timeout: 60\n", encoding="utf-8")
    monkeypatch.setattr(admin, "_config_path", lambda file: str(path))
    body = {"config": {"openai_endpoints": {"anthropic": {"base_url": "https://h.invalid/v1", "api_key_env": "K"}}}}

    with pytest.raises(HTTPException) as refused:
        await admin.write_config("llm", _JsonRequest(body), user={"sub": "owner"})

    assert refused.value.status_code == 400
    assert "anthropic" in refused.value.detail
    assert path.read_text(encoding="utf-8") == "llm_call_timeout: 60\n"


@pytest.mark.asyncio
async def test_saving_a_valid_endpoint_still_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A well-formed endpoint section is written through unchanged."""
    from dashboard.routers import admin

    path = tmp_path / "llm.yaml"
    path.write_text("llm_call_timeout: 60\n", encoding="utf-8")
    monkeypatch.setattr(admin, "_config_path", lambda file: str(path))
    endpoints = {"steak": {"base_url": "https://llm.example.invalid/v1", "api_key_env": "STEAK_LLM_API_KEY"}}

    await admin.write_config("llm", _JsonRequest({"config": {"openai_endpoints": endpoints}}), user={"sub": "owner"})

    assert yaml.safe_load(path.read_text(encoding="utf-8"))["openai_endpoints"] == endpoints
