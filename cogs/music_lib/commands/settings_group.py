"""``/music_settings``: per-server music settings (managers only)."""

from __future__ import annotations

from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from .base import MusicCommandBase


@app_commands.guild_only()
@app_commands.default_permissions(manage_guild=True)
class MusicSettingsGroup(MusicCommandBase, commands.GroupCog, group_name="music_settings",
                         group_description="伺服器音樂設定：DJ 身分組、24/7、點歌頻道…"):
    """``/music_settings`` subcommands; only members who can manage the server see and use them."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Lets only members who can manage the server change the settings."""
        permissions = getattr(interaction.user, "guild_permissions", None)
        if interaction.guild is not None and permissions is not None and (permissions.manage_guild or permissions.administrator):
            return True
        await self.fail(interaction, self.t(getattr(interaction.guild, "id", 0), "commands", "music_settings", "errors", "no_permission"))
        return False

    def _store(self):
        return self.music.store

    async def _saved(self, interaction: discord.Interaction, key: str, **kwargs) -> None:
        await self.ok(interaction, self.t(interaction.guild.id, "commands", "music_settings", "responses", key, **kwargs),
                      emoji="⚙️")

    def _on_off(self, guild_id: int, enabled: bool) -> str:
        return self.t(guild_id, "commands", "music_settings", "values", "on" if enabled else "off")

    @app_commands.command(name="view", description="查看目前的音樂設定")
    async def view(self, interaction: discord.Interaction) -> None:
        if await self.require_music(interaction) is None:
            return
        guild = interaction.guild
        settings = self._store().get_settings(guild.id)
        none = self.t(guild.id, "commands", "music_settings", "values", "none")

        def mention(kind: str, item_id: Optional[int]) -> str:
            if item_id is None:
                return none
            return f"<@&{item_id}>" if kind == "role" else f"<#{item_id}>"

        label = lambda key: self.t(guild.id, "commands", "music_settings", "fields", key)  # noqa: E731
        embed = discord.Embed(title=f"⚙️ | {self.t(guild.id, 'commands', 'music_settings', 'responses', 'view_title')}",
                              color=discord.Color.blue())
        embed.add_field(name=label("dj"), value=mention("role", settings.dj_role_id), inline=True)
        embed.add_field(name=label("vote_ratio"), value=f"{round(settings.vote_ratio * 100)}%", inline=True)
        embed.add_field(name=label("default_volume"), value=f"{settings.default_volume}%", inline=True)
        stay = self._on_off(guild.id, settings.stay_247)
        if settings.stay_247 and settings.stay_channel_id:
            stay += f" ({mention('channel', settings.stay_channel_id)})"
        embed.add_field(name=label("stay_247"), value=stay, inline=True)
        embed.add_field(name=label("request_channel"), value=mention("channel", settings.request_channel_id), inline=True)
        embed.add_field(name=label("stage_announce"), value=self._on_off(guild.id, settings.stage_announce), inline=True)
        await self.send(interaction, embed=embed, ephemeral=True)

    @app_commands.command(name="dj", description="設定 DJ 身分組（不填則取消，所有人都能控制音樂）")
    @app_commands.describe(role="DJ 身分組")
    async def dj(self, interaction: discord.Interaction, role: Optional[discord.Role] = None) -> None:
        if await self.require_music(interaction) is None:
            return
        self._store().update_settings(interaction.guild.id, dj_role_id=role.id if role else None)
        if role is None:
            await self._saved(interaction, "dj_cleared")
        else:
            await self._saved(interaction, "dj_set", role=role.name)

    @app_commands.command(name="vote_ratio", description="非 DJ 跳過歌曲需要多少比例的聽眾投票")
    @app_commands.describe(percent="百分比（預設 50）")
    async def vote_ratio(self, interaction: discord.Interaction, percent: app_commands.Range[int, 10, 100]) -> None:
        if await self.require_music(interaction) is None:
            return
        self._store().update_settings(interaction.guild.id, vote_ratio=percent / 100)
        await self._saved(interaction, "vote_ratio_set", percent=percent)

    @app_commands.command(name="default_volume", description="每次開始播放時的預設音量")
    @app_commands.describe(percent="音量百分比 (0-100)")
    async def default_volume(self, interaction: discord.Interaction, percent: app_commands.Range[int, 0, 100]) -> None:
        if await self.require_music(interaction) is None:
            return
        self._store().update_settings(interaction.guild.id, default_volume=percent)
        await self._saved(interaction, "default_volume_set", percent=percent)

    @app_commands.command(name="stay_247", description="24/7 模式：播完或沒人時也留在語音頻道，重啟後自動回來")
    @app_commands.describe(enabled="開啟或關閉", channel="要常駐的語音頻道（預設為你所在的頻道）")
    async def stay_247(self, interaction: discord.Interaction, enabled: bool,
                       channel: Optional[discord.VoiceChannel] = None) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        guild = interaction.guild
        if not enabled:
            music.store.update_settings(guild.id, stay_247=False)
            await music.leave_if_idle(guild.id)
            await self._saved(interaction, "stay_247_off")
            return
        voice = getattr(interaction.user, "voice", None)
        bot_voice = guild.voice_client
        target = channel or (voice.channel if voice else None) or (bot_voice.channel if bot_voice else None)
        if target is None:
            await self.fail(interaction, self.t(guild.id, "commands", "music_settings", "errors", "no_channel"))
            return
        await interaction.response.defer(ephemeral=False)
        music.store.update_settings(guild.id, stay_247=True, stay_channel_id=target.id)
        if not await music.stay_in(guild, target):
            await self.fail(interaction, self.t(guild.id, "system", "music", "ai_errors", "voice_connect_failed"))
            return
        await self._saved(interaction, "stay_247_on", channel=target.name)

    @app_commands.command(name="request_channel", description="設定點歌頻道：在那裡輸入的文字都會直接點歌（不填則取消）")
    @app_commands.describe(channel="點歌頻道")
    async def request_channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None) -> None:
        music = await self.require_music(interaction)
        if music is None:
            return
        await interaction.response.defer(ephemeral=True)
        if channel is None:
            await music.requests.disable(interaction.guild)
            await self._saved(interaction, "request_channel_cleared")
            return
        if not await music.requests.enable(interaction.guild, channel):
            await self.fail(interaction, self.t(interaction.guild.id, "commands", "music_settings", "errors", "request_channel_failed"))
            return
        await self._saved(interaction, "request_channel_set", channel=channel.mention)

    @app_commands.command(name="stage_announce", description="在舞台頻道播放時，把舞台主題設為目前的歌名")
    @app_commands.describe(enabled="開啟或關閉")
    async def stage_announce(self, interaction: discord.Interaction, enabled: bool) -> None:
        if await self.require_music(interaction) is None:
            return
        self._store().update_settings(interaction.guild.id, stage_announce=enabled)
        await self._saved(interaction, "stage_announce_set", status=self._on_off(interaction.guild.id, enabled))
