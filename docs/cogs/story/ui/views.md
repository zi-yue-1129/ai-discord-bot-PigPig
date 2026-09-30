# File: `cogs/story/ui/views.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/ui/views.py`.

## Classes

### `InitialStoryView`
初始故事視圖  用於故事開始前的準備工作，包含： - 世界選擇選單 - 創建世界按鈕 - 創建角色按鈕 - 開始故事按鈕

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute story_manager
  - `ui_manager` (`Any`): Instance attribute ui_manager
  - `channel_id` (`Any`): Instance attribute channel_id
  - `guild_id` (`Any`): Instance attribute guild_id
  - `selected_world` (`Optional[str]`): Instance attribute selected_world
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `on_timeout(self) -> Any`: 視圖超時處理
  - `world_select(self, interaction, select) -> Any`: 世界選擇選單
  - `create_world_button(self, interaction, button) -> Any`: 創建世界按鈕
  - `create_character_button(self, interaction, button) -> Any`: 創建角色按鈕
  - `load_default_character_button(self, interaction, button) -> Any`: 從預設載入角色按鈕
  - `start_story_button(self, interaction, button) -> Any`: 開始故事按鈕
  - `_refresh_world_select(self) -> Any`: 重新整理世界選擇選單

### `ActiveStoryView`
進行中故事視圖  用於管理正在進行的故事，包含： - 加入故事按鈕 - 暫停/恢復故事按鈕（管理員） - 結束故事按鈕（管理員）

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute story_manager
  - `story_instance` (`Any`): Instance attribute story_instance
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_update_narration_button_state(self) -> Any`: 更新旁白切換按鈕的狀態
  - `_update_pause_button_state(self) -> Any`: 更新暫停/恢復按鈕的狀態
  - `join_story_button(self, interaction, button) -> Any`: 加入故事按鈕
  - `pause_story_button(self, interaction, button) -> Any`: 暫停故事按鈕（管理員專用）
  - `toggle_narration_button(self, interaction, button) -> Any`: 切換旁白功能的按鈕
  - `end_story_button(self, interaction, button) -> Any`: 結束故事按鈕（管理員專用）

### `NPCSelectView`
NPC 選擇視圖  讓玩家在開始故事時選擇要參與的 NPC

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute story_manager
  - `guild_id` (`Any`): Instance attribute guild_id
  - `channel_id` (`Any`): Instance attribute channel_id
  - `world_name` (`Any`): Instance attribute world_name
  - `initial_date` (`Any`): Instance attribute initial_date
  - `initial_time` (`Any`): Instance attribute initial_time
  - `initial_location` (`Any`): Instance attribute initial_location
  - `characters` (`Any`): Instance attribute characters
  - `logger` (`Any`): Instance attribute logger
  - `npc_select` (`Any`): Instance attribute npc_select

- **Methods**:
  - `create(cls, manager, interaction, channel_id, world_name, initial_date, initial_time, initial_location, system_prompt) -> 'NPCSelectView'`: 非同步工廠方法，用於創建和填充 NPCSelectView。
  - `npc_select_callback(self, interaction) -> Any`: 處理 NPC 選擇的回調
  - `confirm_button(self, interaction, button) -> Any`: 確認選擇並將邏輯委派給 StoryManager 開始故事

## Functions

None
