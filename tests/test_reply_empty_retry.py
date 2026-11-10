"""An empty reply (no postable text and no tool call) is asked again once before the fallback.

On 2026-11-10 the live Qwen answered "改" (change your nickname) twice with completely empty output,
and the bot posted "不知道該怎麼回覆你了". The same request replayed later got the tool call 12 of 12
times, so one more attempt recovers most of these.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, List

import pytest
from langchain_core.messages import AIMessageChunk, HumanMessage

from llm.utils import send_message as send_message_module
from llm.utils.reply_retry import EMPTY_REPLY_REMINDER, run_with_empty_retry
from llm.utils.send_message import EmptyReplyError

_MODEL = {"langgraph_node": "model"}


class _Lang:
    """Language manager stand-in with a fixed empty-reply text."""

    def translate(self, *keys: str, **kwargs: Any) -> str:
        return "EMPTY_FALLBACK" if "empty_fallback" in keys else "…"


def _process(chunks: List[AIMessageChunk], monkeypatch: pytest.MonkeyPatch, empty_fallback: bool) -> tuple:
    """Runs the stream processor and returns (result or raised error, edits, deletes)."""
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
        for chunk in chunks:
            yield chunk, _MODEL

    monkeypatch.setattr(send_message_module, "safe_edit_message", record_edit)
    monkeypatch.setattr(send_message_module, "_safe_send_message", record_send)
    loop = asyncio.new_event_loop()
    try:
        outcome = loop.run_until_complete(
            send_message_module._process_token_stream(
                stream(),
                None,
                SimpleNamespace(delete=_delete),
                SimpleNamespace(),
                SimpleNamespace(guild=SimpleNamespace(id=1)),
                _Lang(),
                update_interval=0,
                tools=[SimpleNamespace(name="change_own_nickname")],
                empty_fallback=empty_fallback,
            )
        )
    except EmptyReplyError as error:
        outcome = error
    finally:
        loop.close()
    return outcome, edits, deleted


def _empty_stop() -> AIMessageChunk:
    return AIMessageChunk(content="", response_metadata={"finish_reason": "stop"},
                          usage_metadata={"input_tokens": 9000, "output_tokens": 1, "total_tokens": 9001})


def test_an_empty_reply_raises_without_posting_when_a_retry_will_follow(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, edits, deleted = _process([_empty_stop()], monkeypatch, empty_fallback=False)

    assert isinstance(outcome, EmptyReplyError)
    assert edits == []
    assert deleted == []


def test_the_error_carries_the_finish_reason_and_token_count(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, _, _ = _process([_empty_stop()], monkeypatch, empty_fallback=False)

    assert outcome.finish_reason == "stop"
    assert outcome.output_tokens == 1


def test_a_reply_that_is_only_tool_text_also_counts_as_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, edits, _ = _process([AIMessageChunk(content="<som> [change_own_nickname: 小豬] <eom>")], monkeypatch, empty_fallback=False)

    assert isinstance(outcome, EmptyReplyError)
    assert edits == []


def test_a_real_tool_call_is_never_treated_as_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    call = AIMessageChunk(
        content="",
        tool_call_chunks=[{"name": "change_own_nickname", "args": '{"new_nickname": "小豬"}', "id": "c1", "index": 0}],
    )

    outcome, edits, deleted = _process([call], monkeypatch, empty_fallback=False)

    assert not isinstance(outcome, EmptyReplyError)
    assert edits == []
    assert deleted == [True]


def test_without_a_retry_the_usual_fallback_is_posted(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, edits, _ = _process([_empty_stop()], monkeypatch, empty_fallback=True)

    assert edits == ["EMPTY_FALLBACK"]
    assert outcome[0] == "EMPTY_FALLBACK"


def _run(attempt: Any, messages: List[Any]) -> tuple:
    seen: List[EmptyReplyError] = []
    result = asyncio.run(run_with_empty_retry(attempt, messages, on_empty=seen.append))
    return result, seen


def test_an_empty_first_reply_is_asked_once_more_with_the_reminder() -> None:
    calls: List[tuple] = []

    async def attempt(messages: List[Any], empty_fallback: bool) -> str:
        calls.append((list(messages), empty_fallback))
        if len(calls) == 1:
            raise EmptyReplyError("stop", 1, "")
        return "<som>好<eom>"

    history = [HumanMessage(content="改")]
    result, seen = _run(attempt, history)

    assert result == "<som>好<eom>"
    assert len(seen) == 1
    assert [fallback for _, fallback in calls] == [False, True]
    assert calls[1][0][:-1] == history
    assert calls[1][0][-1].content == EMPTY_REPLY_REMINDER
    assert history == [HumanMessage(content="改")]


def test_a_reply_with_text_or_a_tool_call_is_not_asked_again() -> None:
    calls: List[bool] = []

    async def attempt(messages: List[Any], empty_fallback: bool) -> str:
        calls.append(empty_fallback)
        return ""

    result, seen = _run(attempt, [HumanMessage(content="改")])

    assert result == ""
    assert calls == [False]
    assert seen == []


def test_the_reminder_asks_for_tagged_text_and_a_real_function_call() -> None:
    assert "<som>" in EMPTY_REPLY_REMINDER
    assert "function call" in EMPTY_REPLY_REMINDER
