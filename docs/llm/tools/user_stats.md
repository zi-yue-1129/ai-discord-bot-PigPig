# File: `llm/tools/user_stats.py`

## Overview
The `UserStatsTools` class provides tools for the AI agent to retrieve and visualize user activity patterns within a Discord server. It can generate both a structured text "card" for immediate conversational use and a rich graphical PNG image containing a word cloud and activity charts.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `user_stats.py`, providing vital integrations within the PigPig bot ecosystem.
User stats tools for LLM integration.

Provides tools for the AI agent to retrieve user statistics as a text card
(for embedding in conversation) or generate a PNG stats image with word cloud
(sent as a Discord file attachment).

## Classes

### `UserStatsTools`
Container for user statistics query and image generation tools.

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Performs internal processing logic.
  - `_get_stats_storage() -> Any`: Retrieve StatsStorage from StatsCog.
  - `get_tools() -> list`: Return user stats tools.

## Functions

### `_find_cjk_font() -> Optional[str]`
Find the first available CJK font path on the system.

### `_make_t(bot: Any, guild_id: str) -> Callable[Tuple]`
Build a translate helper bound to guild_id and the user_stats namespace.

### `_format_text_card(display_name: str, stats: Dict[Tuple], t: Callable[Tuple]) -> str`
Format user stats into a readable text card using localized strings.

### `_hour_to_period_key(hour: int) -> str`
Return a translation key for the time-of-day period (0-23).

### `_generate_stats_image_sync(display_name: str, stats: Dict[Tuple], avatar_url: Optional[str], labels: Dict[Tuple]) -> bytes`
Generate a PNG stats image with word cloud.
