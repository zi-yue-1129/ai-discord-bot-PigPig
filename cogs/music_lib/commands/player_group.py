"""``/music`` (position, history, lyrics) and ``/filter`` commands."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from typing import Any, List, Optional

from addons.settings import music_config

from ..filters import FILTER_NAMES, get_preset
from ..lyrics import Lyrics, paginate
from ..ui.text import format_clock, parse_clock, shorten
from .base import MusicCommandBase

# Effect names shown in the /filter menu (slash command choices are registered once, in
# the language of the other command descriptions); replies use the server's language.
_FILTER_CHOICE_NAMES = {
    "off": "關閉音效", "nightcore": "Nightcore", "vaporwave": "Vaporwave", "slowed_reverb": "Slowed + Reverb",
    "8d": "8D 環繞", "bassboost": "重低音", "karaoke": "卡拉 OK（去人聲）", "soft": "柔和（低通）",
    "tremolo": "顫音 Tremolo", "vibrato": "抖音 Vibrato", "speed_up": "加速 1.25x", "slow_down": "減速 0.8x",
}

# Longest jump one forward/rewind command may make.
MAX_STEP_SECONDS = 600
HISTORY_TITLE_WIDTH = 50


@app_commands.guild_only()
class MusicGroup(MusicCommandBase, commands.GroupCog, group_name="music", group_description="音樂播放工具：快轉、倒轉、歷史、歌詞"):
    """``/music`` subcommands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    async def _seek(self, interaction: discord.Interaction, seconds: float, *, relative: bool, key: str) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        result = await music.service.seek(self.ctx(interaction), seconds, relative=relative)
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        await self.ok(interaction, self.t(
            interaction.guild.id, "commands", "music", "responses", key,
            position=format_clock(result.data["position"]), duration=format_clock(result.data["duration"]),
            seconds=int(abs(seconds)), title=shorten(result.data.get("title") or "", HISTORY_TITLE_WIDTH),
        ), emoji="⏩" if seconds >= 0 else "⏪")

    @app_commands.command(name="seek", description="Jump to a time of the current song (e.g. 1:30 or 90)")
    @app_commands.describe(time="Time, e.g. 1:30, 90 or 1:02:03")
    async def seek(self, interaction: discord.Interaction, time: str) -> None:
        try:
            seconds = parse_clock(time)
        except ValueError:
            await self.fail(interaction, self.t(interaction.guild.id, "commands", "music", "errors", "invalid_time"))
            return
        await self._seek(interaction, seconds, relative=False, key="seeked")

    @app_commands.command(name="forward", description="Skip ahead in the current song")
    @app_commands.describe(seconds="Seconds to skip ahead (default 10)")
    async def forward(self, interaction: discord.Interaction,
                      seconds: app_commands.Range[int, 1, MAX_STEP_SECONDS] = 10) -> None:
        await self._seek(interaction, seconds, relative=True, key="forwarded")

    @app_commands.command(name="rewind", description="Rewind the current song")
    @app_commands.describe(seconds="Seconds to rewind (default 10)")
    async def rewind(self, interaction: discord.Interaction,
                     seconds: app_commands.Range[int, 1, MAX_STEP_SECONDS] = 10) -> None:
        await self._seek(interaction, -seconds, relative=True, key="rewound")

    @app_commands.command(name="replay", description="Play the current song from the start")
    async def replay(self, interaction: discord.Interaction) -> None:
        await self._seek(interaction, 0, relative=False, key="replayed")

    @app_commands.command(name="previous", description="Go back to the previous song")
    async def previous(self, interaction: discord.Interaction) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        result = await music.service.previous(self.ctx(interaction))
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        key = "replayed" if result.data.get("replayed") else "previous"
        await self.ok(interaction, self.t(
            interaction.guild.id, "commands", "music", "responses", key,
            title=shorten(result.data.get("title") or "", HISTORY_TITLE_WIDTH), position="0:00",
        ), emoji="⏮️")

    @app_commands.command(name="lyrics", description="Show the lyrics of the current song, or search another song's")
    @app_commands.describe(query="Song to look up (empty: the current song)")
    async def lyrics(self, interaction: discord.Interaction, query: Optional[str] = None) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        guild_id = interaction.guild.id
        if not music_config.lyrics.enabled:
            await self.fail(interaction, self.t(guild_id, "system", "music", "lyrics", "disabled"))
            return
        song = music.state_manager.get_state(guild_id).current_song
        if not query and not song:
            await self.fail(interaction, self.t(guild_id, "system", "music", "ai_errors", "nothing_playing"))
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        found = await (music.lyrics.for_text(query) if query else music.current_lyrics(guild_id))
        if found is None:
            await self.fail(interaction, self.t(guild_id, "system", "music", "lyrics", "not_found"))
            return
        title = f"{found.artist} - {found.track}" if found.artist and found.track else (query or song.get("title", ""))
        embeds = lyrics_embeds(found, shorten(title, 200), self.t(guild_id, "system", "music", "lyrics", "source"))
        can_sync = not query and bool(found.synced) and not music.state_manager.get_state(guild_id).show_lyrics

        async def show_synced(button_interaction: discord.Interaction) -> None:
            if not music.state_manager.get_state(guild_id).show_lyrics:
                await music.handle_toggle_lyrics(button_interaction)
            if not button_interaction.response.is_done():
                await button_interaction.response.defer()

        view = LyricsPages(embeds, sync_label=self.t(guild_id, "system", "music", "lyrics", "show_on_player") if can_sync else None,
                           on_sync=show_synced)
        await self.send(interaction, embed=embeds[0], view=view, ephemeral=True)

    @app_commands.command(name="history", description="Show the songs played in this session")
    async def history(self, interaction: discord.Interaction) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        guild_id = interaction.guild.id
        songs = music.service.history(guild_id)
        if not songs:
            await self.fail(interaction, self.t(guild_id, "system", "music", "ai_errors", "no_history"))
            return
        lines = []
        for index, song in enumerate(songs, 1):
            title = shorten(song.get("title") or "", HISTORY_TITLE_WIDTH)
            url = song.get("url")
            lines.append(f"{index}. [{title}]({url}) · {format_clock(song.get('duration') or 0)}" if url
                         else f"{index}. {title}")
        description = "\n".join(lines)[:4000]
        await self.ok(interaction, self.t(guild_id, "commands", "music", "responses", "history_title", count=len(songs)),
                      emoji="🕘", description=description, ephemeral=True)


class LyricsPages(discord.ui.View):
    """Pages through lyrics; offers to show them synced on the player when they are time-stamped."""

    def __init__(self, embeds: List[discord.Embed], *, sync_label: Optional[str], on_sync: Any) -> None:
        super().__init__(timeout=600)
        self.embeds = embeds
        self.page = 0
        self._on_sync = on_sync
        if len(embeds) < 2:
            self.remove_item(self.back)
            self.remove_item(self.next)
        if sync_label is None:
            self.remove_item(self.sync)
        else:
            self.sync.label = sync_label
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.back.disabled = self.page == 0
        self.next.disabled = self.page >= len(self.embeds) - 1

    async def _turn(self, interaction: discord.Interaction, step: int) -> None:
        self.page = max(0, min(len(self.embeds) - 1, self.page + step))
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.gray)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._turn(interaction, -1)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._turn(interaction, 1)

    @discord.ui.button(emoji="🎤", style=discord.ButtonStyle.primary)
    async def sync(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await self._on_sync(interaction)


def lyrics_embeds(lyrics: Lyrics, title: str, footer: str) -> List[discord.Embed]:
    """Builds one embed per page of lyrics."""
    pages = paginate(lyrics.plain or "♪")
    embeds = []
    for index, page in enumerate(pages, 1):
        embed = discord.Embed(title=f"🎤 | {title}", description=page, color=discord.Color.blue())
        embed.set_footer(text=f"{footer} · {index}/{len(pages)}" if len(pages) > 1 else footer)
        embeds.append(embed)
    return embeds


class FilterCommand(MusicCommandBase, commands.Cog, name="MusicFilter"):
    """``/filter``: audio effects."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.guild_only()
    @app_commands.command(name="filter", description="Apply an audio effect (nightcore, 8D, karaoke...); choose Off to remove it")
    @app_commands.describe(effect="Audio effect to apply")
    @app_commands.choices(effect=[
        app_commands.Choice(name=f"{get_preset(name).emoji} {_FILTER_CHOICE_NAMES[name]}", value=name) for name in FILTER_NAMES
    ])
    async def filter(self, interaction: discord.Interaction, effect: app_commands.Choice[str]) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        result = await music.service.set_filter(self.ctx(interaction), effect.value)
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        guild_id = interaction.guild.id
        name = self.t(guild_id, "system", "music", "filters", effect.value)
        await self.ok(interaction, self.t(guild_id, "commands", "filter", "responses",
                                          "cleared" if effect.value == "off" else "applied", effect=name),
                      emoji=get_preset(effect.value).emoji)

