"""Tests for stripping protocol and context-format artifacts from model replies.

The samples below are taken from real bot replies that leaked into channels.
"""

from __future__ import annotations

import pytest

from llm.utils.reply_sanitizer import sanitize_reply

METADATA = "[Replying to @awen07712: '<@1208661941539704852> 超級敷衍喔' (MessageID:1501223473899376792) | timestamp: 1777989968.522 (2026-05-05 14:06:08 UTC)]"


def test_plain_text_is_unchanged() -> None:
    assert sanitize_reply("哈囉，今天過得好嗎？") == "哈囉，今天過得好嗎？"


def test_text_between_the_markers_is_returned() -> None:
    assert sanitize_reply("<som> Hello! <eom>") == "Hello!"


def test_a_missing_opening_marker_does_not_leak_the_closing_one() -> None:
    assert sanitize_reply("好喔 😊 <eom>\n") == "好喔 😊"


def test_metadata_after_the_closing_marker_is_dropped() -> None:
    raw = f"<@848933622730981386> 嗚哇，這是在指控我嗎！ 😂 <eom> {METADATA}"

    assert sanitize_reply(raw) == "<@848933622730981386> 嗚哇，這是在指控我嗎！ 😂"


def test_metadata_without_markers_is_dropped() -> None:
    raw = f"查了一下，三重有很多好吃的喔！ 😋  {METADATA}"

    assert sanitize_reply(raw) == "查了一下，三重有很多好吃的喔！ 😋"


def test_an_imitated_history_prefix_and_suffix_are_dropped() -> None:
    raw = (
        "[PigPig🐖 | UserID:1208661941539704852 | MessageID:1501296554163101722] <som> 像是：夜市小吃 <eom> "
        "[timestamp: 1778007408.112 (2026-05-05 18:56:48 UTC)]"
    )

    assert sanitize_reply(raw) == "像是：夜市小吃"


def test_a_prefix_inside_the_reply_text_is_dropped() -> None:
    raw = "查了一下  [PigPig🐖 | UserID:12 | MessageID:34] <som> 三重很多好吃的 <eom>"

    assert sanitize_reply(raw) == "三重很多好吃的"


def test_the_tool_call_placeholder_is_never_a_reply() -> None:
    assert sanitize_reply("[Assistant: Calling tool(s): add_reaction, add_reaction]") == ""


def test_the_tool_call_placeholder_is_removed_from_a_longer_reply() -> None:
    raw = "<som> 好喔！ <eom> [Assistant: Calling tool(s): add_reaction]"

    assert sanitize_reply(raw) == "好喔！"


def test_a_tool_result_header_is_removed() -> None:
    assert sanitize_reply("[System: Tool Result (get_guild_emojis)]\n哈囉") == "哈囉"


def test_reaction_and_reply_fields_are_dropped() -> None:
    raw = "好 [reply_to: 1501223473899376792 | reactions: 👍, 😂 | timestamp: 1.5 (2026-05-05 14:06:08 UTC)]"

    assert sanitize_reply(raw) == "好"


def test_thinking_before_the_reply_is_dropped() -> None:
    raw = "<think>The user wants a joke.</think><som> 為什麼雞要過馬路？ <eom>"

    assert sanitize_reply(raw) == "為什麼雞要過馬路？"


def test_text_after_the_last_closing_think_tag_is_the_reply() -> None:
    assert sanitize_reply("<think>hmm</think>\n答案是 42") == "答案是 42"


def test_an_unclosed_thinking_block_yields_nothing() -> None:
    assert sanitize_reply("<think>I should say hello but") == ""


def test_several_marked_segments_are_joined() -> None:
    assert sanitize_reply("<som>第一段<eom> 雜訊 <som>第二段<eom>") == "第一段\n第二段"


def test_nothing_remains_of_a_reply_made_only_of_tags() -> None:
    assert sanitize_reply("<som> <eom>") == ""


@pytest.mark.parametrize(
    "text",
    [
        "用 `[name | UserID:42]` 這種格式只是範例",
        "```python\nitems = [1, 2, 3]\n```",
        "現在是 <t:1731427200:f>，倒數 <t:1731427200:R>",
        "the timestamp: 12345 is just a number in my sentence",
        "他說 [很重要] 的事情 [見下方]",
        "<@123456789012345678> 你好 **粗體** > 引用",
    ],
)
def test_ordinary_content_is_left_alone(text: str) -> None:
    assert sanitize_reply(text) == text


def test_blank_lines_are_collapsed() -> None:
    assert sanitize_reply("<som>a\n\n\n\n\nb<eom>") == "a\n\nb"
