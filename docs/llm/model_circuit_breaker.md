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
  - `QUOTA_EXHAUSTED` (`Any`): Attribute QUOTA_EXHAUSTED
  - `MODEL_NOT_FOUND` (`Any`): Attribute MODEL_NOT_FOUND
  - `RATE_LIMITED` (`Any`): Attribute RATE_LIMITED
  - `AUTHENTICATION` (`Any`): Attribute AUTHENTICATION
  - `TRANSIENT` (`Any`): Attribute TRANSIENT
  - `UNKNOWN` (`Any`): Attribute UNKNOWN

- **Methods**:
  - None

### `FailureRecord`
Record of a model failure.

- **Attributes**:
  - `model_name` (`str`): Attribute model_name
  - `category` (`ErrorCategory`): Attribute category
  - `failure_time` (`float`): Attribute failure_time
  - `cooldown_until` (`float`): Attribute cooldown_until
  - `error_message` (`str`): Attribute error_message
  - `consecutive_failures` (`int`): Attribute consecutive_failures

- **Methods**:
  - None

### `ModelCircuitBreaker`
Thread-safe circuit breaker for LLM model calls.  Tracks model failures and temporarily disables calls to models that are known to be failing. This prevents wasting API quota and reduces latency by avoiding doomed retry attempts.  Attributes:     _failures: Dict mapping model names to their failure records.     _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_failures` (`Dict[str, FailureRecord]`): Instance attribute _failures
  - `_lock` (`Any`): Instance attribute _lock

- **Methods**:
  - `categorize_error(self, error) -> ErrorCategory`: Classify an exception into an error category.  Args:     error: The exception to categorize.      Returns:     The ErrorCategory that best matches the exception.
  - `is_available(self, model_name) -> bool`: Check if a model is currently available (not in cooldown).  Args:     model_name: The model identifier (e.g., 'google_genai:gemini-2.5-flash').      Returns:     True if the model can be tried, False if it's in cooldown.
  - `record_failure(self, model_name, error, category) -> ErrorCategory`: Record a model failure and start the cooldown period.  Args:     model_name: The model identifier that failed.     error: The exception that occurred.     category: Optional explicit category (auto-detected if not provided).      Returns:     The ErrorCategory assigned to this failure.
  - `get_available_models(self, model_list) -> list[str]`: Filter a model list to only include available models.  Args:     model_list: List of model identifiers to filter.      Returns:     List of models that are currently available (not in cooldown).
  - `reset(self, model_name) -> None`: Reset circuit breaker state.  Args:     model_name: Specific model to reset, or None to reset all.
  - `get_status(self) -> Dict[str, Dict]`: Get current status of all tracked failures.  Returns:     Dict mapping model names to their failure status info.

## Functions

### `get_model_circuit_breaker() -> ModelCircuitBreaker`
Get the global ModelCircuitBreaker singleton instance.  Returns:     The singleton ModelCircuitBreaker instance.

