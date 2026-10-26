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
from cogs.story.manager import MAX_PENDING_DICE, StoryManager
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


class FakeGuild:
    """Finds channels, and members as they are now (by default the interaction's member)."""

    def __init__(self, get_channel_or_thread: Any, *members: Any) -> None:
        self.get_channel_or_thread = get_channel_or_thread
        self.members = {member.id: member for member in members}
        self.fetched: List[int] = []

    def get_member(self, user_id: int) -> Any:
        return self.members.get(user_id)

    async def fetch_member(self, user_id: int) -> Any:
        self.fetched.append(user_id)
        raise discord.NotFound(SimpleNamespace(status=404, reason="gone"), "gone")


class FakeInteraction:
    def __init__(self, user_id: int = 1, channel_id: int = 500, message: Any = None, permissions: Any = None) -> None:
        self.user = SimpleNamespace(id=user_id, display_name=f"user{user_id}", mention=f"<@{user_id}>")
        self.guild_id = GUILD_ID
        self.channel_id = channel_id
        self.channel = FakeChannel(channel_id)
        self.guild = FakeGuild(lambda cid: self.channel if cid == self.channel.id else None, self.user)
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
    def __init__(self, channel_id: int = 500, fail: bool = False, fail_on: Optional[int] = None) -> None:
        self.id = channel_id
        self.fail = fail
        # Fail only the send with this number (1-based), once.
        self.fail_on = fail_on
        self.attempts = 0
        self.sent: List[tuple] = []
        self.history_messages: List[Any] = []
        self.history_readers: Optional[set] = None  # None: everyone who sees it may read the history
        self.viewer_ids: Optional[set] = None  # None: every member sees the channel
        self.managers: set = set()  # members with Manage Events
        self.type = discord.ChannelType.text
        # Each member has a role of their own, so permissions are worked out per member.
        self.guild = SimpleNamespace(
            default_role=SimpleNamespace(id=0), members=[SimpleNamespace(id=i, roles=[]) for i in range(1, 10)]
        )

    @property
    def overwrites(self) -> dict:
        """An overwrite denying the history (or the channel) to whoever is left out."""
        if self.history_readers is None and self.viewer_ids is None:
            return {}
        deny = SimpleNamespace(view_channel=self.viewer_ids is not None, read_message_history=self.history_readers is not None)
        return {discord.Object(1234): SimpleNamespace(pair=lambda: (SimpleNamespace(), deny))}

    def permissions_for(self, who: Any) -> Any:
        who_id = getattr(who, "id", None)
        if getattr(who, "lost_access", False):  # a member whose role was taken away
            return SimpleNamespace(view_channel=False, read_message_history=False, manage_threads=False)
        if who_id == 0:  # @everyone
            return SimpleNamespace(view_channel=self.viewer_ids is None, read_message_history=self.viewer_ids is None, manage_threads=False)
        sees = self.viewer_ids is None or who_id in self.viewer_ids
        reads = sees and (self.history_readers is None or who_id in self.history_readers)
        return SimpleNamespace(
            view_channel=sees, read_message_history=reads, manage_threads=False, manage_events=who_id in self.managers
        )

    async def send(self, content: Any = None, **kwargs: Any) -> Any:
        self.attempts += 1
        if self.fail or self.attempts == self.fail_on:
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
    async def fetch_channel(channel_id: int) -> Any:
        raise discord.NotFound(SimpleNamespace(status=404, reason="gone"), "gone")

    async def wait_until_ready() -> None:
        return None

    bot = SimpleNamespace(
        get_channel=lambda channel_id: channel if channel_id == channel.id else None, get_cog=lambda name: None,
        fetch_channel=fetch_channel, wait_until_ready=wait_until_ready,
    )
    cog = EventsCog(bot, store=store)
    cog.lang_manager = FakeLang()
    cog._now = lambda: NOW
    cog.hidden_ids = lambda guild_id: set()
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
    assert interaction.followups[0]["content"] == "event_gone|"

    started = _event(store, starts_in=-10)
    interaction = FakeInteraction(user_id=3, message=SimpleNamespace(id=started.message_id))
    await cog.answer(interaction, GOING)
    assert interaction.followups[0]["content"] == "event_started|"
    assert store.roster(started).going == []


@pytest.mark.asyncio
async def test_only_the_host_or_an_event_manager_can_cancel(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)

    stranger = FakeInteraction(user_id=9)
    await EventsCog.cancel.callback(cog, stranger, event.id)
    assert stranger.sent[0][0] == "not_yours|" and store.get(event.id).status == OPEN

    manager = FakeInteraction(user_id=9, permissions=SimpleNamespace(manage_events=True))
    manager.channel.managers = {9}
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
    # The real queue of pending rolls.
    add_dice_result = StoryManager.add_dice_result
    confirm_dice_result = StoryManager.confirm_dice_result
    discard_dice_result = StoryManager.discard_dice_result

    def __init__(self, instance: Any, characters: Optional[dict] = None) -> None:
        self.instance = instance
        self.dice_results: dict = {}
        self.dice_generation: dict = {}
        self.character_db = SimpleNamespace(
            get_character=lambda character_id: (characters or {}).get(character_id),
            get_selectable_characters=lambda guild_id, user_id: [
                c for c in (characters or {}).values() if c.guild_id == guild_id and (c.is_public or c.creator_id == user_id)
            ],
        )

    def _get_db(self, guild_id: int) -> Any:
        return SimpleNamespace(get_story_instance=lambda channel_id: self.instance if channel_id == 500 else None)

    @property
    def dice(self) -> List[tuple]:
        return [(channel_id, roll.text) for channel_id, rolls in self.dice_results.items() for roll in rolls]


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

    manager = SimpleNamespace(dice_results={}, dice_generation={})
    for index in range(MAX_PENDING_DICE + 3):
        StoryManager.add_dice_result(manager, 500, f"roll {index}")
    assert [roll.text for roll in manager.dice_results[500]] == [f"roll {i}" for i in range(3, MAX_PENDING_DICE + 3)]


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
    message = SimpleNamespace(
        guild=SimpleNamespace(id=GUILD_ID, default_role=SimpleNamespace(id=GUILD_ID)), channel=channel, author=SimpleNamespace(id=5)
    )

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
    interaction.guild = FakeGuild(channel, interaction.user)
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


@pytest.mark.asyncio
async def test_the_event_list_hides_events_in_private_threads(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    thread_event = _event(store)

    thread = SimpleNamespace(
        type=discord.ChannelType.private_thread,
        permissions_for=lambda member: SimpleNamespace(view_channel=True, read_message_history=True, manage_threads=False),  # inherited
        members=[], owner_id=1,
    )
    interaction = FakeInteraction(user_id=3)
    interaction.guild = FakeGuild(lambda channel_id: thread, interaction.user)
    await EventsCog.list_events.callback(cog, interaction)

    assert interaction.sent[0][0] == "none_upcoming|"
    assert thread_event.id  # the event exists, it is just not shown


@pytest.mark.asyncio
async def test_a_press_queued_behind_a_cancel_does_not_sign_up(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store)
    interaction = FakeInteraction(user_id=3, message=SimpleNamespace(id=event.message_id))

    async with cog._lock(event.id):
        press = asyncio.create_task(cog.answer(interaction, GOING))
        await asyncio.sleep(0)  # the press read the event before the cancel and now waits for the lock
        store.cancel(event.id)
    await press

    assert interaction.followups[0]["content"] == "event_gone|" and interaction.edits == []
    assert store.roster(store.get(event.id)).going == []


@pytest.mark.asyncio
async def test_no_reminder_for_an_event_cancelled_after_it_fell_due(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store)
    store.sign_up(event.id, 1, GOING, NOW)
    stale = store.due_reminders(NOW + 3000)[0]
    store.cancel(event.id)

    await cog._remind(stale, NOW + 3000)

    assert channel.sent == [] and store.get(event.id).status == CANCELLED


@pytest.mark.asyncio
async def test_a_retry_after_a_failed_second_message_mentions_only_those_still_waiting(store: EventStore) -> None:
    channel = FakeChannel(fail_on=2)
    cog = _events_cog(store, channel)
    event = _event(store)
    users = list(range(10**17, 10**17 + 100))
    for user in users:
        store.sign_up(event.id, user, GOING, NOW)

    await cog._remind(store.get(event.id), NOW + 3000)
    assert store.get(event.id).status == OPEN
    await cog._remind(store.get(event.id), NOW + 3100)

    mentioned = [user for content, _ in channel.sent for user in users if f"<@{user}>" in content]
    assert sorted(mentioned) == users  # everyone exactly once
    assert store.get(event.id).status == REMINDED


@pytest.mark.asyncio
async def test_a_food_search_without_results_never_pings_the_keyword() -> None:
    class Provider:
        async def async_search_list(self, keyword: str, lang: str) -> list:
            return []

    search = SimpleNamespace(
        db=SimpleNamespace(), provider=Provider(),
        recommender=SimpleNamespace(rank_candidates=lambda guild, found: found),
    )
    cog = WheelCog(SimpleNamespace(get_cog=lambda name: search, rate_limiter=None))
    cog.lang_manager = FakeLang()
    interaction = FakeInteraction()

    await WheelCog.food.callback(cog, interaction, "<@123>")

    assert "<@123>" in interaction.edits[-1]["content"]
    assert interaction.edits[-1]["allowed_mentions"].users is False


@pytest.mark.asyncio
@pytest.mark.parametrize("summaries", [[], ["勇者進了洞窟。"]])
async def test_recap_is_refused_to_members_who_cannot_read_the_history(summaries: list) -> None:
    cog = _story_cog(_instance(summaries=summaries), orchestrator=object())
    interaction = FakeInteraction(user_id=5)
    interaction.channel.history_readers = {6}

    await StoryManagerCog.recap.callback(cog, interaction)

    assert interaction.sent[0][0] == "recap_no_history|" and interaction.followups == []


@pytest.mark.asyncio
async def test_no_daily_recap_where_members_cannot_read_the_history(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_write(*args: Any) -> str:
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", fake_write)
    cog = _story_cog(_instance(), orchestrator=object())
    channel = FakeChannel()
    channel.history_readers = {5}  # not @everyone
    message = SimpleNamespace(
        guild=SimpleNamespace(id=GUILD_ID, default_role=SimpleNamespace(id=GUILD_ID)), channel=channel, author=SimpleNamespace(id=5)
    )
    cog.recap_store.set_active_day(500, "2026-10-25")
    cog._today = lambda: "2026-10-26"

    await cog.maybe_post_daily_recap(message)

    assert channel.sent == [] and cog.recap_store.last_active_day(500) == "2026-10-26"


@pytest.mark.asyncio
async def test_a_card_never_shares_the_channel_image_history() -> None:
    from cogs.gen_img import ImageGenerationCog

    class Images:
        conversation_history: dict = {}
        _get_conversation_history = ImageGenerationCog._get_conversation_history
        _update_conversation_history = ImageGenerationCog._update_conversation_history

        def __init__(self) -> None:
            self.conversation_history = {500: [{"role": "user", "content": "earlier public request"}]}
            self.seen: list = []

        async def _generate_image_logic(self, prompt: str, guild_id: str, channel_id: Any) -> dict:
            self.seen.append(list(self._get_conversation_history(channel_id)))
            self._update_conversation_history(channel_id, "user", prompt)
            return {"attachments": [{"data_base64": base64.b64encode(b"png").decode()}]}

    images = Images()
    characters = {"c2": _character(character_id="c2", name="影", description="秘密身分", is_public=False)}
    cog = _story_cog(characters=characters, cogs={"ImageGenerationCog": images}, rate_limiter=None)

    await StoryManagerCog.card.callback(cog, FakeInteraction(user_id=5), "c2")

    assert images.seen == [[]]  # the card did not see the channel's earlier requests
    assert images.conversation_history == {500: [{"role": "user", "content": "earlier public request"}]}


def test_the_recap_input_stays_within_its_budget() -> None:
    from llm import story_recap_writer

    captured: list = []

    async def fake_ask(orchestrator, guild_id, prompt, purpose, charge):
        captured.append(prompt[1].content)
        return "ok"

    original = story_recap_writer._ask
    story_recap_writer._ask = fake_ask
    try:
        asyncio.run(story_recap_writer.write_recap(None, "1", "English", ["s" * 6100], ["line " + "x" * 395] * 40))
    finally:
        story_recap_writer._ask = original

    text = captured[0]
    assert len(text) <= story_recap_writer.MAX_INPUT_CHARS  # headings and delimiters included
    assert "Latest messages:" in text and text.rstrip(">").endswith("x")  # the newest lines are kept


def _private_thread() -> Any:
    """A private thread under a readable parent, with only member 1 in it."""
    return SimpleNamespace(
        id=600, type=discord.ChannelType.private_thread, members=[SimpleNamespace(id=1)], owner_id=1,
        permissions_for=lambda member: SimpleNamespace(view_channel=True, read_message_history=True, manage_threads=False),
    )


@pytest.mark.asyncio
async def test_an_event_manager_who_cannot_see_the_thread_cannot_cancel_or_learn_its_title(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    hidden_id = store.add(GUILD_ID, 600, 1, "秘密聚會", NOW + 3600, 0, 15, NOW)
    store.set_message(hidden_id, 6000)
    thread = _private_thread()

    manager = FakeInteraction(user_id=9, permissions=SimpleNamespace(manage_events=True))
    manager.guild = FakeGuild(lambda cid: thread, manager.user)
    await EventsCog.cancel.callback(cog, manager, hidden_id)

    assert manager.sent[0][0] == "not_found|" and store.get(hidden_id).status == OPEN

    host = FakeInteraction(user_id=1)
    host.guild = FakeGuild(lambda cid: thread, host.user)
    await EventsCog.cancel.callback(cog, host, hidden_id)
    assert store.get(hidden_id).status == CANCELLED


@pytest.mark.asyncio
async def test_reminders_and_promotions_leave_the_title_out_where_viewers_cannot_read_the_history(store: EventStore) -> None:
    channel = FakeChannel()
    channel.history_readers = {1, 2, 3}  # members 4–9 see new messages only
    cog = _events_cog(store, channel)
    event = _event(store, capacity=1)
    store.sign_up(event.id, 1, GOING, NOW)
    store.sign_up(event.id, 2, GOING, NOW)

    await cog._remind(store.get(event.id), NOW + 3000)
    content, _ = channel.sent[-1]
    assert "Valorant" not in content and f"untitled_event|id={event.id}" in content

    leaving = FakeInteraction(user_id=1, message=SimpleNamespace(id=event.message_id))
    leaving.channel = channel
    await cog.answer(leaving, None)
    content, _ = channel.sent[-1]
    assert "<@2>" in content and "Valorant" not in content

    channel.history_readers = None
    await cog._announce_promotion(channel, store.get(event.id), [2])
    assert "title=Valorant 五排" in channel.sent[-1][0]


@pytest.mark.asyncio
async def test_a_recap_is_shown_only_to_the_requester_when_a_role_cannot_read_the_history(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_write(*args: Any) -> str:
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", fake_write)
    cog = _story_cog(_instance(), orchestrator=object())
    interaction = FakeInteraction(user_id=5)
    interaction.channel.history_readers = {1, 2, 3, 4, 5}  # a role denies history to 6–9

    await StoryManagerCog.recap.callback(cog, interaction)

    assert interaction.deferred == {"ephemeral": True}
    assert interaction.followups[0]["ephemeral"] is True and interaction.followups[0]["embed"].description == "recap"

    public = FakeInteraction(user_id=5)
    await StoryManagerCog.recap.callback(cog, public)
    assert public.deferred == {"ephemeral": False}


@pytest.mark.asyncio
async def test_a_role_restricted_story_channel_gets_no_public_daily_recap(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_write(*args: Any) -> str:
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", fake_write)
    cog = _story_cog(_instance(), orchestrator=object())
    channel = FakeChannel()
    channel.viewer_ids = {1, 5, 6}  # @everyone cannot see it; the Players role can, with history
    message = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), channel=channel, author=SimpleNamespace(id=5))
    cog.recap_store.set_active_day(500, "2026-10-25")
    cog._today = lambda: "2026-10-26"

    await cog.maybe_post_daily_recap(message)

    # Decided from the channel's permissions alone, which err towards not posting.
    assert channel.sent == []


def test_a_database_from_an_earlier_schema_still_opens_and_reminds(tmp_path: Any) -> None:
    import sqlite3

    path = tmp_path / "events.db"
    old = sqlite3.connect(path)
    old.executescript(
        """
        CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL,
            message_id INTEGER, creator_id INTEGER NOT NULL, title TEXT NOT NULL, starts_at REAL NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 0, remind_minutes INTEGER NOT NULL DEFAULT 15,
            status TEXT NOT NULL DEFAULT 'open', attempts INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL);
        CREATE TABLE event_signups (event_id INTEGER NOT NULL, user_id INTEGER NOT NULL, status TEXT NOT NULL,
            joined_at REAL NOT NULL, seq INTEGER NOT NULL, PRIMARY KEY (event_id, user_id));
        """
    )
    old.close()

    store = EventStore(path)
    event = _event(store)
    store.sign_up(event.id, 1, GOING, NOW)
    store.mark_users_reminded(event.id, [1])

    assert store.reminded_users(event.id) == [1]
    assert [e.id for e in store.due_reminders(NOW + 3000)] == [event.id]


@pytest.mark.asyncio
async def test_leaving_and_rejoining_between_reminder_messages_does_not_repeat_the_mention(store: EventStore) -> None:
    channel = FakeChannel(fail_on=2)
    cog = _events_cog(store, channel)
    event = _event(store)
    users = list(range(10**17, 10**17 + 100))
    for user in users:
        store.sign_up(event.id, user, GOING, NOW)

    await cog._remind(store.get(event.id), NOW + 3000)
    first = users[0]
    store.leave(event.id, first)
    store.sign_up(event.id, first, GOING, NOW)
    await cog._remind(store.get(event.id), NOW + 3100)

    assert sum(content.count(f"<@{first}>") for content, _ in channel.sent) == 1


@pytest.mark.asyncio
async def test_a_press_is_acknowledged_before_waiting_behind_a_slow_reminder(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)
    interaction = FakeInteraction(user_id=3, message=SimpleNamespace(id=event.message_id))

    async with cog._lock(event.id):  # e.g. a reminder in the middle of a slow send
        press = asyncio.create_task(cog.answer(interaction, GOING))
        await asyncio.sleep(0)
        assert interaction.deferred == {}  # acknowledged while still waiting
    await press
    assert store.roster(store.get(event.id)).going == [3]


@pytest.mark.asyncio
async def test_a_join_queued_across_the_start_time_is_refused(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store, starts_in=5)
    interaction = FakeInteraction(user_id=3, message=SimpleNamespace(id=event.message_id))

    async with cog._lock(event.id):
        press = asyncio.create_task(cog.answer(interaction, GOING))
        await asyncio.sleep(0)
        cog._now = lambda: NOW + 10  # the start passes while the press waits
    await press

    assert interaction.followups[0]["content"] == "event_started|"
    assert store.roster(store.get(event.id)).going == []


@pytest.mark.asyncio
async def test_a_failed_message_edit_still_confirms_and_announces_the_promotion(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store, capacity=1)
    store.sign_up(event.id, 1, GOING, NOW)
    store.sign_up(event.id, 2, GOING, NOW)
    leaving = FakeInteraction(user_id=1, message=SimpleNamespace(id=event.message_id))
    leaving.channel = channel

    async def broken_edit(**kwargs: Any) -> None:
        raise discord.HTTPException(SimpleNamespace(status=500, reason="boom"), "boom")

    leaving.edit_original_response = broken_edit
    await cog.answer(leaving, None)

    assert leaving.followups[-1]["content"] == "you_left|"
    assert "<@2>" in channel.sent[-1][0]


@pytest.mark.asyncio
async def test_reminders_wait_for_the_bot_to_be_ready(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    ready = asyncio.Event()
    cog.bot.wait_until_ready = ready.wait
    rounds: list = []

    async def deliver(now: float) -> None:
        rounds.append(now)

    cog._deliver_due = deliver
    cog._wake = asyncio.Event()
    task = asyncio.create_task(cog._run_scheduler())
    await asyncio.sleep(0.01)
    assert rounds == []
    ready.set()
    await asyncio.sleep(0.01)
    assert rounds
    task.cancel()


@pytest.mark.asyncio
async def test_an_uncached_channel_is_fetched_and_only_a_deleted_one_ends_the_reminder(store: EventStore) -> None:
    archived = FakeChannel(channel_id=700)
    cog = _events_cog(store, FakeChannel())
    fetches: list = []

    async def fetch_channel(channel_id: int) -> Any:
        fetches.append(channel_id)
        if channel_id == 700:
            return archived
        if channel_id == 701:
            raise discord.HTTPException(SimpleNamespace(status=503, reason="down"), "down")
        raise discord.NotFound(SimpleNamespace(status=404, reason="gone"), "gone")

    cog.bot.fetch_channel = fetch_channel
    events = {}
    for channel_id in (700, 701, 702):
        event_id = store.add(GUILD_ID, channel_id, 1, "x", NOW + 3600, 0, 15, NOW)
        store.set_message(event_id, 9000 + channel_id)
        store.sign_up(event_id, 1, GOING, NOW)
        events[channel_id] = event_id
        await cog._remind(store.get(event_id), NOW + 3000)

    assert fetches == [700, 701, 702]
    assert "<@1>" in archived.sent[0][0] and store.get(events[700]).status == REMINDED
    assert store.get(events[701]).status == OPEN and store.get(events[701]).attempts == 1
    assert store.get(events[702]).status == REMINDED and store.get(events[702]).attempts == 0


def test_reminders_recorded_on_sign_ups_by_an_earlier_version_are_kept(tmp_path: Any) -> None:
    import sqlite3

    path = tmp_path / "events.db"
    old = sqlite3.connect(path)
    old.executescript(
        """
        CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, channel_id INTEGER NOT NULL,
            message_id INTEGER, creator_id INTEGER NOT NULL, title TEXT NOT NULL, starts_at REAL NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 0, remind_minutes INTEGER NOT NULL DEFAULT 15,
            status TEXT NOT NULL DEFAULT 'open', attempts INTEGER NOT NULL DEFAULT 0, next_try_at REAL, created_at REAL NOT NULL);
        CREATE TABLE event_signups (event_id INTEGER NOT NULL, user_id INTEGER NOT NULL, status TEXT NOT NULL,
            joined_at REAL NOT NULL, seq INTEGER NOT NULL, reminded INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (event_id, user_id));
        INSERT INTO events (id, guild_id, channel_id, message_id, creator_id, title, starts_at, created_at)
            VALUES (1, 42, 500, 1001, 1, 'x', 1800003600, 1800000000);
        INSERT INTO event_signups VALUES (1, 1, 'going', 0, 1, 1), (1, 2, 'going', 0, 2, 0);
        """
    )
    old.commit()
    old.close()

    assert EventStore(path).reminded_users(1) == [1]



@pytest.mark.asyncio
async def test_a_permission_change_during_the_recap_keeps_it_private(monkeypatch: pytest.MonkeyPatch) -> None:
    channel_holder: list = []

    async def slow_write(*args: Any) -> str:
        channel_holder[0].history_readers = {1, 2, 3, 4, 5}  # a role loses history meanwhile
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", slow_write)
    cog = _story_cog(_instance(), orchestrator=object())
    interaction = FakeInteraction(user_id=5)
    channel_holder.append(interaction.channel)

    await StoryManagerCog.recap.callback(cog, interaction)

    assert interaction.deferred == {"ephemeral": False}
    assert interaction.followups[0]["content"] == "recap_sent_privately|"
    assert interaction.followups[1]["ephemeral"] is True and interaction.followups[1]["embed"].description == "recap"

    daily = FakeChannel()
    channel_holder[0] = daily
    message = SimpleNamespace(guild=SimpleNamespace(id=GUILD_ID), channel=daily, author=SimpleNamespace(id=5))
    cog.recap_store.set_active_day(500, "2026-10-25")
    cog._today = lambda: "2026-10-26"
    await cog.maybe_post_daily_recap(message)
    assert daily.sent == []


@pytest.mark.asyncio
async def test_cancel_is_acknowledged_before_waiting_for_the_event(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)
    host = FakeInteraction(user_id=1)

    async with cog._lock(event.id):
        task = asyncio.create_task(EventsCog.cancel.callback(cog, host, event.id))
        await asyncio.sleep(0)
        assert host.deferred == {"ephemeral": True}
    await task

    assert store.get(event.id).status == CANCELLED
    assert host.followups[0]["content"].startswith("cancelled|")


@pytest.mark.asyncio
async def test_a_role_taken_away_during_the_recap_is_noticed_although_the_interaction_is_older(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changes: list = []

    async def slow_write(*args: Any) -> str:
        changes.pop(0)()
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", slow_write)
    cog = _story_cog(_instance(), orchestrator=object())

    # The member cache now has the member without the role; the interaction still shows them with it.
    interaction = FakeInteraction(user_id=5)
    changes.append(lambda: interaction.guild.members.__setitem__(5, SimpleNamespace(id=5, lost_access=True)))
    await StoryManagerCog.recap.callback(cog, interaction)
    assert [followup["content"] for followup in interaction.followups] == ["recap_no_history|"]

    # A member who left meanwhile (not cached, cannot be fetched) counts as unable to read.
    gone = FakeInteraction(user_id=5)
    changes.append(gone.guild.members.clear)
    await StoryManagerCog.recap.callback(cog, gone)
    assert gone.guild.fetched == [5]
    assert [followup["content"] for followup in gone.followups] == ["recap_no_history|"]


@pytest.mark.asyncio
async def test_a_cancel_waiting_for_the_event_checks_access_again(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store)
    host = FakeInteraction(user_id=1)
    host.channel = channel

    async with cog._lock(event.id):
        task = asyncio.create_task(EventsCog.cancel.callback(cog, host, event.id))
        await asyncio.sleep(0)
        channel.viewer_ids = {2, 3}  # the host loses the channel meanwhile
    await task

    assert store.get(event.id).status == OPEN
    assert [followup["content"] for followup in host.followups] == ["not_found|"]


@pytest.mark.asyncio
async def test_two_cancels_at_once_cancel_once(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)
    first = FakeInteraction(user_id=1)
    second = FakeInteraction(user_id=9, permissions=SimpleNamespace(manage_events=True))
    second.channel = first.channel
    first.channel.managers = {9}

    async with cog._lock(event.id):
        tasks = [asyncio.create_task(EventsCog.cancel.callback(cog, who, event.id)) for who in (first, second)]
        await asyncio.sleep(0)
    await asyncio.gather(*tasks)

    replies = sorted(who.followups[0]["content"].split("|")[0] for who in (first, second))
    assert replies == ["already_cancelled", "cancelled"]
    assert store.get(event.id).status == CANCELLED


@pytest.mark.asyncio
async def test_each_reminder_message_checks_again_whether_the_title_may_be_shown(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store)
    users = [10**17 + number for number in range(150)]
    for user_id in users:
        store.sign_up(event.id, user_id, GOING, NOW)
    send = channel.send

    async def send_then_restrict(content: Any = None, **kwargs: Any) -> Any:
        sent = await send(content, **kwargs)
        channel.history_readers = {1}  # a role loses the history after the first message
        return sent

    channel.send = send_then_restrict
    await cog._remind(store.get(event.id), NOW + 3000)

    assert len(channel.sent) >= 2
    assert "Valorant" in channel.sent[0][0]
    for content, _ in channel.sent[1:]:
        assert "Valorant" not in content and f"untitled_event|id={event.id}" in content
        assert len(content) <= 2000
    mentioned = [user.id for _, kwargs in channel.sent for user in kwargs["allowed_mentions"].users]
    assert mentioned == users
    assert store.get(event.id).status == REMINDED


@pytest.mark.asyncio
async def test_the_recap_is_checked_again_after_the_note_that_it_went_private(monkeypatch: pytest.MonkeyPatch) -> None:
    holder: list = []

    async def slow_write(*args: Any) -> str:
        holder[0].channel.history_readers = {1, 2, 3, 4, 5}  # the audience shrinks: the note will be sent
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", slow_write)
    cog = _story_cog(_instance(), orchestrator=object())
    interaction = FakeInteraction(user_id=5)
    holder.append(interaction)
    note = interaction._followup

    async def note_then_lose_role(content: Any = None, **kwargs: Any) -> None:
        await note(content, **kwargs)
        # The requester's role is taken away while the note is being sent.
        interaction.guild.members[5] = SimpleNamespace(id=5, lost_access=True)

    interaction.followup.send = note_then_lose_role
    await StoryManagerCog.recap.callback(cog, interaction)

    assert [followup["content"] for followup in interaction.followups] == ["recap_sent_privately|", "recap_no_history|"]
    assert all("embed" not in followup for followup in interaction.followups)


class FailingLookupGuild(FakeGuild):
    def __init__(self, get_channel_or_thread: Any, error: Exception) -> None:
        super().__init__(get_channel_or_thread)
        self.error = error

    async def fetch_member(self, user_id: int) -> Any:
        self.fetched.append(user_id)
        raise self.error


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [404, 500])
async def test_a_cancel_by_a_member_who_cannot_be_looked_up_is_refused(store: EventStore, status: int) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)
    host = FakeInteraction(user_id=1)
    response = SimpleNamespace(status=status, reason="boom")
    error = discord.NotFound(response, "gone") if status == 404 else discord.HTTPException(response, "boom")
    # The host left while the cancel was acknowledged: not in the cache, and the lookup fails.
    host.guild = FailingLookupGuild(host.guild.get_channel_or_thread, error)

    await EventsCog.cancel.callback(cog, host, event.id)

    assert host.guild.fetched == [1]
    assert store.get(event.id).status == OPEN
    assert [followup["content"] for followup in host.followups] == ["not_found|"]


@pytest.mark.asyncio
async def test_a_manager_who_loses_manage_events_while_waiting_cannot_cancel(store: EventStore) -> None:
    cog = _events_cog(store, FakeChannel())
    event = _event(store)  # hosted by member 1
    manager = FakeInteraction(user_id=9, permissions=SimpleNamespace(manage_events=True))
    manager.channel.managers = {9}

    async with cog._lock(event.id):
        task = asyncio.create_task(EventsCog.cancel.callback(cog, manager, event.id))
        await asyncio.sleep(0)
        manager.channel.managers = set()  # the management role is taken away; the channel stays readable
    await task

    assert store.get(event.id).status == OPEN
    assert [followup["content"] for followup in manager.followups] == ["not_yours|"]


@pytest.mark.asyncio
async def test_the_cancel_confirmation_leaves_the_title_out_when_access_ends_during_the_edit(store: EventStore) -> None:
    channel = FakeChannel()
    cog = _events_cog(store, channel)
    event = _event(store)
    host = FakeInteraction(user_id=1)
    host.channel = channel
    refresh = cog._refresh_message

    async def refresh_then_revoke(event: Any) -> None:
        await refresh(event)
        channel.viewer_ids = {2, 3}  # the host loses the channel during the edit

    cog._refresh_message = refresh_then_revoke
    await EventsCog.cancel.callback(cog, host, event.id)

    assert store.get(event.id).status == CANCELLED
    reply = host.followups[0]["content"]
    assert reply.startswith("cancelled|") and "Valorant" not in reply and f"untitled_event|id={event.id}" in reply


@pytest.mark.asyncio
async def test_the_audience_is_decided_after_the_requester_is_looked_up_again(monkeypatch: pytest.MonkeyPatch) -> None:
    async def write(*args: Any) -> str:
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", write)
    cog = _story_cog(_instance(), orchestrator=object())
    interaction = FakeInteraction(user_id=5)
    channel = interaction.channel

    class SlowLookupGuild(FakeGuild):
        async def fetch_member(self, user_id: int) -> Any:
            # While the requester (not cached) is fetched, the channel stops showing @everyone its history.
            channel.history_readers = {5}
            return SimpleNamespace(id=user_id)

    interaction.guild = SlowLookupGuild(interaction.guild.get_channel_or_thread)
    await StoryManagerCog.recap.callback(cog, interaction)

    assert interaction.deferred == {"ephemeral": False}
    public = [followup for followup in interaction.followups if not followup.get("ephemeral")]
    assert [followup["content"] for followup in public] == ["recap_sent_privately|"]
    assert interaction.followups[-1]["embed"].description == "recap" and interaction.followups[-1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_ending_a_story_forgets_its_pending_rolls() -> None:
    from cogs.story.ui import views

    saved: list = []
    manager = SimpleNamespace(
        language_manager=FakeLang(), character_db=SimpleNamespace(), interventions={}, bot=SimpleNamespace(),
        dice_results={500: ["left over"], 501: ["elsewhere"]}, dice_generation={},
        _get_db=lambda guild_id: SimpleNamespace(save_story_instance=saved.append),
    )
    manager.clear_dice_results = lambda channel_id: StoryManager.clear_dice_results(manager, channel_id)
    instance = SimpleNamespace(
        guild_id=GUILD_ID, channel_id=500, is_active=True, narration_enabled=True, active_character_ids=[], world_name="w"
    )
    view = views.ActiveStoryView(manager=manager, story_instance=instance)

    async def is_admin(interaction: Any) -> bool:
        return True

    interaction = FakeInteraction(user_id=1)
    interaction.client = SimpleNamespace(get_cog=lambda name: SimpleNamespace(check_admin_permissions=is_admin))
    await view.end_story_button.callback(interaction)

    assert saved == [instance] and instance.is_active is False
    assert manager.dice_results == {501: ["elsewhere"]}



class _NoTyping:
    def __init__(self, channel: Any) -> None:
        pass

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *exc: Any) -> None:
        return None


def _scratch_dir() -> str:
    import tempfile

    return tempfile.mkdtemp(prefix="story-test-")


def _real_story_manager(monkeypatch: pytest.MonkeyPatch, plan: Any) -> tuple:
    """A real StoryManager and prompt builder whose GM turn stops at the plan.

    ``plan`` is what the model returns, an exception it raises, or an async function giving either.
    Returns the manager and the dice part of every GM prompt built (None when it had no rolls).
    """
    import cogs.story.manager as story_module

    prompts: list = []

    class Agent:
        async def ainvoke(self, payload: Any) -> Any:
            outcome = await plan() if callable(plan) else plan
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    def create_agent(model: Any, tools: Any, system_prompt: str, **kwargs: Any) -> Agent:
        dice_part = system_prompt.split("## Dice Rolls", 1)[1].split("##", 1)[0] if "## Dice Rolls" in system_prompt else None
        prompts.append([line[2:] for line in dice_part.splitlines() if line.startswith("- ")] if dice_part else None)
        return Agent()

    monkeypatch.setitem(story_module.__dict__, "SafeTyping", _NoTyping)
    monkeypatch.setitem(story_module.__dict__, "ModelManager", lambda: SimpleNamespace(get_model=lambda *a, **k: ("m", None)))
    monkeypatch.setitem(story_module.__dict__, "create_model_instance", lambda *a, **k: object())
    monkeypatch.setitem(story_module.__dict__, "create_agent", create_agent)
    monkeypatch.setattr(story_module.func, "report_error", lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(story_module, "ROLL_REPLY_WAIT_SECONDS", 0.5)

    instance = SimpleNamespace(
        guild_id=GUILD_ID, channel_id=500, is_active=True, world_name="w", active_character_ids=[], outlines=[], summaries=[],
        current_location="洞窟", current_date="day 1", current_time="night", narration_enabled=True,
    )
    db = SimpleNamespace(
        get_story_instance=lambda channel_id: instance, get_world=lambda name: SimpleNamespace(world_name=name, locations=[])
    )
    # Built the way the bot builds it (its databases under a temporary folder), then pointed at the fakes.
    monkeypatch.chdir(_scratch_dir())
    manager = StoryManager(
        SimpleNamespace(user=SimpleNamespace(id=1), get_cog=lambda name: None),
        object(),
        SimpleNamespace(get_effective_full_prompt=lambda *a: "base prompt"),
    )
    manager._initialized = True
    manager._get_db = lambda guild_id: db
    manager.character_db = SimpleNamespace(get_character=lambda character_id: None)
    manager.language_manager = FakeLang()
    manager.logger = SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
    manager._extract_structured_response = lambda response, model, name: response
    return manager, prompts


def _story_message(replies: list) -> Any:
    async def reply(content: Any = None, **kwargs: Any) -> None:
        replies.append(content)

    return SimpleNamespace(
        guild=SimpleNamespace(id=GUILD_ID), channel=SimpleNamespace(id=500), content="我撬鎖", reply=reply,
    )


def _pending(manager: Any) -> List[str]:
    return [roll.text for roll in manager.dice_results.get(500, [])]


@pytest.mark.asyncio
@pytest.mark.parametrize("plan", [RuntimeError("model down"), None])
async def test_a_failed_gm_turn_keeps_the_rolls_for_the_next_one(monkeypatch: pytest.MonkeyPatch, plan: Any) -> None:
    manager, prompts = _real_story_manager(monkeypatch, plan)
    manager.add_dice_result(500, "a rolled 3")
    replies: list = []

    await manager.process_story_message(_story_message(replies))
    manager.add_dice_result(500, "b rolled 18")

    assert prompts == [["a rolled 3"]] and len(replies) == 1
    assert _pending(manager) == ["a rolled 3", "b rolled 18"]


@pytest.mark.asyncio
async def test_a_turn_uses_a_roll_only_once_its_reply_went_out(monkeypatch: pytest.MonkeyPatch) -> None:
    manager, prompts = _real_story_manager(monkeypatch, None)
    cog = _story_cog(_instance())
    cog.story_manager = manager
    real_roll = dice.roll
    monkeypatch.setattr(dice, "roll", lambda notation: real_roll(notation, random.Random(7)))  # the same roll every time
    replies: list = []
    turns: list = []

    def reply_while_a_turn_starts(fails: bool) -> Any:
        async def send(content: Any = None, **kwargs: Any) -> None:
            # A player's message is handled while this reply is on its way.
            turns.append(asyncio.create_task(manager.process_story_message(_story_message(replies))))
            await asyncio.sleep(0.01)
            if fails:
                raise discord.HTTPException(SimpleNamespace(status=500, reason="boom"), "boom")

        return send

    shown = FakeInteraction(user_id=5)
    shown.response.send_message = reply_while_a_turn_starts(False)
    await StoryManagerCog.roll.callback(cog, shown, "1d20", None)
    await turns[-1]
    assert len(prompts[-1]) == 1 and prompts[-1][0].startswith("user5 rolled")

    # (That turn came to nothing, so the roll waits for the next one.) The same roll again, but its
    # reply fails: the turn that waited for it goes on with the first roll only.
    first = prompts[-1][0]
    unseen = FakeInteraction(user_id=5)
    unseen.response.send_message = reply_while_a_turn_starts(True)
    with pytest.raises(discord.HTTPException):
        await StoryManagerCog.roll.callback(cog, unseen, "1d20", None)
    await turns[-1]
    assert prompts[-1] == [first] and _pending(manager) == [first]


@pytest.mark.asyncio
async def test_rolls_of_an_ended_story_do_not_come_back_when_its_turn_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    holder: list = []

    async def story_ends_meanwhile() -> Exception:
        holder[0].clear_dice_results(500)  # the end-story button (or a new story) while the model runs
        return RuntimeError("model down")

    manager, prompts = _real_story_manager(monkeypatch, story_ends_meanwhile)
    holder.append(manager)
    manager.add_dice_result(500, "a rolled 3")

    await manager.process_story_message(_story_message([]))

    assert prompts == [["a rolled 3"]] and _pending(manager) == []


@pytest.mark.asyncio
async def test_two_failed_turns_put_their_rolls_back_in_the_order_they_were_rolled(monkeypatch: pytest.MonkeyPatch) -> None:
    gates = [asyncio.Event(), asyncio.Event()]
    calls: list = []

    async def wait_then_fail() -> Exception:
        gate = gates[len(calls)]
        calls.append(gate)
        await gate.wait()
        return RuntimeError("model down")

    manager, prompts = _real_story_manager(monkeypatch, wait_then_fail)
    for number in range(MAX_PENDING_DICE):
        manager.add_dice_result(500, f"A{number}")
    first = asyncio.create_task(manager.process_story_message(_story_message([])))
    while not calls:
        await asyncio.sleep(0)
    for number in range(MAX_PENDING_DICE):
        manager.add_dice_result(500, f"B{number}")
    second = asyncio.create_task(manager.process_story_message(_story_message([])))
    while len(calls) < 2:
        await asyncio.sleep(0)

    gates[0].set()  # the older turn fails first
    await first
    gates[1].set()
    await second

    assert _pending(manager) == [f"B{number}" for number in range(MAX_PENDING_DICE)]


@pytest.mark.asyncio
async def test_starting_a_story_forgets_the_rolls_made_before_it(monkeypatch: pytest.MonkeyPatch) -> None:
    manager, prompts = _real_story_manager(monkeypatch, None)
    manager.add_dice_result(500, "left over")
    edits: list = []

    async def edit_original_response(**kwargs: Any) -> None:
        edits.append(kwargs)

    manager._get_db = lambda guild_id: SimpleNamespace(get_world=lambda name: None)  # stops right after the cleanup
    interaction = SimpleNamespace(guild_id=GUILD_ID, channel_id=500, edit_original_response=edit_original_response)
    await manager.start_story(interaction, "w", [], True, None, None, "洞窟")

    assert _pending(manager) == [] and edits


@pytest.mark.asyncio
async def test_an_event_whose_message_cannot_be_found_is_taken_back(store: EventStore) -> None:
    from datetime import datetime

    cog = _events_cog(store, FakeChannel())
    cog.parse_time = lambda text: datetime.fromtimestamp(NOW + float(text))
    interaction = FakeInteraction(user_id=1)

    async def posted(**kwargs: Any) -> Any:
        return SimpleNamespace(message_id=4242)

    interaction.response.send_message = posted
    await EventsCog.create.callback(cog, interaction, "Valorant 五排", "7200", 0, 15)
    assert store.by_message(4242) is not None

    lost = FakeInteraction(user_id=2)

    async def posted_without_id(**kwargs: Any) -> Any:
        return None

    async def lookup_fails() -> Any:
        raise discord.HTTPException(SimpleNamespace(status=500, reason="boom"), "boom")

    deleted: list = []

    async def delete_original_response() -> None:
        deleted.append(True)

    lost.response.send_message = posted_without_id
    lost.original_response = lookup_fails
    lost.delete_original_response = delete_original_response
    await EventsCog.create.callback(cog, lost, "Apex", "10800", 0, 15)
    # Its buttons and reminder could never work: the post is removed and the host asked to try again.
    assert [event.title for event in store.upcoming(GUILD_ID, NOW)] == ["Valorant 五排"]
    assert deleted == [True] and lost.followups[0]["content"] == "post_failed|"


@pytest.mark.asyncio
async def test_the_recap_includes_what_story_characters_said_through_their_webhooks(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list = []

    async def write(orchestrator: Any, guild_id: str, language: str, summaries: Any, lines: Any, charge: Any) -> str:
        captured.extend(lines)
        return "recap"

    monkeypatch.setitem(StoryManagerCog._recap_text.__globals__, "write_recap", write)
    king = SimpleNamespace(webhook_url="https://discord.com/api/webhooks/777/token")
    cog = _story_cog(_instance(active_character_ids=["king"]), characters={"king": king}, orchestrator=object())
    channel = FakeChannel()

    def message(author: str, author_id: int, content: str = "", embed: Optional[str] = None, webhook_id: Any = None) -> Any:
        embeds = [SimpleNamespace(description=embed)] if embed else []
        return SimpleNamespace(
            author=SimpleNamespace(id=author_id, display_name=author), content=content, embeds=embeds, webhook_id=webhook_id
        )

    newest_first = [
        message("player", 5, "國王怎麼了？"),
        message("國王", 777, embed="國王倒下了。", webhook_id=777),
        message("other", 888, embed="無關的通知", webhook_id=888),
    ]

    async def history(limit: int, before: Any = None) -> Any:
        for item in newest_first:
            yield item

    channel.history = history
    await cog._recap_text(channel, cog.story_manager.instance, 5)
    assert captured == ["國王: 國王倒下了。", "player: 國王怎麼了？"]


@pytest.mark.asyncio
async def test_a_card_that_could_not_be_drawn_is_not_charged() -> None:
    from addons.rate_limiter import LimitRule, RateLimiter

    class NoImage(FakeImages):
        async def _generate_image_logic(self, prompt: str, guild_id: str, channel_id: int) -> dict:
            return {"attachments": []}

    limiter = RateLimiter({"image": LimitRule(max_requests=1, per_seconds=3600)})
    cog = _story_cog(characters={"c1": _character()}, cogs={"ImageGenerationCog": NoImage()}, rate_limiter=limiter)

    for _ in range(2):  # the only use in the window, given back each time
        interaction = FakeInteraction(user_id=7)
        await StoryManagerCog.card.callback(cog, interaction, "c1")
        assert interaction.followups[0]["content"] == "card_failed|"
    assert limiter.hit("image", 7) == 0


@pytest.mark.asyncio
async def test_a_reply_settled_right_as_the_wait_ends_is_used_exactly_once(monkeypatch: pytest.MonkeyPatch) -> None:
    from cogs.story.manager import PendingRoll

    manager, prompts = _real_story_manager(monkeypatch, None)
    roll = manager.add_dice_result(500, "a rolled 3", delivered=False)

    async def times_out_as_the_reply_lands(self: Any, timeout: float) -> None:
        await asyncio.sleep(0)
        manager.confirm_dice_result(roll)  # the wait gave up, but the reply went out before the turn looked

    monkeypatch.setattr(PendingRoll, "wait", times_out_as_the_reply_lands)
    assert await manager._take_dice_results(500) == [roll]
    assert _pending(manager) == []


@pytest.mark.asyncio
async def test_a_story_ending_while_a_turn_waits_for_a_roll_leaves_the_turn_without_it(monkeypatch: pytest.MonkeyPatch) -> None:
    from cogs.story.manager import PendingRoll

    manager, prompts = _real_story_manager(monkeypatch, None)
    roll = manager.add_dice_result(500, "a rolled 3", delivered=False)

    async def story_ends_then_reply_lands(self: Any, timeout: float) -> None:
        manager.clear_dice_results(500)
        manager.confirm_dice_result(roll)

    monkeypatch.setattr(PendingRoll, "wait", story_ends_then_reply_lands)
    await manager.process_story_message(_story_message([]))

    assert prompts == [None] and _pending(manager) == []


@pytest.mark.asyncio
async def test_an_announcement_that_cannot_be_removed_loses_its_buttons(store: EventStore) -> None:
    from datetime import datetime

    cog = _events_cog(store, FakeChannel())
    cog.parse_time = lambda text: datetime.fromtimestamp(NOW + float(text))
    interaction = FakeInteraction(user_id=2)

    async def posted_without_id(**kwargs: Any) -> Any:
        return None

    async def fails(*args: Any, **kwargs: Any) -> Any:
        raise discord.HTTPException(SimpleNamespace(status=500, reason="boom"), "boom")

    interaction.response.send_message = posted_without_id
    interaction.original_response = fails
    interaction.delete_original_response = fails
    await EventsCog.create.callback(cog, interaction, "Apex", "10800", 0, 15)

    assert store.upcoming(GUILD_ID, NOW) == []
    assert interaction.edits == [{"content": "post_failed|", "embed": None, "view": None}]


def test_a_refund_gives_back_exactly_the_failed_use_and_only_once() -> None:
    from addons.rate_limiter import LimitRule, RateLimiter

    now = [0.0]
    limiter = RateLimiter({"image": LimitRule(max_requests=2, per_seconds=10)}, clock=lambda: now[0])
    _, failed = limiter.take("image", 7)  # t=0, fails later
    now[0] = 9
    assert limiter.hit("image", 7) == 0  # t=9, succeeds (the existing hit() callers)
    now[0] = 9.5
    limiter.refund(failed)
    limiter.refund(failed)  # a second refund changes nothing

    assert limiter.hit("image", 7) == 0  # the failed use's place
    assert limiter.hit("image", 7) > 0  # but the t=9 use still counts
    now[0] = 30
    assert limiter.hit("image", 7) == 0 and limiter.hit("image", 7) == 0 and limiter.hit("image", 7) > 0


@pytest.mark.asyncio
async def test_a_card_whose_reply_cannot_be_acknowledged_is_not_charged() -> None:
    from addons.rate_limiter import LimitRule, RateLimiter

    limiter = RateLimiter({"image": LimitRule(max_requests=1, per_seconds=3600)})
    cog = _story_cog(characters={"c1": _character()}, cogs={"ImageGenerationCog": FakeImages()}, rate_limiter=limiter)
    interaction = FakeInteraction(user_id=7)

    async def fail(**kwargs: Any) -> None:
        raise discord.HTTPException(SimpleNamespace(status=500, reason="boom"), "boom")

    interaction.response.defer = fail
    with pytest.raises(discord.HTTPException):
        await StoryManagerCog.card.callback(cog, interaction, "c1")
    assert limiter.hit("image", 7) == 0
