"""Games: a quiz about the server's own history, a word chain, and guess the song.

Each quiz question is written by the model from one randomly picked memory, and the answer is
shown with where it came from (channel, day and a link to the original messages). In the word
chain, players continue each other's words and the bot steps in when nobody does. Guess the song
plays short clips of songs this server listened to. Points go to
the shared game leaderboard (``/leaderboard top kind:Game points``).
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Dict, List, Optional, Set

import discord
from discord import app_commands
from discord.ext import commands

from addons.logging import get_logger
from function import func
from llm.game_writer import write_chain_word, write_question

from .community import COMMUNITY_DB_PATH
from .community_lib.store import CommunityStore
from .games_lib.chain import (
    BOT_PLAYER,
    MAX_CJK_LENGTH,
    WordChain,
    homophones_available,
    last_char,
    normalise_word,
)
from .games_lib.quiz import (
    ANSWER_SECONDS,
    OPTION_COUNT,
    QuizQuestion,
    QuizRound,
    QuizScoreboard,
    parse_question,
    usable_memory,
)
from .games_lib import song_guess
from .language_manager import LanguageManager
from .music_lib.context import PlaybackContext

LETTERS = "ABCD"
# Memories sampled per wanted question: some are skipped (too short, unusable answer).
CANDIDATES_PER_QUESTION = 3
PAUSE_SECONDS = 4
# Model calls for games in flight at once, across every server (quiz questions, chain moves).
MAX_MODEL_CALLS = 3
# A word chain ends when nobody continues for this long; halfway through, the bot plays a word.
CHAIN_IDLE_SECONDS = 60
CHAIN_MAX_SECONDS = 15 * 60
# Reactions on word-like messages in a running chain.
CHAIN_REACTIONS = {None: "✅", "wrong_start": "❌", "used": "🔁", "dead_end": "🚫", "twice": "⏳"}
# Songs considered for guess the song (the server's most played ones).
SONG_POOL_SIZE = 200
MIN_SONGS = 3
_LANGUAGE_NAMES = {"zh_TW": "Traditional Chinese", "zh_CN": "Simplified Chinese", "ja_JP": "Japanese", "en_US": "English"}


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
        self.chain_idle_seconds: float = CHAIN_IDLE_SECONDS
        self.chain_max_seconds: float = CHAIN_MAX_SECONDS
        self._running: Dict[int, bool] = {}
        # Players currently hosting a game: one game per player at a time, across channels.
        self._hosts: Set[int] = set()
        self._model_slots = asyncio.Semaphore(MAX_MODEL_CALLS)
        self._chains: Dict[int, "ChainGame"] = {}
        self._guesses: Dict[int, "GuessRound"] = {}
        self.clip_seconds: float = song_guess.CLIP_SECONDS
        self.guess_seconds: float = song_guess.GUESS_SECONDS

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

    # ------------------------------------------------------------ running games
    def _busy(self, interaction: discord.Interaction) -> Optional[str]:
        """Why a game cannot start here (a response key), or None."""
        if self._running.get(interaction.channel.id):
            return "busy"
        if interaction.user.id in self._hosts:
            return "hosting"
        return None

    def _claim(self, interaction: discord.Interaction) -> None:
        self._running[interaction.channel.id] = True
        self._hosts.add(interaction.user.id)

    def _release(self, interaction: discord.Interaction) -> None:
        self._running.pop(interaction.channel.id, None)
        self._hosts.discard(interaction.user.id)

    # ------------------------------------------------------------ questions
    async def make_questions(
        self,
        guild: discord.Guild,
        count: int,
        channel_id: Optional[str] = None,
        since: Optional[float] = None,
        here: Optional[int] = None,
    ) -> List[QuizQuestion]:
        """Writes up to ``count`` questions from random memories of this server.

        Only memories from channels everyone can read (or from ``here``, the channel the quiz is
        played in) are used, so a quiz never reveals what was said in a restricted channel.
        """
        store, orchestrator = self._memory_store(), getattr(self.bot, "orchestrator", None)
        if store is None or orchestrator is None:
            return []
        memories = await store.sample_memories(
            str(guild.id), count * CANDIDATES_PER_QUESTION, channel_id=channel_id, since=since
        )
        hidden = self.store.optouts(guild.id)
        candidates = [
            m
            for m in memories
            if usable_memory(m.metadata or {}, m.content, list(hidden))
            and self._may_show(guild, (m.metadata or {}).get("channel_id"), here)
        ]
        random.shuffle(candidates)

        async def one(memory: Any) -> Optional[QuizQuestion]:
            async with self._model_slots:
                reply = await write_question(orchestrator, str(guild.id), memory.content)
            return parse_question(reply, memory.content, memory.metadata or {}) if reply else None

        questions: List[QuizQuestion] = []
        while candidates and len(questions) < count:
            batch, candidates = candidates[: count - len(questions)], candidates[count - len(questions):]
            for question in await asyncio.gather(*(one(m) for m in batch)):
                if question is not None and len(questions) < count:
                    questions.append(question)
        return questions

    @staticmethod
    def _may_show(guild: discord.Guild, channel_id: Any, here: Optional[int]) -> bool:
        """Whether a memory from ``channel_id`` may be shown in channel ``here``."""
        try:
            channel_id = int(channel_id)
        except (TypeError, ValueError):
            return False
        if here is not None and channel_id == here:
            return True
        channel = guild.get_channel_or_thread(channel_id)
        if channel is None:
            return False
        everyone = channel.permissions_for(guild.default_role)
        return everyone.view_channel and everyone.read_message_history

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
            # Scoring and the answer window both start once the question can be seen.
            quiz_round.started_at = self._now()
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
        busy = self._busy(interaction)
        if busy:
            await interaction.response.send_message(self._t(guild.id, busy), ephemeral=True)
            return
        if self._memory_store() is None or getattr(self.bot, "orchestrator", None) is None:
            await interaction.response.send_message(self._t(guild.id, "unavailable"), ephemeral=True)
            return
        self._claim(interaction)
        try:
            await interaction.response.send_message(self._t(guild.id, "preparing", user=interaction.user.mention, rounds=rounds))
            since = self._now() - days * 86400 if days else None
            questions = await self.make_questions(
                guild, rounds, str(channel.id) if this_channel else None, since, here=channel.id
            )
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
            self._release(interaction)

    # ------------------------------------------------------------ word chain
    async def handle_message(self, message: discord.Message) -> bool:
        """Plays a message in a running word chain; True when it was a move (so the bot does not chat back).

        Only messages that look like a single word count; other chatter in the channel is left alone.
        """
        if message.author.bot:
            return False
        channel_id = getattr(message.channel, "id", None)
        if channel_id in self._guesses:
            return await self._take_guess(message, self._guesses[channel_id])
        game = self._chains.get(channel_id)
        if game is None:
            return False
        word = normalise_word(message.content)
        if word is None:
            return False
        problem = game.chain.play(word, message.author.id)
        if problem is None:
            game.moved.set()
        try:
            await message.add_reaction(CHAIN_REACTIONS[problem])
        except discord.HTTPException:
            pass
        return True

    def _language(self, guild_id: int) -> str:
        get_lang = getattr(self.lang_manager, "get_server_lang", None)
        code = get_lang(str(guild_id)) if get_lang else "en_US"
        return _LANGUAGE_NAMES.get(code, "English")

    async def bot_word(self, guild: discord.Guild, chain: WordChain) -> Optional[str]:
        """The bot's next word, checked against the rules; None when the model has none."""
        orchestrator = getattr(self.bot, "orchestrator", None)
        if orchestrator is None:
            return None
        start = f"the character {last_char(chain.last_word)}"
        if chain.homophones:
            start += " (or any character with the same pinyin, tones ignored)"
        async with self._model_slots:
            reply = await write_chain_word(
                orchestrator, str(guild.id), self._language(guild.id), start, chain.words[-30:], MAX_CJK_LENGTH
            )
        word = normalise_word((reply or "").splitlines()[0].strip(" \"'「」『』。.!！") if reply else "")
        if word is None or chain.problem(word, BOT_PLAYER) is not None:
            return None
        return word

    async def _wait_for_move(self, game: "ChainGame", seconds: float) -> bool:
        game.moved.clear()
        try:
            await asyncio.wait_for(game.moved.wait(), timeout=seconds)
            return True
        except asyncio.TimeoutError:
            return False

    async def run_chain(self, channel: Any, guild: discord.Guild, chain: WordChain) -> WordChain:
        """Runs a word chain in ``channel`` until nobody continues, then records the points."""
        game = ChainGame(chain)
        self._chains[channel.id] = game
        quiet = discord.AllowedMentions.none()
        started = self._now()
        try:
            await channel.send(self._t(guild.id, "chain_first", word=chain.first_word), allowed_mentions=quiet)
            half = self.chain_idle_seconds / 2
            while self._now() - started < self.chain_max_seconds:
                if await self._wait_for_move(game, half):
                    continue
                if chain.last_player != BOT_PLAYER:
                    seen = len(chain.words)
                    word = await self.bot_word(guild, chain)
                    if len(chain.words) != seen:
                        continue  # someone played while the bot was thinking
                    if word is not None and chain.play(word, BOT_PLAYER) is None:
                        await channel.send(self._t(guild.id, "chain_bot_move", word=word), allowed_mentions=quiet)
                        continue
                if await self._wait_for_move(game, half):
                    continue
                break
        finally:
            self._chains.pop(channel.id, None)
        self.store.add_game_scores(guild.id, "chain", chain.points(), self._now())
        await channel.send(embed=self.chain_result_embed(guild.id, chain), allowed_mentions=quiet)
        return chain

    def chain_result_embed(self, guild_id: int, chain: WordChain) -> discord.Embed:
        played = len(chain.words) - 1
        embed = discord.Embed(
            title=self._t(guild_id, "chain_over_title"),
            description=self._t(guild_id, "chain_over", count=played, last=chain.last_word),
        )
        if played:
            shown = chain.words[-20:]
            text = " → ".join(shown)
            embed.add_field(
                name=self._t(guild_id, "chain_words"),
                value=("… → " if len(shown) < len(chain.words) else "") + text[:1000],
                inline=False,
            )
        ranking = sorted(chain.counts().items(), key=lambda item: (-item[1], item[0]))[:5]
        if ranking:
            embed.add_field(
                name=self._t(guild_id, "standings"),
                value="\n".join(
                    self._t(guild_id, "chain_player", user=f"<@{user_id}>", count=count) for user_id, count in ranking
                ),
                inline=False,
            )
        return embed

    def starter_word(self, guild_id: int) -> str:
        words = [w for w in (normalise_word(w) for w in self._t(guild_id, "chain_starters").split(",")) if w]
        return random.choice(words) if words else "apple"

    @game.command(name="chain", description="Word chain: start each word with the last character of the one before")
    @app_commands.describe(homophones="Also accept a character with the same pronunciation (Chinese)")
    async def chain(self, interaction: discord.Interaction, homophones: bool = False) -> None:
        guild, channel = interaction.guild, interaction.channel
        busy = self._busy(interaction)
        if busy:
            await interaction.response.send_message(self._t(guild.id, busy), ephemeral=True)
            return
        use_homophones = homophones and homophones_available()
        self._claim(interaction)
        try:
            key = "chain_rules_homophones" if use_homophones else "chain_rules"
            text = self._t(guild.id, key, user=interaction.user.mention, seconds=int(self.chain_idle_seconds))
            if homophones and not use_homophones:
                text += "\n" + self._t(guild.id, "chain_no_homophones")
            await interaction.response.send_message(text)
            await self.run_chain(channel, guild, WordChain(self.starter_word(guild.id), homophones=use_homophones))
        except Exception as error:
            self.logger.error("games: the word chain failed", exc_info=True)
            await func.report_error(error, "games: word chain")
            try:
                await channel.send(self._t(guild.id, "failed"))
            except discord.HTTPException:
                pass
        finally:
            self._release(interaction)

    # ------------------------------------------------------------ guess the song
    async def _take_guess(self, message: discord.Message, guess_round: "GuessRound") -> bool:
        """Checks a guess; the first correct one wins the round. Messages to the bot itself are let through."""
        bot_user = getattr(self.bot, "user", None)
        if bot_user is not None and bot_user.id in getattr(message, "raw_mentions", []):
            return False
        if guess_round.winner is None and song_guess.is_correct(message.content, guess_round.title):
            guess_round.winner = (message.author.id, self._now() - guess_round.started_at)
            guess_round.solved.set()
            try:
                await message.add_reaction("✅")
            except discord.HTTPException:
                pass
        return True

    def song_pool(self, music: Any, guild_id: int) -> List[tuple]:
        """``(video_id, title)`` of the server's most played songs, shuffled."""
        rows = music._taste_store.top_played(guild_id, 0, float("inf"), SONG_POOL_SIZE)
        pool = [(video_id, title) for video_id, title, *_ in rows if video_id and title]
        random.shuffle(pool)
        return pool

    async def _wait_solved(self, guess_round: "GuessRound", seconds: float) -> bool:
        try:
            await asyncio.wait_for(guess_round.solved.wait(), timeout=max(0.0, seconds))
            return True
        except asyncio.TimeoutError:
            return False

    async def play_round(self, channel: Any, guild: discord.Guild, voice_client: Any, music: Any, song: dict) -> "GuessRound":
        """Plays one clip and takes guesses until someone is right or time is up."""
        start = song_guess.clip_start(song.get("duration"))
        volume = music.state_manager.get_state(guild.id).volume
        source = music.audio_manager.create_audio_source(song, volume=volume, start_offset=start)
        guess_round = GuessRound(song.get("title") or "", self._now())
        self._guesses[channel.id] = guess_round
        try:
            voice_client.play(source)
            if not await self._wait_solved(guess_round, self.clip_seconds):
                voice_client.stop()
                await self._wait_solved(guess_round, self.guess_seconds - self.clip_seconds)
        finally:
            self._guesses.pop(channel.id, None)
            if voice_client.is_playing():
                voice_client.stop()
        return guess_round

    def song_answer_embed(self, guild_id: int, number: int, total: int, song: dict, guess_round: "GuessRound", scoreboard: QuizScoreboard) -> discord.Embed:
        name = song_guess.answer_name(song.get("title") or "")
        embed = discord.Embed(
            title=self._t(guild_id, "song_round_title", number=number, total=total),
            description=self._t(guild_id, "song_answer", title=name[:200], url=song.get("url") or ""),
        )
        if guess_round.winner is not None:
            user_id, elapsed = guess_round.winner
            result = self._t(guild_id, "song_winner", user=f"<@{user_id}>", seconds=f"{elapsed:.1f}")
        else:
            result = self._t(guild_id, "song_nobody")
        embed.add_field(name=self._t(guild_id, "result"), value=result, inline=False)
        standings = self.standings_text(scoreboard)
        if standings:
            embed.add_field(name=self._t(guild_id, "standings"), value=standings, inline=False)
        if song.get("thumbnail"):
            embed.set_thumbnail(url=song["thumbnail"])
        return embed

    async def run_song_game(
        self, channel: Any, guild: discord.Guild, voice_client: Any, music: Any, pool: List[tuple], rounds: int, user: Any
    ) -> QuizScoreboard:
        """Plays up to ``rounds`` clips from ``pool`` and records the points."""
        scoreboard = QuizScoreboard()
        quiet = discord.AllowedMentions.none()
        context = PlaybackContext(guild=guild, channel=channel, user=user)
        number = 0
        for video_id, _ in pool[: rounds * 2]:  # a few songs may not be playable any more
            if number >= rounds:
                break
            if voice_client.is_playing() or voice_client.is_paused():
                await channel.send(self._t(guild.id, "song_interrupted"), allowed_mentions=quiet)
                break
            song, _ = await music.youtube.resolve_stream(f"https://www.youtube.com/watch?v={video_id}", context)
            if not song:
                continue
            number += 1
            await channel.send(
                embed=discord.Embed(
                    title=self._t(guild.id, "song_round_title", number=number, total=rounds),
                    description=self._t(guild.id, "song_round", seconds=int(self.guess_seconds)),
                ),
                allowed_mentions=quiet,
            )
            guess_round = await self.play_round(channel, guild, voice_client, music, song)
            if guess_round.winner is not None:
                user_id, elapsed = guess_round.winner
                scoreboard.add({user_id: song_guess.points_for(elapsed)})
            await channel.send(
                embed=self.song_answer_embed(guild.id, number, rounds, song, guess_round, scoreboard), allowed_mentions=quiet
            )
            if number < rounds:
                await asyncio.sleep(self.pause_seconds)
        self.store.add_game_scores(guild.id, "guess_song", scoreboard.totals, self._now())
        final = discord.Embed(
            title=self._t(guild.id, "final_title"),
            description=self.standings_text(scoreboard) or self._t(guild.id, "final_none"),
        )
        await channel.send(embed=final, allowed_mentions=quiet)
        return scoreboard

    @game.command(name="guess_song", description="Guess the song from a short clip of what this server listened to")
    @app_commands.describe(rounds="How many songs (3-10)")
    async def guess_song(self, interaction: discord.Interaction, rounds: app_commands.Range[int, 3, 10] = 5) -> None:
        guild, channel = interaction.guild, interaction.channel
        voice = getattr(interaction.user, "voice", None)
        music = self.bot.get_cog("YTMusic")
        voice_client = guild.voice_client
        problem = None
        if voice is None or voice.channel is None:
            problem = "song_need_voice"
        elif music is None or getattr(music, "youtube", None) is None:
            problem = "song_unavailable"
        elif (voice_client is not None and (voice_client.is_playing() or voice_client.is_paused())) or not (
            music.queue_manager.is_queue_empty(guild.id)
        ):
            problem = "song_music_playing"
        else:
            problem = self._busy(interaction)
        pool = self.song_pool(music, guild.id) if problem is None else []
        if problem is None and len(pool) < MIN_SONGS:
            problem = "song_not_enough"
        if problem is not None:
            await interaction.response.send_message(self._t(guild.id, problem, count=MIN_SONGS), ephemeral=True)
            return
        self._claim(interaction)
        joined = False
        try:
            await interaction.response.send_message(
                self._t(guild.id, "song_preparing", user=interaction.user.mention, rounds=rounds, channel=voice.channel.mention)
            )
            if voice_client is None:
                voice_client = await voice.channel.connect()
                joined = True
            elif voice_client.channel != voice.channel:
                await voice_client.move_to(voice.channel)
            await self.run_song_game(channel, guild, voice_client, music, pool, min(rounds, len(pool)), interaction.user)
        except Exception as error:
            self.logger.error("games: guess the song failed", exc_info=True)
            await func.report_error(error, "games: guess the song")
            try:
                await channel.send(self._t(guild.id, "failed"))
            except discord.HTTPException:
                pass
        finally:
            self._release(interaction)
            if joined and voice_client is not None and not (voice_client.is_playing() or voice_client.is_paused()):
                try:
                    await voice_client.disconnect()
                except Exception:
                    self.logger.warning("games: could not leave the voice channel", exc_info=True)


class GuessRound:
    """One clip: its title, when it started, and the first correct guess ``(user_id, seconds)``."""

    def __init__(self, title: str, started_at: float) -> None:
        self.title = title
        self.started_at = started_at
        self.winner: Optional[tuple] = None
        self.solved = asyncio.Event()


class ChainGame:
    """A running word chain and a signal set on every accepted word."""

    def __init__(self, chain: WordChain) -> None:
        self.chain = chain
        self.moved = asyncio.Event()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GamesCog(bot))
