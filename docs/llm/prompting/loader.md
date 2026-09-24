# File: `llm/prompting/loader.py`

## Overview
Core file handling responsibilities within the `llm/prompting` subsystem.

## Classes

### `PromptLoader`
YAML 提示配置載入器

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(config_path: str) -> Any`: 初始化載入器
  - `load_yaml_config() -> Dict[Tuple[str, Any]]`: 載入 YAML 配置檔案
  - `reload_if_changed() -> bool`: 檢查檔案是否變更，如有變更則重新載入
  - `get_last_modified() -> Optional[datetime]`: 獲取配置檔案的最後修改時間
  - `get_cached_config() -> Optional[Dict[Tuple[str, Any]]]`: Get the cached configuration.
  - `is_config_loaded() -> bool`: Check whether a configuration has been loaded into the cache.
  - `get_config_section(section_name: str) -> Optional[Dict[Tuple[str, Any]]]`: Retrieve a specific section from the configuration.
  - `validate_config_structure(config: Dict[Tuple[str, Any]]) -> bool`: 驗證配置結構的基本完整性

## Functions

No module-level functions defined in this file.

