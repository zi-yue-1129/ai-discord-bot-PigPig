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
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Executes __init__ logic.
  - `_get_stats_storage() -> Any`: Retrieve StatsStorage from StatsCog.
  - `get_tools() -> list`: Return user stats tools.

## Functions

### `_find_cjk_font() -> Optional[str]`
Find the first available CJK font path on the system.

### `_make_t(bot: Any, guild_id: str) -> Callable[Tuple[Ellipsis, str]]`
Build a translate helper bound to guild_id and the user_stats namespace.

Falls back to zh_TW hardcoded strings when LanguageManager is unavailable.

### `_format_text_card(display_name: str, stats: Dict[Tuple[str, Any]], t: Callable[Tuple[Ellipsis, str]]) -> str`
Format user stats into a readable text card using localized strings.

### `_hour_to_period_key(hour: int) -> str`
Return a translation key for the time-of-day period (0-23).

### `_generate_stats_image_sync(display_name: str, stats: Dict[Tuple[str, Any]], avatar_url: Optional[str], labels: Dict[Tuple[str, str]]) -> bytes`
Generate a PNG stats image with word cloud.

Args:
    labels: Pre-resolved localized strings (header, top_channels,
            activity_by_hour, top_emojis_prefix).

Returns raw PNG bytes.
