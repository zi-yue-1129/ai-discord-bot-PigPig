# File: `bot.py`

## Overview
Discord bot main module.

## Classes

### `PigPig`
Main Discord bot class with music, messaging, and logging features.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(*args, **kwargs) -> Any`: Initialize the PigPig bot instance.
  - `change_status_task() -> Any`: Update bot status every 15 seconds.
  - `_change_presence(*args, **kwargs) -> Any`: Wrapper for change_presence to handle connection errors.
  - `get_logger_for_guild(guild_id) -> Any`: Get or create logger for a specific guild.
  - `setup_logger_for_guild(guild_id) -> Any`: Set up logger for a guild if it doesn't exist.
  - `on_message(self, message: discord.Message) -> None`: Handle incoming Discord messages.
  - `on_message_edit(before: discord.Message, after: discord.Message) -> Any`: Handle edited Discord messages.
  - `setup_hook() -> None`: Set up bot before connecting to Discord.
  - `on_ready() -> Any`: Handle bot ready event.
  - `on_error(event_method: str, *args, **kwargs) -> Any`: Handle errors in event handlers.
  - `on_command_error(ctx: commands.Context, error: commands.CommandError) -> Any`: Handle errors in command execution.
  - `send_error_report(embed: discord.Embed) -> Any`: No description provided.
  - `close() -> Any`: Gracefully shut down the bot and all systems.

## Functions

No module-level functions defined in this file.

