"""Music playback tools for LLM integration.

This module provides LangChain-compatible tools for interacting with the bot's music capabilities.
"""

from addons.logging import get_logger
from typing import Optional, TYPE_CHECKING
import discord
from langchain_core.tools import tool
from function import func

if TYPE_CHECKING:
    from llm.schema import OrchestratorRequest

_logger = get_logger(server_id="Bot", source="llm.tools.music")

class MusicTools:
    """Container class for music playback tools.

    This class holds the runtime context and provides factory methods
    for tools that control the YTMusic cog.
    """

    def __init__(self, runtime: "OrchestratorRequest"):
        self.runtime = runtime
        self.logger = getattr(self.runtime, "logger", _logger)

    def get_tools(self) -> list:
        runtime = self.runtime

        @tool
        async def play_music(query: str) -> str:
            """
            Plays music or adds it to the queue using YouTube or a URL.

            Call this tool when the user asks to play a song, start music, or add music to the queue.

            Args:
                query: The search query or URL of the song to play.
            """
            message = getattr(runtime, "message", None)
            if not message or not message.guild:
                return "Error: Cannot play music outside of a server."

            bot = getattr(runtime, "bot", None)
            if not bot:
                return "Error: Bot instance not found."

            music_cog = bot.get_cog("YTMusic")
            if not music_cog:
                return "Error: Music system is currently unavailable."

            try:
                if not message.author.voice:
                    return "Error: You must be in a voice channel to play music."

                dummy_interaction = await music_cog._create_dummy_interaction(message.channel, message.guild, message)

                if message.guild.voice_client is None:
                    try:
                        await message.author.voice.channel.connect()
                    except Exception as e:
                        return f"Error connecting to voice channel: {e}"

                # Process the query using internal methods similar to what the slash command does
                if "youtube.com" in query or "youtu.be" in query:
                    if "list" in query:
                        await music_cog._handle_playlist(dummy_interaction, query)
                    else:
                        await music_cog._handle_single_video(dummy_interaction, query)
                else:
                    # Normally _handle_search shows a UI with options for the slash command,
                    # but here the LLM can just trigger the search. However, to make it seamless without requiring button presses:
                    # Actually, the quickest way to enqueue without UI is to just take the top result.
                    results = await music_cog.youtube.search_videos(query)
                    if not results:
                        return f"No results found for '{query}'."

                    # For LLM, automatically picking the first result is usually best
                    # but _handle_search pops up a select menu, so it's better to fetch URL and play directly
                    top_url = results[0]['url']
                    await music_cog._handle_single_video(dummy_interaction, top_url)

                return f"Successfully processed request to play '{query}'."
            except Exception as e:
                await func.report_error(e, "play_music tool")
                return f"An error occurred while trying to play music: {e}"

        @tool
        async def skip_music() -> str:
            """
            Skips the currently playing song.

            Call this tool when the user asks to skip the song, next track, etc.
            """
            message = getattr(runtime, "message", None)
            if not message or not message.guild:
                return "Error: Cannot control music outside of a server."

            bot = getattr(runtime, "bot", None)
            if not bot:
                return "Error: Bot instance not found."

            music_cog = bot.get_cog("YTMusic")
            if not music_cog:
                return "Error: Music system is currently unavailable."

            try:
                dummy_interaction = await music_cog._create_dummy_interaction(message.channel, message.guild, message)
                await music_cog.handle_skip(dummy_interaction)
                return "Successfully skipped the current song."
            except Exception as e:
                return f"Error skipping music: {e}"

        @tool
        async def stop_music() -> str:
            """
            Stops the music playback and clears the queue.

            Call this tool when the user asks to stop the music, clear the queue, etc.
            """
            message = getattr(runtime, "message", None)
            if not message or not message.guild:
                return "Error: Cannot control music outside of a server."

            bot = getattr(runtime, "bot", None)
            if not bot:
                return "Error: Bot instance not found."

            music_cog = bot.get_cog("YTMusic")
            if not music_cog:
                return "Error: Music system is currently unavailable."

            try:
                dummy_interaction = await music_cog._create_dummy_interaction(message.channel, message.guild, message)
                await music_cog.handle_stop(dummy_interaction)
                return "Successfully stopped the music and cleared the queue."
            except Exception as e:
                return f"Error stopping music: {e}"

        @tool
        async def pause_or_resume_music() -> str:
            """
            Pauses or resumes the currently playing music.

            Call this tool when the user asks to pause or resume the music.
            """
            message = getattr(runtime, "message", None)
            if not message or not message.guild:
                return "Error: Cannot control music outside of a server."

            bot = getattr(runtime, "bot", None)
            if not bot:
                return "Error: Bot instance not found."

            music_cog = bot.get_cog("YTMusic")
            if not music_cog:
                return "Error: Music system is currently unavailable."

            try:
                dummy_interaction = await music_cog._create_dummy_interaction(message.channel, message.guild, message)
                await music_cog.handle_toggle_playback(dummy_interaction)
                return "Successfully toggled music playback state."
            except Exception as e:
                return f"Error toggling music playback: {e}"

        return [play_music, skip_music, stop_music, pause_or_resume_music]
