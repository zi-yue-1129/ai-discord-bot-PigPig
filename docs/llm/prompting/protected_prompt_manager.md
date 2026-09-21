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
  - `PROTECTED_MODULES` (`Set[str]`): Attribute holding PROTECTED_MODULES data.
  - `CUSTOMIZABLE_MODULES` (`Set[str]`): Attribute holding CUSTOMIZABLE_MODULES data.
  - `base_config_path` (`Any`): Attribute holding base_config_path data.
  - `base_config` (`Dict`): Attribute holding base_config data.
  - `custom_modules` (`Dict[Tuple[str, str]]`): Attribute holding custom_modules data.

- **Methods**:
  - `__init__(base_config_path: Optional[str]) -> Any`: Initialize the protected prompt manager.
  - `_load_base_config() -> None`: Load base configuration from YAML file.
  - `get_protected_module(module_name: str) -> Optional[str]`: Get a protected module's content.
  - `get_customizable_module(module_name: str, custom_content: Optional[str]) -> Optional[str]`: Get a customizable module's content.
  - `set_custom_module(module_name: str, content: str) -> bool`: Set custom content for a customizable module.
  - `compose_system_prompt(module_order: Optional[List[str]], custom_module_contents: Optional[Dict[Tuple[str, str]]]) -> str`: Compose complete system prompt from modules.
  - `get_base_variables() -> Dict[Tuple[str, str]]`: Get base configuration variables (bot_name, creator, etc.).
  - `is_module_protected(module_name: str) -> bool`: Check if a module is protected (cannot be modified).
  - `is_module_customizable(module_name: str) -> bool`: Check if a module is customizable.
  - `get_module_info() -> Dict[Tuple[str, any]]`: Get information about available modules.

## Functions

### `get_protected_prompt_manager(config_path: Optional[str]) -> ProtectedPromptManager`
Get or create a ProtectedPromptManager instance.

Args:
    config_path: Path to base config file.
                Defaults to message_agent.yaml in base_configs/prompt/

Returns:
    ProtectedPromptManager instance
