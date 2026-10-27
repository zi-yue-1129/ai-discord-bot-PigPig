"""addons.confirm.ask re-checks that a question may still be posted after the old one is closed."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from addons.confirm import ConfirmView, ask


class _Channel:
    """A channel that records what is sent."""

    def __init__(self) -> None:
        self.sent: List[str] = []

    async def send(self, content: str, **kwargs: Any) -> SimpleNamespace:
        self.sent.append(content)
        return SimpleNamespace(id=len(self.sent))


class _OpenQuestion:
    """A question already open under the same key; closing it takes an await, like an HTTP edit."""

    def __init__(self, on_replace: Any) -> None:
        self.on_replace = on_replace
        self.replaced = False

    async def replace(self) -> None:
        self.on_replace()
        self.replaced = True


async def _answer(*args: Any) -> str:
    return "done"


def _view(pending: Dict[Any, Any]) -> ConfirmView:
    return ConfirmView(1, lambda key: key, lambda: _answer(), pending, ("guild", "asker", "target"))


@pytest.mark.asyncio
async def test_a_question_that_is_no_longer_allowed_is_not_posted() -> None:
    allowed = {"value": True}
    pending: Dict[Any, Any] = {}
    pending[("guild", "asker", "target")] = _OpenQuestion(lambda: allowed.update(value=False))
    channel = _Channel()

    async def still_allowed() -> bool:
        return allowed["value"]

    posted = await ask(channel, "ping <@1>", _view(pending), still_allowed=still_allowed)

    assert posted is None
    assert channel.sent == [], "nothing is sent once the member may no longer be pinged"
    assert pending == {}, "the key is not left reserved"


@pytest.mark.asyncio
async def test_a_question_that_is_still_allowed_is_posted() -> None:
    pending: Dict[Any, Any] = {}
    channel = _Channel()

    async def still_allowed() -> bool:
        return True

    view = _view(pending)
    posted = await ask(channel, "ping <@1>", view, still_allowed=still_allowed)

    assert posted is view and channel.sent == ["ping <@1>"]
