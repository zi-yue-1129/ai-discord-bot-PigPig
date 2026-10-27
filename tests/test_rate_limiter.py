"""Per-user limits on AI chat and image generation, set by the bot owner in base.yaml."""

from __future__ import annotations

from addons.rate_limiter import DEFAULT_LIMITS, LimitRule, RateLimiter, format_wait


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _limiter(max_requests: int = 2, per_seconds: float = 60, **kwargs) -> tuple[RateLimiter, _Clock]:
    clock = _Clock()
    return RateLimiter({"chat": LimitRule(max_requests, per_seconds)}, clock=clock, **kwargs), clock


def test_uses_within_the_limit_are_allowed_and_the_next_one_waits() -> None:
    limiter, clock = _limiter()

    assert limiter.hit("chat", 1) == 0
    assert limiter.hit("chat", 1) == 0
    clock.now += 10
    assert limiter.hit("chat", 1) == 50


def test_the_window_slides() -> None:
    limiter, clock = _limiter()
    limiter.hit("chat", 1)
    clock.now += 30
    limiter.hit("chat", 1)

    clock.now += 31  # the first use has left the window
    assert limiter.hit("chat", 1) == 0
    assert limiter.hit("chat", 1) > 0


def test_each_user_has_their_own_limit() -> None:
    limiter, _ = _limiter(max_requests=1)

    assert limiter.hit("chat", 1) == 0
    assert limiter.hit("chat", 2) == 0
    assert limiter.hit("chat", 1) > 0


def test_a_blocked_attempt_does_not_extend_the_wait() -> None:
    limiter, clock = _limiter(max_requests=1)
    limiter.hit("chat", 1)
    for _ in range(5):
        clock.now += 10
        limiter.hit("chat", 1)

    clock.now += 11
    assert limiter.hit("chat", 1) == 0


def test_zero_means_unlimited_and_unknown_buckets_are_not_limited() -> None:
    limiter, _ = _limiter(max_requests=0)

    assert all(limiter.hit("chat", 1) == 0 for _ in range(50))
    assert limiter.hit("image", 1) == 0


def test_the_owner_is_exempt_unless_the_config_says_otherwise() -> None:
    config = {"chat": {"max_requests": 1, "per_seconds": 60}}

    exempt = RateLimiter.from_config(config, owner_id=42)
    assert [exempt.hit("chat", 42) for _ in range(3)] == [0, 0, 0]

    limited = RateLimiter.from_config({**config, "exempt_owner": False}, owner_id=42)
    limited.hit("chat", 42)
    assert limited.hit("chat", 42) > 0


def test_missing_config_uses_the_defaults() -> None:
    limiter = RateLimiter.from_config(None)

    assert limiter.rules["chat"].max_requests == DEFAULT_LIMITS["chat"]["max_requests"]
    assert limiter.rules["image"].per_seconds == DEFAULT_LIMITS["image"]["per_seconds"]


def test_the_user_is_told_only_once_per_window() -> None:
    limiter, clock = _limiter()

    assert limiter.should_notify("chat", 1, 30) is True
    assert limiter.should_notify("chat", 1, 30) is False
    clock.now += 31
    assert limiter.should_notify("chat", 1, 30) is True


def test_waits_are_shown_as_whole_seconds() -> None:
    assert format_wait(0.2) == 1
    assert format_wait(12.1) == 13


# ------------------------------------------------- daily and per-server caps


def _linked(chat: int = 10, daily: int = 3, server: int = 4) -> tuple[RateLimiter, _Clock]:
    clock = _Clock()
    rules = {
        "chat": LimitRule(chat, 60),
        "chat_daily": LimitRule(daily, 86400),
        "chat_server": LimitRule(server, 3600),
    }
    return RateLimiter(rules, clock=clock, exempt_user_ids=[42]), clock


def test_the_daily_cap_holds_after_the_minute_window_has_passed() -> None:
    limiter, clock = _linked(chat=10, daily=3, server=0)
    for _ in range(3):
        assert limiter.hit("chat", 1) == 0
        clock.now += 61

    wait = limiter.hit("chat", 1)

    assert wait > 3600


def test_a_server_cap_counts_every_member_together() -> None:
    limiter, _ = _linked(daily=0, server=2)
    assert limiter.hit("chat", 1, guild_id=7) == 0
    assert limiter.hit("chat", 2, guild_id=7) == 0

    assert limiter.hit("chat", 3, guild_id=7) > 0
    # Another server and a use without a server are not affected.
    assert limiter.hit("chat", 3, guild_id=8) == 0
    assert limiter.hit("chat", 3) == 0


def test_a_blocked_use_is_charged_nowhere() -> None:
    limiter, clock = _linked(chat=1, daily=5, server=5)
    assert limiter.hit("chat", 1, guild_id=7) == 0
    assert limiter.hit("chat", 1, guild_id=7) > 0  # the minute limit blocks

    clock.now += 61
    # Only the first use counts towards the day and the server.
    for _ in range(3):
        assert limiter.hit("chat", 2, guild_id=7) == 0
        clock.now += 61
    assert limiter.hit("chat", 3, guild_id=7) == 0
    assert limiter.hit("chat", 4, guild_id=7) > 0


def test_a_refund_gives_back_every_linked_window() -> None:
    limiter, _ = _linked(chat=1, daily=1, server=1)
    wait, use = limiter.take("chat", 1, guild_id=7)
    assert wait == 0

    limiter.refund(use)

    assert limiter.hit("chat", 1, guild_id=7) == 0


def test_the_owner_is_not_counted_towards_the_server_cap() -> None:
    limiter, _ = _linked(daily=0, server=1)
    for _ in range(5):
        assert limiter.hit("chat", 42, guild_id=7) == 0

    assert limiter.hit("chat", 1, guild_id=7) == 0


def test_old_records_are_forgotten() -> None:
    limiter, clock = _linked(chat=5, daily=0, server=0)
    for user_id in range(50):
        limiter.hit("chat", user_id)

    clock.now += 3600
    limiter.hit("chat", 999)

    assert set(limiter._hits) == {("chat", 999)}


def test_the_new_caps_have_defaults() -> None:
    limiter = RateLimiter.from_config(None)

    assert limiter.rules["chat_daily"] == LimitRule(DEFAULT_LIMITS["chat_daily"]["max_requests"], 86400)
    assert limiter.rules["chat_server"].per_seconds == 3600
