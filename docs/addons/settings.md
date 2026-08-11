# File: `addons/settings.py`

## Overview
The `addons/settings.py` module is the central configuration engine for the PigPig Bot. It handles loading YAML configuration files, managing environment variables via `.env`, and providing a structured API for other modules to access settings.

## Classes

### `BaseConfig`
Configuration object mapped from config/base.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.

### `LLMConfig`
Configuration object mapped from config/llm.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.

### `UpdateConfig`
Configuration object mapped from config/update.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.

### `MusicConfig`
Configuration object mapped from config/music.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.

### `PromptConfig`
Configuration object mapped from config/prompt/*.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.

- **Methods**:
  - `get_system_prompt(agent_name, bot_id, message) -> str`: Retrieve system_prompt from agent config and apply dynamic variable replacement.  Args:     agent_name: Name of the agent.     bot_id: Optional bot ID for {bot_id} replacement.     message: Optional Discord message object (reserved for future use).  Returns:     Formatted system_prompt string, or empty string if not found.

### `MemoryConfig`
Memory subsystem configuration object mapped from config/memory.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.

### `_AttachmentImageConfig`
Manages the state and core operations for _AttachmentImageConfig.

### `_AttachmentPdfConfig`
Manages the state and core operations for _AttachmentPdfConfig.

### `_AttachmentVideoConfig`
Manages the state and core operations for _AttachmentVideoConfig.

### `_AttachmentEmbedsConfig`
Manages the state and core operations for _AttachmentEmbedsConfig.

### `AttachmentConfig`
Configuration for attachment and embed processing (base_configs/attachments.yaml).

- **Attributes**:
  - `path` (`Any`): Instance attribute managing path.
  - `image` (`Any`): Instance attribute managing image.
  - `pdf` (`Any`): Instance attribute managing pdf.
  - `video` (`Any`): Instance attribute managing video.
  - `embeds` (`Any`): Instance attribute managing embeds.

