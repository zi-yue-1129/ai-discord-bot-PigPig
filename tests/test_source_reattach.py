"""After the merge model rewrote the memory, the code puts each fact's source tag back."""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any, List

import pytest

from cogs.userdata import UserDataCog
from llm.memory.source_label import reattach_source_tags

A = "[source: server id=1]"
B = "[source: server id=2]"
DM = "[source: direct message]"


def test_tags_the_model_kept_stay() -> None:
    merged = f"likes jazz {A}\nlikes tea {B}"

    assert reattach_source_tags(merged, [f"likes jazz {A}"], f"likes tea {B}") == merged


def test_every_fact_gets_its_own_tag_back_when_the_model_dropped_them_all() -> None:
    result = reattach_source_tags("likes jazz\nlikes tea", [f"likes jazz {A}"], f"likes tea {B}")

    assert result == f"likes jazz {A}\nlikes tea {B}"


def test_a_line_that_joins_two_facts_carries_both_tags() -> None:
    result = reattach_source_tags("likes jazz and likes tea", [f"likes jazz {A}"], f"likes tea {B}")

    assert A in result and B in result


def test_a_tag_the_model_invented_is_dropped() -> None:
    result = reattach_source_tags(f"likes jazz {A} [source: server id=999]", [f"likes jazz {A}"], f"likes tea {B}")

    assert result == f"likes jazz {A}"


def test_an_old_fact_without_a_tag_stays_without_one() -> None:
    result = reattach_source_tags("plays go\nlikes tea", ["plays go"], f"likes tea {B}")

    assert result == f"plays go\nlikes tea {B}"


def test_a_fact_the_model_rewrote_still_finds_its_source() -> None:
    result = reattach_source_tags("喜歡吃拉麵", [f"喜歡拉麵 {A}"], f"喜歡茶 {B}")

    assert result == f"喜歡吃拉麵 {A}"


def test_a_line_that_matches_nothing_is_new_in_this_save() -> None:
    result = reattach_source_tags("lives in Taipei", [f"likes jazz {A}"], f"likes tea {B}")

    assert result == f"lives in Taipei {B}"


def test_nothing_is_invented_when_the_save_has_no_tag() -> None:
    assert reattach_source_tags("lives in Taipei", [f"likes jazz {A}"], "likes tea") == "lives in Taipei"


def test_one_fact_told_in_two_places_keeps_both_tags() -> None:
    assert reattach_source_tags("likes jazz", [f"likes jazz {A}"], f"likes jazz {DM}") == f"likes jazz {A} {DM}"


def test_empty_memory_stays_empty() -> None:
    assert reattach_source_tags(None, [f"likes jazz {A}"], f"x {B}") is None
    assert reattach_source_tags("", [f"likes jazz {A}"], f"x {B}") == ""


def test_huge_memories_are_handled_in_bounded_time() -> None:
    lines = [f"fact number {number} about something {A}" for number in range(3000)]
    merged = "\n".join(line.replace(f" {A}", "") for line in lines)

    started = time.monotonic()
    result = reattach_source_tags(merged, ["\n".join(lines)], f"new {B}")

    assert time.monotonic() - started < 2.0
    assert result is not None and result.count(A) >= 1


# ------------------------------------------------------------ through the save path


@pytest.mark.asyncio
async def test_saving_puts_the_tags_back_even_when_the_merge_model_drops_them() -> None:
    from cogs.memory.users.models import UserInfo

    saved: List[Any] = []

    class _Users:
        async def get_user_info(self, user_id: str) -> Any:
            return UserInfo(discord_id="1", discord_name="n", procedural_memory=f"likes jazz {A}")

        async def update_user_data(self, user_id: str, merged: Any, **kwargs: Any) -> bool:
            saved.append(merged)
            return True

    class _Logger:
        def info(self, *args: Any, **kwargs: Any) -> None:
            return None

        warning = error = debug = info

    async def merge(old: Any, new: str, user_id: str, guild_id: str) -> Any:
        return UserInfo(discord_id="1", discord_name="n", procedural_memory="likes jazz\nlikes tea")

    cog = SimpleNamespace(
        user_manager=_Users(), _invoke_ai_merge_agent=merge, logger=_Logger(),
        _translate=lambda guild_id, *path, fallback_key="", **kwargs: "ok",
        _get_guild_id_from_context=lambda context: "2", bot=SimpleNamespace(orchestrator=None),
    )
    message = SimpleNamespace(guild=SimpleNamespace(name="Tea House", id=2))

    await UserDataCog._save_user_data(cog, "1", "n", "likes tea", message)

    assert saved[0].procedural_memory == f"likes jazz {A}\nlikes tea {B}"
