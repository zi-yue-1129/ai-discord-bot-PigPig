# File: `llm/memory/short_term.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ShortTermMemoryProvider`
Provides short-term memory as a list of LangChain messages.

The provider fetches recent message history from the channel and converts
each Discord message to a LangChain HumanMessage or AIMessage.

- **Attributes**:
  - `limit` (`Any`): Attribute holding limit data.
  - `max_cache_size` (`Any`): Attribute holding max_cache_size data.
  - `bot` (`Any`): Attribute holding bot data.
  - `_attachment_cache` (`OrderedDict`): Attribute holding _attachment_cache data.

- **Methods**:
  - `__init__(bot: Any, limit: int, max_cache_size: int) -> Any`: Initialize the provider.
  - `get(message: discord.Message) -> List[BaseMessage]`: Fetch recent messages and return as LangChain BaseMessage list.

## Functions

No top-level functions defined.
