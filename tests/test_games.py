"""The server quiz: grounded questions from episodic memories, scoring, and game points."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional

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


def _memory(text: str, authors: Optional[list] = None) -> SimpleNamespace:
    return SimpleNamespace(content=text, metadata={**META, "author_ids": authors or ["7"]})


@pytest.fixture
def store(tmp_path: Path) -> CommunityStore:
    return CommunityStore(tmp_path / "community.db")


@pytest.fixture
def cog(store: CommunityStore) -> GamesCog:
    memories = [_memory(MEMORY), _memory(MEMORY, ["13"]), _memory("太短"), _memory(MEMORY + "（第二次）")]
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

    questions = await cog.make_questions(SimpleNamespace(id=GUILD_ID), 3, channel_id="500", since=10.0)

    assert len(questions) == 2  # the hidden author's memory and the short one are skipped
    assert sorted(seen) == sorted([MEMORY, MEMORY + "（第二次）"])
    assert cog.bot.vector_manager.store.calls == [(str(GUILD_ID), 9, "500", 10.0)]


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
