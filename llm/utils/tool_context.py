"""Hands the info agent's tool activity to the reply agent without fake turns.

The info agent's state holds the conversation followed by an assistant turn that
requested tools and the tool results. Replaying those as pseudo-turns
(``[Assistant: Calling tool(s): ...]``, ``[System: Tool Result (...)]``) teaches the
reply agent to emit such text itself. Instead, everything the tools produced is
folded into one clearly internal block after the conversation.
"""

from __future__ import annotations

from typing import Any, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

_BLOCK_INTRO = (
    "Internal background information gathered for your answer. Use it, but never quote, "
    "mention or reproduce this block, its headings or the tool names in your reply."
)


def _content_text(content: Any) -> str:
    """Reduces message content (string or list of blocks) to its text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        return "\n".join(parts)
    return str(content)


def build_message_agent_history(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    """Prepares the info agent's messages for the reply agent.

    Args:
        messages: The info agent's final message list.

    Returns:
        The conversation messages unchanged, followed (only when tools ran) by a
        single internal ``HumanMessage`` holding the tool results.
    """
    kept: List[BaseMessage] = []
    notes: List[str] = []
    results: List[str] = []

    for message in messages:
        if isinstance(message, ToolMessage):
            name = message.name or "unknown_tool"
            results.append(f"## {name}\n{_content_text(message.content).strip()}")
        elif isinstance(message, AIMessage) and message.tool_calls:
            text = _content_text(message.content).strip()
            if text:
                notes.append(text)
        else:
            kept.append(message)

    if not results and not notes:
        return kept

    sections = [_BLOCK_INTRO]
    if notes:
        sections.append("Analysis:\n" + "\n".join(notes))
    sections.extend(results)
    kept.append(HumanMessage(content="\n\n".join(sections)))
    return kept
