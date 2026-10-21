"""``/queue`` commands: reorder, export and import the queue."""

from __future__ import annotations

import io

import discord
from discord import app_commands
from discord.ext import commands

from ..track_io import parse_tracks, tracks_to_text
from ..ui.text import shorten
from .base import MusicCommandBase

TITLE_WIDTH = 50
# Imported files larger than this are refused (a list of 500 links is far smaller).
MAX_IMPORT_BYTES = 256 * 1024


@app_commands.guild_only()
class QueueGroup(MusicCommandBase, commands.GroupCog, group_name="queue", group_description="待播清單：調整順序、匯出、匯入"):
    """``/queue`` subcommands (``/queue_remove`` and ``/queue_clear`` stay where they were)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    async def _refresh_panel(self, guild_id: int) -> None:
        """Updates the player's queue list and menu after the order changed."""
        view = self.music.ui_manager.get_current_view(guild_id)
        if view is None:
            return
        if await view.refresh_queue_field() and view.message is not None and view.current_embed is not None:
            try:
                await view.message.edit(embed=view.current_embed, view=view)
            except discord.HTTPException:
                pass
        await view.update_button_state()

    @app_commands.command(name="move", description="把待播清單的一首歌移到另一個位置")
    @app_commands.describe(position="歌曲目前的位置（1 是下一首）", to="要移到的位置")
    async def move(self, interaction: discord.Interaction, position: app_commands.Range[int, 1, 50],
                   to: app_commands.Range[int, 1, 50]) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        result = await music.service.move(self.ctx(interaction), position, to)
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        await self._refresh_panel(interaction.guild.id)
        await self.ok(interaction, self.t(interaction.guild.id, "commands", "queue", "responses", "moved",
                                          title=shorten(result.data["title"], TITLE_WIDTH), position=to), emoji="↕️")

    @app_commands.command(name="swap", description="交換待播清單中兩首歌的位置")
    @app_commands.describe(first="第一首的位置", second="第二首的位置")
    async def swap(self, interaction: discord.Interaction, first: app_commands.Range[int, 1, 50],
                   second: app_commands.Range[int, 1, 50]) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        result = await music.service.swap(self.ctx(interaction), first, second)
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        await self._refresh_panel(interaction.guild.id)
        await self.ok(interaction, self.t(interaction.guild.id, "commands", "queue", "responses", "swapped",
                                          first=shorten(result.data["first"], TITLE_WIDTH),
                                          second=shorten(result.data["second"], TITLE_WIDTH)), emoji="🔃")

    @app_commands.command(name="export", description="把目前的歌曲和待播清單匯出成文字檔")
    async def export(self, interaction: discord.Interaction) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        guild_id = interaction.guild.id
        tracks = music.service.upcoming_tracks(guild_id)
        if not tracks:
            await self.fail(interaction, self.t(guild_id, "system", "music", "ai_errors", "nothing_to_import"))
            return
        text = tracks_to_text(tracks, f"PigPig queue - {interaction.guild.name}")
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename="queue.txt")
        title = self.t(guild_id, "commands", "queue", "responses", "exported", count=len(tracks))
        await self.send(interaction, embed=discord.Embed(title=f"📤 | {title}", color=discord.Color.blue()),
                        file=file, ephemeral=True)

    @app_commands.command(name="import", description="從文字檔匯入歌曲到待播清單（每行一個連結）")
    @app_commands.describe(file="用 /queue export 或 /playlist export 匯出的文字檔", shuffle="打亂順序")
    async def import_(self, interaction: discord.Interaction, file: discord.Attachment, shuffle: bool = False) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        guild_id = interaction.guild.id
        tracks = await read_track_file(file)
        if not tracks:
            await self.fail(interaction, self.t(guild_id, "system", "music", "ai_errors", "nothing_to_import"))
            return
        await interaction.response.defer(thinking=True)
        result = await music.service.play_tracks(self.ctx(interaction), tracks, shuffle=shuffle)
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        await self.ok(interaction, self.t(guild_id, "commands", "queue", "responses", "imported",
                                          count=result.data["total"]), emoji="📥")


async def read_track_file(file: discord.Attachment) -> list:
    """Reads the songs of an uploaded text file (nothing for a file that is too big or not text)."""
    if file.size > MAX_IMPORT_BYTES:
        return []
    try:
        content = (await file.read()).decode("utf-8-sig")
    except (discord.HTTPException, UnicodeDecodeError):
        return []
    return parse_tracks(content)
