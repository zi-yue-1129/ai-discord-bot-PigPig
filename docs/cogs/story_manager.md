# File: `cogs/story_manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `story_manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `StoryManagerCog`
故事模組主要 Cog

重構後的故事模組採用 UI 驅動設計：
- 單一 /story 命令作為入口點
- 所有功能透過 Discord UI 元件操作
- 臨時性介面降低狀態管理複雜度

- **Attributes**:
  - `story` (`Any`): Class attribute representing story.
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `system_prompt_manager` (`Optional[...]`): Instance attribute for system_prompt_manager.
  - `story_manager` (`Optional[...]`): Instance attribute for story_manager.
  - `ui_manager` (`Optional[...]`): Instance attribute for ui_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `get_logger` and `info`.
  - `story_menu(interaction) -> Any`: 故事管理主命令
  - `intervene(interaction) -> Any`: Allows a user to intervene in the story with OOC instructions for the director.
  - `on_ready() -> Any`: Cog 準備就緒事件。
  - `handle_story_message(message) -> Any`: 處理故事頻道中的訊息

## Functions

### `setup(bot) -> Any`
設定函式，將 Cog 加入到 bot 中
