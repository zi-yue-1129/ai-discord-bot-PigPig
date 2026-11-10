"""Only the reply model's own text reaches Discord: no tool status, tool output or tool-call text."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from llm.utils import send_message as send_message_module
from llm.utils.reply_sanitizer import sanitize_reply

_MODEL = {"langgraph_node": "model"}
_TOOLS = {"langgraph_node": "tools"}


@dataclass
class _Discord:
    """The latest text of every message the processor edited or sent, in order."""

    texts: Dict[int, str] = field(default_factory=dict)
    order: List[int] = field(default_factory=list)
    keep: List[Any] = field(default_factory=list)

    def shown(self) -> str:
        return "".join(self.texts[key] for key in self.order)


class _Tool:
    """A tool that records every run."""

    name = "add_reaction"

    def __init__(self) -> None:
        self.runs = 0

    async def ainvoke(self, args: Any) -> str:
        self.runs += 1
        return "Reaction added"


class _Lang:
    """Gives the tool status line the bot shows while a tool runs."""

    def translate(self, *keys: str, **kwargs: Any) -> str:
        if "tools" in keys:
            return "🛠️ 正在使用 add_reaction..."
        return "…"


def _run(items: List[tuple], monkeypatch: pytest.MonkeyPatch, tools: Optional[list] = None) -> tuple[_Discord, str]:
    discord_state = _Discord()

    async def record_edit(message: Any, content: str, *args: Any, **kwargs: Any) -> bool:
        if id(message) not in discord_state.texts:
            discord_state.order.append(id(message))
            discord_state.keep.append(message)
        discord_state.texts[id(message)] = content
        return True

    async def record_send(channel: Any, content: str, *args: Any, **kwargs: Any) -> Any:
        sent = SimpleNamespace(delete=_no_delete)
        await record_edit(sent, content)
        return sent

    async def _no_delete() -> None:
        return None

    async def stream():
        for item in items:
            yield item

    monkeypatch.setattr(send_message_module, "safe_edit_message", record_edit)
    monkeypatch.setattr(send_message_module, "_safe_send_message", record_send)
    loop = asyncio.new_event_loop()
    try:
        result, _ = loop.run_until_complete(
            send_message_module._process_token_stream(
                stream(),
                None,
                SimpleNamespace(delete=_no_delete),
                SimpleNamespace(),
                SimpleNamespace(guild=None),
                _Lang(),
                update_interval=0,
                tools=tools,
            )
        )
    finally:
        loop.close()
    return discord_state, result


def _tool_call_chunk() -> AIMessageChunk:
    return AIMessageChunk(
        content="",
        tool_call_chunks=[{"name": "add_reaction", "args": '{"emoji": "🐷"}', "id": "call-1", "index": 0}],
    )


def test_a_tool_call_after_the_text_does_not_replace_the_reply_with_a_tool_status(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _Tool()
    discord_state, _ = _run(
        [(AIMessageChunk(content="<som>好喔，幫你按讚<eom>"), _MODEL), (_tool_call_chunk(), _MODEL)],
        monkeypatch,
        tools=[tool],
    )

    assert discord_state.shown() == "好喔，幫你按讚"
    assert "🛠️" not in discord_state.shown()


def test_the_sender_does_not_run_a_tool_the_agent_already_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _Tool()
    _run(
        [(AIMessageChunk(content="<som>好<eom>"), _MODEL), (_tool_call_chunk(), _MODEL)],
        monkeypatch,
        tools=[tool],
    )

    assert tool.runs == 0


def test_text_from_a_model_called_inside_a_tool_is_not_posted(monkeypatch: pytest.MonkeyPatch) -> None:
    discord_state, result = _run(
        [
            (AIMessageChunk(content="<som>完成了<eom>"), _MODEL),
            (AIMessageChunk(content="<som>INNER WRITER DRAFT<eom>"), _TOOLS),
            (ToolMessage(content="Reaction added", tool_call_id="call-1"), _TOOLS),
            (AIMessage(content="Model call limits exceeded: run limit (1/1)"), {"langgraph_node": "ModelCallLimitMiddleware.before_model"}),
        ],
        monkeypatch,
    )

    assert discord_state.shown() == "完成了"
    assert "INNER" not in result


@pytest.mark.parametrize(
    "pieces",
    [
        ["<som>好的", '<tool_call>{"name": "add_reaction", "arguments": {}}</tool_call>', "，按好了<eom>"],
        ["<som>好的", "<|tool_call>call:add_reaction{emoji:🐷}<tool_call|>", "，按好了<eom>"],
        ["<som>好的", "<tool_results>\n## get_server_info\n{\"members\": 3}\n</tool_results>", "，按好了<eom>"],
        ["<som>好的<tool_", 'call>{"name": "x"}</tool', "_call>，按好了<eom>"],
    ],
)
def test_tool_call_text_written_into_the_reply_is_hidden_while_streaming(
    pieces: List[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    discord_state, _ = _run([(AIMessageChunk(content=piece), _MODEL) for piece in pieces], monkeypatch)

    assert discord_state.shown() == "好的，按好了"


def test_tool_call_text_is_removed_in_the_fallback_path_too() -> None:
    raw = '好的<tool_call>{"name": "add_reaction"}</tool_call>，按好了<eom>'

    assert sanitize_reply(raw) == "好的，按好了"


def test_an_unclosed_tool_block_hides_the_rest_in_the_fallback_path() -> None:
    assert sanitize_reply("好的<tool_results>\n## get_server_info\n{}") == "好的"


def test_plain_streams_without_metadata_still_post(monkeypatch: pytest.MonkeyPatch) -> None:
    discord_state, _ = _run([(AIMessageChunk(content="<som>嗨<eom>"), {})], monkeypatch)

    assert discord_state.shown() == "嗨"
