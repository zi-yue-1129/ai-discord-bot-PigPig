# File: `cogs/story/ui/ui_manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `ui_manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `UIManager`
故事模組的 UI 管理器

負責協調和管理所有 UI 介面的顯示、更新與生命週期。
採用臨時性 (ephemeral) 介面設計，降低狀態管理複雜度。

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `story_manager` (`Any`): Instance attribute for story_manager.
  - `character_db` (`Any`): Instance attribute for character_db.
  - `system_prompt_manager` (`Any`): Instance attribute for system_prompt_manager.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(bot, story_manager, system_prompt_manager) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `show_main_menu(interaction) -> Any`: 顯示主要的故事管理選單
  - `_create_initial_story_embed(guild_id, channel_id) -> discord.Embed`: 創建初始故事選單的 Embed
  - `_create_active_story_embed(story_instance) -> discord.Embed`: 創建進行中故事的 Embed
  - `_update_world_select_options(view, guild_id) -> Any`: 更新視圖中的世界選擇選單選項
  - `handle_load_default_character(interaction) -> Any`: 處理從頻道預設設定載入角色的請求
  - `show_character_create_modal(interaction, name, description) -> Any`: 顯示角色創建 Modal，可選填預設值
