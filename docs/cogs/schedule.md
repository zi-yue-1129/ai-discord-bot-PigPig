# File: `cogs/schedule.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `schedule` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `ScheduleManager`
Represents the `ScheduleManager` class in the system.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `schedule_dir` (`Any`): Instance attribute for schedule_dir.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `makedirs`.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_sanitize_schedule_data(data, fallback_channel_id) -> Any`: Ensure schedule_data has required keys and types. Returns (data, repaired).
  - `upload_schedule_command(interaction, file) -> Any`: Handles the `upload_schedule_command` functionality. Internally, it interacts with methods like `command` and `defer`.
  - `_core_upload_schedule(user_id, channel_id, yaml_data) -> Any`: Handles the `_core_upload_schedule` functionality. Internally, it interacts with methods like `safe_load` and `YAMLError`.
  - `query_schedule_command(interaction, query_type, time, day, target_user) -> Any`: Handles the `query_schedule_command` functionality. Internally, it interacts with methods like `command` and `choices`.
  - `_core_query_schedule(interaction_or_ctx, query_type, target_user_id, time, day) -> Any`: Handles the `_core_query_schedule` functionality. Internally, it interacts with methods like `join` and `_sanitize_schedule_data`.
  - `format_full_schedule(schedule, guild_id) -> Any`: Handles the `format_full_schedule` functionality. Internally, it interacts with methods like `items` and `translate`.
  - `format_specific_time_schedule(schedule, specific_time, day, guild_id) -> Any`: Handles the `format_specific_time_schedule` functionality. Internally, it interacts with methods like `translate` and `get`.
  - `format_next_schedule(schedule, now, guild_id) -> Any`: Handles the `format_next_schedule` functionality. Internally, it interacts with methods like `items` and `get`.
  - `update_schedule_command(interaction, day, time, description) -> Any`: Handles the `update_schedule_command` functionality. Internally, it interacts with methods like `command` and `defer`.
  - `_core_update_schedule(user_id, day, time, description) -> Any`: Handles the `_core_update_schedule` functionality. Internally, it interacts with methods like `join` and `_sanitize_schedule_data`.
  - `show_template_command(interaction) -> None`: Handles the `show_template_command` functionality. Internally, it interacts with methods like `command` and `open`.

## Functions

### `setup(bot) -> Any`
Provides `setup` functionality. Internally, it interacts with methods like `add_cog` and `ScheduleManager`.
