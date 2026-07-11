# File: `llm/memory/short_term.py`

## Overview
The `ShortTermMemoryProvider` is responsible for providing the immediate conversational context. It fetches the most recent messages from a Discord channel and converts them into a format that multimodal LLMs can understand.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `short_term.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ShortTermMemoryProvider`
Provides short-term memory as a list of LangChain messages.

The provider fetches recent message history from the channel and converts
each Discord message to a LangChain HumanMessage or AIMessage.

- **Attributes**:
  - `limit` (`Any`): Internal instance state.
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any, limit: int) -> Any`: Initialize the provider.
  - `get(message: discord.Message) -> List[BaseMessage]`: Fetch recent messages and return as LangChain BaseMessage list.
