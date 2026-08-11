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
  - `runtime` (`Any`): Instance attribute managing runtime.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_tools() -> list`: Return user stats tools.

