# File: `llm/context_manager.py`

## Overview
The `ContextManager` class is responsible for building procedural context strings, retrieving episodic memories (when available), and managing short-term memory messages for LLM interactions. It serves as a bridge between the Discord message system and the LLM by providing formatted context and conversation history.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `context_manager.py`, providing vital integrations within the PigPig bot ecosystem.
Context manager that returns procedural context string and short-term LangChain messages.

This module implements the new ContextManager per docs/llm/context_manager.md:
- get_context returns Tuple[str, List[BaseMessage]]
- _format_context_for_prompt formats procedural memory only

## Classes

### `ContextManager`
Build procedural context string and return short-term messages list.

- **Attributes**:
  - `short_term_provider` (`Any`): Internal instance state.
  - `procedural_provider` (`Any`): Internal instance state.
  - `episodic_provider` (`Any`): Internal instance state.
  - `knowledge_provider` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(short_term_provider: ShortTermMemoryProvider, procedural_provider: ProceduralMemoryProvider, episodic_provider: Optional[EpisodicMemoryProvider], knowledge_provider: Optional[KnowledgeMemoryProvider]) -> None`: Initialize with memory providers.
  - `get_context(message: discord.Message) -> Tuple[Tuple]`: Return (procedural_context_str, short_term_msgs).
  - `_extract_user_ids_from_messages(messages: List[BaseMessage], message: discord.Message) -> List[str]`: Extract unique user ids from short-term messages and include message author.
  - `_format_context_for_prompt(procedural_memory: ProceduralMemory, channel_name: str, timestamp: float, episodic_str: Optional[str], human_time: Optional[str], knowledge: Optional[KnowledgeMemory]) -> str`: Format procedural memory and current state into a single string.
