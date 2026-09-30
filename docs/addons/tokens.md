# File: `addons/tokens.py`

## Overview
This file is part of utility modules and configurations and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `addons/tokens.py`.

## Classes

### `TOKENS`
Class representing TOKENS.

- **Attributes**:
  - `token` (`Any`): Instance attribute token
  - `client_id` (`Any`): Instance attribute client_id
  - `client_secret_id` (`Any`): Instance attribute client_secret_id
  - `secret_key` (`Any`): Instance attribute secret_key
  - `bug_report_channel_id` (`Any`): Instance attribute bug_report_channel_id
  - `anthropic_api_key` (`Any`): Instance attribute anthropic_api_key
  - `openai_api_key` (`Any`): Instance attribute openai_api_key
  - `google_api_key` (`Any`): Instance attribute google_api_key
  - `tenor_api_key` (`Any`): Instance attribute tenor_api_key
  - `vllm_api_key` (`Any`): Instance attribute vllm_api_key
  - `vector_store_api_key` (`Any`): Instance attribute vector_store_api_key
  - `bot_owner_id` (`Any`): Instance attribute bot_owner_id

- **Methods**:
  - `_validate_environment_variables(self) -> None`: Verify all required environment variables exist and are valid; terminate if validation fails.

## Functions

None

