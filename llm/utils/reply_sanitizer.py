"""Removes protocol and context-format artifacts from a model's reply.

The model is shown channel history as ``[name | UserID:n | MessageID:n] <som> text
<eom> [reply_to: ... | timestamp: ...]`` and is asked to answer with
``<som> text <eom>``. Models regularly imitate the surrounding format: they drop
the opening ``<som>``, append a metadata block after ``<eom>``, or echo internal
placeholders. :func:`sanitize_reply` turns such raw output into the text that is
safe to post in a channel.
"""

from __future__ import annotations

import re

_THINK_BLOCK = re.compile(r"<(think|thinking)>.*?</\1>\s*", re.DOTALL)
_UNCLOSED_THINK = re.compile(r"<(?:think|thinking)>.*\Z", re.DOTALL)
_SOM_SEGMENT = re.compile(r"<som>(.*?)(?:<eom>|\Z)", re.DOTALL)

# "[name | UserID:123 | MessageID:456]" in front of a message, with an optional ":".
_IDENTITY_PREFIX = re.compile(r"\[[^\[\]\n]*\|\s*UserID:\d+\s*\|\s*MessageID:\d+\]\s*:?\s*")

# Metadata the history renderer appends to messages, in bracket groups.
_TIMESTAMP_GROUP = re.compile(r"\[[^\[\]]*\btimestamp:\s*\d[\d.]*\s*\([^)]*UTC\)[^\[\]]*\]")
_REPLYING_GROUP = re.compile(r"\[Replying to @[^\n]*?\(MessageID:\d+\)\]")
_FIELD_GROUP = re.compile(r"\[(?:reply_to|reactions):[^\[\]\n]*\]")

# Placeholders and headers the orchestrator uses internally.
_ASSISTANT_PLACEHOLDER = re.compile(r"\[Assistant:[^\]]*\]")
_SYSTEM_HEADER = re.compile(r"\[System:[^\]\n]*\]\s*")

_STRAY_TAG = re.compile(r"</?(?:som|eom)>")
_BLANK_RUN = re.compile(r"\n{3,}")


def _drop_thinking(text: str) -> str:
    """Removes reasoning blocks, keeping only what follows the last closing tag."""
    for closing in ("</think>", "</thinking>"):
        if closing in text:
            text = text.rsplit(closing, 1)[-1]
    text = _THINK_BLOCK.sub("", text)
    return _UNCLOSED_THINK.sub("", text)


def _marked_body(text: str) -> str:
    """Returns the text the model marked as its answer.

    Uses every ``<som>...<eom>`` segment when an opening marker exists. Without
    one, a lone ``<eom>`` means the model forgot the opening marker, so the text
    before it is the answer and anything after it is noise.
    """
    segments = [segment.strip() for segment in _SOM_SEGMENT.findall(text)]
    segments = [segment for segment in segments if segment]
    if segments:
        # Text outside the markers is invisible by protocol, so it is not an answer.
        return "\n".join(segments)
    if "<som>" in text:
        return ""
    if "<eom>" in text:
        return text.split("<eom>", 1)[0]
    return text


def sanitize_reply(raw: str) -> str:
    """Cleans a raw model reply so only the intended message text remains.

    Args:
        raw: The model's output, possibly containing ``<som>``/``<eom>`` tags,
            reasoning blocks, imitated history metadata and internal placeholders.

    Returns:
        The text to post, or an empty string when nothing postable remains.
    """
    text = _drop_thinking(raw)
    text = _marked_body(text)
    text = _IDENTITY_PREFIX.sub("", text)
    for pattern in (_TIMESTAMP_GROUP, _REPLYING_GROUP, _FIELD_GROUP, _ASSISTANT_PLACEHOLDER, _SYSTEM_HEADER):
        text = pattern.sub("", text)
    text = _STRAY_TAG.sub("", text)
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip()
    return _BLANK_RUN.sub("\n\n", text)
