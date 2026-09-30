# File: `cogs/story/ui/modals.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/ui/modals.py`.

## Classes

### `WorldCreateModal`
世界創建 Modal  提供表單介面讓使用者輸入新世界的名稱、背景和第一個地點的資訊

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute story_manager
  - `story_db` (`Any`): Instance attribute story_db
  - `guild_id` (`Any`): Instance attribute guild_id
  - `logger` (`Any`): Instance attribute logger
  - `world_name` (`Any`): Attribute world_name
  - `background` (`Any`): Attribute background
  - `first_location_name` (`Any`): Attribute first_location_name
  - `location_description` (`Any`): Attribute location_description

- **Methods**:
  - `on_submit(self, interaction) -> Any`: 處理世界創建表單提交
  - `on_error(self, interaction, error) -> Any`: 處理 Modal 錯誤

### `CharacterCreateModal`
角色創建 Modal  提供表單介面讓使用者創建新角色

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute story_manager
  - `character_db` (`Any`): Instance attribute character_db
  - `guild_id` (`Any`): Instance attribute guild_id
  - `logger` (`Any`): Instance attribute logger
  - `character_name` (`Any`): Instance attribute character_name
  - `description` (`Any`): Instance attribute description
  - `webhook_url` (`Any`): Instance attribute webhook_url
  - `privacy_input` (`Any`): Instance attribute privacy_input

- **Methods**:
  - `on_submit(self, interaction) -> Any`: 處理角色創建表單提交
  - `on_error(self, interaction, error) -> Any`: 處理 Modal 錯誤

### `StoryStartModal`
故事開始 Modal  收集故事開始時的初始世界狀態

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute story_manager
  - `bot` (`Any`): Instance attribute bot
  - `guild_id` (`Any`): Instance attribute guild_id
  - `channel_id` (`Any`): Instance attribute channel_id
  - `world_name` (`Any`): Instance attribute world_name
  - `logger` (`Any`): Instance attribute logger
  - `initial_date` (`Any`): Attribute initial_date
  - `initial_time` (`Any`): Attribute initial_time
  - `initial_location` (`Any`): Attribute initial_location

- **Methods**:
  - `on_submit(self, interaction) -> Any`: 立即回應互動以防止超時，並在背景準備 NPC 選擇介面。
  - `_prepare_and_send_npc_select(self, interaction) -> Any`: 在背景中執行耗時操作，然後發送帶有 NPC 選擇視圖的 followup 訊息。
  - `on_error(self, interaction, error) -> Any`: 處理 Modal 錯誤

### `InterventionModal`
A modal for users to submit an OOC intervention to the story director.

- **Attributes**:
  - `manager` (`Any`): Instance attribute manager
  - `logger` (`Any`): Instance attribute logger
  - `intervention_text` (`Any`): Attribute intervention_text

- **Methods**:
  - `on_submit(self, interaction) -> Any`: Handles the submission of the intervention.
  - `on_error(self, interaction, error) -> Any`: Handles errors in the modal.

## Functions

None
