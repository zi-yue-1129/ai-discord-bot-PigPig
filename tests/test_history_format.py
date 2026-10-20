"""Tests for how channel history is rendered into the model's context."""

from __future__ import annotations

import asyncio
import datetime
from types import SimpleNamespace
from typing import Any, List

from langchain_core.messages import AIMessage, HumanMessage

from llm.memory.short_term import ShortTermMemoryProvider

BOT_ID = 999


class _Channel:
    def __init__(self, messages: List[Any]) -> None:
        self._messages = messages

    async def history(self, limit: int):
        for message in self._messages[:limit]:
            yield message


def _message(message_id: int, author_id: int, name: str, text: str, *, bot: bool, reference: Any = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=message_id,
        content=text,
        attachments=[],
        embeds=[],
        reactions=[],
        reference=reference,
        created_at=datetime.datetime(2026, 5, 5, 14, 6, 8, tzinfo=datetime.timezone.utc),
        author=SimpleNamespace(name=name, id=author_id, bot=bot),
    )


def _render(*messages: SimpleNamespace) -> list:
    bot = SimpleNamespace(user=SimpleNamespace(id=BOT_ID))
    provider = ShortTermMemoryProvider(bot=bot, limit=10)
    newest_first = list(reversed(messages))
    return asyncio.run(provider.get(SimpleNamespace(channel=_Channel(newest_first))))


def _text(message: Any) -> str:
    return "".join(part["text"] for part in message.content if part["type"] == "text")


def test_user_messages_keep_their_identity_and_time() -> None:
    rendered = _render(_message(1, 42, "alice", "你好", bot=False))

    assert isinstance(rendered[0], HumanMessage)
    text = _text(rendered[0])
    assert "alice | UserID:42 | MessageID:1" in text
    assert "<som> 你好 <eom>" in text
    assert "timestamp:" in text


def test_the_bots_own_past_messages_keep_their_message_id_for_tool_targeting() -> None:
    rendered = _render(_message(2, BOT_ID, "PigPig🐖", "哈囉！", bot=True))

    assert isinstance(rendered[0], AIMessage)
    assert _text(rendered[0]) == "[PigPig🐖 | UserID:999 | MessageID:2] <som> 哈囉！ <eom>"


def test_the_bots_past_messages_carry_no_trailing_metadata_to_imitate() -> None:
    reference = SimpleNamespace(message_id=1, resolved=None, cached_message=None)
    rendered = _render(_message(2, BOT_ID, "PigPig🐖", "好喔", bot=True, reference=reference))

    text = _text(rendered[0])
    for artifact in ("timestamp", "reply_to", "Replying", "reactions"):
        assert artifact not in text
    assert text.endswith("<eom>")


def test_an_empty_bot_message_is_an_empty_reply() -> None:
    rendered = _render(_message(2, BOT_ID, "PigPig🐖", "", bot=True))

    assert _text(rendered[0]) == "[PigPig🐖 | UserID:999 | MessageID:2] <som> <eom>"


def test_other_bots_keep_their_full_metadata() -> None:
    rendered = _render(_message(3, 555, "OtherBot", "beep", bot=True))

    text = _text(rendered[0])
    assert "OtherBot | UserID:555 | MessageID:3" in text
    assert "timestamp:" in text


def _named(message_id: int, author_id: int, name: str, display_name: str, text: str, *, bot: bool) -> SimpleNamespace:
    message = _message(message_id, author_id, name, text, bot=bot)
    message.author.display_name = display_name
    return message


def test_another_bots_message_is_not_shown_as_the_bots_own_turn() -> None:
    rendered = _render(_message(3, 555, "OtherBot", "beep", bot=True))

    assert isinstance(rendered[0], HumanMessage)
    assert rendered[0].name == "OtherBot_555"


def test_another_bots_message_is_labelled_as_a_bot() -> None:
    rendered = _render(_message(3, 555, "OtherBot", "beep", bot=True))

    assert _text(rendered[0]).startswith("[BOT OtherBot | UserID:555 | MessageID:3] <som> beep <eom>")


def test_the_bots_own_message_is_the_only_assistant_turn() -> None:
    rendered = _render(
        _message(1, 42, "alice", "hi", bot=False),
        _message(2, 555, "OtherBot", "beep", bot=True),
        _message(3, BOT_ID, "PigPig🐖", "哈囉", bot=True),
    )

    assert [type(message) for message in rendered] == [HumanMessage, HumanMessage, AIMessage]


def test_a_member_with_a_display_name_is_labelled_with_both_names() -> None:
    rendered = _render(_named(1, 42, "alice", "愛麗絲", "你好", bot=False))

    assert _text(rendered[0]).startswith("[愛麗絲 (alice) | UserID:42 | MessageID:1] <som> 你好 <eom>")


def test_a_member_whose_display_name_equals_the_username_is_labelled_once() -> None:
    rendered = _render(_named(1, 42, "alice", "alice", "你好", bot=False))

    assert _text(rendered[0]).startswith("[alice | UserID:42 | MessageID:1] <som> 你好 <eom>")


def test_the_bots_own_label_is_not_changed_by_a_display_name() -> None:
    rendered = _render(_named(2, BOT_ID, "PigPig🐖", "豬豬", "哈囉！", bot=True))

    assert _text(rendered[0]) == "[PigPig🐖 | UserID:999 | MessageID:2] <som> 哈囉！ <eom>"
