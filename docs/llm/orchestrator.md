# File: `llm/orchestrator.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/orchestrator.py`.

## Classes

### `DirectToolOutputMiddleware`
Class representing DirectToolOutputMiddleware.

- **Attributes**:
  - None

- **Methods**:
  - `after_tools(self, state, runtime) -> Any`: Method after_tools.

### `Orchestrator`
Orchestrator updated to accept ContextManager's new return type.  ContextManager.get_context now returns Tuple[str, List[BaseMessage]]:   (procedural_context_str, short_term_msgs)  Short-term memory (short_term_msgs) is passed directly as LangChain BaseMessage objects into agents' `messages` parameter to preserve structure and avoid double-serialization.

- **Attributes**:
  - `model_manager` (`Any`): Instance attribute model_manager
  - `bot` (`Any`): Instance attribute bot
  - `context_manager` (`Any`): Instance attribute context_manager

- **Methods**:
  - `_build_info_agent_prompt(self, bot_id, message) -> str`: Build system prompt for info_agent from settings with fallback.
  - `_get_info_agent_fallback_prompt(self, bot_id) -> str`: Method _get_info_agent_fallback_prompt.
  - `_build_message_agent_prompt(self, bot_id, message) -> str`: Build system prompt for message_agent using ProtectedPromptManager.  System-level modules (Discord format, input parsing, memory system, etc.) are protected and always loaded from base_configs. Only customizable modules (identity, personality) can be overridden by users.  Args:     bot_id: Discord bot ID     message: Discord message object      Returns:     Complete system prompt with protected system modules and customizable personality
  - `_build_action_tools_rules(tools) -> str`: Inject behavioral rules for message-mode action tools.  Tool names and descriptions are already provided via tool binding — this section only adds the cross-cutting rules that tool docstrings cannot express: how action tools interact with the <som>/<eom> response format.
  - `_sanitize_messages_for_model(self, messages, model_name, image_cache) -> List[BaseMessage]`: Sanitize messages for the specific model. - Ollama requires base64 images instead of direct HTTP URLs. - Gemini 3.x models require thought_signature for tool_calls. To prevent 400 errors, we convert past tool calls to text.
  - `handle_message(self, bot, message_edit, message, logger, announce_new_version) -> OrchestratorResponse`: Main entrypoint for handling an incoming Discord message.  This method adapts to ContextManager returning a tuple: (procedural_context_str, short_term_msgs).  short_term_msgs (List[BaseMessage]) are injected directly into the agents' messages lists (oldest -> newest), placed before the current user input to preserve conversation order.

## Functions

None

