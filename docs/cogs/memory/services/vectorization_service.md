# File: `cogs/memory/services/vectorization_service.py`

## Overview
Core file handling responsibilities within the `cogs/memory/services` subsystem.

## Classes

### `VectorizationService`
Service responsible for converting EventSummary objects into MemoryFragment objects,

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: Any, storage: StorageInterface, vector_manager: Any, settings: MemoryConfig) -> None`: No description provided.
  - `process_event_summaries(event_summaries: List[EventSummary]) -> None`: Process a list of EventSummary objects and store them in the vector database.
  - `_convert_event_summaries_to_fragments(event_summaries: List[EventSummary]) -> List[MemoryFragment]`: Convert EventSummary objects to MemoryFragment objects.

## Functions

No module-level functions defined in this file.
