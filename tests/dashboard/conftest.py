"""Pytest fixtures for dashboard tests.

Module stubs for heavy dependencies live in the test modules themselves so
the root conftest can isolate them per module (see tests/conftest.py).
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# FastAPI test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def owner_token_payload() -> dict:
    """Return a minimal JWT payload with Bot Owner role."""
    return {"sub": "owner_discord_id", "role": "owner", "guild_ids": []}


@pytest.fixture()
def user_token_payload() -> dict:
    """Return a minimal JWT payload with general user role."""
    return {"sub": "user_discord_id", "role": "user", "guild_ids": []}
