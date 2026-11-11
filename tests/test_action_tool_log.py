"""The message agent's action tools (nickname, reactions, stickers...) show up in the logs.

Only the info agent's tool calls used to be logged, so an action tool that really ran (the bot did
change its nickname) looked in the logs as if it had never been called.
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterator, List, Tuple
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from llm.callbacks import ToolLogCallbackHandler
from llm.orchestrator import stream_message_agent
from llm.utils.tool_trace import ToolCallRecord, describe_reply_tools


class _RecordingLogger:
    """Collects (level, message) pairs."""

    def __init__(self) -> None:
        self.records: List[Tuple[str, str]] = []

    def info(self, message: str) -> None:
        self.records.append(("info", message))

    def error(self, message: str) -> None:
        self.records.append(("error", message))


class _ToolCallingModel(GenericFakeChatModel):
    """A fake chat model that accepts tools and answers from a fixed list of messages."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> "_ToolCallingModel":
        return self


def test_the_log_handler_remembers_which_tools_started() -> None:
    handler = ToolLogCallbackHandler(_RecordingLogger())

    asyncio.run(handler.on_tool_start({"name": "change_own_nickname"}, "{}", run_id=uuid4()))
    asyncio.run(handler.on_tool_start({"name": "add_reaction"}, "{}", run_id=uuid4()))

    assert handler.started_tools == ["change_own_nickname", "add_reaction"]


def test_a_tool_the_message_agent_runs_while_streaming_is_logged() -> None:
    nicknames: List[str] = []

    @tool
    async def change_own_nickname(new_nickname: str) -> str:
        """Changes the bot's nickname."""
        nicknames.append(new_nickname)
        return f"Successfully changed my local nickname to {new_nickname}"

    answers: Iterator[AIMessage] = iter([
        AIMessage(content="<som> 好 <eom>", tool_calls=[
            {"name": "change_own_nickname", "args": {"new_nickname": "測試豬"}, "id": "call-1"},
        ]),
        AIMessage(content="<som> 改好了 <eom>"),
    ])
    # The fake model cannot stream tool calls, so it answers whole messages.
    agent = create_agent(model=_ToolCallingModel(messages=answers, disable_streaming=True), tools=[change_own_nickname])
    logger = _RecordingLogger()
    handler = ToolLogCallbackHandler(logger)

    async def consume() -> List[Any]:
        return [chunk async for chunk in stream_message_agent(agent, [HumanMessage("改名")], [handler])]

    chunks = asyncio.run(consume())

    assert chunks
    assert nicknames == ["測試豬"]
    assert handler.started_tools == ["change_own_nickname"]
    assert any("Tool started: change_own_nickname" in message for _, message in logger.records)


def test_the_reply_log_lists_the_action_tools_next_to_the_info_tools() -> None:
    info_calls = [ToolCallRecord(name="internet_search", arguments="{}", status="ok", result_chars=5)]

    text = describe_reply_tools(info_calls, ["change_own_nickname"])

    assert text == "tools_called: ['internet_search'], actions_called: ['change_own_nickname']"


def test_the_reply_log_says_when_no_action_tool_ran() -> None:
    assert describe_reply_tools([], []) == "tools_called: [], actions_called: []"
