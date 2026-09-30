# File: `cogs/story/ui/ui_manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/ui/ui_manager.py`.

## Classes

### `UIManager`
故事模組的 UI 管理器  負責協調和管理所有 UI 介面的顯示、更新與生命週期。 採用臨時性 (ephemeral) 介面設計，降低狀態管理複雜度。

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `story_manager` (`Any`): Instance attribute story_manager
  - `character_db` (`Any`): Instance attribute character_db
  - `system_prompt_manager` (`Any`): Instance attribute system_prompt_manager
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `show_main_menu(self, interaction) -> Any`: 顯示主要的故事管理選單  根據當前頻道是否有活躍的故事實例，決定顯示： 1. InitialStoryView - 故事開始前的準備介面 2. ActiveStoryView - 正在進行故事的管理介面  Args:     interaction: Discord 互動物件
  - `_create_initial_story_embed(self, guild_id, channel_id) -> discord.Embed`: 創建初始故事選單的 Embed
  - `_create_active_story_embed(self, story_instance) -> discord.Embed`: 創建進行中故事的 Embed
  - `_update_world_select_options(self, view, guild_id) -> Any`: 更新視圖中的世界選擇選單選項
  - `handle_load_default_character(self, interaction) -> Any`: 處理從頻道預設設定載入角色的請求
  - `show_character_create_modal(self, interaction, name, description) -> Any`: 顯示角色創建 Modal，可選填預設值

## Functions

None
