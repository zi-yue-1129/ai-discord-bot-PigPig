# File: `cogs/memory/embedding_providers/__init__.py`

## Overview
Core logic and functionalities for __init__.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Functions

### `list_providers() -> List[str]`
Return registered embedding provider names.

### `get_provider_factory(name) -> Optional[Callable]`
Return the factory callable for a given provider name, or None if not found.

