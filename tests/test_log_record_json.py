"""A log record must never be lost because one of its extra values is not JSON serializable."""

from __future__ import annotations

import json

from addons.logging import LogRecord


def _record(extra: dict) -> LogRecord:
    return LogRecord(
        timestamp="2026-10-11T14:00:00Z", level="DEBUG", source="openai._base_client", server_id="Bot", message="Request options", extra=extra,
    )


def _parser(value: str) -> str:
    return value


def test_a_function_in_the_extra_fields_does_not_lose_the_record() -> None:
    line = _record({"method": "post", "post_parser": _parser}).to_json_line()

    loaded = json.loads(line)
    assert loaded["extra"]["method"] == "post"
    assert "_parser" in loaded["extra"]["post_parser"]


def test_nested_unserializable_values_are_kept_as_text() -> None:
    line = _record({"json_data": {"tools": [{"callback": _parser}], "n": 2}}).to_json_line()

    loaded = json.loads(line)
    assert loaded["extra"]["json_data"]["n"] == 2
    assert "_parser" in loaded["extra"]["json_data"]["tools"][0]["callback"]


def test_ordinary_records_are_serialized_exactly_as_before() -> None:
    line = _record({"a": 1, "名稱": "音樂"}).to_json_line()

    assert line == (
        '{"timestamp":"2026-10-11T14:00:00Z","level":"DEBUG","source":"openai._base_client","server_id":"Bot",'
        '"channel_or_file":"","user_id":"","action":"","message":"Request options","trace_id":null,'
        '"extra":{"a":1,"名稱":"音樂"}}'
    )
