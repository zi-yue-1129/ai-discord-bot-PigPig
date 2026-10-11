import asyncio
import os
import discord
from discord.ext import commands
from discord import app_commands
from addons.logging import get_logger
log = get_logger(source=__name__, server_id="system")
logger = log
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Any

from addons.settings import music_config
from .music_lib.youtube import YouTubeManager
from .music_lib.audio_manager import AudioManager
from .music_lib.state_manager import StateManager
from .music_lib.queue_manager import QueueManager, PlayMode
from .music_lib.context import PlaybackContext, user_shares_voice_channel
from .music_lib.prefetch import Prefetcher
from .music_lib.service import MusicService, classify_query
from .music_lib.ui_manager import UIManager
from .music_lib.ui.song_select import SongSelectView
from cogs.language_manager import LanguageManager # Import LanguageManager
from function import func

# Playback attempts that may fail back-to-back before the player gives up.
MAX_CONSECUTIVE_FAILURES = 3
# How long a paused player may sit idle before the bot leaves the voice channel.
PAUSED_DISCONNECT_SECONDS = 300
# How long the "queue finished" message stays before the bot leaves the voice channel.
QUEUE_END_DISCONNECT_SECONDS = 10


class PlaybackAbortedError(RuntimeError):
    """Raised when consecutive failures exhausted the retry budget."""


class YTMusic(commands.Cog):
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
        self.service = MusicService(self, music_config.ai)
        self.prefetcher = Prefetcher(
            get_youtube=lambda: self.youtube,
            queue_manager=self.queue_manager,
            get_folder=lambda guild_id: self._get_guild_folder(guild_id)[1],
        )

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

    @app_commands.command(name="shuffle", description="切換隨機播放")
    async def shuffle(self, interaction: discord.Interaction):
        """隨機播放命令"""
        guild_id = interaction.guild.id
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
            text = self.lang_manager.translate(guild_id, "commands", "queue_tools", "errors", result.reason)
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
    async def play(self, interaction: discord.Interaction, query: Optional[str] = None):
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
        
        query_kind = classify_query(query)
        if query_kind == "playlist":
            await self._handle_playlist(interaction, query.strip())
        elif query_kind == "video":
            is_valid = await self._handle_single_video(interaction, query.strip())
            if not is_valid:
                return
        else:
            await self._handle_search(interaction, query)
            return
        
        # 播放音樂
        voice_client = interaction.guild.voice_client
        if not voice_client.is_playing():
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

    async def _handle_single_video(self, interaction: discord.Interaction, url: str) -> bool:
        """Handle single video URL"""
        guild_id_str = str(interaction.guild.id)
        video_info, failure = await self.service.enqueue_video(PlaybackContext.from_interaction(interaction), url)

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

    async def _handle_search(self, interaction: discord.Interaction, query: str):
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

        view = SongSelectView(self, results, interaction)
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
        title = self.lang_manager.translate(str(guild_id), "commands", "play", "responses", "queue_finished")
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
                voice_client.stop()

            song = state.current_song
            audio_source = self.audio_manager.create_audio_source(song, volume=state.volume)

            message = await self.ui_manager.update_player_ui(
                ctx,
                state.current_song,
                state.current_message,
                self.youtube,
                music_cog=self
            )
            self.state_manager.update_state(ctx.guild.id, current_message=message)

            voice_client.play(audio_source)
            if not song.get('is_live'):
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
                await self._refill_queue(guild_id)
                next_song = await self.queue_manager.get_next_item(guild_id)

            if not next_song:
                return None

            if next_song.get('is_live') or next_song.get('file_path'):
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

    async def _refill_queue(self, guild_id: int):
        """Refill the queue with songs"""
        queue_copy, new_queue = await self.queue_manager.copy_queue(
            guild_id, 
            shuffle=self.queue_manager.is_shuffle_enabled(guild_id)
        )
        if queue_copy:
            self.queue_manager.set_queue(guild_id, new_queue)

    async def _play_song(self, ctx: PlaybackContext, song: dict, voice_client: Any) -> None:
        """Play a song and update UI"""
        guild_id = ctx.guild.id
        await self._cancel_disconnect_timer(guild_id)
        if voice_client.is_playing():
            voice_client.stop()

        audio_source = self.audio_manager.create_audio_source(song, volume=self.state_manager.get_state(guild_id).volume)
        message = await self.ui_manager.update_player_ui(
            ctx,
            song,
            self.state_manager.get_state(guild_id).current_message,
            self.youtube,
            music_cog=self
        )
        self.state_manager.update_state(guild_id, current_message=message, current_song=song, last_played_song=song)

        voice_client.play(audio_source)
        self.state_manager.update_state(guild_id, consecutive_failures=0)
        self.prefetcher.schedule(ctx)
        if not song.get('is_live'):
            self.state_manager.cancel_player_loop(guild_id)
            task = self.bot.loop.create_task(self._player_loop(ctx, song))
            self.state_manager.update_state(guild_id, player_loop_task=task)

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

            # 如果是清單循環模式，將剛播放完的歌曲（包含檔案路徑）重新加入佇列
            if play_mode == PlayMode.LOOP_QUEUE and current_song:
                await self.queue_manager.add_to_queue(guild_id, current_song, force=True)
                logger.info(f"[音樂] 在清單循環模式下，將 '{current_song['title']}' 重新加入佇列。")

            # 只有在非循環且非直播的模式下才刪除檔案
            if play_mode not in [PlayMode.LOOP_SINGLE, PlayMode.LOOP_QUEUE] and not song.get('is_live'):
                file_path = song.get('file_path')
                if file_path:
                    await self.audio_manager.delete_file(guild_id, file_path)

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
        except Exception as e:
            # The queue housekeeping failed, but the listeners still want music:
            # report it and carry on with the next song.
            await func.report_error(e, "housekeeping after play")

        # play_next handles its own failures and gives up after a bounded number of retries.
        await self.play_next(ctx)

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
        exclude_ids = {s.get('video_id') for s in queue_snapshot if s.get('video_id')}
        if state.current_song and state.current_song.get('video_id'):
            exclude_ids.add(state.current_song.get('video_id'))

        related_videos, error = await self.youtube.get_related_videos(
            video_id, title, author, ctx, limit=needed, exclude_ids=exclude_ids
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
        else:
            text = self.lang_manager.translate(guild_id, "system", "music", "controls", "no_music")
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    async def _ensure_can_control(self, interaction: discord.Interaction) -> bool:
        """Check that the user sits in the bot's voice channel before changing playback.

        Without a voice client there is nothing to protect, so the handler's own
        "nothing is playing" reply applies and this returns ``True``.

        Args:
            interaction: The interaction that triggered the control.

        Returns:
            ``True`` when the control may proceed; otherwise an ephemeral
            explanation has been sent and ``False`` is returned.
        """
        guild_id = interaction.guild.id
        voice_client = self.get_voice_client(guild_id)
        if voice_client is None or user_shares_voice_channel(interaction.user, voice_client):
            return True
        text = self.lang_manager.translate(str(guild_id), "system", "music", "controls", "not_in_channel")
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)
        return False

    # --- Callback Handlers ---
    async def handle_previous(self, interaction: discord.Interaction):
        if not await self._ensure_can_control(interaction):
            return
        voice_client = self.get_voice_client(interaction.guild.id)
        if not voice_client:
            await interaction.response.send_message(self.lang_manager.translate(str(interaction.guild.id), "system", "music", "controls", "no_music"), ephemeral=True)
            return

        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            view = self.ui_manager.get_current_view(interaction.guild.id)
            if view:
                await view.update_embed(
                    interaction,
                    self.lang_manager.translate(str(interaction.guild.id), "system", "music", "controls", "previous", user=interaction.user.name)
                )

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

    async def handle_toggle_mode(self, interaction: discord.Interaction):
        if not await self._ensure_can_control(interaction):
            return
        guild_id = interaction.guild.id
        current_mode = self.queue_manager.get_play_mode(guild_id)
        
        mode_order = ["no_loop", "loop_queue", "loop_single"]
        current_index = mode_order.index(current_mode.value)
        next_mode_str = mode_order[(current_index + 1) % len(mode_order)]
        
        self.queue_manager.set_play_mode(guild_id, PlayMode(next_mode_str))
        
        mode_name = self.lang_manager.translate(str(guild_id), "commands", "mode", "choices", next_mode_str)
        
        view = self.ui_manager.get_current_view(guild_id)
        if view:
            await view.update_button_state()
            await view.update_embed(interaction, self.lang_manager.translate(str(guild_id), "system", "music", "controls", "mode_changed", user=interaction.user.name, mode=mode_name))

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

        queue_text = await self.get_queue_text(guild_id)
        view.current_embed.set_field_at(4, name=self.lang_manager.translate(str(guild_id), "system", "music", "player", "queue"), value=queue_text, inline=False)
        await view.update_embed(interaction, view.current_embed.title, view.current_embed.color)

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
        
        title = self.lang_manager.translate(str(guild_id), "system", "music", "autoplay", "toggled", status=status_str)
        
        await interaction.response.send_message(f"✅ | {title}", ephemeral=True)

        if not state.autoplay:
            return

        ctx = PlaybackContext.from_interaction(interaction)
        voice_client = interaction.guild.voice_client
        if voice_client and not voice_client.is_playing():
            # Nothing playing: play_next fills the empty queue through autoplay itself.
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 觸發閒置時的 Autoplay。")
            self.bot.loop.create_task(self.play_next(ctx))
        elif self.queue_manager.is_queue_empty(guild_id):
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, Autoplay 已啟用且待播清單為空，立即觸發推薦填充。")
            self.bot.loop.create_task(self._trigger_autoplay(ctx, guild_id, notify=True))

    async def get_queue_text(self, guild_id: int) -> str:
        """Generates the text for the queue display."""
        guild_id_str = str(guild_id)
        state = self.state_manager.get_state(guild_id)
        
        queue_items = self.queue_manager.get_queue_snapshot(guild_id)
        
        text = ""
        if state.current_song:
            minutes, seconds = divmod(float(state.current_song.get("duration", 0)), 60)
            prefix = self.lang_manager.translate(guild_id_str, "system", "music", "controls", "now_playing_prefix")
            text += f"{prefix} {state.current_song['title']} | {int(minutes):02d}:{int(seconds):02d}\n\n"
        
        if queue_items:
            label = self.lang_manager.translate(guild_id_str, "system", "music", "controls", "queue_songs")
            text += f"{label}\n"
            for i, item in enumerate(queue_items, 1):
                duration = item.get("duration", 0)
                minutes, seconds = divmod(float(duration), 60)
                line = f"{i}. {item['title']} | {int(minutes):02d}:{int(seconds):02d}\n"
                
                # Check if adding the current line exceeds embed field limit (1024 chars).
                # Keep a 100 character buffer for the "more songs" localized suffix.
                if len(text) + len(line) + 100 > 1024:
                    remaining_count = len(queue_items) - i + 1
                    more_songs_text = self.lang_manager.translate(
                        guild_id_str, "system", "music", "player", "more_songs", count=remaining_count
                    )
                    text += more_songs_text
                    break
                
                text += line
        
        return text if text.strip() else self.lang_manager.translate(guild_id_str, "system", "music", "player", "queue_empty")

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

        # Clean up all UI messages
        for message in state.ui_messages:
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
        _, folder = self._get_guild_folder(guild_id)
        await self.audio_manager.cleanup_guild_files(guild_id, folder)
        self.state_manager.update_state(guild_id, current_song=None, last_played_song=None, current_message=None, current_view=None, ui_messages=[])
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
        if voice_client and voice_client.is_connected() and not voice_client.is_playing():
            logger.info(f"[音樂] 伺服器 ID: {guild_id}, 閒置超過 {delay:g} 秒，自動斷線。")

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
                # No one left, pause the player and start disconnect timer
                if voice_client.is_playing():
                    logger.info(f"[音樂] 伺服器 ID: {member.guild.id}, 頻道內無人，自動暫停播放。")
                    voice_client.pause()
                    await self._start_disconnect_timer(member.guild.id)

                    # Update UI button state (progress updater handles paused state on its own)
                    view = self.ui_manager.get_current_view(member.guild.id)
                    if view:
                        await view.update_button_state()

            else:
                # Someone is in the channel, resume if paused
                if voice_client.is_paused():
                    # Check if the pause was due to inactivity (i.e., a timer is running)
                    if member.guild.id in self.disconnect_timers:
                        logger.info(f"[音樂] 伺服器 ID: {member.guild.id}, 有使用者加入，自動恢復播放。")
                        voice_client.resume()
                        await self._cancel_disconnect_timer(member.guild.id)

                        view = self.ui_manager.get_current_view(member.guild.id)
                        if view:
                            await view.update_button_state()

    async def _player_loop(self, ctx: PlaybackContext, song: dict) -> None:
        """Monitors the player and handles song completion."""
        guild_id = ctx.guild.id
        logger.info(f"[{guild_id}] Player loop started for '{song['title']}'.")

        await asyncio.sleep(2)  # Wait for playback to start

        while True:
            voice_client = self.get_voice_client(guild_id)
            if not voice_client or not voice_client.is_connected():
                logger.warning(f"[{guild_id}] Player loop exiting: voice client disconnected.")
                return

            if voice_client.is_paused():
                await asyncio.sleep(1)
                continue

            if not voice_client.is_playing():
                logger.info(f"[{guild_id}] Player loop detected song has finished.")
                break

            await asyncio.sleep(1)

        state = self.state_manager.get_state(guild_id)
        # Ensure we are still on the same song before triggering after_play
        if state.current_song and state.current_song['video_id'] == song['video_id']:
            logger.info(f"[{guild_id}] 歌曲 '{song['title']}' 播放完畢，觸發 _handle_after_play。")
            await self._handle_after_play(ctx, song)
        else:
            logger.info(f"[{guild_id}] Player loop for '{song['title']}' exiting without action. (Song might have been skipped).")


async def setup(bot):
    """Initialize the music cog"""
    cog = YTMusic(bot)
    await cog.setup_hook()  # Initialize async components
    await bot.add_cog(cog)
