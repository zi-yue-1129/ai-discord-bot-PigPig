import discord
import asyncio
from typing import Optional
from ..context import PlaybackContext
from .progress import ProgressDisplay
from cogs.language_manager import LanguageManager
from ..queue_manager import PlayMode
from ..filters import FILTER_NAMES, get_preset
from addons.logging import get_logger

log = get_logger(source=__name__, server_id="system")


# Value of the placeholder option shown while the queue is empty (the menu is disabled then).
_EMPTY_QUEUE_VALUE = "__empty__"
# Seconds the rewind and fast-forward buttons jump.
SEEK_STEP_SECONDS = 10
_MODE_EMOJIS = {"no_loop": "➡️", "loop_queue": "🔁", "loop_single": "🔂"}


class QueueSongActions(discord.ui.View):
    """What to do with the queued song picked in the player's queue menu (shown only to the picker)."""

    def __init__(self, video_id: str, callback, translate) -> None:
        super().__init__(timeout=120)
        self.video_id = video_id
        self._callback = callback
        for action, custom_id, emoji, style in (
            ("play_next", "queue_play_next", "⏭️", discord.ButtonStyle.primary),
            ("remove", "queue_remove", "🗑️", discord.ButtonStyle.danger),
        ):
            button = discord.ui.Button(label=translate("controls", f"{custom_id}_action"), emoji=emoji, style=style,
                                       custom_id=custom_id)
            button.callback = self._make_callback(action)
            self.add_item(button)

    def _make_callback(self, action: str):
        async def run(interaction: discord.Interaction) -> None:
            await self._callback(interaction, action, self.video_id)
            self.stop()
            if not interaction.response.is_done():
                await interaction.response.edit_message(content="✅", view=None)
        return run


def set_queue_field(embed: discord.Embed, name: str, text: str) -> None:
    """Shows the queue on a player embed, replacing the field when it is already there.

    The field is found by name, not position: a live stream has no progress field.

    Args:
        embed: The player embed.
        name: The translated field name.
        text: The queue text.
    """
    position = next((index for index, field in enumerate(embed.fields) if field.name == name), None)
    if position is None:
        embed.add_field(name=name, value=text, inline=False)
    else:
        embed.set_field_at(position, name=name, value=text, inline=False)


def remove_queue_field(embed: discord.Embed, name: str) -> None:
    """Hides the queue on a player embed (nothing happens when it is not shown).

    Args:
        embed: The player embed.
        name: The translated field name.
    """
    position = next((index for index, field in enumerate(embed.fields) if field.name == name), None)
    if position is not None:
        embed.remove_field(position)


class MusicControlView(discord.ui.View):
    def __init__(self, ctx: PlaybackContext, *,
                song_info: dict,  # Add song_info
                previous_callback, toggle_playback_callback, skip_callback, stop_callback,
                toggle_shuffle_callback, show_queue_callback, toggle_autoplay_callback,
                get_queue_manager, get_state_manager, get_voice_client, get_lang_manager,
                get_queue_text=None, get_queue_options=None, queue_select_callback=None,
                set_mode_callback=None, set_filter_callback=None, seek_callback=None,
                toggle_lyrics_callback=None, refresh_lyrics=None):
        super().__init__(timeout=None)
        self.guild = ctx.guild
        self.message = None
        self.current_embed = None
        self.song_info = song_info  # Store song_info
        self.lang_manager: Optional[LanguageManager] = None
        self._is_updating = False
        self.update_task = None
        self.current_position = 0

        # Action Callbacks
        self.previous_callback = previous_callback
        self.toggle_playback_callback = toggle_playback_callback
        self.skip_callback = skip_callback
        self.stop_callback = stop_callback
        self.set_mode_callback = set_mode_callback
        self.set_filter_callback = set_filter_callback
        self.seek_callback = seek_callback
        self.toggle_lyrics_callback = toggle_lyrics_callback
        # Updates the synced lyrics field of ``current_embed``; returns whether it is shown.
        self.refresh_lyrics = refresh_lyrics
        self.toggle_shuffle_callback = toggle_shuffle_callback
        self.show_queue_callback = show_queue_callback
        self.toggle_autoplay_callback = toggle_autoplay_callback

        # State/Manager Getters
        self.get_queue_manager = get_queue_manager
        self.get_state_manager = get_state_manager
        self.get_voice_client = get_voice_client
        self.get_lang_manager = get_lang_manager
        self.get_queue_text = get_queue_text
        self.get_queue_options = get_queue_options
        self.queue_select_callback = queue_select_callback
        self._queue_menus: list = []
        if get_queue_options and queue_select_callback:
            self._queue_menus = [self._add_queue_menu("queue_song", row=2)]
            self.refresh_queue_menus()
        self._mode_menu = self._add_mode_menu(row=3) if set_mode_callback else None
        self._filter_menu = self._add_filter_menu(row=4) if set_filter_callback else None
        self.refresh_setting_menus()

        asyncio.create_task(self.update_button_state(update_message=False))

    def _add_queue_menu(self, custom_id: str, *, row: int) -> discord.ui.Select:
        """Adds the queue menu: the picked song gets a private message to play it next or remove it.

        Args:
            custom_id: The menu's ID (its placeholder text is ``<custom_id>_placeholder``).
            row: The row under the buttons.

        Returns:
            The added menu.
        """
        menu = discord.ui.Select(
            custom_id=custom_id,
            placeholder=self._translate_music("controls", f"{custom_id}_placeholder"),
            options=[discord.SelectOption(label="-", value=_EMPTY_QUEUE_VALUE)],
            row=row,
        )

        async def choose(interaction: discord.Interaction) -> None:
            video_id = menu.values[0]
            label = next((option.label for option in menu.options if option.value == video_id), video_id)
            actions = QueueSongActions(video_id, self.queue_select_callback, self._translate_music)
            await interaction.response.send_message(f"🎵 {label}", view=actions, ephemeral=True)

        menu.callback = choose
        self.add_item(menu)
        return menu

    def _add_mode_menu(self, *, row: int) -> discord.ui.Select:
        """Adds the loop mode menu (the current mode is pre-selected)."""
        menu = discord.ui.Select(custom_id="play_mode", options=[
            discord.SelectOption(label=self._get_mode_name(mode.value), value=mode.value, emoji=_MODE_EMOJIS[mode.value])
            for mode in PlayMode
        ], row=row)

        async def choose(interaction: discord.Interaction) -> None:
            await self.set_mode_callback(interaction, menu.values[0])
            if not interaction.response.is_done():
                await interaction.response.defer()

        menu.callback = choose
        self.add_item(menu)
        return menu

    def _add_filter_menu(self, *, row: int) -> discord.ui.Select:
        """Adds the audio effect menu (the current effect is pre-selected)."""
        menu = discord.ui.Select(custom_id="audio_filter", options=[
            discord.SelectOption(label=self._translate_music("filters", name), value=name, emoji=get_preset(name).emoji)
            for name in FILTER_NAMES
        ], row=row)

        async def choose(interaction: discord.Interaction) -> None:
            await self.set_filter_callback(interaction, menu.values[0])
            if not interaction.response.is_done():
                await interaction.response.defer()

        menu.callback = choose
        self.add_item(menu)
        return menu

    def refresh_setting_menus(self) -> None:
        """Marks the current loop mode and effect in their menus."""
        guild_id = self.guild.id
        if self._mode_menu is not None:
            current = self.get_queue_manager().get_play_mode(guild_id).value
            for option in self._mode_menu.options:
                option.default = option.value == current
        if self._filter_menu is not None:
            current = self.get_state_manager().get_state(guild_id).audio_filter
            for option in self._filter_menu.options:
                option.default = option.value == current

    def refresh_queue_menus(self) -> None:
        """Lists the current queue in both menus (disabled while the queue is empty)."""
        if not self._queue_menus:
            return
        options = self.get_queue_options(self.guild.id)
        for menu in self._queue_menus:
            if options:
                menu.options = list(options)
                menu.disabled = False
            else:
                menu.options = [
                    discord.SelectOption(label=self._translate_music("controls", "queue_select_empty"), value=_EMPTY_QUEUE_VALUE)
                ]
                menu.disabled = True

    def _get_lang_manager(self):
        """Get language manager instance"""
        if not self.lang_manager:
            self.lang_manager = self.get_lang_manager()
        return self.lang_manager
        
    def _translate_music(self, *path, **kwargs) -> str:
        """音樂模組專用翻譯方法"""
        lang_manager = self._get_lang_manager()
        if not lang_manager:
            return self._get_fallback_text(path[-1], **kwargs)
        
        return lang_manager.translate(str(self.guild.id), "system", "music", *path, **kwargs)
        
    def _get_fallback_text(self, key: str, **kwargs) -> str:
        """備用文字機制"""
        fallback_texts = {
            "no_music": "❌ 沒有正在播放的音樂！",
            "no_songs": "❌ 沒有可播放的歌曲！",
            "previous": "⏮️ {user} 返回上一首",
            "paused": "⏸️ {user} 暫停了音樂",
            "resumed": "▶️ {user} 繼續了音樂",
            "skipped": "⏭️ {user} 跳過了音樂",
            "stopped": "⏹️ {user} 停止了播放",
            "mode_changed": "🔄 {user} 將播放模式設為 {mode}",
            "shuffle_toggled": "🔀 {user} {status}隨機播放",
            "now_playing_prefix": "▶️ 正在播放:",
            "queue_songs": "待播放歌曲:",
            "update_failed": "無法更新播放清單"
        }
        
        text = fallback_texts.get(key, key)
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
            
    def _get_mode_name(self, mode: str) -> str:
        """獲取播放模式翻譯名稱"""
        lang_manager = self._get_lang_manager()
        if lang_manager:
            return lang_manager.translate(str(self.guild.id), "commands", "mode", "choices", mode)
        
        # 備用機制
        mode_names = {
            "no_loop": "不循環",
            "loop_queue": "清單循環",
            "loop_single": "單曲循環"
        }
        return mode_names.get(mode, mode)
        
    def _get_shuffle_status(self, is_enabled: bool) -> str:
        """獲取隨機播放狀態文字"""
        lang_manager = self._get_lang_manager()
        if lang_manager:
            status_key = "enabled" if is_enabled else "disabled"
            return lang_manager.translate(str(self.guild.id), "commands", "shuffle", "responses", status_key)
        
        # 備用機制
        return "開啟" if is_enabled else "關閉"

    async def update_button_state(self, update_message: bool = True):
        """Update button states based on current playback and mode status"""
        voice_client = self.get_voice_client()
        guild_id = self.guild.id
        queue_manager = self.get_queue_manager()

        self.refresh_queue_menus()
        self.refresh_setting_menus()

        # Update button states
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                # Play/Pause button
                if child.custom_id == "toggle_playback":
                    if voice_client and voice_client.is_playing():
                        child.emoji = discord.PartialEmoji.from_str('⏸️')
                    elif voice_client and voice_client.is_paused():
                        child.emoji = discord.PartialEmoji.from_str('▶️')
                    else:
                        child.emoji = discord.PartialEmoji.from_str('⏯️')

                # Lyrics button: lit while the synced lyrics are shown
                elif child.custom_id == "toggle_lyrics":
                    show_lyrics = self.get_state_manager().get_state(guild_id).show_lyrics
                    child.style = discord.ButtonStyle.green if show_lyrics else discord.ButtonStyle.gray
                    child.disabled = self.toggle_lyrics_callback is None

                elif child.custom_id in ("seek_back", "seek_forward"):
                    child.disabled = self.seek_callback is None or bool(self.song_info.get('is_live'))

                # Shuffle button
                elif child.custom_id == "toggle_shuffle":
                    is_shuffle = queue_manager.is_shuffle_enabled(guild_id)
                    child.style = discord.ButtonStyle.green if is_shuffle else discord.ButtonStyle.gray
                    child.emoji = discord.PartialEmoji.from_str('🔀')

                # Queue button: lit while the queue list is shown
                elif child.custom_id == "show_queue":
                    show_queue = self.get_state_manager().get_state(guild_id).show_queue
                    child.style = discord.ButtonStyle.green if show_queue else discord.ButtonStyle.gray

                # Autoplay button
                elif child.custom_id == "toggle_autoplay":
                    state = self.get_state_manager().get_state(guild_id)
                    is_autoplay = state.autoplay
                    child.style = discord.ButtonStyle.green if is_autoplay else discord.ButtonStyle.gray
                    child.emoji = discord.PartialEmoji.from_str('🎶')

        # Only update message if requested and message exists
        if update_message and self.message:
            try:
                await self.message.edit(view=self)
            except Exception as e:
                log.error(f"Failed to update button state: {e}")

    async def refresh_queue_field(self) -> bool:
        """Brings the shown queue list up to date (songs may have been added or removed).

        Returns:
            Whether the queue is shown, so the embed was changed.
        """
        state = self.get_state_manager().get_state(self.guild.id)
        if not (state.show_queue and self.get_queue_text and self.current_embed):
            return False
        set_queue_field(
            self.current_embed, self._translate_music("player", "queue"), await self.get_queue_text(self.guild.id)
        )
        return True

    def start_progress_updater(self, duration: int, start_position: int = 0):
        """Starts the progress bar updater.

        Args:
            duration: Song length in seconds.
            start_position: Seconds already played (non-zero after a resume).
        """
        # 如果是直播，則不啟動進度更新器
        if self.song_info.get('is_live', False):
            return
            
        if self.update_task:
            self.update_task.cancel()
        self.current_position = start_position
        self.update_task = asyncio.create_task(self.update_progress(duration))

    def stop_progress_updater(self):
        if self.update_task:
            self.update_task.cancel()
            self.update_task = None
            self._is_updating = False

    async def update_progress(self, duration):
        # 如果是直播，則不更新進度
        if self.song_info.get('is_live', False):
            return

        try:
            if self._is_updating:
                return

            self._is_updating = True
            await self.update_button_state()
            update_interval = 5
            last_update = 0
            message_refresh_interval = 600
            last_message_refresh = asyncio.get_event_loop().time()

            try:
                while True:
                    voice_client = self.get_voice_client()
                    if not voice_client or not voice_client.is_connected():
                        await self.update_button_state()
                        break

                    # When paused, wait without advancing position or updating UI
                    if voice_client.is_paused():
                        await asyncio.sleep(1)
                        continue

                    if not voice_client.is_playing():
                        await self.update_button_state()
                        break

                    position = getattr(self.get_state_manager().get_state(self.guild.id), "position", None)
                    self.current_position = int(position) if isinstance(position, (int, float)) and position else self.current_position + 1
                    if self.current_position > duration:
                        await self.update_button_state()
                        break

                    current_time = asyncio.get_event_loop().time()

                    # Refresh message periodically to keep it at the bottom of chat
                    if current_time - last_message_refresh >= message_refresh_interval:
                        try:
                            new_message = await self.message.channel.send(embed=self.current_embed, view=self)
                            await self.message.delete()
                            self.message = new_message
                            last_message_refresh = current_time
                        except Exception as e:
                            log.error(f"刷新訊息失敗: {e}")
                            break

                    # Update progress bar every update_interval seconds (more often while synced lyrics show)
                    lyrics_shown = self.get_state_manager().get_state(self.guild.id).show_lyrics
                    interval = 2 if lyrics_shown else update_interval
                    if current_time - last_update >= interval:
                        if self.current_embed and self.message:
                            try:
                                progress_bar = ProgressDisplay.create_progress_bar(self.current_position, duration)
                                progress_field_name = self._translate_music("player", "progress")
                                await self.refresh_queue_field()
                                if self.refresh_lyrics is not None:
                                    self.refresh_lyrics(self)
                                # Find the progress field by name to avoid hardcoded index
                                for idx, field in enumerate(self.current_embed.fields):
                                    if field.name == progress_field_name or field.name == "🎵 播放進度":
                                        self.current_embed.set_field_at(idx, name=progress_field_name, value=progress_bar, inline=False)
                                        break

                                await self.message.edit(embed=self.current_embed, view=self)
                                last_update = current_time
                            except discord.errors.HTTPException as e:
                                if e.code == 50027:  # Invalid Webhook Token
                                    try:
                                        new_message = await self.message.channel.send(embed=self.current_embed, view=self)
                                        try:
                                            await self.message.delete()
                                        except discord.errors.NotFound:
                                            pass
                                        self.message = new_message
                                        last_update = current_time
                                        log.info("Successfully recreated message in update_progress")
                                    except Exception as inner_e:
                                        log.error(f"Failed to recreate message in update_progress: {inner_e}")
                                        break
                                else:
                                    log.error(f"更新進度條位置失敗: {e}")

                    await asyncio.sleep(1)
            finally:
                self._is_updating = False
                if hasattr(self, 'update_task'):
                    self.update_task = None
        except Exception as e:
            log.error(f"Progress update error: {e}")
            try:
                await self.update_button_state()
            except Exception as view_error:
                log.error(f"Failed to update button state after error: {view_error}")

    async def update_embed(self, interaction: discord.Interaction, title: str, color: discord.Color = discord.Color.blue()):
        """Update the embed with error handling and message recreation"""
        if not (self.current_embed and self.message):
            return

        self.current_embed.title = title
        self.current_embed.color = color

        async def try_edit_or_recreate(message, embed, view):
            try:
                await message.edit(embed=embed)
                return message
            except discord.errors.HTTPException as e:
                if e.code == 50027:  # Invalid Webhook Token
                    try:
                        # Create new message
                        new_message = await message.channel.send(embed=embed, view=view)
                        # Try to delete old message
                        try:
                            await message.delete()
                        except (discord.errors.NotFound, discord.errors.Forbidden):
                            pass
                        log.info("Successfully recreated message")
                        return new_message
                    except Exception as inner_e:
                        log.error(f"Failed to recreate message: {inner_e}")
                        return None
                else:
                    log.error(f"Failed to update embed: {e}")
                    return None
            except Exception as e:
                log.error(f"Unexpected error in update_embed: {e}")
                return None

        new_message = await try_edit_or_recreate(self.message, self.current_embed, self)
        if new_message:
            self.message = new_message

    @discord.ui.button(emoji='⏮️', style=discord.ButtonStyle.gray, custom_id="previous", row=0)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.previous_callback(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='⏯️', style=discord.ButtonStyle.gray, custom_id="toggle_playback", row=0)
    async def toggle_playback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_playback_callback(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='⏭️', style=discord.ButtonStyle.gray, custom_id="skip", row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.response.is_done():
            await interaction.response.defer()
        await self.skip_callback(interaction)

    @discord.ui.button(emoji='⏹️', style=discord.ButtonStyle.red, custom_id="stop", row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.stop_callback(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='🎤', style=discord.ButtonStyle.gray, custom_id="toggle_lyrics", row=0)
    async def toggle_lyrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shows or hides the synced lyrics on the player."""
        if self.toggle_lyrics_callback is not None:
            await self.toggle_lyrics_callback(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='🔀', style=discord.ButtonStyle.gray, custom_id="toggle_shuffle", row=1)
    async def toggle_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        """切換隨機播放"""
        await self.toggle_shuffle_callback(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='📜', style=discord.ButtonStyle.gray, custom_id="show_queue", row=1)
    async def show_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_queue_callback(interaction)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='🎶', style=discord.ButtonStyle.gray, custom_id="toggle_autoplay", row=1)
    async def toggle_autoplay(self, interaction: discord.Interaction, button: discord.ui.Button):
        """切換自動播放"""
        await self.toggle_autoplay_callback(interaction)

    @discord.ui.button(emoji='⏪', style=discord.ButtonStyle.gray, custom_id="seek_back", row=1)
    async def seek_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rewinds the song."""
        if self.seek_callback is not None:
            await self.seek_callback(interaction, -SEEK_STEP_SECONDS)
        if not interaction.response.is_done():
            await interaction.response.defer()

    @discord.ui.button(emoji='⏩', style=discord.ButtonStyle.gray, custom_id="seek_forward", row=1)
    async def seek_forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fast-forwards the song."""
        if self.seek_callback is not None:
            await self.seek_callback(interaction, SEEK_STEP_SECONDS)
        if not interaction.response.is_done():
            await interaction.response.defer()
