"""The short context note the info agent gets instead of the full system context.

The reply agent gets the whole system context (stored user memory, server knowledge, recalled
episodes). Putting that same block into the info agent's system prompt made the live model write a
chat reply instead of calling tools: in a replay of the real conversations it answered 0 of 36 tool
requests with a tool call, against about 30 of 36 when the block was left out and only the time and
channel were given after the conversation. The info agent only decides which tools to call, so it
gets just what that decision needs: where and when this is, and the music player status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from langchain_core.messages import HumanMessage

_NOTE = (
    "[Background for the tool execution agent, not a user message. "
    "Choose tools for the user's message above, or output nothing.]"
)


def build_info_context_message(
    channel_name: str,
    created_at: Optional[datetime],
    music_context: str = "",
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> HumanMessage:
    """Builds the note that goes after the conversation in the info agent's input.

    Args:
        channel_name: Name of the channel the message was written in.
        created_at: When the triggering message was written; a time without a zone counts as UTC.
            ``None`` uses the current time.
        music_context: The music player status, or an empty string when there is none.
        now: Source of the current time; replaced in tests.

    Returns:
        A ``HumanMessage`` holding the note, the channel, the time and, when given, the player status.
    """
    moment = created_at if created_at is not None else now()
    moment = moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)
    parts = [
        _NOTE,
        "--- System Context ---",
        f"Channel: #{channel_name}\nTimestamp: {moment.timestamp()}\nCurrent Time: {moment.strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]
    if music_context:
        parts.append(music_context)
    parts.append("--- End System Context ---")
    return HumanMessage(content="\n\n".join(parts))
