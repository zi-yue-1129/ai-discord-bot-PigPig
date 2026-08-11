# File: `cogs/language_manager.py`

## Overview
The Language Manager cog is the backbone of the bot's multi-language localization system. It manages server-specific language preferences, loads translation data from a structured file system, and provides a centralized API for translating UI elements, command responses, and system messages.

## Classes

### `MissingTranslationError`
Custom exception for missing translation keys

### `TranslationCache`
Multi-layer cache for translations with LRU eviction

- **Attributes**:
  - `_max_size` (`Any`): Instance attribute managing _max_size.

- **Methods**:
  - `get(key) -> Optional[str]`: Get cached translation with LRU tracking
  - `put(key, value) -> Any`: Store translation in cache with LRU eviction
  - `clear() -> Any`: Clear all cached items
  - `size() -> int`: Get current cache size

### `LanguageManager`
Language Management System with modular translation support

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `config_dir` (`Any`): Instance attribute managing config_dir.
  - `logger` (`Any`): Instance attribute managing logger.
  - `default_lang` (`Any`): Instance attribute managing default_lang.
  - `_translation_cache` (`Any`): Instance attribute managing _translation_cache.
  - `supported_languages` (`Any`): Instance attribute managing supported_languages.

- **Methods**:
  - `get_server_lang(guild_id) -> str`: Get the server's language setting.
  - `save_server_lang(guild_id, lang) -> bool`: Save the server's language setting.
  - `translate(guild_id, *keys, **kwargs) -> str`: Translate specified text.  Standard calling convention: translate(guild_id, "commands", "botinfo", "fields", "basic_stats", "name") translate(guild_id, "system", "language_manager", "supported_languages", "zh_TW") translate(guild_id, "errors", "permission_denied")  File structure mapping: - translate(guild_id, "commands", "botinfo", "fields", "basic_stats", "name")   → translations/zh_TW/commands/botinfo.json → ["fields"]["basic_stats"]["name"]  - translate(guild_id, "system", "language_manager", "supported_languages", "zh_TW")   → translations/zh_TW/system/language_manager.json → ["supported_languages"]["zh_TW"]  Args:     guild_id: Server ID.     *keys: Path of translation keys (multiple arguments).     **kwargs: Formatting arguments.      Returns:     str: Translated text.
  - `clear_cache() -> Any`: Clear translation cache.
  - `get_cache_stats() -> Dict[Tuple[str, Any]]`: Get cache statistics.
  - `set_language(interaction, language) -> Any`: Set the display language of the server.
  - `current_language(interaction) -> Any`: Display the current language used by the server.
  - `get_instance(bot) -> Optional[LanguageManager]`: Get LanguageManager instance.

## Functions

### `setup(bot) -> Any`
Performs setup operations.

