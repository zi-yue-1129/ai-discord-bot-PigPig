# File: `cogs/memory/services/event_summarization_service.py`

## Overview
EventSummarizationService: Process Discord message lists into meaningful events using LLM summarization.

## Classes

### `EventMetadata`
Structured metadata for an event.

- **Attributes**:
  - `start_message_id` (`int`): Class attribute representing start_message_id.
  - `end_message_id` (`int`): Class attribute representing end_message_id.
  - `channel_id` (`int`): Class attribute representing channel_id.
  - `guild_id` (`int`): Class attribute representing guild_id.
  - `user_ids` (`List[...]`): Class attribute representing user_ids.
  - `start_timestamp` (`float`): Class attribute representing start_timestamp.
  - `end_timestamp` (`float`): Class attribute representing end_timestamp.
  - `reaction_list` (`List[...]`): Class attribute representing reaction_list.
  - `event_type` (`Optional[...]`): Class attribute representing event_type.

### `Entity`
Represents an entity extracted from the conversation.

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `type` (`str`): Class attribute representing type.
  - `description` (`str`): Class attribute representing description.

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
  - `query_key` (`str`): Class attribute representing query_key.
  - `query_keywords` (`List[...]`): Class attribute representing query_keywords.
  - `query_value` (`str`): Class attribute representing query_value.
  - `start_message_id` (`int`): Class attribute representing start_message_id.
  - `end_message_id` (`int`): Class attribute representing end_message_id.
  - `entities` (`List[...]`): Class attribute representing entities.

### `MemoryFragmentList`
A list of MemoryFragment objects, representing all significant events extracted from a conversation.

Attributes:
    fragments: A list of memory fragments extracted from the conversation.

- **Attributes**:
  - `fragments` (`List[...]`): Class attribute representing fragments.

### `EventSummary`
Structured output for an event summary.

- **Attributes**:
  - `query_key` (`str`): Class attribute representing query_key.
  - `query_keywords` (`List[...]`): Class attribute representing query_keywords.
  - `query_value` (`str`): Class attribute representing query_value.
  - `entities` (`List[...]`): Class attribute representing entities.
  - `metadata` (`EventMetadata`): Class attribute representing metadata.

### `EventSummarizationService`
Service for processing Discord messages into meaningful event summaries using LLM.

This service groups related messages and uses LLM to extract key information
for improved memory retrieval and vectorization.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `settings` (`Any`): Instance attribute for settings.
  - `model_manager` (`Any`): Instance attribute for model_manager.

- **Methods**:
  - `__init__(bot, settings) -> None`: Initialize the Event Summarization Service.
  - `_extract_structured_response(response, expected_model, context) -> Optional[...]`: Unified extractor for structured agent responses.
  - `summarize_events(messages, previous_summary) -> List[...]`: Process a list of messages and extract event summaries using LLM.
  - `_group_messages(messages) -> List[...]`: Group related messages into events.
  - `_process_message_group(messages, previous_summary) -> Optional[...]`: Process a group of messages into an event summary using LLM.
  - `_prepare_message_data(messages) -> List[...]`: Prepare message data for LLM processing.
  - `_get_llm_summary(message_data, previous_summary) -> Optional[...]`: Get event summary from LLM using the episodic memory extractor prompt with structured output.
  - `_create_llm_instance(model_name, force_json) -> Any`: Create a LangChain model instance from a model name string.
  - `_get_system_prompt() -> str`: Get the system prompt from the episodic memory extractor template.
  - `_get_user_prompt_with_messages(message_data, previous_summary) -> str`: Get the user prompt with the prepared message data.
  - `_create_event_summary(messages, memory_fragment) -> Optional[...]`: Create an EventSummary from LLM response and message metadata.
  - `_generate_query_value(summary, query_key) -> str`: Generate query value for vector search.
  - `_create_event_metadata(messages, memory_fragment) -> EventMetadata`: Create event metadata from a group of messages using MemoryFragment info.
