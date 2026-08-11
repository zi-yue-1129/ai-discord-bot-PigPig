# File: `cogs/story/ui/ui_manager.py`

## Overview
Core logic and functionalities for ui_manager.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `UIManager`
故事模組的 UI 管理器

負責協調和管理所有 UI 介面的顯示、更新與生命週期。
採用臨時性 (ephemeral) 介面設計，降低狀態管理複雜度。

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `character_db` (`Any`): Instance attribute managing character_db.
  - `system_prompt_manager` (`Any`): Instance attribute managing system_prompt_manager.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `show_main_menu(interaction) -> Any`: 顯示主要的故事管理選單  根據當前頻道是否有活躍的故事實例，決定顯示： 1. InitialStoryView - 故事開始前的準備介面 2. ActiveStoryView - 正在進行故事的管理介面  Args:     interaction: Discord 互動物件
  - `handle_load_default_character(interaction) -> Any`: 處理從頻道預設設定載入角色的請求
  - `show_character_create_modal(interaction, name, description) -> Any`: 顯示角色創建 Modal，可選填預設值
