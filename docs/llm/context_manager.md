# File: `llm/context_manager.py`

## Overview
Context manager that returns procedural context string and short-term LangChain messages.

## Classes

### `ContextManager`
Build procedural context string and return short-term messages list.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(short_term_provider: ShortTermMemoryProvider, procedural_provider: ProceduralMemoryProvider, episodic_provider: Optional[EpisodicMemoryProvider], knowledge_provider: Optional[KnowledgeMemoryProvider]) -> None`: Initialize with memory providers.
  - `get_context(message: discord.Message) -> Tuple[Tuple[str, List[BaseMessage]]]`: Return (procedural_context_str, short_term_msgs).
  - `_extract_user_ids_from_messages(messages: List[BaseMessage], message: discord.Message) -> List[str]`: Extract unique user ids from short-term messages and include message author.
  - `_format_context_for_prompt(procedural_memory: ProceduralMemory, channel_name: str, timestamp: float, episodic_str: Optional[str], human_time: Optional[str], knowledge: Optional[KnowledgeMemory]) -> str`: Format procedural memory and current state into a single string.

## Functions

No module-level functions defined in this file.

