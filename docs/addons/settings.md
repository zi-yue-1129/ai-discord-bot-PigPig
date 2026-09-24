# File: `addons/settings.py`

## Overview
Core file handling responsibilities within the `addons` subsystem.

## Classes

### `BaseConfig`
Configuration object mapped from config/base.yaml

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.

### `LLMConfig`
Configuration object mapped from config/llm.yaml

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.

### `UpdateConfig`
Configuration object mapped from config/update.yaml

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.

### `MusicConfig`
Configuration object mapped from config/music.yaml

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.

### `PromptConfig`
Configuration object mapped from config/prompt/*.yaml

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.
  - `get_system_prompt(agent_name: str, bot_id: int | None, message) -> str`: Retrieve system_prompt from agent config and apply dynamic variable replacement.

### `MemoryConfig`
Memory subsystem configuration object mapped from config/memory.yaml

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.

### `_AttachmentImageConfig`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(data: dict) -> None`: No description provided.

### `_AttachmentPdfConfig`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(data: dict) -> None`: No description provided.

### `_AttachmentVideoConfig`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(data: dict) -> None`: No description provided.

### `_AttachmentEmbedsConfig`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(data: dict) -> None`: No description provided.

### `AttachmentConfig`
Configuration for attachment and embed processing (base_configs/attachments.yaml).

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(path: str) -> None`: No description provided.

## Functions

### `_load_yaml_file(path: str) -> dict`
Safely load a YAML file; report errors via func.report_error and return an empty dict on failure.

### `_get_config_root() -> str`
Read CONFIG_ROOT environment variable.

