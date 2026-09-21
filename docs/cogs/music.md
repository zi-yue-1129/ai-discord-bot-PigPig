# File: `cogs/music.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `YTMusic`
Core class implementation.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `youtube` (`Any`): Attribute holding youtube data.
  - `_executor` (`Any`): Attribute holding _executor data.
  - `settings` (`Any`): Attribute holding settings data.
  - `audio_manager` (`Any`): Attribute holding audio_manager data.
  - `state_manager` (`Any`): Attribute holding state_manager data.
  - `queue_manager` (`Any`): Attribute holding queue_manager data.
  - `ui_manager` (`Any`): Attribute holding ui_manager data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.
  - `disconnect_timers` (`Any`): Attribute holding disconnect_timers data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `setup_hook() -> Any`: Initialize async components and LanguageManager.
  - `mode(interaction: discord.Interaction, mode: app_commands.Choice[str]) -> Any`: 播放模式命令
  - `shuffle(interaction: discord.Interaction) -> Any`: 隨機播放命令
  - `play(interaction: discord.Interaction, query: Optional[str]) -> Any`: 播放音樂或刷新UI命令
  - `_handle_playlist(interaction: discord.Interaction, url: str) -> Any`: Handle playlist URL
  - `_handle_single_video(interaction: discord.Interaction, url: str) -> bool`: Handle single video URL
  - `_handle_search(interaction: discord.Interaction, query: str) -> Any`: Handle search query
  - `play_next(interaction: discord.Interaction, force_new: bool) -> None`: Play the next song in the queue.
  - `_handle_single_loop(interaction: discord.Interaction, state, voice_client) -> Any`: Handle single song loop playback
  - `_get_next_song(interaction: discord.Interaction, guild_id: int, force_new: bool) -> Any`: Get the next song to play, handling autoplay and ensuring download.
  - `_refill_queue(guild_id: int) -> Any`: Refill the queue with songs
  - `_play_song(interaction: discord.Interaction, song: dict, voice_client: Any) -> None`: Play a song and update UI
  - `_handle_after_play(interaction: discord.Interaction, song: dict) -> None`: Handle cleanup and queue transitions after a song finishes playing.
  - `_trigger_autoplay(interaction: discord.Interaction, guild_id: int) -> Any`: 根據最後播放的歌曲觸發自動播放，精確填充推薦歌曲至5首，並排除重複。
  - `_get_guild_folder(guild_id: int) -> tuple`: Get guild queue and folder
  - `get_queue_manager() -> QueueManager`: Executes get_queue_manager logic.
  - `get_state_manager() -> StateManager`: Executes get_state_manager logic.
  - `get_voice_client(guild_id: int) -> Optional[discord.VoiceClient]`: Executes get_voice_client logic.
  - `get_lang_manager() -> Optional[LanguageManager]`: Executes get_lang_manager logic.
  - `handle_previous(interaction: discord.Interaction) -> Any`: Executes handle_previous logic.
  - `handle_toggle_playback(interaction: discord.Interaction) -> Any`: Executes handle_toggle_playback logic.
  - `handle_skip(interaction: discord.Interaction) -> Any`: Executes handle_skip logic.
  - `handle_stop(interaction: discord.Interaction) -> Any`: Executes handle_stop logic.
  - `handle_toggle_mode(interaction: discord.Interaction) -> Any`: Executes handle_toggle_mode logic.
  - `handle_toggle_shuffle(interaction: discord.Interaction) -> Any`: Executes handle_toggle_shuffle logic.
  - `handle_show_queue(interaction: discord.Interaction) -> Any`: Executes handle_show_queue logic.
  - `handle_toggle_autoplay(interaction: discord.Interaction) -> Any`: 切換自動播放模式
  - `get_queue_text(guild_id: int) -> str`: Generates the text for the queue display.
  - `_fill_autoplay_queue(interaction: discord.Interaction) -> None`: Fills the queue with recommended songs when autoplay is on.
  - `_cleanup_voice_session(guild_id: int) -> Any`: Cleans up the voice session for a guild.
  - `_cancel_disconnect_timer(guild_id: int) -> Any`: Cancels the disconnect timer for a guild.
  - `_start_disconnect_timer(guild_id: int) -> Any`: Starts the disconnect timer for a guild.
  - `_disconnect_after_delay(guild_id: int) -> Any`: Disconnects the bot after a 5-minute delay if it's still paused.
  - `on_voice_state_update(member, before, after) -> Any`: Handle voice state changes, including auto-pause and auto-disconnect.
  - `_create_dummy_interaction(channel, guild, original_interaction) -> Any`: Creates a dummy interaction object for internal use.
  - `_player_loop(interaction: discord.Interaction, song: dict) -> Any`: Monitors the player and handles song completion.

## Functions

### `setup(bot) -> Any`
Initialize the music cog
