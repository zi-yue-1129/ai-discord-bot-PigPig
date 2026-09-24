# File: `cogs/music_lib/ui/controls.py`

## Overview
Core file handling responsibilities within the `cogs/music_lib/ui` subsystem.

## Classes

### `MusicControlView`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(interaction: discord.Interaction, song_info: dict, previous_callback, toggle_playback_callback, skip_callback, stop_callback, toggle_mode_callback, toggle_shuffle_callback, show_queue_callback, toggle_autoplay_callback, get_queue_manager, get_state_manager, get_voice_client, get_lang_manager) -> Any`: No description provided.
  - `_get_lang_manager() -> Any`: Get language manager instance
  - `_translate_music(*path, **kwargs) -> str`: 音樂模組專用翻譯方法
  - `_get_fallback_text(key: str, **kwargs) -> str`: 備用文字機制
  - `_get_mode_name(mode: str) -> str`: 獲取播放模式翻譯名稱
  - `_get_shuffle_status(is_enabled: bool) -> str`: 獲取隨機播放狀態文字
  - `update_button_state(update_message: bool) -> Any`: Update button states based on current playback and mode status
  - `start_progress_updater(duration: int) -> Any`: No description provided.
  - `stop_progress_updater() -> Any`: No description provided.
  - `update_progress(duration) -> Any`: No description provided.
  - `update_embed(interaction: discord.Interaction, title: str, color: discord.Color) -> Any`: Update the embed with error handling and message recreation
  - `previous(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: No description provided.
  - `toggle_playback(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: No description provided.
  - `skip(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: No description provided.
  - `stop(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: No description provided.
  - `toggle_mode(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 切換播放模式
  - `toggle_shuffle(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 切換隨機播放
  - `show_queue(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: No description provided.
  - `toggle_autoplay(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 切換自動播放

## Functions

No module-level functions defined in this file.
