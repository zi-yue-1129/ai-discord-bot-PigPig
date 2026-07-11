# File: `cogs/schedule.py`

## Overview
The Schedule cog provides comprehensive scheduling and event management capabilities for Discord users. It enables users to create, manage, and track events, appointments, and recurring schedules with advanced features like time zone handling, reminder integration, and collaborative scheduling.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `schedule.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ScheduleManager`
Class managing ScheduleManager state and behavior.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `schedule_dir` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_sanitize_schedule_data(data: Any, fallback_channel_id: int) -> Any`: Ensure schedule_data has required keys and types. Returns (data, repaired).
  - `upload_schedule_command(interaction: discord.Interaction, file: discord.Attachment) -> Any`: Performs internal processing logic.
  - `_core_upload_schedule(user_id: int, channel_id: int, yaml_data: bytes) -> Any`: Performs internal processing logic.
  - `query_schedule_command(interaction: discord.Interaction, query_type: app_commands.Choice[str], time: str, day: app_commands.Choice[str], target_user: discord.Member) -> Any`: Performs internal processing logic.
  - `_core_query_schedule(interaction_or_ctx: Any, query_type: str, target_user_id: int, time: str, day: str) -> Any`: Performs internal processing logic.
  - `format_full_schedule(schedule: Any, guild_id: Any) -> Any`: Performs internal processing logic.
  - `format_specific_time_schedule(schedule: Any, specific_time: Any, day: Any, guild_id: Any) -> Any`: Performs internal processing logic.
  - `format_next_schedule(schedule: Any, now: Any, guild_id: Any) -> Any`: Performs internal processing logic.
  - `update_schedule_command(interaction: discord.Interaction, day: str, time: str, description: str) -> Any`: Performs internal processing logic.
  - `_core_update_schedule(user_id: int, day: str, time: str, description: str) -> Any`: Performs internal processing logic.
  - `show_template_command(interaction: discord.Interaction) -> None`: Performs internal processing logic.

## Functions

### `setup(bot: Any) -> Any`
Performs internal processing logic.
