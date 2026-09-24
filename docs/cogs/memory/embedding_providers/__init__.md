# File: `cogs/memory/embedding_providers/__init__.py`

## Overview
Core file handling responsibilities within the `cogs/memory/embedding_providers` subsystem.

## Classes

No classes defined in this file.

## Functions

### `_import_all_providers() -> None`
Import all modules in this package so that registration decorators run.

### `list_providers() -> List[str]`
Return registered embedding provider names.

### `get_provider_factory(name: str) -> Optional[Callable]`
Return the factory callable for a given provider name, or None if not found.
