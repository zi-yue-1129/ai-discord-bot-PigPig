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
  - `QUOTA_EXHAUSTED` (`Any`): Class attribute representing QUOTA_EXHAUSTED.
  - `MODEL_NOT_FOUND` (`Any`): Class attribute representing MODEL_NOT_FOUND.
  - `RATE_LIMITED` (`Any`): Class attribute representing RATE_LIMITED.
  - `AUTHENTICATION` (`Any`): Class attribute representing AUTHENTICATION.
  - `TRANSIENT` (`Any`): Class attribute representing TRANSIENT.
  - `UNKNOWN` (`Any`): Class attribute representing UNKNOWN.

### `FailureRecord`
Record of a model failure.

- **Attributes**:
  - `model_name` (`str`): Class attribute representing model_name.
  - `category` (`ErrorCategory`): Class attribute representing category.
  - `failure_time` (`float`): Class attribute representing failure_time.
  - `cooldown_until` (`float`): Class attribute representing cooldown_until.
  - `error_message` (`str`): Class attribute representing error_message.
  - `consecutive_failures` (`int`): Class attribute representing consecutive_failures.

### `ModelCircuitBreaker`
Thread-safe circuit breaker for LLM model calls.

Tracks model failures and temporarily disables calls to models that are
known to be failing. This prevents wasting API quota and reduces latency
by avoiding doomed retry attempts.

Attributes:
    _failures: Dict mapping model names to their failure records.
    _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_failures` (`Dict[...]`): Instance attribute for _failures.
  - `_lock` (`Any`): Instance attribute for _lock.

- **Methods**:
  - `__init__() -> None`: Initialize the circuit breaker with empty failure tracking.
  - `categorize_error(error) -> ErrorCategory`: Classify an exception into an error category.
  - `is_available(model_name) -> bool`: Check if a model is currently available (not in cooldown).
  - `record_failure(model_name, error, category) -> ErrorCategory`: Record a model failure and start the cooldown period.
  - `get_available_models(model_list) -> list[...]`: Filter a model list to only include available models.
  - `reset(model_name) -> None`: Reset circuit breaker state.
  - `get_status() -> Dict[...]`: Get current status of all tracked failures.

## Functions

### `get_model_circuit_breaker() -> ModelCircuitBreaker`
Get the global ModelCircuitBreaker singleton instance.
