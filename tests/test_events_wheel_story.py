"""Events (sign-ups, waiting list, reminders), the decision wheel, and the story add-ons (dice, recap, card)."""

from __future__ import annotations

import asyncio
import base64
import itertools
import random
from types import SimpleNamespace
from typing import Any, List, Optional

import discord
import pytest

from cogs.events import MAX_DELIVERY_ATTEMPTS, RETRY_DELAY_SECONDS, EventsCog, mention_chunks, mention_lines
from cogs.events_lib.store import CANCELLED, GOING, MAYBE, OPEN, REMINDED, EventStore
from cogs.games_lib import wheel
from cogs.story import dice
from cogs.story.recap_store import RecapStore
from cogs.story_manager import StoryManagerCog, card_prompt
from cogs.wheel import WheelCog

GUILD_ID = 42
_MESSAGE_IDS = itertools.count(700)
NOW = 1_800_000_000.0


class FakeLang:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return f"{keys[-1]}|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))

    def get_server_lang(self, guild_id: str) -> str:
        return "zh_TW"


# ---------------------------------------------------------------------- wheel


def test_wheel_options_are_split_trimmed_and_deduplicated() -> None:
    assert wheel.parse_options("火鍋, 拉麵，咖哩、火鍋 | Ramen;ramen") == ["火鍋", "拉麵", "咖哩", "Ramen"]
    assert wheel.parse_options(" , ,") == []
    assert len(wheel.parse_options(",".join(str(i) for i in range(50)))) == wheel.MAX_OPTIONS
    assert len(wheel.parse_options("x" * 500)[0]) == wheel.MAX_OPTION_LENGTH


def test_the_wheel_moves_every_frame_and_stops_on_a_fair_pick() -> None:
    options = ["a", "b", "c"]
    wins = {index: 0 for index in range(3)}
    for seed in range(300):
        frames = wheel.spin(options, random.Random(seed))
        assert len(frames) == wheel.SPIN_FRAMES + 1
        assert all(a != b for a, b in zip(frames, frames[1:]))
        wins[frames[-1]] += 1
    assert min(wins.values()) > 60  # each of three options wins about a third of the time


def test_two_options_still_spin() -> None:
    frames = wheel.spin(["yes", "no"], random.Random(1))
    assert all(a != b for a, b in zip(frames, frames[1:]))
    assert "🎯 **no**" in wheel.render(["yes", "no"], 1, final=True)


class FakeInteraction:
    def __init__(self, user_id: int = 1, channel_id: int = 500, message: Any = None, permissions: Any = None) -> None:
        self.user = SimpleNamespace(id=user_id, display_name=f"user{user_id}", mention=f"<@{user_id}>")
        self.guild_id = GUILD_ID
        self.channel_id = channel_id
        self.channel = FakeChannel(channel_id)
        self.message = message
        self.permissions = permissions or SimpleNamespace(manage_events=False)
        self.id = 99
        self.sent: List[tuple] = []
        self.edits: List[dict] = []
        self.followups: List[dict] = []
        self.deferred: Optional[dict] = None
        self.response = SimpleNamespace(
            send_message=self._send_message, defer=self._defer, edit_message=self._edit_message,
            is_done=lambda: self.deferred is not None,
        )
        self.followup = SimpleNamespace(send=self._followup)

    async def _send_message(self, content: Any = None, **kwargs: Any) -> None:
        self.sent.append((content, kwargs))

    async def _defer(self, **kwargs: Any) -> None:
        self.deferred = kwargs

    async def _edit_message(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)

    async def _followup(self, content: Any = None, **kwargs: Any) -> None:
        self.followups.append({"content": content, **kwargs})

    async def edit_original_response(self, **kwargs: Any) -> None:
        self.edits.append(kwargs)

    async def original_response(self) -> Any:
        return SimpleNamespace(id=next(_MESSAGE_IDS))


class FakeChannel:
    def __init__(self, channel_id: int = 500, fail: bool = False) -> None:
        self.id = channel_id
        self.fail = fail
        self.sent: List[tuple] = []
        self.history_messages: List[Any] = []

    async def send(self, content: Any = None, **kwargs: Any) -> Any:
        if self.fail:
            raise discord.HTTPException(SimpleNamespace(status=500, reason="boom"), "boom")
        self.sent.append((content, kwargs))
        return SimpleNamespace(id=len(self.sent))

    def get_partial_message(self, message_id: int) -> Any:
        channel = self

        class Partial:
            async def edit(self, **kwargs: Any) -> None:
                channel.sent.append(("edit", kwargs))

        return Partial()

    async def history(self, limit: int = 40, before: Any = None):
        for message in self.history_messages[:limit]:
            yield message


@pytest.mark.asyncio
async def test_a_spin_edits_the_message_until_it_stops_and_blocks_a_second_spin() -> None:
    cog = WheelCog(SimpleNamespace())
    cog.lang_manager = FakeLang()
    cog.frame_seconds = 0
    interaction = FakeInteraction()

    await WheelCog.spin.callback(cog, interaction, "火鍋, 拉麵, 咖哩")

    assert len(interaction.edits) == wheel.SPIN_FRAMES + 1
    final = interaction.edits[-1]["embed"]
    assert final.footer.text.startswith("result|option=")
    assert all(edit["allowed_mentions"].everyone is False for edit in interaction.edits)
    assert cog._spinning == set()

    cog._spinning.add(500)
    busy = FakeInteraction()
    await WheelCog.spin.callback(cog, busy, "a, b")
    assert busy.sent[0][0] == "busy|" and busy.edits == []


@pytest.mark.asyncio
async def test_too_few_options_are_refused() -> None:
    cog = WheelCog(SimpleNamespace())
    cog.lang_manager = FakeLang()
    interaction = FakeInteraction()

    await WheelCog.spin.callback(cog, interaction, "only one")

    assert interaction.sent[0][0] == "too_few|minimum=2"


@pytest.mark.asyncio
async def test_food_wheel_charges_the_search_and_ends_on_the_restaurant_card(monkeypatch: pytest.MonkeyPatch) -> None:
    hits: list = []
    places = [{"name": f"店{i}", "rating": 4.0, "address": "x", "maps_url": f"u{i}"} for i in range(8)]

    class Provider:
        async def async_search_list(self, keyword: str, lang: str) -> list:
            return [dict(place) for place in places]

        async def async_fetch_detail(self, url: str, lang: str) -> dict:
            return {"photo_url": "p"}

    db = SimpleNamespace(getKeywords=lambda: [("拉麵",)], storeSearchRecord=lambda **kwargs: 5)
    recommender = SimpleNamespace(suggest_keyword=lambda guild, keywords: keywords[0], rank_candidates=lambda guild, found: found)
    search = SimpleNamespace(db=db, recommender=recommender, provider=Provider())
    bot = SimpleNamespace(
        get_cog=lambda name: search if name == "InternetSearchCog" else None,
        rate_limiter=SimpleNamespace(hit=lambda bucket, user_id: hits.append(bucket) or 0),
    )
    cog = WheelCog(bot)
    cog.lang_manager = FakeLang()
    cog.frame_seconds = 0
    interaction = FakeInteraction()

    await WheelCog.food.callback(cog, interaction, None)

    assert hits == ["chat"]
    spin = interaction.edits[0]["embed"].description
    assert spin.count("\n") == 5  # six restaurants on the wheel
    card = interaction.edits[-1]
    assert card["view"] is not None and card["embed"].image.url == "p"


@pytest.mark.asyncio
async def test_food_wheel_respects_the_quota() -> None:
    bot = SimpleNamespace(
        get_cog=lambda name: SimpleNamespace(db=1, recommender=1, provider=1),
        rate_limiter=SimpleNamespace(hit=lambda bucket, user_id: 12.5),
    )
    cog = WheelCog(bot)
    cog.lang_manager = FakeLang()
    interaction = FakeInteraction()

    await WheelCog.food.callback(cog, interaction, "拉麵")

    assert interaction.sent[0][0] == "rate_limited|seconds=13"


# ---------------------------------------------------------------------- events


@pytest.fixture
def store() -> EventStore:
    return EventStore(":memory:")


def _event(store: EventStore, capacity: int = 0, starts_in: float = 3600, remind: int = 15) -> Any:
    event_id = store.add(GUILD_ID, 500, 1, "Valorant 五排", NOW + starts_in, capacity, remind, NOW)
    store.set_message(event_id, 1000 + event_id)
    return store.get(event_id)


def test_the_waiting_list_moves_up_when_someone_leaves(store: EventStore) -> None:
    event = _event(store, capacity=2)
    for user in (1, 2, 3, 4):
        store.sign_up(event.id, user, GOING, NOW)
    store.sign_up(event.id, 5, MAYBE, NOW)

    roster = store.roster(event)
    assert (roster.going, roster.waiting, roster.maybe) == ([1, 2], [3, 4], [5])

    store.leave(event.id, 1)
    roster = store.roster(event)
    assert (roster.going, roster.waiting) == ([2, 3], [4])


def test_switching_to_maybe_and_back_goes_to_the_end_of_the_line(store: EventStore) -> None:
    event = _event(store, capacity=2)
    for user in (1, 2, 3):
        store.sign_up(event.id, user, GOING, NOW)
    store.sign_up(event.id, 1, MAYBE, NOW)
    store.sign_up(event.id, 1, GOING, NOW)
    store.sign_up(event.id, 2, GOING, NOW)  # answering the same again keeps the place

    roster = store.roster(event)
    assert (roster.going, roster.waiting) == ([2, 3], [1])


def test_reminders_fall_due_and_a_failure_waits_before_the_retry(store: EventStore) -> None:
    event = _event(store, starts_in=3600, remind=15)
    unposted = store.add(GUILD_ID, 500, 1, "draft", NOW + 60, 0, 15, NOW)  # no message yet

    assert store.due_reminders(NOW) == []
    remind_at = NOW + 3600 - 15 * 60
    assert store.next_reminder_at() == remind_at
    assert [e.id for e in store.due_reminders(remind_at)] == [event.id]

    store.record_failure(event.id, remind_at + 60)
    assert store.due_reminders(remind_at + 30) == []
    assert store.next_reminder_at() == remind_at + 60
    store.mark_reminded(event.id)
    assert store.get(event.id).status == REMINDED
    assert store.get(unposted).status == OPEN and store.due_reminders(NOW + 10_000) == []


def test_mentions_fit_discord_limits() -> None:
    users = list(range(10**17, 10**17 + 100))
    field = mention_lines(users, more="+{count}")
    assert len(field) <= 1024 and field.endswith(f"+{100 - field.count('<@')}")
    chunks = mention_chunks("⏰ start!", users)
    assert all(len(chunk) <= 2000 for chunk in chunks)
    assert sum(chunk.count("<@") for chunk in chunks) == 100


def _events_cog(store: EventStore, channel: FakeChannel) -> EventsCog:
    bot = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == channel.id else None, get_cog=lambda name: None)
    cog = EventsCog(bot, store=store)
    cog.lang_manager = FakeLang()
    cog._now = lambda: NOW
    return cog


@pytest.mark.asyncio
async def test_joining_a_full_event_waits_and_leaving_promotes_and_pings_only_the_promoted(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store, capacity=1)
    store.sign_up(event.id, 1, GOING, NOW)
    message = SimpleNamespace(id=event.message_id)

    waiting = FakeInteraction(user_id=2, message=message)
    waiting.channel = channel
    await cog.answer(waiting, GOING)
    assert waiting.followups[-1]["content"] == "you_are_waiting|position=1"
    assert waiting.followups[-1]["ephemeral"] is True

    leaving = FakeInteraction(user_id=1, message=message)
    leaving.channel = channel
    await cog.answer(leaving, None)

    assert leaving.followups[-1]["content"] == "you_left|"
    content, kwargs = channel.sent[-1]
    assert "<@2>" in content and "<@1>" not in content
    assert [user.id for user in kwargs["allowed_mentions"].users] == [2]


@pytest.mark.asyncio
async def test_buttons_refuse_cancelled_and_started_events(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)
    store.cancel(event.id)
    interaction = FakeInteraction(user_id=3, message=SimpleNamespace(id=event.message_id))
    await cog.answer(interaction, GOING)
    assert interaction.sent[0][0] == "event_gone|"

    started = _event(store, starts_in=-10)
    interaction = FakeInteraction(user_id=3, message=SimpleNamespace(id=started.message_id))
    await cog.answer(interaction, GOING)
    assert interaction.sent[0][0] == "event_started|"
    assert store.roster(started).going == []


@pytest.mark.asyncio
async def test_only_the_host_or_an_event_manager_can_cancel(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)

    stranger = FakeInteraction(user_id=9)
    await EventsCog.cancel.callback(cog, stranger, event.id)
    assert stranger.sent[0][0] == "not_yours|" and store.get(event.id).status == OPEN

    manager = FakeInteraction(user_id=9, permissions=SimpleNamespace(manage_events=True))
    await EventsCog.cancel.callback(cog, manager, event.id)
    assert store.get(event.id).status == CANCELLED

    other_guild = _event(store)
    with store._session() as db:
        db.execute("UPDATE events SET guild_id = 7 WHERE id = ?", (other_guild.id,))
    host = FakeInteraction(user_id=1)
    await EventsCog.cancel.callback(cog, host, other_guild.id)
    assert host.sent[0][0] == "not_found|"


@pytest.mark.asyncio
async def test_the_reminder_pings_only_people_going_and_is_marked_after_sending(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store, capacity=1)
    store.sign_up(event.id, 1, GOING, NOW)
    store.sign_up(event.id, 2, GOING, NOW)  # waiting
    store.sign_up(event.id, 3, MAYBE, NOW)

    await cog._remind(store.get(event.id), NOW + 3000)

    content, kwargs = channel.sent[-1]
    assert "<@1>" in content and "<@2>" not in content and "<@3>" not in content
    assert [user.id for user in kwargs["allowed_mentions"].users] == [1]
    assert kwargs["allowed_mentions"].everyone is False
    assert store.get(event.id).status == REMINDED


@pytest.mark.asyncio
async def test_a_failed_reminder_is_retried_a_few_times_then_dropped(store: EventStore) -> None:
    channel = FakeChannel(fail=True)
    cog = _events_cog(store, channel)
    event = _event(store)
    store.sign_up(event.id, 1, GOING, NOW)

    for attempt in range(MAX_DELIVERY_ATTEMPTS):
        assert store.get(event.id).status == OPEN
        now = NOW + 3000 + attempt * RETRY_DELAY_SECONDS
        assert [e.id for e in store.due_reminders(now)] == [event.id]
        await cog._remind(store.get(event.id), now)
        assert store.due_reminders(now) == []  # waits before the next try

    assert store.get(event.id).status == REMINDED


@pytest.mark.asyncio
async def test_creating_an_event_checks_the_time_and_limits(store: EventStore) -> None:
    from datetime import datetime

    cog = _events_cog(store, FakeChannel())
    cog.parse_time = lambda text: None if text == "?" else datetime.fromtimestamp(NOW + float(text))

    for when, expected in (("?", "invalid_time|"), ("-5", "past_time|"), (str(400 * 86400), "too_far|")):
        interaction = FakeInteraction()
        await EventsCog.create.callback(cog, interaction, "開黑", when, 0, 15)
        assert interaction.sent[0][0] == expected

    for _ in range(5):
        await EventsCog.create.callback(cog, FakeInteraction(), "開黑", "3600", 0, 15)
    interaction = FakeInteraction()
    await EventsCog.create.callback(cog, interaction, "開黑", "3600", 0, 15)
    assert interaction.sent[0][0] == "user_limit|limit=5"

    event = store.upcoming(GUILD_ID, NOW)[0]
    assert event.message_id >= 700 and store.roster(event).going == [1]  # the host goes to their own event


# ---------------------------------------------------------------------- dice


def test_dice_notation_rolls_and_describes_itself() -> None:
    result = dice.roll("2d6 + 3", random.Random(4))
    assert result.notation == "2d6+3"
    assert 5 <= result.total <= 15
    faces = result.rolls[0][2]
    assert result.describe() == f"2d6+3 → [{faces[0]}, {faces[1]}] + 3 = {sum(faces) + 3}"
    assert dice.roll("d20-1", random.Random(1)).notation == "1d20-1"
    assert dice.roll("-d4", random.Random(1)).total < 0


@pytest.mark.parametrize("notation", ["", "abc", "2d", "d1", "0d6", "5", "2d6++3", "2d6 3", "d6d6"])
def test_bad_dice_are_refused(notation: str) -> None:
    with pytest.raises(dice.DiceError) as error:
        dice.parse(notation)
    assert error.value.key == "dice_invalid"


@pytest.mark.parametrize("notation", ["101d6", "1d1001", "60d6+60d6", "d6+99999"])
def test_too_many_dice_are_refused(notation: str) -> None:
    with pytest.raises(dice.DiceError) as error:
        dice.parse(notation)
    assert error.value.key == "dice_too_many"


# ---------------------------------------------------------------------- story


class FakeStoryManager:
    def __init__(self, instance: Any, characters: Optional[dict] = None) -> None:
        self.instance = instance
        self.dice: List[tuple] = []
        self.character_db = SimpleNamespace(
            get_character=lambda character_id: (characters or {}).get(character_id),
            get_selectable_characters=lambda guild_id, user_id: [
                c for c in (characters or {}).values() if c.guild_id == guild_id and (c.is_public or c.creator_id == user_id)
            ],
        )

    def _get_db(self, guild_id: int) -> Any:
        return SimpleNamespace(get_story_instance=lambda channel_id: self.instance if channel_id == 500 else None)

    def add_dice_result(self, channel_id: int, text: str) -> None:
        self.dice.append((channel_id, text))


def _story_cog(instance: Any = None, characters: Optional[dict] = None, **bot_attrs: Any) -> StoryManagerCog:
    lang = FakeLang()
    cogs = {"LanguageManager": lang, **bot_attrs.pop("cogs", {})}
    bot = SimpleNamespace(get_cog=lambda name: cogs.get(name), user=SimpleNamespace(id=1), **bot_attrs)
    cog = StoryManagerCog(bot)
    cog.recap_store = RecapStore(":memory:")
    cog.story_manager = FakeStoryManager(instance, characters)
    return cog


def _instance(**overrides: Any) -> Any:
    data = dict(guild_id=GUILD_ID, channel_id=500, is_active=True, summaries=["勇者進了洞窟。"])
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_a_roll_in_a_story_channel_is_handed_to_the_story() -> None:
    cog = _story_cog(_instance())
    interaction = FakeInteraction(user_id=5)

    await StoryManagerCog.roll.callback(cog, interaction, "1d20", "撬鎖")

    text, kwargs = interaction.sent[0]
    assert "roll_in_story|" in text and kwargs["allowed_mentions"].users is False
    assert cog.story_manager.dice[0][0] == 500 and cog.story_manager.dice[0][1].endswith("for: 撬鎖")

    elsewhere = FakeInteraction(user_id=5, channel_id=501)
    await StoryManagerCog.roll.callback(cog, elsewhere, "1d20", None)
    assert "roll_in_story" not in elsewhere.sent[0][0] and len(cog.story_manager.dice) == 1

    bad = FakeInteraction()
    await StoryManagerCog.roll.callback(cog, bad, "1000d6", None)
    assert bad.sent[0][0].startswith("dice_too_many|") and bad.sent[0][1]["ephemeral"] is True


def test_the_story_manager_keeps_the_latest_few_dice_for_the_next_turn() -> None:
    from cogs.story.manager import MAX_PENDING_DICE, StoryManager

    manager = SimpleNamespace(dice_results={})
    for index in range(MAX_PENDING_DICE + 3):
        StoryManager.add_dice_result(manager, 500, f"roll {index}")
    assert manager.dice_results[500] == [f"roll {i}" for i in range(3, MAX_PENDING_DICE + 3)]


@pytest.mark.asyncio
async def test_the_daily_recap_is_posted_once_on_a_new_day(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list = []

    async def fake_write(orchestrator, guild_id, language, summaries, lines, charge):
        calls.append((summaries, lines, charge()))
        return "前情提要：勇者還在洞窟裡。"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", fake_write)
    hits: list = []
    cog = _story_cog(
        _instance(), orchestrator=object(), rate_limiter=SimpleNamespace(hit=lambda bucket, user_id: hits.append(user_id) or 0)
    )
    channel = FakeChannel()
    channel.history_messages = [
        SimpleNamespace(author=SimpleNamespace(id=1, display_name="PigPig"), content="", embeds=[SimpleNamespace(description="洞窟裡很暗。")]),
        SimpleNamespace(author=SimpleNamespace(id=5, display_name="Alice"), content="我點起火把", embeds=[]),
    ]
    message = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), channel=channel, author=SimpleNamespace(id=5))

    day = ["2026-10-25"]
    cog._today = lambda: day[0]
    await cog.maybe_post_daily_recap(message)  # first day the story is seen: nothing to recap
    assert channel.sent == []

    day[0] = "2026-10-26"
    await asyncio.gather(cog.maybe_post_daily_recap(message), cog.maybe_post_daily_recap(message))
    assert len(channel.sent) == 1
    assert channel.sent[0][1]["embed"].description == "前情提要：勇者還在洞窟裡。"
    summaries, lines, _ = calls[0]
    assert lines == ["Alice: 我點起火把", "PigPig: 洞窟裡很暗。"]
    assert hits == [5]  # the model call is charged to whoever moved the story on


@pytest.mark.asyncio
async def test_a_recap_falls_back_to_the_saved_summary_when_the_quota_is_used_up(monkeypatch: pytest.MonkeyPatch) -> None:
    from llm.game_writer import QuotaExhausted

    async def out_of_quota(*args: Any) -> str:
        raise QuotaExhausted(30)

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", out_of_quota)
    cog = _story_cog(_instance(), orchestrator=object(), rate_limiter=SimpleNamespace(hit=lambda b, u: 30))
    interaction = FakeInteraction()

    await StoryManagerCog.recap.callback(cog, interaction)

    assert interaction.followups[0]["embed"].description == "勇者進了洞窟。"


@pytest.mark.asyncio
async def test_recap_needs_a_running_story() -> None:
    cog = _story_cog(_instance(is_active=False))
    interaction = FakeInteraction()
    await StoryManagerCog.recap.callback(cog, interaction)
    assert interaction.sent[0][0] == "no_story|"


def _character(**overrides: Any) -> Any:
    data = dict(
        character_id="c1", name="艾莉絲", description="銀髮的劍士", guild_id=GUILD_ID, creator_id=5,
        is_public=True, attributes={"職業": "劍士"},
    )
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeImages:
    def __init__(self) -> None:
        self.prompts: List[str] = []

    async def _generate_image_logic(self, prompt: str, guild_id: str, channel_id: int) -> dict:
        self.prompts.append(prompt)
        return {"attachments": [{"data_base64": base64.b64encode(b"png").decode()}]}


@pytest.mark.asyncio
async def test_a_character_card_is_drawn_and_a_private_one_is_shown_only_to_its_creator() -> None:
    images = FakeImages()
    hits: list = []
    characters = {"c1": _character(), "c2": _character(character_id="c2", name="影", is_public=False)}
    cog = _story_cog(
        characters=characters, cogs={"ImageGenerationCog": images},
        rate_limiter=SimpleNamespace(hit=lambda bucket, user_id: hits.append(bucket) or 0),
    )

    public = FakeInteraction(user_id=7)
    await StoryManagerCog.card.callback(cog, public, "c1")
    assert public.deferred == {"ephemeral": False}
    assert public.followups[0]["embed"].title == "艾莉絲" and public.followups[0]["ephemeral"] is False
    assert "艾莉絲" in images.prompts[0] and "銀髮的劍士" in images.prompts[0]

    stranger = FakeInteraction(user_id=7)
    await StoryManagerCog.card.callback(cog, stranger, "c2")
    assert stranger.sent[0][0] == "card_not_found|"

    owner = FakeInteraction(user_id=5)
    await StoryManagerCog.card.callback(cog, owner, "c2")
    assert owner.deferred == {"ephemeral": True} and owner.followups[0]["ephemeral"] is True
    assert hits == ["image", "image"]  # the refused card was not charged


@pytest.mark.asyncio
async def test_card_autocomplete_lists_only_selectable_characters() -> None:
    characters = {"c1": _character(), "c2": _character(character_id="c2", name="影", is_public=False), "c3": _character(character_id="c3", name="外人", guild_id=7)}
    cog = _story_cog(characters=characters)

    choices = await cog._card_autocomplete(FakeInteraction(user_id=7), "")

    assert [choice.value for choice in choices] == ["c1"]


def test_card_prompt_keeps_details_short() -> None:
    prompt = card_prompt(_character(description="x" * 5000))
    assert len(prompt) < 1500 and "no text" in prompt


@pytest.mark.asyncio
async def test_the_event_list_hides_events_in_channels_the_member_cannot_see(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    visible = _event(store)
    hidden_id = store.add(GUILD_ID, 600, 1, "秘密聚會", NOW + 3600, 0, 15, NOW)
    store.set_message(hidden_id, 5000)

    def channel(channel_id: int) -> Any:
        allowed = channel_id == 500
        return SimpleNamespace(
            permissions_for=lambda member: SimpleNamespace(view_channel=allowed, read_message_history=allowed)
        )

    interaction = FakeInteraction(user_id=3)
    interaction.guild = SimpleNamespace(get_channel_or_thread=channel)
    await EventsCog.list_events.callback(cog, interaction)

    text = interaction.sent[0][0]
    assert f"id={visible.id}" in text and "秘密聚會" not in text


@pytest.mark.asyncio
async def test_buttons_reach_the_cog_loaded_now() -> None:
    from cogs.events import EventView

    pressed: list = []
    current = SimpleNamespace(answer=lambda interaction, status: _record(pressed, status))
    view = EventView(SimpleNamespace(get_cog=lambda name: current if name == "EventsCog" else None))

    await view._answer(FakeInteraction(), GOING)

    assert pressed == [GOING]


async def _record(log: list, status: Any) -> None:
    log.append(status)
