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
  - `config` (`Any`): Instance attribute managing config.
  - `bot_owner_id` (`Any`): Instance attribute managing bot_owner_id.
  - `github_config` (`Any`): Instance attribute managing github_config.
  - `version_checker` (`Any`): Instance attribute managing version_checker.
  - `permission_checker` (`Any`): Instance attribute managing permission_checker.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `check_version(with_message) -> str`: Check current version status  Args:     with_message: Whether to print message      Returns:     Latest version string
  - `install_version(version, is_latest, is_beta) -> bool`: Install specified version  Args:     version: Version to install     is_latest: Whether to install latest version     is_beta: Whether to install beta version      Returns:     Installation success status
  - `parse_args() -> argparse.Namespace`: Parse command line arguments
  - `run() -> int`: Main execution method

## Functions

### `main() -> Any`
Main entry point

