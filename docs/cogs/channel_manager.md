# File: `cogs/channel_manager.py`

## Overview
The ChannelManager cog provides comprehensive server and channel permission management capabilities. It enables administrators to configure bot response modes, manage whitelists/blacklists, set channel-specific modes, and control automatic responses on a per-channel basis.

## Classes

### `ChannelManager`
Cog for managing server-wide and channel-specific response modes and permissions.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `data_dir` (`Any`): Instance attribute managing data_dir.
  - `tokens` (`Any`): Instance attribute managing tokens.

- **Methods**:
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `get_config_path(guild_id) -> str`: Get the file path for a guild's configuration.
  - `load_config(guild_id) -> Dict[Tuple[str, Any]]`: Load configuration for a specific guild.
  - `save_config(guild_id, config) -> Any`: Save configuration for a specific guild.
  - `check_admin_permissions(interaction) -> bool`: Check if the user has administrator permissions or is the bot owner.
  - `set_server_mode(interaction, mode) -> Any`: Set the global response mode for the entire server.
  - `set_channel_mode(interaction, channel, mode) -> Any`: Configure a specific mode override for a single channel.
  - `add_channel_command(interaction, channel, list_type) -> Any`: Add a channel to the server's whitelist or blacklist.
  - `remove_channel_command(interaction, channel, list_type) -> Any`: Remove a channel from the server's whitelist or blacklist.
  - `auto_response_command(interaction, channel, enabled) -> Any`: Enable or disable automatic bot responses in a specific channel.
  - `is_allowed_channel(channel, guild_id) -> Tuple[Tuple[bool, bool, Optional[str]]]`: Determine if the bot is allowed to respond in a channel and get its effective mode.  Returns:     A tuple of (is_allowed, auto_response_enabled, effective_mode).

## Functions

### `setup(bot) -> Any`
Set up the ChannelManager cog.

