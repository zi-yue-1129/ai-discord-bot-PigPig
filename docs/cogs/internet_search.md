# File: `cogs/internet_search.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/internet_search.py`.

## Classes

### `InternetSearchCog`
Cog for internet search functionality including general web search, YouTube, and food recommendations.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `db` (`Any`): Instance attribute db
  - `recommender` (`Any`): Instance attribute recommender
  - `provider` (`Any`): Instance attribute provider
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `cog_load(self) -> Any`: Initialize LanguageManager when the cog is loaded.
  - `cog_unload(self) -> Any`: Close the restaurant provider's HTTP session when the cog is unloaded.
  - `search_command(self, interaction, type, query) -> None`: Slash command wrapper for internet_search.  Delegates to internet_search and returns the textual result if available. Ensures Discord message length limits are respected by splitting long markdown outputs into multiple followups.
  - `internet_search(self, ctx, query, search_type, message_to_edit, guild_id) -> Any`: High-level search entry point that delegates to specific search functions.
  - `google_search(self, ctx, query, message_to_edit) -> Any`: Perform a web search using Gemini grounding, with fallback to legacy scraping.
  - `_extract_sources_from_grounding(self, response) -> Any`: Extract source URLs and titles from Gemini grounding metadata.
  - `_legacy_google_search(self, ctx, query, message_to_edit) -> Any`: Original Selenium-based Google scraping preserved as a fallback.
  - `get_chrome_options() -> Any`: Configure Chrome options for headless scraping.
  - `youtube_search(self, ctx, query, message_to_edit) -> Any`: Search for YouTube videos and return a random result from the top hits.
  - `eat_search(self, ctx, keyword, message_to_edit) -> Any`: Food recommendation search using WeightedRecommender and restaurant providers.

## Functions

### `install_driver() -> Any`
Install Chrome driver using ChromeDriverManager.

### `setup(bot) -> Any`
Set up the InternetSearchCog.

