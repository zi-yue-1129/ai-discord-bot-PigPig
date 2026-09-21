# File: `update.py`

## Overview
Lightweight CLI wrapper for update system

This script provides a lightweight CLI interface that delegates core functionality
to the new update architecture in addons.update.* modules.

Usage:
    python update.py -c           # Check version
    python update.py -l           # Install latest version
    python update.py -v <version> # Install specific version
    python update.py -b           # Install beta version

## Classes

### `UpdateCLI`
Lightweight CLI wrapper for update operations

- **Attributes**:
  - `config` (`Any`): Attribute holding config data.
  - `bot_owner_id` (`Any`): Attribute holding bot_owner_id data.
  - `github_config` (`Any`): Attribute holding github_config data.
  - `version_checker` (`Any`): Attribute holding version_checker data.
  - `permission_checker` (`Any`): Attribute holding permission_checker data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__() -> Any`: Initialize CLI wrapper
  - `_init_bot_owner_id() -> Any`: Initialize bot owner ID from environment
  - `check_version(with_message: bool) -> str`: Check current version status
  - `install_version(version: Optional[str], is_latest: bool, is_beta: bool) -> bool`: Install specified version
  - `parse_args() -> argparse.Namespace`: Parse command line arguments
  - `run() -> int`: Main execution method

## Functions

### `main() -> Any`
Main entry point
