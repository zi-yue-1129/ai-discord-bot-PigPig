"""Games: a quiz about the server's own history, made from its episodic memories.

Each question is written by the model from one randomly picked memory, and the answer is
shown with where it came from (channel, day and a link to the original messages). Points go
to the shared game leaderboard (``/leaderboard top kind:Game points``).
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Dict, List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from function import func
from llm.quiz_writer import write_question

from .community import COMMUNITY_DB_PATH
from .community_lib.store import CommunityStore
from .games_lib.quiz import (
    ANSWER_SECONDS,
    OPTION_COUNT,
    QuizQuestion,
    QuizRound,
    QuizScoreboard,
    parse_question,
    usable_memory,
)
from .language_manager import LanguageManager

LETTERS = "ABCD"
# Memories sampled per wanted question: some are skipped (too short, unusable answer).
CANDIDATES_PER_QUESTION = 3
PAUSE_SECONDS = 4


class QuizView(discord.ui.View):
    """A–D answer buttons for one question."""

    def __init__(self, cog: "GamesCog", guild_id: int, quiz_round: QuizRound) -> None:
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.round = quiz_round
        for index in range(OPTION_COUNT):
            button = discord.ui.Button(label=LETTERS[index], style=discord.ButtonStyle.primary)
            button.callback = self._answer_callback(index)
            self.add_item(button)

    def _answer_callback(self, index: int) -> Any:
        async def callback(interaction: discord.Interaction) -> None:
            first = self.round.answer(interaction.user.id, index, self.cog._now())
            key = "answered" if first else "already_answered"
            await interaction.response.send_message(self.cog._t(self.guild_id, key, letter=LETTERS[index]), ephemeral=True)

        return callback


class GamesCog(commands.Cog):
    """Server games; one game per channel at a time."""

    game = app_commands.Group(name="game", description="Play a game with the server", guild_only=True)

    def __init__(self, bot: commands.Bot, store: Optional[CommunityStore] = None) -> None:
        self.bot = bot
        self.store = store or CommunityStore(COMMUNITY_DB_PATH)
        self.lang_manager: Optional[LanguageManager] = None
        self.logger = get_logger(server_id="Bot", source="games")
        self._now = time.time
        self.answer_seconds: float = ANSWER_SECONDS
        self.pause_seconds: float = PAUSE_SECONDS
        self._running: Dict[int, bool] = {}

    async def cog_load(self) -> None:
        self.lang_manager = LanguageManager.get_instance(self.bot)

    def _t(self, guild_id: Any, key: str, **kwargs: Any) -> str:
        if self.lang_manager is None:
            return key
        return self.lang_manager.translate(str(guild_id), "commands", "games", "responses", key, **kwargs)

    def _memory_store(self) -> Any:
        manager = getattr(self.bot, "vector_manager", None)
        store = getattr(manager, "store", None)
        return store if hasattr(store, "sample_memories") else None

    # ------------------------------------------------------------ questions
    async def make_questions(
        self, guild: discord.Guild, count: int, channel_id: Optional[str] = None, since: Optional[float] = None
    ) -> List[QuizQuestion]:
        """Writes up to ``count`` questions from random memories of this server."""
        store, orchestrator = self._memory_store(), getattr(self.bot, "orchestrator", None)
        if store is None or orchestrator is None:
            return []
        memories = await store.sample_memories(
            str(guild.id), count * CANDIDATES_PER_QUESTION, channel_id=channel_id, since=since
        )
        hidden = self.store.optouts(guild.id)
        candidates = [m for m in memories if usable_memory(m.metadata or {}, m.content, list(hidden))]
        random.shuffle(candidates)

        async def one(memory: Any) -> Optional[QuizQuestion]:
            reply = await write_question(orchestrator, str(guild.id), memory.content)
            return parse_question(reply, memory.content, memory.metadata or {}) if reply else None

        questions: List[QuizQuestion] = []
        while candidates and len(questions) < count:
            batch, candidates = candidates[: count - len(questions)], candidates[count - len(questions):]
            for question in await asyncio.gather(*(one(m) for m in batch)):
                if question is not None and len(questions) < count:
                    questions.append(question)
        return questions

    # ------------------------------------------------------------ layout
    def question_embed(self, guild_id: int, number: int, total: int, question: QuizQuestion) -> discord.Embed:
        options = "\n".join(f"**{LETTERS[i]}.** {option}" for i, option in enumerate(question.options))
        embed = discord.Embed(
            title=self._t(guild_id, "question_title", number=number, total=total),
            description=f"{question.question}\n\n{options}",
        )
        embed.set_footer(text=self._t(guild_id, "question_footer", seconds=int(self.answer_seconds)))
        return embed

    def answer_embed(
        self, guild: discord.Guild, number: int, total: int, quiz_round: QuizRound, scoreboard: QuizScoreboard
    ) -> discord.Embed:
        question = quiz_round.question
        correct = quiz_round.points()
        options = "\n".join(
            f"{'✅' if i == question.answer else '▫️'} **{LETTERS[i]}.** {option}" for i, option in enumerate(question.options)
        )
        embed = discord.Embed(
            title=self._t(guild.id, "question_title", number=number, total=total),
            description=f"{question.question}\n\n{options}",
        )
        result = (
            self._t(guild.id, "correct_count", count=len(correct), answered=len(quiz_round.answers))
            if correct
            else self._t(guild.id, "nobody_correct")
        )
        embed.add_field(name=self._t(guild.id, "result"), value=result, inline=False)
        source = self.source_text(guild.id, question)
        if source:
            embed.add_field(name=self._t(guild.id, "source"), value=source, inline=False)
        standings = self.standings_text(scoreboard)
        if standings:
            embed.add_field(name=self._t(guild.id, "standings"), value=standings, inline=False)
        return embed

    def source_text(self, guild_id: int, question: QuizQuestion) -> str:
        parts = []
        if question.channel_id:
            parts.append(f"<#{question.channel_id}>")
        if question.timestamp:
            parts.append(f"<t:{int(question.timestamp)}:D>")
        if question.jump_url:
            parts.append(f"[{self._t(guild_id, 'source_link')}]({question.jump_url})")
        return " · ".join(parts)

    @staticmethod
    def standings_text(scoreboard: QuizScoreboard) -> str:
        medals = ["🥇", "🥈", "🥉"]
        return "\n".join(
            f"{medals[i] if i < len(medals) else f'`#{i + 1}`'} <@{user_id}> · {points:,}"
            for i, (user_id, points) in enumerate(scoreboard.standings())
        )

    # ------------------------------------------------------------ game
    async def run_quiz(self, channel: Any, guild: discord.Guild, questions: List[QuizQuestion]) -> QuizScoreboard:
        """Plays the questions in ``channel`` and records the points."""
        scoreboard = QuizScoreboard()
        quiet = discord.AllowedMentions.none()
        for number, question in enumerate(questions, start=1):
            quiz_round = QuizRound(question=question, started_at=self._now())
            view = QuizView(self, guild.id, quiz_round)
            message = await channel.send(
                embed=self.question_embed(guild.id, number, len(questions), question), view=view, allowed_mentions=quiet
            )
            await asyncio.sleep(self.answer_seconds)
            view.stop()
            scoreboard.add(quiz_round.points())
            await message.edit(embed=self.answer_embed(guild, number, len(questions), quiz_round, scoreboard), view=None)
            if number < len(questions):
                await asyncio.sleep(self.pause_seconds)
        self.store.add_game_scores(guild.id, "quiz", scoreboard.totals, self._now())
        final = discord.Embed(
            title=self._t(guild.id, "final_title"),
            description=self.standings_text(scoreboard) or self._t(guild.id, "final_none"),
        )
        await channel.send(embed=final, allowed_mentions=quiet)
        return scoreboard

    @game.command(name="quiz", description="A quiz about things that happened on this server")
    @app_commands.describe(
        rounds="How many questions (3-10)",
        days="Only use memories from the last this many days",
        this_channel="Only use memories from this channel",
    )
    async def quiz(
        self,
        interaction: discord.Interaction,
        rounds: app_commands.Range[int, 3, 10] = 5,
        days: Optional[app_commands.Range[int, 1, 3650]] = None,
        this_channel: bool = False,
    ) -> None:
        guild, channel = interaction.guild, interaction.channel
        if self._running.get(channel.id):
            await interaction.response.send_message(self._t(guild.id, "busy"), ephemeral=True)
            return
        if self._memory_store() is None or getattr(self.bot, "orchestrator", None) is None:
            await interaction.response.send_message(self._t(guild.id, "unavailable"), ephemeral=True)
            return
        self._running[channel.id] = True
        try:
            await interaction.response.send_message(self._t(guild.id, "preparing", user=interaction.user.mention, rounds=rounds))
            since = self._now() - days * 86400 if days else None
            questions = await self.make_questions(guild, rounds, str(channel.id) if this_channel else None, since)
            if not questions:
                await channel.send(self._t(guild.id, "no_memories"))
                return
            await self.run_quiz(channel, guild, questions)
        except Exception as error:
            self.logger.error("games: the quiz failed", exc_info=True)
            await func.report_error(error, "games: quiz")
            try:
                await channel.send(self._t(guild.id, "failed"))
            except discord.HTTPException:
                pass
        finally:
            self._running.pop(channel.id, None)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GamesCog(bot))
