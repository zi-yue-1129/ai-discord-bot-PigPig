"""Marks which server a fact in the global user memory was told in.

User memory is keyed by Discord ID only, so one member's memory is shown on every server they
talk to the bot in. Tagging each saved fact with where it came from lets the model (and a reader)
tell "said in this server" from "said somewhere else".
"""

from __future__ import annotations

import re
from typing import Any, Optional

MAX_SERVER_NAME_CHARS = 40

# Added to the merge prompt so the merge model keeps the tags next to their facts.
SOURCE_TAG_INSTRUCTION = (
    "A fact may end with a [source: ...] tag saying where it was told. Keep that tag "
    "attached to its fact; when the same fact comes from several places keep every tag. "
    "Never add a tag to a fact that has none and never change a tag."
)

# Characters a server owner could use to close the tag early or open a fake one.
_TAG_BREAKING = re.compile(r'[\[\]"]')
_WHITESPACE = re.compile(r"\s+")
# A tag typed into the fact itself would pass for a real one (the merge prompt keeps every tag).
_TYPED_TAG = re.compile(r"\[\s*source\s*:[^\]]*\]", re.IGNORECASE)


def _clean_server_name(name: str) -> str:
    """Make a server name safe to put inside a ``[source: ...]`` tag.

    Server names are chosen by server owners, so they are untrusted text.

    Args:
        name: The raw guild name.

    Returns:
        The name on one line, without brackets or quotes, cut to ``MAX_SERVER_NAME_CHARS``.
    """
    cleaned = _TAG_BREAKING.sub("", name)
    cleaned = _WHITESPACE.sub(" ", cleaned).strip()
    return cleaned[:MAX_SERVER_NAME_CHARS].rstrip()


def tag_with_source(text: str, context: Optional[Any]) -> str:
    """Append the place ``text`` was told in to it.

    Args:
        text: The fact to save.
        context: The Discord message or interaction that triggered the save, or ``None``.

    Returns:
        ``text`` followed by ``[source: server "<name>" id=<id>]`` (the id tells apart servers with
        the same name) or ``[source: direct message]``. Any tag already typed into ``text`` is
        removed. Without a context the text is returned unchanged.
    """
    if context is None:
        return text
    text = _TYPED_TAG.sub("", text).strip()
    guild = getattr(context, "guild", None)
    if guild is None:
        return f"{text} [source: direct message]"
    return f'{text} [source: server "{_clean_server_name(str(guild.name))}" id={guild.id}]'
