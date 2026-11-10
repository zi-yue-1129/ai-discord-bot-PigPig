"""The owner can switch Qwen's thinking on for vLLM models, per agent role, from llm.yaml.

vLLM serves the model with thinking off by default (--default-chat-template-kwargs). A request
turns it on with chat_template_kwargs; the reasoning parser keeps the reasoning out of the reply text.
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import HumanMessage

from addons import settings
from addons.settings import llm_config, parse_vllm_thinking
from llm.utils import model_init


def _thinking(model: Any) -> Any:
    payload = model._get_request_payload([HumanMessage("hi")])
    return (payload.get("extra_body") or {}).get("chat_template_kwargs", {}).get("enable_thinking")


@pytest.fixture
def thinking_for(monkeypatch: pytest.MonkeyPatch):
    """Sets the parsed config for the test."""

    def apply(value: Any) -> None:
        monkeypatch.setattr(llm_config, "vllm_enable_thinking", parse_vllm_thinking(value), raising=False)

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    return apply


def test_thinking_is_off_by_default(thinking_for) -> None:
    thinking_for(None)

    assert _thinking(model_init.create_model_instance("vllm:gemma4-26b", role="message")) is False


def test_true_turns_thinking_on_for_every_role(thinking_for) -> None:
    thinking_for(True)

    for role in ("info", "message", "other"):
        assert _thinking(model_init.create_model_instance("vllm:gemma4-26b", role=role)) is True


def test_thinking_can_be_turned_on_for_one_role_only(thinking_for) -> None:
    thinking_for({"info": True})

    assert _thinking(model_init.create_model_instance("vllm:gemma4-26b", role="info")) is True
    assert _thinking(model_init.create_model_instance("vllm:gemma4-26b", role="message")) is False
    assert _thinking(model_init.create_model_instance("vllm:gemma4-26b")) is False


def test_other_providers_are_not_given_the_vllm_option(thinking_for) -> None:
    thinking_for(True)

    model = model_init.create_model_instance("google_genai:gemini-2.5-flash", role="message")

    assert "chat_template_kwargs" not in str(getattr(model, "model_kwargs", {}))


def test_an_extra_body_from_the_caller_is_kept(thinking_for) -> None:
    thinking_for(True)

    model = model_init.create_model_instance("vllm:gemma4-26b", role="info", extra_body={"top_k": 20})
    payload = model._get_request_payload([HumanMessage("hi")])

    assert payload["extra_body"]["top_k"] == 20
    assert payload["extra_body"]["chat_template_kwargs"]["enable_thinking"] is True


@pytest.mark.parametrize("value", ["yes", {"reply": True}, {"info": "on"}, [True]])
def test_an_invalid_value_is_reported_and_leaves_thinking_off(value: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    warnings: list = []
    monkeypatch.setattr(settings.logger, "warning", lambda text, *args, **kwargs: warnings.append(text))

    parsed = parse_vllm_thinking(value)

    assert parsed == {"info": False, "message": False, "other": False}
    assert warnings and "vllm_enable_thinking" in warnings[0]
