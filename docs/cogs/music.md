# File: `cogs/music.py`

## Overview
The Music cog provides a comprehensive YouTube music player system with advanced queue management, playback controls, autoplay functionality, and an intuitive user interface. It features a robust architecture with separated concerns across multiple library modules.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `music.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `YTMusic`
Class managing YTMusic state and behavior.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `youtube` (`Any`): Internal instance state.
  - `_executor` (`Any`): Internal instance state.
  - `settings` (`Any`): Internal instance state.
  - `audio_manager` (`Any`): Internal instance state.
  - `state_manager` (`Any`): Internal instance state.
  - `queue_manager` (`Any`): Internal instance state.
  - `ui_manager` (`Any`): Internal instance state.
  - `disconnect_timers` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `setup_hook() -> Any`: Initialize async components and LanguageManager.
  - `mode(interaction: discord.Interaction, mode: app_commands.Choice[str]) -> Any`: 播放模式命令
  - `shuffle(interaction: discord.Interaction) -> Any`: 隨機播放命令
  - `play(interaction: discord.Interaction, query: Optional[str]) -> Any`: 播放音樂或刷新UI命令
  - `_handle_playlist(interaction: discord.Interaction, url: str) -> Any`: Handle playlist URL
  - `_handle_single_video(interaction: discord.Interaction, url: str) -> bool`: Handle single video URL
  - `_handle_search(interaction: discord.Interaction, query: str) -> Any`: Handle search query
  - `play_next(interaction: discord.Interaction, force_new: bool) -> None`: Play the next song in the queue.
  - `_handle_single_loop(interaction: discord.Interaction, state: Any, voice_client: Any) -> Any`: Handle single song loop playback
  - `_get_next_song(interaction: discord.Interaction, guild_id: int, force_new: bool) -> Any`: Get the next song to play, handling autoplay and ensuring download.
  - `_refill_queue(guild_id: int) -> Any`: Refill the queue with songs
  - `_play_song(interaction: discord.Interaction, song: dict, voice_client: Any) -> None`: Play a song and update UI
  - `_handle_after_play(interaction: discord.Interaction, song: dict) -> None`: Handle cleanup and queue transitions after a song finishes playing.
  - `_trigger_autoplay(interaction: discord.Interaction, guild_id: int) -> Any`: 根據最後播放的歌曲觸發自動播放，精確填充推薦歌曲至5首，並排除重複。
  - `_get_guild_folder(guild_id: int) -> tuple`: Get guild queue and folder
  - `get_queue_manager() -> QueueManager`: Performs internal processing logic.
  - `get_state_manager() -> StateManager`: Performs internal processing logic.
  - `get_voice_client(guild_id: int) -> Optional[discord.VoiceClient]`: Performs internal processing logic.
  - `get_lang_manager() -> Optional[LanguageManager]`: Performs internal processing logic.
  - `handle_previous(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_toggle_playback(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_skip(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_stop(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_toggle_mode(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_toggle_shuffle(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_show_queue(interaction: discord.Interaction) -> Any`: Performs internal processing logic.
  - `handle_toggle_autoplay(interaction: discord.Interaction) -> Any`: 切換自動播放模式
  - `get_queue_text(guild_id: int) -> str`: Generates the text for the queue display.
  - `_fill_autoplay_queue(interaction: discord.Interaction) -> None`: Fills the queue with recommended songs when autoplay is on.
  - `_cleanup_voice_session(guild_id: int) -> Any`: Cleans up the voice session for a guild.
  - `_cancel_disconnect_timer(guild_id: int) -> Any`: Cancels the disconnect timer for a guild.
  - `_start_disconnect_timer(guild_id: int) -> Any`: Starts the disconnect timer for a guild.
  - `_disconnect_after_delay(guild_id: int) -> Any`: Disconnects the bot after a 5-minute delay if it's still paused.
  - `on_voice_state_update(member: Any, before: Any, after: Any) -> Any`: Handle voice state changes, including auto-pause and auto-disconnect.
  - `_create_dummy_interaction(channel: Any, guild: Any, original_interaction: Any) -> Any`: Creates a dummy interaction object for internal use.
  - `_player_loop(interaction: discord.Interaction, song: dict) -> Any`: Monitors the player and handles song completion.

## Functions

### `setup(bot: Any) -> Any`
Initialize the music cog
