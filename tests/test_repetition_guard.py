"""A model that gets stuck repeating itself is recognised early and cut where the loop begins."""

from __future__ import annotations

import pytest

from llm.utils.repetition_guard import Loop, RepetitionGuard, find_loop


def _distinct_text(length: int) -> str:
    """Return text in which no short pattern repeats, standing in for a normal reply."""
    return "".join(chr(0x4E00 + (index * 7919) % 5000) for index in range(length))


def test_one_character_repeated_over_and_over_is_cut_after_three() -> None:
    text = "今天天氣真好。" + "好" * 200

    assert find_loop(text) == Loop(keep_length=len("今天天氣真好。好好好"), period=1)


def test_a_repeated_phrase_is_cut_after_its_first_copy() -> None:
    text = "我覺得" + "好吃好吃，" * 40

    assert find_loop(text) == Loop(keep_length=len("我覺得好吃好吃，"), period=5)


def test_a_repeated_sentence_is_cut_after_its_first_copy() -> None:
    sentence = "我現在沒有辦法回答這個問題，因為我不知道答案是什麼。"
    text = "抱歉，" + sentence * 8

    assert find_loop(text) == Loop(keep_length=len("抱歉，" + sentence), period=len(sentence))


@pytest.mark.parametrize(
    "text",
    [
        "哈" * 30,
        "哈哈哈哈哈哈哈哈哈哈！！！！！！！！！！wwwwwwwwww" * 2,
        "好" * 79,
        "-" * 120,
        "|" + "---|" * 20,
        "好吃好吃，" * 19,
        _distinct_text(3000),
    ],
)
def test_ordinary_text_is_not_mistaken_for_a_loop(text: str) -> None:
    assert find_loop(text) is None


def test_the_thresholds_sit_where_documented() -> None:
    assert find_loop("好" * 79) is None
    assert find_loop("好" * 80) == Loop(keep_length=3, period=1)
    assert find_loop("好吃好吃，" * 19) is None
    assert find_loop("好吃好吃，" * 21) == Loop(keep_length=5, period=5)


def test_a_run_of_separator_characters_is_only_a_loop_when_extreme() -> None:
    assert find_loop("=" * 399) is None
    assert find_loop("=" * 400) == Loop(keep_length=3, period=1)


def test_the_guard_trips_as_soon_as_the_loop_is_long_enough() -> None:
    guard = RepetitionGuard()
    prefix = "前言。"
    fed = 0
    verdicts = []

    for character in prefix + "好" * 200:
        fed += 1
        verdicts.append(guard.feed(character))
        if verdicts[-1] is not None:
            break

    assert verdicts[-1] == Loop(keep_length=len(prefix) + 3, period=1)
    assert fed == len(prefix) + 80
    assert guard.feed("好") == verdicts[-1]


@pytest.mark.parametrize("chunk_size", [1, 3, 7, 50])
def test_the_cut_position_does_not_depend_on_how_the_text_arrives(chunk_size: int) -> None:
    text = "我覺得" + "好吃好吃，" * 40
    guard = RepetitionGuard()
    verdicts = [guard.feed(text[start : start + chunk_size]) for start in range(0, len(text), chunk_size)]

    assert verdicts[-1] == find_loop(text)


def test_the_cut_position_counts_from_the_start_of_the_whole_reply_not_a_window() -> None:
    text = _distinct_text(10_000) + "好" * 400
    guard = RepetitionGuard()
    verdicts = [guard.feed(text[start : start + 40]) for start in range(0, len(text), 40)]

    assert verdicts[-1] == Loop(keep_length=10_003, period=1)


def test_a_reply_that_never_repeats_never_trips_the_guard() -> None:
    text = _distinct_text(5000)
    guard = RepetitionGuard()

    assert {guard.feed(text[start : start + 25]) for start in range(0, 5000, 25)} == {None}
