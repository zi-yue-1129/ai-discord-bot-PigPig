"""Auto-response channels can reply to everything, by chance, or only when the topic is relevant."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from cogs.channel_manager import GENERIC_REACTIONS, ChannelManager, decide_auto_response, get_auto_response_settings


def test_a_channel_that_is_off_has_mode_off() -> None:
    assert get_auto_response_settings({}, "1")["mode"] == "off"
    assert get_auto_response_settings({"auto_response": {"1": False}}, "1")["mode"] == "off"


def test_a_channel_switched_on_before_modes_existed_replies_to_everything() -> None:
    settings = get_auto_response_settings({"auto_response": {"1": True}}, "1")

    assert settings["mode"] == "all"
    assert decide_auto_response(settings, "hi", ["PigPig"], in_conversation=False) is True


def test_chance_mode_replies_to_that_share_of_messages() -> None:
    config = {"auto_response": {"1": True}, "auto_response_settings": {"1": {"mode": "chance", "chance": 30}}}
    settings = get_auto_response_settings(config, "1")

    assert decide_auto_response(settings, "hi", [], False, roll=0.29) is True
    assert decide_auto_response(settings, "hi", [], False, roll=0.30) is False


def test_chance_is_kept_between_0_and_100() -> None:
    config = {"auto_response": {"1": True}, "auto_response_settings": {"1": {"mode": "chance", "chance": 500}}}

    assert get_auto_response_settings(config, "1")["chance"] == 100


def test_relevant_mode_replies_when_the_bot_or_a_keyword_is_named() -> None:
    config = {"auto_response": {"1": True},
              "auto_response_settings": {"1": {"mode": "relevant", "keywords": ["音樂", " "]}}}
    settings = get_auto_response_settings(config, "1")

    assert settings["keywords"] == ["音樂"]
    assert decide_auto_response(settings, "pigpig 你在嗎", ["PigPig", ""], False) is True
    assert decide_auto_response(settings, "今天的音樂好聽", ["PigPig"], False) is True
    assert decide_auto_response(settings, "晚餐吃什麼", ["PigPig"], False) is False


def test_relevant_mode_keeps_talking_with_someone_it_just_answered() -> None:
    settings = {"mode": "relevant", "chance": 0, "keywords": []}

    assert decide_auto_response(settings, "然後呢", ["PigPig"], in_conversation=True) is True


def test_the_config_is_reread_only_when_the_file_changes(tmp_path: Path) -> None:
    manager = ChannelManager(SimpleNamespace())
    manager.data_dir = str(tmp_path)
    manager.save_config("9", {**manager._get_default_config(), "mode": "whitelist"})

    first = manager.load_config("9")
    first["mode"] = "changed by a caller"
    assert manager.load_config("9")["mode"] == "whitelist"  # callers get a copy

    # Another writer (the dashboard) changes the file.
    path = manager.get_config_path("9")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"mode": "blacklist"}, f)
    stat = os.stat(path)
    os.utime(path, (stat.st_atime, stat.st_mtime + 5))

    reloaded = manager.load_config("9")
    assert reloaded["mode"] == "blacklist"
    assert reloaded["auto_response_settings"] == {}


# ------------------------------------------------- model check in "relevant"


def _relevant_manager(tmp_path: Path, monkeypatch, verdicts: list) -> tuple[ChannelManager, list]:
    import cogs.channel_manager as cm

    asked: list = []

    async def fake_judge(orchestrator, bot, message, keywords, history_messages=8):
        asked.append((message.content, list(keywords)))
        return verdicts.pop(0) if verdicts else False

    monkeypatch.setattr(cm, "judge_relevance", fake_judge)
    bot = SimpleNamespace(user=SimpleNamespace(id=900, name="PigPig"), orchestrator=object())
    manager = ChannelManager(bot)
    manager.data_dir = str(tmp_path)
    config = manager._get_default_config()
    config["auto_response"]["5"] = True
    config["auto_response_settings"]["5"] = {"mode": "relevant", "keywords": ["音樂"]}
    manager.save_config("1", config)
    return manager, asked


def _message(content: str, author: int = 7) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        channel=SimpleNamespace(id=5),
        author=SimpleNamespace(id=author),
        guild=SimpleNamespace(me=SimpleNamespace(display_name="小豬")),
    )


import pytest  # noqa: E402


@pytest.mark.asyncio
async def test_the_model_decides_when_no_rule_matches(tmp_path: Path, monkeypatch) -> None:
    manager, asked = _relevant_manager(tmp_path, monkeypatch, [True])

    assert await manager.should_auto_respond(_message("有人知道 Python 的 asyncio 怎麼用嗎"), "1") is True
    assert asked == [("有人知道 Python 的 asyncio 怎麼用嗎", ["音樂"])]


@pytest.mark.asyncio
async def test_rules_answer_without_asking_the_model(tmp_path: Path, monkeypatch) -> None:
    manager, asked = _relevant_manager(tmp_path, monkeypatch, [])

    assert await manager.should_auto_respond(_message("小豬你在嗎"), "1") is True
    assert await manager.should_auto_respond(_message("推薦一些音樂"), "1") is True
    assert asked == []


@pytest.mark.asyncio
async def test_the_model_is_asked_at_most_once_per_cooldown_per_channel(tmp_path: Path, monkeypatch) -> None:
    manager, asked = _relevant_manager(tmp_path, monkeypatch, [False, True])

    assert await manager.should_auto_respond(_message("今天天氣好熱喔"), "1") is False
    assert await manager.should_auto_respond(_message("我晚餐想吃火鍋"), "1") is False
    assert len(asked) == 1


@pytest.mark.asyncio
async def test_very_short_messages_are_not_sent_to_the_model(tmp_path: Path, monkeypatch) -> None:
    manager, asked = _relevant_manager(tmp_path, monkeypatch, [True])

    assert await manager.should_auto_respond(_message("ok"), "1") is False
    assert asked == []


def test_only_a_yes_counts_as_yes() -> None:
    from llm.relevance_judge import parse_answer

    assert parse_answer("YES") and parse_answer(" yes.") and parse_answer("**Yes**")
    assert not parse_answer("NO") and not parse_answer("") and not parse_answer("Maybe yes")


def test_tuning_comes_from_base_yaml_with_safe_defaults() -> None:
    from cogs.channel_manager import AutoResponseTuning

    assert AutoResponseTuning.from_config(None) == AutoResponseTuning()
    tuned = AutoResponseTuning.from_config({"relevance_cooldown_seconds": 60, "relevance_min_chars": "10",
                                           "relevance_history_messages": 0, "conversation_window_seconds": "x"})
    assert tuned.relevance_cooldown_seconds == 60 and tuned.relevance_min_chars == 10
    assert tuned.relevance_history_messages == 1  # the model always sees at least one earlier message
    assert tuned.conversation_window_seconds == 180


@pytest.mark.asyncio
async def test_the_owner_tuning_is_used(tmp_path: Path, monkeypatch) -> None:
    from cogs.channel_manager import AutoResponseTuning

    manager, asked = _relevant_manager(tmp_path, monkeypatch, [False, False])
    manager.tuning = AutoResponseTuning(relevance_cooldown_seconds=0, relevance_min_chars=1)

    await manager.should_auto_respond(_message("ok"), "1")
    await manager.should_auto_respond(_message("hm"), "1")
    assert len(asked) == 2


class _FakeManager:
    def __init__(self, lists: dict) -> None:
        self.lists = lists

    def has_models(self, key: str) -> bool:
        return bool(self.lists.get(key))

    def get_model_priority_list(self, key: str) -> list:
        return self.lists[key]


class _History:
    def __init__(self, messages: list) -> None:
        self.messages = messages

    def __call__(self, limit: int, before=None):
        async def gen():
            for m in self.messages[:limit]:
                yield m
        return gen()


async def _judge_with(monkeypatch, lists: dict) -> list:
    import llm.relevance_judge as rj

    used: list = []

    class _Model:
        def __init__(self, name: str) -> None:
            self.name = name

        async def ainvoke(self, prompt):
            used.append(self.name)
            return SimpleNamespace(content="YES")

    monkeypatch.setattr(rj, "create_model_instance", lambda name, **kw: _Model(name))
    monkeypatch.setattr(rj, "get_model_circuit_breaker",
                        lambda: SimpleNamespace(is_available=lambda n: True, record_failure=lambda n, e: None))
    author = SimpleNamespace(id=7, display_name="Al")
    message = SimpleNamespace(
        content="anyone know asyncio?", author=author,
        channel=SimpleNamespace(history=_History([])),
        guild=SimpleNamespace(id=1, me=SimpleNamespace(display_name="PigPig")),
    )
    bot = SimpleNamespace(user=SimpleNamespace(id=900, name="PigPig"))
    assert await rj.judge_relevance(SimpleNamespace(model_manager=_FakeManager(lists)), bot, message, []) is True
    return used


@pytest.mark.asyncio
async def test_the_relevance_check_uses_its_own_model_list(monkeypatch) -> None:
    used = await _judge_with(monkeypatch, {"relevance_model": ["g:tiny"], "message_model": ["g:chat"]})
    assert used == ["g:tiny"]


@pytest.mark.asyncio
async def test_without_its_own_list_it_falls_back_to_the_chat_models(monkeypatch) -> None:
    used = await _judge_with(monkeypatch, {"message_model": ["g:chat"]})
    assert used == ["g:chat"]


# ------------------------------------------------------------ reaction-only replies


def test_the_reaction_chance_is_off_unless_set_and_kept_between_0_and_100() -> None:
    on = {"auto_response": {"1": True}, "auto_response_settings": {"1": {"mode": "all", "reaction_chance": 250}}}

    assert get_auto_response_settings({"auto_response": {"1": True}}, "1")["reaction_chance"] == 0
    assert get_auto_response_settings(on, "1")["reaction_chance"] == 100
    assert get_auto_response_settings({}, "1")["reaction_chance"] == 0


class _ReactMessage:
    def __init__(self, refuse: tuple = ()) -> None:
        self.channel = SimpleNamespace(id=1)
        self.guild = SimpleNamespace(id=9, emojis=[_Emoji("<:pig:5>")])
        self.refuse = refuse
        self.reactions: list = []

    async def add_reaction(self, emoji: str) -> None:
        if emoji in self.refuse:
            import discord

            raise discord.HTTPException(SimpleNamespace(status=400, reason="Unknown Emoji"), "unknown emoji")
        self.reactions.append(emoji)


class _Emoji:
    available = True

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


def _reacting_manager(tmp_path: Path, chance: int, terms: list) -> ChannelManager:
    async def get_weekly_terms(guild_id: str, week: str, kind: str, limit: int) -> list:
        assert kind == "emoji"
        return terms

    storage = SimpleNamespace(get_weekly_terms=get_weekly_terms)
    bot = SimpleNamespace(get_cog=lambda name: SimpleNamespace(stats_storage=storage) if name == "StatsCog" else None)
    manager = ChannelManager(bot)
    manager.data_dir = str(tmp_path)
    config = manager._get_default_config()
    config["auto_response"]["1"] = True
    config["auto_response_settings"]["1"] = {"mode": "all", "reaction_chance": chance}
    manager.save_config("9", config)
    return manager


@pytest.mark.asyncio
async def test_some_unprompted_replies_are_a_favourite_emoji(tmp_path: Path) -> None:
    manager = _reacting_manager(tmp_path, 30, [("<:pig:5>", 40), ("<:gone:6>", 30)])
    message = _ReactMessage()

    assert await manager.react_instead(message, "9", roll=0.31) is False
    assert message.reactions == []
    assert await manager.react_instead(message, "9", roll=0.29) is True
    # The server's own emoji comes first; one from another server or a deleted one is never tried.
    assert message.reactions == ["<:pig:5>"]


@pytest.mark.asyncio
async def test_an_unusable_emoji_falls_back_to_a_generic_one(tmp_path: Path) -> None:
    manager = _reacting_manager(tmp_path, 100, [("<:pig:5>", 40)])
    message = _ReactMessage(refuse=("<:pig:5>",))

    assert await manager.react_instead(message, "9") is True
    assert len(message.reactions) == 1 and message.reactions[0] in GENERIC_REACTIONS


@pytest.mark.asyncio
async def test_a_failed_emoji_lookup_means_a_normal_reply_and_lookups_are_cached(tmp_path: Path) -> None:
    calls: list = []

    async def broken(guild_id: str, week: str, kind: str, limit: int) -> list:
        calls.append(guild_id)
        raise RuntimeError("database is locked")

    manager = _reacting_manager(tmp_path, 100, [])
    manager.bot.get_cog("StatsCog").stats_storage.get_weekly_terms = broken
    message = _ReactMessage()

    # The lookup failure gives no favourites, so a generic emoji is used instead.
    assert await manager.react_instead(message, "9") is True
    assert await manager.react_instead(message, "9") is True
    assert calls == ["9"]


@pytest.mark.asyncio
async def test_an_unexpected_error_never_stops_the_reply(tmp_path: Path) -> None:
    manager = _reacting_manager(tmp_path, 100, [])

    def explode(guild_id: str) -> dict:
        raise ValueError("bad config")

    manager.load_config = explode

    assert await manager.react_instead(_ReactMessage(), "9") is False
