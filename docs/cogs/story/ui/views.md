# File: `cogs/story/ui/views.py`

## Overview
Core logic and functionalities for views.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `InitialStoryView`
初始故事視圖

用於故事開始前的準備工作，包含：
- 世界選擇選單
- 創建世界按鈕
- 創建角色按鈕
- 開始故事按鈕

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `ui_manager` (`Any`): Instance attribute managing ui_manager.
  - `channel_id` (`Any`): Instance attribute managing channel_id.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `on_timeout() -> Any`: 視圖超時處理
  - `world_select(interaction, select) -> Any`: 世界選擇選單
  - `create_world_button(interaction, button) -> Any`: 創建世界按鈕
  - `create_character_button(interaction, button) -> Any`: 創建角色按鈕
  - `load_default_character_button(interaction, button) -> Any`: 從預設載入角色按鈕
  - `start_story_button(interaction, button) -> Any`: 開始故事按鈕

### `ActiveStoryView`
進行中故事視圖

用於管理正在進行的故事，包含：
- 加入故事按鈕
- 暫停/恢復故事按鈕（管理員）
- 結束故事按鈕（管理員）

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `story_instance` (`Any`): Instance attribute managing story_instance.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `join_story_button(interaction, button) -> Any`: 加入故事按鈕
  - `pause_story_button(interaction, button) -> Any`: 暫停故事按鈕（管理員專用）
  - `toggle_narration_button(interaction, button) -> Any`: 切換旁白功能的按鈕
  - `end_story_button(interaction, button) -> Any`: 結束故事按鈕（管理員專用）

### `NPCSelectView`
NPC 選擇視圖

讓玩家在開始故事時選擇要參與的 NPC

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `channel_id` (`Any`): Instance attribute managing channel_id.
  - `world_name` (`Any`): Instance attribute managing world_name.
  - `initial_date` (`Any`): Instance attribute managing initial_date.
  - `initial_time` (`Any`): Instance attribute managing initial_time.
  - `initial_location` (`Any`): Instance attribute managing initial_location.
  - `characters` (`Any`): Instance attribute managing characters.
  - `logger` (`Any`): Instance attribute managing logger.
  - `npc_select` (`Any`): Instance attribute managing npc_select.

- **Methods**:
  - `create(cls, manager, interaction, channel_id, world_name, initial_date, initial_time, initial_location, system_prompt) -> NPCSelectView`: 非同步工廠方法，用於創建和填充 NPCSelectView。
  - `npc_select_callback(interaction) -> Any`: 處理 NPC 選擇的回調
  - `confirm_button(interaction, button) -> Any`: 確認選擇並將邏輯委派給 StoryManager 開始故事
