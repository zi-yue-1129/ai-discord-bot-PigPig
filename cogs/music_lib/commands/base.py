"""Shared plumbing for the music command groups.

The groups live in their own cogs (one per slash command group) but act on the
``YTMusic`` cog's player, so each looks it up when a command runs.
"""

from __future__ import annotations

from typing import Any, Optional

import discord

from ..context import PlaybackContext


class MusicCommandBase:
    """Mixin giving a command cog access to the music player and to translations.

    Attributes:
        bot: The Discord bot.
    """

    bot: Any

    @property
    def music(self) -> Any:
        """The ``YTMusic`` cog (``None`` when it failed to load)."""
        return self.bot.get_cog("YTMusic")

    def t(self, guild_id: Any, *path: str, **kwargs: Any) -> str:
        """Translates ``path`` for the guild (falls back to the last key)."""
        lang_manager = self.bot.get_cog("LanguageManager")
        if lang_manager is None:
            return path[-1]
        return lang_manager.translate(str(guild_id), *path, **kwargs)

    @staticmethod
    def ctx(interaction: discord.Interaction) -> PlaybackContext:
        """The playback context of a command."""
        return PlaybackContext.from_interaction(interaction)

    async def send(self, interaction: discord.Interaction, *, ephemeral: bool = False, **kwargs: Any) -> None:
        """Answers the interaction, as a follow-up when it was already answered or deferred."""
        if interaction.response.is_done():
            await interaction.followup.send(ephemeral=ephemeral, **kwargs)
        else:
            await interaction.response.send_message(ephemeral=ephemeral, **kwargs)

    async def ok(self, interaction: discord.Interaction, text: str, *, emoji: str = "✅", ephemeral: bool = False,
                 description: Optional[str] = None) -> None:
        """Answers with a blue success embed."""
        embed = discord.Embed(title=f"{emoji} | {text}", description=description, color=discord.Color.blue())
        await self.send(interaction, embed=embed, ephemeral=ephemeral)

    async def fail(self, interaction: discord.Interaction, text: str) -> None:
        """Answers (only to the user) with a red error embed."""
        await self.send(interaction, embed=discord.Embed(title=f"❌ | {text}", color=discord.Color.red()), ephemeral=True)

    async def fail_result(self, interaction: discord.Interaction, result: Any) -> None:
        """Answers with the translated reason of a failed ``ActionResult``."""
        await self.fail(interaction, self.t(
            interaction.guild.id, "system", "music", "ai_errors", result.reason, detail=result.detail
        ))

    async def require_music(self, interaction: discord.Interaction) -> Optional[Any]:
        """Returns the music cog, or answers that music is unavailable and returns ``None``."""
        music = self.music
        if music is None:
            await self.fail(interaction, "Music is not available.")
        return music
