"""Chooses the message shown to a user when a slash command fails."""

from __future__ import annotations

from typing import Any, Optional

from discord import app_commands

from addons.logging import get_logger

logger = get_logger(server_id="Bot", source=__name__)

_NOT_FOUND_MARKER = "[Translation not found"
_COOLDOWN_FALLBACK = "⏳ 請稍後再試，此指令冷卻中，還需等待 {retry_after} 秒。(Command on cooldown, wait {retry_after}s.)"
_PERMISSION_FALLBACK = "❌ 你沒有權限使用此指令。(Permission denied)"
_BOT_PERMISSION_FALLBACK = "🤖 機器人缺少必要的權限來執行此指令。(The bot is missing permissions to run this command.)"
_UNEXPECTED_FALLBACK = "❌ 抱歉，執行此指令時發生未預期的錯誤。(An unexpected error occurred.)"


def _translated(lang_manager: Optional[Any], guild_id: str, keys: tuple, fallback: str, **kwargs: Any) -> str:
    """Translates ``keys``, using ``fallback`` when there is no usable translation."""
    if lang_manager is None:
        return fallback.format(**kwargs)
    try:
        text = lang_manager.translate(guild_id, *keys, **kwargs)
    except Exception:
        # The user still needs an answer when a translation file is broken.
        logger.error(f"Translation failed for {keys}", exc_info=True)
        return fallback.format(**kwargs)
    if not text or text.startswith(_NOT_FOUND_MARKER):
        return fallback.format(**kwargs)
    return text


def describe_command_error(error: app_commands.AppCommandError, lang_manager: Optional[Any], guild_id: str) -> str:
    """Returns the user-facing text for a slash command error.

    Args:
        error: The error raised by the command or its checks.
        lang_manager: The language manager, or None.
        guild_id: The guild whose language is used.

    Returns:
        A translated message; never a "translation not found" placeholder.
    """
    if isinstance(error, app_commands.CommandOnCooldown):
        return _translated(
            lang_manager, guild_id, ("errors", "cooldown"), _COOLDOWN_FALLBACK, retry_after=round(error.retry_after, 1)
        )
    if isinstance(error, app_commands.BotMissingPermissions):
        return _BOT_PERMISSION_FALLBACK
    if isinstance(error, app_commands.CheckFailure):
        # Includes MissingPermissions and ``app_commands.check`` failures such as owner-only commands.
        return _translated(lang_manager, guild_id, ("errors", "permission_denied"), _PERMISSION_FALLBACK)
    return _translated(lang_manager, guild_id, ("system", "errors", "unexpected"), _UNEXPECTED_FALLBACK)
