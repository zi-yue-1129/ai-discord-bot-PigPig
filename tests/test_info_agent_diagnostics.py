"""The info agent's request and answer are logged by shape only, so a failure can be compared with a replay.

Since 2026-11-03 the live info agent wrote text instead of calling tools in every request, while a
replay of similar requests called the right tool almost every time. The log line shows what the live
request looked like without storing any member's words.
"""

from __future__ import annotations

from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from llm.utils.tool_trace import describe_info_agent_request

_SECRET = "我的秘密內容"


def _sent() -> list:
    return [
        HumanMessage(content=[{"type": "text", "text": _SECRET}, {"type": "image_url", "image_url": {"url": "https://x/1.png"}}]),
        HumanMessage(content=_SECRET),
        AIMessage(content=_SECRET),
        HumanMessage(content=_SECRET),
    ]


def _answer() -> list:
    return [
        AIMessage(content="", tool_calls=[{"name": "internet_search", "args": {"query": _SECRET}, "id": "c1"}],
                  response_metadata={"finish_reason": "tool_calls"}),
        ToolMessage(content=_SECRET, tool_call_id="c1"),
        AIMessage(content="", response_metadata={"finish_reason": "stop"}),
    ]


def _line(answer: list) -> str:
    tools = [SimpleNamespace(name="internet_search"), SimpleNamespace(name="play_music")]
    return describe_info_agent_request(_sent(), "SYSTEM PROMPT", tools, answer)


def test_the_role_order_and_the_last_role_are_shown_with_runs_counted() -> None:
    line = _line(_answer())

    assert "roles=human x2,ai,human" in line
    assert "last=human" in line


def test_tool_count_prompt_size_and_images_are_shown() -> None:
    line = _line(_answer())

    assert "tools=2" in line
    assert f"prompt_chars={len('SYSTEM PROMPT') + 4 * len(_SECRET)}" in line
    assert "images=1" in line


def test_the_first_model_answer_gives_finish_reason_and_tool_call_count() -> None:
    line = _line(_answer())

    assert "finish_reason=tool_calls" in line
    assert "tool_calls=1" in line


def test_a_text_answer_reports_zero_tool_calls() -> None:
    line = _line([AIMessage(content="[internet_search(query=x)]", response_metadata={"finish_reason": "stop"})])

    assert "finish_reason=stop" in line
    assert "tool_calls=0" in line


def test_no_message_content_reaches_the_log() -> None:
    assert _SECRET not in _line(_answer())


def test_a_system_message_in_the_list_is_named_too() -> None:
    line = describe_info_agent_request([SystemMessage(content="x"), HumanMessage(content="y")], "", [], [])

    assert "roles=system,human" in line
    assert "finish_reason=None" in line
