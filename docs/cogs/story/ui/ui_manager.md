# File: `cogs/story/ui/ui_manager.py`

## Overview
Core file handling responsibilities within the `cogs/story/ui` subsystem.

## Classes

### `UIManager`
故事模組的 UI 管理器

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot, story_manager: str, system_prompt_manager: SystemPromptManager) -> Any`: No description provided.
  - `show_main_menu(interaction: discord.Interaction) -> Any`: 顯示主要的故事管理選單
  - `_create_initial_story_embed(guild_id: int, channel_id: int) -> discord.Embed`: 創建初始故事選單的 Embed
  - `_create_active_story_embed(story_instance) -> discord.Embed`: 創建進行中故事的 Embed
  - `_update_world_select_options(view, guild_id: int) -> Any`: 更新視圖中的世界選擇選單選項
  - `handle_load_default_character(interaction: discord.Interaction) -> Any`: 處理從頻道預設設定載入角色的請求
  - `show_character_create_modal(interaction: discord.Interaction, name: str, description: str) -> Any`: 顯示角色創建 Modal，可選填預設值

## Functions

No module-level functions defined in this file.
