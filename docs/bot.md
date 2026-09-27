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
  - `loggers` (`Any`): Instance attribute for loggers.
  - `state_manager` (`Any`): Instance attribute for state_manager.
  - `ui_manager` (`Any`): Instance attribute for ui_manager.
  - `stats_collector` (`Any`): Instance attribute for stats_collector.
  - `status_cycle` (`Any`): Instance attribute for status_cycle.

- **Methods**:
  - `__init__(*args, **kwargs) -> Any`: Initialize the PigPig bot instance.
  - `change_status_task() -> Any`: Update bot status every 15 seconds.
  - `_change_presence(*args, **kwargs) -> Any`: Wrapper for change_presence to handle connection errors.
  - `get_logger_for_guild(guild_id) -> Any`: Get or create logger for a specific guild.
  - `setup_logger_for_guild(guild_id) -> Any`: Set up logger for a guild if it doesn't exist.
  - `on_message() -> None`: Handle incoming Discord messages.
  - `on_message_edit(before, after) -> Any`: Handle edited Discord messages.
  - `setup_hook() -> None`: Set up bot before connecting to Discord.
  - `on_ready() -> Any`: Handle bot ready event.
  - `on_error(event_method, *args, **kwargs) -> Any`: Handle errors in event handlers.
  - `on_command_error(ctx, error) -> Any`: Handle errors in command execution.
  - `send_error_report(embed) -> Any`: Handles the `send_error_report` functionality. Internally, it interacts with methods like `get_logger_for_guild` and `get_channel`.
  - `close() -> Any`: Gracefully shut down the bot and all systems.
