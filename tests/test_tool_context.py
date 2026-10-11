"""Tests for how the info agent's tool activity is handed to the reply agent."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from llm.utils.tool_context import build_message_agent_history


def _tool_round() -> list:
    return [
        HumanMessage(content="[alice | UserID:1 | MessageID:2] <som> 有哪些貼圖？ <eom> [timestamp: 1.0 (2026-01-01 00:00:00 UTC)]"),
        AIMessage(content="", tool_calls=[{"name": "get_guild_stickers", "args": {}, "id": "call-1"}]),
        ToolMessage(content="Stickers: wave, cheer", name="get_guild_stickers", tool_call_id="call-1"),
    ]


def test_conversation_messages_are_kept_untouched_and_in_order() -> None:
    history = build_message_agent_history(_tool_round(), history_length=1)

    assert history[0].content.startswith("[alice | UserID:1")
    assert len(history) == 2


def test_tool_results_are_folded_into_one_internal_block_at_the_end() -> None:
    history = build_message_agent_history(_tool_round(), history_length=1)

    block = history[-1]
    assert isinstance(block, HumanMessage)
    assert "get_guild_stickers" in block.content
    assert "Stickers: wave, cheer" in block.content


def test_the_block_tells_the_model_not_to_repeat_it() -> None:
    block = build_message_agent_history(_tool_round(), history_length=1)[-1]

    assert "never" in block.content.lower()


def test_no_fake_assistant_turn_is_created_for_tool_calls() -> None:
    history = build_message_agent_history(_tool_round(), history_length=1)

    assert not any(isinstance(message, AIMessage) for message in history)
    assert not any("Calling tool" in str(message.content) for message in history)


def test_no_system_style_header_is_used_for_tool_results() -> None:
    history = build_message_agent_history(_tool_round(), history_length=1)

    assert not any("[System:" in str(message.content) for message in history)


def test_text_the_info_agent_wrote_next_to_its_tool_calls_is_not_forwarded() -> None:
    messages = _tool_round()
    messages[1] = AIMessage(
        content="使用者想知道貼圖", tool_calls=[{"name": "get_guild_stickers", "args": {}, "id": "call-1"}]
    )

    history = build_message_agent_history(messages, history_length=1)

    assert "使用者想知道貼圖" not in "".join(str(message.content) for message in history)


def test_the_info_agents_final_text_is_never_replayed_as_the_bots_own_words() -> None:
    """The info agent must only call tools; a conclusion such as "I can't play that" would
    otherwise reach the reply agent as if the bot had said it and be repeated to the user."""
    messages = _tool_round() + [
        AIMessage(content="[PigPig🐖 | UserID:9 | MessageID:8] <som> I can't play that right now. <eom>"),
    ]

    history = build_message_agent_history(messages, history_length=1)

    assert not any(isinstance(message, AIMessage) for message in history)
    assert "can't play" not in "".join(str(message.content) for message in history)


def test_earlier_assistant_messages_in_the_conversation_history_are_kept() -> None:
    messages = [
        HumanMessage(content="hi"),
        AIMessage(content="[PigPig🐖 | UserID:9 | MessageID:8] <som> hello <eom>"),
        HumanMessage(content="播放綠光"),
    ] + _tool_round()[1:]

    history = build_message_agent_history(messages, history_length=3)

    assert isinstance(history[1], AIMessage)
    assert "hello" in history[1].content


def test_several_tool_results_are_all_included_in_call_order() -> None:
    messages = _tool_round() + [
        ToolMessage(content="Emojis: 🐷", name="get_guild_emojis", tool_call_id="call-2"),
    ]

    block = build_message_agent_history(messages, history_length=1)[-1].content

    assert block.index("get_guild_stickers") < block.index("get_guild_emojis")


def test_list_shaped_tool_content_is_reduced_to_its_text() -> None:
    messages = _tool_round()
    messages[2] = ToolMessage(
        content=[{"type": "text", "text": "Stickers: wave"}], name="get_guild_stickers", tool_call_id="call-1"
    )

    block = build_message_agent_history(messages, history_length=1)[-1].content

    assert "Stickers: wave" in block
    assert "'type'" not in block


def test_without_tool_activity_the_messages_pass_through() -> None:
    messages = [HumanMessage(content="hi"), AIMessage(content="analysis text")]

    assert build_message_agent_history(messages, history_length=2) == messages
