# File: `cogs/story_manager.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `StoryManagerCog`
故事模組主要 Cog

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: No description provided.
  - `story_menu(interaction: discord.Interaction) -> Any`: 故事管理主命令
  - `intervene(interaction: discord.Interaction) -> Any`: Allows a user to intervene in the story with OOC instructions for the director.
  - `on_ready() -> Any`: Cog 準備就緒事件。
  - `handle_story_message(message: discord.Message) -> Any`: 處理故事頻道中的訊息

## Functions

### `setup(bot: commands.Bot) -> Any`
設定函式，將 Cog 加入到 bot 中

