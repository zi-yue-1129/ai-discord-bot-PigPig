"""Tests that format artifacts in a model's reply never reach the Discord channel."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, AsyncIterator, List

import pytest
from langchain_core.messages import AIMessageChunk

from llm.utils import send_message as send_message_module

METADATA = "[Replying to @awen07712: '超級敷衍喔' (MessageID:1501223473899376792) | timestamp: 1777989968.522 (2026-05-05 14:06:08 UTC)]"


async def _stream(*pieces: str) -> AsyncIterator[tuple]:
    """Yields the pieces as streamed model chunks."""
    for piece in pieces:
        yield (AIMessageChunk(content=piece), {})


def _run(*pieces: str, monkeypatch: pytest.MonkeyPatch) -> tuple[List[str], str]:
    """Streams ``pieces`` through the real processor and records every edit."""
    edits: List[str] = []

    async def record_edit(message: Any, content: str, *args: Any, **kwargs: Any) -> bool:
        edits.append(content)
        return True

    async def no_delete() -> None:
        return None

    monkeypatch.setattr(send_message_module, "safe_edit_message", record_edit)
    current_message = SimpleNamespace(delete=no_delete)
    result, _ = asyncio.run(
        send_message_module._process_token_stream(
            _stream(*pieces),
            None,
            current_message,
            SimpleNamespace(),
            SimpleNamespace(guild=None),
            None,
        )
    )
    # Discord trims surrounding whitespace, so it is not part of the contract.
    return [edit.strip() for edit in edits], result


def test_a_well_formed_reply_is_sent_as_is(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _run("<som> 哈囉 ", "世界 <eom>", monkeypatch=monkeypatch)

    assert edits[-1] == "哈囉 世界"


def test_a_reply_missing_its_opening_marker_does_not_show_the_closing_one(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _run("你是「最頂的醫學博士」啊，", "這還用問嗎？ <eom>", monkeypatch=monkeypatch)

    assert edits[-1] == "你是「最頂的醫學博士」啊，這還用問嗎？"


def test_metadata_after_the_closing_marker_does_not_reach_the_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _run("嗚哇，這是在指控我嗎！ 😂 <eom> ", METADATA, monkeypatch=monkeypatch)

    assert edits[-1] == "嗚哇，這是在指控我嗎！ 😂"
    assert not any("Replying to" in edit or "timestamp" in edit for edit in edits)


def test_a_tool_call_placeholder_is_not_sent_as_the_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _run("[Assistant: Calling tool(s): add_reaction, send_sticker]", monkeypatch=monkeypatch)

    assert not any("Assistant" in edit or "Calling tool" in edit for edit in edits)
    assert edits[-1] == "..."


def test_a_reply_without_any_markers_is_still_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _run("沒有標記的回覆", monkeypatch=monkeypatch)

    assert edits[-1] == "沒有標記的回覆"


def test_thinking_without_markers_is_not_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _run("<think>先想一下</think>", "答案是 42", monkeypatch=monkeypatch)

    assert edits[-1] == "答案是 42"
