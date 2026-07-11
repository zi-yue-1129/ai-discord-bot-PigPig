# File: `llm/utils/model_init.py`

## Overview
This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `model_init.py`, providing vital integrations within the PigPig bot ecosystem.
Shared model instantiation helper with vLLM support via the OpenAI-compatible API.

## Classes

## Functions

### `create_model_instance(model_name: str) -> BaseChatModel`
Create a LangChain chat model, routing 'vllm:' prefixed names through ChatOpenAI.
