# File: `llm/memory/short_term.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/memory/short_term.py`.

## Classes

### `ShortTermMemoryProvider`
Provides short-term memory as a list of LangChain messages.  The provider fetches recent message history from the channel and converts each Discord message to a LangChain HumanMessage or AIMessage.

- **Attributes**:
  - `limit` (`Any`): Instance attribute limit
  - `max_cache_size` (`Any`): Instance attribute max_cache_size
  - `bot` (`Any`): Instance attribute bot
  - `_attachment_cache` (`OrderedDict`): Instance attribute _attachment_cache

- **Methods**:
  - `get(self, message) -> List[BaseMessage]`: Fetch recent messages and return as LangChain BaseMessage list.  The returned order is oldest -> newest.

## Functions

None

