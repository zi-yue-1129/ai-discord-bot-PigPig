# File: `cogs/music_lib/state_manager.py`

## Overview
Core file handling responsibilities within the `cogs/music_lib` subsystem.

## Classes

### `PlayerState`
No description provided.

- **Attributes**:
  - `current_song` (`Optional[Dict[Tuple[str, Any]]]`): Class attribute
  - `last_played_song` (`Optional[Dict[Tuple[str, Any]]]`): Class attribute
  - `current_message` (`Optional[discord.Message]`): Class attribute
  - `current_view` (`Optional[Any]`): Class attribute
  - `ui_messages` (`list`): Class attribute
  - `autoplay` (`bool`): Class attribute
  - `player_loop_task` (`Optional[asyncio.Task]`): Class attribute

- **Methods**:
  - None specified.

### `StateManager`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> Any`: No description provided.
  - `get_state(guild_id: int) -> PlayerState`: Get or create state for a guild.
  - `update_state(guild_id: int, **kwargs) -> Any`: Update state attributes for a guild.
  - `cancel_player_loop(guild_id: int) -> Any`: Cancel any running player loop task for a guild.
  - `clear_state(guild_id: int) -> Any`: Clear state for a guild.

## Functions

No module-level functions defined in this file.

