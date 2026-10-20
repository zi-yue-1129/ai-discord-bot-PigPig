"""A reply that never stops is cut, the model stream is closed, and ordinary replies are left alone."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, AsyncIterator, Dict, List

import pytest
from langchain_core.messages import AIMessageChunk

from llm.utils import send_message as send_message_module
from llm.utils.repetition_guard import MAX_REPLY_CHARS


@dataclass
class _Model:
    """A fake model stream that records how much of it was read and whether it was closed."""

    pieces: List[str]
    consumed: int = 0
    closed: bool = False

    async def stream(self) -> AsyncIterator[tuple]:
        """Yield the pieces as streamed chunks, noting the moment the consumer closes the stream."""
        try:
            for piece in self.pieces:
                self.consumed += 1
                yield (AIMessageChunk(content=piece), {})
        finally:
            self.closed = True


@dataclass
class _Discord:
    """What reached Discord: the latest text of every message the processor edited or sent."""

    texts: Dict[int, str] = field(default_factory=dict)
    order: List[int] = field(default_factory=list)
    messages: List[Any] = field(default_factory=list)  # keeps every message alive so ids stay unique

    def shown(self) -> str:
        """Return everything the channel displays, message after message."""
        return "".join(self.texts[key] for key in self.order)


def _run(pieces: List[str], monkeypatch: pytest.MonkeyPatch) -> tuple[_Model, _Discord, str]:
    """Stream ``pieces`` through the real processor with an update after every chunk."""
    model, discord_state = _Model(pieces), _Discord()

    async def record_edit(message: Any, content: str, *args: Any, **kwargs: Any) -> bool:
        if id(message) not in discord_state.texts:
            discord_state.order.append(id(message))
            discord_state.messages.append(message)
        discord_state.texts[id(message)] = content
        return True

    async def record_send(channel: Any, content: str, *args: Any, **kwargs: Any) -> Any:
        async def no_delete() -> None:
            return None

        sent = SimpleNamespace(delete=no_delete)
        await record_edit(sent, content)
        return sent

    async def no_delete() -> None:
        return None

    monkeypatch.setattr(send_message_module, "safe_edit_message", record_edit)
    monkeypatch.setattr(send_message_module, "_safe_send_message", record_send)
    result, _ = asyncio.run(
        send_message_module._process_token_stream(
            model.stream(),
            None,
            SimpleNamespace(delete=no_delete),
            SimpleNamespace(),
            SimpleNamespace(guild=None),
            None,
            update_interval=0,
        )
    )
    return model, discord_state, result


def test_a_reply_stuck_on_one_character_is_cut_and_the_model_stream_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    model, discord_state, result = _run(["<som>好的，"] + ["好"] * 5000, monkeypatch)

    assert model.closed
    assert model.consumed < 200
    assert discord_state.shown().strip() == "好的，好好好…"
    assert result == "<som>好的，好好好<eom>"


def test_a_reply_stuck_on_a_phrase_is_cut_after_one_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    model, discord_state, result = _run(["<som>我覺得"] + ["好吃好吃，"] * 400, monkeypatch)

    assert model.closed
    assert model.consumed < 100
    assert discord_state.shown().strip() == "我覺得好吃好吃，…"
    assert result == "<som>我覺得好吃好吃，<eom>"


def test_a_loop_inside_the_thinking_block_stops_the_stream_too(monkeypatch: pytest.MonkeyPatch) -> None:
    model, discord_state, result = _run(["<think>嗯，"] + ["嗯"] * 5000, monkeypatch)

    assert model.closed
    assert model.consumed < 200
    assert discord_state.shown().strip() == "..."
    assert result == "..."


def test_a_reply_beyond_the_size_cap_is_cut_and_the_stream_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    sentences = [f"第{number}句話。" for number in range(5000)]

    model, discord_state, result = _run(["<som>"] + sentences, monkeypatch)

    shown = discord_state.shown().rstrip("…")
    assert model.closed
    assert model.consumed < len(sentences)
    assert MAX_REPLY_CHARS - 20 <= len(shown) <= MAX_REPLY_CHARS
    assert discord_state.shown().endswith("…")
    assert result.startswith("<som>第0句話。第1句話。") and result.endswith("<eom>")
    assert len(discord_state.order) >= 3


def test_an_ordinary_reply_is_sent_in_full(monkeypatch: pytest.MonkeyPatch) -> None:
    pieces = ["<som>哈", "哈" * 30, " 好笑 <eom>"]

    model, discord_state, result = _run(pieces, monkeypatch)

    assert model.consumed == len(pieces)
    assert discord_state.shown().strip() == "哈" + "哈" * 30 + " 好笑"
    assert result == "".join(pieces)
