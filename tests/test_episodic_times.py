"""Episodic memory gives when an event happened as Discord timestamps and where it came from as a source label.

The bot's prompt tells it to write every date and time as ``<t:UNIX:STYLE>`` and to copy a fragment's source
label when it uses the fragment. A UTC date written out in the tool result was copied into replies instead,
and the tool gave a bare ``Jump URL`` line the bot did not cite (live report).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
import yaml

from cogs.episodic_memory import EpisodicMemoryService
from llm.memory.episodic import EpisodicMemoryProvider
from llm.tools.episodic_memory import EpisodicMemoryTools

ROOT = Path(__file__).resolve().parents[1]

# 2025-12-27 00:24:24 UTC to 01:33:22 UTC, copied from a stored fragment of the live collection.
START = 1766795064
END = 1766799202
JUMP_URL = "https://discord.com/channels/1/2/3"
SOURCE_LABEL = f"[[Source <t:{START}:R>]({JUMP_URL})]"
STORED_METADATA: Dict[str, Any] = {
    "fragment_id": "1454253545854337076-1454270903960600778-1",
    "author_ids": ["646887224125685760", "474232209772118037"],
    "jump_url": JUMP_URL,
    "start_timestamp": float(START),
    "end_timestamp": float(END),
}


class _Store:
    def __init__(self, fragments: List[Any]) -> None:
        self.fragments = fragments

    async def search(self, **kwargs: Any) -> List[Any]:
        return self.fragments

    async def search_memories_by_vector(self, **kwargs: Any) -> List[Any]:
        return self.fragments


def _fragment(metadata: Dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(content="they talked about a concert", score=0.9, metadata=metadata)


def _tool(fragments: List[Any]) -> Any:
    bot = SimpleNamespace(vector_manager=SimpleNamespace(store=_Store(fragments)))
    message = SimpleNamespace(channel=SimpleNamespace(id=5), guild=None)
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]
    return tool


async def _tool_output(metadata: Dict[str, Any]) -> str:
    return await _tool([_fragment(metadata)]).ainvoke({"vector_query": "concert"})


# ------------------------------------------------------------------ the time


@pytest.mark.asyncio
async def test_the_tool_gives_the_start_as_a_discord_timestamp() -> None:
    output = await _tool_output(STORED_METADATA)

    assert f"<t:{START}:F>" in output
    assert "Unknown Time" not in output


@pytest.mark.asyncio
async def test_the_tool_gives_the_relative_time_as_a_discord_timestamp() -> None:
    output = await _tool_output(STORED_METADATA)

    assert f"Time: <t:{START}:F>" in output and f"(<t:{START}:R>)" in output


@pytest.mark.asyncio
async def test_the_tool_gives_the_end_of_a_short_conversation_as_a_clock_time() -> None:
    output = await _tool_output(STORED_METADATA)

    assert f"<t:{END}:t>" in output


@pytest.mark.asyncio
async def test_the_tool_gives_the_end_of_a_long_conversation_as_a_full_date() -> None:
    output = await _tool_output({**STORED_METADATA, "end_timestamp": float(START + 3 * 86_400)})

    assert f"<t:{START + 3 * 86_400}:F>" in output


@pytest.mark.asyncio
async def test_the_tool_does_not_write_the_time_out_as_text_the_model_would_copy() -> None:
    """Live report: the bot answered with '2025-12-27 00:24 UTC' instead of a Discord timestamp."""
    output = await _tool_output(STORED_METADATA)

    assert "UTC" not in output
    assert "2025-12-27" not in output
    assert "days ago" not in output


@pytest.mark.asyncio
async def test_a_fragment_without_any_time_says_so_instead_of_inventing_one() -> None:
    output = await _tool_output({"fragment_id": "x", "author_ids": ["1"]})

    assert "Time: unknown" in output


@pytest.mark.parametrize("value", [None, "", "soon", float("nan"), -1.0])
@pytest.mark.asyncio
async def test_an_unusable_stored_time_is_reported_as_unknown(value: Optional[Any]) -> None:
    output = await _tool_output({"fragment_id": "x", "start_timestamp": value})

    assert "Time: unknown" in output


# 253402300800 is one second past the year 9999: a number, finite and positive, that no date can hold.
BEYOND_YEAR_9999 = 253402300800


@pytest.mark.asyncio
async def test_one_out_of_range_time_does_not_discard_the_other_memories() -> None:
    """Codex review: a conversion error aborted the whole search and the bot got only an error message."""
    bad = _fragment({"fragment_id": "bad", "start_timestamp": BEYOND_YEAR_9999})

    output = await _tool([bad, _fragment(STORED_METADATA)]).ainvoke({"vector_query": "concert"})

    assert "An error occurred" not in output
    assert "Time: unknown" in output and f"<t:{START}:F>" in output


@pytest.mark.asyncio
async def test_an_out_of_range_end_time_falls_back_to_the_start() -> None:
    output = await _tool_output({**STORED_METADATA, "end_timestamp": BEYOND_YEAR_9999})

    assert f"<t:{START}:F>" in output
    assert f"<t:{END}:t>" not in output


@pytest.mark.asyncio
async def test_a_single_moment_is_not_given_as_a_range() -> None:
    output = await _tool_output({**STORED_METADATA, "end_timestamp": float(START)})

    assert f"<t:{START}:F>" in output
    assert " - <t:" not in output


# ------------------------------------------------------- who and where from


@pytest.mark.asyncio
async def test_the_tool_lists_the_participants_it_stored() -> None:
    output = await _tool_output(STORED_METADATA)

    assert "646887224125685760" in output and "474232209772118037" in output
    assert "Unknown" not in output


@pytest.mark.asyncio
async def test_the_tool_gives_a_source_label_ready_to_copy() -> None:
    """Live report: the bot left out the source; a bare 'Jump URL' line was not something it cited."""
    output = await _tool_output(STORED_METADATA)

    assert f"Source: {SOURCE_LABEL}" in output


@pytest.mark.asyncio
async def test_a_fragment_without_a_link_has_no_source_line() -> None:
    output = await _tool_output({k: v for k, v in STORED_METADATA.items() if k != "jump_url"})

    assert "Source:" not in output


@pytest.mark.asyncio
async def test_the_tool_tells_the_model_to_copy_the_times_and_the_source() -> None:
    description = _tool([]).description

    assert "<t:" in description and "copy" in description and "Source" in description


# ------------------------------------------------------------- slash command


def _slash_command_text(metadata: Dict[str, Any]) -> str:
    cog = SimpleNamespace(_translate_text=lambda lang, guild, *keys, **kwargs: f"Time: {kwargs['time']}" if keys[-1] == "result_time" else keys[-1])
    return EpisodicMemoryService._format_search_results(cog, None, "1", [_fragment(metadata)])


def test_the_slash_command_shows_the_time_of_a_stored_fragment_in_the_viewers_time() -> None:
    text = _slash_command_text(STORED_METADATA)

    assert f"Time: <t:{START}:F>" in text
    assert "UTC" not in text


def test_the_slash_command_still_leaves_out_the_time_of_a_fragment_without_one() -> None:
    text = _slash_command_text({"fragment_id": "x"})

    assert "Time:" not in text


def test_the_slash_command_survives_an_out_of_range_time() -> None:
    text = _slash_command_text({"fragment_id": "x", "start_timestamp": BEYOND_YEAR_9999})

    assert "Time:" not in text


# ------------------------------------------------- the automatic recall and the prompt


@pytest.mark.asyncio
async def test_an_injected_memory_carries_the_source_label_and_no_text_date() -> None:
    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(read_optouts=lambda guild_id: set()))}
    bot = SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=_Store([_fragment(STORED_METADATA)])))
    message = SimpleNamespace(
        content="what did we plan for the concert last week", channel=SimpleNamespace(id=7),
        guild=SimpleNamespace(id=42), author=SimpleNamespace(id=10),
    )

    text = await EpisodicMemoryProvider(bot).get(message)

    assert SOURCE_LABEL in text
    assert "UTC" not in text and "2025-12-27" not in text


def test_the_prompt_covers_every_place_a_memory_is_given_to_the_bot() -> None:
    prompt = yaml.safe_load((ROOT / "base_configs" / "prompt" / "message_agent.yaml").read_text(encoding="utf-8"))
    rules = prompt["memory_system"]["content"]

    for place in ("--- Relevant Past Memories ---", "--- Recently Recalled Memories ---", "search_episodic_memory"):
        assert place in rules, f"the source rule must name {place}"
    assert "<t:" in rules and "UTC" in rules, "times are Discord timestamps, never written-out UTC"
