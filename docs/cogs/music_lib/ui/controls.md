# File: `cogs/music_lib/ui/controls.py`

## Overview
Core logic and functionalities for controls.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `MusicControlView`
Represents MusicControlView.

- **Attributes**:
  - `guild` (`Any`): Instance attribute managing guild.
  - `message` (`Any`): Instance attribute managing message.
  - `current_embed` (`Any`): Instance attribute managing current_embed.
  - `song_info` (`Any`): Instance attribute managing song_info.
  - `_is_updating` (`Any`): Instance attribute managing _is_updating.
  - `update_task` (`Any`): Instance attribute managing update_task.
  - `current_position` (`Any`): Instance attribute managing current_position.
  - `previous_callback` (`Any`): Instance attribute managing previous_callback.
  - `toggle_playback_callback` (`Any`): Instance attribute managing toggle_playback_callback.
  - `skip_callback` (`Any`): Instance attribute managing skip_callback.
  - `stop_callback` (`Any`): Instance attribute managing stop_callback.
  - `toggle_mode_callback` (`Any`): Instance attribute managing toggle_mode_callback.
  - `toggle_shuffle_callback` (`Any`): Instance attribute managing toggle_shuffle_callback.
  - `show_queue_callback` (`Any`): Instance attribute managing show_queue_callback.
  - `toggle_autoplay_callback` (`Any`): Instance attribute managing toggle_autoplay_callback.
  - `get_queue_manager` (`Any`): Instance attribute managing get_queue_manager.
  - `get_state_manager` (`Any`): Instance attribute managing get_state_manager.
  - `get_voice_client` (`Any`): Instance attribute managing get_voice_client.
  - `get_lang_manager` (`Any`): Instance attribute managing get_lang_manager.

- **Methods**:
  - `update_button_state(update_message) -> Any`: Update button states based on current playback and mode status
  - `start_progress_updater(duration) -> Any`: Executes start_progress_updater operation.
  - `stop_progress_updater() -> Any`: Executes stop_progress_updater operation.
  - `update_progress(duration) -> Any`: Executes update_progress operation.
  - `update_embed(interaction, title, color) -> Any`: Update the embed with error handling and message recreation
  - `previous(interaction, button) -> Any`: Executes previous operation.
  - `toggle_playback(interaction, button) -> Any`: Executes toggle_playback operation.
  - `skip(interaction, button) -> Any`: Executes skip operation.
  - `stop(interaction, button) -> Any`: Executes stop operation.
  - `toggle_mode(interaction, button) -> Any`: 切換播放模式
  - `toggle_shuffle(interaction, button) -> Any`: 切換隨機播放
  - `show_queue(interaction, button) -> Any`: Executes show_queue operation.
  - `toggle_autoplay(interaction, button) -> Any`: 切換自動播放
