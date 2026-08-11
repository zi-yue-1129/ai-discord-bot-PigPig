# File: `cogs/memory/services/vectorization_service.py`

## Overview
Core logic and functionalities for vectorization_service.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `VectorizationService`
Service responsible for converting EventSummary objects into MemoryFragment objects,
uploading them to the vector store.

Dependencies are injected to keep this service testable and decoupled:
  - bot: used only for contextual logging if needed
  - storage: implements StorageInterface
  - vector_manager: object that exposes .store.add_memories(...)
  - settings: MemoryConfig

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `storage` (`Any`): Instance attribute managing storage.
  - `vector_manager` (`Any`): Instance attribute managing vector_manager.
  - `settings` (`Any`): Instance attribute managing settings.

- **Methods**:
  - `process_event_summaries(event_summaries) -> None`: Process a list of EventSummary objects and store them in the vector database.  Args:     event_summaries: List of EventSummary objects to process and store      Returns:     None
