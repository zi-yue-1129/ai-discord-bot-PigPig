# File: `cogs/schedule.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/schedule.py`.

## Classes

### `ScheduleManager`
Class representing ScheduleManager.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `schedule_dir` (`Any`): Instance attribute schedule_dir
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager

- **Methods**:
  - `cog_load(self) -> Any`: 當 Cog 載入時初始化語言管理器
  - `_sanitize_schedule_data(self, data, fallback_channel_id) -> Any`: Ensure schedule_data has required keys and types. Returns (data, repaired).
  - `upload_schedule_command(self, interaction, file) -> Any`: Method upload_schedule_command.
  - `_core_upload_schedule(self, user_id, channel_id, yaml_data) -> Any`: Method _core_upload_schedule.
  - `query_schedule_command(self, interaction, query_type, time, day, target_user) -> Any`: Method query_schedule_command.
  - `_core_query_schedule(self, interaction_or_ctx, query_type, target_user_id, time, day) -> Any`: Method _core_query_schedule.
  - `format_full_schedule(self, schedule, guild_id) -> Any`: Method format_full_schedule.
  - `format_specific_time_schedule(self, schedule, specific_time, day, guild_id) -> Any`: Method format_specific_time_schedule.
  - `format_next_schedule(self, schedule, now, guild_id) -> Any`: Method format_next_schedule.
  - `update_schedule_command(self, interaction, day, time, description) -> Any`: Method update_schedule_command.
  - `_core_update_schedule(self, user_id, day, time, description) -> Any`: Method _core_update_schedule.
  - `show_template_command(self, interaction) -> None`: Method show_template_command.

## Functions

### `setup(bot) -> Any`
Function setup.

