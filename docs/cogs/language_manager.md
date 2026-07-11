# File: `cogs/language_manager.py`

## Overview
The Language Manager cog is the backbone of the bot's multi-language localization system. It manages server-specific language preferences, loads translation data from a structured file system, and provides a centralized API for translating UI elements, command responses, and system messages.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `language_manager.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `MissingTranslationError`
Custom exception for missing translation keys

### `TranslationCache`
Multi-layer cache for translations with LRU eviction

- **Attributes**:
  - `_max_size` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(max_size: int) -> Any`: Performs internal processing logic.
  - `get(key: str) -> Optional[str]`: Get cached translation with LRU tracking
  - `put(key: str, value: str) -> Any`: Store translation in cache with LRU eviction
  - `_evict_lru() -> Any`: Evict least recently used item
  - `clear() -> Any`: Clear all cached items
  - `size() -> int`: Get current cache size

### `LanguageManager`
Language Management System with modular translation support

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `config_dir` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `default_lang` (`Any`): Internal instance state.
  - `_translation_cache` (`Any`): Internal instance state.
  - `supported_languages` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: Performs internal processing logic.
  - `_load_translations() -> Any`: Load all language translations, supporting multi-file structure.
  - `_load_directory(lang_code: str, directory: str, target_dict: Dict[Tuple]) -> Any`: Recursively load all JSON files in a directory.
  - `_get_supported_languages() -> Dict[Tuple]`: Get the list of supported languages.
  - `get_server_lang(guild_id: str) -> str`: Get the server's language setting.
  - `save_server_lang(guild_id: str, lang: str) -> bool`: Save the server's language setting.
  - `_traverse_nested_dict(data: Dict[Tuple], keys: List[str]) -> Optional[Any]`: Traverse a nested dictionary.
  - `translate(guild_id: str) -> str`: Translate specified text.
  - `_format_result(result: str, kwargs: Dict[Tuple]) -> str`: Format translation result.
  - `_log_missing_translation(guild_id: str, lang: str, keys: List[str]) -> Any`: Log missing translations.
  - `clear_cache() -> Any`: Clear translation cache.
  - `get_cache_stats() -> Dict[Tuple]`: Get cache statistics.
  - `set_language(interaction: discord.Interaction, language: str) -> Any`: Set the display language of the server.
  - `current_language(interaction: discord.Interaction) -> Any`: Display the current language used by the server.
  - `get_instance(bot: commands.Bot) -> Optional[LanguageManager]`: Get LanguageManager instance.

## Functions

### `setup(bot: commands.Bot) -> Any`
Performs internal processing logic.
