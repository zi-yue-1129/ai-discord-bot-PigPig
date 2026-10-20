"""The prompts must tell the model how to tell speakers apart using what it is actually shown."""

from __future__ import annotations

from pathlib import Path

import yaml

PROMPT_DIR = Path(__file__).resolve().parent.parent / "base_configs" / "prompt"


def _prompt_text(name: str) -> str:
    """Returns every module of a prompt file as one string."""
    modules = yaml.safe_load((PROMPT_DIR / name).read_text(encoding="utf-8"))
    return repr(modules)


def test_prompts_do_not_rely_on_a_name_attribute_the_model_never_receives() -> None:
    for name in ("message_agent.yaml", "info_agent.yaml"):
        assert "`name` attribute" not in _prompt_text(name), name


def test_reply_prompt_says_which_user_id_is_the_bot_itself() -> None:
    assert "`UserID:{bot_id}` is you" in _prompt_text("message_agent.yaml")


def test_both_prompts_explain_that_bot_prefixed_speakers_are_other_bots() -> None:
    for name in ("message_agent.yaml", "info_agent.yaml"):
        assert "starting with `BOT `" in _prompt_text(name), name
