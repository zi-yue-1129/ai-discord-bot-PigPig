"""Tool groups: optional tools load only where the bot owner allows them, after the core tools.

The tool list is part of every model call's prompt prefix, so it must come in the same order on
every call (core tools first, then the groups in ``TOOL_GROUP_ORDER``): a list that changes order
between calls would make the provider re-read the whole prompt instead of using its cache.
"""

from __future__ import annotations

import types
from types import SimpleNamespace

import pytest
from langchain_core.tools.structured import StructuredTool

from llm import tools_factory
from llm.tools_factory import (
    CORE_TOOL_GROUP,
    TOOL_GROUP_ORDER,
    group_allowed,
    normalize_tool_groups,
    sort_tools,
    tool_group,
)


def _tool(name: str, group: str | None = None, mode: str = "info") -> StructuredTool:
    def run() -> str:
        return name

    metadata = {"target_agent_mode": mode}
    if group:
        metadata["tool_group"] = group
    return StructuredTool.from_function(func=run, name=name, description=name, metadata=metadata)


def _channel(channel_id: int, parent_id: int | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=channel_id, parent_id=parent_id)


# ---------------------------------------------------------------- group_allowed
def test_a_tool_without_a_group_is_a_core_tool():
    assert tool_group(_tool("a")) == CORE_TOOL_GROUP
    assert tool_group(_tool("b", "Events")) == "events"


def test_a_group_without_settings_is_used_everywhere():
    assert group_allowed("events", _channel(1), {})
    assert group_allowed("events", _channel(1), None)
    assert group_allowed("events", None, {"games": {"enabled": False}})


def test_core_tools_cannot_be_turned_off():
    settings = {CORE_TOOL_GROUP: {"enabled": False, "channels": [99]}}
    assert group_allowed(CORE_TOOL_GROUP, _channel(1), settings)


def test_a_disabled_group_is_never_used():
    assert not group_allowed("games", _channel(1), {"games": {"enabled": False}})


def test_a_group_limited_to_channels_is_only_used_there():
    settings = {"games": {"channels": [10, "11"]}}
    assert group_allowed("games", _channel(10), settings)
    assert group_allowed("games", _channel(11), settings)
    assert not group_allowed("games", _channel(12), settings)
    # Without a channel there is nothing to match the list against.
    assert not group_allowed("games", None, settings)


def test_excluded_channels_win_over_the_allowed_list():
    settings = {"games": {"channels": [10], "exclude_channels": [10]}}
    assert not group_allowed("games", _channel(10), settings)
    assert not group_allowed("events", _channel(5), {"events": {"exclude_channels": [5]}})
    assert group_allowed("events", _channel(6), {"events": {"exclude_channels": [5]}})


def test_a_thread_follows_its_parent_channel():
    assert group_allowed("games", _channel(500, parent_id=10), {"games": {"channels": [10]}})
    assert not group_allowed("games", _channel(500, parent_id=10), {"games": {"exclude_channels": [10]}})


def test_a_single_channel_id_works_like_a_list():
    assert group_allowed("games", _channel(10), {"games": {"channels": 10}})
    assert group_allowed("games", _channel(10), {"games": {"channels": " 10 "}})
    assert not group_allowed("games", _channel(11), {"games": {"channels": 10}})
    assert not group_allowed("games", _channel(10), {"games": {"exclude_channels": "10"}})


def test_an_empty_channel_list_means_no_limit():
    assert group_allowed("games", _channel(10), {"games": {"channels": []}})
    assert group_allowed("games", _channel(10), {"games": None})  # "games:" with nothing under it


@pytest.mark.parametrize("value", [False, "false", "False", " no ", "off", 0, "0"])
def test_common_ways_of_writing_false_turn_a_group_off(value):
    assert not group_allowed("games", _channel(10), {"games": {"enabled": value}})


@pytest.mark.parametrize("value", [True, "true", "yes", "on", 1, "1"])
def test_common_ways_of_writing_true_keep_a_group_on(value):
    assert group_allowed("games", _channel(10), {"games": {"enabled": value}})


@pytest.mark.parametrize(
    "rules",
    [
        "off",
        3,
        ["games"],
        {"enabled": "maybe"},
        {"enabled": 2},
        {"channels": "abc"},
        {"channels": [10, None]},
        {"channels": {"id": 10}},
        {"exclude_channels": True},
    ],
)
def test_unreadable_settings_turn_the_group_off_with_a_warning(rules, monkeypatch):
    warnings: list = []
    monkeypatch.setattr(tools_factory, "_warned", set())
    monkeypatch.setattr(tools_factory.logger, "warning", warnings.append)

    assert not group_allowed("games", _channel(10), {"games": rules})
    assert not group_allowed("games", _channel(10), {"games": rules})
    assert len(warnings) == 1 and "games" in warnings[0]  # logged once, not on every message
    # Other groups are not affected.
    assert group_allowed("music", _channel(10), {"games": rules})


def test_group_names_ignore_case_and_spaces_and_unknown_names_are_logged(monkeypatch):
    warnings: list = []
    monkeypatch.setattr(tools_factory, "_warned", set())
    monkeypatch.setattr(tools_factory.logger, "warning", warnings.append)

    settings = normalize_tool_groups({"Games ": {"enabled": False}, "game": {"enabled": False}})

    assert not group_allowed("games", _channel(10), settings)
    assert group_allowed("music", _channel(10), settings)
    assert len(warnings) == 1 and "'game'" in warnings[0]


def test_the_same_group_named_twice_turns_it_off(monkeypatch):
    warnings: list = []
    monkeypatch.setattr(tools_factory, "_warned", set())
    monkeypatch.setattr(tools_factory.logger, "warning", warnings.append)

    settings = normalize_tool_groups({"games": {"channels": [10]}, "Games": {"channels": [11]}})

    assert not group_allowed("games", _channel(10), settings)
    assert any("twice" in text for text in warnings)


@pytest.mark.parametrize("raw", [["games"], "games", 3])
def test_tool_groups_that_are_not_a_mapping_are_ignored_with_a_warning(raw, monkeypatch):
    warnings: list = []
    monkeypatch.setattr(tools_factory, "_warned", set())
    monkeypatch.setattr(tools_factory.logger, "warning", warnings.append)

    assert normalize_tool_groups(raw) == {}
    assert len(warnings) == 1
    assert normalize_tool_groups(None) == {}


def test_llm_config_warns_when_tool_groups_is_not_a_mapping(tmp_path, monkeypatch):
    from addons import settings as settings_module

    warnings: list = []
    monkeypatch.setattr(settings_module.logger, "warning", warnings.append)
    path = tmp_path / "llm.yaml"
    path.write_text("tool_groups: [games]\n", encoding="utf-8")

    config = settings_module.LLMConfig(str(path))

    assert config.tool_groups == {}
    assert any("tool_groups" in text for text in warnings)


# ---------------------------------------------------------------- order
def test_core_tools_come_first_then_the_groups_in_a_fixed_order():
    tools = [
        _tool("roll_dice", "fun"),
        _tool("zeta"),
        _tool("play_music", "music"),
        _tool("create_event", "events"),
        _tool("alpha"),
        _tool("custom_b", "zzz"),
        _tool("custom_a", "aaa"),
        _tool("get_leaderboard", "community"),
    ]
    names = [t.name for t in sort_tools(tools)]
    assert names == [
        "alpha", "zeta", "play_music", "get_leaderboard", "create_event", "roll_dice",
        # Groups not in TOOL_GROUP_ORDER go last, by group name.
        "custom_a", "custom_b",
    ]


def test_the_order_does_not_depend_on_the_order_tools_were_found():
    tools = [_tool("b"), _tool("a"), _tool("x", "games"), _tool("w", "community")]
    assert [t.name for t in sort_tools(tools)] == [t.name for t in sort_tools(list(reversed(tools)))]


def test_core_comes_first_in_the_group_order():
    assert TOOL_GROUP_ORDER[0] == CORE_TOOL_GROUP


# ---------------------------------------------------------------- get_tools
@pytest.fixture
def factory(monkeypatch):
    """``get_tools`` over a fake tools package and owner settings the test can change."""
    module = types.ModuleType("llm.tools.fake")
    module.get_tools = lambda runtime: [
        _tool("roll_dice", "fun"),
        _tool("start_server_game", "games"),
        _tool("get_server_context"),
        _tool("add_reaction", mode="message"),
        _tool("play_music", "music"),
        _tool("get_leaderboard", "community"),
    ]
    settings: dict = {}
    monkeypatch.setattr(tools_factory, "_discover_tools_package", lambda: [module])
    monkeypatch.setattr(tools_factory, "_compute_pkg_dir_mtime", lambda path: 12345.0)
    monkeypatch.setattr(tools_factory, "_cached_modules", None)
    monkeypatch.setattr(tools_factory, "_get_user_permissions", lambda user, guild: {})
    monkeypatch.setattr(tools_factory, "_tool_group_settings", lambda: settings)

    def call(channel_id: int, mode: str = "info", parent_id: int | None = None) -> list:
        runtime = SimpleNamespace(message=SimpleNamespace(channel=_channel(channel_id, parent_id)))
        return [t.name for t in tools_factory.get_tools(None, None, runtime, agent_mode=mode)]

    call.settings = settings
    return call


def test_get_tools_returns_core_tools_first_and_the_same_list_every_time(factory):
    first = factory(1)
    assert first == ["get_server_context", "play_music", "get_leaderboard", "roll_dice", "start_server_game"]
    assert factory(1) == first


def test_get_tools_leaves_out_groups_the_channel_may_not_use(factory):
    factory.settings.update({"games": {"channels": [2]}, "music": {"exclude_channels": [1]}})
    assert factory(1) == ["get_server_context", "get_leaderboard", "roll_dice"]
    assert factory(2) == ["get_server_context", "play_music", "get_leaderboard", "roll_dice", "start_server_game"]
    # A thread in channel 2 gets channel 2's tools.
    assert factory(700, parent_id=2) == factory(2)


def test_core_tools_stay_a_prefix_whatever_groups_are_loaded(factory):
    full = factory(1)
    factory.settings.update({"fun": {"enabled": False}, "community": {"enabled": False}})
    fewer = factory(1)
    assert fewer == ["get_server_context", "play_music", "start_server_game"]
    # The groups that stay keep their place relative to each other.
    assert [name for name in full if name in fewer] == fewer


def test_agent_mode_filtering_still_applies(factory):
    assert factory(1, mode="message") == ["add_reaction"]


def test_music_tools_are_in_the_music_group():
    from llm.tools.music_tools import MusicTools

    tools = MusicTools(SimpleNamespace(bot=None, message=None, logger=None)).get_tools()
    assert tools and {tool_group(t) for t in tools} == {"music"}
