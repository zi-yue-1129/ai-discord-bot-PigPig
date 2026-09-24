# File: `cogs/music_lib/queue_manager.py`

## Overview
Core file handling responsibilities within the `cogs/music_lib` subsystem.

## Classes

### `PlayMode`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - None specified.

### `QueueManager`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: No description provided.
  - `get_guild_settings(guild_id: int) -> Dict[Tuple[str, Any]]`: Get server playback settings.
  - `get_guild_queue_and_folder(guild_id: int) -> Tuple[Tuple[asyncio.Queue, str]]`: Ensure the server has a unique folder and playlist.
  - `get_queue(guild_id: int) -> asyncio.Queue`: Get the queue for the guild.
  - `clear_guild_data(guild_id: int) -> Any`: Clear the playlist for the specified server.
  - `set_playlist(guild_id: int, video_infos: List[Dict[Tuple[str, Any]]]) -> Any`: Set the server's playlist.
  - `get_next_playlist_songs(guild_id: int, count: int, youtube_manager, folder: Optional[str], interaction) -> List[Dict[Tuple[str, Any]]]`: Get the next song from the playlist.
  - `has_playlist_songs(guild_id: int) -> bool`: Check if there are more songs in the playlist.
  - `toggle_shuffle(guild_id: int) -> bool`: Toggle shuffle playback state.
  - `set_play_mode(guild_id: int, mode: PlayMode) -> Any`: Set the playback mode.
  - `get_play_mode(guild_id: int) -> PlayMode`: Get the playback mode.
  - `is_shuffle_enabled(guild_id: int) -> bool`: Check if shuffle playback is enabled.
  - `copy_queue(guild_id: int, shuffle: bool) -> Tuple[Tuple[List[Dict[Tuple[str, Any]]], asyncio.Queue]]`: Copy queue contents without consuming the original queue.
  - `get_queue_snapshot(guild_id: int) -> List[Dict[Tuple[str, Any]]]`: Get a snapshot of the current playback queue.
  - `is_queue_empty(guild_id: int) -> bool`: Check if the queue is empty.
  - `clear_queue(guild_id: int) -> Any`: Clear the playback queue for the specified server.
  - `set_queue(guild_id: int, q: asyncio.Queue) -> Any`: Set the queue for a specific guild.
  - `add_to_queue(guild_id: int, item: Dict[Tuple[str, Any]], force: bool) -> bool`: Add an item to the queue and apply different priority logic based on the adder (user or bot).
  - `add_to_front_of_queue(guild_id: int, item: Dict[Tuple[str, Any]]) -> bool`: Add item to the front of the queue and handle overflow. Returns True on success, False on failure.
  - `get_next_item(guild_id: int) -> Optional[Dict[Tuple[str, Any]]]`: Get the next item from the queue.
  - `enforce_autoplay_limit(guild_id: int, limit: int) -> Any`: Ensure the number of autoplayed songs in the queue does not exceed the specified limit.

## Functions

No module-level functions defined in this file.

