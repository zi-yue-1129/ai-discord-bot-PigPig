# File: `addons/settings.py`

## Overview
This file is part of utility modules and configurations and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `addons/settings.py`.

## Classes

### `BaseConfig`
Configuration object mapped from config/base.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute path
  - `prefix` (`str`): Instance attribute prefix
  - `activity` (`list`): Instance attribute activity
  - `ipc_server` (`dict`): Instance attribute ipc_server
  - `version` (`str`): Instance attribute version
  - `dashboard` (`dict`): Instance attribute dashboard
  - `logging` (`dict`): Instance attribute logging

- **Methods**:
  - None

### `LLMConfig`
Configuration object mapped from config/llm.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute path
  - `data` (`dict`): Instance attribute data
  - `model_priorities` (`list`): Instance attribute model_priorities
  - `google_search_agent` (`str`): Instance attribute google_search_agent
  - `vllm_url` (`Optional[str]`): Instance attribute vllm_url
  - `ollama_url` (`Optional[str]`): Instance attribute ollama_url
  - `llm_call_timeout` (`float`): Instance attribute llm_call_timeout
  - `reasoning_optimization_prompt` (`str`): Instance attribute reasoning_optimization_prompt

- **Methods**:
  - None

### `UpdateConfig`
Configuration object mapped from config/update.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute path
  - `auto_update` (`dict`): Instance attribute auto_update
  - `security` (`dict`): Instance attribute security
  - `notification` (`dict`): Instance attribute notification
  - `restart` (`dict`): Instance attribute restart
  - `github` (`dict`): Instance attribute github

- **Methods**:
  - None

### `MusicConfig`
Configuration object mapped from config/music.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute path
  - `music_temp_base` (`dict`): Instance attribute music_temp_base
  - `ffmpeg` (`dict`): Instance attribute ffmpeg
  - `youtube_cookies_path` (`str`): Instance attribute youtube_cookies_path

- **Methods**:
  - None

### `PromptConfig`
Configuration object mapped from config/prompt/*.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute path

- **Methods**:
  - `get_system_prompt(self, agent_name, bot_id, message) -> str`: Retrieve system_prompt from agent config and apply dynamic variable replacement.  Args:     agent_name: Name of the agent.     bot_id: Optional bot ID for {bot_id} replacement.     message: Optional Discord message object (reserved for future use).  Returns:     Formatted system_prompt string, or empty string if not found.

### `MemoryConfig`
Memory subsystem configuration object mapped from config/memory.yaml

- **Attributes**:
  - `path` (`Any`): Instance attribute path
  - `enabled` (`bool`): Instance attribute enabled
  - `procedural_cache_ttl` (`float`): Instance attribute procedural_cache_ttl
  - `procedural_max_cache_size` (`int`): Instance attribute procedural_max_cache_size
  - `knowledge_cache_ttl` (`float`): Instance attribute knowledge_cache_ttl
  - `episodic_cache_ttl` (`float`): Instance attribute episodic_cache_ttl
  - `knowledge_max_cache_size` (`int`): Instance attribute knowledge_max_cache_size
  - `episodic_max_cache_size` (`int`): Instance attribute episodic_max_cache_size
  - `procedural_data_path` (`str`): Instance attribute procedural_data_path
  - `episodic_data_path` (`str`): Instance attribute episodic_data_path
  - `vector_store_type` (`str`): Instance attribute vector_store_type
  - `qdrant_url` (`str`): Instance attribute qdrant_url
  - `qdrant_api_key` (`Optional[str]`): Instance attribute qdrant_api_key
  - `qdrant_collection_name` (`str`): Instance attribute qdrant_collection_name
  - `embedding_provider` (`str`): Instance attribute embedding_provider
  - `embedding_model_name` (`str`): Instance attribute embedding_model_name
  - `embedding_dim` (`int`): Instance attribute embedding_dim
  - `vector_search_k` (`int`): Instance attribute vector_search_k
  - `keyword_search_k` (`int`): Instance attribute keyword_search_k
  - `vllm_url` (`Optional[str]`): Instance attribute vllm_url
  - `ollama_url` (`Optional[str]`): Instance attribute ollama_url
  - `provider_options` (`dict`): Instance attribute provider_options
  - `short_term_limit` (`int`): Instance attribute short_term_limit
  - `episodic_top_k` (`int`): Instance attribute episodic_top_k
  - `episodic_max_chars` (`int`): Instance attribute episodic_max_chars
  - `message_threshold` (`int`): Instance attribute message_threshold
  - `time_threshold` (`int`): Instance attribute time_threshold
  - `processing_concurrency` (`int`): Instance attribute processing_concurrency
  - `processing_delay` (`float`): Instance attribute processing_delay

- **Methods**:
  - None

### `_AttachmentImageConfig`
Class representing _AttachmentImageConfig.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute enabled
  - `max_dimension` (`int`): Instance attribute max_dimension

- **Methods**:
  - None

### `_AttachmentPdfConfig`
Class representing _AttachmentPdfConfig.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute enabled
  - `max_pages` (`int`): Instance attribute max_pages
  - `dpi_full` (`int`): Instance attribute dpi_full
  - `dpi_medium` (`int`): Instance attribute dpi_medium
  - `dpi_compressed` (`int`): Instance attribute dpi_compressed
  - `threshold_full` (`int`): Instance attribute threshold_full
  - `threshold_medium` (`int`): Instance attribute threshold_medium
  - `notify_truncated` (`bool`): Instance attribute notify_truncated

- **Methods**:
  - None

### `_AttachmentVideoConfig`
Class representing _AttachmentVideoConfig.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute enabled
  - `max_frames` (`int`): Instance attribute max_frames
  - `min_interval_sec` (`float`): Instance attribute min_interval_sec

- **Methods**:
  - None

### `_AttachmentEmbedsConfig`
Class representing _AttachmentEmbedsConfig.

- **Attributes**:
  - `enabled` (`bool`): Instance attribute enabled
  - `include_images` (`bool`): Instance attribute include_images

- **Methods**:
  - None

### `AttachmentConfig`
Configuration for attachment and embed processing (base_configs/attachments.yaml).

- **Attributes**:
  - `path` (`Any`): Instance attribute path
  - `enabled` (`bool`): Instance attribute enabled
  - `max_download_bytes` (`int`): Instance attribute max_download_bytes
  - `image` (`Any`): Instance attribute image
  - `pdf` (`Any`): Instance attribute pdf
  - `video` (`Any`): Instance attribute video
  - `embeds` (`Any`): Instance attribute embeds

- **Methods**:
  - None

## Functions

### `_load_yaml_file(path) -> dict`
Safely load a YAML file; report errors via func.report_error and return an empty dict on failure.

### `_get_config_root() -> str`
Read CONFIG_ROOT environment variable.  If CONFIG_ROOT is not set, report the issue via func.report_error and fall back to 'config' to allow startup to continue.

