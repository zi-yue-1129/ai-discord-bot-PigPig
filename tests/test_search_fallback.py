"""Search fallback and action-tool logging."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

from cogs.internet_search import InternetSearchCog

HTML = """<div class="result"><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa">Title A</a>
<a class="result__snippet">Snippet A</a></div><div class="result"></div>"""


def test_parse_duckduckgo_html():
    out = InternetSearchCog._parse_duckduckgo_html(HTML)
    assert "Title A" in out and "Snippet A" in out and "https://example.com/a" in out
    assert InternetSearchCog._parse_duckduckgo_html("<html></html>") == ""


def _cog():
    cog = InternetSearchCog.__new__(InternetSearchCog)
    cog.logger = MagicMock()
    return cog


def test_fallback_uses_duckduckgo_first():
    cog = _cog()
    cog._duckduckgo_search = AsyncMock(return_value="found")
    cog._legacy_google_search = AsyncMock(return_value="legacy")
    assert asyncio.run(cog._fallback_search(None, "q")) == "found"
    cog._legacy_google_search.assert_not_awaited()


def test_fallback_raises_when_everything_empty():
    cog = _cog()
    cog._duckduckgo_search = AsyncMock(side_effect=RuntimeError("down"))
    cog._legacy_google_search = AsyncMock(return_value="")
    try:
        asyncio.run(cog._fallback_search(None, "q"))
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError")
