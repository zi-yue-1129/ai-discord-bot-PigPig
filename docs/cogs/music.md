# File: `cogs/music.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/music.py`.

## Classes

### `YTMusic`
Class representing YTMusic.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `youtube` (`Any`): Instance attribute youtube
  - `_executor` (`Any`): Instance attribute _executor
  - `settings` (`Any`): Instance attribute settings
  - `audio_manager` (`Any`): Instance attribute audio_manager
  - `state_manager` (`Any`): Instance attribute state_manager
  - `queue_manager` (`Any`): Instance attribute queue_manager
  - `ui_manager` (`Any`): Instance attribute ui_manager
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager
  - `disconnect_timers` (`Any`): Instance attribute disconnect_timers

- **Methods**:
  - `setup_hook(self) -> Any`: Initialize async components and LanguageManager.
  - `mode(self, interaction, mode) -> Any`: 播放模式命令
  - `shuffle(self, interaction) -> Any`: 隨機播放命令
  - `play(self, interaction, query) -> Any`: 播放音樂或刷新UI命令
  - `_handle_playlist(self, interaction, url) -> Any`: Handle playlist URL
  - `_handle_single_video(self, interaction, url) -> bool`: Handle single video URL
  - `_handle_search(self, interaction, query) -> Any`: Handle search query
  - `play_next(self, interaction, force_new) -> None`: Play the next song in the queue.  Args:     interaction: The Discord interaction object.     force_new: Whether to force playing a new song instead of looping.
  - `_handle_single_loop(self, interaction, state, voice_client) -> Any`: Handle single song loop playback
  - `_get_next_song(self, interaction, guild_id, force_new) -> Any`: Get the next song to play, handling autoplay and ensuring download.
  - `_refill_queue(self, guild_id) -> Any`: Refill the queue with songs
  - `_play_song(self, interaction, song, voice_client) -> None`: Play a song and update UI
  - `_handle_after_play(self, interaction, song) -> None`: Handle cleanup and queue transitions after a song finishes playing.  Args:     interaction: The Discord interaction object.     song: The song dictionary that just finished playing.
  - `_trigger_autoplay(self, interaction, guild_id) -> Any`: 根據最後播放的歌曲觸發自動播放，精確填充推薦歌曲至5首，並排除重複。
  - `_get_guild_folder(self, guild_id) -> tuple`: Get guild queue and folder
  - `get_queue_manager(self) -> QueueManager`: Method get_queue_manager.
  - `get_state_manager(self) -> StateManager`: Method get_state_manager.
  - `get_voice_client(self, guild_id) -> Optional[discord.VoiceClient]`: Method get_voice_client.
  - `get_lang_manager(self) -> Optional[LanguageManager]`: Method get_lang_manager.
  - `handle_previous(self, interaction) -> Any`: Method handle_previous.
  - `handle_toggle_playback(self, interaction) -> Any`: Method handle_toggle_playback.
  - `handle_skip(self, interaction) -> Any`: Method handle_skip.
  - `handle_stop(self, interaction) -> Any`: Method handle_stop.
  - `handle_toggle_mode(self, interaction) -> Any`: Method handle_toggle_mode.
  - `handle_toggle_shuffle(self, interaction) -> Any`: Method handle_toggle_shuffle.
  - `handle_show_queue(self, interaction) -> Any`: Method handle_show_queue.
  - `handle_toggle_autoplay(self, interaction) -> Any`: 切換自動播放模式
  - `get_queue_text(self, guild_id) -> str`: Generates the text for the queue display.
  - `_fill_autoplay_queue(self, interaction) -> None`: Fills the queue with recommended songs when autoplay is on.  Args:     interaction: The Discord interaction object.
  - `_cleanup_voice_session(self, guild_id) -> Any`: Cleans up the voice session for a guild.
  - `_cancel_disconnect_timer(self, guild_id) -> Any`: Cancels the disconnect timer for a guild.
  - `_start_disconnect_timer(self, guild_id) -> Any`: Starts the disconnect timer for a guild.
  - `_disconnect_after_delay(self, guild_id) -> Any`: Disconnects the bot after a 5-minute delay if it's still paused.
  - `on_voice_state_update(self, member, before, after) -> Any`: Handle voice state changes, including auto-pause and auto-disconnect.
  - `_create_dummy_interaction(self, channel, guild, original_interaction) -> Any`: Creates a dummy interaction object for internal use.
  - `_player_loop(self, interaction, song) -> Any`: Monitors the player and handles song completion.

## Functions

### `setup(bot) -> Any`
Initialize the music cog

