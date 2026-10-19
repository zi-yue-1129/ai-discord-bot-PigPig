"""Automatic episodic recall: Chinese questions are searched, and only relevant fragments come back."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from llm.memory import episodic
from llm.memory.episodic import EpisodicMemoryProvider


class _Store:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def search_memories_by_vector(self, **kwargs: Any) -> list:
        self.calls.append(kwargs)
        return []


async def _recall(content: str) -> List[Dict[str, Any]]:
    store = _Store()
    provider = EpisodicMemoryProvider(SimpleNamespace(vector_manager=SimpleNamespace(store=store)))
    await provider.get(SimpleNamespace(content=content, channel=SimpleNamespace(id=42)))
    return store.calls


@pytest.mark.asyncio
async def test_a_chinese_question_is_searched() -> None:
    assert len(await _recall("我上次說的那家拉麵店叫什麼")) == 1


@pytest.mark.asyncio
async def test_a_short_chinese_greeting_is_not_searched() -> None:
    assert await _recall("早安") == []


@pytest.mark.asyncio
async def test_a_short_english_greeting_is_not_searched() -> None:
    assert await _recall("hi there") == []


@pytest.mark.asyncio
async def test_a_mention_alone_is_not_searched() -> None:
    assert await _recall("<@123456> 嗨") == []


@pytest.mark.asyncio
async def test_recall_asks_only_for_relevant_fragments() -> None:
    (call,) = await _recall("remember our previous project discussion")

    assert call["min_score"] == episodic._MIN_RELEVANCE_SCORE
    assert 0.0 < episodic._MIN_RELEVANCE_SCORE < 1.0
