# File: `cogs/music_lib/audio_manager.py`

## Overview
Core responsibilities and logic for `cogs/music_lib/audio_manager.py`. This module is part of the cogs subsystem and handles the associated business logic, state management, and integrations.

## Classes

### `AudioManager`
Manages the state and core operations for AudioManager.

- **Methods**:
  - `create_audio_source(song) -> FFmpegPCMAudio`: Create an FFmpeg audio source based on song information.
  - `delete_file(guild_id, file_path) -> Any`: Non-blocking file deletion using asyncio.to_thread.
  - `cleanup_guild_files(guild_id, folder) -> Any`: Clean up all audio files for a guild.

