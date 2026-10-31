"""Says, for the log, which tools the info agent really called in one reply.

The reply log used to list every tool the bot *could* use, and nothing about the ones it did use, so
nobody could tell from the logs whether the agent skipped a tool, called it and got an error, or never
got an answer. The functions here read the agent's final message list and answer exactly that.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

_ARGUMENT_LIMIT = 200
_TEXT_LIMIT = 80


@dataclass(frozen=True)
class ToolCallRecord:
    """One tool call of the info agent.

    Attributes:
        name: Tool name.
        arguments: The arguments as JSON, cut to at most 200 characters.
        status: ``ok``, ``error``, or ``no_result`` when the agent never got an answer back.
        result_chars: Length of the tool's answer, 0 when there was none.
    """

    name: str
    arguments: str
    status: str
    result_chars: int


def _clip(text: str, limit: int) -> str:
    """Cuts ``text`` to at most ``limit`` characters, marking the cut."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _content_text(content: Any) -> str:
    """Reduces message content (a string or a list of blocks) to its text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part if isinstance(part, str) else str(part.get("text", ""))
            for part in content
            if isinstance(part, (str, dict))
        )
    return str(content)


def collect_tool_calls(messages: Sequence[BaseMessage], history_length: int) -> List[ToolCallRecord]:
    """Lists the tool calls the info agent made, in the order it made them.

    Args:
        messages: The info agent's final message list: the conversation it was given followed by
            whatever it produced.
        history_length: How many leading messages are the conversation itself; they are ignored.

    Returns:
        One record per call, matched to its result by call id.
    """
    pending: Dict[str, Dict[str, Any]] = {}
    for message in messages[history_length:]:
        if isinstance(message, AIMessage):
            for call in message.tool_calls or []:
                call_id = str(call.get("id") or f"call-{len(pending)}")
                pending[call_id] = {
                    "name": str(call.get("name", "unknown_tool")),
                    "arguments": _clip(json.dumps(call.get("args", {}), ensure_ascii=False, default=str), _ARGUMENT_LIMIT),
                    "status": "no_result",
                    "result_chars": 0,
                }
        elif isinstance(message, ToolMessage) and message.tool_call_id in pending:
            entry = pending[message.tool_call_id]
            entry["status"] = "error" if getattr(message, "status", "success") == "error" else "ok"
            entry["result_chars"] = len(_content_text(message.content))
    return [ToolCallRecord(**entry) for entry in pending.values()]


def describe_info_agent_outcome(messages: Sequence[BaseMessage], history_length: int) -> str:
    """Renders what the info agent did as one log line fragment.

    Args:
        messages: The info agent's final message list.
        history_length: How many leading messages are the conversation itself.

    Returns:
        ``tool calls (n): name(args)=status, N chars; ...`` or, when it called nothing,
        ``no tool calls`` followed by any text it wrote instead.
    """
    calls = collect_tool_calls(messages, history_length)
    if calls:
        parts = [f"{call.name}({call.arguments})={call.status}, {call.result_chars} chars" for call in calls]
        return f"tool calls ({len(calls)}): " + "; ".join(parts)
    written = ""
    for message in messages[history_length:]:
        if isinstance(message, AIMessage):
            written = _content_text(message.content).strip()
    if written:
        return f"no tool calls; the agent wrote text instead: {_clip(written, _TEXT_LIMIT)!r}"
    return "no tool calls"
