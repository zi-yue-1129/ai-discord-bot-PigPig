"""Models built for chat replies are capped in how many tokens they may generate."""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from addons.settings import llm_config
from llm.utils import model_init


@pytest.fixture
def token_limit(monkeypatch: pytest.MonkeyPatch) -> int:
    """Pin the configured cap so the expectations do not depend on the live config file."""
    monkeypatch.setattr(llm_config, "max_output_tokens", 4321, raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    return 4321


def test_a_vllm_model_gets_the_configured_token_cap(token_limit: int) -> None:
    model = model_init.create_model_instance("vllm:gemma4-26b", limit_output=True)

    assert model.max_tokens == token_limit


def test_the_cap_is_part_of_the_request_sent_to_vllm(token_limit: int) -> None:
    model = model_init.create_model_instance("vllm:gemma4-26b", limit_output=True)

    payload = model._get_request_payload([HumanMessage("hi")])

    assert payload["max_completion_tokens"] == token_limit


def test_a_gemini_model_gets_the_configured_token_cap(token_limit: int) -> None:
    model = model_init.create_model_instance("google_genai:gemini-2.5-flash", limit_output=True)

    assert model.max_output_tokens == token_limit


def test_models_are_uncapped_unless_the_caller_asks_for_the_cap(token_limit: int) -> None:
    model = model_init.create_model_instance("vllm:gemma4-26b")

    assert model.max_tokens is None


def test_a_cap_of_zero_means_no_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_config, "max_output_tokens", 0, raising=False)

    model = model_init.create_model_instance("vllm:gemma4-26b", limit_output=True)

    assert model.max_tokens is None


def test_an_explicit_cap_from_the_caller_wins(token_limit: int) -> None:
    model = model_init.create_model_instance("vllm:gemma4-26b", limit_output=True, max_tokens=99)

    assert model.max_tokens == 99
