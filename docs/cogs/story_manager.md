# File: `cogs/story_manager.py`

## Overview
The Story Manager cog provides comprehensive story creation and management capabilities for Discord users. It enables users to create, develop, and manage interactive stories with AI assistance, collaborative story-building features, and various story formats including collaborative writing, role-playing adventures, and creative narratives.

## Classes

### `StoryManagerCog`
故事模組主要 Cog

重構後的故事模組採用 UI 驅動設計：
- 單一 /story 命令作為入口點
- 所有功能透過 Discord UI 元件操作
- 臨時性介面降低狀態管理複雜度

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `story_menu(interaction) -> Any`: 故事管理主命令  根據當前頻道狀態顯示對應的 UI 介面： - 無故事：顯示初始設定選單（創建世界、角色、開始故事） - 有故事：顯示故事控制面板（加入、暫停、結束等）
  - `intervene(interaction) -> Any`: Allows a user to intervene in the story with OOC instructions for the director.
  - `on_ready() -> Any`: Cog 準備就緒事件。 此時所有 cogs 都已載入，可以安全地獲取其他 cog。
  - `handle_story_message(message) -> Any`: 處理故事頻道中的訊息  此方法由 bot.py 的 on_message 事件呼叫， 當頻道模式為 'story' 時處理使用者的故事互動。  Args:     message: Discord 訊息物件

## Functions

### `setup(bot) -> Any`
設定函式，將 Cog 加入到 bot 中

Args:
    bot: Discord Bot 實例

