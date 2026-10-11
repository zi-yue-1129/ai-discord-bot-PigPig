"""Hands the info agent's tool results to the reply agent.

The info agent only calls tools. What reaches the reply agent is the conversation
plus **one** clearly internal block holding the tool results. Anything the info
agent wrote in prose is dropped on purpose: its prompt forbids natural language, and
when a model ignores that rule, a conclusion such as "I can't play that right now"
would be replayed to the reply agent as if the bot itself had said it (this made the
bot refuse to play music it was perfectly able to play).
"""

from __future__ import annotations

from typing import Any, List, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage

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


def build_message_agent_history(messages: Sequence[BaseMessage], history_length: int) -> List[BaseMessage]:
    """Prepares the info agent's messages for the reply agent.

    Args:
        messages: The info agent's final message list: the conversation it was given
            followed by whatever it produced.
        history_length: How many leading messages are the conversation itself.

    Returns:
        The conversation unchanged, followed (only when tools ran) by a single
        internal ``HumanMessage`` holding the tool results in call order.
    """
    kept: List[BaseMessage] = list(messages[:history_length])
    results: List[str] = []

    for message in messages[history_length:]:
        if isinstance(message, ToolMessage):
            name = message.name or "unknown_tool"
            results.append(f"## {name}\n{_content_text(message.content).strip()}")

    if results:
        kept.append(HumanMessage(content="\n\n".join([_BLOCK_INTRO, *results])))
    return kept
