# File: `cogs/music.py`

## Overview
The Music cog provides a comprehensive YouTube music player system with advanced queue management, playback controls, autoplay functionality, and an intuitive user interface. It features a robust architecture with separated concerns across multiple library modules.

## Classes

### `YTMusic`
Manages the state and core operations for YTMusic.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `youtube` (`Any`): Instance attribute managing youtube.
  - `_executor` (`Any`): Instance attribute managing _executor.
  - `settings` (`Any`): Instance attribute managing settings.
  - `audio_manager` (`Any`): Instance attribute managing audio_manager.
  - `state_manager` (`Any`): Instance attribute managing state_manager.
  - `queue_manager` (`Any`): Instance attribute managing queue_manager.
  - `ui_manager` (`Any`): Instance attribute managing ui_manager.
  - `disconnect_timers` (`Any`): Instance attribute managing disconnect_timers.

- **Methods**:
  - `setup_hook() -> Any`: Initialize async components and LanguageManager.
  - `mode(interaction, mode) -> Any`: 播放模式命令
  - `shuffle(interaction) -> Any`: 隨機播放命令
  - `play(interaction, query) -> Any`: 播放音樂或刷新UI命令
  - `play_next(interaction, force_new) -> None`: Play the next song in the queue.  Args:     interaction: The Discord interaction object.     force_new: Whether to force playing a new song instead of looping.
  - `get_voice_client(guild_id) -> Optional[discord.VoiceClient]`: Executes logic for get_voice_client.
  - `handle_previous(interaction) -> Any`: Executes logic for handle_previous.
  - `handle_toggle_playback(interaction) -> Any`: Executes logic for handle_toggle_playback.
  - `handle_skip(interaction) -> Any`: Executes logic for handle_skip.
  - `handle_stop(interaction) -> Any`: Executes logic for handle_stop.
  - `handle_toggle_mode(interaction) -> Any`: Executes logic for handle_toggle_mode.
  - `handle_toggle_shuffle(interaction) -> Any`: Executes logic for handle_toggle_shuffle.
  - `handle_show_queue(interaction) -> Any`: Executes logic for handle_show_queue.
  - `handle_toggle_autoplay(interaction) -> Any`: 切換自動播放模式
  - `get_queue_text(guild_id) -> str`: Generates the text for the queue display.
  - `on_voice_state_update(member, before, after) -> Any`: Handle voice state changes, including auto-pause and auto-disconnect.

## Functions

### `setup(bot) -> Any`
Initialize the music cog

