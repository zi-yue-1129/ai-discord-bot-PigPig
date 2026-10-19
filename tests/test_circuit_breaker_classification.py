"""A failed fetch of a URL must not be mistaken for a missing model."""

from __future__ import annotations

from types import SimpleNamespace

from llm.model_circuit_breaker import ErrorCategory, ModelCircuitBreaker

THUMBNAIL = "https://img.youtube.com/vi/pztQtHvZkRc/maxresdefault.jpg"


def _category(message: str) -> ErrorCategory:
    return ModelCircuitBreaker().categorize_error(Exception(message))


def test_a_404_for_an_image_url_is_not_a_missing_model() -> None:
    message = f"404 Client Error: Not Found for url: {THUMBNAIL}"

    assert _category(message) == ErrorCategory.UNKNOWN


def test_a_vllm_wrapped_url_404_is_not_a_missing_model() -> None:
    message = f"Error code: 500 - {{'error': {{'message': \"404, message='Not Found', url='{THUMBNAIL}'\"}}}}"

    assert _category(message) == ErrorCategory.UNKNOWN


def test_a_missing_model_is_still_recognised() -> None:
    assert _category("404 models/gemini-9 is not found for API version v1beta") == ErrorCategory.MODEL_NOT_FOUND
    assert _category("The model `foo` does not exist") == ErrorCategory.MODEL_NOT_FOUND


def test_thumbnail_url_points_at_an_image_that_always_exists() -> None:
    from cogs.music_lib.youtube import YouTubeManager

    manager = SimpleNamespace()
    assert YouTubeManager.get_thumbnail_url(manager, "abc") == "https://img.youtube.com/vi/abc/hqdefault.jpg"
