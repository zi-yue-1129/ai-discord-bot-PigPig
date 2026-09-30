# File: `cogs/music_lib/audio_manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/music_lib/audio_manager.py`.

## Classes

### `AudioManager`
Class representing AudioManager.

- **Attributes**:
  - `_current_audio` (`Dict[int, Optional[FFmpegPCMAudio]]`): Instance attribute _current_audio

- **Methods**:
  - `create_audio_source(self, song) -> FFmpegPCMAudio`: Create an FFmpeg audio source based on song information.
  - `delete_file(self, guild_id, file_path) -> Any`: Non-blocking file deletion using asyncio.to_thread.
  - `cleanup_guild_files(self, guild_id, folder) -> Any`: Clean up all audio files for a guild.

## Functions

None

