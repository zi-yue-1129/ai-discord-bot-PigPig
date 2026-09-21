# File: `cogs/internet_search.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `InternetSearchCog`
Cog for internet search functionality including general web search, YouTube, and food recommendations.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `db` (`Any`): Attribute holding db data.
  - `recommender` (`Any`): Attribute holding recommender data.
  - `provider` (`Any`): Attribute holding provider data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `cog_unload() -> Any`: Close the restaurant provider's HTTP session when the cog is unloaded.
  - `search_command(interaction: discord.Interaction, type: Optional[app_commands.Choice[str]], query: str) -> None`: Slash command wrapper for internet_search.
  - `internet_search(ctx, query: str, search_type: str, message_to_edit: Optional[discord.Message], guild_id: str) -> Any`: High-level search entry point that delegates to specific search functions.
  - `google_search(ctx, query, message_to_edit) -> Any`: Perform a web search using Gemini grounding, with fallback to legacy scraping.
  - `_extract_sources_from_grounding(response) -> Any`: Extract source URLs and titles from Gemini grounding metadata.
  - `_legacy_google_search(ctx, query, message_to_edit) -> Any`: Original Selenium-based Google scraping preserved as a fallback.
  - `get_chrome_options() -> Any`: Configure Chrome options for headless scraping.
  - `youtube_search(ctx, query, message_to_edit) -> Any`: Search for YouTube videos and return a random result from the top hits.
  - `eat_search(ctx, keyword: str, message_to_edit: discord.Message) -> Any`: Food recommendation search using WeightedRecommender and restaurant providers.

## Functions

### `install_driver() -> Any`
Install Chrome driver using ChromeDriverManager.

### `setup(bot) -> Any`
Set up the InternetSearchCog.
