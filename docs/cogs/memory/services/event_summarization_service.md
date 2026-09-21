# File: `cogs/memory/services/event_summarization_service.py`

## Overview
EventSummarizationService: Process Discord message lists into meaningful events using LLM summarization.

## Classes

### `EventMetadata`
Structured metadata for an event.

- **Attributes**:
  - `start_message_id` (`int`): Attribute holding start_message_id data.
  - `end_message_id` (`int`): Attribute holding end_message_id data.
  - `channel_id` (`int`): Attribute holding channel_id data.
  - `guild_id` (`int`): Attribute holding guild_id data.
  - `user_ids` (`List[int]`): Attribute holding user_ids data.
  - `start_timestamp` (`float`): Attribute holding start_timestamp data.
  - `end_timestamp` (`float`): Attribute holding end_timestamp data.
  - `reaction_list` (`List[Dict[Tuple[str, Any]]]`): Attribute holding reaction_list data.
  - `event_type` (`Optional[str]`): Attribute holding event_type data.

- **Methods**:
  - None specified.

### `Entity`
Represents an entity extracted from the conversation.

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `type` (`str`): Attribute holding type data.
  - `description` (`str`): Attribute holding description data.

- **Methods**:
  - None specified.

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
  - `query_key` (`str`): Attribute holding query_key data.
  - `query_keywords` (`List[str]`): Attribute holding query_keywords data.
  - `query_value` (`str`): Attribute holding query_value data.
  - `start_message_id` (`int`): Attribute holding start_message_id data.
  - `end_message_id` (`int`): Attribute holding end_message_id data.
  - `entities` (`List[Entity]`): Attribute holding entities data.

- **Methods**:
  - None specified.

### `MemoryFragmentList`
A list of MemoryFragment objects, representing all significant events extracted from a conversation.

Attributes:
    fragments: A list of memory fragments extracted from the conversation.

- **Attributes**:
  - `fragments` (`List[MemoryFragment]`): Attribute holding fragments data.

- **Methods**:
  - None specified.

### `EventSummary`
Structured output for an event summary.

- **Attributes**:
  - `query_key` (`str`): Attribute holding query_key data.
  - `query_keywords` (`List[str]`): Attribute holding query_keywords data.
  - `query_value` (`str`): Attribute holding query_value data.
  - `entities` (`List[Dict[Tuple[str, str]]]`): Attribute holding entities data.
  - `metadata` (`EventMetadata`): Attribute holding metadata data.

- **Methods**:
  - None specified.

### `EventSummarizationService`
Service for processing Discord messages into meaningful event summaries using LLM.

This service groups related messages and uses LLM to extract key information
for improved memory retrieval and vectorization.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `settings` (`Any`): Attribute holding settings data.
  - `model_manager` (`Any`): Attribute holding model_manager data.

- **Methods**:
  - `__init__(bot: discord.Client, settings: MemoryConfig) -> None`: Initialize the Event Summarization Service.
  - `_extract_structured_response(response: Any, expected_model: Type[T], context: str) -> Optional[T]`: Unified extractor for structured agent responses.
  - `summarize_events(messages: List[discord.Message], previous_summary: str) -> List[EventSummary]`: Process a list of messages and extract event summaries using LLM.
  - `_group_messages(messages: List[discord.Message]) -> List[List[discord.Message]]`: Group related messages into events.
  - `_process_message_group(messages: List[discord.Message], previous_summary: str) -> Optional[List[EventSummary]]`: Process a group of messages into an event summary using LLM.
  - `_prepare_message_data(messages: List[discord.Message]) -> List[Dict[Tuple[str, Any]]]`: Prepare message data for LLM processing.
  - `_get_llm_summary(message_data: List[Dict[Tuple[str, Any]]], previous_summary: str) -> Optional[MemoryFragmentList]`: Get event summary from LLM using the episodic memory extractor prompt with structured output.
  - `_create_llm_instance(model_name: str, force_json: bool) -> Any`: Create a LangChain model instance from a model name string.
  - `_get_system_prompt() -> str`: Get the system prompt from the episodic memory extractor template.
  - `_get_user_prompt_with_messages(message_data: List[Dict[Tuple[str, Any]]], previous_summary: str) -> str`: Get the user prompt with the prepared message data.
  - `_create_event_summary(messages: List[discord.Message], memory_fragment: MemoryFragment) -> Optional[EventSummary]`: Create an EventSummary from LLM response and message metadata.
  - `_generate_query_value(summary: str, query_key: str) -> str`: Generate query value for vector search.
  - `_create_event_metadata(messages: List[discord.Message], memory_fragment: MemoryFragment) -> EventMetadata`: Create event metadata from a group of messages using MemoryFragment info.

## Functions

No top-level functions defined.
