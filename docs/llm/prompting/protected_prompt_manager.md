# File: `llm/prompting/protected_prompt_manager.py`

## Overview
Protected Prompt Management System.

This module implements a two-tier prompt system:
1. System-level prompts (protected, from base_configs)
2. User-customizable prompts (can be overridden)

The system ensures critical prompts like Discord format instructions,
context handling, and input parsing cannot be accidentally modified by users.

## Classes

### `ProtectedPromptManager`
Manages system-level (protected) and user-customizable prompts.

Protected modules are always loaded from base_configs and cannot be overridden.
User-customizable modules can be modified through database or custom configs.

- **Attributes**:
  - `PROTECTED_MODULES` (`Set[...]`): Class attribute representing PROTECTED_MODULES.
  - `CUSTOMIZABLE_MODULES` (`Set[...]`): Class attribute representing CUSTOMIZABLE_MODULES.
  - `base_config_path` (`Any`): Instance attribute for base_config_path.
  - `base_config` (`Dict`): Instance attribute for base_config.
  - `custom_modules` (`Dict[...]`): Instance attribute for custom_modules.

- **Methods**:
  - `__init__(base_config_path) -> Any`: Initialize the protected prompt manager.
  - `_load_base_config() -> None`: Load base configuration from YAML file.
  - `get_protected_module(module_name) -> Optional[...]`: Get a protected module's content.
  - `get_customizable_module(module_name, custom_content) -> Optional[...]`: Get a customizable module's content.
  - `set_custom_module(module_name, content) -> bool`: Set custom content for a customizable module.
  - `compose_system_prompt(module_order, custom_module_contents) -> str`: Compose complete system prompt from modules.
  - `get_base_variables() -> Dict[...]`: Get base configuration variables (bot_name, creator, etc.).
  - `is_module_protected(module_name) -> bool`: Check if a module is protected (cannot be modified).
  - `is_module_customizable(module_name) -> bool`: Check if a module is customizable.
  - `get_module_info() -> Dict[...]`: Get information about available modules.

## Functions

### `get_protected_prompt_manager(config_path) -> ProtectedPromptManager`
Get or create a ProtectedPromptManager instance.
