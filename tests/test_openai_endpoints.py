"""Named OpenAI-compatible endpoints from llm.yaml can serve models of their own."""

from __future__ import annotations

import pytest

from addons.settings import llm_config
from llm.utils import model_init

ENDPOINT = {"base_url": "https://llm.example.invalid/v1", "api_key_env": "EXAMPLE_LLM_API_KEY"}


@pytest.fixture
def endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Declares an endpoint called ``example`` and its key, independent of the live config."""
    monkeypatch.setattr(llm_config, "openai_endpoints", {"example": ENDPOINT}, raising=False)
    monkeypatch.setenv("EXAMPLE_LLM_API_KEY", "example-secret")


def test_a_model_of_a_named_endpoint_uses_that_endpoints_url_and_key(endpoint: None) -> None:
    model = model_init.create_model_instance("example:qwen")

    assert model.model_name == "qwen"
    assert str(model.openai_api_base) == ENDPOINT["base_url"]
    assert model.openai_api_key.get_secret_value() == "example-secret"


def test_a_named_endpoint_model_gets_the_configured_token_cap(
    endpoint: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llm_config, "max_output_tokens", 4321, raising=False)

    model = model_init.create_model_instance("example:qwen", limit_output=True)

    assert model.max_tokens == 4321


def test_a_missing_key_is_an_explicit_error(endpoint: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EXAMPLE_LLM_API_KEY")

    with pytest.raises(ValueError, match="EXAMPLE_LLM_API_KEY"):
        model_init.create_model_instance("example:qwen")


def test_vllm_models_keep_using_the_vllm_url(endpoint: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_config, "vllm_url", "http://vllm.invalid", raising=False)

    model = model_init.create_model_instance("vllm:gemma4-26b")

    assert str(model.openai_api_base) == "http://vllm.invalid/v1"
