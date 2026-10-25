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
