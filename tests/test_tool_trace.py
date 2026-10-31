"""Tests for the log lines that say which tools the info agent really called."""

from __future__ import annotations

import asyncio
from typing import Any, List, Tuple
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from llm.callbacks import ToolLogCallbackHandler
from llm.utils.tool_trace import collect_tool_calls, describe_info_agent_outcome


def _round(result: str = "sunny", status: str = "success") -> list:
    return [
        HumanMessage(content="[alice | UserID:1 | MessageID:2] 幫我查天氣"),
        AIMessage(content="", tool_calls=[{"name": "internet_search", "args": {"query": "台北天氣"}, "id": "call-1"}]),
        ToolMessage(content=result, name="internet_search", tool_call_id="call-1", status=status),
    ]


def test_a_finished_call_is_reported_with_name_arguments_and_result_size() -> None:
    calls = collect_tool_calls(_round("sunny"), history_length=1)

    assert len(calls) == 1
    assert calls[0].name == "internet_search"
    assert "台北天氣" in calls[0].arguments
    assert calls[0].status == "ok"
    assert calls[0].result_chars == len("sunny")


def test_a_tool_that_failed_is_reported_as_an_error() -> None:
    calls = collect_tool_calls(_round("boom", status="error"), history_length=1)

    assert calls[0].status == "error"


def test_a_call_without_a_result_is_reported_as_such() -> None:
    messages = _round()[:2]

    calls = collect_tool_calls(messages, history_length=1)

    assert calls[0].status == "no_result"
    assert calls[0].result_chars == 0


def test_the_conversation_itself_is_never_mistaken_for_tool_activity() -> None:
    messages = _round()

    assert collect_tool_calls(messages, history_length=3) == []


def test_calls_are_listed_in_the_order_they_were_made() -> None:
    messages = [
        HumanMessage(content="hi"),
        AIMessage(content="", tool_calls=[{"name": "first", "args": {}, "id": "a"}, {"name": "second", "args": {}, "id": "b"}]),
        ToolMessage(content="2", name="second", tool_call_id="b"),
        ToolMessage(content="1", name="first", tool_call_id="a"),
    ]

    assert [call.name for call in collect_tool_calls(messages, history_length=1)] == ["first", "second"]


def test_long_arguments_are_cut_so_one_log_line_stays_readable() -> None:
    messages = _round()
    messages[1] = AIMessage(content="", tool_calls=[{"name": "internet_search", "args": {"query": "x" * 5000}, "id": "call-1"}])

    calls = collect_tool_calls(messages, history_length=1)

    assert len(calls[0].arguments) <= 200


def test_the_summary_names_every_tool_and_its_outcome() -> None:
    text = describe_info_agent_outcome(_round("sunny"), history_length=1)

    assert "internet_search" in text
    assert "ok" in text
    assert "5 chars" in text


def test_the_summary_says_plainly_when_no_tool_was_called() -> None:
    text = describe_info_agent_outcome([HumanMessage(content="hi"), AIMessage(content="")], history_length=1)

    assert "no tool calls" in text


def test_the_summary_shows_text_the_agent_wrote_instead_of_calling_tools() -> None:
    text = describe_info_agent_outcome([HumanMessage(content="hi"), AIMessage(content="No tools needed.")], history_length=1)

    assert "no tool calls" in text
    assert "No tools needed." in text


class _RecordingLogger:
    """Collects log calls as (level, message)."""

    def __init__(self) -> None:
        self.records: List[Tuple[str, str]] = []

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.records.append(("info", message))

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.records.append(("error", message))


class _Clock:
    """A clock that moves forward by a fixed step on every read."""

    def __init__(self, step: float) -> None:
        self._now = 100.0
        self._step = step

    def __call__(self) -> float:
        self._now += self._step
        return self._now


def test_the_callback_logs_start_and_end_with_the_duration() -> None:
    logger = _RecordingLogger()
    handler = ToolLogCallbackHandler(logger, clock=_Clock(1.5))
    run_id = uuid4()

    asyncio.run(handler.on_tool_start({"name": "internet_search"}, "{'query': 'x'}", run_id=run_id))
    asyncio.run(handler.on_tool_end("sunny", run_id=run_id))

    assert [level for level, _ in logger.records] == ["info", "info"]
    assert "internet_search" in logger.records[0][1]
    assert "1.50s" in logger.records[1][1]
    assert "5 chars" in logger.records[1][1]


def test_the_callback_logs_a_failing_tool_at_error_level() -> None:
    logger = _RecordingLogger()
    handler = ToolLogCallbackHandler(logger, clock=_Clock(0.5))
    run_id = uuid4()

    asyncio.run(handler.on_tool_start({"name": "play_music"}, "{}", run_id=run_id))
    asyncio.run(handler.on_tool_error(RuntimeError("no voice channel"), run_id=run_id))

    level, message = logger.records[-1]
    assert level == "error"
    assert "play_music" in message
    assert "no voice channel" in message


def test_a_finish_without_a_start_still_logs_instead_of_crashing() -> None:
    logger = _RecordingLogger()
    handler = ToolLogCallbackHandler(logger, clock=_Clock(1.0))

    asyncio.run(handler.on_tool_end("ok", run_id=uuid4()))

    assert logger.records and logger.records[-1][0] == "info"
