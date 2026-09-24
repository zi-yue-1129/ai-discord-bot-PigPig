# File: `cogs/language_manager.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

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
  - None specified.

- **Methods**:
  - `__init__(max_size: int) -> Any`: No description provided.
  - `get(key: str) -> Optional[str]`: Get cached translation with LRU tracking
  - `put(key: str, value: str) -> Any`: Store translation in cache with LRU eviction
  - `_evict_lru() -> Any`: Evict least recently used item
  - `clear() -> Any`: Clear all cached items
  - `size() -> int`: Get current cache size

### `LanguageManager`
Language Management System with modular translation support

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: No description provided.
  - `_load_translations() -> Any`: Load all language translations, supporting multi-file structure.
  - `_load_directory(lang_code: str, directory: str, target_dict: Dict[Tuple[str, Any]]) -> Any`: Recursively load all JSON files in a directory.
  - `_get_supported_languages() -> Dict[Tuple[str, str]]`: Get the list of supported languages.
  - `get_server_lang(guild_id: str) -> str`: Get the server's language setting.
  - `save_server_lang(guild_id: str, lang: str) -> bool`: Save the server's language setting.
  - `_traverse_nested_dict(data: Dict[Tuple[str, Any]], keys: List[str]) -> Optional[Any]`: Traverse a nested dictionary.
  - `translate(guild_id: str, *keys: str, **kwargs: Any) -> str`: Translate specified text.
  - `_format_result(result: str, kwargs: Dict[Tuple[str, Any]]) -> str`: Format translation result.
  - `_log_missing_translation(guild_id: str, lang: str, keys: List[str]) -> Any`: Log missing translations.
  - `clear_cache() -> Any`: Clear translation cache.
  - `get_cache_stats() -> Dict[Tuple[str, Any]]`: Get cache statistics.
  - `set_language(interaction: discord.Interaction, language: str) -> Any`: Set the display language of the server.
  - `current_language(interaction: discord.Interaction) -> Any`: Display the current language used by the server.
  - `get_instance(bot: commands.Bot) -> Optional[str]`: Get LanguageManager instance.

## Functions

### `setup(bot: commands.Bot) -> Any`
No description provided.

