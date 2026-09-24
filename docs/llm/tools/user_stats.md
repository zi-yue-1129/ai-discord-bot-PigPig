# File: `llm/tools/user_stats.py`

## Overview
User stats tools for LLM integration.

## Classes

### `UserStatsTools`
Container for user statistics query and image generation tools.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(runtime: str) -> None`: No description provided.
  - `_get_stats_storage() -> Any`: Retrieve StatsStorage from StatsCog.
  - `get_tools() -> list`: Return user stats tools.

## Functions

### `_find_cjk_font() -> Optional[str]`
Find the first available CJK font path on the system.

### `_make_t(bot: Any, guild_id: str) -> Callable[Tuple[ellipsis, str]]`
Build a translate helper bound to guild_id and the user_stats namespace.

### `_format_text_card(display_name: str, stats: Dict[Tuple[str, Any]], t: Callable[Tuple[ellipsis, str]]) -> str`
Format user stats into a readable text card using localized strings.

### `_hour_to_period_key(hour: int) -> str`
Return a translation key for the time-of-day period (0-23).

### `_generate_stats_image_sync(display_name: str, stats: Dict[Tuple[str, Any]], avatar_url: Optional[str], labels: Dict[Tuple[str, str]]) -> bytes`
Generate a PNG stats image with word cloud.

