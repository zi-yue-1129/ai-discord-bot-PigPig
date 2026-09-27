# File: `llm/model_manager.py`

## Overview
ModelManager: Loads config/llm.yaml and returns ModelFallbackMiddleware or priority lists based on agent_type.

## Classes

### `ModelManager`
Manages LLM model priority by loading configuration and creating ModelFallbackMiddleware.

- **Methods**:
  - `__init__() -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_load_config`.
  - `_load_config() -> None`: Handles the `_load_config` functionality. Internally, it interacts with methods like `create_task` and `report_error`.
  - `_resolve_priority_list(agent_type) -> List[...]`: 將設定檔中指定的 agent_type 轉成 provider:model 字串清單，順序保留
  - `get_model_priority_list(agent_type) -> List[...]`: Returns the full list of models for a given agent_type.
  - `get_model(agent_type) -> Tuple[...]`: 公開方法，回傳 (primary_model, ModelFallbackMiddleware)。
