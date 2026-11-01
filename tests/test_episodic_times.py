"""Episodic memory shows when an event happened and who took part, from the fields Qdrant really stores."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from cogs.episodic_memory import EpisodicMemoryService
from llm.tools.episodic_memory import EpisodicMemoryTools

# 2025-12-27 00:24:24 UTC to 01:33:22 UTC, copied from a stored fragment of the live collection.
START = 1766795064.0
END = 1766799202.0
STORED_METADATA: Dict[str, Any] = {
    "fragment_id": "1454253545854337076-1454270903960600778-1",
    "author_ids": ["646887224125685760", "474232209772118037"],
    "jump_url": "https://discord.com/channels/1/2/3",
    "start_timestamp": START,
    "end_timestamp": END,
}


class _Store:
    def __init__(self, fragments: List[Any]) -> None:
        self.fragments = fragments

    async def search(self, **kwargs: Any) -> List[Any]:
        return self.fragments


def _fragment(metadata: Dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(content="they talked about a concert", score=0.9, metadata=metadata)


async def _tool_output(metadata: Dict[str, Any]) -> str:
    bot = SimpleNamespace(vector_manager=SimpleNamespace(store=_Store([_fragment(metadata)])))
    message = SimpleNamespace(channel=SimpleNamespace(id=5), guild=None)
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]
    return await tool.ainvoke({"vector_query": "concert"})


@pytest.mark.asyncio
async def test_the_tool_tells_the_date_the_event_started() -> None:
    output = await _tool_output(STORED_METADATA)

    assert "2025-12-27" in output
    assert "Unknown Time" not in output


@pytest.mark.asyncio
async def test_the_tool_tells_the_start_and_the_end_in_utc() -> None:
    output = await _tool_output(STORED_METADATA)

    assert "00:24" in output and "01:33" in output
    assert "UTC" in output


@pytest.mark.asyncio
async def test_the_tool_tells_how_long_ago_it_was() -> None:
    output = await _tool_output(STORED_METADATA)

    assert " days ago" in output


@pytest.mark.asyncio
async def test_a_fragment_without_any_time_says_so_instead_of_inventing_one() -> None:
    output = await _tool_output({"fragment_id": "x", "author_ids": ["1"]})

    assert "Time: unknown" in output


@pytest.mark.asyncio
async def test_the_tool_lists_the_participants_it_stored() -> None:
    output = await _tool_output(STORED_METADATA)

    assert "646887224125685760" in output and "474232209772118037" in output
    assert "Unknown" not in output


def _slash_command_text(metadata: Dict[str, Any]) -> str:
    cog = SimpleNamespace(_translate_text=lambda lang, guild, *keys, **kwargs: f"Time: {kwargs['time']}" if keys[-1] == "result_time" else keys[-1])
    return EpisodicMemoryService._format_search_results(cog, None, "1", [_fragment(metadata)])


def test_the_slash_command_shows_the_time_of_a_stored_fragment() -> None:
    text = _slash_command_text(STORED_METADATA)

    assert "Time: 2025-12-27" in text


def test_the_slash_command_still_leaves_out_the_time_of_a_fragment_without_one() -> None:
    text = _slash_command_text({"fragment_id": "x"})

    assert "Time:" not in text


@pytest.mark.parametrize("value", [None, "", "soon", float("nan"), -1.0])
@pytest.mark.asyncio
async def test_an_unusable_stored_time_is_reported_as_unknown(value: Optional[Any]) -> None:
    output = await _tool_output({"fragment_id": "x", "start_timestamp": value})

    assert "Time: unknown" in output


# 253402300800 is one second past the year 9999: a number, finite and positive, that no date can hold.
BEYOND_YEAR_9999 = 253402300800


@pytest.mark.asyncio
async def test_one_out_of_range_time_does_not_discard_the_other_memories() -> None:
    """Codex review: the conversion error aborted the whole search and the bot got only an error message."""
    bad = _fragment({"fragment_id": "bad", "start_timestamp": BEYOND_YEAR_9999})
    good = _fragment(STORED_METADATA)
    bot = SimpleNamespace(vector_manager=SimpleNamespace(store=_Store([bad, good])))
    runtime = SimpleNamespace(bot=bot, message=SimpleNamespace(channel=SimpleNamespace(id=5), guild=None), logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]

    output = await tool.ainvoke({"vector_query": "concert"})

    assert "An error occurred" not in output
    assert "Time: unknown" in output and "2025-12-27" in output


@pytest.mark.asyncio
async def test_an_out_of_range_end_time_falls_back_to_the_start() -> None:
    output = await _tool_output({**STORED_METADATA, "end_timestamp": BEYOND_YEAR_9999})

    assert "2025-12-27 00:24 UTC" in output


def test_the_slash_command_survives_an_out_of_range_time() -> None:
    text = _slash_command_text({"fragment_id": "x", "start_timestamp": BEYOND_YEAR_9999})

    assert "Time:" not in text
