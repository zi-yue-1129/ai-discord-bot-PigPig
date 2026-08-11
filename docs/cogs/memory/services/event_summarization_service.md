# File: `cogs/memory/services/event_summarization_service.py`

## Overview
EventSummarizationService: Process Discord message lists into meaningful events using LLM summarization.

## Classes

### `EventMetadata`
Structured metadata for an event.

- **Attributes**:
  - `start_message_id` (`int`): Stores data related to start_message_id.
  - `end_message_id` (`int`): Stores data related to end_message_id.
  - `channel_id` (`int`): Stores data related to channel_id.
  - `guild_id` (`int`): Stores data related to guild_id.
  - `user_ids` (`List[int]`): Stores data related to user_ids.
  - `start_timestamp` (`float`): Stores data related to start_timestamp.
  - `end_timestamp` (`float`): Stores data related to end_timestamp.
  - `reaction_list` (`List[Dict[Tuple[str, Any]]]`): Stores data related to reaction_list.
  - `event_type` (`Optional[str]`): Stores data related to event_type.

### `Entity`
Represents an entity extracted from the conversation.

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `type` (`str`): Stores data related to type.
  - `description` (`str`): Stores data related to description.

### `MemoryFragment`
Represents a single, distinct memory extracted from a conversation.

Attributes:
    query_key: A concise, objective, and human-readable summary of a specific
        event, decision, or piece of information from the conversation.
    query_keywords: A list of machine-optimized keywords for efficient
        database searching and retrieval.
    query_value: The detailed content of the memory, suitable for being
        returned as a search result.
    start_message_id: The ID of the first message in the conversation that
        is part of this memory.
    end_message_id: The ID of the last message in the conversation that is
        part of this memory.

- **Attributes**:
  - `query_key` (`str`): Stores data related to query_key.
  - `query_keywords` (`List[str]`): Stores data related to query_keywords.
  - `query_value` (`str`): Stores data related to query_value.
  - `start_message_id` (`int`): Stores data related to start_message_id.
  - `end_message_id` (`int`): Stores data related to end_message_id.
  - `entities` (`List[Entity]`): Stores data related to entities.

### `MemoryFragmentList`
A list of MemoryFragment objects, representing all significant events extracted from a conversation.

Attributes:
    fragments: A list of memory fragments extracted from the conversation.

- **Attributes**:
  - `fragments` (`List[MemoryFragment]`): Stores data related to fragments.

### `EventSummary`
Structured output for an event summary.

- **Attributes**:
  - `query_key` (`str`): Stores data related to query_key.
  - `query_keywords` (`List[str]`): Stores data related to query_keywords.
  - `query_value` (`str`): Stores data related to query_value.
  - `entities` (`List[Dict[Tuple[str, str]]]`): Stores data related to entities.
  - `metadata` (`EventMetadata`): Stores data related to metadata.

### `EventSummarizationService`
Service for processing Discord messages into meaningful event summaries using LLM.

This service groups related messages and uses LLM to extract key information
for improved memory retrieval and vectorization.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `settings` (`Any`): Instance attribute managing settings.
  - `model_manager` (`Any`): Instance attribute managing model_manager.

- **Methods**:
  - `summarize_events(messages, previous_summary) -> List[EventSummary]`: Process a list of messages and extract event summaries using LLM.  Args:     messages: List of Discord messages to process     previous_summary: Summary of previous events for context      Returns:     List of EventSummary objects representing extracted events
