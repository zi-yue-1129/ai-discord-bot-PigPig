"""Episodic memories the bot just recalled stay in a channel's context for a while, not for one message."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set

import pytest

from llm.memory.episodic import EpisodicMemoryProvider
from llm.memory.recent_recall import RecentRecall
from llm.tools.episodic_memory import EpisodicMemoryTools

GUILD = 42
CHANNEL = 7
OTHER_CHANNEL = 8
VISIBLE = 10
HIDDEN = 11
START = 1766795064.0


class _Clock:
    """A clock the tests move by hand."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _fragment(fragment_id: str, content: str, participants: Optional[List[int]] = None) -> Any:
    metadata = {
        "fragment_id": fragment_id,
        "author_ids": [str(user) for user in (participants or [VISIBLE])],
        "start_timestamp": START,
        "end_timestamp": START + 600,
        "jump_url": f"https://discord.com/channels/1/2/{fragment_id}",
    }
    return SimpleNamespace(content=content, metadata=metadata)


def _recall(clock: _Clock, **options: Any) -> RecentRecall:
    return RecentRecall(ttl=600.0, max_per_channel=3, clock=clock, **options)


# ---------------------------------------------------------------- the store


def test_a_recalled_fragment_is_still_there_before_it_expires() -> None:
    clock = _Clock()
    recall = _recall(clock)
    recall.remember("c1", [_fragment("a", "we planned the concert")])

    clock.now += 599

    assert [f.content for f in recall.recall("c1", set())] == ["we planned the concert"]


def test_a_recalled_fragment_is_gone_after_the_time_limit() -> None:
    clock = _Clock()
    recall = _recall(clock)
    recall.remember("c1", [_fragment("a", "we planned the concert")])

    clock.now += 601

    assert recall.recall("c1", set()) == []


def test_recalling_a_fragment_again_renews_it_without_a_duplicate() -> None:
    clock = _Clock()
    recall = _recall(clock)
    recall.remember("c1", [_fragment("a", "one")])
    clock.now += 500
    recall.remember("c1", [_fragment("a", "one")])
    clock.now += 500

    assert [f.content for f in recall.recall("c1", set())] == ["one"]


def test_only_the_newest_fragments_of_a_channel_are_kept_newest_first() -> None:
    recall = _recall(_Clock())
    recall.remember("c1", [_fragment(name, name) for name in ("a", "b", "c", "d")])

    assert [f.content for f in recall.recall("c1", set())] == ["d", "c", "b"]


def test_another_channel_never_sees_the_fragments() -> None:
    recall = _recall(_Clock())
    recall.remember("c1", [_fragment("a", "private to c1")])

    assert recall.recall("c2", set()) == []


def test_a_fragment_with_a_hidden_participant_is_not_returned_and_not_kept() -> None:
    recall = _recall(_Clock())
    recall.remember("c1", [_fragment("a", "with the hidden one", [HIDDEN, VISIBLE]), _fragment("b", "visible only")])

    assert [f.content for f in recall.recall("c1", {HIDDEN})] == ["visible only"]
    assert [f.content for f in recall.recall("c1", set())] == ["visible only"], "once dropped for privacy it does not come back"


def test_the_oldest_channels_are_forgotten_beyond_the_channel_limit() -> None:
    recall = RecentRecall(ttl=600.0, max_per_channel=3, max_channels=2, clock=_Clock())
    for channel in ("c1", "c2", "c3"):
        recall.remember(channel, [_fragment(channel, f"in {channel}")])

    assert recall.recall("c1", set()) == []
    assert [f.content for f in recall.recall("c3", set())] == ["in c3"]


def test_a_fragment_without_any_id_is_told_apart_by_its_content() -> None:
    recall = _recall(_Clock())
    recall.remember("c1", [SimpleNamespace(content="x", metadata={}), SimpleNamespace(content="y", metadata={}), SimpleNamespace(content="x", metadata={})])

    assert sorted(f.content for f in recall.recall("c1", set())) == ["x", "y"]


@pytest.mark.parametrize("options", [{"ttl": 0.0}, {"ttl": -1.0}, {"max_per_channel": 0}, {"max_channels": 0}])
def test_unusable_limits_are_refused(options: Dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="must be"):
        RecentRecall(**{"ttl": 600.0, "max_per_channel": 3, **options})


# ------------------------------------------------------------ the provider


def _bot(hidden: Set[int], found: List[Any], broken: bool = False) -> Any:
    state = {"found": found, "hidden": set(hidden), "broken": broken}

    def optouts(guild_id: int) -> Set[int]:
        if state["broken"]:
            raise RuntimeError("database is locked")
        return set(state["hidden"])

    class Store:
        async def search_memories_by_vector(self, **kwargs: Any) -> list:
            return list(state["found"])

        async def search(self, **kwargs: Any) -> list:
            return list(state["found"])

    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(read_optouts=optouts))}
    bot = SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=Store()), state=state)
    return bot


def _message(content: str, channel: int = CHANNEL) -> Any:
    return SimpleNamespace(content=content, channel=SimpleNamespace(id=channel), guild=SimpleNamespace(id=GUILD), author=SimpleNamespace(id=VISIBLE))


QUESTION = "what did we plan for the concert last week"
FOLLOW_UP = "when was that"


@pytest.mark.asyncio
async def test_a_short_follow_up_still_carries_what_the_last_question_found() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    await provider.get(_message(QUESTION))
    bot.state["found"] = []

    follow_up = await provider.get(_message(FOLLOW_UP))

    assert follow_up is not None and "the concert at the Fox" in follow_up


@pytest.mark.asyncio
async def test_a_follow_up_in_another_channel_gets_nothing() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    await provider.get(_message(QUESTION))
    bot.state["found"] = []

    assert await provider.get(_message(FOLLOW_UP, channel=OTHER_CHANNEL)) is None


@pytest.mark.asyncio
async def test_the_follow_up_does_not_repeat_a_fragment_it_found_again() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    await provider.get(_message(QUESTION))

    again = await provider.get(_message("remind me what the concert plan was"))

    assert again is not None and again.count("the concert at the Fox") == 1


@pytest.mark.asyncio
async def test_a_member_who_hides_after_the_recall_is_no_longer_retold() -> None:
    bot = _bot(set(), [_fragment("a", "the concert plan of the soon hidden one", [HIDDEN])])
    provider = EpisodicMemoryProvider(bot)
    await provider.get(_message(QUESTION))
    bot.state["found"] = []
    bot.state["hidden"] = {HIDDEN}

    assert await provider.get(_message(FOLLOW_UP)) is None


@pytest.mark.asyncio
async def test_nothing_is_retold_while_the_opt_out_list_cannot_be_read() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    await provider.get(_message(QUESTION))
    bot.state["found"] = []
    bot.state["broken"] = True

    assert await provider.get(_message(FOLLOW_UP)) is None


@pytest.mark.asyncio
async def test_a_recalled_fragment_tells_when_it_happened_in_words() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])

    text = await EpisodicMemoryProvider(bot).get(_message(QUESTION))

    assert text is not None and "2025-12-27" in text and "UTC" in text


@pytest.mark.asyncio
async def test_what_the_search_tool_found_is_retold_to_the_next_message() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    bot.orchestrator = SimpleNamespace(context_manager=SimpleNamespace(episodic_provider=provider))
    runtime = SimpleNamespace(bot=bot, message=_message("find the concert"), logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]
    await tool.ainvoke({"vector_query": "concert"})
    bot.state["found"] = []

    follow_up = await provider.get(_message(FOLLOW_UP))

    assert follow_up is not None and "the concert at the Fox" in follow_up


@pytest.mark.asyncio
async def test_a_search_in_another_channel_is_not_retold_here() -> None:
    bot = _bot(set(), [_fragment("a", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    bot.orchestrator = SimpleNamespace(context_manager=SimpleNamespace(episodic_provider=provider))
    runtime = SimpleNamespace(bot=bot, message=_message("find the concert", channel=OTHER_CHANNEL), logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]
    await tool.ainvoke({"vector_query": "concert"})
    bot.state["found"] = []

    assert await provider.get(_message(FOLLOW_UP)) is None


# ------------------------------------------------------- Codex review of the first version


@pytest.mark.asyncio
async def test_a_search_answered_from_the_cache_still_renews_what_it_told() -> None:
    """Repeating a question served from the cache must keep its fragment recalled for the follow-up."""
    bot = _bot(set(), [_fragment("plan", "we planned the concert at the Fox")])
    provider = EpisodicMemoryProvider(bot)
    await provider.get(_message(QUESTION))
    provider.remember(str(CHANNEL), [_fragment(f"other{n}", f"unrelated talk {n}") for n in range(5)])
    bot.state["found"] = []

    await provider.get(_message(QUESTION))  # the cached answer, the store is not asked again
    follow_up = await provider.get(_message(FOLLOW_UP))

    assert follow_up is not None and "the concert at the Fox" in follow_up


@pytest.mark.asyncio
async def test_one_oversized_recalled_fragment_does_not_hide_the_smaller_ones() -> None:
    bot = _bot(set(), [])
    provider = EpisodicMemoryProvider(bot)
    provider.remember(str(CHANNEL), [_fragment("short", "we planned the concert at the Fox")])
    provider.remember(str(CHANNEL), [_fragment("huge", "long " * 400)])  # newest, 2,000 characters

    follow_up = await provider.get(_message(FOLLOW_UP))

    assert follow_up is not None and "the concert at the Fox" in follow_up


@pytest.mark.asyncio
async def test_the_new_and_the_recalled_memories_together_stay_within_the_limit() -> None:
    bot = _bot(set(), [_fragment("new", "n" * 650)])
    provider = EpisodicMemoryProvider(bot, max_chars=1500)
    provider.remember(str(CHANNEL), [_fragment("old", "o" * 650)])

    text = await provider.get(_message(QUESTION))

    assert text is not None and "n" * 650 in text
    assert len(text) <= 1500


# -------------------------------------------- Codex review, second round: privacy at the last await, invalidation


def _bot_with_reads(reads: List[Set[int]], found: List[Any]) -> Any:
    """A bot whose successive opt-out reads answer ``reads`` in order (the last one repeats)."""
    remaining = list(reads)

    def optouts(guild_id: int) -> Set[int]:
        return set(remaining.pop(0) if len(remaining) > 1 else remaining[0])

    class Store:
        async def search_memories_by_vector(self, **kwargs: Any) -> list:
            return list(found)

    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(read_optouts=optouts))}
    return SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=Store()))


@pytest.mark.asyncio
async def test_a_member_who_hides_during_the_last_read_is_not_retold_by_the_new_search_either() -> None:
    """The searched fragment passed the check after the search; the last read (for the recalled ones) saw the opt-out."""
    bot = _bot_with_reads([set(), set(), {HIDDEN}], [_fragment("new", "the concert plan of the hider", [HIDDEN])])
    provider = EpisodicMemoryProvider(bot)
    provider.remember(str(CHANNEL), [_fragment("old", "an older chat about the Fox", [VISIBLE])])

    text = await provider.get(_message(QUESTION))

    assert text is None or "the hider" not in text


@pytest.mark.asyncio
async def test_an_invalidated_channel_forgets_what_it_recalled() -> None:
    bot = _bot(set(), [])
    provider = EpisodicMemoryProvider(bot)
    provider.remember(str(CHANNEL), [_fragment("a", "we planned the concert at the Fox")])

    await provider.invalidate(str(CHANNEL))

    assert await provider.get(_message(FOLLOW_UP)) is None


@pytest.mark.asyncio
async def test_a_request_in_flight_during_an_invalidation_gets_nothing_from_before() -> None:
    gate = asyncio.Event()

    class SlowStore:
        async def search_memories_by_vector(self, **kwargs: Any) -> list:
            await gate.wait()
            return []

    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(read_optouts=lambda guild_id: set()))}
    bot = SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=SlowStore()))
    provider = EpisodicMemoryProvider(bot)
    provider.remember(str(CHANNEL), [_fragment("a", "we planned the concert at the Fox")])

    request = asyncio.create_task(provider.get(_message(QUESTION)))
    await asyncio.sleep(0.05)  # the request has taken its snapshot and waits for the search
    await provider.invalidate(str(CHANNEL))
    gate.set()

    assert await request is None


# ------------------------------------------------ Codex review, third round: a tool search in flight, expiry mid-request


def _gated_bot(gate: asyncio.Event, found: List[Any]) -> Any:
    """A bot whose searches (tool and automatic) wait for ``gate`` before answering ``found``."""

    class SlowStore:
        async def search_memories_by_vector(self, **kwargs: Any) -> list:
            await gate.wait()
            return list(found)

        async def search(self, **kwargs: Any) -> list:
            await gate.wait()
            return list(found)

    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(read_optouts=lambda guild_id: set()))}
    return SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=SlowStore()))


@pytest.mark.asyncio
async def test_a_tool_search_finishing_after_an_invalidation_does_not_recall_the_old_fragment() -> None:
    gate = asyncio.Event()
    bot = _gated_bot(gate, [_fragment("old", "the outdated concert plan")])
    provider = EpisodicMemoryProvider(bot)
    bot.orchestrator = SimpleNamespace(context_manager=SimpleNamespace(episodic_provider=provider))
    runtime = SimpleNamespace(bot=bot, message=_message("find the concert"), logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]

    search = asyncio.create_task(tool.ainvoke({"vector_query": "concert"}))
    await asyncio.sleep(0.05)  # the tool has asked the store
    await provider.invalidate(str(CHANNEL))  # the channel's memory was replaced meanwhile
    gate.set()
    await search

    assert await provider.get(_message(FOLLOW_UP)) is None


@pytest.mark.asyncio
async def test_a_fragment_that_expires_while_the_request_runs_is_not_told() -> None:
    clock = _Clock()
    gate = asyncio.Event()
    bot = _gated_bot(gate, [])
    provider = EpisodicMemoryProvider(bot)
    provider.recent = RecentRecall(ttl=10.0, max_per_channel=5, clock=clock)
    provider.remember(str(CHANNEL), [_fragment("a", "we planned the concert at the Fox")])

    clock.now += 9  # still alive when the request starts
    request = asyncio.create_task(provider.get(_message(QUESTION)))
    await asyncio.sleep(0.05)
    clock.now += 2  # expired while the search ran
    gate.set()

    assert await request is None
