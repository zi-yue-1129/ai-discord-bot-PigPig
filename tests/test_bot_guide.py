"""The bot describes its own commands, abilities and visible content from what it is really built with."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import discord
import pytest
from discord import app_commands
from discord.ext import commands
from langchain_core.tools import BaseTool, StructuredTool

from llm import self_knowledge
from llm.self_knowledge import (
    CommandInfo,
    ParamInfo,
    build_guide,
    build_self_description,
    collect_commands,
    group_abilities,
    render_command,
)
from llm.tools import bot_guide


class DemoCog(commands.Cog):
    """A cog with every kind of command the catalog has to understand."""

    GUIDE_NOTES = "Use the buttons under the player to skip or pause."

    @app_commands.command(name="ping", description="Check latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        return None

    @app_commands.command(name="play", description="Play a song")
    @app_commands.describe(query="Link or keywords")
    async def play(self, interaction: discord.Interaction, query: str, insert: bool = False) -> None:
        return None

    @app_commands.command(name="mode", description="Set the loop mode")
    @app_commands.choices(mode=[app_commands.Choice(name="Off", value="off"), app_commands.Choice(name="Song", value="song")])
    async def mode(self, interaction: discord.Interaction, mode: str) -> None:
        return None

    @app_commands.command(name="reboot", description="Restart the bot")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def reboot(self, interaction: discord.Interaction) -> None:
        return None

    memory = app_commands.Group(name="memory", description="Personal memory")

    @memory.command(name="save", description="Remember something about you")
    @app_commands.describe(text="What to remember")
    async def memory_save(self, interaction: discord.Interaction, text: str) -> None:
        return None

    @app_commands.command(name="help", description="Display all commands")
    async def help(self, interaction: discord.Interaction) -> None:
        return None


def _bot() -> SimpleNamespace:
    return SimpleNamespace(cogs={"DemoCog": DemoCog()})


def _tool(name: str, module: str, description: str) -> StructuredTool:
    async def run() -> str:
        return ""

    run.__module__ = module
    return StructuredTool.from_function(coroutine=run, name=name, description=description)


def _tools() -> List[StructuredTool]:
    return [
        _tool("play_music", "llm.tools.music_tools", "Plays music in the voice channel.\n\nArgs:\n    query: what to play"),
        _tool("skip_music", "llm.tools.music_tools", "Skips the current song."),
        _tool("set_reminder", "llm.tools.reminder", "Sets a reminder for a user."),
        _tool("mystery", "somewhere.else", "Does something."),
    ]


def _command(name: str) -> CommandInfo:
    return next(command for command in collect_commands(_bot()) if command.name == name)


def test_commands_are_collected_in_definition_order_with_groups_flattened() -> None:
    names = [command.name for command in collect_commands(_bot())]

    assert names == ["ping", "play", "mode", "reboot", "memory save", "help"]


def test_a_parameter_carries_its_description_type_requirement_and_choices() -> None:
    assert _command("play").params == (
        ParamInfo(name="query", description="Link or keywords", required=True, type="string", choices=()),
        ParamInfo(name="insert", description="", required=False, type="boolean", choices=()),
    )
    assert _command("mode").params[0].choices == ("Off", "Song")


def test_restrictions_and_cog_notes_are_collected() -> None:
    assert _command("reboot").restriction == "server only; needs permission manage_guild"
    assert _command("ping").restriction == ""
    assert _command("play").notes == "Use the buttons under the player to skip or pause."
    assert _command("play").cog == "DemoCog"


def test_a_command_is_rendered_with_usage_and_parameters() -> None:
    assert render_command(_command("play")) == "\n".join(
        [
            "/play <query> [insert] — Play a song",
            "  query (string, required): Link or keywords",
            "  insert (boolean, optional)",
        ]
    )
    assert "  mode (string, required, choices: Off, Song)" in render_command(_command("mode"))
    assert "  Restrictions: server only; needs permission manage_guild" in render_command(_command("reboot"))


def test_abilities_are_grouped_by_the_module_that_defines_them() -> None:
    assert group_abilities(_tools()) == {
        "music": ["play_music", "skip_music"],
        "reminder": ["set_reminder"],
        "other": ["mystery"],
    }


class _ClassTool(BaseTool):
    """A tool written as a class, like the knowledge tools."""

    name: str = "update_guild_knowledge"
    description: str = "Record facts for the whole server."

    def _run(self, *args: Any, **kwargs: Any) -> str:
        return ""


_ClassTool.__module__ = "llm.tools.knowledge"


def test_a_tool_written_as_a_class_is_grouped_by_its_module() -> None:
    assert group_abilities([_ClassTool()]) == {"knowledge": ["update_guild_knowledge"]}


def test_tools_about_the_toolbox_itself_are_not_listed_as_abilities() -> None:
    tools = [
        *_tools(),
        _tool("get_bot_guide", "llm.tools.bot_guide", "Explains the bot."),
        _tool("list_tools", "llm.tools.tools_overview", "Lists tools."),
    ]

    text = build_self_description(tools, history_limit=30)

    assert "music (play_music, skip_music)" in text
    assert "get_bot_guide" not in text
    assert "list_tools" not in text


def test_the_overview_lists_every_command_by_cog_and_every_ability_group() -> None:
    text = build_guide("", collect_commands(_bot()), _tools(), history_limit=30)

    assert "### DemoCog" in text
    assert "/ping — Check latency" in text
    assert "/memory save <text> — Remember something about you" in text
    assert "music (play_music, skip_music)" in text
    assert "last 30 messages" in text


def test_notes_are_found_by_a_whole_word_but_not_by_part_of_a_word() -> None:
    assert "/play <query> [insert]" in build_guide("skip", collect_commands(_bot()), [], history_limit=30)
    assert build_guide("laye", collect_commands(_bot()), [], history_limit=30).startswith("No exact match for “laye”")


@pytest.mark.parametrize("topic", ["play", "/play", "PLAY"])
def test_a_command_name_finds_that_command_in_detail(topic: str) -> None:
    text = build_guide(topic, collect_commands(_bot()), _tools(), history_limit=30)

    assert "/play <query> [insert] — Play a song" in text
    assert "  query (string, required): Link or keywords" in text
    assert "/ping" not in text


def test_a_word_from_a_description_finds_the_command() -> None:
    text = build_guide("latency", collect_commands(_bot()), _tools(), history_limit=30)

    assert "/ping — Check latency" in text
    assert "/play" not in text


def test_a_cog_name_finds_all_of_its_commands() -> None:
    text = build_guide("demo", collect_commands(_bot()), _tools(), history_limit=30)

    assert "/ping — Check latency" in text
    assert "/play <query> [insert] — Play a song" in text


def test_the_notes_of_a_cog_are_shown_once_after_its_commands() -> None:
    text = build_guide("demo", collect_commands(_bot()), _tools(), history_limit=30)

    assert text.count("Use the buttons under the player to skip or pause.") == 1
    assert "Notes about DemoCog: Use the buttons under the player to skip or pause." in text


def test_a_word_only_matches_the_start_of_other_words_not_their_middle() -> None:
    text = build_guide("play", collect_commands(_bot()), [], history_limit=30)

    assert "/play <query> [insert] — Play a song" in text
    assert "/help" not in text


def test_text_in_other_scripts_is_matched_anywhere() -> None:
    tools = [_tool("play_music", "llm.tools.music_tools", "在語音頻道播放音樂。")]

    assert "play_music (music): 在語音頻道播放音樂。" in build_guide("播放", [], tools, history_limit=30)


def test_an_ability_name_finds_the_ability_with_its_full_description() -> None:
    text = build_guide("play_music", collect_commands(_bot()), _tools(), history_limit=30)

    assert "play_music (music): Plays music in the voice channel." in text
    assert "what to play" not in text


def test_a_topic_that_matches_nothing_says_so_and_shows_the_overview() -> None:
    text = build_guide("zzz", collect_commands(_bot()), _tools(), history_limit=30)

    assert "No exact match for “zzz”" in text
    assert "### DemoCog" in text
    assert "music (play_music, skip_music)" in text


def test_a_broad_topic_shows_a_limited_number_of_matches_and_counts_the_rest() -> None:
    many = [_tool(f"tool_{number}", "llm.tools.bulk", f"Does thing {number}.") for number in range(10)]

    text = build_guide("tool_", [], many, history_limit=30)

    assert text.count("Does thing") == 6
    assert "…and 4 more" in text


def test_the_always_on_description_covers_what_the_bot_sees_and_can_do(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        self_knowledge,
        "describe_supported_attachments",
        lambda: ["images (resized to fit 1024 px)", "videos (up to 3 still frames, no sound)"],
    )
    monkeypatch.setattr(
        self_knowledge,
        "attachment_config",
        SimpleNamespace(max_download_bytes=50 * 1024 * 1024, embeds=SimpleNamespace(enabled=True)),
    )

    text = build_self_description(_tools(), history_limit=30)

    assert text.startswith("## About yourself")
    assert "last 30 messages" in text
    assert "images (resized to fit 1024 px), videos (up to 3 still frames, no sound)" in text
    assert "Files over 50 MB are skipped" in text
    assert "sound and voice messages, stickers" in text
    assert "music (play_music, skip_music)" in text
    assert "`/help`" in text


def test_the_description_says_so_when_no_attachment_can_be_opened(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(self_knowledge, "describe_supported_attachments", lambda: [])

    text = build_self_description([], history_limit=30)

    assert "You cannot open attachments" in text


@pytest.mark.asyncio
async def test_the_guide_tool_answers_from_the_live_bot_and_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    asked: List[Any] = []

    def fake_get_tools(user: Any, guid: Any, runtime: Any, agent_mode: str = "all") -> List[StructuredTool]:
        asked.append((user, guid, agent_mode))
        return _tools()

    monkeypatch.setattr(bot_guide.tools_factory, "get_tools", fake_get_tools)
    author, guild = object(), object()
    runtime = SimpleNamespace(bot=_bot(), message=SimpleNamespace(author=author, guild=guild), logger=None)

    (tool,) = bot_guide.BotGuideTools(runtime).get_tools()
    text = await tool.ainvoke({"topic": "play"})

    assert tool.name == "get_bot_guide"
    assert tool.metadata == {"target_agent_mode": "info"}
    assert asked == [(author, guild, "all")]
    assert "/play <query> [insert] — Play a song" in text
    assert "play_music (music)" in text
