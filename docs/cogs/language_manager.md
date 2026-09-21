# File: `cogs/language_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `MissingTranslationError`
Custom exception for missing translation keys

- **Attributes**:
  - None specified.

- **Methods**:
  - None specified.

### `TranslationCache`
Multi-layer cache for translations with LRU eviction

- **Attributes**:
  - `_cache` (`Dict[Tuple[str, str]]`): Attribute holding _cache data.
  - `_max_size` (`Any`): Attribute holding _max_size data.
  - `_access_times` (`Dict[Tuple[str, float]]`): Attribute holding _access_times data.
  - `_access_counts` (`Dict[Tuple[str, int]]`): Attribute holding _access_counts data.

- **Methods**:
  - `__init__(max_size: int) -> Any`: Executes __init__ logic.
  - `get(key: str) -> Optional[str]`: Get cached translation with LRU tracking
  - `put(key: str, value: str) -> Any`: Store translation in cache with LRU eviction
  - `_evict_lru() -> Any`: Evict least recently used item
  - `clear() -> Any`: Clear all cached items
  - `size() -> int`: Get current cache size

### `LanguageManager`
Language Management System with modular translation support

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `config_dir` (`Any`): Attribute holding config_dir data.
  - `logger` (`Any`): Attribute holding logger data.
  - `default_lang` (`Any`): Attribute holding default_lang data.
  - `translations` (`Dict[Tuple[str, Dict[Tuple[str, Any]]]]`): Attribute holding translations data.
  - `_translation_cache` (`Any`): Attribute holding _translation_cache data.
  - `supported_languages` (`Any`): Attribute holding supported_languages data.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: Executes __init__ logic.
  - `_load_translations() -> Any`: Load all language translations, supporting multi-file structure.
  - `_load_directory(lang_code: str, directory: str, target_dict: Dict[Tuple[str, Any]]) -> Any`: Recursively load all JSON files in a directory.
  - `_get_supported_languages() -> Dict[Tuple[str, str]]`: Get the list of supported languages.
  - `get_server_lang(guild_id: str) -> str`: Get the server's language setting.
  - `save_server_lang(guild_id: str, lang: str) -> bool`: Save the server's language setting.
  - `_traverse_nested_dict(data: Dict[Tuple[str, Any]], keys: List[str]) -> Optional[Any]`: Traverse a nested dictionary.
  - `translate(guild_id: str, *keys, **kwargs) -> str`: Translate specified text.
  - `_format_result(result: str, kwargs: Dict[Tuple[str, Any]]) -> str`: Format translation result.
  - `_log_missing_translation(guild_id: str, lang: str, keys: List[str]) -> Any`: Log missing translations.
  - `clear_cache() -> Any`: Clear translation cache.
  - `get_cache_stats() -> Dict[Tuple[str, Any]]`: Get cache statistics.
  - `set_language(interaction: discord.Interaction, language: str) -> Any`: Set the display language of the server.
  - `current_language(interaction: discord.Interaction) -> Any`: Display the current language used by the server.
  - `get_instance(bot: commands.Bot) -> Optional[LanguageManager]`: Get LanguageManager instance.

## Functions

### `setup(bot: commands.Bot) -> Any`
Performs setup operations.
