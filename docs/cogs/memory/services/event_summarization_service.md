# File: `cogs/memory/services/event_summarization_service.py`

## Overview
EventSummarizationService: Process Discord message lists into meaningful events using LLM summarization.

## Classes

### `EventMetadata`
Structured metadata for an event.

- **Attributes**:
  - `start_message_id` (`int`): Attribute start_message_id
  - `end_message_id` (`int`): Attribute end_message_id
  - `channel_id` (`int`): Attribute channel_id
  - `guild_id` (`int`): Attribute guild_id
  - `user_ids` (`List[int]`): Attribute user_ids
  - `start_timestamp` (`float`): Attribute start_timestamp
  - `end_timestamp` (`float`): Attribute end_timestamp
  - `reaction_list` (`List[Dict[str, Any]]`): Attribute reaction_list
  - `event_type` (`Optional[str]`): Attribute event_type

- **Methods**:
  - None

### `Entity`
Represents an entity extracted from the conversation.

- **Attributes**:
  - `name` (`str`): Attribute name
  - `type` (`str`): Attribute type
  - `description` (`str`): Attribute description

- **Methods**:
  - None

### `MemoryFragment`
Represents a single, distinct memory extracted from a conversation.  Attributes:     query_key: A concise, objective, and human-readable summary of a specific         event, decision, or piece of information from the conversation.     query_keywords: A list of machine-optimized keywords for efficient         database searching and retrieval.     query_value: The detailed content of the memory, suitable for being         returned as a search result.     start_message_id: The ID of the first message in the conversation that         is part of this memory.     end_message_id: The ID of the last message in the conversation that is         part of this memory.

- **Attributes**:
  - `query_key` (`str`): Attribute query_key
  - `query_keywords` (`List[str]`): Attribute query_keywords
  - `query_value` (`str`): Attribute query_value
  - `start_message_id` (`int`): Attribute start_message_id
  - `end_message_id` (`int`): Attribute end_message_id
  - `entities` (`List[Entity]`): Attribute entities

- **Methods**:
  - None

### `MemoryFragmentList`
A list of MemoryFragment objects, representing all significant events extracted from a conversation.  Attributes:     fragments: A list of memory fragments extracted from the conversation.

- **Attributes**:
  - `fragments` (`List[MemoryFragment]`): Attribute fragments

- **Methods**:
  - None

### `EventSummary`
Structured output for an event summary.

- **Attributes**:
  - `query_key` (`str`): Attribute query_key
  - `query_keywords` (`List[str]`): Attribute query_keywords
  - `query_value` (`str`): Attribute query_value
  - `entities` (`List[Dict[str, str]]`): Attribute entities
  - `metadata` (`EventMetadata`): Attribute metadata

- **Methods**:
  - None

### `EventSummarizationService`
Service for processing Discord messages into meaningful event summaries using LLM.  This service groups related messages and uses LLM to extract key information for improved memory retrieval and vectorization.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `settings` (`Any`): Instance attribute settings
  - `model_manager` (`Any`): Instance attribute model_manager

- **Methods**:
  - `_extract_structured_response(self, response, expected_model, context) -> Optional[T]`: Unified extractor for structured agent responses.  Args:     response: Raw response returned by agent.ainvoke()     expected_model: Expected Pydantic model class     context: Logging context      Returns:     Parsed model instance on success, None on failure.
  - `summarize_events(self, messages, previous_summary) -> List[EventSummary]`: Process a list of messages and extract event summaries using LLM.  Args:     messages: List of Discord messages to process     previous_summary: Summary of previous events for context      Returns:     List of EventSummary objects representing extracted events
  - `_group_messages(self, messages) -> List[List[discord.Message]]`: Group related messages into events.  Current implementation: treat all messages as a single event. Future implementation: implement sophisticated grouping algorithms.  Args:     messages: List of Discord messages      Returns:     List of message groups, each group is a list of messages
  - `_process_message_group(self, messages, previous_summary) -> Optional[List[EventSummary]]`: Process a group of messages into an event summary using LLM.  Args:     messages: Group of related Discord messages     previous_summary: Context from previous events      Returns:     EventSummary object or None if processing failed
  - `_prepare_message_data(self, messages) -> List[Dict[str, Any]]`: Prepare message data for LLM processing.  Args:     messages: List of Discord messages      Returns:     List of message dictionaries with author, timestamp, and content
  - `_get_llm_summary(self, message_data, previous_summary) -> Optional[MemoryFragmentList]`: Get event summary from LLM using the episodic memory extractor prompt with structured output.  Uses circuit breaker to avoid calling models that are known to be failing.  Args:     message_data: Prepared message data for LLM processing     previous_summary: Context from previous events      Returns:     MemoryFragmentList object or None if failed
  - `_create_llm_instance(self, model_name, force_json) -> Any`: Create a LangChain model instance from a model name string.  Args:     model_name: Model identifier (e.g. 'ollama:gpt-oss:20b')     force_json: Whether to force the model into JSON mode if supported      Returns:     LangChain chat model instance
  - `_get_system_prompt(self) -> str`: Get the system prompt from the episodic memory extractor template.
  - `_get_user_prompt_with_messages(self, message_data, previous_summary) -> str`: Get the user prompt with the prepared message data.  Args:     message_data: Prepared message data     previous_summary: Context from previous events      Returns:     User prompt string with message data
  - `_create_event_summary(self, messages, memory_fragment) -> Optional[EventSummary]`: Create an EventSummary from LLM response and message metadata.  Args:     messages: Original message group     memory_fragment: Structured response from LLM      Returns:     EventSummary object or None if creation failed
  - `_generate_query_value(self, summary, query_key) -> str`: Generate query value for vector search.  Args:     summary: Event summary     query_key: Query key      Returns:     Generated query value
  - `_create_event_metadata(self, messages, memory_fragment) -> EventMetadata`: Create event metadata from a group of messages using MemoryFragment info.  Args:     messages: List of Discord messages     memory_fragment: MemoryFragment containing start_message_id and end_message_id      Returns:     EventMetadata object

## Functions

None
