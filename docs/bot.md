# File: `bot.py`

## Overview
Discord bot main module.

This module contains the main bot class and configuration for a Discord bot
with music playback, message handling, and logging capabilities.

## Classes

### `PigPig`
Main Discord bot class with music, messaging, and logging features.

This bot extends discord.ext.commands.Bot with additional functionality including:
- Per-guild logging system
- Music playback state management
- AI-powered message handling
- Performance monitoring
- Dynamic status updates

Attributes:
    loggers (dict): Dictionary mapping guild names to their logger instances.
    state_manager (StateManager): Manager for music playback states.
    ui_manager (UIManager): Manager for music player UI components.
    status_cycle (itertools.cycle): Cycle iterator for rotating bot status messages.
    message_handler (MessageHandler): Handler for processing Discord messages.

- **Attributes**:
  - `loggers` (`Any`): Attribute holding loggers data.
  - `state_manager` (`Any`): Attribute holding state_manager data.
  - `ui_manager` (`Any`): Attribute holding ui_manager data.
  - `stats_collector` (`Any`): Attribute holding stats_collector data.
  - `status_cycle` (`Any`): Attribute holding status_cycle data.

- **Methods**:
  - `__init__(*args, **kwargs) -> Any`: Initialize the PigPig bot instance.
  - `change_status_task() -> Any`: Update bot status every 15 seconds.
  - `_change_presence(*args, **kwargs) -> Any`: Wrapper for change_presence to handle connection errors.
  - `get_logger_for_guild(guild_id) -> Any`: Get or create logger for a specific guild.
  - `setup_logger_for_guild(guild_id) -> Any`: Set up logger for a guild if it doesn't exist.
  - `on_message(message: discord.Message) -> None`: Handle incoming Discord messages.
  - `on_message_edit(before: discord.Message, after: discord.Message) -> Any`: Handle edited Discord messages.
  - `setup_hook() -> None`: Set up bot before connecting to Discord.
  - `on_ready() -> Any`: Handle bot ready event.
  - `on_error(event_method: str, *args, **kwargs) -> Any`: Handle errors in event handlers.
  - `on_command_error(ctx: commands.Context, error: commands.CommandError) -> Any`: Handle errors in command execution.
  - `send_error_report(embed: discord.Embed) -> Any`: Executes send_error_report logic.
  - `close() -> Any`: Gracefully shut down the bot and all systems.

## Functions

No top-level functions defined.
