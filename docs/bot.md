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
  - `loggers` (`Any`): Instance attribute managing loggers.
  - `state_manager` (`Any`): Instance attribute managing state_manager.
  - `ui_manager` (`Any`): Instance attribute managing ui_manager.
  - `stats_collector` (`Any`): Instance attribute managing stats_collector.
  - `status_cycle` (`Any`): Instance attribute managing status_cycle.

- **Methods**:
  - `change_status_task() -> Any`: Update bot status every 15 seconds.  Cycles through predefined status messages, replacing placeholders with current bot statistics (e.g., number of guilds).  Note:     This is a discord.ext.tasks loop that runs continuously.
  - `get_logger_for_guild(guild_id) -> Any`: Get or create logger for a specific guild.  Args:     guild_id (str): ID of the guild to get logger for.      Returns:     logging.Logger: Logger instance for the specified guild.      Note:     Creates a new logger if one doesn't exist for the guild.
  - `setup_logger_for_guild(guild_id) -> Any`: Set up logger for a guild if it doesn't exist.
  - `on_message() -> None`: Handle incoming Discord messages.  Processes messages by: 1. Setting up guild-specific logging 2. Logging message details 3. Ignoring bot messages 4. Processing commands 5. Handling special channel modes (story mode) 6. Delegating to message handler for AI responses  Args:     message (discord.Message): The incoming Discord message object.      Returns:     None      Note:     - Ignores messages from DMs (no guild)     - Ignores messages from other bots     - Checks channel permissions and modes before processing
  - `on_message_edit(before, after) -> Any`: Handle edited Discord messages.  When a message mentioning the bot is edited: 1. Logs the edit details 2. Deletes the bot's previous reply to the original message 3. Generates a new response to the edited message 4. Handles story mode channels specially  Args:     before (discord.Message): The message before editing.     after (discord.Message): The message after editing.      Returns:     None      Note:     - Ignores edits in DMs     - Ignores edits from bots     - Only responds to messages that mention the bot     - Searches last 50 messages to find bot's previous reply
  - `setup_hook() -> None`: Set up bot before connecting to Discord.  This method is called automatically by discord.py and performs: 1. Loading all cog modules from the cogs folder 2. Initializing MessageHandler 3. Starting IPC server if enabled 4. Updating version in settings 5. Syncing command tree with Discord  Returns:     None      Note:     - Filters out __init__.py, private modules (_*), and hidden files (.*)      - Prints success/failure for each cog load attempt     - Initializes performance monitoring
  - `on_ready() -> Any`: Handle bot ready event.  Called when the bot has successfully connected to Discord. Performs: 1. Prints bot information (name, ID, versions) 2. Collects and saves guild/channel information to JSON 3. Sets up loggers for all guilds 4. Updates client ID in tokens 5. Starts status update task  Returns:     None      Note:     - Creates logs/guilds_and_channels.json with server structure     - Initializes logger for each guild the bot is in     - Starts periodic status updates if not already running
  - `on_error(event_method, *args, **kwargs) -> Any`: Handle errors in event handlers.  Called when an exception occurs in an event handler. Performs: 1. Gets appropriate logger 2. Logs error details and traceback 3. Reports error through error reporting system  Args:     event_method (str): Name of the event method where error occurred.     *args: Variable length argument list from the event.     **kwargs: Arbitrary keyword arguments from the event.      Returns:     None      Note:     - Uses "Bot" as guild name for logger if guild context unavailable     - Prints to console in addition to logging to file
  - `on_command_error(ctx, error) -> Any`: Handle errors in command execution.  Called when a command raises an exception. Performs: 1. Ignores certain expected errors (CommandNotFound, DisabledCommand) 2. Logs error details with full traceback 3. Reports error through error reporting system 4. Sends error message to channel  Args:     ctx (commands.Context): The invocation context where error occurred.     error (commands.CommandError): The exception that was raised.      Returns:     None      Note:     - Uses guild name for logger, or "DirectMessage" for DMs     - Gracefully handles failures in error message sending     - Prints to console as fallback if logger unavailable
  - `send_error_report(embed) -> Any`: Executes logic for send_error_report.
  - `close() -> Any`: Gracefully shut down the bot and all systems.  Performs cleanup in the following order: 1. Calls parent class close() to disconnect from Discord 2. Cancels all pending asyncio tasks 3. Shuts down default executor thread pool  Returns:     None      Note:     - Prevents "Task exception was never retrieved" warnings     - Avoids threading._shutdown hanging issues     - Handles exceptions during shutdown gracefully     - Should be called before program termination

