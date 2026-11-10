"""The reply prompt tells the model that action tools only run through a real function call.

With Qwen behind vLLM, the reply model wrote actions as text ("[add_reaction: 🤖]",
"<change_own_nickname>小豬豬</change_own_nickname>") instead of calling the tool, so the action
never happened. The rules are generated in code because the live bot reads its prompt YAML from
configs/, which a change to base_configs/ does not reach.
"""

from __future__ import annotations

from types import SimpleNamespace

from llm.orchestrator import Orchestrator


def _rules() -> str:
    return Orchestrator._build_action_tools_rules([SimpleNamespace(name="add_reaction")])


def test_actions_run_only_through_a_function_call_after_the_text() -> None:
    rules = _rules()

    assert "function call" in rules
    assert "after `<eom>`" in rules.lower()


def test_the_written_forms_seen_live_are_named_as_doing_nothing() -> None:
    rules = _rules()

    assert "[add_reaction: 👍]" in rules
    assert "does nothing" in rules


def test_a_request_for_an_action_must_be_answered_with_the_tool() -> None:
    assert "change your nickname" in _rules()


def test_no_rules_without_action_tools() -> None:
    assert Orchestrator._build_action_tools_rules([]) == ""
