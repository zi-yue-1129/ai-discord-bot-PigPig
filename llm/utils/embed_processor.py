# llm/utils/embed_processor.py
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from addons.settings import attachment_config

if TYPE_CHECKING:
    import discord

_YOUTUBE_MAXRES = re.compile(r"^(https://img\.youtube\.com/vi/[\w-]+/)maxresdefault\.jpg$")


def _usable_image_url(url: str) -> str:
    """Replaces YouTube's ``maxresdefault.jpg`` thumbnail, which 404s for some videos.

    Earlier music embeds in the channel history still use that URL, and a 404 while the
    model server fetches it fails the whole model call.

    Args:
        url: The image URL of an embed.

    Returns:
        The same URL, or the always-available ``hqdefault.jpg`` for YouTube thumbnails.
    """
    return _YOUTUBE_MAXRES.sub(r"\1hqdefault.jpg", url)


def process_embed(embed: "discord.Embed") -> list[dict]:
    """Convert a Discord Embed to LangChain content_parts.

    Text fields (title, description, fields, url) are serialized as a single
    structured text part. Images and thumbnails are appended as image_url parts
    when ``attachment_config.embeds.include_images`` is enabled. Empty embeds
    (no text and no images) return an empty list.

    Args:
        embed: A Discord ``Embed`` object (or compatible mock) to convert.

    Returns:
        A list of content-part dicts compatible with the LangChain
        ``content_parts`` format. Each dict has at minimum a ``"type"`` key
        with value ``"text"`` or ``"image_url"``.
    """
    if not attachment_config.embeds.enabled:
        return []

    lines: list[str] = []

    if embed.title:
        lines.append(f"[Embed: {embed.title}]")
    if embed.description:
        lines.append(embed.description)
    if embed.fields:
        lines.append("Fields:")
        for field in embed.fields:
            lines.append(f"  • {field.name}: {field.value}")
    if embed.url:
        lines.append(f"URL: {embed.url}")

    parts: list[dict] = []

    if lines:
        parts.append({"type": "text", "text": "\n".join(lines)})

    if attachment_config.embeds.include_images:
        if embed.image and embed.image.url:
            parts.append({"type": "image_url", "image_url": {"url": _usable_image_url(embed.image.url)}})
        if embed.thumbnail and embed.thumbnail.url:
            parts.append({"type": "image_url", "image_url": {"url": _usable_image_url(embed.thumbnail.url)}})

    return parts
