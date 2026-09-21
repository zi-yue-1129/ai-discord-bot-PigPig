# File: `cogs/story/ui/modals.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `WorldCreateModal`
世界創建 Modal

提供表單介面讓使用者輸入新世界的名稱、背景和第一個地點的資訊

- **Attributes**:
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `story_db` (`Any`): Attribute holding story_db data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: StoryManager, guild_id: int) -> Any`: Executes __init__ logic.
  - `on_submit(interaction: discord.Interaction) -> Any`: 處理世界創建表單提交
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: 處理 Modal 錯誤

### `CharacterCreateModal`
角色創建 Modal

提供表單介面讓使用者創建新角色

- **Attributes**:
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `character_db` (`Any`): Attribute holding character_db data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `logger` (`Any`): Attribute holding logger data.
  - `character_name` (`Any`): Attribute holding character_name data.
  - `description` (`Any`): Attribute holding description data.
  - `webhook_url` (`Any`): Attribute holding webhook_url data.
  - `privacy_input` (`Any`): Attribute holding privacy_input data.

- **Methods**:
  - `__init__(manager: StoryManager, guild_id: int, name: str, description: str) -> Any`: Executes __init__ logic.
  - `on_submit(interaction: discord.Interaction) -> Any`: 處理角色創建表單提交
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: 處理 Modal 錯誤

### `StoryStartModal`
故事開始 Modal

收集故事開始時的初始世界狀態

- **Attributes**:
  - `story_manager` (`Any`): Attribute holding story_manager data.
  - `bot` (`Any`): Attribute holding bot data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `channel_id` (`Any`): Attribute holding channel_id data.
  - `world_name` (`Any`): Attribute holding world_name data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(story_manager: StoryManager, bot: commands.Bot, guild_id: int, channel_id: int, world_name: str) -> Any`: Executes __init__ logic.
  - `on_submit(interaction: discord.Interaction) -> Any`: 立即回應互動以防止超時，並在背景準備 NPC 選擇介面。
  - `_prepare_and_send_npc_select(interaction: discord.Interaction) -> Any`: 在背景中執行耗時操作，然後發送帶有 NPC 選擇視圖的 followup 訊息。
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: 處理 Modal 錯誤

### `InterventionModal`
A modal for users to submit an OOC intervention to the story director.

- **Attributes**:
  - `manager` (`Any`): Attribute holding manager data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: StoryManager) -> Any`: Executes __init__ logic.
  - `on_submit(interaction: discord.Interaction) -> Any`: Handles the submission of the intervention.
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: Handles errors in the modal.

## Functions

No top-level functions defined.
