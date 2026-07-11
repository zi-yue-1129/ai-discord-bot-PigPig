# File: `cogs/story_manager.py`

## Overview
The Story Manager cog provides comprehensive story creation and management capabilities for Discord users. It enables users to create, develop, and manage interactive stories with AI assistance, collaborative story-building features, and various story formats including collaborative writing, role-playing adventures, and creative narratives.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `story_manager.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `StoryManagerCog`
故事模組主要 Cog

重構後的故事模組採用 UI 驅動設計：
- 單一 /story 命令作為入口點
- 所有功能透過 Discord UI 元件操作
- 臨時性介面降低狀態管理複雜度

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: Performs internal processing logic.
  - `story_menu(interaction: discord.Interaction) -> Any`: 故事管理主命令
  - `intervene(interaction: discord.Interaction) -> Any`: Allows a user to intervene in the story with OOC instructions for the director.
  - `on_ready() -> Any`: Cog 準備就緒事件。
  - `handle_story_message(message: discord.Message) -> Any`: 處理故事頻道中的訊息

## Functions

### `setup(bot: commands.Bot) -> Any`
設定函式，將 Cog 加入到 bot 中
