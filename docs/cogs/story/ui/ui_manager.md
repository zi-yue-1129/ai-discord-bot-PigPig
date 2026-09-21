# File: `cogs/story/ui/ui_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `UIManager`
故事模組的 UI 管理器

負責協調和管理所有 UI 介面的顯示、更新與生命週期。
採用臨時性 (ephemeral) 介面設計，降低狀態管理複雜度。

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `character_db` (`Any`): Attribute holding character_db data.
  - `system_prompt_manager` (`Any`): Attribute holding system_prompt_manager data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(bot: commands.Bot, story_manager: StoryManager, system_prompt_manager: SystemPromptManager) -> Any`: Executes __init__ logic.
  - `show_main_menu(interaction: discord.Interaction) -> Any`: 顯示主要的故事管理選單
  - `_create_initial_story_embed(guild_id: int, channel_id: int) -> discord.Embed`: 創建初始故事選單的 Embed
  - `_create_active_story_embed(story_instance) -> discord.Embed`: 創建進行中故事的 Embed
  - `_update_world_select_options(view, guild_id: int) -> Any`: 更新視圖中的世界選擇選單選項
  - `handle_load_default_character(interaction: discord.Interaction) -> Any`: 處理從頻道預設設定載入角色的請求
  - `show_character_create_modal(interaction: discord.Interaction, name: str, description: str) -> Any`: 顯示角色創建 Modal，可選填預設值

## Functions

No top-level functions defined.
