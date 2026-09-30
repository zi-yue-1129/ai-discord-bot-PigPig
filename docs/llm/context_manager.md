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
  - `short_term_provider` (`Any`): Instance attribute short_term_provider
  - `procedural_provider` (`Any`): Instance attribute procedural_provider
  - `episodic_provider` (`Any`): Instance attribute episodic_provider
  - `knowledge_provider` (`Any`): Instance attribute knowledge_provider

- **Methods**:
  - `get_context(self, message) -> Tuple[str, List[BaseMessage]]`: Return (procedural_context_str, short_term_msgs).  The short_term_msgs are returned in oldest->newest order as produced by ShortTermMemoryProvider.
  - `_extract_user_ids_from_messages(self, messages, message) -> List[str]`: Extract unique user ids from short-term messages and include message author.  ShortTerm messages may not include explicit user ids. We attempt a best-effort extraction by parsing numeric ids in leading bracketed segments like "[123456]".
  - `_format_context_for_prompt(self, procedural_memory, channel_name, timestamp, episodic_str, human_time, knowledge) -> str`: Format procedural memory and current state into a single string.  This method intentionally does NOT serialize short-term memory; callers receive STM as LangChain messages separately. The `timestamp` parameter is a numeric UNIX timestamp (float seconds). If a human-readable form is needed, callers should format it explicitly.

## Functions

None

