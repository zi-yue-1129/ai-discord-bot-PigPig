# File: `cogs/language_manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `language_manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `MissingTranslationError`
Custom exception for missing translation keys

### `TranslationCache`
Multi-layer cache for translations with LRU eviction

- **Attributes**:
  - `_cache` (`Dict[...]`): Instance attribute for _cache.
  - `_max_size` (`Any`): Instance attribute for _max_size.
  - `_access_times` (`Dict[...]`): Instance attribute for _access_times.
  - `_access_counts` (`Dict[...]`): Instance attribute for _access_counts.

- **Methods**:
  - `__init__(max_size) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get(key) -> Optional[...]`: Get cached translation with LRU tracking
  - `put(key, value) -> Any`: Store translation in cache with LRU eviction
  - `_evict_lru() -> Any`: Evict least recently used item
  - `clear() -> Any`: Clear all cached items
  - `size() -> int`: Get current cache size

### `LanguageManager`
Language Management System with modular translation support

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `config_dir` (`Any`): Instance attribute for config_dir.
  - `logger` (`Any`): Instance attribute for logger.
  - `default_lang` (`Any`): Instance attribute for default_lang.
  - `translations` (`Dict[...]`): Instance attribute for translations.
  - `_translation_cache` (`Any`): Instance attribute for _translation_cache.
  - `supported_languages` (`Any`): Instance attribute for supported_languages.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `makedirs` and `TranslationCache`.
  - `_load_translations() -> Any`: Load all language translations, supporting multi-file structure.
  - `_load_directory(lang_code, directory, target_dict) -> Any`: Recursively load all JSON files in a directory.
  - `_get_supported_languages() -> Dict[...]`: Get the list of supported languages.
  - `get_server_lang(guild_id) -> str`: Get the server's language setting.
  - `save_server_lang(guild_id, lang) -> bool`: Save the server's language setting.
  - `_traverse_nested_dict(data, keys) -> Optional[...]`: Traverse a nested dictionary.
  - `translate(guild_id, *keys, **kwargs) -> str`: Translate specified text.
  - `_format_result(result, kwargs) -> str`: Format translation result.
  - `_log_missing_translation(guild_id, lang, keys) -> Any`: Log missing translations.
  - `clear_cache() -> Any`: Clear translation cache.
  - `get_cache_stats() -> Dict[...]`: Get cache statistics.
  - `set_language(interaction, language) -> Any`: Set the display language of the server.
  - `current_language(interaction) -> Any`: Display the current language used by the server.
  - `get_instance(bot) -> Optional[...]`: Get LanguageManager instance.

## Functions

### `setup(bot) -> Any`
Provides `setup` functionality. Internally, it interacts with methods like `add_cog` and `LanguageManager`.
