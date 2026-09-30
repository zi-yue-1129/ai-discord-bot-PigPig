# File: `cogs/channel_manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/channel_manager.py`.

## Classes

### `ChannelManager`
Cog for managing server-wide and channel-specific response modes and permissions.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `data_dir` (`Any`): Instance attribute data_dir
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager
  - `tokens` (`Any`): Instance attribute tokens

- **Methods**:
  - `cog_load(self) -> Any`: Initialize LanguageManager when the cog is loaded.
  - `get_config_path(self, guild_id) -> str`: Get the file path for a guild's configuration.
  - `load_config(self, guild_id) -> Dict[str, Any]`: Load configuration for a specific guild.
  - `_get_default_config(self) -> Dict[str, Any]`: Provide a default configuration template.
  - `save_config(self, guild_id, config) -> Any`: Save configuration for a specific guild.
  - `check_admin_permissions(self, interaction) -> bool`: Check if the user has administrator permissions or is the bot owner.
  - `set_server_mode(self, interaction, mode) -> Any`: Set the global response mode for the entire server.
  - `set_channel_mode(self, interaction, channel, mode) -> Any`: Configure a specific mode override for a single channel.
  - `add_channel_command(self, interaction, channel, list_type) -> Any`: Add a channel to the server's whitelist or blacklist.
  - `remove_channel_command(self, interaction, channel, list_type) -> Any`: Remove a channel from the server's whitelist or blacklist.
  - `auto_response_command(self, interaction, channel, enabled) -> Any`: Enable or disable automatic bot responses in a specific channel.
  - `is_allowed_channel(self, channel, guild_id) -> Tuple[bool, bool, Optional[str]]`: Determine if the bot is allowed to respond in a channel and get its effective mode.  Returns:     A tuple of (is_allowed, auto_response_enabled, effective_mode).

## Functions

### `setup(bot) -> Any`
Set up the ChannelManager cog.

