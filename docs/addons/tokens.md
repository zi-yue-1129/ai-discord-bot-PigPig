# File: `addons/tokens.py`

## Overview
This file is part of the `addons` subsystem. It is responsible for `tokens` related functionality within the PigPig system, contributing to utility functions, configurations, and core extensions.

## Classes

### `TOKENS`
Represents the `TOKENS` class in the system.

- **Attributes**:
  - `token` (`Any`): Instance attribute for token.
  - `client_id` (`Any`): Instance attribute for client_id.
  - `client_secret_id` (`Any`): Instance attribute for client_secret_id.
  - `secret_key` (`Any`): Instance attribute for secret_key.
  - `bug_report_channel_id` (`Any`): Instance attribute for bug_report_channel_id.
  - `anthropic_api_key` (`Any`): Instance attribute for anthropic_api_key.
  - `openai_api_key` (`Any`): Instance attribute for openai_api_key.
  - `google_api_key` (`Any`): Instance attribute for google_api_key.
  - `tenor_api_key` (`Any`): Instance attribute for tenor_api_key.
  - `vllm_api_key` (`Any`): Instance attribute for vllm_api_key.
  - `vector_store_api_key` (`Any`): Instance attribute for vector_store_api_key.

- **Methods**:
  - `__init__() -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `getenv` and `_validate_environment_variables`.
  - `_validate_environment_variables() -> None`: Verify all required environment variables exist and are valid; terminate if validation fails.
