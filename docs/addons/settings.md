# File: `addons/settings.py`

## Overview
The `addons/settings.py` module is the central configuration engine for the PigPig Bot. It handles loading YAML configuration files, managing environment variables via `.env`, and providing a structured API for other modules to access settings.

This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `settings.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `BaseConfig`
Configuration object mapped from config/base.yaml

- **Attributes**:
  - `path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.

### `LLMConfig`
Configuration object mapped from config/llm.yaml

- **Attributes**:
  - `path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.

### `UpdateConfig`
Configuration object mapped from config/update.yaml

- **Attributes**:
  - `path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.

### `MusicConfig`
Configuration object mapped from config/music.yaml

- **Attributes**:
  - `path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.

### `PromptConfig`
Configuration object mapped from config/prompt/*.yaml

- **Attributes**:
  - `path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.
  - `get_system_prompt(agent_name: str, bot_id: Any, message: Any) -> str`: Retrieve system_prompt from agent config and apply dynamic variable replacement.

### `MemoryConfig`
Memory subsystem configuration object mapped from config/memory.yaml

- **Attributes**:
  - `path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.

### `_AttachmentImageConfig`
Class managing _AttachmentImageConfig state and behavior.

- **Methods**:
  - `__init__(data: dict) -> None`: Performs internal processing logic.

### `_AttachmentPdfConfig`
Class managing _AttachmentPdfConfig state and behavior.

- **Methods**:
  - `__init__(data: dict) -> None`: Performs internal processing logic.

### `_AttachmentVideoConfig`
Class managing _AttachmentVideoConfig state and behavior.

- **Methods**:
  - `__init__(data: dict) -> None`: Performs internal processing logic.

### `_AttachmentEmbedsConfig`
Class managing _AttachmentEmbedsConfig state and behavior.

- **Methods**:
  - `__init__(data: dict) -> None`: Performs internal processing logic.

### `AttachmentConfig`
Configuration for attachment and embed processing (base_configs/attachments.yaml).

- **Attributes**:
  - `path` (`Any`): Internal instance state.
  - `image` (`Any`): Internal instance state.
  - `pdf` (`Any`): Internal instance state.
  - `video` (`Any`): Internal instance state.
  - `embeds` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(path: str) -> None`: Performs internal processing logic.

## Functions

### `_load_yaml_file(path: str) -> dict`
Safely load a YAML file; report errors via func.report_error and return an empty dict on failure.

### `_get_config_root() -> str`
Read CONFIG_ROOT environment variable.
