"""A tool call the model writes as text, or an imitated identity header, never reaches Discord.

Qwen sometimes answers an action request with text such as ``[add_reaction: 🤖]`` instead of a
real function call. The live bot posted ``<PigPig🐖 | UserID:… | MessageID:…> [add_reaction: 🤖]``
to a channel on 2026-11-10. These tests use the names of the tools the sender is given.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, List

import pytest
from langchain_core.messages import AIMessageChunk

from llm.utils import send_message as send_message_module
from llm.utils.reply_sanitizer import sanitize_reply

_MODEL = {"langgraph_node": "model"}
_NAMES = ("add_reaction", "change_own_nickname", "send_sticker")


class _Tool:
    """A bound tool; only its name matters to the sender."""

    def __init__(self, name: str) -> None:
        self.name = name


class _Lang:
    """Language manager stand-in with a fixed empty-reply text."""

    def translate(self, *keys: str, **kwargs: Any) -> str:
        return "EMPTY_FALLBACK" if "empty_fallback" in keys else "…"


def _stream(pieces: List[str], monkeypatch: pytest.MonkeyPatch, extra: List[AIMessageChunk] = ()) -> tuple:
    """Feeds the pieces to the sender and returns every text it showed, in order, and the deletes."""
    edits: List[str] = []
    deleted: List[bool] = []

    async def record_edit(message: Any, content: str, *args: Any, **kwargs: Any) -> bool:
        edits.append(content)
        return True

    async def record_send(channel: Any, content: str, *args: Any, **kwargs: Any) -> Any:
        edits.append(content)
        return SimpleNamespace(delete=_delete)

    async def _delete() -> None:
        deleted.append(True)

    async def stream():
        for piece in pieces:
            yield AIMessageChunk(content=piece), _MODEL
        for chunk in extra:
            yield chunk, _MODEL

    monkeypatch.setattr(send_message_module, "safe_edit_message", record_edit)
    monkeypatch.setattr(send_message_module, "_safe_send_message", record_send)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(
            send_message_module._process_token_stream(
                stream(),
                None,
                SimpleNamespace(delete=_delete),
                SimpleNamespace(),
                SimpleNamespace(guild=SimpleNamespace(id=1)),
                _Lang(),
                update_interval=0,
                tools=[_Tool(name) for name in _NAMES],
            )
        )
    finally:
        loop.close()
    return edits, deleted


@pytest.mark.parametrize(
    "raw",
    [
        "<PigPig🐖 | UserID:1208661941539704852 | MessageID:1569611316782694401> [add_reaction: 🤖]",
        "[PigPig🐖 | UserID:1208661941539704852 | MessageID:1569612427459301439] [add_reaction: 🤖] <eom>",
    ],
)
def test_the_real_leaked_replies_leave_nothing_to_post(raw: str) -> None:
    assert sanitize_reply(raw, tool_names=_NAMES) == ""


@pytest.mark.parametrize(
    "raw",
    [
        "好喔 [add_reaction: 👍] 收到",
        "好喔 [change_own_nickname](小豬豬) 收到",
        "好喔 change_own_nickname(name=\"小豬豬\") 收到",
        "好喔 [send_sticker] 收到",
        "<som>好喔 [add_reaction: 👍] 收到<eom>",
        # Forms Qwen wrote in a replay of the real conversation on 2026-11-10.
        "好喔 <change_own_nickname>小豬豬</change_own_nickname> 收到",
        "好喔 <change_own_nickname:小豬豬> 收到",
        '好喔 <tool_code>\n{"name": "change_own_nickname", "arguments": {"new_nickname": "小豬豬"}}\n</tool_code> 收到',
        "好喔 <function=add_reaction>\n<parameter=emoji>\n🐖\n</parameter>\n</function>\n</tool_call> 收到",
    ],
)
def test_tool_calls_written_as_text_are_removed(raw: str) -> None:
    assert sanitize_reply(raw, tool_names=_NAMES) == "好喔 收到"


def test_ordinary_brackets_and_a_tool_named_in_prose_stay() -> None:
    raw = "[笑] 我可以用 add_reaction 幫你按讚 (真的)"

    assert sanitize_reply(raw, tool_names=_NAMES) == raw


def test_a_tool_name_unknown_to_the_sender_is_not_touched() -> None:
    assert sanitize_reply("看看 [weather: 台北]", tool_names=_NAMES) == "看看 [weather: 台北]"


def test_a_tool_written_as_text_is_never_shown_while_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _stream(["<som>好喔 [add_", "reaction: 👍", "] 收到<eom>"], monkeypatch)

    assert all("add_reaction" not in text and "[add_" not in text for text in edits)
    assert edits[-1] == "好喔 收到"


def test_a_tool_code_block_is_never_shown_while_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _stream(["<som>好喔 <tool_", 'code>{"name": "send_sticker"}</tool_code>', " 收到<eom>"], monkeypatch)

    assert all("send_sticker" not in text and "tool_code" not in text for text in edits)
    assert edits[-1] == "好喔  收到"


def test_a_bare_function_block_is_never_shown_while_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    pieces = ["<som>好喔 <func", "tion=add_reaction>\n<parameter=emoji>\n🐖\n</parameter>\n</function>\n</tool_call>", " 收到<eom>"]

    edits, _ = _stream(pieces, monkeypatch)

    assert all("add_reaction" not in text and "parameter" not in text for text in edits)
    assert edits[-1].split() == ["好喔", "收到"]


def test_an_identity_header_inside_the_markers_is_never_shown(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _stream(["<som>[PigPig🐖 | UserID:12", "08661941539704852 | MessageID:9] 嗨", "<eom>"], monkeypatch)

    assert all("UserID" not in text for text in edits)
    assert edits[-1] == "嗨"


def test_a_reply_that_is_only_tool_text_falls_back_when_no_tool_ran(monkeypatch: pytest.MonkeyPatch) -> None:
    edits, _ = _stream(["<som>[add_reaction: 🤖]<eom>"], monkeypatch)

    assert edits == ["EMPTY_FALLBACK"]


def test_a_reply_that_is_only_tool_text_posts_nothing_when_a_tool_really_ran(monkeypatch: pytest.MonkeyPatch) -> None:
    call = AIMessageChunk(
        content="",
        tool_call_chunks=[{"name": "add_reaction", "args": '{"emoji": "🤖"}', "id": "call-1", "index": 0}],
    )

    edits, deleted = _stream(["<som>[add_reaction: 🤖]<eom>"], monkeypatch, extra=[call])

    assert edits == []
    assert deleted == [True]
