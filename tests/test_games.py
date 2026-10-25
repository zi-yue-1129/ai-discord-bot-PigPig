"""The server quiz: grounded questions from episodic memories, scoring, and game points."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional

import discord
import pytest

from cogs.community_lib.store import CommunityStore
from cogs.games import GamesCog
from cogs.games_lib.quiz import BASE_POINTS, QuizQuestion, QuizRound, QuizScoreboard, parse_question, points_for, usable_memory

ROOT = Path(__file__).resolve().parents[1]
GUILD_ID = 42
MEMORY = "小明在 #美食 推薦了一家叫做「豬豬拉麵」的店，大家約好週五晚上一起去吃。"
META = {"channel_id": "500", "start_timestamp": 1761400000.5, "jump_url": "https://discord.com/channels/42/500/1", "author_ids": ["7"]}


def _reply(**overrides: Any) -> str:
    data = {"question": "小明推薦了哪家店？", "options": ["豬豬拉麵", "牛牛火鍋", "雞雞咖哩", "羊羊壽司"], "answer": 0}
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


# ------------------------------------------------------------------ questions


def test_a_grounded_question_keeps_its_source() -> None:
    question = parse_question("```json\n" + _reply() + "\n```", MEMORY, META)

    assert question == QuizQuestion(
        question="小明推薦了哪家店？",
        options=["豬豬拉麵", "牛牛火鍋", "雞雞咖哩", "羊羊壽司"],
        answer=0,
        channel_id="500",
        timestamp=1761400000.5,
        jump_url="https://discord.com/channels/42/500/1",
    )


@pytest.mark.parametrize(
    "reply",
    [
        _reply(answer=1),  # the marked answer is not in the memory: made up
        _reply(options=["豬豬拉麵", "牛牛火鍋", "雞雞咖哩"]),
        _reply(options=["豬豬拉麵", "豬豬 拉麵", "雞雞咖哩", "羊羊壽司"]),  # duplicates
        _reply(options=["豬豬拉麵", "", "雞雞咖哩", "羊羊壽司"]),
        _reply(answer=4),
        _reply(answer=True),
        _reply(question=""),
        "not json at all",
        "{broken json",
    ],
)
def test_bad_or_made_up_questions_are_dropped(reply: str) -> None:
    assert parse_question(reply, MEMORY, META) is None


def test_memories_need_text_and_a_visible_author() -> None:
    assert usable_memory(META, MEMORY, hidden=[]) is True
    assert usable_memory(META, MEMORY, hidden=[7]) is False
    assert usable_memory({"author_ids": ["7", "8"]}, MEMORY, hidden=[7]) is True
    assert usable_memory(META, "短", hidden=[]) is False


# ------------------------------------------------------------------ scoring


def test_faster_correct_answers_score_more_and_only_the_first_answer_counts() -> None:
    quiz_round = QuizRound(question=QuizQuestion("q", ["a", "b", "c", "d"], 2), started_at=100.0)

    assert quiz_round.answer(1, 2, 100.0) is True
    assert quiz_round.answer(2, 2, 110.0) is True
    assert quiz_round.answer(3, 0, 101.0) is True
    assert quiz_round.answer(1, 0, 102.0) is False

    assert quiz_round.points() == {1: 1000, 2: 750}
    assert points_for(30) == BASE_POINTS
    board = QuizScoreboard()
    board.add({1: 10, 2: 30})
    board.add({1: 25})
    assert board.standings() == [(1, 35), (2, 30)]


def test_game_points_are_summed_per_player_and_period(tmp_path: Path) -> None:
    store = CommunityStore(tmp_path / "community.db")
    store.add_game_scores(GUILD_ID, "quiz", {1: 500, 2: 0}, 100.0)
    store.add_game_scores(GUILD_ID, "quiz", {1: 200, 3: 900}, 200.0)
    store.add_game_scores(99, "quiz", {1: 5000}, 200.0)

    assert store.game_points(GUILD_ID) == [(3, 900), (1, 700)]
    assert store.game_points(GUILD_ID, since=150) == [(3, 900), (1, 200)]


# ------------------------------------------------------------------ cog


class FakeLang:
    def translate(self, guild_id: str, *keys: str, **kwargs: Any) -> str:
        return f"{keys[-1]}|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))


class FakeMessage:
    def __init__(self, embed: Any, view: Any) -> None:
        self.embed, self.view = embed, view
        self.edits: list = []

    async def edit(self, embed: Any = None, view: Any = None) -> None:
        self.edits.append((embed, view))


class FakeChannel:
    """Every player answers as soon as a question is posted."""

    def __init__(self, picks: dict) -> None:
        self.id = 500
        self.picks = picks
        self.sent: List[FakeMessage] = []

    async def send(self, content: Any = None, embed: Any = None, view: Any = None, allowed_mentions: Any = None) -> FakeMessage:
        message = FakeMessage(embed, view)
        if view is not None:
            for user_id, pick in self.picks.items():
                view.round.answer(user_id, pick(view.round.question), view.round.started_at + 2)
        self.sent.append(message)
        return message


class FakeVectorStore:
    def __init__(self, memories: list) -> None:
        self.memories = memories
        self.calls: list = []

    async def sample_memories(self, guild_id: str, limit: int, channel_id: Optional[str] = None, since: Optional[float] = None) -> list:
        self.calls.append((guild_id, limit, channel_id, since))
        return self.memories[:limit]


def _memory(text: str, authors: Optional[list] = None, channel_id: str = "500") -> SimpleNamespace:
    return SimpleNamespace(content=text, metadata={**META, "author_ids": authors or ["7"], "channel_id": channel_id})


class FakeTextChannel:
    def __init__(self, public: bool) -> None:
        self.public = public

    def permissions_for(self, role: Any) -> Any:
        return SimpleNamespace(view_channel=self.public, read_message_history=self.public)


class FakeGuild:
    """Channel 500 is public, 501 is restricted, 502 is where a private quiz runs."""

    id = GUILD_ID
    default_role = object()
    channels = {500: FakeTextChannel(True), 501: FakeTextChannel(False), 502: FakeTextChannel(False)}

    def get_channel_or_thread(self, channel_id: int) -> Any:
        return self.channels.get(channel_id)


@pytest.fixture
def store(tmp_path: Path) -> CommunityStore:
    return CommunityStore(tmp_path / "community.db")


@pytest.fixture
def cog(store: CommunityStore) -> GamesCog:
    memories = [
        _memory(MEMORY),
        _memory(MEMORY, ["13"]),
        _memory("太短"),
        _memory(MEMORY + "（第二次）"),
        _memory(MEMORY + "（私密頻道）", channel_id="501"),
        _memory(MEMORY + "（這裡）", channel_id="502"),
        _memory(MEMORY + "（已刪除的頻道）", channel_id="999"),
    ]
    bot = SimpleNamespace(orchestrator=object(), vector_manager=SimpleNamespace(store=FakeVectorStore(memories)))
    instance = GamesCog(bot, store=store)
    instance.lang_manager = FakeLang()
    instance.answer_seconds = 0
    instance.pause_seconds = 0
    store.set_optout(GUILD_ID, 13, True)
    return instance


@pytest.mark.asyncio
async def test_questions_come_from_usable_memories_only(cog: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list = []

    async def fake_write(orchestrator: Any, guild_id: str, memory_text: str) -> str:
        seen.append(memory_text)
        return _reply()

    monkeypatch.setitem(GamesCog.make_questions.__globals__, "write_question", fake_write)

    questions = await cog.make_questions(FakeGuild(), 7, channel_id="500", since=10.0, here=502)

    # Skipped: the hidden author's memory, the short one, and those from a restricted or unknown channel.
    assert len(questions) == 3
    assert sorted(seen) == sorted([MEMORY, MEMORY + "（第二次）", MEMORY + "（這裡）"])
    assert cog.bot.vector_manager.store.calls == [(str(GUILD_ID), 21, "500", 10.0)]


@pytest.mark.asyncio
async def test_a_quiz_shows_answers_with_sources_and_records_points(cog: GamesCog, store: CommunityStore) -> None:
    question = parse_question(_reply(), MEMORY, META)
    channel = FakeChannel({10: lambda q: q.answer, 11: lambda q: (q.answer + 1) % 4})
    guild = SimpleNamespace(id=GUILD_ID)

    board = await cog.run_quiz(channel, guild, [question, question])

    assert board.totals == {10: 2 * points_for(2)}
    first, second, final = channel.sent
    answer_embed = first.edits[0][0]
    fields = {field.name: field.value for field in answer_embed.fields}
    assert fields["result|"] == "correct_count|answered=2|count=1"
    assert fields["source|"] == "<#500> · <t:1761400000:D> · [source_link|](https://discord.com/channels/42/500/1)"
    assert fields["standings|"] == f"🥇 <@10> · {points_for(2):,}"
    assert "✅ **A.** 豬豬拉麵" in answer_embed.description
    assert first.edits[0][1] is None  # buttons removed
    assert final.embed.title == "final_title|"
    assert store.game_points(GUILD_ID) == [(10, 2 * points_for(2))]


@pytest.mark.parametrize("folder", ["en_US", "zh_TW", "zh_CN", "ja_JP"])
def test_every_language_has_the_same_game_texts(folder: str) -> None:
    def keys(lang: str) -> set:
        return set(json.loads((ROOT / "translations" / lang / "commands" / "games.json").read_text("utf-8"))["responses"])

    assert keys(folder) == keys("en_US")


# ------------------------------------------------------------------ word chain

from cogs.games_lib.chain import BOT_PLAYER, WORD_POINTS, WordChain, chains, last_char, normalise_word  # noqa: E402


def test_only_single_words_count_as_moves() -> None:
    assert normalise_word(" 蘋果 ") == "蘋果"
    assert normalise_word("Apple") == "apple"
    assert normalise_word("ｒｉｖｅｒ") == "river"  # full-width letters
    assert normalise_word("哈哈 好笑") is None
    assert normalise_word("果") is None
    assert normalise_word("這是一句很長很長的話吧") is None
    assert normalise_word("ok!") is None


def test_words_chain_by_their_last_character() -> None:
    assert chains("蘋果", "果汁") and chains("apple", "egg")
    assert not chains("蘋果", "汁液")
    assert last_char("コーヒー") == "ヒ" and chains("コーヒー", "ひこうき") and chains("コーヒー", "ヒント")
    assert chains("でんしゃ", "やま")  # small kana count as large
    assert chains("蘋果", "過年", homophones=True) and not chains("蘋果", "過年")


def test_the_chain_refuses_repeats_dead_ends_and_double_turns() -> None:
    chain = WordChain("蘋果")

    assert chain.play("汁液", 1) == "wrong_start"
    assert chain.play("果汁", 1) is None
    assert chain.play("汁水", 1) == "twice"
    assert chain.play("汁水", 2) is None
    assert chain.play("水果", 1) is None
    assert chain.play("果汁", 2) == "used"
    assert WordChain("みかん").problem("みかん", 1) == "wrong_start"
    assert WordChain("りんご").problem("ごはん", 1) == "dead_end"
    assert chain.play("果醬", BOT_PLAYER) is None

    assert chain.counts() == {1: 2, 2: 1}
    assert chain.points() == {1: 2 * WORD_POINTS, 2: WORD_POINTS}


class ChainMessage:
    def __init__(self, channel: Any, author_id: int, content: str, bot: bool = False) -> None:
        self.channel = channel
        self.author = SimpleNamespace(id=author_id, bot=bot)
        self.content = content
        self.reactions: list = []

    async def add_reaction(self, emoji: str) -> None:
        self.reactions.append(emoji)


class ChainChannel:
    def __init__(self) -> None:
        self.id = 600
        self.sent: list = []

    async def send(self, content: Any = None, embed: Any = None, allowed_mentions: Any = None) -> None:
        self.sent.append(content if embed is None else embed)


@pytest.mark.asyncio
async def test_a_word_chain_takes_moves_lets_the_bot_step_in_and_records_points(
    cog: GamesCog, store: CommunityStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    asked: list = []

    async def fake_word(orchestrator: Any, guild_id: str, language: str, start: str, used: Any, max_length: int) -> str:
        asked.append(start)
        return "「汁液」"

    monkeypatch.setitem(GamesCog.bot_word.__globals__, "write_chain_word", fake_word)
    cog.chain_idle_seconds = 0.2
    channel, guild = ChainChannel(), SimpleNamespace(id=GUILD_ID)
    game = asyncio.create_task(cog.run_chain(channel, guild, WordChain("蘋果")))
    await asyncio.sleep(0)

    chat = ChainMessage(channel, 10, "大家好 今天吃什麼")
    first = ChainMessage(channel, 10, "果汁")
    again = ChainMessage(channel, 10, "汁液")
    wrong = ChainMessage(channel, 11, "蛋糕")
    assert await cog.handle_message(chat) is False
    assert await cog.handle_message(first) is True
    assert await cog.handle_message(again) is True
    assert await cog.handle_message(wrong) is True
    assert (first.reactions, again.reactions, wrong.reactions) == (["✅"], ["⏳"], ["❌"])

    chain = await game

    assert chain.words == ["蘋果", "果汁", "汁液"]
    assert chain.players == [BOT_PLAYER, 10, BOT_PLAYER]
    assert asked == ["the character 汁"]
    assert channel.sent[:2] == ["chain_first|word=蘋果", "chain_bot_move|word=汁液"]
    result = channel.sent[-1]
    assert result.description == "chain_over|count=2|last=汁液"
    assert {f.name: f.value for f in result.fields}["standings|"] == "chain_player|count=1|user=<@10>"
    assert store.game_points(GUILD_ID) == [(10, WORD_POINTS)]
    assert await cog.handle_message(ChainMessage(channel, 10, "液體")) is False  # the game is over


# ------------------------------------------------------------------ guess the song

from cogs.games_lib import song_guess  # noqa: E402

TITLE_JP = "YOASOBI「夜に駆ける」 Official Music Video"
TITLE_ZH = "周杰倫 Jay Chou【告白氣球 Love Confession】Official MV"
TITLE_EN = "Ed Sheeran - Shape of You (Official Music Video) [4K]"


@pytest.mark.parametrize(
    "guess, title",
    [
        ("夜に駆ける", TITLE_JP),
        ("yoasobi", TITLE_JP),
        ("告白气球", TITLE_ZH),  # Simplified for a Traditional title
        ("love confession", TITLE_ZH),
        ("周杰倫", TITLE_ZH),
        ("shape of u", TITLE_EN),
        ("Shape Of You!!", TITLE_EN),
    ],
)
def test_close_guesses_of_the_song_or_artist_count(guess: str, title: str) -> None:
    assert song_guess.is_correct(guess, title)


@pytest.mark.parametrize("guess", ["you", "official music video", "4k", "a", "Perfect"])
def test_noise_and_wrong_guesses_do_not_count(guess: str) -> None:
    assert not song_guess.is_correct(guess, TITLE_EN)


def test_the_answer_is_shown_without_tags_and_the_clip_starts_mid_song() -> None:
    import random as random_module

    assert song_guess.answer_name(TITLE_EN) == "Ed Sheeran - Shape of You"
    assert song_guess.answer_name(TITLE_ZH) == "周杰倫 Jay Chou【告白氣球 Love Confession】"
    assert song_guess.clip_start(30) == 0.0
    starts = {song_guess.clip_start(200, random_module.Random(seed)) for seed in range(50)}
    assert min(starts) >= 40 and max(starts) <= 120
    assert song_guess.points_for(0) == 1000 and song_guess.points_for(30) == 500


class FakeVoiceClient:
    def __init__(self) -> None:
        self.played: list = []
        self.playing = False
        self.source: Any = None
        self.disconnected = False

    def play(self, source: Any) -> None:
        if self.playing:
            raise discord.ClientException("Already playing audio.")
        self.played.append(source)
        self.playing, self.source = True, source

    def stop(self) -> None:
        self.playing, self.source = False, None

    async def disconnect(self) -> None:
        self.disconnected = True

    def is_playing(self) -> bool:
        return self.playing

    def is_paused(self) -> bool:
        return False


class FakeMusic:
    def __init__(self, songs: dict) -> None:
        self.songs = songs
        self.state_manager = SimpleNamespace(get_state=lambda guild_id: SimpleNamespace(volume=0.4))
        self.audio_manager = SimpleNamespace(create_audio_source=self._source)
        self.youtube = SimpleNamespace(resolve_stream=self._resolve)
        self.queue: list = []
        self.queue_manager = SimpleNamespace(is_queue_empty=lambda guild_id: not self.queue)
        self.sources: list = []
        self.played_next: list = []

    async def play_next(self, ctx: Any) -> None:
        self.played_next.append(ctx)

    def _source(self, song: dict, volume: float, start_offset: float) -> tuple:
        self.sources.append((song["video_id"], volume, start_offset))
        return ("source", song["video_id"])

    async def _resolve(self, url: str, ctx: Any) -> tuple:
        video_id = url.rsplit("=", 1)[1]
        song = self.songs.get(video_id)
        return (dict(song, video_id=video_id), None) if song else (None, None)


class GuessChannel(ChainChannel):
    """Sends a guess from each player in ``guesses`` as soon as a round starts."""

    def __init__(self, cog: GamesCog, guesses: list) -> None:
        super().__init__()
        self.cog = cog
        self.guesses = guesses
        self.messages: list = []

    async def send(self, content: Any = None, embed: Any = None, allowed_mentions: Any = None) -> None:
        await super().send(content, embed, allowed_mentions)
        if embed is not None and embed.description == "song_round|seconds=0" and self.guesses:
            for author, text in self.guesses.pop(0):
                message = ChainMessage(self, author, text)
                message.raw_mentions = []
                self.messages.append(message)
                asyncio.get_running_loop().call_soon(asyncio.ensure_future, self.cog.handle_message(message))


import asyncio  # noqa: E402


@pytest.mark.asyncio
async def test_guess_the_song_plays_clips_and_the_first_right_guess_wins(cog: GamesCog, store: CommunityStore) -> None:
    music = FakeMusic(
        {
            "a": {"title": TITLE_EN, "duration": 200, "url": "https://youtu.be/a"},
            "c": {"title": TITLE_JP, "duration": 30, "url": "https://youtu.be/c"},
        }
    )
    cog.clip_seconds, cog.guess_seconds = 0.05, 0.1
    channel = GuessChannel(cog, [[(10, "perfect"), (11, "shape of you"), (10, "Shape of You")], [(12, "hello")]])
    voice = FakeVoiceClient()
    pool = [("a", TITLE_EN), ("b", "gone"), ("c", TITLE_JP)]

    board = await cog.run_song_game(channel, SimpleNamespace(id=GUILD_ID), voice, music, pool, 2, SimpleNamespace(id=1))

    assert [video for video, _, _ in music.sources] == ["a", "c"]  # "b" can't be played any more
    assert music.sources[1] == ("c", 0.4, 0.0) and 40 <= music.sources[0][2] <= 120
    assert list(board.totals) == [11]
    answers = [e for e in channel.sent if getattr(e, "title", None) == "song_round_title|number=1|total=2"]
    fields = {f.name: f.value for f in answers[-1].fields}
    assert answers[-1].description == "song_answer|title=Ed Sheeran - Shape of You|url=https://youtu.be/a"
    assert fields["result|"].startswith("song_winner|seconds=") and fields["result|"].endswith("user=<@11>")
    assert [m.reactions for m in channel.messages[:3]] == [[], ["✅"], []]
    last_round = [e for e in channel.sent if getattr(e, "title", None) == "song_round_title|number=2|total=2"][-1]
    assert {f.name: f.value for f in last_round.fields}["result|"] == "song_nobody|"
    assert voice.playing is False
    assert [user for user, _ in store.game_points(GUILD_ID)] == [11]


# ------------------------------------------------------------------ limits and timing (review follow-ups)


@pytest.mark.asyncio
async def test_question_writing_is_bounded_across_the_bot(cog: GamesCog, monkeypatch: pytest.MonkeyPatch) -> None:
    from cogs.games import MAX_MODEL_CALLS

    in_flight, peak = 0, 0

    async def slow_write(orchestrator: Any, guild_id: str, memory_text: str) -> str:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return _reply()

    monkeypatch.setitem(GamesCog.make_questions.__globals__, "write_question", slow_write)
    cog.bot.vector_manager.store.memories = [_memory(MEMORY + str(i)) for i in range(30)]

    await asyncio.gather(*(cog.make_questions(FakeGuild(), 10) for _ in range(3)))

    assert peak == MAX_MODEL_CALLS


def _interaction(user_id: int, channel_id: int) -> Any:
    return SimpleNamespace(user=SimpleNamespace(id=user_id), channel=SimpleNamespace(id=channel_id), guild_id=GUILD_ID)


def test_a_player_hosts_one_game_at_a_time(cog: GamesCog) -> None:
    cog._claim(_interaction(10, 500))

    assert cog._busy(_interaction(10, 501)) == "hosting|"
    assert cog._busy(_interaction(11, 500)) == "busy|"
    assert cog._busy(_interaction(11, 501)) is None
    cog._release(_interaction(10, 500))
    assert cog._busy(_interaction(10, 501)) is None


def test_games_respect_the_chat_quota_and_stay_out_of_the_request_channel(cog: GamesCog) -> None:
    hits: list = []
    cog.bot.rate_limiter = SimpleNamespace(hit=lambda bucket, user_id: hits.append((bucket, user_id)) or (12.4 if user_id == 13 else 0))
    requests = SimpleNamespace(is_request_channel=lambda channel: channel.id == 777)
    cog.bot.get_cog = lambda name: SimpleNamespace(requests=requests) if name == "YTMusic" else None

    assert cog._busy(_interaction(13, 500)) == "rate_limited|seconds=12"
    assert cog._busy(_interaction(14, 777)) == "request_channel|"
    assert cog._busy(_interaction(14, 500, )) is None
    assert cog._busy(_interaction(13, 500), uses_model=False) is None  # guess the song calls no model
    assert hits == [("chat", 13), ("chat", 14)]


@pytest.mark.asyncio
async def test_a_reloaded_cog_shares_the_limits_and_unloading_stops_running_games(cog: GamesCog, store: CommunityStore) -> None:
    started = asyncio.Event()

    async def hosted_game() -> None:
        cog._claim(_interaction(10, 500))
        try:
            started.set()
            await asyncio.sleep(60)
        finally:
            cog._release(_interaction(10, 500))

    task = asyncio.create_task(hosted_game())
    await started.wait()
    reloaded = GamesCog(cog.bot, store=store)
    reloaded.lang_manager = FakeLang()

    assert reloaded._busy(_interaction(10, 501)) == "hosting|"
    assert reloaded.limits.model_slots is cog.limits.model_slots
    await cog.cog_unload()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert reloaded._busy(_interaction(10, 501)) is None


@pytest.mark.asyncio
async def test_the_answer_clock_starts_once_the_question_is_posted(cog: GamesCog) -> None:
    clock = [100.0]
    cog._now = lambda: clock[0]
    rounds: list = []

    class SlowChannel(FakeChannel):
        async def send(self, content: Any = None, embed: Any = None, view: Any = None, allowed_mentions: Any = None) -> FakeMessage:
            clock[0] += 10  # Discord took 10 seconds to accept the message
            if view is not None:
                rounds.append(view.round)
            return FakeMessage(embed, view)

    question = parse_question(_reply(), MEMORY, META)
    await cog.run_quiz(SlowChannel({}), SimpleNamespace(id=GUILD_ID), [question])

    assert rounds[0].started_at == 110.0
    rounds[0].answer(10, question.answer, 110.0)
    assert rounds[0].points() == {10: BASE_POINTS * 2}


class FakeThread(FakeTextChannel):
    def __init__(self, public_parent: bool, private: bool) -> None:
        super().__init__(public_parent)  # a thread inherits its parent's permissions
        self.parent_id = 500
        self.parent = object()
        self.type = discord.ChannelType.private_thread if private else discord.ChannelType.public_thread


def test_a_private_thread_under_a_public_channel_is_not_public() -> None:
    guild = FakeGuild()
    guild.channels = {**FakeGuild.channels, 600: FakeThread(True, private=True), 601: FakeThread(True, private=False)}

    assert GamesCog._may_show(guild, "600", here=None) is False
    assert GamesCog._may_show(guild, "601", here=None) is True
    assert GamesCog._may_show(guild, "600", here=600) is True  # the quiz runs in that thread


@pytest.mark.asyncio
async def test_a_question_whose_channel_became_private_is_not_posted(cog: GamesCog) -> None:
    guild = FakeGuild()
    guild.channels = dict(FakeGuild.channels)
    public = parse_question(_reply(), MEMORY, META)
    restricted_later = parse_question(_reply(), MEMORY, {**META, "channel_id": "501"})
    channel = FakeChannel({})
    channel.id = 502

    await cog.run_quiz(channel, guild, [restricted_later, public])

    first, final = channel.sent
    assert first.embed.title == "question_title|number=1|total=1"
    assert final.embed.title == "final_title|"


@pytest.mark.asyncio
async def test_a_clip_only_stops_its_own_audio_and_hands_queued_music_back(cog: GamesCog) -> None:
    music = FakeMusic({"a": {"title": TITLE_EN, "duration": 200, "url": "u"}})
    voice = FakeVoiceClient()
    cog.clip_seconds, cog.guess_seconds = 0.05, 0.1
    channel, guild = ChainChannel(), SimpleNamespace(id=GUILD_ID)
    song = dict(music.songs["a"], video_id="a")

    async def someone_plays_music() -> None:
        await asyncio.sleep(0.02)
        voice.stop()
        voice.play("music")  # /play replaced the clip
        music.queue.append("next song")

    await asyncio.gather(cog.play_round(channel, guild, voice, music, song), someone_plays_music())
    assert voice.source == "music" and voice.playing

    # A second game in the same voice connection cannot start a clip over the music.
    with pytest.raises(discord.ClientException):
        await cog.play_round(channel, guild, voice, music, song)
    assert voice.source == "music"

    voice.stop()
    await cog._hand_back_voice(guild, channel, voice, music, joined=True, user=SimpleNamespace(id=1))
    assert len(music.played_next) == 1 and voice.disconnected is False
    music.queue.clear()
    await cog._hand_back_voice(guild, channel, voice, music, joined=True, user=SimpleNamespace(id=1))
    assert voice.disconnected is True


@pytest.mark.asyncio
async def test_queued_music_ends_the_song_game(cog: GamesCog) -> None:
    music = FakeMusic({"a": {"title": TITLE_EN, "duration": 200, "url": "u"}})
    music.queue.append("song")
    channel = ChainChannel()

    await cog.run_song_game(channel, SimpleNamespace(id=GUILD_ID), FakeVoiceClient(), music, [("a", TITLE_EN)], 1, SimpleNamespace(id=1))

    assert channel.sent[0] == "song_interrupted|" and music.sources == []
