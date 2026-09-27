# File: `cogs/story/ui/modals.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `modals` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `WorldCreateModal`
世界創建 Modal

提供表單介面讓使用者輸入新世界的名稱、背景和第一個地點的資訊

- **Attributes**:
  - `world_name` (`Any`): Class attribute representing world_name.
  - `background` (`Any`): Class attribute representing background.
  - `first_location_name` (`Any`): Class attribute representing first_location_name.
  - `location_description` (`Any`): Class attribute representing location_description.
  - `story_manager` (`Any`): Instance attribute for story_manager.
  - `story_db` (`Any`): Instance attribute for story_db.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, guild_id) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `_get_db`.
  - `on_submit(interaction) -> Any`: 處理世界創建表單提交
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `CharacterCreateModal`
角色創建 Modal

提供表單介面讓使用者創建新角色

- **Attributes**:
  - `story_manager` (`Any`): Instance attribute for story_manager.
  - `character_db` (`Any`): Instance attribute for character_db.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `logger` (`Any`): Instance attribute for logger.
  - `character_name` (`Any`): Instance attribute for character_name.
  - `description` (`Any`): Instance attribute for description.
  - `webhook_url` (`Any`): Instance attribute for webhook_url.
  - `privacy_input` (`Any`): Instance attribute for privacy_input.

- **Methods**:
  - `__init__(manager, guild_id, name, description) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `TextInput`.
  - `on_submit(interaction) -> Any`: 處理角色創建表單提交
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `StoryStartModal`
故事開始 Modal

收集故事開始時的初始世界狀態

- **Attributes**:
  - `initial_date` (`Any`): Class attribute representing initial_date.
  - `initial_time` (`Any`): Class attribute representing initial_time.
  - `initial_location` (`Any`): Class attribute representing initial_location.
  - `story_manager` (`Any`): Instance attribute for story_manager.
  - `bot` (`Any`): Instance attribute for bot.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `channel_id` (`Any`): Instance attribute for channel_id.
  - `world_name` (`Any`): Instance attribute for world_name.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(story_manager, bot, guild_id, channel_id, world_name) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `on_submit(interaction) -> Any`: 立即回應互動以防止超時，並在背景準備 NPC 選擇介面。
  - `_prepare_and_send_npc_select(interaction) -> Any`: 在背景中執行耗時操作，然後發送帶有 NPC 選擇視圖的 followup 訊息。
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `InterventionModal`
A modal for users to submit an OOC intervention to the story director.

- **Attributes**:
  - `intervention_text` (`Any`): Class attribute representing intervention_text.
  - `manager` (`Any`): Instance attribute for manager.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `on_submit(interaction) -> Any`: Handles the submission of the intervention.
  - `on_error(interaction, error) -> Any`: Handles errors in the modal.
