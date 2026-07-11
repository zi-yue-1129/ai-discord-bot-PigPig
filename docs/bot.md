# File: `bot.py`

## Overview
The `PigPig` class is the central orchestrator of the Discord bot. It extends `commands.Bot` and integrates various subsystems like memory, music management, and AI-driven message processing.

This file belongs to the Core System. Its core responsibility is to handle logic related to `bot.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `loggers` (`Any`): Internal instance state.
  - `state_manager` (`Any`): Internal instance state.
  - `ui_manager` (`Any`): Internal instance state.
  - `stats_collector` (`Any`): Internal instance state.
  - `status_cycle` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: Initialize the PigPig bot instance.
  - `change_status_task() -> Any`: Update bot status every 15 seconds.
  - `_change_presence() -> Any`: Wrapper for change_presence to handle connection errors.
  - `get_logger_for_guild(guild_id: Any) -> Any`: Get or create logger for a specific guild.
  - `setup_logger_for_guild(guild_id: Any) -> Any`: Set up logger for a guild if it doesn't exist.
  - `on_message() -> None`: Handle incoming Discord messages.
  - `on_message_edit(before: discord.Message, after: discord.Message) -> Any`: Handle edited Discord messages.
  - `setup_hook() -> None`: Set up bot before connecting to Discord.
  - `on_ready() -> Any`: Handle bot ready event.
  - `on_error(event_method: str) -> Any`: Handle errors in event handlers.
  - `on_command_error(ctx: commands.Context, error: commands.CommandError) -> Any`: Handle errors in command execution.
  - `send_error_report(embed: discord.Embed) -> Any`: Performs internal processing logic.
  - `close() -> Any`: Gracefully shut down the bot and all systems.
