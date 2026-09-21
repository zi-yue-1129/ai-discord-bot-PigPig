# File: `llm/model_circuit_breaker.py`

## Overview
ModelCircuitBreaker: Tracks model failures and temporarily skips known-failing models.

This module implements a circuit breaker pattern to prevent repeated API calls
to models that are known to fail (due to quota exhaustion, non-existent models,
rate limits, etc.). Failed models are temporarily marked as 'open' (unavailable)
and will be skipped until a cooldown period expires.

Typical usage:
    from llm.model_circuit_breaker import get_model_circuit_breaker

    cb = get_model_circuit_breaker()

    # Check before calling
    if cb.is_available(model_name):
        try:
            result = await call_model(model_name)
        except Exception as e:
            cb.record_failure(model_name, e)

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
  - `model_name` (`str`): Attribute holding model_name data.
  - `category` (`ErrorCategory`): Attribute holding category data.
  - `failure_time` (`float`): Attribute holding failure_time data.
  - `cooldown_until` (`float`): Attribute holding cooldown_until data.
  - `error_message` (`str`): Attribute holding error_message data.
  - `consecutive_failures` (`int`): Attribute holding consecutive_failures data.

- **Methods**:
  - None specified.

### `ModelCircuitBreaker`
Thread-safe circuit breaker for LLM model calls.

Tracks model failures and temporarily disables calls to models that are
known to be failing. This prevents wasting API quota and reduces latency
by avoiding doomed retry attempts.

Attributes:
    _failures: Dict mapping model names to their failure records.
    _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_failures` (`Dict[Tuple[str, FailureRecord]]`): Attribute holding _failures data.
  - `_lock` (`Any`): Attribute holding _lock data.

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

Returns:
    The singleton ModelCircuitBreaker instance.
