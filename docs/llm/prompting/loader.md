# File: `llm/prompting/loader.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `loader` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `PromptLoader`
YAML 提示配置載入器

- **Attributes**:
  - `config_path` (`Any`): Instance attribute for config_path.
  - `logger` (`Any`): Instance attribute for logger.
  - `_cached_config` (`Optional[...]`): Instance attribute for _cached_config.
  - `_last_loaded` (`Optional[...]`): Instance attribute for _last_loaded.

- **Methods**:
  - `__init__(config_path) -> Any`: 初始化載入器
  - `load_yaml_config() -> Dict[...]`: 載入 YAML 配置檔案
  - `reload_if_changed() -> bool`: 檢查檔案是否變更，如有變更則重新載入
  - `get_last_modified() -> Optional[...]`: 獲取配置檔案的最後修改時間
  - `get_cached_config() -> Optional[...]`: Get the cached configuration.
  - `is_config_loaded() -> bool`: Check whether a configuration has been loaded into the cache.
  - `get_config_section(section_name) -> Optional[...]`: Retrieve a specific section from the configuration.
  - `validate_config_structure(config) -> bool`: 驗證配置結構的基本完整性
