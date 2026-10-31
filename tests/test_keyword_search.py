"""Keyword search finds a memory whatever the letter case, and the payload indexes sit on the fields really used."""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any, List, Tuple

import pytest
from qdrant_client.models import Filter, MatchAny, MatchText, PayloadSchemaType, TextIndexParams

from cogs.memory.vector_stores.qdrant_store import QdrantStore
from llm.tools.episodic_memory import EpisodicMemoryTools


def _conditions(query: str) -> list:
    """The text-match conditions of the keyword filter (fails if there is no filter)."""
    return [condition for condition in QdrantStore._keyword_filter(query).should if isinstance(condition.match, MatchText)]


def _texts(query: str) -> List[str]:
    return [condition.match.text for condition in _conditions(query)]


def test_each_word_is_matched_as_text_on_the_keywords_field() -> None:
    assert {condition.key for condition in _conditions("HAREKAZE Kuma")} == {"metadata.keywords"}
    assert _texts("HAREKAZE Kuma") == ["HAREKAZE", "Kuma"]


def test_without_the_text_index_the_old_exact_lowercase_match_is_used_alone() -> None:
    """A text match without its index is a case-sensitive substring scan that can crowd out exact hits (sql vs NoSQL)."""
    conditions = QdrantStore._keyword_filter("HAREKAZE Kuma", text_index=False).should

    assert len(conditions) == 1 and isinstance(conditions[0].match, MatchAny)
    assert conditions[0].match.any == ["harekaze", "kuma"]


def test_any_word_may_match_not_all_of_them() -> None:
    assert not QdrantStore._keyword_filter("a b").must, "'should' means any word matches"


def test_chinese_words_are_kept_as_they_are() -> None:
    assert _texts("刮刮樂 期望值") == ["刮刮樂", "期望值"]


def test_an_empty_query_has_no_filter() -> None:
    assert QdrantStore._keyword_filter("   ") is None


def test_a_flood_of_words_is_capped() -> None:
    assert len(_texts(" ".join(f"w{number}" for number in range(500)))) == QdrantStore.MAX_KEYWORD_QUERY_WORDS


class _Client:
    def __init__(self, failing_field: str = "") -> None:
        self.created: List[Tuple[str, Any]] = []
        self.failing_field = failing_field

    def collection_exists(self, name: str) -> bool:
        return True

    def create_payload_index(self, collection_name: str, field_name: str, field_schema: Any) -> None:
        if field_name == self.failing_field:
            raise RuntimeError("index refused")
        self.created.append((field_name, field_schema))


def _store(client: _Client) -> QdrantStore:
    store = QdrantStore.__new__(QdrantStore)
    store.client = client
    store.collection_name = "memories"
    return store


@pytest.mark.asyncio
async def test_the_indexes_are_created_on_the_metadata_fields_the_filters_use() -> None:
    client = _Client()

    await _store(client).ensure_storage()

    created = dict(client.created)
    assert set(created) == {"metadata.keywords", "metadata.author_ids", "metadata.channel_id", "metadata.guild_id"}
    assert created["metadata.guild_id"] == PayloadSchemaType.KEYWORD
    keywords = created["metadata.keywords"]
    assert isinstance(keywords, TextIndexParams) and keywords.lowercase is True


ALL_FIELDS = {"metadata.keywords", "metadata.author_ids", "metadata.channel_id", "metadata.guild_id"}


@pytest.mark.asyncio
@pytest.mark.parametrize("refused", sorted(ALL_FIELDS))
async def test_one_refused_index_does_not_stop_the_others(refused: str) -> None:
    """Whichever index is refused, the rest are still built (refusing only the last one proves nothing)."""
    client = _Client(failing_field=refused)

    await _store(client).ensure_storage()

    assert {field for field, _ in client.created} == ALL_FIELDS - {refused}


@pytest.mark.asyncio
async def test_the_text_match_is_only_used_once_its_index_exists() -> None:
    built, refused = _store(_Client()), _store(_Client(failing_field="metadata.keywords"))
    assert built._keyword_index_ready is False and refused._keyword_index_ready is False, "nothing is built yet"

    await built.ensure_storage()
    await refused.ensure_storage()

    assert built._keyword_index_ready is True
    assert refused._keyword_index_ready is False


class _QueryClient:
    def __init__(self) -> None:
        self.filters: List[Any] = []

    def query_points(self, **kwargs: Any) -> Any:
        self.filters.append(kwargs["query_filter"])
        return SimpleNamespace(points=[])


@pytest.mark.asyncio
@pytest.mark.parametrize("ready, expected", [(True, MatchText), (False, MatchAny)])
async def test_the_search_builds_the_filter_for_the_index_state(ready: bool, expected: type) -> None:
    client = _QueryClient()
    store = _store(client)
    store.embedding_dim = 2
    store._keyword_index_ready = ready

    await store.search_memories_by_keyword("Kuma", guild_id="9")

    keyword_filter = [part for part in client.filters[0].must if isinstance(part, Filter)]
    assert len(keyword_filter) == 1 and isinstance(keyword_filter[0].should[0].match, expected)


# ---------------------------------------------------------------- what the model is told


class _EmptyStore:
    async def search(self, **kwargs: Any) -> list:
        return []


def _tool() -> Any:
    bot = SimpleNamespace(vector_manager=SimpleNamespace(store=_EmptyStore()))
    message = SimpleNamespace(channel=SimpleNamespace(id=1), guild=SimpleNamespace(id=2))
    runtime = SimpleNamespace(bot=bot, message=message, logger=None)
    (tool,) = [t for t in EpisodicMemoryTools(runtime).get_tools() if t.name == "search_episodic_memory"]
    return tool


def test_the_tool_description_asks_for_single_topic_words_not_ids_or_sentences() -> None:
    description = _tool().description

    assert "single" in description and "not" in description and "ID" in description
    assert "exact-term" not in description and "precise tokens or phrases" not in description


@pytest.mark.asyncio
async def test_an_empty_result_tells_the_model_not_to_search_again_with_a_longer_query() -> None:
    answer = await _tool().ainvoke({"keyword_query": "something"})

    assert answer.startswith("No relevant memories found.")
    assert "do not" in answer.lower() and "retry" in answer.lower()


@pytest.mark.asyncio
async def test_an_empty_semantic_search_is_not_told_to_stop_searching() -> None:
    """The retry warning is about keyword queries; a semantic query may still be worth trying."""
    answer = await _tool().ainvoke({"vector_query": "what did we talk about"})

    assert answer == "No relevant memories found."


@pytest.mark.asyncio
async def test_the_empty_keyword_answer_points_to_a_semantic_search_instead() -> None:
    answer = await _tool().ainvoke({"keyword_query": "something"})

    assert "vector_query" in answer


class _ThreadRecordingClient(_Client):
    def __init__(self) -> None:
        super().__init__()
        self.threads: List[int] = []

    def create_payload_index(self, collection_name: str, field_name: str, field_schema: Any) -> None:
        self.threads.append(threading.get_ident())
        super().create_payload_index(collection_name, field_name, field_schema)


@pytest.mark.asyncio
async def test_building_the_indexes_does_not_block_the_event_loop() -> None:
    """On the live 67k-point collection the server call can take many seconds."""
    client = _ThreadRecordingClient()

    await _store(client).ensure_storage()

    assert client.threads and threading.get_ident() not in client.threads
