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


def test_a_fact_the_model_rewrote_keeps_its_source() -> None:
    """Reworded without a tag from the model: only the old fact's own tag, never this save's (unrelated save, review)."""
    result = reattach_source_tags("喜歡吃拉麵", [f"喜歡拉麵 {A}"], f"喜歡茶 {B}")

    assert result == f"喜歡吃拉麵 {A}"


def test_a_line_that_matches_nothing_stays_untagged() -> None:
    """Changed from 'gets this save's tag': a wrong 'told here' claim is worse than a missing tag (review)."""
    result = reattach_source_tags("lives in Taipei", [f"likes jazz {A}"], f"likes tea {B}")

    assert result == "lives in Taipei"


def test_nothing_is_invented_when_the_save_has_no_tag() -> None:
    assert reattach_source_tags("lives in Taipei", [f"likes jazz {A}"], "likes tea") == "lives in Taipei"


def test_one_fact_told_in_two_places_keeps_both_tags() -> None:
    assert reattach_source_tags("likes jazz", [f"likes jazz {A}"], f"likes jazz {DM}") == f"likes jazz {A} {DM}"


def test_empty_memory_stays_empty() -> None:
    assert reattach_source_tags(None, [f"likes jazz {A}"], f"x {B}") is None
    assert reattach_source_tags("", [f"likes jazz {A}"], f"x {B}") == ""


def test_huge_memories_are_handled_in_bounded_time() -> None:
    """Every merged line is reworded, so each needs a similarity search: without the time budget this takes minutes."""
    lines = [f"fact number {number} about something {A}" for number in range(3000)]
    merged = "\n".join(f"fact no. {number} about something" for number in range(3000))

    started = time.monotonic()
    result = reattach_source_tags(merged, ["\n".join(lines)], f"new {B}")

    assert time.monotonic() - started < 2.0
    assert result is not None and len(result.split("\n")) == 3000


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


# ----------------------------------------------------------------- review findings


def test_reworded_long_lines_cannot_stall_the_matching() -> None:
    """Fuzzy comparison is quadratic in line length; a 16,000 character rewrite took 5 seconds."""
    started = time.monotonic()
    result = reattach_source_tags("ba" * 8000, [f"{'ab' * 8000} {A}"], f"x {B}")

    assert time.monotonic() - started < 1.0
    assert result is not None


def test_a_joined_line_keeps_the_tag_the_model_gave_for_the_part_that_was_reworded() -> None:
    """'likes jazz' is found inside the line; 'likes tea' was shortened, so only the model's own tag knows it."""
    result = reattach_source_tags(f"likes jazz and tea {B}", [f"likes jazz {A}"], f"likes tea {B}")

    # The model tagged the line, so its choice stands even though A is also in it: the code
    # fills in untagged lines and never adds to a tagged one (an incomplete tag beats a false one).
    assert result == f"likes jazz and tea {B}"


def test_facts_that_differ_only_in_symbols_are_not_the_same_fact() -> None:
    result = reattach_source_tags(f"Programs in C# {B}", [f"Programs in C++ {A}"], f"Programs in C# {B}")

    assert result == f"Programs in C# {B}"


def test_a_reworded_old_fact_is_not_claimed_by_this_save() -> None:
    """Wrongly saying 'told here' is worse than a missing tag, so an unmatched line stays untagged."""
    result = reattach_source_tags("My favorite drink is tea", ["Enjoys drinking tea"], f"lives in Taipei {B}")

    assert result == "My favorite drink is tea"


def test_a_reworded_new_fact_still_gets_this_saves_tag() -> None:
    result = reattach_source_tags("living in Taipei", [f"likes jazz {A}"], f"lives in Taipei {B}")

    assert result == f"living in Taipei {B}"


# ---------------------------------------------------- independent review (second round)


def test_a_superseded_fact_without_a_model_tag_keeps_only_the_old_source() -> None:
    """Known limit: the update may have come from this save, but guessing it would also tag unrelated rewrites."""
    result = reattach_source_tags("Is 26 years old", [f"Is 25 years old {A}"], f"Just turned 26 {B}")

    assert result == f"Is 26 years old {A}"


def test_a_reworded_untagged_legacy_fact_is_not_claimed_by_this_save() -> None:
    result = reattach_source_tags("Is 26 years old", ["Is 25 years old"], f"Just turned 26 {B}")

    assert result == "Is 26 years old"


def test_a_fact_inside_a_longer_word_is_not_contained() -> None:
    """'use go' is in 'use goat farming tools' only as the start of another word."""
    result = reattach_source_tags("use goat farming tools", [f"use go {A}"], f"likes tea {B}")

    assert result == "use goat farming tools"


def test_seventy_reworded_lines_all_keep_their_tags() -> None:
    """There used to be a silent cliff at about 64 lines where all matching was switched off."""
    earlier = "\n".join(f"fact number {number} about something {A}" for number in range(70))
    merged = "\n".join(f"fact no. {number} about something" for number in range(70))

    result = reattach_source_tags(merged, [earlier], f"new fact {B}")

    assert result.count(A) == 70


def test_indentation_of_a_nested_list_is_kept() -> None:
    assert reattach_source_tags("  - jazz", [f"  - jazz {A}"], f"x {B}") == f"  - jazz {A}"


def test_a_malformed_tag_the_model_invented_cannot_pass_as_text_with_a_server_id() -> None:
    result = reattach_source_tags("likes jazz [source: server  id=9]", [f"likes jazz {A}"], f"x {B}")

    assert "[source: server  id=9]" not in result and "[source" in result and A in result


# ------------------------------------------------------- Codex review (third round)


def test_a_repeated_fact_in_other_words_keeps_the_tag_the_model_merged_in() -> None:
    """'likes jazz' told in A, then 'I like jazz' in B: the model merges them and rightly keeps both tags."""
    result = reattach_source_tags(f"likes jazz {A} {B}", [f"likes jazz {A}"], f"I like jazz {B}")

    assert result == f"likes jazz {A} {B}"


def test_when_the_model_tagged_a_reworded_line_its_known_tags_win_over_the_guess() -> None:
    """Old 'Uses C++ [A]', new 'I write software in C# [B]'; the model wrote 'Uses C# ... [B]': not told in A."""
    result = reattach_source_tags(
        f"Uses C# for programming {B}", [f"Uses C++ for programming {A}"], f"I write software in C# {B}"
    )

    assert result == f"Uses C# for programming {B}"


def test_an_exact_match_still_drops_a_tag_nobody_knows() -> None:
    result = reattach_source_tags(f"likes jazz {A} [source: server id=999]", [f"likes jazz {A}"], f"x {B}")

    assert result == f"likes jazz {A}"


# ------------------------------------------------------- Codex review (fourth round)

S1 = "[source: server id=1]"
S2 = "[source: server id=2]"
S3 = "[source: server id=3]"


def test_containment_cannot_run_past_the_time_budget() -> None:
    """100 facts of repeated letters against a 40,000 letter line took 2.8 s in the containment step alone."""
    earlier = "\n".join("a" * length for length in range(400, 500))

    started = time.monotonic()
    result = reattach_source_tags("a" * 40_000, [earlier], f"x {B}")

    assert time.monotonic() - started < 1.0
    assert result is not None


def test_this_saves_tags_do_not_include_the_history_of_a_fact_it_repeated() -> None:
    """Saving 'Likes jazz' from server 2 again must not hand server 1 to an unrelated rewritten fact."""
    result = reattach_source_tags(
        "Likes jazz\nLives in central Taipei",
        [f"Likes jazz {S1}\nLives in Taipei {S3}"],
        f"Likes jazz {S2}",
    )

    assert result == f"Likes jazz {S1} {S2}\nLives in central Taipei {S3}"


def test_a_symbol_that_belongs_to_the_word_is_not_a_boundary() -> None:
    """'Uses C' is not inside 'Uses C++ daily' (and not C# either)."""
    result = reattach_source_tags(f"Uses C++ daily {S2}", [f"Uses C {S1}"], f"I program in C++ {S2}")

    assert result == f"Uses C++ daily {S2}"


# ----------------------------------------------- Codex review (fifth round): one principle


def test_a_paraphrased_private_fact_is_not_claimed_by_an_unrelated_save() -> None:
    """A fact from a DM must not become '[source: this server]' because someone saved something else there."""
    result = reattach_source_tags("Living in Taipei", [f"Lives in Taipei {DM}"], f"Likes jazz {B}")

    assert result == f"Living in Taipei {DM}"


def test_a_negated_fact_keeps_the_tag_the_model_gave_not_the_one_it_contains() -> None:
    result = reattach_source_tags(f"No longer likes jazz {B}", [f"Likes jazz {A}"], f"I dislike jazz now {B}")

    assert result == f"No longer likes jazz {B}"


def test_a_gigantic_memory_is_not_searched_for_similar_facts_at_all() -> None:
    """9,000,000 letters against 9,000,001 took 4 s inside one containment check; past a size cap only identical lines count."""
    huge = "a" * 9_000_000

    started = time.monotonic()
    result = reattach_source_tags("a" * 9_001_001, [f"{huge} {A}"], f"x {B}")

    assert time.monotonic() - started < 1.0
    assert result == "a" * 9_001_001, "no similarity work, so the untagged line stays untagged"
