"""Story turns, edited mentions and /summarize all count against the chat quota."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import pytest

from addons.rate_limiter import LimitRule, RateLimiter
from bot import PigPig

BOT_ID = 900


class _Channel:
    def __init__(self) -> None:
        self.id = 70
        self.name = "story"
        self.history_reads = 0

    def history(self, limit: int) -> Any:
        self.history_reads += 1

        async def generator() -> Any:
            if False:
                yield None

        return generator()


class _Message:
    def __init__(self, channel: _Channel, author_id: int = 1, mention: bool = True) -> None:
        self.id = 5
        self.guild = SimpleNamespace(id=7)
        self.channel = channel
        self.author = SimpleNamespace(id=author_id, bot=False, name="al", display_name="Al")
        self.raw_mentions = [BOT_ID] if mention else []
        self.mention_everyone = False
        self.content = "hi"
        self.reference = None
        self.replies: List[str] = []
        self.reactions: List[str] = []

    async def reply(self, content: str, **kwargs: Any) -> Any:
        self.replies.append(content)
        return SimpleNamespace(content=content)

    async def add_reaction(self, emoji: str) -> None:
        self.reactions.append(emoji)


class _Story:
    def __init__(self) -> None:
        self.turns: List[Any] = []

    async def handle_story_message(self, message: Any) -> None:
        self.turns.append(message)


class _Channels:
    def __init__(self, mode: str) -> None:
        self.mode = mode

    def is_allowed_channel(self, channel: Any, guild_id: str) -> tuple:
        return True, False, self.mode


def _bot(mode: str, chat_limit: int = 1) -> Any:
    story = _Story()
    handled: List[Any] = []

    async def handle_message(bot: Any, edit: Any, message: Any, logger: Any, **kwargs: Any) -> None:
        handled.append(message)

    cogs = {"StoryManagerCog": story, "ChannelManager": _Channels(mode)}
    logger = SimpleNamespace(info=lambda *a, **k: None, bind=lambda **k: logger)
    fake = SimpleNamespace(
        user=SimpleNamespace(id=BOT_ID),
        rate_limiter=RateLimiter({"chat": LimitRule(chat_limit, 60)}),
        get_cog=lambda name: cogs.get(name),
        get_logger_for_guild=lambda guild_id: logger,
        orchestrator=SimpleNamespace(handle_message=handle_message),
        story=story,
        handled=handled,
    )
    fake._charge_chat = lambda message: PigPig._charge_chat(fake, message)
    fake._tell_rate_limited = lambda message, bucket, wait: PigPig._tell_rate_limited(fake, message, bucket, wait)
    return fake


@pytest.mark.asyncio
async def test_story_turns_from_an_edit_count_against_the_quota() -> None:
    fake = _bot("story")
    channel = _Channel()

    for _ in range(3):
        await PigPig.on_message_edit(fake, _Message(channel), _Message(channel))

    assert len(fake.story.turns) == 1


@pytest.mark.asyncio
async def test_an_edit_over_the_quota_reads_no_history() -> None:
    fake = _bot("unrestricted")
    channel = _Channel()

    for _ in range(4):
        await PigPig.on_message_edit(fake, _Message(channel), _Message(channel))

    assert len(fake.handled) == 1
    assert channel.history_reads == 1


@pytest.mark.asyncio
async def test_charging_tells_the_member_once_and_then_reacts() -> None:
    fake = _bot("story")
    first, second, third = (_Message(_Channel()) for _ in range(3))

    assert await PigPig._charge_chat(fake, first) is True
    assert await PigPig._charge_chat(fake, second) is False
    assert await PigPig._charge_chat(fake, third) is False

    assert len(second.replies) == 1 and third.reactions == ["⏳"]


@pytest.mark.asyncio
async def test_story_messages_count_against_the_quota() -> None:
    fake = _bot("story")
    logger = fake.get_logger_for_guild("7")

    async def process_commands(message: Any) -> None:
        return None

    fake.message_tracker = None
    fake.setup_logger_for_guild = lambda guild_id: None
    fake.loggers = {"7": logger}
    fake.process_commands = process_commands
    channel = _Channel()

    for _ in range(3):
        await PigPig.on_message(fake, _Message(channel, mention=False))

    assert len(fake.story.turns) == 1


@pytest.mark.asyncio
async def test_summarize_counts_against_the_quota() -> None:
    from cogs.summarizer import SummarizerCog

    bot = SimpleNamespace(rate_limiter=RateLimiter({"chat": LimitRule(1, 60)}))
    cog = SummarizerCog.__new__(SummarizerCog)
    cog.bot = bot
    cog.lang_manager = None
    sent: List[str] = []

    async def send_message(text: str, **kwargs: Any) -> None:
        sent.append(text)

    async def defer(**kwargs: Any) -> None:
        raise AssertionError("over the quota, the summary must not start")

    interaction = SimpleNamespace(
        guild_id=7, user=SimpleNamespace(id=1),
        response=SimpleNamespace(send_message=send_message, defer=defer),
    )
    bot.rate_limiter.hit("chat", 1)

    await SummarizerCog.summarize.callback(cog, interaction)

    assert len(sent) == 1 and "Try again" in sent[0]
