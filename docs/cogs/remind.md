# File: `cogs/remind.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `ReminderCog`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: No description provided.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_set_reminder_logic(channel, target_user, time_str: str, message: str, guild_id: str, interaction: Optional[discord.Interaction]) -> Any`: 核心提醒邏輯，可被斜線命令和LLM工具共用
  - `remind(interaction: discord.Interaction, time: str, message: str, user: discord.User) -> Any`: No description provided.
  - `_parse_relative_time_regex(time_str: str) -> Optional[datetime]`: 使用正規表示式解析簡單的相對時間，例如 '10 分鐘後'
  - `parse_time(time_str: str, guild_id: str) -> Optional[datetime]`: 使用 dateparser 解析時間字串，並提供基於正規表示式的備用方案。
  - `format_timedelta(td: timedelta, guild_id: str) -> str`: 格式化時間長度為本地化字串
  - `_format_time_fallback(td: timedelta) -> str`: 備用時間格式化機制（當翻譯系統不可用時）

## Functions

### `setup(bot) -> Any`
No description provided.

