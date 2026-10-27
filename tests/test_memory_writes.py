"""Knowledge stays within a size budget; user memory is never swapped for the asker's."""

from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from cogs.memory.db.knowledge_storage import MAX_KNOWLEDGE_CHARS
from cogs.userdata import UserDataCog
from llm.tools.user_data import UserMemoryTools

# The module the cog really runs in: ``from cogs import userdata`` can return an older copy
# left on the package by a test file that ran earlier (the root conftest re-imports cogs modules).
userdata = sys.modules[UserDataCog.__module__]

TARGET = "111"
ASKER = "222"


class _Logger:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def info(self, text: str, *args: Any, **kwargs: Any) -> None:
        self.lines.append(text)

    warning = error = debug = info


class _FakeModel:
    def __init__(self, reply: Any) -> None:
        self.reply = reply
        self.messages: List[Dict[str, str]] = []

    def with_structured_output(self, schema: Any) -> "_FakeModel":
        assert schema is userdata.UserDataResponse
        return self

    async def ainvoke(self, messages: List[Dict[str, str]]) -> Any:
        self.messages = messages
        return self.reply


@pytest.fixture
def fake_model(monkeypatch: pytest.MonkeyPatch) -> _FakeModel:
    model = _FakeModel(SimpleNamespace(content="### General Info\n- merged"))
    monkeypatch.setattr(userdata, "ModelManager", lambda: SimpleNamespace(get_model=lambda name, guild_id: ("m", None)))
    monkeypatch.setattr(userdata, "create_model_instance", lambda model_id, guild_id, max_retries: model)
    return model


# ------------------------------------------------------- #12 knowledge size


@pytest.mark.asyncio
async def test_the_merge_prompt_states_the_size_budget(fake_model: _FakeModel) -> None:
    cog = SimpleNamespace(logger=_Logger())

    await UserDataCog._invoke_knowledge_merge_agent(cog, "old", "new fact", "guild", "general", guild_id="1")

    assert str(MAX_KNOWLEDGE_CHARS) in fake_model.messages[1]["content"]


class _KnowledgeStore:
    def __init__(self) -> None:
        self.saved: List[str] = []

    async def get_knowledge(self, target_type: str, target_id: str) -> Optional[str]:
        return "old knowledge"

    async def update_knowledge(self, target_type: str, target_id: str, content: str) -> bool:
        self.saved.append(content)
        return True


def _knowledge_cog(merges: List[str]) -> SimpleNamespace:
    pending = list(merges)
    requests: List[str] = []

    async def merge(existing: Optional[str], new: str, target_type: str, category: str, *, guild_id: str) -> str:
        requests.append(new)
        return pending.pop(0)

    return SimpleNamespace(
        _knowledge_lock=asyncio.Lock(),
        _get_guild_id_from_context=lambda context: "1",
        _invoke_knowledge_merge_agent=merge,
        knowledge_storage=_KnowledgeStore(),
        logger=_Logger(),
        bot=SimpleNamespace(orchestrator=None),
        requests=requests,
    )


@pytest.mark.asyncio
async def test_an_oversized_merge_is_condensed_before_saving() -> None:
    cog = _knowledge_cog(["x" * (MAX_KNOWLEDGE_CHARS + 1), "condensed"])

    await UserDataCog._save_knowledge_data(cog, "guild", "1", "new fact", "general", context=None)

    assert cog.knowledge_storage.saved == ["condensed"]
    assert len(cog.requests) == 2


@pytest.mark.asyncio
async def test_knowledge_that_cannot_be_condensed_is_not_saved() -> None:
    too_long = "x" * (MAX_KNOWLEDGE_CHARS + 1)
    cog = _knowledge_cog([too_long, too_long])

    result = await UserDataCog._save_knowledge_data(cog, "guild", "1", "new fact", "general", context=None)

    assert cog.knowledge_storage.saved == []
    assert str(MAX_KNOWLEDGE_CHARS) in result


class _Followup:
    def __init__(self, sent: List[str]) -> None:
        self.sent = sent

    async def send(self, content: str, ephemeral: bool = False) -> None:
        assert ephemeral
        self.sent.append(content)


class _Interaction:
    def __init__(self) -> None:
        self.sent: List[str] = []
        self.guild_id = 1
        self.channel_id = 2
        self.response = SimpleNamespace(defer=self._defer)
        self.followup = _Followup(self.sent)

    async def _defer(self, thinking: bool, ephemeral: bool) -> None:
        assert ephemeral

    async def edit_original_response(self, content: str) -> None:
        self.sent.append(content)


@pytest.mark.asyncio
async def test_showing_long_knowledge_is_split_into_discord_sized_messages() -> None:
    lines = "\n".join(f"- fact number {index} " + "y" * 40 for index in range(60))
    store = _KnowledgeStore()

    async def stored(target_type: str, target_id: str) -> str:
        return lines

    store.get_knowledge = stored
    cog = SimpleNamespace(
        lang_manager=object(),
        knowledge_storage=store,
        logger=_Logger(),
        _translate=lambda guild_id, *path, fallback_key, **kwargs: kwargs.get("content", fallback_key),
    )
    interaction = _Interaction()

    await UserDataCog.knowledge_show.callback(cog, interaction, SimpleNamespace(value="guild"))

    assert len(interaction.sent) > 1
    assert all(len(message) <= 2000 for message in interaction.sent)
    assert "\n".join(interaction.sent) == lines


# ------------------------------------------------------ #13 user memory


@pytest.mark.asyncio
async def test_user_memory_is_merged_without_translating(
    fake_model: _FakeModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(userdata.prompt_config, "get_system_prompt", lambda name: None)
    fake_model.reply = userdata.UserDataResponse(procedural_memory="likes ramen")

    await UserDataCog._invoke_ai_merge_agent(SimpleNamespace(), None, "喜歡拉麵", TARGET, guild_id="1")

    system, user = (message["content"] for message in fake_model.messages)
    assert "Traditional Chinese" not in system
    assert "translate" in user


class _Users:
    def __init__(self) -> None:
        self.asked: List[str] = []
        self.created: List[str] = []

    async def update_user_activity(self, user_id: str, name: str, nickname: Optional[str]) -> None:
        self.created.append(user_id)

    async def get_user_info(self, user_id: str) -> Optional[Any]:
        self.asked.append(user_id)
        if user_id == ASKER:
            return SimpleNamespace(procedural_memory="asker secret", user_background="", display_names=[])
        return None


@pytest.mark.asyncio
async def test_reading_an_unknown_user_does_not_return_the_askers_memory() -> None:
    users = _Users()
    cog = SimpleNamespace(
        user_manager=users,
        logger=_Logger(),
        _get_guild_id_from_context=lambda context: "1",
        _extract_user_id_from_context=lambda context: ASKER,
        _translate=lambda guild_id, *path, fallback_key, **kwargs: fallback_key,
    )
    message = SimpleNamespace(author=SimpleNamespace(id=int(ASKER)))

    result = await UserDataCog._read_user_data(cog, TARGET, message)

    assert result == "data_not_found"
    assert users.asked == [TARGET]


@pytest.mark.asyncio
async def test_the_read_tool_reports_an_unknown_user_instead_of_the_asker() -> None:
    users = _Users()
    reads: List[str] = []

    async def read(user_id: str, context: Any) -> str:
        reads.append(user_id)
        return "data"

    cog = SimpleNamespace(user_manager=users, _read_user_data=read)
    # Someone else's memory is only read once the opt-out list can be read (it is empty here): without a
    # readable list the tool refuses, which is covered in test_memory_privacy.py.
    leaderboard = SimpleNamespace(store=SimpleNamespace(read_optouts=lambda guild_id: set()))
    cogs = {"LeaderboardCog": leaderboard}
    bot = SimpleNamespace(get_cog=lambda name: cogs.get(name, cog), get_user=lambda user_id: SimpleNamespace(id=user_id, name="n"))
    message = SimpleNamespace(author=SimpleNamespace(id=int(ASKER)), guild=SimpleNamespace(id=1))
    runtime = SimpleNamespace(bot=bot, message=message, logger=_Logger())
    (tool,) = [t for t in UserMemoryTools(runtime).get_tools() if t.name == "read_user_memory"]

    result = await tool.ainvoke({"user_id": int(TARGET)})

    assert result == "data_not_found"
    assert reads == []
    assert users.created == []


# ------------------------------------- memories about others need their OK


class _Member:
    def __init__(self, user_id: int) -> None:
        self.id = user_id
        self.name = f"member{user_id}"
        self.display_name = f"Member {user_id}"


def _save_tool(saves: List[tuple], members: tuple = (int(TARGET),), limiter: Any = None) -> Any:
    async def save(user_id: str, name: str, data: str, context: Any, nickname: Optional[str] = None) -> str:
        saves.append((user_id, name, data, nickname))
        return "saved"

    cog = SimpleNamespace(_save_user_data=save)
    bot = SimpleNamespace(get_cog=lambda name: cog if name == "UserDataCog" else None, get_user=lambda user_id: None)
    if limiter is not None:
        bot.rate_limiter = limiter
    author = SimpleNamespace(id=int(ASKER), name="asker", display_name="Asker")
    guild = SimpleNamespace(id=1, get_member=lambda user_id: _Member(user_id) if user_id in members else None)
    message = SimpleNamespace(author=author, guild=guild, channel=SimpleNamespace(id=5))
    runtime = SimpleNamespace(bot=bot, message=message, logger=_Logger())
    (tool,) = [t for t in UserMemoryTools(runtime).get_tools() if t.name == "save_user_memory"]
    return tool


@pytest.fixture
def asks(monkeypatch: pytest.MonkeyPatch) -> List[tuple]:
    """Records the questions posted instead of sending them."""
    posted: List[tuple] = []

    async def fake_ask(channel: Any, content: Any, view: Any, allowed_mentions: Any = None) -> Any:
        posted.append((content, view, allowed_mentions))
        return view

    monkeypatch.setattr(sys.modules[UserMemoryTools.__module__], "ask", fake_ask)
    return posted


@pytest.mark.asyncio
async def test_a_memory_about_another_member_waits_for_them(asks: List[tuple]) -> None:
    saves: List[tuple] = []

    result = await _save_tool(saves).ainvoke({"user_id": int(TARGET), "memory_to_save": "likes jazz"})

    assert "accept" in result.lower()
    assert saves == []
    content, view, allowed = asks[0]
    assert view.owner_id == int(TARGET)
    assert "likes jazz" in content
    assert [user.id for user in allowed.users] == [int(TARGET)] and allowed.everyone is False


@pytest.mark.asyncio
async def test_the_memory_is_saved_for_them_when_they_accept(asks: List[tuple]) -> None:
    saves: List[tuple] = []
    await _save_tool(saves).ainvoke({"user_id": int(TARGET), "memory_to_save": "likes jazz"})

    await asks[0][1].on_confirm()

    assert saves == [(TARGET, f"member{TARGET}", "likes jazz", f"Member {TARGET}")]


@pytest.mark.asyncio
async def test_a_memory_for_someone_outside_the_server_is_refused(asks: List[tuple]) -> None:
    saves: List[tuple] = []

    result = await _save_tool(saves, members=()).ainvoke({"user_id": int(TARGET), "memory_to_save": "x"})

    assert result.startswith("Refused") and asks == [] and saves == []


@pytest.mark.asyncio
async def test_asking_others_too_often_is_limited(asks: List[tuple]) -> None:
    from addons.rate_limiter import LimitRule, RateLimiter

    limiter = RateLimiter({"ask_others": LimitRule(1, 3600)})
    tool = _save_tool([], limiter=limiter)
    await tool.ainvoke({"user_id": int(TARGET), "memory_to_save": "one"})

    result = await tool.ainvoke({"user_id": int(TARGET), "memory_to_save": "two"})

    assert len(asks) == 1 and "too often" in result.lower()


@pytest.mark.asyncio
async def test_a_memory_about_the_asker_is_saved_under_their_own_name(asks: List[tuple]) -> None:
    saves: List[tuple] = []

    result = await _save_tool(saves).ainvoke({"user_id": int(ASKER), "memory_to_save": "likes tea"})

    assert result == "saved" and asks == []
    assert saves == [(ASKER, "asker", "likes tea", "Asker")]
