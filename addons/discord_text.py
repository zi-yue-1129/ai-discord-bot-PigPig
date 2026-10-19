"""Helpers for sending text that may exceed Discord's 2000 character message limit."""

from __future__ import annotations

from typing import Any, List, Optional

# Leaves room under Discord's 2000 character limit.
DEFAULT_LIMIT = 1900


def split_for_discord(text: str, limit: int = DEFAULT_LIMIT) -> List[str]:
    """Splits text into chunks that each fit in one Discord message.

    Chunks end at line breaks where possible, so ``"\\n".join(chunks)`` restores the
    text; a single line longer than ``limit`` is cut.

    Args:
        text: The text to split.
        limit: Maximum length of a chunk.

    Returns:
        The chunks (one empty chunk for empty text).
    """
    chunks: List[str] = []
    current: Optional[str] = None
    for line in text.split("\n"):
        while len(line) > limit:
            if current is not None:
                chunks.append(current)
                current = None
            chunks.append(line[:limit])
            line = line[limit:]
        if current is None:
            current = line
        elif len(current) + 1 + len(line) <= limit:
            current = f"{current}\n{line}"
        else:
            chunks.append(current)
            current = line
    if current is not None:
        chunks.append(current)
    return chunks


async def reply_in_chunks(interaction: Any, text: str, *, ephemeral: bool = False) -> None:
    """Replies to a deferred interaction, using follow-ups for text beyond one message.

    The first chunk replaces the "thinking" message; the rest are sent as follow-ups
    with the same visibility.

    Args:
        interaction: A deferred ``discord.Interaction``.
        text: The full reply.
        ephemeral: Whether the follow-ups are visible only to the user.
    """
    first, *rest = split_for_discord(text)
    await interaction.edit_original_response(content=first)
    for chunk in rest:
        await interaction.followup.send(chunk, ephemeral=ephemeral)
