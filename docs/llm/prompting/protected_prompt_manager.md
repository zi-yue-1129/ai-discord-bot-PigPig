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
  - `PROTECTED_MODULES` (`Set[str]`): Stores data related to PROTECTED_MODULES.
  - `CUSTOMIZABLE_MODULES` (`Set[str]`): Stores data related to CUSTOMIZABLE_MODULES.
  - `base_config_path` (`Any`): Instance attribute managing base_config_path.

- **Methods**:
  - `get_protected_module(module_name) -> Optional[str]`: Get a protected module's content.  Protected modules are ALWAYS loaded from base_configs and cannot be overridden.  Args:     module_name: Name of the module      Returns:     Module content string, or None if not found
  - `get_customizable_module(module_name, custom_content) -> Optional[str]`: Get a customizable module's content.  If custom_content is provided, it overrides the base config. Otherwise, returns the base config content.  Args:     module_name: Name of the module     custom_content: Optional custom content to override base      Returns:     Module content string, or None if not found
  - `set_custom_module(module_name, content) -> bool`: Set custom content for a customizable module.  Args:     module_name: Name of the module     content: Custom content      Returns:     True if successful, False if module is protected or error occurred
  - `compose_system_prompt(module_order, custom_module_contents) -> str`: Compose complete system prompt from modules.  Protected modules are always loaded from base_configs. Customizable modules can be overridden through custom_module_contents.  Args:     module_order: List of module names in desired order.                  Defaults to composition.module_order from base config.     custom_module_contents: Dict mapping module names to custom content.                            Only works for customizable modules.  Returns:     Complete system prompt string
  - `get_base_variables() -> Dict[Tuple[str, str]]`: Get base configuration variables (bot_name, creator, etc.).  Returns:     Dict of base variables
  - `is_module_protected(module_name) -> bool`: Check if a module is protected (cannot be modified).
  - `is_module_customizable(module_name) -> bool`: Check if a module is customizable.
  - `get_module_info() -> Dict[Tuple[str, any]]`: Get information about available modules.  Returns:     Dict containing module categorization and descriptions

## Functions

### `get_protected_prompt_manager(config_path) -> ProtectedPromptManager`
Get or create a ProtectedPromptManager instance.

Args:
    config_path: Path to base config file.
                Defaults to message_agent.yaml in base_configs/prompt/

Returns:
    ProtectedPromptManager instance
