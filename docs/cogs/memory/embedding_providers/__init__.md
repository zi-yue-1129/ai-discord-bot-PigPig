# File: `cogs/memory/embedding_providers/__init__.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/embedding_providers/__init__.py`.

## Classes

None

## Functions

### `_import_all_providers() -> None`
Import all modules in this package so that registration decorators run. Provider modules should call register_embedding_provider when defined.

### `list_providers() -> List[str]`
Return registered embedding provider names.

### `get_provider_factory(name) -> Optional[Callable]`
Return the factory callable for a given provider name, or None if not found.

