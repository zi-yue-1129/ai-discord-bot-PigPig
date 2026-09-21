# File: `cogs/story/ui/views.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `InitialStoryView`
初始故事視圖

用於故事開始前的準備工作，包含：
- 世界選擇選單
- 創建世界按鈕
- 創建角色按鈕
- 開始故事按鈕

- **Attributes**:
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `ui_manager` (`Any`): Attribute holding ui_manager data.
  - `channel_id` (`Any`): Attribute holding channel_id data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `selected_world` (`Optional[str]`): Attribute holding selected_world data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: StoryManager, channel_id: int, guild_id: int, ui_manager: UIManager) -> Any`: Executes __init__ logic.
  - `on_timeout() -> Any`: 視圖超時處理
  - `world_select(interaction: discord.Interaction, select: discord.ui.Select) -> Any`: 世界選擇選單
  - `create_world_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 創建世界按鈕
  - `create_character_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 創建角色按鈕
  - `load_default_character_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 從預設載入角色按鈕
  - `start_story_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 開始故事按鈕
  - `_refresh_world_select() -> Any`: 重新整理世界選擇選單

### `ActiveStoryView`
進行中故事視圖

用於管理正在進行的故事，包含：
- 加入故事按鈕
- 暫停/恢復故事按鈕（管理員）
- 結束故事按鈕（管理員）

- **Attributes**:
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `story_instance` (`Any`): Attribute holding story_instance data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: StoryManager, story_instance: StoryInstance) -> Any`: Executes __init__ logic.
  - `_update_narration_button_state() -> Any`: 更新旁白切換按鈕的狀態
  - `_update_pause_button_state() -> Any`: 更新暫停/恢復按鈕的狀態
  - `join_story_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 加入故事按鈕
  - `pause_story_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 暫停故事按鈕（管理員專用）
  - `toggle_narration_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 切換旁白功能的按鈕
  - `end_story_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 結束故事按鈕（管理員專用）

### `NPCSelectView`
NPC 選擇視圖

讓玩家在開始故事時選擇要參與的 NPC

- **Attributes**:
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `channel_id` (`Any`): Attribute holding channel_id data.
  - `world_name` (`Any`): Attribute holding world_name data.
  - `initial_date` (`Any`): Attribute holding initial_date data.
  - `initial_time` (`Any`): Attribute holding initial_time data.
  - `initial_location` (`Any`): Attribute holding initial_location data.
  - `characters` (`Any`): Attribute holding characters data.
  - `logger` (`Any`): Attribute holding logger data.
  - `npc_select` (`Any`): Attribute holding npc_select data.

- **Methods**:
  - `create(cls, manager: StoryManager, interaction: discord.Interaction, channel_id: int, world_name: str, initial_date: Optional[str], initial_time: Optional[str], initial_location: str, system_prompt: str) -> NPCSelectView`: 非同步工廠方法，用於創建和填充 NPCSelectView。
  - `__init__(manager: StoryManager, guild_id: int, channel_id: int, world_name: str, initial_date: Optional[str], initial_time: Optional[str], initial_location: str, characters: List[StoryCharacter], options: List[discord.SelectOption]) -> Any`: Executes __init__ logic.
  - `npc_select_callback(interaction: discord.Interaction) -> Any`: 處理 NPC 選擇的回調
  - `confirm_button(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 確認選擇並將邏輯委派給 StoryManager 開始故事

## Functions

No top-level functions defined.
