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


def is_error_answer(text: str) -> bool:
    """Tells whether a tool's answer is a failure report.

    Most of the bot's tools do not raise when they fail; they return ``"Error: ..."`` or
    ``"Error updating ..."``, which LangChain counts as a success.

    Args:
        text: The tool's answer.

    Returns:
        True when the answer starts with ``Error:`` or ``Error `` (ignoring leading whitespace).
    """
    return text.lstrip().startswith(("Error:", "Error "))


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
            text = _content_text(message.content)
            failed = getattr(message, "status", "success") == "error" or is_error_answer(text)
            entry["status"] = "error" if failed else "ok"
            entry["result_chars"] = len(text)
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


_ROLE_NAMES = {"human": "human", "ai": "ai", "system": "system", "tool": "tool"}


def _role_runs(messages: Sequence[BaseMessage]) -> str:
    """Compresses the message roles into runs, e.g. ``human x2,ai,human``."""
    runs: List[List[Any]] = []
    for message in messages:
        role = _ROLE_NAMES.get(message.type, message.type)
        if runs and runs[-1][0] == role:
            runs[-1][1] += 1
        else:
            runs.append([role, 1])
    return ",".join(role if count == 1 else f"{role} x{count}" for role, count in runs)


def _text_chars(message: BaseMessage) -> int:
    """Counts the characters of a message's text parts (images and other blocks count 0)."""
    if isinstance(message.content, str):
        return len(message.content)
    return sum(
        len(part) if isinstance(part, str) else len(str(part.get("text", "")))
        for part in message.content
        if isinstance(part, (str, dict))
    )


def _image_count(messages: Sequence[BaseMessage]) -> int:
    """Counts image parts in the messages' content."""
    count = 0
    for message in messages:
        if isinstance(message.content, list):
            count += sum(
                1 for part in message.content
                if isinstance(part, dict) and part.get("type") in ("image_url", "image")
            )
    return count


def describe_info_agent_request(
    sent: Sequence[BaseMessage], system_prompt: str, tools: Sequence[Any], answer: Sequence[BaseMessage],
) -> str:
    """Describes an info agent run by its shape only, never its content.

    Args:
        sent: The messages the agent was given.
        system_prompt: The agent's system prompt.
        tools: The tools bound to the agent.
        answer: What the agent added after ``sent``.

    Returns:
        ``roles=... last=... tools=N prompt_chars=N images=N finish_reason=... tool_calls=N``, where
        finish_reason and tool_calls describe the model's first answer.
    """
    first = next((message for message in answer if isinstance(message, AIMessage)), None)
    finish_reason = (first.response_metadata or {}).get("finish_reason") if first is not None else None
    tool_calls = len(first.tool_calls or []) if first is not None else 0
    prompt_chars = len(system_prompt) + sum(_text_chars(message) for message in sent)
    last = _ROLE_NAMES.get(sent[-1].type, sent[-1].type) if sent else None
    return (
        f"roles={_role_runs(sent)} last={last} tools={len(tools)} prompt_chars={prompt_chars} "
        f"images={_image_count(sent)} finish_reason={finish_reason} tool_calls={tool_calls}"
    )


def describe_reply_tools(info_calls: Sequence[ToolCallRecord], action_tools: Sequence[str]) -> str:
    """Names the tools both agents ran for one reply, for the reply log line.

    Args:
        info_calls: The info agent's tool calls.
        action_tools: Names of the action tools the message agent ran (nickname, reactions...).

    Returns:
        ``tools_called: [...], actions_called: [...]``.
    """
    return f"tools_called: {[call.name for call in info_calls]}, actions_called: {list(action_tools)}"
