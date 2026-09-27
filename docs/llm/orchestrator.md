# File: `llm/orchestrator.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `orchestrator` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `DirectToolOutputMiddleware`
Represents the `DirectToolOutputMiddleware` class in the system.

- **Methods**:
  - `after_tools(state, runtime) -> Any`: Handles the `after_tools` functionality. Internally, it interacts with methods like `hook_config`.

### `Orchestrator`
Orchestrator updated to accept ContextManager's new return type.

ContextManager.get_context now returns Tuple[str, List[BaseMessage]]:
  (procedural_context_str, short_term_msgs)

Short-term memory (short_term_msgs) is passed directly as LangChain
BaseMessage objects into agents' `messages` parameter to preserve
structure and avoid double-serialization.

- **Attributes**:
  - `model_manager` (`Any`): Instance attribute for model_manager.
  - `bot` (`Any`): Instance attribute for bot.
  - `context_manager` (`Any`): Instance attribute for context_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Initialize model manager and context manager.
  - `_build_info_agent_prompt(bot_id, message) -> str`: Build system prompt for info_agent from settings with fallback.
  - `_get_info_agent_fallback_prompt(bot_id) -> str`: Handles the `_get_info_agent_fallback_prompt` functionality. Executes the underlying business logic for this operation.
  - `_build_message_agent_prompt(bot_id, message) -> str`: Build system prompt for message_agent using ProtectedPromptManager.
  - `_build_action_tools_rules(tools) -> str`: Inject behavioral rules for message-mode action tools.
  - `_sanitize_messages_for_model(messages, model_name, image_cache) -> List[...]`: Sanitize messages for the specific model.
  - `handle_message(bot, message_edit, message, logger, announce_new_version) -> OrchestratorResponse`: Main entrypoint for handling an incoming Discord message.
