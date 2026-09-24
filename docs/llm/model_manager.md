# File: `llm/model_manager.py`

## Overview
ModelManager: Loads config/llm.yaml and returns ModelFallbackMiddleware or priority lists based on agent_type.

## Classes

### `ModelManager`
Manages LLM model priority by loading configuration and creating ModelFallbackMiddleware.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> None`: No description provided.
  - `_load_config() -> None`: No description provided.
  - `_resolve_priority_list(agent_type: str) -> List[str]`: 將設定檔中指定的 agent_type 轉成 provider:model 字串清單，順序保留
  - `get_model_priority_list(agent_type: str) -> List[str]`: Returns the full list of models for a given agent_type.
  - `get_model(agent_type: str) -> Tuple[Tuple[str, ModelFallbackMiddleware]]`: 公開方法，回傳 (primary_model, ModelFallbackMiddleware)。

## Functions

No module-level functions defined in this file.

