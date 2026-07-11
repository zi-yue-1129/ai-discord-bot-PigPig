# File: `cogs/internet_search.py`

## Overview
The Internet Search cog provides advanced web searching, video discovery, and restaurant recommendation capabilities. It integrates Google's Gemini grounding technology for high-accuracy web answers, while maintaining a robust Selenium-based fallback system. It also serves as the entry point for specialized searches like YouTube and the "Eat" (restaurant) system.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `internet_search.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `InternetSearchCog`
Cog for internet search functionality including general web search, YouTube, and food recommendations.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `db` (`Any`): Internal instance state.
  - `recommender` (`Any`): Internal instance state.
  - `provider` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `cog_unload() -> Any`: Close the restaurant provider's HTTP session when the cog is unloaded.
  - `search_command(interaction: discord.Interaction, type: Optional[app_commands.Choice[str]], query: str) -> None`: Slash command wrapper for internet_search.
  - `internet_search(ctx: Any, query: str, search_type: str, message_to_edit: Optional[discord.Message], guild_id: str) -> Any`: High-level search entry point that delegates to specific search functions.
  - `google_search(ctx: Any, query: Any, message_to_edit: Any) -> Any`: Perform a web search using Gemini grounding, with fallback to legacy scraping.
  - `_extract_sources_from_grounding(response: Any) -> Any`: Extract source URLs and titles from Gemini grounding metadata.
  - `_legacy_google_search(ctx: Any, query: Any, message_to_edit: Any) -> Any`: Original Selenium-based Google scraping preserved as a fallback.
  - `get_chrome_options() -> Any`: Configure Chrome options for headless scraping.
  - `youtube_search(ctx: Any, query: Any, message_to_edit: Any) -> Any`: Search for YouTube videos and return a random result from the top hits.
  - `eat_search(ctx: Any, keyword: str, message_to_edit: discord.Message) -> Any`: Food recommendation search using WeightedRecommender and restaurant providers.

## Functions

### `install_driver() -> Any`
Install Chrome driver using ChromeDriverManager.

### `setup(bot: Any) -> Any`
Set up the InternetSearchCog.
