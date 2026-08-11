# File: `llm/memory/short_term.py`

## Overview
The `ShortTermMemoryProvider` is responsible for providing the immediate conversational context. It fetches the most recent messages from a Discord channel and converts them into a format that multimodal LLMs can understand.

## Classes

### `ShortTermMemoryProvider`
Provides short-term memory as a list of LangChain messages.

The provider fetches recent message history from the channel and converts
each Discord message to a LangChain HumanMessage or AIMessage.

- **Attributes**:
  - `limit` (`Any`): Instance attribute managing limit.
  - `bot` (`Any`): Instance attribute managing bot.

- **Methods**:
  - `get(message) -> List[BaseMessage]`: Fetch recent messages and return as LangChain BaseMessage list.  The returned order is oldest -> newest.

