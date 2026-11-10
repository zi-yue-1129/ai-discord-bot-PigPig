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
from functools import lru_cache
from typing import Iterable, Pattern, Tuple

# Gemma wraps its reasoning as "<|channel>thought ... <channel|>".
_CHANNEL_BLOCK = re.compile(r"<\|channel>.*?<channel\|>", re.DOTALL)
_CHANNEL_TOKEN = re.compile(r"</?\|?channel\|?>")
_THINK_BLOCK = re.compile(r"<(think|thinking)>.*?</\1>\s*", re.DOTALL)
_UNCLOSED_THINK = re.compile(r"<(?:think|thinking)>.*\Z", re.DOTALL)
# Tool calls a model writes as text (when its server does not parse them) and copies of
# the internal tool-result block. A block that is never closed hides the rest.
_TOOL_BLOCK = re.compile(
    r"\s*(?:<tool_call>.*?(?:</tool_call>|\Z)"
    r"|<\|tool_call>.*?(?:<tool_call\|>|\Z)"
    r"|<tool_response>.*?(?:</tool_response>|\Z)"
    r"|<\|tool_response>.*?(?:<tool_response\|>|\Z)"
    r"|<tool_results>.*?(?:</tool_results>|\Z)"
    r"|<tool_code>.*?(?:</tool_code>|\Z)"
    r"|<function=.*?(?:</function>|\Z)"
    r"|</tool_call>|</tool_code>)",
    re.DOTALL,
)
_SOM_SEGMENT = re.compile(r"<som>(.*?)(?:<eom>|\Z)", re.DOTALL)

# "[name | UserID:123 | MessageID:456]" (or with angle brackets) in front of a message, with an optional ":".
_IDENTITY_PREFIX = re.compile(r"[\[<][^\[\]<>\n]*\|\s*UserID:\d+\s*\|\s*MessageID:\d+[\]>]\s*:?\s*")
# While streaming, a bracket or angle group that is still open may become a header or a
# written tool call once it closes, so it is held back until then.
_OPEN_GROUP_AT_END = re.compile(r"[\[<][^\[\]<>\n]{0,200}\Z")

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


@lru_cache(maxsize=8)
def _tool_text_patterns(tool_names: Tuple[str, ...]) -> Tuple[Pattern[str], Pattern[str]]:
    """Builds the patterns for tool calls written as text, for one set of tool names.

    Returns:
        ``(complete, open_at_end)``: written calls such as ``[add_reaction: 👍]``,
        ``[change_own_nickname](小豬豬)``, ``[send_sticker]``, ``change_own_nickname(name="x")``
        or ``<change_own_nickname>x</change_own_nickname>``,
        and the start of such a call at the very end of a text that is still streaming.
    """
    names = "|".join(re.escape(name) for name in sorted(tool_names, key=len, reverse=True))
    complete = re.compile(
        rf"\s*\[\s*(?:{names})\s*(?:[:：][^\[\]\n]*)?\](?:\([^()\n]*\))?"
        rf"|\s*(?<![\w`])(?:{names})\s*\([^()\n]*\)"
        rf"|\s*<\s*({names})\s*(?:[:：][^<>\n]*)?>(?:[^<>\n]*</\s*\1\s*>)?"
    )
    open_at_end = re.compile(rf"\s*(?<![\w`])(?:{names})\s*\([^()\n]*\Z|\s*(?<![\w`])[a-z_]{{3,}}\Z")
    return complete, open_at_end


def strip_tool_text(text: str, tool_names: Iterable[str], partial: bool = False) -> str:
    """Removes tool calls the model wrote as text and imitated identity headers.

    Only calls of the given tools are removed, so ordinary brackets and a tool named in
    prose stay.

    Args:
        text: Reply text, without the ``<som>``/``<eom>`` markers.
        tool_names: Names of the tools the model was given.
        partial: True while the reply is still streaming: a bracket group or tool call
            that is still open at the end is held back as well.

    Returns:
        The text with those parts removed.
    """
    text = _IDENTITY_PREFIX.sub("", text)
    names = tuple(sorted(set(tool_names)))
    if names:
        complete, open_at_end = _tool_text_patterns(names)
        text = complete.sub("", text)
        if partial:
            match = open_at_end.search(text)
            # A lowercase word at the end is held back only while it can still become a tool call.
            if match and (match.group(0).strip().startswith(names) or any(
                name.startswith(match.group(0).strip()) for name in names
            )):
                text = text[: match.start()]
    if partial:
        text = _OPEN_GROUP_AT_END.sub("", text)
    return text


def sanitize_reply(raw: str, tool_names: Iterable[str] = ()) -> str:
    """Cleans a raw model reply so only the intended message text remains.

    Args:
        raw: The model's output, possibly containing ``<som>``/``<eom>`` tags,
            reasoning blocks, imitated history metadata and internal placeholders.
        tool_names: Names of the tools the model was given; calls of them written as
            text are removed.

    Returns:
        The text to post, or an empty string when nothing postable remains.
    """
    text = _CHANNEL_TOKEN.sub("", _CHANNEL_BLOCK.sub("", raw))
    text = _drop_thinking(text)
    text = _TOOL_BLOCK.sub("", text)
    text = _marked_body(text)
    text = strip_tool_text(text, tool_names)
    for pattern in (_TIMESTAMP_GROUP, _REPLYING_GROUP, _FIELD_GROUP, _ASSISTANT_PLACEHOLDER, _SYSTEM_HEADER):
        text = pattern.sub("", text)
    text = _STRAY_TAG.sub("", text)
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip()
    return _BLANK_RUN.sub("\n\n", text)
