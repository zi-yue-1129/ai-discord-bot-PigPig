"""Where the info agent gets the system context (stored user memory, server knowledge, time, player status).

The reply agent gets that block in its system prompt. Putting the same block into the *info agent's*
system prompt made the live model write a chat reply instead of calling tools: in a replay of the
real conversations 16 of 36 tool requests got a tool call (0 of 36 in another run). With the block
after the conversation, as a short note, 30 of 36 did, and the info agent still sees the stored
memory ("play my favourite song"). The system prompt therefore stays the static info prompt, which
also keeps the provider's prompt cache valid.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from langchain_core.messages import BaseMessage, HumanMessage

_NOTE = (
    "[Background for the tool execution agent, not a user message. "
    "Choose tools for the user's message above, or output nothing.]"
)


def build_info_agent_request(
    system_prompt: str,
    messages: Sequence[BaseMessage],
    system_context: str,
) -> Tuple[str, List[BaseMessage]]:
    """Builds what the info agent is sent.

    Args:
        system_prompt: The info agent's static instructions.
        messages: The conversation, oldest first, ending with the message to act on.
        system_context: The system context block (user memory, knowledge, channel and time, player
            status). May be empty.

    Returns:
        ``(system_prompt, messages)``: the prompt unchanged, and a new list holding the conversation
        followed, when there is a context, by one note with that context. ``messages`` is not modified.
    """
    conversation = list(messages)
    if system_context:
        conversation.append(HumanMessage(content=f"{_NOTE}\n\n{system_context}"))
    return system_prompt, conversation
