"""Auto-response channels can reply to everything, by chance, or only when the topic is relevant."""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

from cogs.channel_manager import ChannelManager, decide_auto_response, get_auto_response_settings


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
