# File: `cogs/music_lib/audio_manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `audio_manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `AudioManager`
Represents the `AudioManager` class in the system.

- **Attributes**:
  - `_current_audio` (`Dict[...]`): Instance attribute for _current_audio.

- **Methods**:
  - `__init__() -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `create_audio_source(song) -> FFmpegPCMAudio`: Create an FFmpeg audio source based on song information.
  - `delete_file(guild_id, file_path) -> Any`: Non-blocking file deletion using asyncio.to_thread.
  - `cleanup_guild_files(guild_id, folder) -> Any`: Clean up all audio files for a guild.
