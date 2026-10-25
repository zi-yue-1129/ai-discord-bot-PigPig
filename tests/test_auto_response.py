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
