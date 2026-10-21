"""``/playlist``: personal and server playlists."""

from __future__ import annotations

import io
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..playlists import PERSONAL, SERVER, PlaylistService
from ..track_io import tracks_to_text
from ..ui.text import format_clock, shorten
from .base import MusicCommandBase
from .queue_group import read_track_file

TITLE_WIDTH = 50
# Songs listed by /playlist view (the export holds all of them).
VIEW_LIMIT = 40

SCOPE_CHOICES = [
    app_commands.Choice(name="個人歌單", value=PERSONAL),
    app_commands.Choice(name="伺服器歌單", value=SERVER),
]


@app_commands.guild_only()
class PlaylistGroup(MusicCommandBase, commands.GroupCog, group_name="playlist", group_description="個人與伺服器歌單"):
    """``/playlist`` subcommands. ``scope`` defaults to the user's personal playlists."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    def _playlists(self) -> PlaylistService:
        return self.music.playlists

    def _scope(self, scope) -> str:
        return scope.value if scope is not None else PERSONAL

    def _scope_name(self, guild_id: int, scope: str) -> str:
        return self.t(guild_id, "commands", "playlist", "scopes", scope)

    async def _done(self, interaction: discord.Interaction, result, key: str, *, emoji: str = "✅",
                    ephemeral: bool = False, **kwargs) -> None:
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        await self.ok(interaction, self.t(interaction.guild.id, "commands", "playlist", "responses", key,
                                          **{**result.data, **kwargs}), emoji=emoji, ephemeral=ephemeral)

    async def name_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Suggests the user's and the server's playlist names."""
        music = self.music
        if music is None or interaction.guild is None:
            return []
        names = await music.playlists.names(self.ctx(interaction))
        current = current.lower()
        seen, choices = set(), []
        for scope in (PERSONAL, SERVER):
            for playlist in names[scope]:
                if current in playlist.name.lower() and playlist.name.lower() not in seen:
                    seen.add(playlist.name.lower())
                    choices.append(app_commands.Choice(name=f"{playlist.name} ({playlist.track_count})", value=playlist.name))
        return choices[:25]

    @app_commands.command(name="create", description="建立新的歌單")
    @app_commands.describe(name="歌單名稱", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    async def create(self, interaction: discord.Interaction, name: str,
                     scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        scope_value = self._scope(scope)
        result = await self._playlists().create(self.ctx(interaction), name, scope_value)
        await self._done(interaction, result, "created", emoji="📁", scope=self._scope_name(interaction.guild.id, scope_value))

    @app_commands.command(name="delete", description="刪除歌單")
    @app_commands.describe(name="歌單名稱", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def delete(self, interaction: discord.Interaction, name: str,
                     scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        result = await self._playlists().delete(self.ctx(interaction), name, self._scope(scope))
        await self._done(interaction, result, "deleted", emoji="🗑️")

    @app_commands.command(name="rename", description="重新命名歌單")
    @app_commands.describe(name="目前的名稱", new_name="新名稱", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def rename(self, interaction: discord.Interaction, name: str, new_name: str,
                     scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        result = await self._playlists().rename(self.ctx(interaction), name, new_name, self._scope(scope))
        await self._done(interaction, result, "renamed", emoji="✏️", old=name)

    @app_commands.command(name="list", description="列出你的歌單和這個伺服器的歌單")
    async def list_(self, interaction: discord.Interaction) -> None:
        if await self.require_music(interaction) is None:
            return
        guild_id = interaction.guild.id
        names = await self._playlists().names(self.ctx(interaction))
        none = self.t(guild_id, "commands", "playlist", "responses", "none")
        embed = discord.Embed(title=f"📁 | {self.t(guild_id, 'commands', 'playlist', 'responses', 'list_title')}",
                              color=discord.Color.blue())
        for scope in (PERSONAL, SERVER):
            lines = [f"• **{playlist.name}** · {playlist.track_count}" for playlist in names[scope]]
            embed.add_field(name=self._scope_name(guild_id, scope), value="\n".join(lines)[:1024] or none, inline=False)
        await self.send(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="view", description="查看歌單裡的歌曲")
    @app_commands.describe(name="歌單名稱", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def view(self, interaction: discord.Interaction, name: str, scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        guild_id = interaction.guild.id
        result = await self._playlists().get(self.ctx(interaction), name, self._scope(scope))
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        playlist = result.data["playlist"]
        lines = [f"{index}. [{shorten(track['title'], TITLE_WIDTH)}]({track['url']}) · {format_clock(track.get('duration') or 0)}"
                 for index, track in enumerate(playlist.tracks[:VIEW_LIMIT], 1)]
        if playlist.track_count > VIEW_LIMIT:
            lines.append(self.t(guild_id, "commands", "playlist", "responses", "more", count=playlist.track_count - VIEW_LIMIT))
        description = "\n".join(lines)[:4000] or self.t(guild_id, "commands", "playlist", "responses", "empty")
        embed = discord.Embed(title=f"📁 | {playlist.name} ({playlist.track_count})", description=description,
                              color=discord.Color.blue())
        await self.send(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="add", description="把歌曲加入歌單（不填則加入目前播放的歌，也可以貼播放清單連結）")
    @app_commands.describe(name="歌單名稱", query="歌名、影片或播放清單連結（不填則為目前播放的歌曲）",
                           scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def add(self, interaction: discord.Interaction, name: str, query: Optional[str] = None,
                  scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        await interaction.response.defer(thinking=True)
        ctx = self.ctx(interaction)
        found = await self._playlists().resolve(ctx, query)
        if not found.ok:
            await self.fail_result(interaction, found)
            return
        result = await self._playlists().add_tracks(ctx, name, self._scope(scope), found.data["tracks"])
        title = shorten(found.data["tracks"][0].get("title") or "", TITLE_WIDTH) if len(found.data["tracks"]) == 1 else ""
        await self._done(interaction, result, "added_one" if title and result.ok and result.data["added"] else "added",
                         emoji="➕", title=title)

    @app_commands.command(name="remove", description="從歌單移除一首歌")
    @app_commands.describe(name="歌單名稱", position="歌曲在歌單中的位置（用 /playlist view 查看）",
                           scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def remove(self, interaction: discord.Interaction, name: str, position: app_commands.Range[int, 1, 1000],
                     scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        result = await self._playlists().remove_track(self.ctx(interaction), name, position, self._scope(scope))
        if result.ok:
            result.data["title"] = shorten(result.data["title"], TITLE_WIDTH)
        await self._done(interaction, result, "removed", emoji="➖", name=name)

    @app_commands.command(name="play", description="播放歌單")
    @app_commands.describe(name="歌單名稱", shuffle="打亂順序", scope="個人或伺服器歌單（不填則先找你的歌單）")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def play(self, interaction: discord.Interaction, name: str, shuffle: bool = False,
                   scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        await interaction.response.defer(thinking=True)
        result = await self._playlists().play(self.ctx(interaction), name, scope.value if scope else None, shuffle=shuffle)
        await self._done(interaction, result, "playing", emoji="▶️")

    @app_commands.command(name="save_queue", description="把目前的歌曲和待播清單存成歌單")
    @app_commands.describe(name="歌單名稱（不存在會自動建立）", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def save_queue(self, interaction: discord.Interaction, name: str, scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        result = await self._playlists().save_queue(self.ctx(interaction), name, self._scope(scope))
        await self._done(interaction, result, "added", emoji="💾")

    @app_commands.command(name="share", description="把你的個人歌單複製一份給其他人")
    @app_commands.describe(name="你的歌單名稱", user="要分享給誰")
    @app_commands.autocomplete(name=name_autocomplete)
    async def share(self, interaction: discord.Interaction, name: str, user: discord.Member) -> None:
        if await self.require_music(interaction) is None:
            return
        result = await self._playlists().share(self.ctx(interaction), name, user)
        await self._done(interaction, result, "shared", emoji="🎁", user=user.display_name)
        if result.ok:
            try:
                await user.send(self.t(interaction.guild.id, "commands", "playlist", "responses", "shared_dm",
                                       sender=interaction.user.display_name, name=result.data["name"],
                                       count=result.data["count"]))
            except (discord.Forbidden, discord.HTTPException):
                pass

    @app_commands.command(name="export", description="把歌單匯出成文字檔")
    @app_commands.describe(name="歌單名稱", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    @app_commands.autocomplete(name=name_autocomplete)
    async def export(self, interaction: discord.Interaction, name: str, scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        result = await self._playlists().get(self.ctx(interaction), name, self._scope(scope))
        if not result.ok:
            await self.fail_result(interaction, result)
            return
        playlist = result.data["playlist"]
        text = tracks_to_text(playlist.tracks, f"PigPig playlist - {playlist.name}")
        file = discord.File(io.BytesIO(text.encode("utf-8")), filename=f"{playlist.name}.txt")
        title = self.t(interaction.guild.id, "commands", "playlist", "responses", "exported",
                       name=playlist.name, count=playlist.track_count)
        await self.send(interaction, embed=discord.Embed(title=f"📤 | {title}", color=discord.Color.blue()),
                        file=file, ephemeral=True)

    @app_commands.command(name="import", description="從文字檔匯入歌曲到歌單（不存在會自動建立）")
    @app_commands.describe(name="歌單名稱", file="每行一個連結的文字檔", scope="個人歌單（預設）或伺服器歌單")
    @app_commands.choices(scope=SCOPE_CHOICES)
    async def import_(self, interaction: discord.Interaction, name: str, file: discord.Attachment,
                      scope: Optional[app_commands.Choice[str]] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        tracks = await read_track_file(file)
        if not tracks:
            await self.fail(interaction, self.t(interaction.guild.id, "system", "music", "ai_errors", "nothing_to_import"))
            return
        result = await self._playlists().add_tracks(self.ctx(interaction), name, self._scope(scope), tracks, create=True)
        await self._done(interaction, result, "added", emoji="📥")
