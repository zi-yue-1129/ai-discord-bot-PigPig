"""LangChain tool for the bot to modify its own system prompt.

The LLM reads its current personality from the system-prompt context it
already has, generates a merged version, and calls this tool to write it.
Only the write side lives here — no extra LLM call is needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.tools.structured import StructuredTool

from addons.logging import get_logger

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_logger = get_logger(server_id="Bot", source="llm.tools.system_prompt_tools")

__all__ = ["check_personality_permission", "write_personality", "SystemPromptTools"]

# Longest part of a proposed personality shown above its Confirm button (Discord allows 2000 characters).
PREVIEW_CHARS = 1500

# Used when the language manager is not loaded.
_FALLBACK_TEXT = {
    "prompt": "{member}, change the {scope} personality to this?",
    "scope_channel": "channel",
    "scope_server": "server",
    "saved": "The personality was updated.",
    "failed": "The personality could not be saved; nothing changed.",
    "no_permission": "You can no longer change this personality; nothing changed.",
    "ask_confirm": "Confirm",
    "ask_cancel": "Cancel",
    "ask_not_yours": "Only the member being asked can answer.",
    "ask_done": "This question was already answered.",
    "ask_cancelled": "Cancelled; nothing changed.",
    "ask_expired": "No answer in time; nothing changed.",
    "ask_replaced": "Replaced by a newer proposal; nothing changed.",
}


def _personality_text(bot: Any, guild_id: str, key: str, **kwargs: Any) -> str:
    """Translates a line of the personality confirmation for a guild."""
    language = bot.get_cog("LanguageManager") if bot is not None else None
    if language is not None:
        text = language.translate(guild_id, "commands", "system_prompt", "ai_confirm", key, **kwargs)
        if isinstance(text, str) and text:
            return text
    return _FALLBACK_TEXT.get(key, key).format(**kwargs)


def _preview(prompt: str) -> str:
    """The proposed personality as a quote, cut to fit one message."""
    text = prompt.strip()
    if len(text) > PREVIEW_CHARS:
        text = text[:PREVIEW_CHARS].rstrip() + "…"
    return "\n".join("> " + line for line in text.splitlines() or [""])


def check_personality_permission(bot: Any, author: Any, guild: Any, channel: Any, scope: str) -> str | None:
    """Check whether *author* may modify the personality at *scope*.

    Any scope other than "server" results in a channel-level write in
    :func:`write_personality`, so it is validated as a channel change.

    Args:
        bot: The discord.ext.commands.Bot instance.
        author: The member requesting the change.
        guild: The guild the change applies to.
        channel: The channel the change applies to.
        scope: "channel" or "server".

    Returns:
        None if permitted, otherwise a human-readable error string.
    """
    from cogs.system_prompt.permissions import PermissionValidator

    validator = PermissionValidator(bot)
    if scope == "server":
        if not validator.can_modify_server_prompt(author, guild):
            return "Error: You need administrator permissions to modify the server-level personality."
    elif not validator.can_modify_channel_prompt(author, channel):
        return "Error: You need manage channel permissions to modify the channel-level personality."
    return None


async def write_personality(
    guild_id: str,
    channel_id: str,
    merged_prompt: str,
    scope: str,
    bot: Any,
    user_id: str,
) -> str:
    """Write a merged personality string to the system prompt store.

    Args:
        guild_id: Discord guild ID string.
        channel_id: Discord channel ID string.
        merged_prompt: The complete merged system prompt text.
        scope: "channel" or "server".
        bot: The discord.ext.commands.Bot instance.
        user_id: ID of the user requesting the change (for audit).

    Returns:
        A human-readable confirmation or error string.
    """
    from cogs.system_prompt.exceptions import ContentTooLongError, UnsafeContentError

    cog = bot.get_cog("SystemPromptManagerCog")
    if cog is None:
        return "Error: SystemPromptManagerCog is not loaded. Cannot save personality."

    manager = cog.get_system_prompt_manager()
    prompt_data: dict[str, Any] = {"prompt": merged_prompt, "enabled": True}

    try:
        if scope == "server":
            manager.set_server_prompt(guild_id, prompt_data, user_id)
            manager.cache.invalidate(guild_id)
            return "Personality updated successfully for the entire server."
        else:
            manager.set_channel_prompt(guild_id, channel_id, prompt_data, user_id)
            manager.cache.invalidate(guild_id, channel_id)
            return "Personality updated successfully for this channel."
    except ContentTooLongError as exc:
        return f"Error: The prompt is too long ({exc}). Please shorten your description."
    except UnsafeContentError as exc:
        return f"Error: The prompt contains unsafe content ({exc}). Please revise."
    except Exception as exc:
        _logger.error(f"write_personality failed: {exc}")
        return f"Error saving personality: {exc}"


class SystemPromptTools:
    """Container for the bot's self-modification tool."""

    def __init__(self, runtime: "OrchestratorRequest") -> None:
        """Initialize with the orchestrator runtime context.

        Args:
            runtime: The current OrchestratorRequest context.
        """
        self.runtime = runtime
        self.logger = getattr(runtime, "logger", _logger)

    def get_tools(self) -> list:
        """Return the list of self-modification tools.

        Returns:
            List containing the update_personality StructuredTool.
        """
        runtime = self.runtime

        async def update_personality(merged_prompt: str, scope: str = "channel") -> str:
            """Propose a new personality or system prompt for this channel or server.

            The proposal is posted with a Confirm button that only the requesting member
            can press; the personality changes only after they press it.

            You already know your current personality from the system prompt in your
            context. Generate a COMPLETE merged version incorporating the user's
            requested changes (do not just write the delta), then call this tool.

            Args:
                merged_prompt: The complete merged system prompt text — your current
                    personality with the requested changes incorporated. Must be a
                    full system prompt, not just the changed part.
                scope: "channel" applies only to the current channel (requires
                    manage-channel permission). "server" applies to the entire
                    server (admin only).

            Returns:
                Confirmation message or an error description.
            """
            message = getattr(runtime, "message", None)
            if message is None:
                return "Error: No message context available."

            guild = getattr(message, "guild", None)
            channel = getattr(message, "channel", None)
            author = getattr(message, "author", None)

            if guild is None or channel is None or author is None:
                return "Error: Cannot determine guild, channel, or author."

            guild_id = str(guild.id)
            channel_id = str(channel.id)
            user_id = str(author.id)
            bot = getattr(runtime, "bot", None)

            permission_error = check_personality_permission(bot, author, guild, channel, scope)
            if permission_error is not None:
                return permission_error

            # The text the model wrote may come from someone else's message or a web page in its
            # context, so the change only happens when the member who asked presses Confirm.
            from addons.confirm import ConfirmView, ask

            def text(key: str, **kwargs: Any) -> str:
                return _personality_text(bot, guild_id, key, **kwargs)

            async def on_confirm() -> str:
                # Checked again: the member may have lost the permission while the question was open.
                member = guild.get_member(author.id) if hasattr(guild, "get_member") else author
                if member is None or check_personality_permission(bot, member, guild, channel, scope) is not None:
                    return text("no_permission")
                result = await write_personality(guild_id, channel_id, merged_prompt, scope, bot, user_id)
                return text("failed") + f" ({result})" if result.startswith("Error") else text("saved")

            pending = getattr(bot, "personality_asks", None)
            if not isinstance(pending, dict):
                pending = {}
                setattr(bot, "personality_asks", pending)
            key = (guild_id, "server" if scope == "server" else channel_id, author.id)
            view = ConfirmView(author.id, text, on_confirm, pending, key)
            scope_name = text("scope_server" if scope == "server" else "scope_channel")
            content = text("prompt", member=f"<@{author.id}>", scope=scope_name) + "\n" + _preview(merged_prompt)
            try:
                await ask(channel, content, view)
            except Exception as exc:
                self.logger.error(f"update_personality could not post its confirmation: {exc}")
                return "Error: Could not post the confirmation button, so the personality was not changed."
            return (
                "Posted the proposed personality with a Confirm button. Nothing changes until the member who "
                "asked presses Confirm; tell them to check it and press it."
            )

        _message_meta: dict[str, str] = {"target_agent_mode": "message"}
        return [
            StructuredTool.from_function(
                func=None,
                name="update_personality",
                metadata=_message_meta,
                coroutine=update_personality,
                description=update_personality.__doc__,
            )
        ]
