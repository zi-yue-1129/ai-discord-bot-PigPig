# File: `cogs/story_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `StoryManagerCog`
故事模組主要 Cog

重構後的故事模組採用 UI 驅動設計：
- 單一 /story 命令作為入口點
- 所有功能透過 Discord UI 元件操作
- 臨時性介面降低狀態管理複雜度

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `logger` (`Any`): Attribute holding logger data.
  - `system_prompt_manager` (`Optional[SystemPromptManager]`): Attribute holding system_prompt_manager data.
  - `story_manager` (`Optional[StoryManager]`): Attribute holding story_manager data.
  - `ui_manager` (`Optional[UIManager]`): Attribute holding ui_manager data.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: Executes __init__ logic.
  - `story_menu(interaction: discord.Interaction) -> Any`: 故事管理主命令
  - `intervene(interaction: discord.Interaction) -> Any`: Allows a user to intervene in the story with OOC instructions for the director.
  - `on_ready() -> Any`: Cog 準備就緒事件。
  - `handle_story_message(message: discord.Message) -> Any`: 處理故事頻道中的訊息

## Functions

### `setup(bot: commands.Bot) -> Any`
設定函式，將 Cog 加入到 bot 中

Args:
    bot: Discord Bot 實例
