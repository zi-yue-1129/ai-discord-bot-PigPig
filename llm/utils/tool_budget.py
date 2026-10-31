"""Keeps the info agent from calling tools without end.

The agent loop is model -> tools -> model until the model stops asking for tools. A local model
can get stuck repeating one call (80 identical ``search_episodic_memory`` calls in two minutes
were seen in the logs), so the loop needs an end that does not depend on the model.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

from addons.logging import get_logger
from langchain.agents.middleware import AgentMiddleware, hook_config
from langchain_core.messages import AIMessage

logger = get_logger(server_id="Bot", source=__name__)

_ToolCall = Dict[str, Any]


def _call_key(call: _ToolCall) -> Tuple[str, str]:
    """Identify a tool call by tool name and arguments, whatever the order of the arguments."""
    return call["name"], json.dumps(call.get("args", {}), sort_keys=True, ensure_ascii=False, default=str)


def _without_dropped_blocks(content: Any, kept_ids: Set[str]) -> Any:
    """Remove provider ``tool_use`` blocks whose call was dropped.

    Anthropic-style models also keep each call as a ``tool_use`` block in the message content; one
    without a matching result makes the next request invalid.

    Args:
        content: The message content (a string or a list of blocks).
        kept_ids: Ids of the tool calls that will still run.

    Returns:
        The content without the blocks of dropped calls.
    """
    if not isinstance(content, list):
        return content
    return [
        block for block in content
        if not (isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") not in kept_ids)
    ]


class ToolCallBudgetMiddleware(AgentMiddleware):
    """Cuts repeated tool calls and caps how many run in total.

    Two cases are cut, and when nothing is left to run the agent ends with the results it already has:

    * a call identical to ones already made in earlier rounds, once it has run
      ``max_identical_calls`` times (a loop gets the same answer every time; a few repeats stay
      allowed because "roll again if it is 1" is a legitimate repeat). Identical calls inside one
      reply are kept, since "roll two dice" is two identical ``roll_dice`` calls;
    * every call beyond ``max_tool_calls`` for the whole run.
    """

    def __init__(self, max_tool_calls: int, max_identical_calls: int = 2) -> None:
        """Create the middleware.

        Args:
            max_tool_calls: Most tool calls one agent run may make.
            max_identical_calls: How many times a call with the same tool and arguments may run
                across the rounds of one agent run.

        Raises:
            ValueError: If either limit is not positive.
        """
        super().__init__()
        if max_tool_calls < 1:
            raise ValueError(f"max_tool_calls must be at least 1, got {max_tool_calls}")
        if max_identical_calls < 1:
            raise ValueError(f"max_identical_calls must be at least 1, got {max_identical_calls}")
        self.max_tool_calls = max_tool_calls
        self.max_identical_calls = max_identical_calls

    @hook_config(can_jump_to=["end"])
    def after_model(self, state: Any, runtime: Any) -> Optional[Dict[str, Any]]:
        """Trim the tool calls the model just asked for.

        Args:
            state: The agent state; ``state["messages"]`` ends with the model's reply.
            runtime: The agent runtime (unused).

        Returns:
            ``None`` when the reply is fine; otherwise the reply without the cut calls, plus a jump
            to the end when no call is left to run.
        """
        messages = state["messages"]
        latest = messages[-1]
        if not isinstance(latest, AIMessage) or not latest.tool_calls:
            return None

        earlier: List[_ToolCall] = [
            call for message in messages[:-1] if isinstance(message, AIMessage) for call in message.tool_calls
        ]
        times_made = Counter(_call_key(call) for call in earlier)
        room = max(self.max_tool_calls - len(earlier), 0)

        fresh = [call for call in latest.tool_calls if times_made[_call_key(call)] < self.max_identical_calls]
        kept = fresh[:room]
        if len(kept) == len(latest.tool_calls):
            return None

        logger.warning(
            "Info agent asked for %d tool call(s); %d will run (%d repeated an earlier round, budget %d, %d used)",
            len(latest.tool_calls), len(kept), len(latest.tool_calls) - len(fresh),
            self.max_tool_calls, len(earlier),
        )
        extra = {key: value for key, value in latest.additional_kwargs.items() if key != "tool_calls"}
        kept_ids = {call["id"] for call in kept}
        trimmed = latest.model_copy(
            update={
                "tool_calls": kept,
                "additional_kwargs": extra,
                "content": _without_dropped_blocks(latest.content, kept_ids),
            }
        )
        if kept:
            return {"messages": [trimmed]}
        return {"messages": [trimmed], "jump_to": "end"}
