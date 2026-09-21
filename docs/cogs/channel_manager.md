# File: `cogs/channel_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ChannelManager`
Cog for managing server-wide and channel-specific response modes and permissions.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `data_dir` (`Any`): Attribute holding data_dir data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.
  - `tokens` (`Any`): Attribute holding tokens data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `get_config_path(guild_id: str) -> str`: Get the file path for a guild's configuration.
  - `load_config(guild_id: str) -> Dict[Tuple[str, Any]]`: Load configuration for a specific guild.
  - `_get_default_config() -> Dict[Tuple[str, Any]]`: Provide a default configuration template.
  - `save_config(guild_id: str, config: Dict[Tuple[str, Any]]) -> Any`: Save configuration for a specific guild.
  - `check_admin_permissions(interaction: discord.Interaction, defer: bool) -> bool`: Check if the user has administrator permissions or is the bot owner.
  - `set_server_mode(interaction: discord.Interaction, mode: app_commands.Choice[str]) -> Any`: Set the global response mode for the entire server.
  - `set_channel_mode(interaction: discord.Interaction, channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]], mode: app_commands.Choice[str]) -> Any`: Configure a specific mode override for a single channel.
  - `add_channel_command(interaction: discord.Interaction, channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]], list_type: app_commands.Choice[str]) -> Any`: Add a channel to the server's whitelist or blacklist.
  - `remove_channel_command(interaction: discord.Interaction, channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]], list_type: app_commands.Choice[str]) -> Any`: Remove a channel from the server's whitelist or blacklist.
  - `auto_response_command(interaction: discord.Interaction, channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]], enabled: bool) -> Any`: Enable or disable automatic bot responses in a specific channel.
  - `is_allowed_channel(channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]], guild_id: str) -> Tuple[Tuple[bool, bool, Optional[str]]]`: Determine if the bot is allowed to respond in a channel and get its effective mode.

## Functions

### `setup(bot) -> Any`
Set up the ChannelManager cog.
