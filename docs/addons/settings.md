# File: `addons/settings.py`

## Overview
This file is part of the `addons` subsystem. It is responsible for `settings` related functionality within the PigPig system, contributing to utility functions, configurations, and core extensions.

## Classes

### `BaseConfig`
Configuration object mapped from config/base.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.
  - `prefix` (`str`): Instance attribute for prefix.
  - `activity` (`list`): Instance attribute for activity.
  - `ipc_server` (`dict`): Instance attribute for ipc_server.
  - `version` (`str`): Instance attribute for version.
  - `dashboard` (`dict`): Instance attribute for dashboard.
  - `logging` (`dict`): Instance attribute for logging.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_yaml_file` and `get`.

### `LLMConfig`
Configuration object mapped from config/llm.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.
  - `data` (`dict`): Instance attribute for data.
  - `model_priorities` (`list`): Instance attribute for model_priorities.
  - `google_search_agent` (`str`): Instance attribute for google_search_agent.
  - `vllm_url` (`Optional[...]`): Instance attribute for vllm_url.
  - `ollama_url` (`Optional[...]`): Instance attribute for ollama_url.
  - `llm_call_timeout` (`float`): Instance attribute for llm_call_timeout.
  - `reasoning_optimization_prompt` (`str`): Instance attribute for reasoning_optimization_prompt.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_yaml_file` and `get`.

### `UpdateConfig`
Configuration object mapped from config/update.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.
  - `auto_update` (`dict`): Instance attribute for auto_update.
  - `security` (`dict`): Instance attribute for security.
  - `notification` (`dict`): Instance attribute for notification.
  - `restart` (`dict`): Instance attribute for restart.
  - `github` (`dict`): Instance attribute for github.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_yaml_file` and `get`.

### `MusicConfig`
Configuration object mapped from config/music.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.
  - `music_temp_base` (`dict`): Instance attribute for music_temp_base.
  - `ffmpeg` (`dict`): Instance attribute for ffmpeg.
  - `youtube_cookies_path` (`str`): Instance attribute for youtube_cookies_path.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_yaml_file` and `get`.

### `PromptConfig`
Configuration object mapped from config/prompt/*.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get_system_prompt(agent_name, bot_id, message) -> str`: Retrieve system_prompt from agent config and apply dynamic variable replacement.

### `MemoryConfig`
Memory subsystem configuration object mapped from config/memory.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.
  - `enabled` (`bool`): Instance attribute for enabled.
  - `procedural_cache_ttl` (`float`): Instance attribute for procedural_cache_ttl.
  - `procedural_max_cache_size` (`int`): Instance attribute for procedural_max_cache_size.
  - `knowledge_cache_ttl` (`float`): Instance attribute for knowledge_cache_ttl.
  - `episodic_cache_ttl` (`float`): Instance attribute for episodic_cache_ttl.
  - `knowledge_max_cache_size` (`int`): Instance attribute for knowledge_max_cache_size.
  - `episodic_max_cache_size` (`int`): Instance attribute for episodic_max_cache_size.
  - `procedural_data_path` (`str`): Instance attribute for procedural_data_path.
  - `episodic_data_path` (`str`): Instance attribute for episodic_data_path.
  - `vector_store_type` (`str`): Instance attribute for vector_store_type.
  - `qdrant_url` (`str`): Instance attribute for qdrant_url.
  - `qdrant_api_key` (`Optional[...]`): Instance attribute for qdrant_api_key.
  - `qdrant_collection_name` (`str`): Instance attribute for qdrant_collection_name.
  - `embedding_provider` (`str`): Instance attribute for embedding_provider.
  - `embedding_model_name` (`str`): Instance attribute for embedding_model_name.
  - `embedding_dim` (`int`): Instance attribute for embedding_dim.
  - `vector_search_k` (`int`): Instance attribute for vector_search_k.
  - `keyword_search_k` (`int`): Instance attribute for keyword_search_k.
  - `vllm_url` (`Optional[...]`): Instance attribute for vllm_url.
  - `ollama_url` (`Optional[...]`): Instance attribute for ollama_url.
  - `provider_options` (`dict`): Instance attribute for provider_options.
  - `short_term_limit` (`int`): Instance attribute for short_term_limit.
  - `episodic_top_k` (`int`): Instance attribute for episodic_top_k.
  - `episodic_max_chars` (`int`): Instance attribute for episodic_max_chars.
  - `message_threshold` (`int`): Instance attribute for message_threshold.
  - `time_threshold` (`int`): Instance attribute for time_threshold.
  - `processing_concurrency` (`int`): Instance attribute for processing_concurrency.
  - `processing_delay` (`float`): Instance attribute for processing_delay.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_yaml_file` and `float`.

### `_AttachmentImageConfig`
Represents the `_AttachmentImageConfig` class in the system.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute for enabled.
  - `max_dimension` (`int`): Instance attribute for max_dimension.

- **Methods**:
  - `__init__(data) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `get`.

### `_AttachmentPdfConfig`
Represents the `_AttachmentPdfConfig` class in the system.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute for enabled.
  - `max_pages` (`int`): Instance attribute for max_pages.
  - `dpi_full` (`int`): Instance attribute for dpi_full.
  - `dpi_medium` (`int`): Instance attribute for dpi_medium.
  - `dpi_compressed` (`int`): Instance attribute for dpi_compressed.
  - `threshold_full` (`int`): Instance attribute for threshold_full.
  - `threshold_medium` (`int`): Instance attribute for threshold_medium.
  - `notify_truncated` (`bool`): Instance attribute for notify_truncated.

- **Methods**:
  - `__init__(data) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `get`.

### `_AttachmentVideoConfig`
Represents the `_AttachmentVideoConfig` class in the system.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute for enabled.
  - `max_frames` (`int`): Instance attribute for max_frames.
  - `min_interval_sec` (`float`): Instance attribute for min_interval_sec.

- **Methods**:
  - `__init__(data) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `float` and `get`.

### `_AttachmentEmbedsConfig`
Represents the `_AttachmentEmbedsConfig` class in the system.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute for enabled.
  - `include_images` (`bool`): Instance attribute for include_images.

- **Methods**:
  - `__init__(data) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `get`.

### `AttachmentConfig`
Configuration for attachment and embed processing (base_configs/attachments.yaml).

- **Attributes**:
  - `path` (`Any`): Instance attribute for path.
  - `enabled` (`bool`): Instance attribute for enabled.
  - `max_download_bytes` (`int`): Instance attribute for max_download_bytes.
  - `image` (`Any`): Instance attribute for image.
  - `pdf` (`Any`): Instance attribute for pdf.
  - `video` (`Any`): Instance attribute for video.
  - `embeds` (`Any`): Instance attribute for embeds.

- **Methods**:
  - `__init__(path) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_yaml_file` and `get`.

## Functions

### `_load_yaml_file(path) -> dict`
Safely load a YAML file; report errors via func.report_error and return an empty dict on failure.

### `_get_config_root() -> str`
Read CONFIG_ROOT environment variable.
