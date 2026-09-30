# File: `llm/model_manager.py`

## Overview
ModelManager: Loads config/llm.yaml and returns ModelFallbackMiddleware or priority lists based on agent_type.

## Classes

### `ModelManager`
Manages LLM model priority by loading configuration and creating ModelFallbackMiddleware.

- **Attributes**:
  - None

- **Methods**:
  - `_load_config(self) -> None`: Method _load_config.
  - `_resolve_priority_list(self, agent_type) -> List[str]`: 將設定檔中指定的 agent_type 轉成 provider:model 字串清單，順序保留
  - `get_model_priority_list(self, agent_type) -> List[str]`: Returns the full list of models for a given agent_type.  This method is useful for streaming fallback scenarios where ModelFallbackMiddleware doesn't work (streaming mode).  Args:     agent_type: The agent type to get models for (e.g., 'info_model').  Returns:     List of model strings in priority order (e.g., ['google_genai:gemini-2.5-flash', 'ollama:gpt-oss:20b']).  Raises:     ValueError: If no model priorities are configured for the agent_type.
  - `get_model(self, agent_type) -> Tuple[str, ModelFallbackMiddleware]`: 公開方法，回傳 (primary_model, ModelFallbackMiddleware)。  若找不到對應的 model_priorities，會丟出 ValueError 以避免呼叫端誤解包 None。 同時在發生錯誤時會使用 func.report_error 上報錯誤以便集中化日誌管理。

## Functions

None

