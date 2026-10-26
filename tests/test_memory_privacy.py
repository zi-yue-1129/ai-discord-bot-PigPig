"""What a hidden member (/leaderboard optout) said is not retold from the bot's long-term memory."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List, Optional, Set

import pytest

from llm.memory.privacy import fragment_user_ids, hidden_in_guild, without_hidden_participants
from llm.memory.episodic import EpisodicMemoryProvider
from llm.tools.episodic_memory import EpisodicMemoryTools

GUILD = 42
HIDDEN = 11
VISIBLE = 10


def _fragment(content: str, **metadata: Any) -> Any:
    return SimpleNamespace(content=content, metadata=metadata)


def _bot(hidden: Set[int], broken: bool = False, fragments: Optional[List[Any]] = None, cogs: Optional[dict] = None) -> Any:
    def optouts(guild_id: int) -> Set[int]:
        if broken:
            raise RuntimeError("database is locked")
        return set(hidden)

    class Store:
        async def search_memories_by_vector(self, **kwargs: Any) -> list:
            return list(fragments or [])

        async def search(self, **kwargs: Any) -> list:
            return list(fragments or [])

    known = {"LeaderboardCog": SimpleNamespace(store=SimpleNamespace(optouts=optouts)), **(cogs or {})}
    return SimpleNamespace(get_cog=known.get, vector_manager=SimpleNamespace(store=Store()))


def test_the_participants_of_a_fragment_are_read_from_every_metadata_shape() -> None:
    assert fragment_user_ids({"user_ids": [10, "11", "x"]}) == {10, 11}
    assert fragment_user_ids({"author_id": "12"}) == {12}
    assert fragment_user_ids({"author": "someone"}) == set()
    assert fragment_user_ids(None) == set()


def test_fragments_with_a_hidden_participant_are_dropped() -> None:
    fragments = [_fragment("a", user_ids=[VISIBLE]), _fragment("b", user_ids=[VISIBLE, HIDDEN]), _fragment("c"), _fragment("d", author_id=HIDDEN)]

    kept = without_hidden_participants(fragments, {HIDDEN})

    assert [fragment.content for fragment in kept] == ["a", "c"]


def test_no_fragment_is_kept_when_the_opt_out_list_cannot_be_read() -> None:
    assert without_hidden_participants([_fragment("a", user_ids=[VISIBLE]), _fragment("c")], None) == []


def test_the_hidden_members_are_read_through_the_leaderboard_cog() -> None:
    assert hidden_in_guild(_bot({HIDDEN}), GUILD) == {HIDDEN}
    assert hidden_in_guild(_bot(set(), broken=True), GUILD) is None


def _message(bot: Any) -> Any:
    guild = SimpleNamespace(id=GUILD)
    return SimpleNamespace(
        content="what did we plan for the trip last week", channel=SimpleNamespace(id=7), guild=guild,
        author=SimpleNamespace(id=VISIBLE),
    )


@pytest.mark.asyncio
async def test_a_hidden_members_conversation_is_not_injected_into_the_context() -> None:
    bot = _bot({HIDDEN}, fragments=[_fragment("trip with the hidden one", user_ids=[HIDDEN]), _fragment("trip by the visible one", user_ids=[VISIBLE])])

    injected = await EpisodicMemoryProvider(bot).get(_message(bot))

    assert "visible one" in injected and "hidden one" not in injected


@pytest.mark.asyncio
async def test_nothing_is_injected_while_the_opt_out_list_cannot_be_read() -> None:
    bot = _bot(set(), broken=True, fragments=[_fragment("trip by the visible one", user_ids=[VISIBLE])])

    assert await EpisodicMemoryProvider(bot).get(_message(bot)) is None


@pytest.mark.asyncio
async def test_the_search_tool_leaves_out_a_hidden_members_conversation() -> None:
    bot = _bot({HIDDEN}, fragments=[_fragment("trip with the hidden one", user_ids=[HIDDEN]), _fragment("trip by the visible one", user_ids=[VISIBLE])])
    runtime = SimpleNamespace(bot=bot, message=_message(bot), logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]

    reply = await tool.ainvoke({"vector_query": "trip"})

    assert "visible one" in reply and "hidden one" not in reply


@pytest.mark.asyncio
async def test_the_search_tool_finds_nothing_while_the_opt_out_list_cannot_be_read() -> None:
    bot = _bot(set(), broken=True, fragments=[_fragment("trip by the visible one", user_ids=[VISIBLE])])
    runtime = SimpleNamespace(bot=bot, message=_message(bot), logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]

    assert "visible one" not in await tool.ainvoke({"vector_query": "trip"})


# ----------------------------------------------------------------- personal memory of a hidden member


def _read_tool(hidden: Set[int], asker_id: int, broken: bool = False) -> Any:
    """The ``read_user_memory`` tool, asked by ``asker_id``; returns it with the list of memories it read."""
    from llm.tools.user_data import UserMemoryTools

    reads: List[str] = []

    class Users:
        async def get_user_info(self, user_id: str) -> Any:
            return SimpleNamespace(procedural_memory="likes tea", user_background="", display_names=[])

    async def read(user_id: str, context: Any) -> str:
        reads.append(user_id)
        return f"memory of {user_id}"

    cog = SimpleNamespace(user_manager=Users(), _read_user_data=read)
    bot = _bot(hidden, broken=broken, cogs={"UserDataCog": cog})
    message = SimpleNamespace(author=SimpleNamespace(id=asker_id), guild=SimpleNamespace(id=GUILD), channel=SimpleNamespace(id=7))
    quiet = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
    runtime = SimpleNamespace(bot=bot, message=message, logger=quiet)
    (tool,) = [t for t in UserMemoryTools(runtime).get_tools() if t.name == "read_user_memory"]
    return tool, reads


@pytest.mark.asyncio
async def test_a_hidden_members_personal_memory_is_not_read_out_to_others() -> None:
    tool, reads = _read_tool({HIDDEN}, asker_id=VISIBLE)

    reply = await tool.ainvoke({"user_id": HIDDEN})

    assert reads == [] and "hidden" in reply and "likes tea" not in reply


@pytest.mark.asyncio
async def test_a_hidden_member_can_still_read_their_own_memory() -> None:
    tool, reads = _read_tool({HIDDEN}, asker_id=HIDDEN)

    assert await tool.ainvoke({"user_id": HIDDEN}) == f"memory of {HIDDEN}"
    assert reads == [str(HIDDEN)]


@pytest.mark.asyncio
async def test_anyone_elses_memory_is_not_read_out_while_the_opt_out_list_cannot_be_read() -> None:
    tool, reads = _read_tool(set(), asker_id=VISIBLE, broken=True)

    assert reads == [] and "cannot be shown" in await tool.ainvoke({"user_id": 12})


@pytest.mark.asyncio
async def test_a_visible_members_memory_is_read_as_before() -> None:
    tool, reads = _read_tool({HIDDEN}, asker_id=VISIBLE)

    assert await tool.ainvoke({"user_id": 12}) == "memory of 12"
    assert reads == ["12"]
