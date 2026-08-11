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
  - `short_term_provider` (`Any`): Instance attribute managing short_term_provider.
  - `procedural_provider` (`Any`): Instance attribute managing procedural_provider.
  - `episodic_provider` (`Any`): Instance attribute managing episodic_provider.
  - `knowledge_provider` (`Any`): Instance attribute managing knowledge_provider.

- **Methods**:
  - `get_context(message) -> Tuple[Tuple[str, List[BaseMessage]]]`: Return (procedural_context_str, short_term_msgs).  The short_term_msgs are returned in oldest->newest order as produced by ShortTermMemoryProvider.

