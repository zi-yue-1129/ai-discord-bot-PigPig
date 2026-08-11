# File: `cogs/story/ui/modals.py`

## Overview
Core logic and functionalities for modals.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `WorldCreateModal`
世界創建 Modal

提供表單介面讓使用者輸入新世界的名稱、背景和第一個地點的資訊

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `story_db` (`Any`): Instance attribute managing story_db.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `on_submit(interaction) -> Any`: 處理世界創建表單提交
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `CharacterCreateModal`
角色創建 Modal

提供表單介面讓使用者創建新角色

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `character_db` (`Any`): Instance attribute managing character_db.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `logger` (`Any`): Instance attribute managing logger.
  - `character_name` (`Any`): Instance attribute managing character_name.
  - `description` (`Any`): Instance attribute managing description.
  - `webhook_url` (`Any`): Instance attribute managing webhook_url.
  - `privacy_input` (`Any`): Instance attribute managing privacy_input.

- **Methods**:
  - `on_submit(interaction) -> Any`: 處理角色創建表單提交
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `StoryStartModal`
故事開始 Modal

收集故事開始時的初始世界狀態

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute managing story_manager.
  - `bot` (`Any`): Instance attribute managing bot.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `channel_id` (`Any`): Instance attribute managing channel_id.
  - `world_name` (`Any`): Instance attribute managing world_name.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `on_submit(interaction) -> Any`: 立即回應互動以防止超時，並在背景準備 NPC 選擇介面。
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `InterventionModal`
A modal for users to submit an OOC intervention to the story director.

- **Attributes**:
  - `manager` (`Any`): Instance attribute managing manager.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `on_submit(interaction) -> Any`: Handles the submission of the intervention.
  - `on_error(interaction, error) -> Any`: Handles errors in the modal.
