# File: `cogs/channel_manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `channel_manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `ChannelManager`
Cog for managing server-wide and channel-specific response modes and permissions.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `data_dir` (`Any`): Instance attribute for data_dir.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.
  - `tokens` (`Any`): Instance attribute for tokens.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `makedirs`.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `get_config_path(guild_id) -> str`: Get the file path for a guild's configuration.
  - `load_config(guild_id) -> Dict[...]`: Load configuration for a specific guild.
  - `_get_default_config() -> Dict[...]`: Provide a default configuration template.
  - `save_config(guild_id, config) -> Any`: Save configuration for a specific guild.
  - `check_admin_permissions(interaction) -> bool`: Check if the user has administrator permissions or is the bot owner.
  - `set_server_mode(interaction, mode) -> Any`: Set the global response mode for the entire server.
  - `set_channel_mode(interaction, channel, mode) -> Any`: Configure a specific mode override for a single channel.
  - `add_channel_command(interaction, channel, list_type) -> Any`: Add a channel to the server's whitelist or blacklist.
  - `remove_channel_command(interaction, channel, list_type) -> Any`: Remove a channel from the server's whitelist or blacklist.
  - `auto_response_command(interaction, channel, enabled) -> Any`: Enable or disable automatic bot responses in a specific channel.
  - `is_allowed_channel(channel, guild_id) -> Tuple[...]`: Determine if the bot is allowed to respond in a channel and get its effective mode.

## Functions

### `setup(bot) -> Any`
Set up the ChannelManager cog.
