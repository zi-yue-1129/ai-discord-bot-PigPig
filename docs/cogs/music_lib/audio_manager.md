# File: `cogs/music_lib/audio_manager.py`

## Overview
Core file handling responsibilities within the `cogs/music_lib` subsystem.

## Classes

### `AudioManager`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> Any`: No description provided.
  - `create_audio_source(song: Dict[Tuple[str, Any]]) -> FFmpegPCMAudio`: Create an FFmpeg audio source based on song information.
  - `delete_file(guild_id: int, file_path: str) -> Any`: Non-blocking file deletion using asyncio.to_thread.
  - `cleanup_guild_files(guild_id: int, folder: str) -> Any`: Clean up all audio files for a guild.

## Functions

No module-level functions defined in this file.

