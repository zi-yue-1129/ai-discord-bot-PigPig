"""The info agent cannot call tools forever: repeats are dropped and the total is capped."""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from llm.utils.tool_budget import ToolCallBudgetMiddleware


def _call(name: str, call_id: str, **arguments: Any) -> Dict[str, Any]:
    return {"name": name, "args": arguments, "id": call_id, "type": "tool_call"}


def _state(*messages: Any) -> Dict[str, Any]:
    return {"messages": list(messages)}


def _apply(middleware: ToolCallBudgetMiddleware, *messages: Any) -> Dict[str, Any]:
    """Runs the hook; returns the update (empty dict when it leaves the state alone)."""
    return middleware.after_model(_state(*messages), runtime=None) or {}


def test_first_calls_are_left_alone() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=8)
    reply = AIMessage(content="", id="a1", tool_calls=[_call("search", "c1", q="x"), _call("weather", "c2", city="y")])

    assert _apply(middleware, HumanMessage(content="hi"), reply) == {}


def test_a_call_already_made_in_an_earlier_round_is_dropped_and_the_run_ends() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=8)
    first = AIMessage(content="", id="a1", tool_calls=[_call("search", "c1", q="x")])
    result = ToolMessage(content="found", tool_call_id="c1", name="search")
    again = AIMessage(content="", id="a2", tool_calls=[_call("search", "c2", q="x")])

    update = _apply(middleware, HumanMessage(content="hi"), first, result, again)

    assert update["jump_to"] == "end"
    assert update["messages"][0].id == "a2" and update["messages"][0].tool_calls == []


def test_same_tool_with_other_arguments_is_a_new_call() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=8)
    first = AIMessage(content="", id="a1", tool_calls=[_call("search", "c1", q="x")])
    result = ToolMessage(content="found", tool_call_id="c1", name="search")
    other = AIMessage(content="", id="a2", tool_calls=[_call("search", "c2", q="y")])

    assert _apply(middleware, HumanMessage(content="hi"), first, result, other) == {}


def test_argument_order_does_not_hide_a_repeat() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=8)
    first = AIMessage(content="", id="a1", tool_calls=[_call("find", "c1", a=1, b=2)])
    result = ToolMessage(content="r", tool_call_id="c1", name="find")
    again = AIMessage(content="", id="a2", tool_calls=[_call("find", "c2", b=2, a=1)])

    assert _apply(middleware, first, result, again)["jump_to"] == "end"


def test_calls_over_the_budget_are_cut_and_the_run_ends_after_them() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=3)
    flood = AIMessage(content="", id="a1", tool_calls=[_call("search", f"c{i}", q=str(i)) for i in range(10)])

    update = _apply(middleware, HumanMessage(content="hi"), flood)

    kept = update["messages"][0].tool_calls
    assert [call["id"] for call in kept] == ["c0", "c1", "c2"]
    assert "jump_to" not in update, "the three allowed calls still have to run"


def test_an_exhausted_budget_ends_the_run() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=2)
    first = AIMessage(content="", id="a1", tool_calls=[_call("a", "c1"), _call("b", "c2")])
    results = [ToolMessage(content="r", tool_call_id="c1", name="a"), ToolMessage(content="r", tool_call_id="c2", name="b")]
    more = AIMessage(content="", id="a2", tool_calls=[_call("c", "c3")])

    update = _apply(middleware, HumanMessage(content="hi"), first, *results, more)

    assert update["jump_to"] == "end" and update["messages"][0].tool_calls == []


def test_the_same_call_twice_in_one_reply_is_kept_because_it_may_be_meant() -> None:
    """Rolling two dice is two identical roll_dice calls; only a repeat after a result is a loop."""
    middleware = ToolCallBudgetMiddleware(max_tool_calls=8)
    twice = AIMessage(content="", id="a1", tool_calls=[_call("roll_dice", "c1", sides=6), _call("roll_dice", "c2", sides=6)])

    assert _apply(middleware, HumanMessage(content="hi"), twice) == {}


def test_a_reply_without_tool_calls_is_left_alone() -> None:
    middleware = ToolCallBudgetMiddleware(max_tool_calls=8)

    assert _apply(middleware, HumanMessage(content="hi"), AIMessage(content="done", id="a1")) == {}


def test_budget_must_be_positive() -> None:
    with pytest.raises(ValueError, match="max_tool_calls"):
        ToolCallBudgetMiddleware(max_tool_calls=0)


@pytest.mark.asyncio
async def test_a_model_that_repeats_one_call_forever_runs_the_tool_once() -> None:
    """The live failure: 80 identical search calls in a row, one per model round."""
    runs: List[str] = []

    @tool
    def search(q: str) -> str:
        """Search for q."""
        runs.append(q)
        return f"result for {q}"

    def endless() -> Any:
        number = 0
        while True:
            number += 1
            yield AIMessage(content="", tool_calls=[_call("search", f"call-{number}", q="same")])

    class _Model(GenericFakeChatModel):
        def bind_tools(self, tools: Any, **kwargs: Any) -> "_Model":
            return self

    agent = create_agent(
        model=_Model(messages=endless()), tools=[search], middleware=[ToolCallBudgetMiddleware(max_tool_calls=8)]
    )

    result = await agent.ainvoke({"messages": [HumanMessage(content="find it")]}, config={"recursion_limit": 60})

    assert runs == ["same"]
    assert any(isinstance(message, ToolMessage) and "result for same" in message.content for message in result["messages"])


def test_the_budget_comes_from_llm_yaml_with_a_default(tmp_path: Any) -> None:
    from addons.settings import LLMConfig

    configured = tmp_path / "llm.yaml"
    configured.write_text("info_agent_max_tool_calls: 3\n", encoding="utf-8")
    empty = tmp_path / "empty.yaml"
    empty.write_text("model_priorities: []\n", encoding="utf-8")

    assert LLMConfig(str(configured)).info_agent_max_tool_calls == 3
    assert LLMConfig(str(empty)).info_agent_max_tool_calls == 8


def test_the_orchestrator_installs_the_budget_middleware() -> None:
    import inspect

    from llm import orchestrator

    source = inspect.getsource(orchestrator)
    assert "ToolCallBudgetMiddleware(llm_config.info_agent_max_tool_calls)" in source
    assert "DirectToolOutputMiddleware" not in source, "the no-op middleware (after_tools is no hook) is gone"
