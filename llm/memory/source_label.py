"""Marks which server a fact in the global user memory was told in.

User memory is keyed by Discord ID only, so one member's memory is shown on every server they
talk to the bot in. Each saved fact is tagged with the server it came from, and when the memory is
read the tag is turned into "this server" or "another server", so the model can tell what was said
here from what was said somewhere else.

Only the server **id** is stored. A server name is chosen by its owner (so it could carry
instructions into every other server's prompt) and would tell other servers which communities the
member belongs to.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Added to the merge prompt so the merge model keeps the tags next to their facts.
SOURCE_TAG_INSTRUCTION = (
    "A fact may end with a [source: ...] tag saying where it was told. Keep that tag "
    "attached to its fact; when the same fact comes from several places keep every tag. "
    "Never add a tag to a fact that has none and never change a tag."
)

# A tag typed into the fact itself would pass for a real one (the merge prompt keeps every tag).
_TYPED_TAG = re.compile(r"\[\s*source\s*:[^\]]*\]", re.IGNORECASE)
_SERVER_TAG = re.compile(r"\[source: server id=(\d+)\]")


def tag_with_source(text: str, context: Optional[Any]) -> str:
    """Append the place ``text`` was told in to it.

    Args:
        text: The fact to save.
        context: The Discord message or interaction that triggered the save, or ``None``.

    Returns:
        ``text`` followed by ``[source: server id=<id>]`` or ``[source: direct message]``. Any tag
        already typed into ``text`` is removed. Without a context the text is returned unchanged.
    """
    if context is None:
        return text
    # Repeat until nothing changes: removing an inner tag can join the rest into a new one.
    previous = None
    while previous != text:
        previous = text
        text = _TYPED_TAG.sub("", text)
    guild = getattr(context, "guild", None)
    tag = "[source: direct message]" if guild is None else f"[source: server id={guild.id}]"
    # Every line is its own fact; the merge keeps a tag next to its fact and never tags an untagged one.
    return "\n".join(f"{line.strip()} {tag}" if line.strip() else "" for line in text.strip().split("\n"))


def render_sources(text: str, current_guild_id: Optional[str]) -> str:
    """Turn stored server ids into "this server" / "another server" for whoever reads the memory.

    Args:
        text: Stored memory text.
        current_guild_id: The server the memory is being read in, or ``None`` in a direct message.

    Returns:
        ``text`` with each ``[source: server id=<id>]`` replaced; other text is left alone.
    """
    def replace(match: "re.Match[str]") -> str:
        where = "this server" if current_guild_id is not None and match.group(1) == str(current_guild_id) else "another server"
        return f"[source: {where}]"

    return _SERVER_TAG.sub(replace, text)
