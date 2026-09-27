# File: `llm/context_manager.py`

## Overview
Context manager that returns procedural context string and short-term LangChain messages.

This module implements the new ContextManager per docs/llm/context_manager.md:
- get_context returns Tuple[str, List[BaseMessage]]
- _format_context_for_prompt formats procedural memory only

## Classes

### `ContextManager`
Build procedural context string and return short-term messages list.

- **Attributes**:
  - `short_term_provider` (`Any`): Instance attribute for short_term_provider.
  - `procedural_provider` (`Any`): Instance attribute for procedural_provider.
  - `episodic_provider` (`Any`): Instance attribute for episodic_provider.
  - `knowledge_provider` (`Any`): Instance attribute for knowledge_provider.

- **Methods**:
  - `__init__(short_term_provider, procedural_provider, episodic_provider, knowledge_provider) -> None`: Initialize with memory providers.
  - `get_context(message) -> Tuple[...]`: Return (procedural_context_str, short_term_msgs).
  - `_extract_user_ids_from_messages(messages, message) -> List[...]`: Extract unique user ids from short-term messages and include message author.
  - `_format_context_for_prompt(procedural_memory, channel_name, timestamp, episodic_str, human_time, knowledge) -> str`: Format procedural memory and current state into a single string.
