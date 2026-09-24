# File: `cogs/schedule.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `ScheduleManager`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: No description provided.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_sanitize_schedule_data(data, fallback_channel_id: int) -> Any`: Ensure schedule_data has required keys and types. Returns (data, repaired).
  - `upload_schedule_command(interaction: discord.Interaction, file: discord.Attachment) -> Any`: No description provided.
  - `_core_upload_schedule(user_id: int, channel_id: int, yaml_data: bytes) -> Any`: No description provided.
  - `query_schedule_command(interaction: discord.Interaction, query_type: app_commands.Choice[str], time: str, day: app_commands.Choice[str], target_user: discord.Member) -> Any`: No description provided.
  - `_core_query_schedule(interaction_or_ctx, query_type: str, target_user_id: int, time: str, day: str) -> Any`: No description provided.
  - `format_full_schedule(schedule, guild_id) -> Any`: No description provided.
  - `format_specific_time_schedule(schedule, specific_time, day, guild_id) -> Any`: No description provided.
  - `format_next_schedule(schedule, now, guild_id) -> Any`: No description provided.
  - `update_schedule_command(interaction: discord.Interaction, day: str, time: str, description: str) -> Any`: No description provided.
  - `_core_update_schedule(user_id: int, day: str, time: str, description: str) -> Any`: No description provided.
  - `show_template_command(interaction: discord.Interaction) -> None`: No description provided.

## Functions

### `setup(bot) -> Any`
No description provided.

