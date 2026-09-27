# File: `llm/memory/short_term.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `short_term` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `ShortTermMemoryProvider`
Provides short-term memory as a list of LangChain messages.

The provider fetches recent message history from the channel and converts
each Discord message to a LangChain HumanMessage or AIMessage.

- **Attributes**:
  - `limit` (`Any`): Instance attribute for limit.
  - `max_cache_size` (`Any`): Instance attribute for max_cache_size.
  - `bot` (`Any`): Instance attribute for bot.
  - `_attachment_cache` (`OrderedDict`): Instance attribute for _attachment_cache.

- **Methods**:
  - `__init__(bot, limit, max_cache_size) -> Any`: Initialize the provider.
  - `get(message) -> List[...]`: Fetch recent messages and return as LangChain BaseMessage list.
