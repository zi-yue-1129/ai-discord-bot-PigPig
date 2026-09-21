# File: `cogs/memory/services/vectorization_service.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

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
  - `bot` (`Any`): Attribute holding bot data.
  - `storage` (`Any`): Attribute holding storage data.
  - `vector_manager` (`Any`): Attribute holding vector_manager data.
  - `settings` (`Any`): Attribute holding settings data.

- **Methods**:
  - `__init__(bot: Any, storage: StorageInterface, vector_manager: Any, settings: MemoryConfig) -> None`: Executes __init__ logic.
  - `process_event_summaries(event_summaries: List[EventSummary]) -> None`: Process a list of EventSummary objects and store them in the vector database.
  - `_convert_event_summaries_to_fragments(event_summaries: List[EventSummary]) -> List[MemoryFragment]`: Convert EventSummary objects to MemoryFragment objects.

## Functions

No top-level functions defined.
