# File: `cogs/internet_search.py`

## Overview
The Internet Search cog provides advanced web searching, video discovery, and restaurant recommendation capabilities. It integrates Google's Gemini grounding technology for high-accuracy web answers, while maintaining a robust Selenium-based fallback system. It also serves as the entry point for specialized searches like YouTube and the "Eat" (restaurant) system.

## Classes

### `InternetSearchCog`
Cog for internet search functionality including general web search, YouTube, and food recommendations.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `db` (`Any`): Instance attribute managing db.
  - `recommender` (`Any`): Instance attribute managing recommender.
  - `provider` (`Any`): Instance attribute managing provider.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `cog_unload() -> Any`: Close the restaurant provider's HTTP session when the cog is unloaded.
  - `search_command(interaction, type, query) -> None`: Slash command wrapper for internet_search.  Delegates to internet_search and returns the textual result if available. Ensures Discord message length limits are respected by splitting long markdown outputs into multiple followups.
  - `internet_search(ctx, query, search_type, message_to_edit, guild_id) -> Any`: High-level search entry point that delegates to specific search functions.
  - `google_search(ctx, query, message_to_edit) -> Any`: Perform a web search using Gemini grounding, with fallback to legacy scraping.
  - `get_chrome_options() -> Any`: Configure Chrome options for headless scraping.
  - `youtube_search(ctx, query, message_to_edit) -> Any`: Search for YouTube videos and return a random result from the top hits.
  - `eat_search(ctx, keyword, message_to_edit) -> Any`: Food recommendation search using WeightedRecommender and restaurant providers.

## Functions

### `install_driver() -> Any`
Install Chrome driver using ChromeDriverManager.

### `setup(bot) -> Any`
Set up the InternetSearchCog.

