# File: `llm/model_circuit_breaker.py`

## Overview
The `ModelCircuitBreaker` module implements a fault-tolerance pattern to manage LLM provider failures. It tracks model performance in real-time and temporarily "trips" (disables) models that are consistently failing, preventing the bot from wasting API quota and reducing latency caused by doomed retry attempts.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `model_circuit_breaker.py`, providing vital integrations within the PigPig bot ecosystem.
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

### `FailureRecord`
Record of a model failure.

- **Attributes**:
  - `model_name` (`str`): Property holding the model_name state.
  - `category` (`ErrorCategory`): Property holding the category state.
  - `failure_time` (`float`): Property holding the failure_time state.
  - `cooldown_until` (`float`): Property holding the cooldown_until state.
  - `error_message` (`str`): Property holding the error_message state.
  - `consecutive_failures` (`int`): Property holding the consecutive_failures state.

### `ModelCircuitBreaker`
Thread-safe circuit breaker for LLM model calls.

Tracks model failures and temporarily disables calls to models that are
known to be failing. This prevents wasting API quota and reduces latency
by avoiding doomed retry attempts.

Attributes:
    _failures: Dict mapping model names to their failure records.
    _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_lock` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> None`: Initialize the circuit breaker with empty failure tracking.
  - `categorize_error(error: Exception) -> ErrorCategory`: Classify an exception into an error category.
  - `is_available(model_name: str) -> bool`: Check if a model is currently available (not in cooldown).
  - `record_failure(model_name: str, error: Exception, category: Optional[ErrorCategory]) -> ErrorCategory`: Record a model failure and start the cooldown period.
  - `get_available_models(model_list: list[str]) -> list[str]`: Filter a model list to only include available models.
  - `reset(model_name: Optional[str]) -> None`: Reset circuit breaker state.
  - `get_status() -> Dict[Tuple]`: Get current status of all tracked failures.

## Functions

### `get_model_circuit_breaker() -> ModelCircuitBreaker`
Get the global ModelCircuitBreaker singleton instance.
