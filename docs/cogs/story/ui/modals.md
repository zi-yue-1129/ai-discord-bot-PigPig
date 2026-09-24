# File: `cogs/story/ui/modals.py`

## Overview
Core file handling responsibilities within the `cogs/story/ui` subsystem.

## Classes

### `WorldCreateModal`
世界創建 Modal

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: str, guild_id: int) -> Any`: No description provided.
  - `on_submit(interaction: discord.Interaction) -> Any`: 處理世界創建表單提交
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: 處理 Modal 錯誤

### `CharacterCreateModal`
角色創建 Modal

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: str, guild_id: int, name: str, description: str) -> Any`: No description provided.
  - `on_submit(interaction: discord.Interaction) -> Any`: 處理角色創建表單提交
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: 處理 Modal 錯誤

### `StoryStartModal`
故事開始 Modal

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(story_manager: str, bot: commands.Bot, guild_id: int, channel_id: int, world_name: str) -> Any`: No description provided.
  - `on_submit(interaction: discord.Interaction) -> Any`: 立即回應互動以防止超時，並在背景準備 NPC 選擇介面。
  - `_prepare_and_send_npc_select(interaction: discord.Interaction) -> Any`: 在背景中執行耗時操作，然後發送帶有 NPC 選擇視圖的 followup 訊息。
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: 處理 Modal 錯誤

### `InterventionModal`
A modal for users to submit an OOC intervention to the story director.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: str) -> Any`: No description provided.
  - `on_submit(interaction: discord.Interaction) -> Any`: Handles the submission of the intervention.
  - `on_error(interaction: discord.Interaction, error: Exception) -> Any`: Handles errors in the modal.

## Functions

No module-level functions defined in this file.
