"""Robustness fixes found in the non-music audit: update buttons, error reports and blocking calls."""

from __future__ import annotations

import ast
import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from cogs import gen_img, gif_tools, internet_search
from cogs.update_manager import UpdateActionView, UpdateConfirmView

ROOT = Path(__file__).resolve().parents[1]
OWNER_ID = 100
STRANGER_ID = 200


# --------------------------------------------------------------- update buttons


class _Response:
    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []

    async def send_message(self, content: str = "", **kwargs: Any) -> None:
        self.sent.append({"content": content, **kwargs})


def _click(user_id: int) -> SimpleNamespace:
    return SimpleNamespace(user=SimpleNamespace(id=user_id), response=_Response())


def _translate(guild_id: str, *keys: str, **kwargs: Any) -> str:
    return "/".join(keys)


def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


@pytest.fixture(params=["action", "confirm"])
def update_view(request: pytest.FixtureRequest) -> Any:
    if request.param == "action":
        return UpdateActionView(object(), "1", _translate, is_owner=_is_owner)
    return UpdateConfirmView(object(), None, "1", _translate, is_owner=_is_owner)


@pytest.mark.asyncio
async def test_a_stranger_cannot_use_the_update_buttons(update_view: Any) -> None:
    click = _click(STRANGER_ID)

    allowed = await update_view.interaction_check(click)

    assert allowed is False
    assert click.response.sent == [{"content": "commands/update_manager/permissions/owner_only_update", "ephemeral": True}]


@pytest.mark.asyncio
async def test_the_owner_can_use_the_update_buttons(update_view: Any) -> None:
    click = _click(OWNER_ID)

    assert await update_view.interaction_check(click) is True
    assert click.response.sent == []


# ------------------------------------------------------------- error reporting


def test_error_reports_never_pass_the_bot_as_the_error() -> None:
    """``func.report_error(error, details)`` takes the error first; the bot object is not an error."""
    offenders = []
    for path in (ROOT / "cogs").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "report_error" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Attribute) and first.attr == "bot":
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")

    assert offenders == []


# ------------------------------------------------------------ blocking calls


class _Probe:
    """Records where and how a blocking call was made."""

    def __init__(self) -> None:
        self.thread_id: int = 0
        self.kwargs: Dict[str, Any] = {}


@pytest.mark.asyncio
async def test_the_tenor_request_has_a_timeout_and_runs_off_the_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _Probe()

    def fake_get(url: str, **kwargs: Any) -> SimpleNamespace:
        probe.thread_id = threading.get_ident()
        probe.kwargs = kwargs
        return SimpleNamespace(status_code=200, content=b'{"results": []}', text="")

    monkeypatch.setattr(gif_tools.requests, "get", fake_get)
    cog = SimpleNamespace(tenor_api_key="key", lang_manager=None, logger=gif_tools.log)

    result = await gif_tools.GifTools.search_gif(cog, "cat")

    assert result == []
    assert probe.thread_id != threading.get_ident()
    assert probe.kwargs["timeout"] > 0


@pytest.mark.asyncio
async def test_the_youtube_search_runs_off_the_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _Probe()

    class _Search:
        def __init__(self, query: str, max_results: int) -> None:
            probe.thread_id = threading.get_ident()

        def to_dict(self) -> List[dict]:
            return [{"title": "t", "channel": "c", "views": "1", "url_suffix": "/watch?v=x"}]

    monkeypatch.setattr(internet_search, "YoutubeSearch", _Search)
    cog = SimpleNamespace(lang_manager=None)

    text = await internet_search.InternetSearchCog.youtube_search(cog, SimpleNamespace(guild=None), "query")

    assert "Found: t" == text
    assert probe.thread_id != threading.get_ident()


@pytest.mark.asyncio
async def test_a_hanging_youtube_search_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    class _Search:
        def __init__(self, query: str, max_results: int) -> None:
            self.query = query

        def to_dict(self) -> List[dict]:
            release.wait(timeout=5)
            return []

    async def no_report(error: Exception, details: str = "") -> None:
        return None

    monkeypatch.setattr(internet_search, "YoutubeSearch", _Search)
    monkeypatch.setattr(internet_search, "YOUTUBE_SEARCH_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(internet_search.func, "report_error", no_report)
    cog = SimpleNamespace(lang_manager=None)

    text = await asyncio.wait_for(
        internet_search.InternetSearchCog.youtube_search(cog, SimpleNamespace(guild=None), "query"), timeout=3
    )
    release.set()

    assert text.startswith("Search failed")


@pytest.mark.asyncio
async def test_a_hanging_gemini_search_falls_back_to_the_legacy_search(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    class _Models:
        def generate_content(self, **kwargs: Any) -> Any:
            release.wait(timeout=5)
            return None

    class _Client:
        def __init__(self, api_key: str) -> None:
            self.models = _Models()

    async def no_report(error: Exception, details: str = "") -> None:
        return None

    async def legacy(ctx: Any, query: str, message_to_edit: Any = None) -> str:
        return "legacy answer"

    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setattr(internet_search.genai, "Client", _Client)
    monkeypatch.setattr(internet_search, "GEMINI_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(internet_search.func, "report_error", no_report)
    cog = SimpleNamespace(lang_manager=None, _legacy_google_search=legacy)

    answer = await asyncio.wait_for(
        internet_search.InternetSearchCog.google_search(cog, SimpleNamespace(guild=None), "query"), timeout=3
    )
    release.set()

    assert answer == "legacy answer"


@pytest.mark.asyncio
async def test_a_hanging_gemini_image_request_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    release = threading.Event()

    class _Models:
        def generate_content(self, **kwargs: Any) -> Any:
            release.wait(timeout=5)
            return None

    async def no_report(error: Exception, details: str = "") -> None:
        return None

    monkeypatch.setattr(gen_img, "GEMINI_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(gen_img.func, "report_error", no_report)
    cog = SimpleNamespace(client=SimpleNamespace(models=_Models()), lang_manager=None, logger=gen_img.get_logger(server_id="Bot", source="test"))

    result = await asyncio.wait_for(gen_img.ImageGenerationCog.generate_with_gemini(cog, "a cat", [], []), timeout=3)
    release.set()

    assert result == (None, None)
