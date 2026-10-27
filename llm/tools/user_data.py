# MIT License
#
# Copyright (c) 2024 starpig1129
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""User memory management tools for LLM integration.

This module provides LangChain-compatible tools for managing user personal
memory (procedural memory) through the UserDataCog.
"""

from addons.logging import get_logger
from typing import Optional, Any, TYPE_CHECKING, Union, cast

import discord
from langchain_core.tools import tool

from function import func
from addons.confirm import ConfirmView, ask
from addons.rate_limiter import format_wait
from cogs.userdata import UserDataCog
from llm.memory.privacy import hidden_in_guild_async

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest


# Module-level logger
_logger = get_logger(server_id="Bot", source="llm.tools.user_data")


# Longest part of a proposed memory quoted in the question to the member it is about.
ASK_PREVIEW_CHARS = 500

# Used when the language manager is not loaded.
_ASK_FALLBACK = {
    "prompt": "{target}, {asker} would like me to remember this about you: {memory}\nSave it to your personal memory?",
    "too_often": "You have asked people to accept too often lately. Try again in {wait}s.",
    "ask_confirm": "Accept",
    "ask_cancel": "Decline",
    "ask_not_yours": "Only the member being asked can answer.",
    "ask_done": "This question was already answered.",
    "ask_cancelled": "Declined; nothing was remembered.",
    "ask_expired": "No answer in time; nothing was remembered.",
    "ask_replaced": "Replaced by a newer request; this one was not remembered.",
}


class UserMemoryTools:
    """Container class for user memory management tools.
    
    This class provides tools for a LangChain Agent to manage a user's
    personal memory (also known as procedural memory). It encapsulates
    the UserDataCog's functionality, allowing the Agent to read or save
    specific preferences, facts, or interaction rules that the user has
    previously asked the bot to remember.
    
    Attributes:
        runtime: The orchestrator request containing bot, message, and logger.
        logger: Logger instance for this tool.
    """

    def __init__(self, runtime: "OrchestratorRequest"):
        """Initializes UserMemoryTools with runtime context.
        
        Args:
            runtime: The orchestrator request object containing necessary context
                (bot, logger, message, etc.).
        """
        self.runtime = runtime
        self.logger = getattr(self.runtime, "logger", _logger)

    def _get_bot(self) -> Optional[Any]:
        """Safely retrieves the bot instance from the runtime.
        
        Returns:
            The bot instance if available, None otherwise.
        """
        bot = getattr(self.runtime, "bot", None)
        if not bot:
            self.logger.error("Bot instance not available in runtime.")
        return bot

    def _get_cog(self) -> Optional[UserDataCog]:
        """Safely retrieves the UserDataCog.
        
        Returns:
            The UserDataCog instance if available, None otherwise.
        """
        bot = self._get_bot()
        if not bot:
            return None
        
        cog = bot.get_cog("UserDataCog")
        if not cog:
            self.logger.error("UserDataCog is not loaded.")
            return None
        
        return cog

    def get_tools(self) -> list:
        """Returns a list of LangChain tools bound to this runtime.
        
        Returns:
            A list containing user memory management tools with runtime context.
        """
        runtime = self.runtime
        logger = self.logger
        get_bot = self._get_bot
        get_cog = self._get_cog

        async def _invalidate_procedural_cache(effective_id: Any) -> None:
            """Best-effort invalidation of procedural memory cache."""
            try:
                bot = get_bot()
                if not bot:
                    return
                orchestrator = getattr(bot, "orchestrator", None)
                if orchestrator:
                    provider = getattr(
                        getattr(orchestrator, "context_manager", None),
                        "procedural_provider",
                        None,
                    )
                    if provider and hasattr(provider, "invalidate"):
                        await provider.invalidate(str(effective_id))
            except Exception as e:
                logger.warning(
                    "Procedural cache invalidation failed",
                    extra={"effective_id": effective_id},
                    exception=e,
                )
        
        def _ask_text(guild_id: str, key: str, **kwargs: Any) -> str:
            bot = get_bot()
            language = bot.get_cog("LanguageManager") if bot is not None else None
            if language is not None:
                text = language.translate(guild_id, "commands", "userdata", "ask_others", key, **kwargs)
                if isinstance(text, str) and text:
                    return text
            return _ASK_FALLBACK.get(key, key).format(**kwargs)

        async def _ask_to_save(message: Any, target_id: int, memory: str) -> str:
            """Posts ``memory`` with Accept and Decline buttons only the member it is about can press."""
            guild = getattr(message, "guild", None)
            channel = getattr(message, "channel", None)
            target = guild.get_member(target_id) if guild is not None else None
            if target is None or channel is None:
                return "Refused: a memory about someone else can only be proposed to a member of this server."
            asker_id = message.author.id
            guild_id = str(guild.id)
            # Each question pings the member, so how often one person may ask is limited (owner's rate_limits).
            limiter = getattr(get_bot(), "rate_limiter", None)
            if limiter is not None:
                wait = limiter.hit("ask_others", asker_id)
                if wait:
                    return _ask_text(guild_id, "too_often", wait=format_wait(wait))

            async def on_confirm() -> str:
                cog = get_cog()
                if cog is None:
                    return "Error: Personal memory system (UserDataCog) is not loaded."
                result = await cog._save_user_data(
                    str(target_id), getattr(target, "name", f"User_{target_id}"), memory, message,
                    nickname=getattr(target, "display_name", None),
                )
                await _invalidate_procedural_cache(target_id)
                return f"<@{target_id}> {result}"

            bot = get_bot()
            pending = getattr(bot, "memory_asks", None)
            if not isinstance(pending, dict):
                pending = {}
                setattr(bot, "memory_asks", pending)
            view = ConfirmView(
                target_id, lambda key: _ask_text(guild_id, key), on_confirm, pending, (guild_id, asker_id, target_id)
            )
            preview = memory if len(memory) <= ASK_PREVIEW_CHARS else memory[:ASK_PREVIEW_CHARS].rstrip() + "…"
            content = _ask_text(guild_id, "prompt", target=f"<@{target_id}>", asker=f"<@{asker_id}>", memory=preview)
            await ask(channel, content, view, allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=[discord.Object(id=target_id)]
            ))
            return (
                "Asked the other member to accept. Nothing is saved unless they press Accept; "
                "tell the user so."
            )

        @tool
        async def read_user_memory(user_id: int) -> str:
            """Reads the personal memory or preferences stored for a specific user.
    
            Use this tool when you need to know if the user has previously asked
            you to remember something (e.g., their name, a specific interaction
            style, or other preferences).
    
            Args:
                user_id: The Discord user's ID.
    
            Returns:
                A string containing the stored memory, or ``data_not_found`` when
                nothing is stored for that user.
            """
            cog = get_cog()
            if not cog:
                return "Error: Personal memory system (UserDataCog) is not loaded."
    
            try:
                logger.info(
                    "Reading personal memory",
                    extra={"user_id": user_id}
                )
    
                # Only the requested user's memory is ever returned; an unknown user is
                # reported as such instead of being replaced by the message author.
                try:
                    effective_id = int(user_id)
                except (TypeError, ValueError):
                    return f"Error: invalid user_id {user_id!r}; pass the numeric Discord user ID."

                # A member hidden with /leaderboard optout can read their own memory, nobody else's;
                # without the opt-out list nobody else's memory is read out either.
                message = getattr(runtime, "message", None)
                guild = getattr(message, "guild", None)
                asker_id = getattr(getattr(message, "author", None), "id", None)
                if guild is not None and asker_id != effective_id:
                    hidden = await hidden_in_guild_async(get_bot(), guild.id)
                    if hidden is None:
                        return "This memory cannot be shown right now."
                    if effective_id in hidden:
                        return "This member's memory is hidden (they opted out); do not share or guess it."

                user_mgr = getattr(cog, "user_manager", None)
                if user_mgr and not await user_mgr.get_user_info(str(effective_id)):
                    return "data_not_found"
                    
                # Ensure cog receives a string user_id (storage uses text keys).
                return await cog._read_user_data(
                    str(effective_id),
                    cast(
                        Union[discord.Interaction, discord.Message],
                        getattr(runtime, "message", None)
                    ),
                )
            except Exception as e:
                await func.report_error(
                    e, f"Failed to read personal memory for user_id={user_id}"
                )
                return f"An unexpected error occurred while reading memory: {e}"

        @tool
        async def clear_user_memory(user_id: int) -> str:
            """Clears all personal memory and preferences stored for a specific user.

            Use this tool when the user **explicitly asks** you to forget everything
            about them or clear their memory/preferences.

            Args:
                user_id: The Discord user's ID.

            Returns:
                A string confirming that the memory was successfully cleared,
                or an error message if the operation failed.
            """
            cog = get_cog()
            if not cog:
                return "Error: Personal memory system (UserDataCog) is not loaded."

            try:
                logger.info("Clearing personal memory", extra={"requested_user_id": user_id})

                # Always clear for the requesting user when context is available.
                context = cast(
                    Optional[Union[discord.Interaction, discord.Message]],
                    getattr(runtime, "message", None) or getattr(runtime, "interaction", None)
                )
                requester_id = None

                if isinstance(context, discord.Message) and getattr(context, "author", None):
                    requester_id = getattr(context.author, "id", None)
                elif isinstance(context, discord.Interaction) and getattr(context, "user", None):
                    requester_id = getattr(context.user, "id", None)

                if requester_id:
                    if str(requester_id) != str(user_id):
                        logger.warning(
                            "clear_user_memory: overriding provided user_id with requesting user",
                            extra={"provided_user_id": user_id, "requester_id": requester_id}
                        )
                    effective_id = requester_id
                else:
                    try:
                        effective_id = int(user_id)
                    except Exception:
                        logger.error(
                            "clear_user_memory: unable to determine requesting user",
                            extra={"provided_user_id": user_id}
                        )
                        return "Error: Unable to identify the requesting user to clear memory."

                if not context:
                    logger.error("clear_user_memory: no interaction or message context available")
                    return "Error: Cannot clear memory without a message or interaction context."

                result_msg = await cog._clear_user_data(str(effective_id), context)

                # Invalidate ProceduralMemoryProvider cache so the next request
                # reflects the updated data without waiting for TTL expiry.
                await _invalidate_procedural_cache(effective_id)

                return result_msg

            except Exception as e:
                await func.report_error(
                    e, f"Failed to clear personal memory for user_id={user_id}"
                )
                return f"An unexpected error occurred while clearing memory: {e}"

        @tool
        async def save_user_memory(user_id: int, memory_to_save: str) -> str:
            """Saves or updates a personal memory or preference for a specific user.
    
            Use this tool only when the user **explicitly asks** you to remember
            something (e.g., "My name is Bob," "Please call me Master,"
            "I am a Python developer"). This new information will be intelligently
            merged with any existing memory. A memory about another member is not
            saved right away: that member is asked and it is saved only if they accept.
    
            Args:
                user_id: The Discord ID of the member the memory is about.
                memory_to_save: The new piece of information to remember.
    
            Returns:
                A string confirming that the memory was successfully saved or updated,
                or an error message if the operation failed.
            """
            cog = get_cog()
            if not cog:
                return "Error: Personal memory system (UserDataCog) is not loaded."
            
            if not memory_to_save or memory_to_save.strip() == "":
                return "Error: 'memory_to_save' parameter cannot be empty."
    
            try:
                logger.info(
                    "Saving personal memory",
                    extra={"user_id": user_id}
                )
    
                # A memory is shown to the model in every later chat with that member, on every server,
                # so a memory about someone else is only saved once that member accepts it.
                msg = getattr(runtime, "message", None)
                author_id = getattr(getattr(msg, "author", None), "id", None)
                if author_id is None:
                    return "Error: Cannot save memory without knowing who is asking."
                try:
                    requested_id = int(user_id)
                except (TypeError, ValueError):
                    requested_id = author_id
                if requested_id != author_id:
                    return await _ask_to_save(msg, requested_id, memory_to_save)
                effective_id = author_id

                discord_name = getattr(msg.author, "name", None) or f"User_{effective_id}"
                nickname = getattr(msg.author, "display_name", None)

                # Debug details about what will be saved
                logger.debug(
                    "save_user_memory inputs",
                    extra={"user_id": effective_id, "discord_name": discord_name, "nickname": nickname, "memory_length": len(memory_to_save)}
                )
    
                # Call the internal method from UserDataCog with correct parameter order:
                # (user_id: str, display_name: str, user_data: str, context)
                result_msg = await cog._save_user_data(
                    str(effective_id),
                    discord_name,
                    memory_to_save,
                    cast(
                        Union[discord.Interaction, discord.Message],
                        getattr(runtime, "message", None)
                    ),
                    nickname=nickname
                )

                # Invalidate ProceduralMemoryProvider cache so the next request
                # reflects the updated data without waiting for TTL expiry.
                await _invalidate_procedural_cache(effective_id)

                return result_msg
            except Exception as e:
                await func.report_error(
                    e, f"Failed to save personal memory for user_id={user_id}"
                )
                return f"An unexpected error occurred while saving memory: {e}"

        return [read_user_memory, save_user_memory, clear_user_memory]
