# File: `update.py`

## Overview
The PigPig Bot features a sophisticated update system divided into two parts: a Command-Line Interface (CLI) for manual management and an integrated background service for automatic checks.

This file belongs to the Core System. Its core responsibility is to handle logic related to `update.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `config` (`Any`): Internal instance state.
  - `bot_owner_id` (`Any`): Internal instance state.
  - `github_config` (`Any`): Internal instance state.
  - `version_checker` (`Any`): Internal instance state.
  - `permission_checker` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

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
