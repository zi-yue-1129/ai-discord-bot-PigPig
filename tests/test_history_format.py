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
