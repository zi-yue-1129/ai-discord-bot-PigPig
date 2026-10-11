"""The prompts must keep the AI from claiming music actions that did not happen."""

from __future__ import annotations

from pathlib import Path

import pytest

PROMPT_DIR = Path(__file__).resolve().parents[2] / "base_configs" / "prompt"


def _text(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def test_the_reply_agent_may_only_confirm_actions_that_a_tool_result_confirms() -> None:
    text = _text("message_agent.yaml")

    assert "### Actions Must Be Confirmed" in text
    assert "no tool result" in text


def test_the_info_agent_plays_vague_requests_instead_of_asking_or_checking() -> None:
    text = _text("info_agent.yaml")

    assert "one more" in text
    assert "choose the query yourself" in text


@pytest.mark.parametrize("name", ["message_agent.yaml", "info_agent.yaml"])
def test_prompts_stay_valid_yaml(name: str) -> None:
    import yaml

    assert isinstance(yaml.safe_load(_text(name)), dict)
