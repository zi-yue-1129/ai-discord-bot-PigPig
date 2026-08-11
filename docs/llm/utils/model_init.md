# File: `llm/utils/model_init.py`

## Overview
Shared model instantiation helper with vLLM support via the OpenAI-compatible API.

## Functions

### `create_model_instance(model_name, **kwargs) -> BaseChatModel`
Create a LangChain chat model, routing 'vllm:' prefixed names through ChatOpenAI.

init_chat_model has no native 'vllm' provider. Since vLLM exposes an
OpenAI-compatible endpoint, 'vllm:<model>' is rewritten to 'openai:<model>'
with base_url pointed at llm_config.vllm_url and a placeholder api_key
(vLLM does not require a real key).

Args:
    model_name: e.g. 'vllm:gemma4:26b', 'google_genai:gemini-2.5-flash', 'ollama:gemma4:26b'
    **kwargs:   Forwarded to the underlying constructor (max_retries, temperature, …)
