# File: `cogs/music_lib/audio_manager.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `audio_manager.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `AudioManager`
Class managing AudioManager state and behavior.

- **Methods**:
  - `__init__() -> Any`: Performs internal processing logic.
  - `create_audio_source(song: Dict[Tuple]) -> FFmpegPCMAudio`: Create an FFmpeg audio source based on song information.
  - `delete_file(guild_id: int, file_path: str) -> Any`: Non-blocking file deletion using asyncio.to_thread.
  - `cleanup_guild_files(guild_id: int, folder: str) -> Any`: Clean up all audio files for a guild.


## Handwritten Context
# Music Library - Audio Manager

**File:** [`cogs/music_lib/audio_manager.py`](cogs/music_lib/audio_manager.py)

The `AudioManager` is a focused utility class responsible for creating audio sources that Discord can play and for managing the cleanup of temporary audio files.

## `AudioManager` Class

### `create_audio_source(self, song: Dict[str, Any]) -> FFmpegPCMAudio`

This is the primary method of the class. It takes a song dictionary and returns a `discord.FFmpegPCMAudio` object, which is the audio source that the bot's voice client plays.

*   **Parameters:**
    *   `song` (Dict[str, Any]): A dictionary containing the song's metadata.
*   **Logic:**
    *   **Live Streams:** If the song dictionary has `is_live` set to `True`, it uses the `stream_url` and applies FFmpeg options optimized for reconnecting to live streams (`-reconnect 1`, etc.).
    *   **Local Files:** If the song is not a live stream, it uses the `file_path` to create a standard audio source for a local file.
*   **Returns:** A playable `FFmpegPCMAudio` source.
*   **Raises:** `ValueError` if the required information (like `stream_url` or `file_path`) is missing from the song dictionary.

### `delete_file(self, guild_id: int, file_path: str)`

An asynchronous method for safely deleting a temporary audio file from the disk. It uses `asyncio.to_thread` to run the file deletion in a separate thread, preventing it from blocking the bot's main event loop.

### `cleanup_guild_files(self, guild_id: int, folder: str)`

A utility method to clean up all temporary audio files for a specific guild. This is typically called when the bot disconnects or the queue is stopped.