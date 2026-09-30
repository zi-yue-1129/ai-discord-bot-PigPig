# File: `cogs/memory/services/vectorization_service.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/services/vectorization_service.py`.

## Classes

### `VectorizationService`
Service responsible for converting EventSummary objects into MemoryFragment objects, uploading them to the vector store.  Dependencies are injected to keep this service testable and decoupled:   - bot: used only for contextual logging if needed   - storage: implements StorageInterface   - vector_manager: object that exposes .store.add_memories(...)   - settings: MemoryConfig

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `storage` (`Any`): Instance attribute storage
  - `vector_manager` (`Any`): Instance attribute vector_manager
  - `settings` (`Any`): Instance attribute settings

- **Methods**:
  - `process_event_summaries(self, event_summaries) -> None`: Process a list of EventSummary objects and store them in the vector database.  Args:     event_summaries: List of EventSummary objects to process and store      Returns:     None
  - `_convert_event_summaries_to_fragments(self, event_summaries) -> List[MemoryFragment]`: Convert EventSummary objects to MemoryFragment objects.  Args:     event_summaries: List of EventSummary objects from EventSummarizationService      Returns:     List of MemoryFragment objects

## Functions

None
