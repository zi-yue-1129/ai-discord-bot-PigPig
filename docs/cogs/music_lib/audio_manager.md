# File: `cogs/music_lib/audio_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `AudioManager`
Core class implementation.

- **Attributes**:
  - `_current_audio` (`Dict[Tuple[int, Optional[FFmpegPCMAudio]]]`): Attribute holding _current_audio data.

- **Methods**:
  - `__init__() -> Any`: Executes __init__ logic.
  - `create_audio_source(song: Dict[Tuple[str, Any]]) -> FFmpegPCMAudio`: Create an FFmpeg audio source based on song information.
  - `delete_file(guild_id: int, file_path: str) -> Any`: Non-blocking file deletion using asyncio.to_thread.
  - `cleanup_guild_files(guild_id: int, folder: str) -> Any`: Clean up all audio files for a guild.

## Functions

No top-level functions defined.
