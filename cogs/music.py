import asyncio
import os
import time
import discord
from discord.ext import commands
from discord import app_commands
from addons.logging import get_logger
log = get_logger(source=__name__, server_id="system")
logger = log
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from addons.settings import music_config
from .music_lib.youtube import YouTubeManager
from .music_lib.audio_manager import AudioManager
from .music_lib.state_manager import StateManager
from .music_lib.queue_manager import QueueManager, PlayMode
from .music_lib.context import PlaybackContext, user_shares_voice_channel
from .music_lib.prefetch import Prefetcher
from .music_lib.recommender import TasteMemory
from .music_lib.taste_store import TasteStore
from .music_lib.music_store import MusicStore
from .music_lib.filters import get_preset
from .music_lib.lyrics import LyricsClient, synced_excerpt
from .music_lib.playlists import PlaylistService
from .music_lib.requests import RequestChannel
from .music_lib.service import HISTORY_SIZE, MusicService, classify_query
from .music_lib.ui_manager import UIManager
from .music_lib.ui.controls import remove_queue_field, set_queue_field
from .music_lib.ui.text import format_clock, shorten
from .music_lib.ui.song_select import SongSelectView
from cogs.language_manager import LanguageManager # Import LanguageManager
from function import func

# Playback attempts that may fail back-to-back before the player gives up.
MAX_CONSECUTIVE_FAILURES = 3
# How long a paused player may sit idle before the bot leaves the voice channel.
PAUSED_DISCONNECT_SECONDS = 300
# How long the bot waits in a voice channel nobody is in before it leaves and removes the panel.
EMPTY_CHANNEL_DISCONNECT_SECONDS = 60
# How long the "queue finished" message stays before the bot leaves the voice channel.
QUEUE_END_DISCONNECT_SECONDS = 10
# The lyrics field is edited every 2 seconds from a position that is up to a second old, and an
# edit takes a moment to arrive, so it shows the line due this many seconds ahead to avoid lagging.
LYRICS_DISPLAY_LEAD = 1.5

# Columns a song title may take in the queue list (full-width characters count twice), so a
# line with its length and requester still fits on one row of the player interface.
QUEUE_TITLE_WIDTH = 36
# Discord allows 25 options per menu and 100 characters per option label.
QUEUE_MENU_LIMIT = 25
QUEUE_MENU_LABEL_WIDTH = 90
# A stage topic may hold 120 characters (counted here as columns, which is stricter).
STAGE_TOPIC_WIDTH = 110


class PlaybackAbortedError(RuntimeError):
    """Raised when consecutive failures exhausted the retry budget."""


class YTMusic(commands.Cog):
    # Read by llm.self_knowledge so the bot can explain the player when asked.
    GUIDE_NOTES = (
        "The player message has buttons: ⏮️ previous, ⏯️ pause or resume, ⏭️ skip, ⏹️ stop, 🔄 loop mode, "
        "🔀 shuffle, 📜 show or hide the queue list, 🎶 autoplay (keeps adding recommended songs). "
        "With the queue list shown, two menus under it play a queued song next or remove one. "
        "Members must be in the bot's voice channel to control it. /play takes YouTube links or keywords, "
        "SoundCloud links and Spotify track links; with insert it plays next. "
        "In chat the bot can also play, skip, pause, queue and change the volume when asked."
    )

    def __init__(self, bot):
        self.bot = bot
        self.youtube = None  # Will be initialized in setup_hook
        self._executor = ThreadPoolExecutor(max_workers=3)
        self.settings = music_config
        
        # Initialize managers
        self.audio_manager = AudioManager()
        self.state_manager = bot.state_manager
        self.queue_manager = QueueManager(bot=bot)
        self.ui_manager = bot.ui_manager
        self.lang_manager: Optional[LanguageManager] = None # Initialize lang_manager
        self.disconnect_timers = {}
        # Background tasks that delete a finished song's file once its download completes.
        self._cleanup_tasks: set = set()
        # Monotonic clock used to measure how long a song has really played (replaced in tests).
        self._clock = time.monotonic
        # What each guild plays, requests and skips; guides autoplay recommendations.
        self._taste_store = TasteStore(music_config.autoplay.database_path)
        self._taste: Dict[int, TasteMemory] = {}
        # Each guild's music settings (DJ role, 24/7, ...) and the saved playlists.
        library = music_config.library
        self.store = MusicStore(
            library.database_path, max_playlists=library.max_playlists, max_tracks=library.max_playlist_tracks
        )
        self.service = MusicService(self, music_config.ai, music_config.streaming)
        self.lyrics = LyricsClient(music_config.lyrics)
        self.playlists = PlaylistService(self)
        self.requests = RequestChannel(self)
        self.prefetcher = Prefetcher(
            get_youtube=lambda: self.youtube,
            queue_manager=self.queue_manager,
            get_folder=lambda guild_id: self._get_guild_folder(guild_id)[1],
        )

    def taste_for(self, guild_id: int) -> TasteMemory:
        """Returns the taste memory of a guild, creating it on first use."""
        if guild_id not in self._taste:
            self._taste[guild_id] = TasteMemory(
                history_size=music_config.autoplay.history_size, store=self._taste_store, guild_id=guild_id
            )
        return self._taste[guild_id]

    async def setup_hook(self):
        """Initialize async components and LanguageManager."""
        self.youtube = await YouTubeManager.create()
        # Attempt early load; each command also lazy-loads if this returns None.
        self.lang_manager = self.bot.get_cog("LanguageManager")

    @app_commands.command(name="mode", description="設置播放模式 (不循環/清單循環/單曲循環)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="不循環", value="no_loop"),
        app_commands.Choice(name="清單循環", value="loop_queue"),
        app_commands.Choice(name="單曲循環", value="loop_single")
    ])
    async def mode(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        """播放模式命令"""
        guild_id = interaction.guild.id
        if not await self._ensure_can_control(interaction):
            return
        if not self.lang_manager: # Ensure lang_manager is loaded
             self.lang_manager = self.bot.get_cog("LanguageManager")
             if not self.lang_manager:
                 await interaction.response.send_message("Language manager not loaded.", ephemeral=True)
                 return
 
         # Localize choices (name is already localized by decorator, but value needs translation for response)
        mode_value = mode.value
        mode_name = self.lang_manager.translate(str(guild_id), "commands", "mode", "choices", mode_value)

        self.queue_manager.set_play_mode(guild_id, PlayMode(mode_value))

        title = self.lang_manager.translate(str(guild_id), "commands", "mode", "responses", "success", mode=mode_name)
        embed = discord.Embed(title=f"✅ | {title}", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        state = self.state_manager.get_state(interaction.guild.id)
        state.ui_messages.append(message)
        await self._refresh_player_buttons(guild_id)

    @app_commands.command(name="shuffle", description="切換隨機播放")
    async def shuffle(self, interaction: discord.Interaction):
        """隨機播放命令"""
        guild_id = interaction.guild.id
        if not await self._ensure_can_control(interaction):
            return
        if not self.lang_manager: # Ensure lang_manager is loaded
             self.lang_manager = self.bot.get_cog("LanguageManager")
             if not self.lang_manager:
                 await interaction.response.send_message("Language manager not loaded.", ephemeral=True)
                 return
 
        is_shuffle = self.queue_manager.toggle_shuffle(guild_id)
        status_key = "enabled" if is_shuffle else "disabled"
        status = self.lang_manager.translate(str(guild_id), "commands", "shuffle", "responses", status_key)
        title = self.lang_manager.translate(str(guild_id), "commands", "shuffle", "responses", "success", status=status)
        embed = discord.Embed(title=f"✅ | {title}", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        state = self.state_manager.get_state(interaction.guild.id)
        state.ui_messages.append(message)
        await self._refresh_player_buttons(guild_id)

    async def _refresh_player_buttons(self, guild_id: int) -> None:
        """Redraws the control buttons so the loop and shuffle states match the settings."""
        view = self.ui_manager.get_current_view(guild_id)
        if view:
            await view.update_button_state()

    async def _reply_service_result(self, interaction: discord.Interaction, result: Any, success_key: str, **format_args: Any) -> None:
        """Answer a slash command from a service result.

        Args:
            interaction: The command interaction (not answered yet).
            result: The ``ActionResult`` returned by the service.
            success_key: Translation key under ``commands.<name>.responses`` is chosen by the caller.
            **format_args: Values substituted into the success message.
        """
        guild_id = str(interaction.guild.id)
        if result.ok:
            title = self.lang_manager.translate(guild_id, "commands", *success_key.split("."), **format_args)
            embed = discord.Embed(title=f"✅ | {title}", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
            return
        if result.reason == "not_in_bot_channel":
            text = self.lang_manager.translate(guild_id, "system", "music", "controls", "not_in_channel")
        else:
            text = self.lang_manager.translate(guild_id, "system", "music", "ai_errors", result.reason, detail=result.detail)
        await interaction.response.send_message(embed=discord.Embed(title=f"❌ | {text}", color=discord.Color.red()), ephemeral=True)

    @app_commands.command(name="volume", description="調整音樂音量 (0-100)")
    @app_commands.describe(percent="音量百分比 (0-100)")
    async def volume(self, interaction: discord.Interaction, percent: app_commands.Range[int, 0, 100]):
        """音量命令"""
        if not self.lang_manager:
            self.lang_manager = self.bot.get_cog("LanguageManager")
        result = await self.service.set_volume(PlaybackContext.from_interaction(interaction), percent)
        await self._reply_service_result(interaction, result, "volume.responses.success", percent=percent)

    @app_commands.command(name="queue_remove", description="從待播清單移除一首歌")
    @app_commands.describe(position="歌曲在待播清單中的位置 (1 是下一首)")
    async def queue_remove(self, interaction: discord.Interaction, position: app_commands.Range[int, 1, 50]):
        """移除待播歌曲命令"""
        if not self.lang_manager:
            self.lang_manager = self.bot.get_cog("LanguageManager")
        result = await self.service.remove_from_queue(PlaybackContext.from_interaction(interaction), position)
        title = result.data.get("title", "") if result.ok else ""
        await self._reply_service_result(interaction, result, "queue_tools.responses.removed", title=title, position=position)

    @app_commands.command(name="queue_clear", description="清空待播清單 (目前播放的歌曲不受影響)")
    async def queue_clear(self, interaction: discord.Interaction):
        """清空待播清單命令"""
        if not self.lang_manager:
            self.lang_manager = self.bot.get_cog("LanguageManager")
        result = await self.service.clear_queue(PlaybackContext.from_interaction(interaction))
        count = result.data.get("removed", 0) if result.ok else 0
        await self._reply_service_result(interaction, result, "queue_tools.responses.cleared", count=count)

    @app_commands.command(name="play", description="播放影片(網址或關鍵字) 或 刷新UI")
    @app_commands.describe(query="影片網址或關鍵字（不填則刷新播放介面）", insert="插播：排到下一首播放")
    async def play(self, interaction: discord.Interaction, query: Optional[str] = None, insert: bool = False):
        """播放音樂或刷新UI命令"""
        guild_id = interaction.guild.id
        if not self.lang_manager: # Ensure lang_manager is loaded
            self.lang_manager = self.bot.get_cog("LanguageManager")
            if not self.lang_manager:
                await interaction.response.send_message("Language manager not loaded.", ephemeral=True)
                return

        # 檢查使用者是否已在語音頻道
        if not interaction.user.voice:
            title = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "no_voice_channel")
            embed = discord.Embed(title=f"❌ | {title}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # While music is playing (or paused) only people in the bot's channel may use /play.
        current_client = interaction.guild.voice_client
        if (current_client is not None and not self._is_idle(current_client)
                and not user_shares_voice_channel(interaction.user, current_client)):
            await interaction.response.send_message(
                self.lang_manager.translate(str(guild_id), "system", "music", "controls", "not_in_channel"),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        # 連接至語音頻道
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            try:
                await channel.connect()
            except Exception as e:
                await func.report_error(e, "music.py/play/channel.connect")
                title = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "voice_connect_failed")
                embed = discord.Embed(title=f"❌ | {title}", color=discord.Color.red())
                await interaction.edit_original_response(embed=embed)
                return
        elif interaction.guild.voice_client.channel != channel:
            # The bot is idle in another channel (busy was refused above): follow the requester.
            await interaction.guild.voice_client.move_to(channel)

        # 如果沒有提供查詢，刷新UI
        if not query:
            state = self.state_manager.get_state(guild_id)
            voice_client = interaction.guild.voice_client
            
            is_active = not self.queue_manager.get_queue(guild_id).empty() or (voice_client and voice_client.is_playing())

            if is_active:
                await self.ui_manager.update_player_ui(
                    interaction,
                    state.current_song,
                    state.current_message,
                    self.youtube,
                    self
                )
                refresh_message = self.lang_manager.translate(str(guild_id), "commands", "play", "responses", "refreshed_ui")
                await interaction.edit_original_response(content=refresh_message)
            else:
                no_song_message = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "nothing_playing")
                await interaction.edit_original_response(content=no_song_message)
            return

        # 如果有提供查詢，將音樂加入播放清單
        logger.info(f"[音樂] 伺服器 ID： {interaction.guild.name}, 使用者名稱： {interaction.user.name}, 使用者輸入： {query}")
        
        query, problem = await self.service.resolve_query(query)
        if problem:
            title = self.lang_manager.translate(str(interaction.guild.id), "commands", "play", "errors", "spotify_failed")
            embed = discord.Embed(title=f"❌ | {title}", color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)
            return

        query_kind = classify_query(query)
        if query_kind == "playlist":
            await self._handle_playlist(interaction, query.strip())
        elif query_kind == "video":
            is_valid = await self._handle_single_video(interaction, query.strip(), play_next=insert)
            if not is_valid:
                return
        else:
            await self._handle_search(interaction, query, play_next=insert)
            return
        
        # 播放音樂
        voice_client = interaction.guild.voice_client
        if self._is_idle(voice_client):
            await self.play_next(interaction)

    async def _handle_playlist(self, interaction: discord.Interaction, url: str):
        """Handle playlist URL"""
        guild_id = interaction.guild.id
        ctx = PlaybackContext.from_interaction(interaction)
        added_songs, total, failure = await self.service.enqueue_playlist(ctx, url)

        if failure:
            title = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "playlist_download_failed", error=failure.detail)
            embed = discord.Embed(title=f"❌ | {title}", color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)
            return

        description = "\n".join([f"🎵 {info['title']}" for info in added_songs])
        title = self.lang_manager.translate(str(guild_id), "commands", "play", "responses", "playlist_added", count=len(added_songs), total=total)
        embed = discord.Embed(
            title=f"✅ | {title}",
            description=description,
            color=discord.Color.blue()
        )
        await interaction.edit_original_response(embed=embed)

    async def _handle_single_video(self, interaction: discord.Interaction, url: str, play_next: bool = False) -> bool:
        """Handle single video URL"""
        guild_id_str = str(interaction.guild.id)
        video_info, failure = await self.service.enqueue_video(
            PlaybackContext.from_interaction(interaction), url, play_next
        )

        if failure and failure.reason == "queue_full":
            title = self.lang_manager.translate(guild_id_str, "commands", "play", "errors", "queue_full_title")
            desc = self.lang_manager.translate(guild_id_str, "commands", "play", "errors", "queue_full_desc")
            embed = discord.Embed(title=f"❌ | {title}", description=desc, color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)
            return False
        if failure:
            title = self.lang_manager.translate(guild_id_str, "commands", "play", "errors", "video_info_failed", error=failure.detail)
            embed = discord.Embed(title=f"❌ | {title}", color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)
            return False

        title = self.lang_manager.translate(guild_id_str, "commands", "play", "responses", "song_added", title=video_info['title'])
        embed = discord.Embed(title=f"✅ | {title}", color=discord.Color.blue())
        await interaction.edit_original_response(embed=embed)
        return True

    async def _handle_search(self, interaction: discord.Interaction, query: str, play_next: bool = False):
        """Handle search query"""
        results = await self.youtube.search_videos(query)
        guild_id = interaction.guild.id
        if not results:
            title = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "no_results")
            embed = discord.Embed(title=f"❌ | {title}", color=discord.Color.red())
            await interaction.edit_original_response(embed=embed)
            return
        
        # Format durations properly
        formatted_results = []
        for i, result in enumerate(results, 1):
            duration_secs = result.get('duration', 0)
            minutes, seconds = divmod(duration_secs, 60)
            duration_str = f"{int(minutes):02d}:{int(seconds):02d}"
            formatted_results.append(f"{i}. {result['title']} ({duration_str})")

        view = SongSelectView(self, results, interaction, play_next)
        desc_prefix = self.lang_manager.translate(str(guild_id), "commands", "play", "responses", "select_song")
        description = f"{desc_prefix}\n\n" + "\n".join(formatted_results)
        embed_title = self.lang_manager.translate(str(guild_id), "commands", "play", "responses", "search_results_title")
        embed = discord.Embed(
            title=f"🔍 | {embed_title}",
            description=description,
            color=discord.Color.blue()
        )
        
        await interaction.edit_original_response(embed=embed, view=view)

    async def play_next(self, source: Any, force_new: bool = False) -> None:
        """Play the next song in the queue.

        Failures are retried with the following song, but only up to
        ``MAX_CONSECUTIVE_FAILURES`` times in a row; after that playback stops
        and the channel is told, instead of grinding through the whole queue.

        Args:
            source: A ``PlaybackContext`` or the ``discord.Interaction`` it is built from.
            force_new: Whether to force playing a new song instead of looping.
        """
        ctx = PlaybackContext.coerce(source)
        guild_id = ctx.guild.id
        voice_client = ctx.guild.voice_client

        if not voice_client or not voice_client.is_connected():
            return

        state = self.state_manager.get_state(guild_id)
        play_mode = self.queue_manager.get_play_mode(guild_id)

        try:
            if not force_new and play_mode == PlayMode.LOOP_SINGLE and state.current_song:
                await self._handle_single_loop(ctx, state, voice_client)
                return

            next_song = await self._get_next_song(ctx, guild_id, force_new)
            if not next_song:
                await self._announce_queue_finished(ctx)
                return

            self.state_manager.update_state(guild_id, current_song=next_song)
            await self._play_song(ctx, next_song, voice_client)

        except PlaybackAbortedError:
            await self._abort_playback(ctx)
        except discord.errors.Forbidden:
            logger.error(f"[Music] Guild ID: {guild_id} - Forbidden error encountered. Stopping playback attempts to prevent infinite loop.")
            state.consecutive_failures = 0
        except Exception as e:
            await func.report_error(e, f"playing next song in guild {guild_id}")
            state.consecutive_failures += 1
            if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                await self._abort_playback(ctx)
                return
            await self.play_next(ctx, force_new=True)

    async def _send_channel_message(self, ctx: PlaybackContext, **kwargs: Any) -> Optional[discord.Message]:
        """Send a message to the player channel and track it for later cleanup.

        Args:
            ctx: The playback context holding the target channel.
            **kwargs: Arguments forwarded to ``channel.send``.

        Returns:
            The sent message, or ``None`` when it could not be delivered.
        """
        if ctx.channel is None:
            return None
        guild_id = ctx.guild.id
        try:
            message = await ctx.channel.send(**kwargs)
        except discord.errors.Forbidden:
            logger.warning(f"[Music] Guild ID: {guild_id} - Failed to send a channel message due to Forbidden (Missing Access).")
            return None
        except discord.HTTPException as send_err:
            logger.error(f"[Music] Guild ID: {guild_id} - Failed to send a channel message: {send_err}")
            return None
        self.state_manager.get_state(guild_id).ui_messages.append(message)
        return message

    async def _announce_queue_finished(self, ctx: PlaybackContext) -> None:
        """Tell the channel that the queue ran out and clear the current song."""
        guild_id = ctx.guild.id
        staying = self.store.get_settings(guild_id).stay_247
        title = self.lang_manager.translate(
            str(guild_id), "commands", "play", "responses", "queue_finished_staying" if staying else "queue_finished"
        )
        embed = discord.Embed(title=f"🌟 | {title}", color=discord.Color.blue())
        await self._send_channel_message(ctx, embed=embed)
        self.state_manager.update_state(guild_id, current_song=None, current_message=None, consecutive_failures=0)
        # The announcement promises a disconnect: keep it for a moment so it can be read, then
        # leave the channel and remove the messages. A new song cancels the timer.
        await self._start_disconnect_timer(guild_id, QUEUE_END_DISCONNECT_SECONDS)

    async def _abort_playback(self, ctx: PlaybackContext) -> None:
        """Give up after repeated failures: stop the player and tell the channel."""
        guild_id = ctx.guild.id
        logger.error(f"[Music] Guild ID: {guild_id} - Giving up after {MAX_CONSECUTIVE_FAILURES} consecutive playback failures.")
        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.is_connected() and voice_client.is_playing():
            voice_client.stop()
        self.state_manager.cancel_player_loop(guild_id)
        self.state_manager.update_state(guild_id, current_song=None, consecutive_failures=0)

        title = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "playback_failed_title")
        desc = self.lang_manager.translate(str(guild_id), "commands", "play", "errors", "playback_failed_desc")
        embed = discord.Embed(title=f"❌ | {title}", description=desc, color=discord.Color.red())
        await self._send_channel_message(ctx, embed=embed)

    async def _handle_single_loop(self, ctx: PlaybackContext, state: Any, voice_client: Any) -> None:
        """Handle single song loop playback"""
        try:
            if voice_client.is_playing():
                self.mark_user_stop(ctx.guild.id)
                voice_client.stop()

            song = state.current_song
            audio_source = self._make_source(ctx.guild.id, song)

            message = await self.ui_manager.update_player_ui(
                ctx,
                state.current_song,
                state.current_message,
                self.youtube,
                music_cog=self
            )
            self.state_manager.update_state(ctx.guild.id, current_message=message)

            voice_client.play(audio_source)
            self.state_manager.update_state(
                ctx.guild.id, user_stopped=False, force_next=False, position=0.0, skip_votes=set(), playback_ctx=ctx
            )
            self.state_manager.cancel_player_loop(ctx.guild.id)
            task = self.bot.loop.create_task(self._player_loop(ctx, song))
            self.state_manager.update_state(ctx.guild.id, player_loop_task=task)
        except Exception as e:
            await func.report_error(e, "handling single loop")
            state.consecutive_failures += 1
            if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                await self._abort_playback(ctx)
                return
            await self.play_next(ctx, force_new=True)

    async def _get_next_song(self, ctx: PlaybackContext, guild_id: int, force_new: bool) -> Optional[dict]:
        """Get the next playable song, skipping songs whose download fails.

        Raises:
            PlaybackAbortedError: If too many downloads failed back-to-back.
        """
        state = self.state_manager.get_state(guild_id)

        while True:
            # --- Autoplay Logic: Fill queue if empty ---
            if state.autoplay and self.queue_manager.is_queue_empty(guild_id):
                await self._trigger_autoplay(ctx, guild_id)

            # --- Queue Logic: Get next song ---
            next_song = await self.queue_manager.get_next_item(guild_id)

            # --- Loop Logic ---
            if not next_song and self.queue_manager.get_play_mode(guild_id) == PlayMode.LOOP_QUEUE:
                self.queue_manager.restart_cycle(guild_id)
                next_song = await self.queue_manager.get_next_item(guild_id)

            if not next_song:
                return None

            if next_song.get('is_live'):
                return next_song
            file_path = next_song.get('file_path')
            if file_path and await asyncio.to_thread(os.path.exists, file_path):
                return next_song
            if file_path:
                # The file is gone (an earlier copy of the same song deleted it): fetch it again.
                next_song['file_path'] = None
                next_song['stream_url'] = None
            elif next_song.get('stream_url'):
                return next_song

            # --- Download Logic: Ensure song is downloaded before playing ---
            _, folder = self._get_guild_folder(guild_id)
            potential_path = os.path.join(folder, f"{next_song.get('video_id')}.mp3")
            if await asyncio.to_thread(os.path.exists, potential_path):
                logger.info(f"歌曲 '{next_song['title']}' 已存在於本地，更新檔案路徑。")
                next_song['file_path'] = potential_path
                return next_song

            logger.info(f"歌曲 '{next_song['title']}' 未下載，開始下載（或等待預先下載完成）...")
            _, error = await self.prefetcher.ensure_downloaded(ctx, next_song)
            if not error:
                return next_song

            logger.error(f"下載失敗: {next_song['title']} - {error}")
            state.consecutive_failures += 1
            if state.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                raise PlaybackAbortedError(f"{state.consecutive_failures} consecutive download failures")

    async def _play_song(self, ctx: PlaybackContext, song: dict, voice_client: Any) -> None:
        """Play a song and update UI"""
        guild_id = ctx.guild.id
        await self._cancel_disconnect_timer(guild_id)
        if voice_client.is_playing():
            self.mark_user_stop(guild_id)
            voice_client.stop()

        # A file is preferred; otherwise the song plays from its stream and may need a resume.
        file_path = song.get('file_path')
        has_file = bool(file_path) and await asyncio.to_thread(os.path.exists, file_path)
        song['streaming'] = bool(song.get('stream_url')) and not has_file and not song.get('is_live')
        self._start_session(guild_id)
        audio_source = self._make_source(guild_id, song)
        message = await self.ui_manager.update_player_ui(
            ctx,
            song,
            self.state_manager.get_state(guild_id).current_message,
            self.youtube,
            music_cog=self
        )
        self.state_manager.update_state(
            guild_id, current_message=message, current_song=song, last_played_song=song, song_started_at=self._clock()
        )
        taste = self.taste_for(guild_id)
        if song.get('video_id'):
            taste.record_played(song['video_id'])
        if song.get('added_by') != self.bot.user.id and song.get('author'):
            taste.record_request(song['author'])

        voice_client.play(audio_source)
        song['resumes'] = 0
        self.state_manager.update_state(
            guild_id, consecutive_failures=0, user_stopped=False, force_next=False, auto_paused=False,
            position=0.0, skip_votes=set(), playback_ctx=ctx, lyrics=None,
        )
        self.prefetcher.schedule(ctx)
        if self.state_manager.get_state(guild_id).show_lyrics:
            self.bot.loop.create_task(self._show_lyrics_for_new_song(guild_id))
        if self.store.get_settings(guild_id).stage_announce:
            self.bot.loop.create_task(self._announce_on_stage(voice_client, song))
        if song.get('stream_url') and not song.get('file_path') and not song.get('is_live'):
            self.prefetcher.download_current(ctx, song)
        # Live streams are watched too, so the queue moves on when one ends or is skipped.
        self.state_manager.cancel_player_loop(guild_id)
        task = self.bot.loop.create_task(self._player_loop(ctx, song))
        self.state_manager.update_state(guild_id, player_loop_task=task)
        if not self._has_listeners(voice_client):
            # Everyone left while this song was being prepared: nobody would ever pause it.
            await self._handle_empty_channel(guild_id, voice_client)

    async def _handle_after_play(self, ctx: PlaybackContext, song: dict) -> None:
        """Handle cleanup and queue transitions after a song finishes playing.

        Args:
            ctx: The playback context.
            song: The song dictionary that just finished playing.
        """
        guild_id = ctx.guild.id

        try:
            state = self.state_manager.get_state(guild_id)
            current_song = state.current_song
            play_mode = self.queue_manager.get_play_mode(guild_id)
            self._record_history(state, song)

            # 只有在非循環且非直播的模式下才刪除檔案
            if play_mode not in [PlayMode.LOOP_SINGLE, PlayMode.LOOP_QUEUE] and not song.get('is_live'):
                file_path = song.get('file_path')
                still_needed = any(
                    queued.get('file_path') == file_path for queued in self.queue_manager.get_queue_snapshot(guild_id)
                )
                if file_path and still_needed:
                    logger.info(f"[音樂] 檔案 {file_path} 仍被佇列中的同一首歌使用，保留。")
                elif file_path:
                    await self.audio_manager.delete_file(guild_id, file_path)
                elif song.get('stream_url'):
                    self._delete_when_downloaded(guild_id, song)

            try:
                # Add more songs from playlist if needed
                queue = self.queue_manager.get_queue(guild_id)
                if queue.qsize() < 5 and self.queue_manager.has_playlist_songs(guild_id):
                    next_songs = await self.queue_manager.get_next_playlist_songs(
                        guild_id,
                        count=5 - queue.qsize()
                    )
                    for next_song_item in next_songs:
                        await self.queue_manager.add_to_queue(guild_id, next_song_item)

                    # Enforce autoplay limit after adding new songs
                    await self.queue_manager.enforce_autoplay_limit(guild_id)

                # Trigger autoplay if enabled and not enough songs in queue
                if state.autoplay:
                    await self._trigger_autoplay(ctx, guild_id)
            finally:
                # 如果是清單循環模式，將剛播放完的歌曲（包含檔案路徑）重新加入佇列。
                # This comes last so the song goes behind everything else: put back first into an
                # empty queue, it would be the next song and play again before the recommendations.
                # It runs even when filling the queue failed, so the song never drops out of the loop.
                if play_mode == PlayMode.LOOP_QUEUE and current_song:
                    if self.queue_manager.is_shuffle_enabled(guild_id):
                        # Shuffle plays every song once per round, so it waits for the next round.
                        self.queue_manager.finish_for_cycle(guild_id, current_song)
                    else:
                        await self.queue_manager.add_to_queue(guild_id, current_song, force=True)
                    logger.info(f"[音樂] 在清單循環模式下，'{current_song['title']}' 已播完，等待下一輪。")
        except Exception as e:
            # The queue housekeeping failed, but the listeners still want music:
            # report it and carry on with the next song.
            await func.report_error(e, "housekeeping after play")

        # A skip must leave a looped song; play_next handles its own failures and gives up
        # after a bounded number of retries.
        force_new = self.state_manager.get_state(guild_id).force_next
        self.state_manager.update_state(guild_id, force_next=False)
        await self.play_next(ctx, force_new=force_new)

    def _delete_when_downloaded(self, guild_id: int, song: dict) -> None:
        """Deletes a streamed song's file once its background download has finished.

        The song may end before the download does; deleting right away would find no file
        and leave it behind.
        """
        download = self.prefetcher.current_download(guild_id)
        if download is None or download.done():
            return
        task = asyncio.get_running_loop().create_task(self._remove_after(guild_id, song, download))
        self._cleanup_tasks.add(task)
        task.add_done_callback(self._cleanup_tasks.discard)

    async def _remove_after(self, guild_id: int, song: dict, download: asyncio.Task) -> None:
        """Waits for ``download`` to end and deletes the file it produced."""
        await asyncio.wait([download])
        file_path = song.get('file_path')
        if file_path:
            await self.audio_manager.delete_file(guild_id, file_path)

    async def _trigger_autoplay(self, ctx: PlaybackContext, guild_id: int, notify: bool = False) -> int:
        """根據最後播放的歌曲觸發自動播放，精確填充推薦歌曲至5首，並排除重複。

        Args:
            ctx: The playback context.
            guild_id: The guild to fill the queue for.
            notify: Whether to tell the channel how many songs were added.

        Returns:
            The number of recommended songs added to the queue.
        """
        state = self.state_manager.get_state(guild_id)

        queue_snapshot = self.queue_manager.get_queue_snapshot(guild_id)
        autoplay_song_count = sum(1 for s in queue_snapshot if s.get('added_by') == self.bot.user.id)

        needed = 5 - autoplay_song_count
        if needed <= 0:
            return 0

        logger.info(f"[音樂] Autoplay 已啟用，需要填充 {needed} 首推薦歌曲。")

        song_to_recommend_from = state.current_song or state.last_played_song
        if not song_to_recommend_from:
            logger.info("[音樂] 沒有可供推薦的歌曲。")
            return 0

        video_id = song_to_recommend_from.get("video_id")
        title = song_to_recommend_from.get("title")
        author = song_to_recommend_from.get("author")
        if not video_id or not title or not author:
            logger.warning("無法觸發自動播放，因為缺少 video_id、title 或 author。")
            return 0

        # 建立一個包含當前歌曲和佇列中所有歌曲ID的集合，以供排除
        taste = self.taste_for(guild_id)
        exclude_ids = {s.get('video_id') for s in queue_snapshot if s.get('video_id')} | taste.played_ids()
        if state.current_song and state.current_song.get('video_id'):
            exclude_ids.add(state.current_song.get('video_id'))

        related_videos, error = await self.youtube.get_related_videos(
            video_id, title, author, ctx, limit=needed, exclude_ids=exclude_ids, taste=taste
        )
        if error:
            logger.warning(f"無法獲取推薦影片: {error}")
            return 0
        if not related_videos:
            return 0

        logger.info(f"成功獲取 {len(related_videos)} 首推薦影片，正在加入佇列。")
        for video in related_videos:
            video['added_by'] = self.bot.user.id
            await self.queue_manager.add_to_queue(guild_id, video)
        await self.queue_manager.enforce_autoplay_limit(guild_id)

        if notify:
            text = self.lang_manager.translate(
                str(guild_id), "system", "music", "autoplay", "songs_added", count=len(related_videos)
            )
            await self._send_channel_message(
                ctx, embed=discord.Embed(title=f"🎶 | {text}", color=discord.Color.blue()), delete_after=15
            )
        return len(related_videos)

    def _make_source(self, guild_id: int, song: dict, start_offset: float = 0.0) -> Any:
        """Creates the audio source of ``song`` with the guild's volume and audio effect."""
        state = self.state_manager.get_state(guild_id)
        chain = get_preset(state.audio_filter).chain
        if chain:
            return self.audio_manager.create_audio_source(
                song, volume=state.volume, start_offset=start_offset, audio_filter=chain
            )
        return self.audio_manager.create_audio_source(song, volume=state.volume, start_offset=start_offset)

    def _start_session(self, guild_id: int) -> None:
        """Applies the server's default volume when a voice session plays its first song."""
        state = self.state_manager.get_state(guild_id)
        if state.session_started:
            return
        state.session_started = True
        state.volume = self.store.get_settings(guild_id).default_volume / 100

    async def _announce_on_stage(self, voice_client: Any, song: dict) -> None:
        """Sets a stage channel's topic to the song that starts (needs the stage moderator permission)."""
        channel = getattr(voice_client, "channel", None)
        if not isinstance(channel, discord.StageChannel):
            return
        topic = shorten(f"🎵 {song.get('title', '')}", STAGE_TOPIC_WIDTH)
        try:
            if channel.instance is not None:
                await channel.instance.edit(topic=topic)
            else:
                await channel.create_instance(topic=topic)
        except (discord.Forbidden, discord.HTTPException):
            logger.warning(f"[音樂] 伺服器 ID: {channel.guild.id}, 無法更新舞台主題（權限不足？）。")

    @staticmethod
    def _record_history(state: Any, song: dict) -> None:
        """Remembers a song that finished or was skipped (not one the previous button left)."""
        if state.going_back:
            state.going_back = False
            return
        if state.history and state.history[-1].get('video_id') == song.get('video_id'):
            return
        state.history.append(song)
        del state.history[:-HISTORY_SIZE]

    async def restart_current(self, guild_id: int, start_offset: float) -> bool:
        """Plays the current song again from ``start_offset`` seconds (seek, effect change).

        A paused song stays paused at the new position.

        Args:
            guild_id: The guild.
            start_offset: Where to start, in seconds of the song.

        Returns:
            Whether a song was restarted.
        """
        state = self.state_manager.get_state(guild_id)
        song = state.current_song
        ctx = state.playback_ctx
        voice_client = self.get_voice_client(guild_id)
        if not song or ctx is None or voice_client is None or not voice_client.is_connected():
            return False
        was_paused = voice_client.is_paused()
        self.state_manager.cancel_player_loop(guild_id)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        offset = 0.0 if song.get('is_live') else max(0.0, start_offset)
        voice_client.play(self._make_source(guild_id, song, start_offset=offset))
        if was_paused:
            voice_client.pause()
        self.state_manager.update_state(guild_id, position=offset, user_stopped=False)
        view = self.ui_manager.get_current_view(guild_id)
        if view and not song.get('is_live'):
            view.start_progress_updater(int(song.get('duration') or 0), start_position=int(offset))
        task = asyncio.get_running_loop().create_task(self._player_loop(ctx, song, offset))
        self.state_manager.update_state(guild_id, player_loop_task=task)
        return True

    def _get_guild_folder(self, guild_id: int) -> tuple:
        """Get guild queue and folder"""
        return self.queue_manager.get_guild_queue_and_folder(guild_id)

    # --- Callback Getters ---
    def get_queue_manager(self) -> QueueManager:
        return self.queue_manager

    def get_state_manager(self) -> StateManager:
        return self.state_manager

    def get_voice_client(self, guild_id: int) -> Optional[discord.VoiceClient]:
        guild = self.bot.get_guild(guild_id)
        return guild.voice_client if guild else None

    def get_lang_manager(self) -> Optional[LanguageManager]:
        return self.lang_manager

    async def _reply_control_denied(self, interaction: discord.Interaction, result: Any) -> None:
        """Tell the user why a control was refused (ephemeral).

        Args:
            interaction: The interaction that triggered the control.
            result: The failed ``ActionResult`` returned by the service.
        """
        guild_id = str(interaction.guild.id)
        if result.reason == "not_in_bot_channel":
            text = self.lang_manager.translate(guild_id, "system", "music", "controls", "not_in_channel")
        elif result.reason == "nothing_playing":
            text = self.lang_manager.translate(guild_id, "system", "music", "controls", "no_music")
        else:
            text = self.lang_manager.translate(guild_id, "system", "music", "ai_errors", result.reason, detail=result.detail)
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    async def _ensure_can_control(self, interaction: discord.Interaction) -> bool:
        """Check that the user may change playback (shares the bot's channel, is a DJ).

        Without a voice client there is nothing to protect from listeners, so the
        handler's own "nothing is playing" reply applies; the DJ rule still holds.

        Args:
            interaction: The interaction that triggered the control.

        Returns:
            ``True`` when the control may proceed; otherwise an ephemeral
            explanation has been sent and ``False`` is returned.
        """
        denied = self.service.check_control(PlaybackContext.from_interaction(interaction), require_connection=False)
        if denied is None:
            return True
        await self._reply_menu_failure(interaction, denied)
        return False

    # --- Callback Handlers ---
    async def handle_previous(self, interaction: discord.Interaction):
        """Goes back to the previous song (or starts the current one over)."""
        guild_id = interaction.guild.id
        result = await self.service.previous(PlaybackContext.from_interaction(interaction))
        if not result.ok:
            await self._reply_menu_failure(interaction, result)
            return
        view = self.ui_manager.get_current_view(guild_id)
        if view:
            key = "replayed" if result.data.get("replayed") else "previous"
            await view.update_embed(
                interaction,
                self.lang_manager.translate(str(guild_id), "system", "music", "controls", key, user=interaction.user.display_name)
            )

    async def handle_seek_step(self, interaction: discord.Interaction, seconds: int):
        """Rewinds (negative) or fast-forwards the current song from the player's buttons."""
        guild_id = interaction.guild.id
        result = await self.service.seek(PlaybackContext.from_interaction(interaction), seconds, relative=True)
        if not result.ok:
            await self._reply_menu_failure(interaction, result)
            return
        view = self.ui_manager.get_current_view(guild_id)
        if view:
            key = "rewound" if seconds < 0 else "forwarded"
            await view.update_embed(interaction, self.lang_manager.translate(
                str(guild_id), "system", "music", "controls", key,
                user=interaction.user.display_name, seconds=abs(seconds), position=format_clock(result.data["position"]),
            ))

    async def handle_toggle_playback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)
        view = self.ui_manager.get_current_view(guild_id)
        if not voice_client or not view:
            return

        ctx = PlaybackContext.from_interaction(interaction)
        if voice_client.is_playing():
            result = await self.service.pause(ctx, refresh_buttons=False)
            message_key = "paused"
        elif voice_client.is_paused():
            result = await self.service.resume(ctx, refresh_buttons=False)
            message_key = "resumed"
        else:
            return

        if not result.ok:
            await self._reply_control_denied(interaction, result)
            return
        await view.update_embed(interaction, self.lang_manager.translate(str(guild_id), "system", "music", "controls", message_key, user=interaction.user.name))
        await view.update_button_state()

    async def handle_skip(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)
        if not voice_client:
            await interaction.response.send_message(self.lang_manager.translate(str(guild_id), "system", "music", "controls", "no_music"), ephemeral=True)
            return

        result = await self.service.skip(PlaybackContext.from_interaction(interaction), refresh_buttons=False)
        if not result.ok:
            await self._reply_control_denied(interaction, result)
            return

        view = self.ui_manager.get_current_view(guild_id)
        if result.data.get("voted"):
            if view:
                await view.update_embed(interaction, self.lang_manager.translate(
                    str(guild_id), "system", "music", "controls", "skip_voted",
                    user=interaction.user.display_name, votes=result.data["votes"], required=result.data["required"],
                ))
            return
        if view:
            await view.update_embed(interaction, self.lang_manager.translate(str(guild_id), "system", "music", "controls", "skipped", user=interaction.user.name))
            await view.update_button_state()

    async def handle_stop(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)

        if not voice_client:
            await interaction.response.send_message(self.lang_manager.translate(str(guild_id), "system", "music", "controls", "no_music"), ephemeral=True)
            return

        result = await self.service.stop(PlaybackContext.from_interaction(interaction))
        if not result.ok:
            await self._reply_control_denied(interaction, result)
            return

        # Send a final confirmation message
        stopped_text = self.lang_manager.translate(str(guild_id), "system", "music", "controls", "stopped", user=interaction.user.name)
        embed = discord.Embed(title=f"{stopped_text}", color=discord.Color.red())

        # Check if the interaction is already responded to
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def handle_set_mode(self, interaction: discord.Interaction, mode: str):
        """Sets the loop mode chosen in the player's menu."""
        guild_id = interaction.guild.id
        result = await self.service.set_mode(PlaybackContext.from_interaction(interaction), mode)
        view = self.ui_manager.get_current_view(guild_id)
        if not result.ok:
            await self._reply_menu_failure(interaction, result)
            if view:
                # Put the menu back on the mode that is really in effect.
                await view.update_button_state()
            return
        mode_name = self.lang_manager.translate(str(guild_id), "commands", "mode", "choices", mode)
        if view:
            await view.update_embed(interaction, self.lang_manager.translate(
                str(guild_id), "system", "music", "controls", "mode_changed", user=interaction.user.display_name, mode=mode_name
            ))

    async def handle_set_filter(self, interaction: discord.Interaction, name: str):
        """Applies the audio effect chosen in the player's menu."""
        guild_id = interaction.guild.id
        if not interaction.response.is_done():
            await interaction.response.defer()
        result = await self.service.set_filter(PlaybackContext.from_interaction(interaction), name)
        view = self.ui_manager.get_current_view(guild_id)
        if not result.ok:
            await self._reply_menu_failure(interaction, result)
            if view:
                await view.update_button_state()
            return
        effect = self.lang_manager.translate(str(guild_id), "system", "music", "filters", name)
        if view:
            await view.update_embed(interaction, self.lang_manager.translate(
                str(guild_id), "system", "music", "controls", "filter_changed", user=interaction.user.display_name, effect=effect
            ))

    async def handle_toggle_lyrics(self, interaction: discord.Interaction):
        """Shows or hides the synced lyrics on the player (a switch, like the queue button)."""
        guild_id = interaction.guild.id
        denied = self.service.check_control(PlaybackContext.from_interaction(interaction), permission="listener")
        if denied:
            await self._reply_menu_failure(interaction, denied)
            return
        view = self.ui_manager.get_current_view(guild_id)
        state = self.state_manager.get_state(guild_id)
        state.show_lyrics = not state.show_lyrics
        if not interaction.response.is_done():
            await interaction.response.defer()
        if state.show_lyrics:
            await self.current_lyrics(guild_id)
        if view:
            self.refresh_lyrics_field(view)
            await view.update_embed(interaction, view.current_embed.title if view.current_embed else "", view.current_embed.color if view.current_embed else discord.Color.blue())
            await view.update_button_state()

    async def current_lyrics(self, guild_id: int) -> Optional[Any]:
        """Returns the lyrics of the song that is playing, looking them up once per song."""
        state = self.state_manager.get_state(guild_id)
        song = state.current_song
        if not song or not music_config.lyrics.enabled:
            return None
        if state.lyrics and state.lyrics[0] == song.get('video_id'):
            return state.lyrics[1]
        found = await self.lyrics.for_song(song)
        current = state.current_song
        if current and current.get('video_id') == song.get('video_id'):
            state.lyrics = (song.get('video_id'), found)
        return found

    def refresh_lyrics_field(self, view: Any) -> bool:
        """Puts the lines around the current position on the player (or removes the field).

        Returns:
            Whether the lyrics are shown.
        """
        embed = getattr(view, "current_embed", None)
        if embed is None:
            return False
        guild_id = view.guild.id
        guild_id_str = str(guild_id)
        state = self.state_manager.get_state(guild_id)
        name = self.lang_manager.translate(guild_id_str, "system", "music", "player", "lyrics")
        song = state.current_song
        if not state.show_lyrics or not song:
            remove_queue_field(embed, name)
            return False
        lyrics = state.lyrics[1] if state.lyrics and state.lyrics[0] == song.get('video_id') else None
        if state.lyrics is None or state.lyrics[0] != song.get('video_id'):
            text = self.lang_manager.translate(guild_id_str, "system", "music", "lyrics", "loading")
        elif lyrics is None:
            text = self.lang_manager.translate(guild_id_str, "system", "music", "lyrics", "not_found")
        elif not lyrics.synced:
            text = self.lang_manager.translate(guild_id_str, "system", "music", "lyrics", "not_synced")
        else:
            text = synced_excerpt(lyrics, state.position + LYRICS_DISPLAY_LEAD)
        set_queue_field(embed, name, text)
        return True

    async def _show_lyrics_for_new_song(self, guild_id: int) -> None:
        """Looks up the new song's lyrics while the synced lyrics are switched on."""
        try:
            await self.current_lyrics(guild_id)
            view = self.ui_manager.get_current_view(guild_id)
            if view and view.message and view.current_embed and self.refresh_lyrics_field(view):
                await view.message.edit(embed=view.current_embed, view=view)
        except discord.HTTPException:
            pass
        except Exception as e:
            await func.report_error(e, "loading lyrics for the player")

    async def handle_toggle_shuffle(self, interaction: discord.Interaction):
        if not await self._ensure_can_control(interaction):
            return
        guild_id = interaction.guild.id
        is_shuffle = self.queue_manager.toggle_shuffle(guild_id)
        status_key = "enabled" if is_shuffle else "disabled"
        status = self.lang_manager.translate(str(guild_id), "commands", "shuffle", "responses", status_key)
        
        view = self.ui_manager.get_current_view(guild_id)
        if view:
            await view.update_button_state()
            await view.update_embed(interaction, self.lang_manager.translate(str(guild_id), "system", "music", "controls", "shuffle_toggled", user=interaction.user.name, status=status))

    async def handle_show_queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        view = self.ui_manager.get_current_view(guild_id)
        if not view or not view.current_embed:
            await interaction.response.send_message(self.lang_manager.translate(str(guild_id), "system", "music", "controls", "update_failed"), ephemeral=True)
            return

        state = self.state_manager.get_state(guild_id)
        state.show_queue = not state.show_queue
        queue_name = self.lang_manager.translate(str(guild_id), "system", "music", "player", "queue")
        if state.show_queue:
            set_queue_field(view.current_embed, queue_name, await self.get_queue_text(guild_id))
        else:
            remove_queue_field(view.current_embed, queue_name)
        await view.update_embed(interaction, view.current_embed.title, view.current_embed.color)
        await view.update_button_state()

    async def handle_toggle_autoplay(self, interaction: discord.Interaction):
        """切換自動播放模式"""
        if not await self._ensure_can_control(interaction):
            return
        guild_id = interaction.guild.id
        state = self.state_manager.get_state(guild_id)
        state.autoplay = not state.autoplay
        self.state_manager.update_state(guild_id, autoplay=state.autoplay)
        logger.info(f"[音樂] 伺服器 ID: {interaction.guild.id}, Autoplay 狀態切換為: {state.autoplay}")

        view = self.ui_manager.get_current_view(guild_id)
        if view:
            await view.update_button_state()

        status_key = "enabled" if state.autoplay else "disabled"
        status_str = self.lang_manager.translate(str(guild_id), "system", "music", "autoplay", status_key)
        
        title = self.lang_manager.translate(str(guild_id), "system", "music", "autoplay", "toggled", user=interaction.user.name, status=status_str)
        
        await interaction.response.send_message(f"✅ | {title}", ephemeral=True)

        if not state.autoplay:
            return

        self.start_autoplay_if_needed(PlaybackContext.from_interaction(interaction), guild_id)

    def start_autoplay_if_needed(self, ctx: PlaybackContext, guild_id: int) -> None:
        """Gets recommendations going right after autoplay was switched on.

        Args:
            ctx: The playback context.
            guild_id: The guild.
        """
        voice_client = ctx.guild.voice_client
        if voice_client and self._is_idle(voice_client):
            # Nothing playing: play_next fills the empty queue through autoplay itself.
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 觸發閒置時的 Autoplay。")
            self.bot.loop.create_task(self.play_next(ctx))
        elif self.queue_manager.is_queue_empty(guild_id):
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, Autoplay 已啟用且待播清單為空，立即觸發推薦填充。")
            self.bot.loop.create_task(self._trigger_autoplay(ctx, guild_id, notify=True))

    def _requester_label(self, guild_id_str: str, item: Dict[str, Any]) -> str:
        """Names who queued a song: the requester, or "recommended" for the bot's own picks.

        Args:
            guild_id_str: The guild (for the language).
            item: The queue entry.

        Returns:
            The label, or an empty string when the requester is unknown.
        """
        if item.get("added_by") == self.bot.user.id:
            return self.lang_manager.translate(guild_id_str, "system", "music", "controls", "recommended")
        requester = item.get("requester")
        return str(getattr(requester, "display_name", None) or getattr(requester, "name", None) or "")

    def queue_menu_options(self, guild_id: int) -> List[discord.SelectOption]:
        """Builds the player menus' options: the first 25 queued songs, in order.

        Args:
            guild_id: The guild.

        Returns:
            One option per song (value: its video ID), empty when the queue is.
        """
        guild_id_str = str(guild_id)
        options: List[discord.SelectOption] = []
        seen = set()
        for i, item in enumerate(self.queue_manager.get_queue_snapshot(guild_id)[:QUEUE_MENU_LIMIT], 1):
            video_id = item.get("video_id")
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            minutes, seconds = divmod(float(item.get("duration", 0)), 60)
            requester = self._requester_label(guild_id_str, item)
            description = f"{int(minutes):02d}:{int(seconds):02d}" + (f" · {requester}" if requester else "")
            options.append(discord.SelectOption(
                label=shorten(f"{i}. {item['title']}", QUEUE_MENU_LABEL_WIDTH),
                value=video_id,
                description=shorten(description, QUEUE_MENU_LABEL_WIDTH),
            ))
        return options

    async def handle_queue_select(self, interaction: discord.Interaction, action: str, video_id: str) -> None:
        """Plays the chosen queued song next, or removes it, from the player's menus.

        Args:
            interaction: The menu interaction.
            action: ``"play_next"`` or ``"remove"``.
            video_id: The chosen song.
        """
        guild_id = interaction.guild.id
        ctx = PlaybackContext.from_interaction(interaction)
        if action == "play_next":
            result = await self.service.play_queued_next(ctx, video_id)
            message_key = "queue_played_next"
        else:
            result = await self.service.remove_queued(ctx, video_id)
            message_key = "queue_removed"
        if not result.ok:
            await self._reply_menu_failure(interaction, result)
            return

        view = self.ui_manager.get_current_view(guild_id)
        if view:
            await view.refresh_queue_field()
            title = self.lang_manager.translate(
                str(guild_id), "system", "music", "controls", message_key,
                user=interaction.user.display_name, title=shorten(result.data["title"], QUEUE_TITLE_WIDTH),
            )
            await view.update_embed(interaction, title)
            await view.update_button_state()

    async def _reply_menu_failure(self, interaction: discord.Interaction, result: Any) -> None:
        """Tells the user (only them) why a queue menu action did nothing."""
        guild_id = str(interaction.guild.id)
        if result.reason == "not_in_bot_channel":
            text = self.lang_manager.translate(guild_id, "system", "music", "controls", "not_in_channel")
        else:
            text = self.lang_manager.translate(guild_id, "system", "music", "ai_errors", result.reason, detail=result.detail)
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    async def get_queue_text(self, guild_id: int) -> str:
        """Generates the text for the queue display.

        The song that is playing is not listed: the player interface already shows it.

        Args:
            guild_id: The guild.

        Returns:
            The number of queued songs and one line per song (title, length, requester).
        """
        guild_id_str = str(guild_id)
        queue_items = self.queue_manager.get_queue_snapshot(guild_id)
        if not queue_items:
            return self.lang_manager.translate(guild_id_str, "system", "music", "player", "queue_empty")

        total = self.lang_manager.translate(
            guild_id_str, "system", "music", "controls", "queue_total", count=len(queue_items)
        )
        text = f"{total}\n"
        for i, item in enumerate(queue_items, 1):
            minutes, seconds = divmod(float(item.get("duration", 0)), 60)
            requester = self._requester_label(guild_id_str, item)
            suffix = f" · {requester}" if requester else ""
            line = f"{i}. {shorten(item['title'], QUEUE_TITLE_WIDTH)} | {int(minutes):02d}:{int(seconds):02d}{suffix}\n"

            # Check if adding the current line exceeds embed field limit (1024 chars).
            # Keep a 100 character buffer for the "more songs" localized suffix.
            if len(text) + len(line) + 100 > 1024:
                remaining_count = len(queue_items) - i + 1
                text += self.lang_manager.translate(
                    guild_id_str, "system", "music", "player", "more_songs", count=remaining_count
                )
                break

            text += line

        return text

    async def _cleanup_voice_session(self, guild_id: int):
        """Cleans up the voice session for a guild."""
        voice_client = self.get_voice_client(guild_id)
        state = self.state_manager.get_state(guild_id)

        # Stop playback and disconnect
        if voice_client:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
            if voice_client.is_connected():
                await voice_client.disconnect()

        # Clean up all UI messages. The progress updater re-posts the panel every few minutes and
        # only the view knows the newest copy, so it is deleted too.
        panels = list(state.ui_messages)
        view = self.ui_manager.get_current_view(guild_id)
        live_panel = getattr(view, "message", None)
        if live_panel is not None and all(live_panel is not message for message in panels):
            panels.append(live_panel)
        for message in panels:
            try:
                await message.delete()
            except (discord.errors.NotFound, discord.errors.Forbidden):
                pass
        
        # Clean up the view
        await self.ui_manager.cleanup_view(guild_id)

        # Cancel any running player loop and clear queue and state
        self.state_manager.cancel_player_loop(guild_id)
        await self.prefetcher.cancel(guild_id)
        self.queue_manager.clear_queue(guild_id)
        self.queue_manager.set_playlist(guild_id, [])
        _, folder = self._get_guild_folder(guild_id)
        await self.audio_manager.cleanup_guild_files(guild_id, folder)
        self.state_manager.update_state(
            guild_id, current_song=None, last_played_song=None, current_message=None, current_view=None, ui_messages=[],
            history=[], going_back=False, skip_votes=set(), position=0.0, playback_ctx=None, audio_filter="off",
            lyrics=None, session_started=False,
        )
        logger.info(f"[音樂] 伺服器 ID: {guild_id}, 已清理語音會話。")

    async def _cancel_disconnect_timer(self, guild_id: int):
        """Cancels the disconnect timer for a guild."""
        if guild_id in self.disconnect_timers:
            self.disconnect_timers[guild_id].cancel()
            del self.disconnect_timers[guild_id]
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 已取消閒置斷線計時器。")

    async def _start_disconnect_timer(self, guild_id: int, delay: float = PAUSED_DISCONNECT_SECONDS):
        """Starts the idle-disconnect timer for a guild.

        Args:
            guild_id: The guild to disconnect from.
            delay: Seconds to wait before disconnecting.
        """
        await self._cancel_disconnect_timer(guild_id) # Cancel any existing timer
        if self.store.get_settings(guild_id).stay_247:
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 24/7 模式開啟，不啟動閒置斷線計時器。")
            return

        logger.info(f"[音樂] 伺服器 ID: {guild_id}, 啟動 {delay:g} 秒閒置斷線計時器。")
        self.disconnect_timers[guild_id] = asyncio.get_running_loop().create_task(
            self._disconnect_after_delay(guild_id, delay)
        )

    async def _disconnect_after_delay(self, guild_id: int, delay: float = PAUSED_DISCONNECT_SECONDS):
        """Disconnects the bot after ``delay`` seconds unless a song is playing again.

        Args:
            guild_id: The guild to disconnect from.
            delay: Seconds to wait before checking.
        """
        await asyncio.sleep(delay)

        voice_client = self.get_voice_client(guild_id)
        nobody_listening = voice_client is not None and not self._has_listeners(voice_client)
        if voice_client and voice_client.is_connected() and (not voice_client.is_playing() or nobody_listening):
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 閒置超過 {delay:g} 秒，自動斷線。")
            # Leaving the channel triggers on_voice_state_update, which cancels the guild's timer;
            # unregister first so that does not cancel this running task mid-cleanup.
            if self.disconnect_timers.get(guild_id) is asyncio.current_task():
                del self.disconnect_timers[guild_id]

            # Find a channel to send the message
            state = self.state_manager.get_state(guild_id)
            channel = None
            if state.current_message:
                channel = state.current_message.channel
            
            await self._cleanup_voice_session(guild_id)
            
            if channel:
                idle_disconnect_msg = self.lang_manager.translate(str(guild_id), "system", "music", "status", "idle_disconnect")
                embed = discord.Embed(title=f"😴 | {idle_disconnect_msg}", color=discord.Color.orange())
                try:
                    await channel.send(embed=embed, delete_after=60)
                except discord.errors.Forbidden:
                    logger.warning(f"[音樂] 伺服器 ID: {guild_id}, 無法發送閒置斷線訊息（權限不足）。")
        else:
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 閒置斷線計時器觸發，但機器人已非暫停狀態，取消操作。")

        # Clean up the timer task from the dictionary
        if guild_id in self.disconnect_timers:
            del self.disconnect_timers[guild_id]

    async def stay_in(self, guild: Any, channel: Any) -> bool:
        """Joins (or moves to, when idle) the 24/7 channel and stops any idle-disconnect timer.

        Returns:
            Whether the bot is now in a voice channel of the guild.
        """
        voice_client = guild.voice_client
        try:
            if voice_client is None:
                await channel.connect()
            elif voice_client.channel != channel and self._is_idle(voice_client):
                await voice_client.move_to(channel)
        except (discord.ClientException, discord.HTTPException, asyncio.TimeoutError):
            logger.error(f"[音樂] 伺服器 ID: {guild.id}, 無法加入 24/7 頻道。", exc_info=True)
            return False
        await self._cancel_disconnect_timer(guild.id)
        return guild.voice_client is not None

    async def leave_if_idle(self, guild_id: int) -> None:
        """Starts the usual idle disconnect after 24/7 was turned off, if nothing is going on."""
        voice_client = self.get_voice_client(guild_id)
        if voice_client is None or not voice_client.is_connected():
            return
        if self._is_idle(voice_client) and self.queue_manager.is_queue_empty(guild_id):
            await self._start_disconnect_timer(guild_id, QUEUE_END_DISCONNECT_SECONDS)
        elif voice_client.is_paused() or not self._has_listeners(voice_client):
            await self._start_disconnect_timer(
                guild_id, PAUSED_DISCONNECT_SECONDS if self._has_listeners(voice_client) else EMPTY_CHANNEL_DISCONNECT_SECONDS
            )

    @commands.Cog.listener()
    async def on_ready(self):
        """Rejoins the 24/7 voice channels after a restart."""
        for guild_id, channel_id in self.store.guilds_staying().items():
            guild = self.bot.get_guild(guild_id)
            channel = guild.get_channel(channel_id) if guild else None
            if channel is None or guild.voice_client is not None:
                continue
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 24/7 模式：重新加入語音頻道。")
            await self.stay_in(guild, channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes, including auto-pause and auto-disconnect."""
        # Ignore bot's own state changes unless it's a disconnect
        if member.id == self.bot.user.id:
            if before.channel is not None and after.channel is None:
                # Bot was disconnected
                guild_id = member.guild.id
                # If discord.py still has a voice_client, it's internally retrying — don't clean up yet
                if member.guild.voice_client is not None:
                    return
                logger.info(f"[音樂] 偵測到機器人被動斷線於伺服器 {member.guild.name}。")
                await self._cancel_disconnect_timer(guild_id)
                await self._cleanup_voice_session(guild_id)
            return

        # Check the voice channel the bot is in
        voice_client = member.guild.voice_client
        if not voice_client or not voice_client.channel:
            return

        # Check if the state change happened in the bot's channel
        if before.channel == voice_client.channel or after.channel == voice_client.channel:
            # Get the number of human members in the channel
            human_members = [m for m in voice_client.channel.members if not m.bot]
            
            if not human_members:
                await self._handle_empty_channel(member.guild.id, voice_client)

            else:
                # Someone is in the channel, resume if paused
                if voice_client.is_paused():
                    # Only resume a pause the bot made itself; a user's pause stays.
                    if self.state_manager.get_state(member.guild.id).auto_paused:
                        logger.info(f"[音樂] 伺服器 ID: {member.guild.id}, 有使用者加入，自動恢復播放。")
                        voice_client.resume()
                        self.state_manager.update_state(member.guild.id, auto_paused=False)
                        await self._cancel_disconnect_timer(member.guild.id)

                        view = self.ui_manager.get_current_view(member.guild.id)
                        if view:
                            await view.update_button_state()

    @staticmethod
    def _has_listeners(voice_client: Any) -> bool:
        """Tells whether any human is in the voice channel the bot is in."""
        channel = getattr(voice_client, "channel", None)
        return any(not member.bot for member in getattr(channel, "members", []))

    async def _handle_empty_channel(self, guild_id: int, voice_client: Any) -> None:
        """Makes the bot leave a voice channel nobody is in.

        A playing song is paused (and resumes if someone comes back). Whatever the player
        is doing - playing, paused by a user, or between two songs - a disconnect timer
        runs, unless one that will fire sooner is already running.

        Args:
            guild_id: The guild.
            voice_client: The bot's voice client in that guild.
        """
        if voice_client.is_playing():
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 頻道內無人，自動暫停播放。")
            voice_client.pause()
            self.state_manager.update_state(guild_id, auto_paused=True)
            # Update UI button state (progress updater handles paused state on its own)
            view = self.ui_manager.get_current_view(guild_id)
            if view:
                await view.update_button_state()
        timer = self.disconnect_timers.get(guild_id)
        if timer is None or timer.done():
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 頻道內無人，{EMPTY_CHANNEL_DISCONNECT_SECONDS} 秒後離開。")
            await self._start_disconnect_timer(guild_id, EMPTY_CHANNEL_DISCONNECT_SECONDS)

    @staticmethod
    def _is_idle(voice_client: Any) -> bool:
        """Tells whether nothing is playing *and* nothing is paused.

        A paused song is still the current one; starting another would replace it and
        leave the paused audio thread running.
        """
        return not (voice_client.is_playing() or voice_client.is_paused())

    def mark_user_stop(self, guild_id: int) -> None:
        """Records that playback is being stopped on purpose (skip, previous, replacement)."""
        self.state_manager.update_state(guild_id, user_stopped=True)

    async def _player_loop(self, ctx: PlaybackContext, song: dict, start_offset: float = 0.0) -> None:
        """Monitors the player and handles song completion.

        Args:
            ctx: The playback context.
            song: The song being played.
            start_offset: Seconds of the song that were already played before this loop
                started (non-zero after a resume).
        """
        guild_id = ctx.guild.id
        logger.info(f"[{guild_id}] Player loop started for '{song['title']}'.")

        played = float(start_offset)
        state = self.state_manager.get_state(guild_id)
        state.position = played
        # A sped-up or slowed-down effect plays more or less than a second of the song per second.
        speed = get_preset(state.audio_filter).speed
        last_tick = self._clock()
        await asyncio.sleep(2)  # Wait for playback to start

        while True:
            voice_client = self.get_voice_client(guild_id)
            if not voice_client or not voice_client.is_connected():
                logger.warning(f"[{guild_id}] Player loop exiting: voice client disconnected.")
                return

            now = self._clock()
            if voice_client.is_paused():
                last_tick = now
                await asyncio.sleep(1)
                continue

            if not voice_client.is_playing():
                logger.info(f"[{guild_id}] Player loop detected song has finished.")
                break

            played += (now - last_tick) * speed
            last_tick = now
            state.position = played
            await asyncio.sleep(1)

        state = self.state_manager.get_state(guild_id)
        # Ensure we are still on the same song before triggering after_play
        if state.current_song and state.current_song['video_id'] == song['video_id']:
            if await self._resume_dropped_stream(ctx, song, played):
                return
            logger.info(f"[{guild_id}] 歌曲 '{song['title']}' 播放完畢，觸發 _handle_after_play。")
            await self._handle_after_play(ctx, song)
        else:
            logger.info(f"[{guild_id}] Player loop for '{song['title']}' exiting without action. (Song might have been skipped).")

    async def _resume_dropped_stream(self, ctx: PlaybackContext, song: dict, played: float) -> bool:
        """Continues a streamed song from its downloaded file when the stream ended early.

        Args:
            ctx: The playback context.
            song: The song whose player loop saw playback end.
            played: Seconds of the song that were played so far.

        Returns:
            True when playback was resumed (a new player loop owns the song now); False
            when the song really ended, was stopped on purpose, or cannot be resumed.
        """
        guild_id = ctx.guild.id
        state = self.state_manager.get_state(guild_id)
        stopped_on_purpose = state.user_stopped
        self.state_manager.update_state(guild_id, user_stopped=False)

        settings = self.service.streaming
        duration = song.get('duration') or 0
        if stopped_on_purpose or not settings.enabled or not song.get('streaming'):
            return False
        if duration <= 0 or played + settings.drop_tolerance_seconds >= duration:
            return False
        if song.get('resumes', 0) >= settings.max_resumes:
            return False

        song['resumes'] = song.get('resumes', 0) + 1
        logger.warning(f"[{guild_id}] 串流在 {played:.0f}/{duration} 秒中斷，改用下載檔接續播放 '{song['title']}'。")

        file_path = song.get('file_path')
        if not (file_path and await asyncio.to_thread(os.path.exists, file_path)):
            _, error = await self.prefetcher.ensure_downloaded(ctx, song)
            file_path = song.get('file_path')
            if error or not (file_path and await asyncio.to_thread(os.path.exists, file_path)):
                logger.error(f"[{guild_id}] 無法接續播放 '{song['title']}': {error or '找不到下載檔'}")
                return False

        # The listener may have skipped or stopped while the download finished.
        voice_client = self.get_voice_client(guild_id)
        current = state.current_song
        if state.user_stopped or not voice_client or not voice_client.is_connected():
            return False
        if not current or current['video_id'] != song['video_id']:
            return False

        audio_source = self._make_source(guild_id, song, start_offset=played)
        voice_client.play(audio_source)
        song['streaming'] = False
        view = self.ui_manager.get_current_view(guild_id)
        if view:
            view.start_progress_updater(duration, start_position=int(played))
        task = asyncio.get_running_loop().create_task(self._player_loop(ctx, song, played))
        self.state_manager.update_state(guild_id, player_loop_task=task)
        return True


async def setup(bot):
    """Initialize the music cog"""
    cog = YTMusic(bot)
    await cog.setup_hook()  # Initialize async components
    await bot.add_cog(cog)
