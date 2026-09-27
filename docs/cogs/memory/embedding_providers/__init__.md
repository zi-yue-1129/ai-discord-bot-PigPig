# File: `cogs/memory/embedding_providers/__init__.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `__init__` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Functions

### `_import_all_providers() -> None`
Import all modules in this package so that registration decorators run.

### `list_providers() -> List[...]`
Return registered embedding provider names.

### `get_provider_factory(name) -> Optional[...]`
Return the factory callable for a given provider name, or None if not found.
