# File: `addons/settings.py`

## Overview
This file is part of the addons subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `BaseConfig`
Configuration object mapped from config/base.yaml

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.
  - `prefix` (`str`): Attribute holding prefix data.
  - `activity` (`list`): Attribute holding activity data.
  - `ipc_server` (`dict`): Attribute holding ipc_server data.
  - `version` (`str`): Attribute holding version data.
  - `dashboard` (`dict`): Attribute holding dashboard data.
  - `logging` (`dict`): Attribute holding logging data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.

### `LLMConfig`
Configuration object mapped from config/llm.yaml

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.
  - `data` (`dict`): Attribute holding data data.
  - `model_priorities` (`list`): Attribute holding model_priorities data.
  - `google_search_agent` (`str`): Attribute holding google_search_agent data.
  - `vllm_url` (`Optional[str]`): Attribute holding vllm_url data.
  - `ollama_url` (`Optional[str]`): Attribute holding ollama_url data.
  - `llm_call_timeout` (`float`): Attribute holding llm_call_timeout data.
  - `reasoning_optimization_prompt` (`str`): Attribute holding reasoning_optimization_prompt data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.

### `UpdateConfig`
Configuration object mapped from config/update.yaml

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.
  - `auto_update` (`dict`): Attribute holding auto_update data.
  - `security` (`dict`): Attribute holding security data.
  - `notification` (`dict`): Attribute holding notification data.
  - `restart` (`dict`): Attribute holding restart data.
  - `github` (`dict`): Attribute holding github data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.

### `MusicConfig`
Configuration object mapped from config/music.yaml

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.
  - `music_temp_base` (`dict`): Attribute holding music_temp_base data.
  - `ffmpeg` (`dict`): Attribute holding ffmpeg data.
  - `youtube_cookies_path` (`str`): Attribute holding youtube_cookies_path data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.

### `PromptConfig`
Configuration object mapped from config/prompt/*.yaml

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.
  - `get_system_prompt(agent_name: str, bot_id: int | None, message) -> str`: Retrieve system_prompt from agent config and apply dynamic variable replacement.

### `MemoryConfig`
Memory subsystem configuration object mapped from config/memory.yaml

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.
  - `enabled` (`bool`): Attribute holding enabled data.
  - `procedural_cache_ttl` (`float`): Attribute holding procedural_cache_ttl data.
  - `procedural_max_cache_size` (`int`): Attribute holding procedural_max_cache_size data.
  - `knowledge_cache_ttl` (`float`): Attribute holding knowledge_cache_ttl data.
  - `episodic_cache_ttl` (`float`): Attribute holding episodic_cache_ttl data.
  - `knowledge_max_cache_size` (`int`): Attribute holding knowledge_max_cache_size data.
  - `episodic_max_cache_size` (`int`): Attribute holding episodic_max_cache_size data.
  - `procedural_data_path` (`str`): Attribute holding procedural_data_path data.
  - `episodic_data_path` (`str`): Attribute holding episodic_data_path data.
  - `vector_store_type` (`str`): Attribute holding vector_store_type data.
  - `qdrant_url` (`str`): Attribute holding qdrant_url data.
  - `qdrant_api_key` (`Optional[str]`): Attribute holding qdrant_api_key data.
  - `qdrant_collection_name` (`str`): Attribute holding qdrant_collection_name data.
  - `embedding_provider` (`str`): Attribute holding embedding_provider data.
  - `embedding_model_name` (`str`): Attribute holding embedding_model_name data.
  - `embedding_dim` (`int`): Attribute holding embedding_dim data.
  - `vector_search_k` (`int`): Attribute holding vector_search_k data.
  - `keyword_search_k` (`int`): Attribute holding keyword_search_k data.
  - `vllm_url` (`Optional[str]`): Attribute holding vllm_url data.
  - `ollama_url` (`Optional[str]`): Attribute holding ollama_url data.
  - `provider_options` (`dict`): Attribute holding provider_options data.
  - `short_term_limit` (`int`): Attribute holding short_term_limit data.
  - `episodic_top_k` (`int`): Attribute holding episodic_top_k data.
  - `episodic_max_chars` (`int`): Attribute holding episodic_max_chars data.
  - `message_threshold` (`int`): Attribute holding message_threshold data.
  - `time_threshold` (`int`): Attribute holding time_threshold data.
  - `processing_concurrency` (`int`): Attribute holding processing_concurrency data.
  - `processing_delay` (`float`): Attribute holding processing_delay data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.

### `_AttachmentImageConfig`
Core class implementation.

- **Attributes**:
  - `enabled` (`bool`): Attribute holding enabled data.
  - `max_dimension` (`int`): Attribute holding max_dimension data.

- **Methods**:
  - `__init__(data: dict) -> None`: Executes __init__ logic.

### `_AttachmentPdfConfig`
Core class implementation.

- **Attributes**:
  - `enabled` (`bool`): Attribute holding enabled data.
  - `max_pages` (`int`): Attribute holding max_pages data.
  - `dpi_full` (`int`): Attribute holding dpi_full data.
  - `dpi_medium` (`int`): Attribute holding dpi_medium data.
  - `dpi_compressed` (`int`): Attribute holding dpi_compressed data.
  - `threshold_full` (`int`): Attribute holding threshold_full data.
  - `threshold_medium` (`int`): Attribute holding threshold_medium data.
  - `notify_truncated` (`bool`): Attribute holding notify_truncated data.

- **Methods**:
  - `__init__(data: dict) -> None`: Executes __init__ logic.

### `_AttachmentVideoConfig`
Core class implementation.

- **Attributes**:
  - `enabled` (`bool`): Attribute holding enabled data.
  - `max_frames` (`int`): Attribute holding max_frames data.
  - `min_interval_sec` (`float`): Attribute holding min_interval_sec data.

- **Methods**:
  - `__init__(data: dict) -> None`: Executes __init__ logic.

### `_AttachmentEmbedsConfig`
Core class implementation.

- **Attributes**:
  - `enabled` (`bool`): Attribute holding enabled data.
  - `include_images` (`bool`): Attribute holding include_images data.

- **Methods**:
  - `__init__(data: dict) -> None`: Executes __init__ logic.

### `AttachmentConfig`
Configuration for attachment and embed processing (base_configs/attachments.yaml).

- **Attributes**:
  - `path` (`Any`): Attribute holding path data.
  - `enabled` (`bool`): Attribute holding enabled data.
  - `max_download_bytes` (`int`): Attribute holding max_download_bytes data.
  - `image` (`Any`): Attribute holding image data.
  - `pdf` (`Any`): Attribute holding pdf data.
  - `video` (`Any`): Attribute holding video data.
  - `embeds` (`Any`): Attribute holding embeds data.

- **Methods**:
  - `__init__(path: str) -> None`: Executes __init__ logic.

## Functions

### `_load_yaml_file(path: str) -> dict`
Safely load a YAML file; report errors via func.report_error and return an empty dict on failure.

### `_get_config_root() -> str`
Read CONFIG_ROOT environment variable.

If CONFIG_ROOT is not set, report the issue via func.report_error and
fall back to 'config' to allow startup to continue.
