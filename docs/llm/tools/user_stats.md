# File: `llm/tools/user_stats.py`

## Overview
User stats tools for LLM integration.

Provides tools for the AI agent to retrieve user statistics as a text card
(for embedding in conversation) or generate a PNG stats image with word cloud
(sent as a Discord file attachment).

## Classes

### `UserStatsTools`
Container for user statistics query and image generation tools.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(runtime) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `_get_stats_storage() -> Any`: Retrieve StatsStorage from StatsCog.
  - `get_tools() -> list`: Return user stats tools.

## Functions

### `_find_cjk_font() -> Optional[...]`
Find the first available CJK font path on the system.

### `_make_t(bot, guild_id) -> Callable[...]`
Build a translate helper bound to guild_id and the user_stats namespace.

### `_format_text_card(display_name, stats, t) -> str`
Format user stats into a readable text card using localized strings.

### `_hour_to_period_key(hour) -> str`
Return a translation key for the time-of-day period (0-23).

### `_generate_stats_image_sync(display_name, stats, avatar_url, labels) -> bytes`
Generate a PNG stats image with word cloud.
