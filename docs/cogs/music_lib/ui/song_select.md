# File: `cogs/music_lib/ui/song_select.py`

## Overview
Core file handling responsibilities within the `cogs/music_lib/ui` subsystem.

## Classes

### `SongSelectView`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(player, results, interaction) -> Any`: No description provided.
  - `_get_lang_manager() -> Any`: Get language manager instance
  - `_translate_music(*path, **kwargs) -> str`: 音樂模組專用翻譯方法
  - `_get_fallback_text(key: str, **kwargs) -> str`: 備用文字機制
  - `on_timeout() -> Any`: Handle view timeout

### `SongSelectMenu`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(results, view) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: Handle song selection

## Functions

No module-level functions defined in this file.
