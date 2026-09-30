# File: `cogs/language_manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/language_manager.py`.

## Classes

### `MissingTranslationError`
Custom exception for missing translation keys

- **Attributes**:
  - None

- **Methods**:
  - None

### `TranslationCache`
Multi-layer cache for translations with LRU eviction

- **Attributes**:
  - `_cache` (`Dict[str, str]`): Instance attribute _cache
  - `_max_size` (`Any`): Instance attribute _max_size
  - `_access_times` (`Dict[str, float]`): Instance attribute _access_times
  - `_access_counts` (`Dict[str, int]`): Instance attribute _access_counts

- **Methods**:
  - `get(self, key) -> Optional[str]`: Get cached translation with LRU tracking
  - `put(self, key, value) -> Any`: Store translation in cache with LRU eviction
  - `_evict_lru(self) -> Any`: Evict least recently used item
  - `clear(self) -> Any`: Clear all cached items
  - `size(self) -> int`: Get current cache size

### `LanguageManager`
Language Management System with modular translation support

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `config_dir` (`Any`): Instance attribute config_dir
  - `logger` (`Any`): Instance attribute logger
  - `default_lang` (`Any`): Instance attribute default_lang
  - `translations` (`Dict[str, Dict[str, Any]]`): Instance attribute translations
  - `_translation_cache` (`Any`): Instance attribute _translation_cache
  - `supported_languages` (`Any`): Instance attribute supported_languages

- **Methods**:
  - `_load_translations(self) -> Any`: Load all language translations, supporting multi-file structure.
  - `_load_directory(self, lang_code, directory, target_dict) -> Any`: Recursively load all JSON files in a directory.  Args:     lang_code: Language code.     directory: Directory path to load.     target_dict: Target dictionary to store loaded data.
  - `_get_supported_languages(self) -> Dict[str, str]`: Get the list of supported languages.
  - `get_server_lang(self, guild_id) -> str`: Get the server's language setting.
  - `save_server_lang(self, guild_id, lang) -> bool`: Save the server's language setting.
  - `_traverse_nested_dict(self, data, keys) -> Optional[Any]`: Traverse a nested dictionary.  Args:     data: The dictionary to traverse.     keys: List of keys.      Returns:     The value found, or None if not found.
  - `translate(self, guild_id, *keys, **kwargs) -> str`: Translate specified text.  Standard calling convention: translate(guild_id, "commands", "botinfo", "fields", "basic_stats", "name") translate(guild_id, "system", "language_manager", "supported_languages", "zh_TW") translate(guild_id, "errors", "permission_denied")  File structure mapping: - translate(guild_id, "commands", "botinfo", "fields", "basic_stats", "name")   → translations/zh_TW/commands/botinfo.json → ["fields"]["basic_stats"]["name"]  - translate(guild_id, "system", "language_manager", "supported_languages", "zh_TW")   → translations/zh_TW/system/language_manager.json → ["supported_languages"]["zh_TW"]  Args:     guild_id: Server ID.     *keys: Path of translation keys (multiple arguments).     **kwargs: Formatting arguments.      Returns:     str: Translated text.
  - `_format_result(self, result, kwargs) -> str`: Format translation result.  Args:     result: Translation result.     kwargs: Formatting parameters.      Returns:     Formatted string.
  - `_log_missing_translation(self, guild_id, lang, keys) -> Any`: Log missing translations.  Args:     guild_id: Server ID.     lang: Language code.     keys: Translation key path.
  - `clear_cache(self) -> Any`: Clear translation cache.
  - `get_cache_stats(self) -> Dict[str, Any]`: Get cache statistics.
  - `set_language(self, interaction, language) -> Any`: Set the display language of the server.
  - `current_language(self, interaction) -> Any`: Display the current language used by the server.
  - `get_instance(bot) -> Optional['LanguageManager']`: Get LanguageManager instance.

## Functions

### `setup(bot) -> Any`
Function setup.

