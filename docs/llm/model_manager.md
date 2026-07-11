# File: `llm/model_manager.py`

## Overview
The `ModelManager` class manages Large Language Model (LLM) priorities and configurations. It provides a centralized way to handle model selection, fallback logic, and priority lists for different agent types (`info_model`, `message_model`, etc.).

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `model_manager.py`, providing vital integrations within the PigPig bot ecosystem.
ModelManager: Loads config/llm.yaml and returns ModelFallbackMiddleware or priority lists based on agent_type.

## Classes

### `ModelManager`
Manages LLM model priority by loading configuration and creating ModelFallbackMiddleware.

- **Methods**:
  - `__init__() -> None`: Performs internal processing logic.
  - `_load_config() -> None`: Performs internal processing logic.
  - `_resolve_priority_list(agent_type: str) -> List[str]`: 將設定檔中指定的 agent_type 轉成 provider:model 字串清單，順序保留
  - `get_model_priority_list(agent_type: str) -> List[str]`: Returns the full list of models for a given agent_type.
  - `get_model(agent_type: str) -> Tuple[Tuple]`: 公開方法，回傳 (primary_model, ModelFallbackMiddleware)。
