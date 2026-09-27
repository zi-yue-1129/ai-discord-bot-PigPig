# File: `cogs/internet_search.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `internet_search` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `InternetSearchCog`
Cog for internet search functionality including general web search, YouTube, and food recommendations.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `db` (`Any`): Instance attribute for db.
  - `recommender` (`Any`): Instance attribute for recommender.
  - `provider` (`Any`): Instance attribute for provider.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `DB` and `WeightedRecommender`.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `cog_unload() -> Any`: Close the restaurant provider's HTTP session when the cog is unloaded.
  - `search_command(interaction, type, query) -> None`: Slash command wrapper for internet_search.
  - `internet_search(ctx, query, search_type, message_to_edit, guild_id) -> Any`: High-level search entry point that delegates to specific search functions.
  - `google_search(ctx, query, message_to_edit) -> Any`: Perform a web search using Gemini grounding, with fallback to legacy scraping.
  - `_extract_sources_from_grounding(response) -> Any`: Extract source URLs and titles from Gemini grounding metadata.
  - `_legacy_google_search(ctx, query, message_to_edit) -> Any`: Original Selenium-based Google scraping preserved as a fallback.
  - `get_chrome_options() -> Any`: Configure Chrome options for headless scraping.
  - `youtube_search(ctx, query, message_to_edit) -> Any`: Search for YouTube videos and return a random result from the top hits.
  - `eat_search(ctx, keyword, message_to_edit) -> Any`: Food recommendation search using WeightedRecommender and restaurant providers.

## Functions

### `install_driver() -> Any`
Install Chrome driver using ChromeDriverManager.

### `setup(bot) -> Any`
Set up the InternetSearchCog.
