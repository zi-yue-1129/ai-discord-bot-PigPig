# File: `llm/memory/short_term.py`

## Overview
Core file handling responsibilities within the `llm/memory` subsystem.

## Classes

### `ShortTermMemoryProvider`
Provides short-term memory as a list of LangChain messages.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: Any, limit: int, max_cache_size: int) -> Any`: Initialize the provider.
  - `get(message: discord.Message) -> List[BaseMessage]`: Fetch recent messages and return as LangChain BaseMessage list.

## Functions

No module-level functions defined in this file.

