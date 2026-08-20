### Create File: docs/llm/utils/model_init.md
# File: `llm/utils/model_init.py`

## Overview
Shared model instantiation helper with vLLM support via the OpenAI-compatible API.

## Classes

No classes defined in this file.

## Functions

### `create_model_instance(model_name, **kwargs) -> BaseChatModel`
Create a LangChain chat model, routing 'vllm:' prefixed names through ChatOpenAI.  init_chat_model has no native 'vllm' provider. Since vLLM exposes an OpenAI-compatible endpoint, 'vllm:<model>' is rewritten to 'openai:<model>' with base_url pointed at llm_config.vllm_url and the api_key vLLM was launched with (VLLM_API_KEY in .env; falls back to the "EMPTY" placeholder vLLM accepts when --api-key is not set).  Args:     model_name: e.g. 'vllm:gemma4:26b', 'google_genai:gemini-2.5-flash', 'ollama:gemma4:26b'     **kwargs:   Forwarded to the underlying constructor (max_retries, temperature, …)
