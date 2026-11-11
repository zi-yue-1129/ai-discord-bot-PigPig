"""The bot's own "..." placeholder never reaches the agents as the newest history message.

The bot replies "..." before it reads the channel history, so that placeholder was the newest
message the agents saw: the conversation ended with the bot's own (empty) turn instead of the
message to answer, and models continued that turn instead of handling the request.
"""

from __future__ import annotations

import asyncio
import datetime
from types import SimpleNamespace
from typing import Any, List

from llm.memory.short_term import ShortTermMemoryProvider

BOT_ID = 999


class _Channel:
    """Yields messages newest first, like discord.py."""

    def __init__(self, newest_first: List[Any]) -> None:
        self._messages = newest_first
        self.limits: List[int] = []

    async def history(self, limit: int):
        self.limits.append(limit)
        for message in self._messages[:limit]:
            yield message


def _message(message_id: int, author_id: int, text: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=message_id, content=text, attachments=[], embeds=[], reactions=[], reference=None,
        created_at=datetime.datetime(2026, 11, 11, 2, 39, tzinfo=datetime.timezone.utc),
        author=SimpleNamespace(name="PigPig🐖" if author_id == BOT_ID else "starpig", id=author_id, bot=author_id == BOT_ID),
    )


def _texts(rendered: list) -> List[str]:
    return ["".join(part["text"] for part in m.content if part["type"] == "text") for m in rendered]


def _get(oldest_first: List[Any], trigger_id: int, limit: int = 10) -> list:
    channel = _Channel(list(reversed(oldest_first)))
    provider = ShortTermMemoryProvider(bot=SimpleNamespace(user=SimpleNamespace(id=BOT_ID)), limit=limit)
    return asyncio.run(provider.get(SimpleNamespace(id=trigger_id, channel=channel)))


def test_the_placeholder_after_the_message_is_left_out() -> None:
    rendered = _get([_message(1, 42, "早"), _message(2, 42, "改暱稱"), _message(3, BOT_ID, "...")], trigger_id=2)

    texts = _texts(rendered)
    assert len(texts) == 2
    assert "改暱稱" in texts[-1]


def test_the_message_to_answer_is_always_the_newest_entry() -> None:
    rendered = _get([_message(1, 42, "早"), _message(2, 42, "改暱稱"), _message(3, BOT_ID, "..."), _message(4, 7, "插話")],
                    trigger_id=2)

    assert "改暱稱" in _texts(rendered)[-1]


def test_the_history_still_holds_the_configured_number_of_messages() -> None:
    older = [_message(i, 42, f"m{i}") for i in range(1, 9)]
    rendered = _get(older + [_message(9, BOT_ID, "...")], trigger_id=8, limit=5)

    texts = _texts(rendered)
    assert len(texts) == 5
    assert "m8" in texts[-1] and "m4" in texts[0]
