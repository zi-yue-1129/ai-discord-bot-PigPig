"""What the bot knows about itself, generated from the code and settings that define it.

Nothing here is a hand-kept list. Slash commands, their parameters and choices are read from
the loaded cogs; abilities from the registered AI tools; readable attachment types from the
attachment registry. A new command, tool or attachment kind therefore appears in the bot's
answers without touching this module. The only text written by hand is an optional
``GUIDE_NOTES`` string on a cog, for usage that no command description can carry (for
example the buttons under the music player).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Sequence, Tuple

from discord import app_commands

from addons.settings import attachment_config
from llm.utils.attachment_processor import describe_supported_attachments

# A topic search shows at most this many commands and this many abilities in detail.
MAX_MATCHES = 6
_TOOL_DESCRIPTION_CHARS = 400
_TOOLS_MODULE_PREFIX = "llm.tools."
_OTHER_GROUP = "other"
# Tools about the toolbox itself; they are not listed among the things the bot can do.
_TOOLBOX_TOOLS = frozenset({"get_bot_guide", "list_tools"})


@dataclass(frozen=True)
class ParamInfo:
    """One parameter of a slash command.

    Attributes:
        name: Parameter name as the user sees it.
        description: What the parameter is for; empty when the command does not say.
        required: Whether the user must fill it in.
        type: Discord option type name, for example ``"string"`` or ``"channel"``.
        choices: Display names of the fixed choices, if the parameter has any.
    """

    name: str
    description: str
    required: bool
    type: str
    choices: Tuple[str, ...]


@dataclass(frozen=True)
class CommandInfo:
    """A slash command as members can use it.

    Attributes:
        name: Full name without the slash, for example ``"memory save"``.
        description: The command's own description.
        cog: Name of the cog that provides it.
        params: Its parameters in order.
        restriction: Where or by whom it can be used; empty when unrestricted.
        notes: The cog's ``GUIDE_NOTES``, shared by all of its commands.
    """

    name: str
    description: str
    cog: str
    params: Tuple[ParamInfo, ...]
    restriction: str
    notes: str


def _clean(text: str) -> str:
    """Return ``text`` on one line; Discord's placeholder ``…`` counts as no text."""
    collapsed = " ".join((text or "").split())
    return "" if collapsed == "…" else collapsed


def _leaves(command: Any, prefix: str = "") -> Iterator[Tuple[str, Any]]:
    """Yield ``(full name, command)`` for every runnable command under ``command``."""
    if isinstance(command, app_commands.Group):
        for child in command.commands:
            yield from _leaves(child, f"{prefix}{command.name} ")
    else:
        yield f"{prefix}{command.name}", command


def _restriction(command: Any) -> str:
    """Describe where a command works and which permission it needs."""
    chain = []
    node = command
    while node is not None:
        chain.append(node)
        node = getattr(node, "parent", None)
    parts = []
    if any(getattr(node, "guild_only", False) for node in chain):
        parts.append("server only")
    required = next((node.default_permissions for node in chain if getattr(node, "default_permissions", None)), None)
    if required is not None:
        names = sorted(name for name, enabled in required if enabled)
        if names:
            parts.append(f"needs permission {', '.join(names)}")
    return "; ".join(parts)


def _describe_command(cog_name: str, name: str, command: Any, notes: str) -> CommandInfo:
    """Read everything the guide needs from one ``app_commands.Command``."""
    params = tuple(
        ParamInfo(
            name=parameter.name,
            description=_clean(parameter.description),
            required=parameter.required,
            type=parameter.type.name,
            choices=tuple(choice.name for choice in parameter.choices),
        )
        for parameter in command.parameters
    )
    return CommandInfo(
        name=name,
        description=_clean(command.description),
        cog=cog_name,
        params=params,
        restriction=_restriction(command),
        notes=notes,
    )


def collect_commands(bot: Any) -> List[CommandInfo]:
    """List the slash commands of every loaded cog.

    Args:
        bot: The running bot; its ``cogs`` are inspected.

    Returns:
        One entry per runnable command, cog by cog in definition order, with command
        groups flattened into names such as ``"memory save"``.
    """
    found: List[CommandInfo] = []
    for cog in bot.cogs.values():
        notes = _clean(getattr(cog, "GUIDE_NOTES", ""))
        for command in cog.get_app_commands():
            for name, leaf in _leaves(command):
                found.append(_describe_command(cog.qualified_name, name, leaf, notes))
    return found


def render_command(command: CommandInfo) -> str:
    """Render one command with its usage, parameters and restrictions.

    The cog's notes are not included: they are shared by all of its commands and are
    shown once per cog by :func:`build_guide`.

    Args:
        command: The command to render.

    Returns:
        Several lines; the first reads like ``/play <query> [insert] — Play a song``,
        where ``<x>`` marks a required and ``[x]`` an optional parameter.
    """
    usage = " ".join(
        [f"/{command.name}", *(f"<{p.name}>" if p.required else f"[{p.name}]" for p in command.params)]
    )
    lines = [f"{usage} — {command.description}" if command.description else usage]
    for param in command.params:
        details = [param.type, "required" if param.required else "optional"]
        if param.choices:
            details.append(f"choices: {', '.join(param.choices)}")
        line = f"  {param.name} ({', '.join(details)})"
        lines.append(f"{line}: {param.description}" if param.description else line)
    if command.restriction:
        lines.append(f"  Restrictions: {command.restriction}")
    return "\n".join(lines)


def _ability_group(tool: Any) -> str:
    """Name the group of an AI tool after the ``llm/tools`` module that defines it.

    Function-based tools are located by their function, class-based tools by their class.
    """
    function = getattr(tool, "coroutine", None) or getattr(tool, "func", None)
    for owner in (function, type(tool)):
        module = getattr(owner, "__module__", "") or ""
        if module.startswith(_TOOLS_MODULE_PREFIX):
            return module[len(_TOOLS_MODULE_PREFIX):].split(".")[0].removesuffix("_tools")
    return _OTHER_GROUP


def group_abilities(tools: Iterable[Any]) -> Dict[str, List[str]]:
    """Group AI tool names by the module that provides them.

    Args:
        tools: The tools bound for the current user.

    Returns:
        Group name (``"music"`` for ``llm/tools/music_tools.py``) to tool names; tools
        from elsewhere go under ``"other"``.
    """
    groups: Dict[str, List[str]] = {}
    for tool in tools:
        groups.setdefault(_ability_group(tool), []).append(tool.name)
    return groups


def _ability_lines(tools: Sequence[Any]) -> List[str]:
    """Render ability groups as ``music (play_music, skip_music)``, ``other`` last.

    Tools that only explain the toolbox itself are left out: they are not things the bot does.
    """
    groups = group_abilities(tool for tool in tools if tool.name not in _TOOLBOX_TOOLS)
    ordered = sorted(groups, key=lambda group: group == _OTHER_GROUP)
    return [f"{group} ({', '.join(groups[group])})" for group in ordered]


def _first_paragraph(text: str) -> str:
    """Return the first paragraph of a tool description on one line."""
    paragraph = (text or "").strip().split("\n\n")[0]
    return " ".join(paragraph.split())[:_TOOL_DESCRIPTION_CHARS]


def _describe_visible_content(history_limit: int) -> str:
    """Say which parts of a conversation the bot can and cannot see."""
    seen = "text, replies and reactions"
    if attachment_config.embeds.enabled:
        seen += ", and embeds (title, text, fields, link and images)"
    lines = [f"- The last {history_limit} messages of this channel: their {seen}."]
    openable = describe_supported_attachments()
    if openable:
        megabytes = round(attachment_config.max_download_bytes / (1024 * 1024))
        lines.append(f"- Attachments you can open: {', '.join(openable)}. Files over {megabytes} MB are skipped.")
    else:
        lines.append("- You cannot open attachments; they reach you only as a placeholder.")
    lines.append(
        "- You cannot see anything else: sound and voice messages, stickers, and other file types "
        "(text, code, archives, office documents). They reach you as a placeholder or not at all. "
        "Say you cannot open them instead of guessing what they contain."
    )
    return "\n".join(lines)


def build_self_description(tools: Sequence[Any], history_limit: int) -> str:
    """Build the short block of self-knowledge that goes into the reply agent's prompt.

    Args:
        tools: The AI tools available to the current user.
        history_limit: How many recent channel messages the bot reads.

    Returns:
        Markdown that states what the bot can see and which abilities it has.
    """
    lines = [
        "## About yourself",
        "Generated from your real settings and tools; trust it over anything said earlier in the chat.",
        "",
        "### What you can see",
        _describe_visible_content(history_limit),
        "",
        "### What you can do",
    ]
    abilities = _ability_lines(tools)
    if abilities:
        lines.append(f"- In conversation you can use these abilities: {', '.join(abilities)}.")
    lines.append("- Members can also use slash commands; `/help` lists them and explains each one.")
    return "\n".join(lines)


def _overview(commands: Sequence[CommandInfo], tools: Sequence[Any], history_limit: int) -> str:
    """Build the full overview of content, commands and abilities."""
    lines = ["## What I can see", _describe_visible_content(history_limit), "", "## Slash commands"]
    current_cog = None
    for command in commands:
        if command.cog != current_cog:
            current_cog = command.cog
            lines.append(f"### {current_cog}")
        lines.append(render_command(command).split("\n")[0])
    abilities = _ability_lines(tools)
    if abilities:
        lines += ["", "## Abilities I use while chatting (no command needed)", *(f"- {line}" for line in abilities)]
    lines += ["", "Ask again with a command or ability name for its details."]
    return "\n".join(lines)


def _mentions(text: str, query: str, whole_word: bool = False) -> bool:
    """Whether the lower-case ``query`` appears in ``text``.

    English words match where another word starts (``play`` finds "playback" and
    "play_music" but not "Display"); with ``whole_word`` they must also end there. Text in
    other scripts, which has no spaces between words, matches anywhere.

    Args:
        text: The text to search.
        query: The lower-case search term.
        whole_word: Require the match to end at the end of a word as well.

    Returns:
        True when the term is found.
    """
    lowered = text.lower()
    if not query.isascii():
        return query in lowered
    ending = r"(?![a-z0-9])" if whole_word else ""
    return re.search(rf"(?<![a-z0-9]){re.escape(query)}{ending}", lowered) is not None


def _command_matches(command: CommandInfo, query: str) -> bool:
    """Whether the lower-case ``query`` appears in any text about the command.

    Notes are shared by all commands of a cog, so they only match whole words: ``play``
    finds the notes that say "play" but not the ones that say "player".
    """
    texts = [command.name, command.description, command.cog]
    texts += [text for param in command.params for text in (param.name, param.description)]
    return any(_mentions(text, query) for text in texts) or _mentions(command.notes, query, whole_word=True)


def _tool_matches(tool: Any, query: str) -> bool:
    """Whether the lower-case ``query`` appears in a tool's name, group or description."""
    return any(_mentions(text, query) for text in (tool.name, _ability_group(tool), tool.description or ""))


def _limited(items: List[str], noun: str) -> List[str]:
    """Keep the first ``MAX_MATCHES`` items and say how many were left out."""
    if len(items) <= MAX_MATCHES:
        return items
    return items[:MAX_MATCHES] + [f"…and {len(items) - MAX_MATCHES} more {noun}; ask with a more specific word."]


def build_guide(topic: str, commands: Sequence[CommandInfo], tools: Sequence[Any], history_limit: int) -> str:
    """Answer a question about the bot itself.

    Args:
        topic: A command name, a feature word or an ability name. Empty gives the full
            overview. Matching ignores case and a leading slash.
        commands: The slash commands from :func:`collect_commands`.
        tools: The AI tools available to the current user.
        history_limit: How many recent channel messages the bot reads.

    Returns:
        Text with the details of everything that matches the topic, or the full overview
        (with a note) when nothing matches.
    """
    query = topic.strip().lstrip("/").lower()
    if not query:
        return _overview(commands, tools, history_limit)
    matched = [command for command in commands if _command_matches(command, query)]
    matched_commands = [render_command(command) for command in matched]
    matched_tools = [
        f"{tool.name} ({_ability_group(tool)}): {_first_paragraph(tool.description)}"
        for tool in tools
        if _tool_matches(tool, query)
    ]
    if not matched_commands and not matched_tools:
        return f"No exact match for “{topic.strip()}”. Here is everything I can do:\n\n" + _overview(
            commands, tools, history_limit
        )
    sections = []
    if matched_commands:
        body = "\n\n".join(_limited(matched_commands, "commands"))
        notes: Dict[str, str] = {}
        for command in matched[:MAX_MATCHES]:
            if command.notes:
                notes.setdefault(command.cog, command.notes)
        for cog, text in notes.items():
            body += f"\n\nNotes about {cog}: {text}"
        sections.append("## Slash commands\n" + body)
    if matched_tools:
        sections.append("## Abilities while chatting\n" + "\n".join(_limited(matched_tools, "abilities")))
    return "\n\n".join(sections)
