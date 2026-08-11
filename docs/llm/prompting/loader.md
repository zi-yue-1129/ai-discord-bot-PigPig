# File: `llm/prompting/loader.py`

## Overview
The `PromptLoader` class is responsible for loading and managing YAML configuration files for the prompting system. It provides file change detection, caching mechanisms, and configuration validation capabilities.

## Classes

### `PromptLoader`
YAML 提示配置載入器

- **Attributes**:
  - `config_path` (`Any`): Instance attribute managing config_path.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `load_yaml_config() -> Dict[Tuple[str, Any]]`: 載入 YAML 配置檔案  Returns:     解析後的配置字典      Raises:     FileNotFoundError: 配置檔案不存在     yaml.YAMLError: YAML 解析錯誤
  - `reload_if_changed() -> bool`: 檢查檔案是否變更，如有變更則重新載入  Returns:     bool: 是否重新載入了配置
  - `get_last_modified() -> Optional[datetime]`: 獲取配置檔案的最後修改時間  Returns:     最後修改時間，如果檔案不存在則返回 None
  - `get_cached_config() -> Optional[Dict[Tuple[str, Any]]]`: Get the cached configuration.  This will attempt to detect whether the underlying YAML file has been modified and reload it if necessary to avoid returning stale data.
  - `is_config_loaded() -> bool`: Check whether a configuration has been loaded into the cache.
  - `get_config_section(section_name) -> Optional[Dict[Tuple[str, Any]]]`: Retrieve a specific section from the configuration.  If the configuration has not been loaded yet, load it. If it has been loaded, attempt to reload if the file changed to ensure latest values.
  - `validate_config_structure(config) -> bool`: 驗證配置結構的基本完整性  Args:     config: 要驗證的配置字典      Returns:     bool: 配置結構是否有效

