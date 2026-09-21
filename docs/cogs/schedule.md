# File: `cogs/schedule.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ScheduleManager`
Core class implementation.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `schedule_dir` (`Any`): Attribute holding schedule_dir data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_sanitize_schedule_data(data, fallback_channel_id: int) -> Any`: Ensure schedule_data has required keys and types. Returns (data, repaired).
  - `upload_schedule_command(interaction: discord.Interaction, file: discord.Attachment) -> Any`: Executes upload_schedule_command logic.
  - `_core_upload_schedule(user_id: int, channel_id: int, yaml_data: bytes) -> Any`: Executes _core_upload_schedule logic.
  - `query_schedule_command(interaction: discord.Interaction, query_type: app_commands.Choice[str], time: str, day: app_commands.Choice[str], target_user: discord.Member) -> Any`: Executes query_schedule_command logic.
  - `_core_query_schedule(interaction_or_ctx, query_type: str, target_user_id: int, time: str, day: str) -> Any`: Executes _core_query_schedule logic.
  - `format_full_schedule(schedule, guild_id) -> Any`: Executes format_full_schedule logic.
  - `format_specific_time_schedule(schedule, specific_time, day, guild_id) -> Any`: Executes format_specific_time_schedule logic.
  - `format_next_schedule(schedule, now, guild_id) -> Any`: Executes format_next_schedule logic.
  - `update_schedule_command(interaction: discord.Interaction, day: str, time: str, description: str) -> Any`: Executes update_schedule_command logic.
  - `_core_update_schedule(user_id: int, day: str, time: str, description: str) -> Any`: Executes _core_update_schedule logic.
  - `show_template_command(interaction: discord.Interaction) -> None`: Executes show_template_command logic.

## Functions

### `setup(bot) -> Any`
Performs setup operations.
