# File: `llm/model_circuit_breaker.py`

## Overview
ModelCircuitBreaker: Tracks model failures and temporarily skips known-failing models.

## Classes

### `ErrorCategory`
Categorizes errors for different cooldown strategies.

- **Attributes**:
  - None specified.

- **Methods**:
  - None specified.

### `FailureRecord`
Record of a model failure.

- **Attributes**:
  - `model_name` (`str`): Class attribute
  - `category` (`ErrorCategory`): Class attribute
  - `failure_time` (`float`): Class attribute
  - `cooldown_until` (`float`): Class attribute
  - `error_message` (`str`): Class attribute
  - `consecutive_failures` (`int`): Class attribute

- **Methods**:
  - None specified.

### `ModelCircuitBreaker`
Thread-safe circuit breaker for LLM model calls.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> None`: Initialize the circuit breaker with empty failure tracking.
  - `categorize_error(error: Exception) -> ErrorCategory`: Classify an exception into an error category.
  - `is_available(model_name: str) -> bool`: Check if a model is currently available (not in cooldown).
  - `record_failure(model_name: str, error: Exception, category: Optional[ErrorCategory]) -> ErrorCategory`: Record a model failure and start the cooldown period.
  - `get_available_models(model_list: list[str]) -> list[str]`: Filter a model list to only include available models.
  - `reset(model_name: Optional[str]) -> None`: Reset circuit breaker state.
  - `get_status() -> Dict[Tuple[str, Dict]]`: Get current status of all tracked failures.

## Functions

### `get_model_circuit_breaker() -> ModelCircuitBreaker`
Get the global ModelCircuitBreaker singleton instance.

