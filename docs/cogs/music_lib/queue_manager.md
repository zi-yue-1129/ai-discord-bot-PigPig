# File: `cogs/music_lib/queue_manager.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `queue_manager.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `PlayMode`
Class managing PlayMode state and behavior.

### `QueueManager`
Class managing QueueManager state and behavior.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `get_guild_settings(guild_id: int) -> Dict[Tuple]`: Get server playback settings.
  - `get_guild_queue_and_folder(guild_id: int) -> Tuple[Tuple]`: Ensure the server has a unique folder and playlist.
  - `get_queue(guild_id: int) -> asyncio.Queue`: Get the queue for the guild.
  - `clear_guild_data(guild_id: int) -> Any`: Clear the playlist for the specified server.
  - `set_playlist(guild_id: int, video_infos: List[Dict[Tuple]]) -> Any`: Set the server's playlist.
  - `get_next_playlist_songs(guild_id: int, count: int, youtube_manager: Any, folder: Optional[str], interaction: Any) -> List[Dict[Tuple]]`: Get the next song from the playlist.
  - `has_playlist_songs(guild_id: int) -> bool`: Check if there are more songs in the playlist.
  - `toggle_shuffle(guild_id: int) -> bool`: Toggle shuffle playback state.
  - `set_play_mode(guild_id: int, mode: PlayMode) -> Any`: Set the playback mode.
  - `get_play_mode(guild_id: int) -> PlayMode`: Get the playback mode.
  - `is_shuffle_enabled(guild_id: int) -> bool`: Check if shuffle playback is enabled.
  - `copy_queue(guild_id: int, shuffle: bool) -> Tuple[Tuple]`: Copy queue contents without consuming the original queue.
  - `get_queue_snapshot(guild_id: int) -> List[Dict[Tuple]]`: Get a snapshot of the current playback queue.
  - `is_queue_empty(guild_id: int) -> bool`: Check if the queue is empty.
  - `clear_queue(guild_id: int) -> Any`: Clear the playback queue for the specified server.
  - `set_queue(guild_id: int, q: asyncio.Queue) -> Any`: Set the queue for a specific guild.
  - `add_to_queue(guild_id: int, item: Dict[Tuple], force: bool) -> bool`: Add an item to the queue and apply different priority logic based on the adder (user or bot).
  - `add_to_front_of_queue(guild_id: int, item: Dict[Tuple]) -> bool`: Add item to the front of the queue and handle overflow. Returns True on success, False on failure.
  - `get_next_item(guild_id: int) -> Optional[Dict[Tuple]]`: Get the next item from the queue.
  - `enforce_autoplay_limit(guild_id: int, limit: int) -> Any`: Ensure the number of autoplayed songs in the queue does not exceed the specified limit.


## Handwritten Context
# Music Library - Queue Manager

**File:** [`cogs/music_lib/queue_manager.py`](cogs/music_lib/queue_manager.py)

The `QueueManager` is responsible for all logic related to the song queue. It manages the order of songs, playback modes, and shuffle settings for each server.

## `PlayMode(Enum)`

An enumeration that defines the possible playback modes:
*   `NO_LOOP`: The queue plays once.
*   `LOOP_QUEUE`: The entire queue repeats.
*   `LOOP_SINGLE`: The current song repeats.

## `QueueManager` Class

### `__init__(self, bot)`

Initializes the manager, creating dictionaries to hold the queues (`guild_queues`), settings (`guild_settings`), and playlists (`guild_playlists`) for each server.

### Key Methods

#### `get_queue(self, guild_id: int) -> asyncio.Queue`

Retrieves the `asyncio.Queue` instance for a specific guild. If one doesn't exist, it creates a new one.

#### `add_to_queue(self, guild_id, item, ...)`

Adds a song to the queue. This method contains intelligent logic for managing the queue:
*   **Priority for Users:** Songs added by users are prioritized over songs added by the bot's autoplay feature. They are inserted before the first autoplayed song in the queue.
*   **Queue Full Handling:** If the queue is full (`MAX_QUEUE_SIZE`), and a user adds a song, the manager will attempt to remove the last autoplayed song to make space. If a bot tries to add a song to a full queue, the action fails.

#### `add_to_front_of_queue(self, guild_id, item, ...)`

Adds a song to the very beginning of the queue, making it the next song to be played. This is typically used for single-song requests.

#### `get_next_item(self, guild_id: int)`

Retrieves and removes the next song from the front of the queue.

#### Play Mode & Shuffle

*   **`set_play_mode(...)` / `get_play_mode(...)`:** Sets and gets the `PlayMode` for the guild.
*   **`toggle_shuffle(...)` / `is_shuffle_enabled(...)`:** Toggles and checks the shuffle status for the guild.

#### Playlist Handling

The manager distinguishes between the active `queue` and a `playlist`. The `playlist` holds songs from a YouTube playlist that have not yet been added to the active queue.

*   **`set_playlist(self, ...)`:** Stores a list of songs from a YouTube playlist.
*   **`get_next_playlist_songs(self, ...)`:** Retrieves a specified number of songs from the stored playlist to be added to the active queue. This is typically done when the active queue is running low on songs.