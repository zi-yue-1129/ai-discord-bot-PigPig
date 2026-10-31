"""Tests for where the info agent gets the system context.

On the live model, the stored user memory and server knowledge in the info agent's *system prompt*
made it write a chat reply instead of calling tools. The same text after the conversation did not.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from llm.utils.info_context import build_info_agent_request

_PROMPT = "You are the tool execution agent."
_CONTEXT = "--- System Context ---\n\nUser: 1\nBackground: likes Lemon\n\nChannel: #general\n\n--- End System Context ---"


def _history() -> list:
    return [
        HumanMessage(content="[alice | UserID:1 | MessageID:2] <som> 播放我最愛的歌 <eom>"),
        AIMessage(content="[PigPig | UserID:9 | MessageID:3] <som> 好 <eom>"),
    ]


def test_the_system_prompt_stays_exactly_the_info_prompt() -> None:
    prompt, _ = build_info_agent_request(_PROMPT, _history(), _CONTEXT)

    assert prompt == _PROMPT


def test_stored_memory_and_knowledge_never_reach_the_system_prompt() -> None:
    prompt, _ = build_info_agent_request(_PROMPT, _history(), _CONTEXT)

    assert "Background:" not in prompt
    assert "System Context" not in prompt


def test_the_context_comes_after_the_conversation() -> None:
    history = _history()

    _, messages = build_info_agent_request(_PROMPT, history, _CONTEXT)

    assert messages[: len(history)] == history
    assert len(messages) == len(history) + 1
    assert isinstance(messages[-1], HumanMessage)
    assert "Background: likes Lemon" in messages[-1].content


def test_the_note_says_it_is_not_a_user_message() -> None:
    _, messages = build_info_agent_request(_PROMPT, _history(), _CONTEXT)

    assert "not a user message" in messages[-1].content


def test_the_callers_message_list_is_not_changed() -> None:
    history = _history()

    build_info_agent_request(_PROMPT, history, _CONTEXT)

    assert len(history) == 2


def test_without_any_context_the_conversation_is_sent_as_it_is() -> None:
    history = _history()

    prompt, messages = build_info_agent_request(_PROMPT, history, "")

    assert prompt == _PROMPT
    assert messages == history
