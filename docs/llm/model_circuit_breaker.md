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

### `FailureRecord`
Record of a model failure.

- **Attributes**:
  - `model_name` (`str`): Stores data related to model_name.
  - `category` (`ErrorCategory`): Stores data related to category.
  - `failure_time` (`float`): Stores data related to failure_time.
  - `cooldown_until` (`float`): Stores data related to cooldown_until.
  - `error_message` (`str`): Stores data related to error_message.
  - `consecutive_failures` (`int`): Stores data related to consecutive_failures.

### `ModelCircuitBreaker`
Thread-safe circuit breaker for LLM model calls.

Tracks model failures and temporarily disables calls to models that are
known to be failing. This prevents wasting API quota and reduces latency
by avoiding doomed retry attempts.

Attributes:
    _failures: Dict mapping model names to their failure records.
    _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_lock` (`Any`): Instance attribute managing _lock.

- **Methods**:
  - `categorize_error(error) -> ErrorCategory`: Classify an exception into an error category.  Args:     error: The exception to categorize.      Returns:     The ErrorCategory that best matches the exception.
  - `is_available(model_name) -> bool`: Check if a model is currently available (not in cooldown).  Args:     model_name: The model identifier (e.g., 'google_genai:gemini-2.5-flash').      Returns:     True if the model can be tried, False if it's in cooldown.
  - `record_failure(model_name, error, category) -> ErrorCategory`: Record a model failure and start the cooldown period.  Args:     model_name: The model identifier that failed.     error: The exception that occurred.     category: Optional explicit category (auto-detected if not provided).      Returns:     The ErrorCategory assigned to this failure.
  - `get_available_models(model_list) -> list[str]`: Filter a model list to only include available models.  Args:     model_list: List of model identifiers to filter.      Returns:     List of models that are currently available (not in cooldown).
  - `reset(model_name) -> None`: Reset circuit breaker state.  Args:     model_name: Specific model to reset, or None to reset all.
  - `get_status() -> Dict[Tuple[str, Dict]]`: Get current status of all tracked failures.  Returns:     Dict mapping model names to their failure status info.

## Functions

### `get_model_circuit_breaker() -> ModelCircuitBreaker`
Get the global ModelCircuitBreaker singleton instance.

Returns:
    The singleton ModelCircuitBreaker instance.

