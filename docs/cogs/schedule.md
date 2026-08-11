# File: `cogs/schedule.py`

## Overview
The Schedule cog provides comprehensive scheduling and event management capabilities for Discord users. It enables users to create, manage, and track events, appointments, and recurring schedules with advanced features like time zone handling, reminder integration, and collaborative scheduling.

## Classes

### `ScheduleManager`
Manages the state and core operations for ScheduleManager.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `schedule_dir` (`Any`): Instance attribute managing schedule_dir.

- **Methods**:
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `upload_schedule_command(interaction, file) -> Any`: Executes logic for upload_schedule_command.
  - `query_schedule_command(interaction, query_type, time, day, target_user) -> Any`: Executes logic for query_schedule_command.
  - `format_full_schedule(schedule, guild_id) -> Any`: Executes logic for format_full_schedule.
  - `format_specific_time_schedule(schedule, specific_time, day, guild_id) -> Any`: Executes logic for format_specific_time_schedule.
  - `format_next_schedule(schedule, now, guild_id) -> Any`: Executes logic for format_next_schedule.
  - `update_schedule_command(interaction, day, time, description) -> Any`: Executes logic for update_schedule_command.
  - `show_template_command(interaction) -> None`: Executes logic for show_template_command.

## Functions

### `setup(bot) -> Any`
Performs setup operations.

