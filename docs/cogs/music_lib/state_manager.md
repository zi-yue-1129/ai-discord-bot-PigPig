# File: `cogs/music_lib/state_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `PlayerState`
Core class implementation.

- **Attributes**:
  - `current_song` (`Optional[Dict[Tuple[str, Any]]]`): Attribute holding current_song data.
  - `last_played_song` (`Optional[Dict[Tuple[str, Any]]]`): Attribute holding last_played_song data.
  - `current_message` (`Optional[discord.Message]`): Attribute holding current_message data.
  - `current_view` (`Optional[Any]`): Attribute holding current_view data.
  - `ui_messages` (`list`): Attribute holding ui_messages data.
  - `autoplay` (`bool`): Attribute holding autoplay data.
  - `player_loop_task` (`Optional[asyncio.Task]`): Attribute holding player_loop_task data.

- **Methods**:
  - None specified.

### `StateManager`
Core class implementation.

- **Attributes**:
  - `states` (`Dict[Tuple[int, PlayerState]]`): Attribute holding states data.

- **Methods**:
  - `__init__() -> Any`: Executes __init__ logic.
  - `get_state(guild_id: int) -> PlayerState`: Get or create state for a guild.
  - `update_state(guild_id: int, **kwargs) -> Any`: Update state attributes for a guild.
  - `cancel_player_loop(guild_id: int) -> Any`: Cancel any running player loop task for a guild.
  - `clear_state(guild_id: int) -> Any`: Clear state for a guild.

## Functions

No top-level functions defined.
