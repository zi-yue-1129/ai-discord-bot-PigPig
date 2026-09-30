# File: `cogs/music_lib/queue_manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/music_lib/queue_manager.py`.

## Classes

### `PlayMode`
Class representing PlayMode.

- **Attributes**:
  - `NO_LOOP` (`Any`): Attribute NO_LOOP
  - `LOOP_QUEUE` (`Any`): Attribute LOOP_QUEUE
  - `LOOP_SINGLE` (`Any`): Attribute LOOP_SINGLE

- **Methods**:
  - None

### `QueueManager`
Class representing QueueManager.

- **Attributes**:
  - `MAX_QUEUE_SIZE` (`Any`): Attribute MAX_QUEUE_SIZE
  - `bot` (`Any`): Instance attribute bot
  - `guild_queues` (`Dict[int, asyncio.Queue]`): Instance attribute guild_queues
  - `guild_settings` (`Dict[int, Dict[str, Any]]`): Instance attribute guild_settings
  - `guild_playlists` (`Dict[int, List[Dict[str, Any]]]`): Instance attribute guild_playlists

- **Methods**:
  - `get_guild_settings(self, guild_id) -> Dict[str, Any]`: Get server playback settings.
  - `get_guild_queue_and_folder(self, guild_id) -> Tuple[asyncio.Queue, str]`: Ensure the server has a unique folder and playlist.
  - `get_queue(self, guild_id) -> asyncio.Queue`: Get the queue for the guild.
  - `clear_guild_data(self, guild_id) -> Any`: Clear the playlist for the specified server.
  - `set_playlist(self, guild_id, video_infos) -> Any`: Set the server's playlist.
  - `get_next_playlist_songs(self, guild_id, count, youtube_manager, folder, interaction) -> List[Dict[str, Any]]`: Get the next song from the playlist.
  - `has_playlist_songs(self, guild_id) -> bool`: Check if there are more songs in the playlist.
  - `toggle_shuffle(self, guild_id) -> bool`: Toggle shuffle playback state.
  - `set_play_mode(self, guild_id, mode) -> Any`: Set the playback mode.
  - `get_play_mode(self, guild_id) -> PlayMode`: Get the playback mode.
  - `is_shuffle_enabled(self, guild_id) -> bool`: Check if shuffle playback is enabled.
  - `copy_queue(self, guild_id, shuffle) -> Tuple[List[Dict[str, Any]], asyncio.Queue]`: Copy queue contents without consuming the original queue.
  - `get_queue_snapshot(self, guild_id) -> List[Dict[str, Any]]`: Get a snapshot of the current playback queue.
  - `is_queue_empty(self, guild_id) -> bool`: Check if the queue is empty.
  - `clear_queue(self, guild_id) -> Any`: Clear the playback queue for the specified server.
  - `set_queue(self, guild_id, q) -> Any`: Set the queue for a specific guild.
  - `add_to_queue(self, guild_id, item, force) -> bool`: Add an item to the queue and apply different priority logic based on the adder (user or bot). Returns True on success, False on failure.
  - `add_to_front_of_queue(self, guild_id, item) -> bool`: Add item to the front of the queue and handle overflow. Returns True on success, False on failure.
  - `get_next_item(self, guild_id) -> Optional[Dict[str, Any]]`: Get the next item from the queue.
  - `enforce_autoplay_limit(self, guild_id, limit) -> Any`: Ensure the number of autoplayed songs in the queue does not exceed the specified limit.

## Functions

None

