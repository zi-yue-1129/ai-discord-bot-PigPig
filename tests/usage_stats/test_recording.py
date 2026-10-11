"""Regression tests for missing command and model events using temporary SQLite."""
from __future__ import annotations

import asyncio
import sqlite3
import time
import types
from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from usage_stats.runtime import (
    AIMessage, AIMessageChunk, AsyncCallbackHandler, BaseChatModel, BaseMessage,
    CallbackManager, CallbackManagerForLLMRun, ChatGeneration, ChatGenerationChunk,
    ChatResult, HumanMessage, commands, create_agent, discord,
)
from pydantic import BaseModel


class OfflineChatModel(BaseChatModel):
    """Exercise real LangChain lifecycle callbacks without contacting a provider."""

    fail: bool = False
    delay: float = 0.02
    response_content: str = "ok"
    fail_tool_binding: bool = False
    use_tool: bool = False

    @property
    def _llm_type(self) -> str:
        return "offline-statistics-test"

    def _generate(
        self, messages: list[BaseMessage], stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any,
    ) -> ChatResult:
        time.sleep(self.delay)
        if self.fail or (self.fail_tool_binding and "tool_choice" in kwargs):
            raise RuntimeError("provider unavailable")
        if self.use_tool and isinstance(messages[-1], HumanMessage):
            message = AIMessage(content="", tool_calls=[{
                "name": "lookup", "args": {}, "id": "lookup-1", "type": "tool_call",
            }])
        else:
            message = AIMessage(content=self.response_content)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(
        self, messages: list[BaseMessage], stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        time.sleep(self.delay)
        yield ChatGenerationChunk(message=AIMessageChunk(content="ok"))
        if self.fail:
            raise RuntimeError("provider unavailable")

    async def _astream(
        self, messages: list[BaseMessage], stop: list[str] | None = None,
        run_manager: Any = None, **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        await asyncio.sleep(self.delay)
        yield ChatGenerationChunk(message=AIMessageChunk(content="ok"))
        if self.fail:
            raise RuntimeError("provider unavailable")

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> Any:
        """Preserve model callbacks when an agent or structured output binds tools.

        Args:
            tools: Tool schemas supplied by LangChain.
            **kwargs: Binding options.

        Returns:
            A real runnable binding to this model.
        """
        return self.bind(**kwargs)


class StructuredReply(BaseModel):
    """Schema used to verify that parsing failures do not hide provider calls."""

    answer: str


def read_rows(db_path: Path, table: str) -> list[tuple[Any, ...]]:
    """Read recorded rows from a temporary database.

    Args:
        db_path: Temporary database file.
        table: Event table name.

    Returns:
        All event rows in insertion order.
    """
    if table not in {"command_events", "llm_call_events"}:
        raise ValueError(table)
    with sqlite3.connect(db_path) as connection:
        return connection.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()


async def emit(bot: commands.Bot, event: str, payload: Any) -> None:
    """Invoke the listeners registered by the production cog.

    Args:
        bot: Offline Discord bot.
        event: Discord event name.
        payload: Event payload.
    """
    for listener in bot.extra_events.get(event, []):
        await listener(payload)


@pytest.mark.asyncio
@pytest.mark.parametrize("application", [False, True])
@pytest.mark.parametrize("guild_id", [123, None])
async def test_commands_record_at_start_without_completion(
    stats_modules: types.SimpleNamespace, tmp_path: Path, application: bool,
    guild_id: int | None,
) -> None:
    """Record attempted commands even when execution never completes.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        application: Whether the invocation is an application command.
        guild_id: Guild or DM context.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
    bot.stats_collector = collector
    created_at = datetime(2026, 10, 1, tzinfo=timezone.utc)
    async with bot:
        await bot.add_cog(stats_modules.cog.StatsCog(bot))
        if application:
            payload = types.SimpleNamespace(
                type=discord.InteractionType.application_command,
                guild_id=guild_id, user=types.SimpleNamespace(id=456),
                command=types.SimpleNamespace(qualified_name="admin reload"),
                created_at=created_at, data={"name": "admin"},
            )
            await emit(bot, "on_interaction", payload)
        else:
            payload = types.SimpleNamespace(
                guild=types.SimpleNamespace(id=guild_id) if guild_id else None,
                author=types.SimpleNamespace(id=456), interaction=None,
                command=types.SimpleNamespace(qualified_name="admin reload"),
                message=types.SimpleNamespace(created_at=created_at),
            )
            await emit(bot, "on_command", payload)
    rows = read_rows(db_path, "command_events")
    assert [row[1:] for row in rows] == [
        (str(guild_id) if guild_id else "0", "456", "admin reload", 1790812800.0)
    ]


@pytest.mark.asyncio
async def test_hybrid_commands_count_once_and_ui_events_are_ignored(
    stats_modules: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Avoid duplicate hybrid slash events and exclude autocomplete and buttons.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
    bot.stats_collector = collector
    interaction = types.SimpleNamespace(
        type=discord.InteractionType.application_command, guild_id=123,
        user=types.SimpleNamespace(id=456), command=None,
        created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        data={"name": "admin", "options": [{"type": 2, "name": "config", "options": [
            {"type": 1, "name": "reload", "options": [{"type": 3, "name": "value"}]}
        ]}]},
    )
    async with bot:
        await bot.add_cog(stats_modules.cog.StatsCog(bot))
        await emit(bot, "on_interaction", interaction)
        await emit(bot, "on_command", types.SimpleNamespace(interaction=interaction))
        interaction.type = discord.InteractionType.autocomplete
        await emit(bot, "on_interaction", interaction)
        interaction.type = discord.InteractionType.component
        await emit(bot, "on_interaction", interaction)
    assert [row[1:4] for row in read_rows(db_path, "command_events")] == [
        ("123", "456", "admin config reload")
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["vllm:local", "openai:remote", "ollama:local"])
@pytest.mark.parametrize("operation", ["invoke", "ainvoke", "stream", "astream", "agent", "structured"])
@pytest.mark.parametrize("fail", [False, True])
async def test_model_helpers_record_each_call_and_failure(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    provider: str, operation: str, fail: bool,
) -> None:
    """Persist actual model lifecycle events across runnable and agent paths.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
        provider: Model identifier passed to the helper.
        operation: LangChain entry point.
        fail: Whether the provider raises an error.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), fail=fail, cache=False)

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    model = stats_modules.model.create_model_instance(provider, guild_id="123")
    before = time.time()

    async def invoke() -> None:
        if operation == "invoke":
            assert model.invoke("hello").content == "ok"
        elif operation == "ainvoke":
            assert (await model.ainvoke("hello")).content == "ok"
        elif operation == "stream":
            assert "".join(chunk.content for chunk in model.stream("hello")) == "ok"
        elif operation == "astream":
            chunks = [chunk async for chunk in model.astream("hello")]
            assert "".join(chunk.content for chunk in chunks) == "ok"
        elif operation == "agent":
            agent = create_agent(model, tools=[])
            response = await agent.ainvoke({"messages": [HumanMessage(content="hello")]})
            assert response["messages"][-1].content == "ok"
        else:
            # Missing tool output still represents a completed provider call.
            await model.with_structured_output(StructuredReply).ainvoke("hello")

    if fail:
        with pytest.raises(RuntimeError, match="provider unavailable"):
            await invoke()
    else:
        await invoke()
    after = time.time()
    rows = read_rows(db_path, "llm_call_events")
    assert len(rows) == 1
    _, guild_id, model_name, timestamp, duration_ms, success = rows[0]
    assert (guild_id, model_name, success) == ("123", provider, int(not fail))
    assert before <= timestamp <= after
    assert 15 <= duration_ms <= (after - before) * 1000 + 10


@pytest.mark.asyncio
async def test_memory_raw_fallback_uses_recording_helper(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the original vLLM name and record raw memory fallback calls.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), cache=False)

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    # The old memory helper bypasses model_init entirely.
    monkeypatch.setattr(stats_modules.memory, "init_chat_model", offline_init, raising=False)
    service = stats_modules.memory.EventSummarizationService.__new__(
        stats_modules.memory.EventSummarizationService
    )
    service.settings = types.SimpleNamespace(vllm_url="http://memory-vllm.invalid")
    model = service._create_llm_instance("vllm:local", force_json=True)
    assert (await model.ainvoke("summarize")).content == "ok"
    rows = read_rows(db_path, "llm_call_events")
    assert len(rows) == 1
    assert rows[0][2] == "vllm:local"
    assert rows[0][-1] == 1


@pytest.mark.asyncio
async def test_timeout_is_a_failed_model_call(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persist cancelled provider streams as failures with elapsed duration.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), delay=1.0, cache=False)

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    model = stats_modules.model.create_model_instance("vllm:slow", guild_id="123")

    async def consume() -> None:
        async for chunk in model.astream("hello"):
            raise AssertionError("Timeout must occur before a token arrives")

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(consume(), timeout=0.04)
    rows = read_rows(db_path, "llm_call_events")
    assert len(rows) == 1
    assert rows[0][1:3] == ("123", "vllm:slow")
    assert rows[0][-1] == 0
    assert 20 <= rows[0][-2] < 500


@pytest.mark.asyncio
async def test_concurrent_calls_keep_separate_timing_and_guilds(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Track overlapping calls on one model by run ID and invocation metadata.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), cache=False)

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    model = stats_modules.model.create_model_instance("vllm:shared")
    responses = await asyncio.gather(
        model.ainvoke("one", config={"metadata": {"guild_id": "123"}}),
        model.ainvoke("two", config={"metadata": {"guild_id": "789"}}),
    )
    assert [response.content for response in responses] == ["ok", "ok"]
    rows = read_rows(db_path, "llm_call_events")
    assert len(rows) == 2
    assert {row[1] for row in rows} == {"123", "789"}
    assert all(row[-1] == 1 and row[-2] >= 15 for row in rows)


class _ErrorLog:
    """Capture error-level log calls made by the statistics callback."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.calls: list[tuple[str, bool]] = []

    def error(self, message: str, *args: Any, exc_info: bool = False, **kwargs: Any) -> None:
        """Record an error message and whether a traceback was requested."""
        self.calls.append((message % args if args else message, exc_info))


@pytest.mark.asyncio
async def test_missing_collector_never_breaks_the_model_call(
    stats_modules: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing collector is logged loudly, but the real model call still succeeds.

    The earlier expectation (the call must raise) was wrong: usage statistics are
    auxiliary data and must never veto the user-facing model invocation.

    Args:
        stats_modules: Isolated production modules.
        monkeypatch: Provider network replacement.
    """
    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), cache=False)

    error_log = _ErrorLog()
    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    monkeypatch.setattr(stats_modules.model, "log", error_log, raising=False)
    model = stats_modules.model.create_model_instance("vllm:local")
    response = await model.ainvoke("hello")
    assert response.content == "ok"
    assert any("collector" in message.lower() for message, _ in error_log.calls)


@pytest.mark.asyncio
async def test_failing_collector_never_breaks_the_model_call(
    stats_modules: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A database error while recording is logged with a traceback and swallowed.

    Args:
        stats_modules: Isolated production modules.
        monkeypatch: Provider network replacement.
    """
    class BrokenCollector:
        """Collector whose storage is unavailable."""

        async def record_llm_call(self, **kwargs: Any) -> None:
            """Fail like a locked SQLite database."""
            raise OSError("database is locked")

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), cache=False)

    error_log = _ErrorLog()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=BrokenCollector())
    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    monkeypatch.setattr(stats_modules.model, "log", error_log, raising=False)
    model = stats_modules.model.create_model_instance("vllm:local")
    response = await model.ainvoke("hello")
    assert response.content == "ok"
    assert error_log.calls
    assert all(with_traceback for _, with_traceback in error_log.calls)


@pytest.mark.asyncio
async def test_failing_collector_does_not_mask_the_provider_error(
    stats_modules: types.SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the provider fails and recording fails too, the provider error surfaces.

    Args:
        stats_modules: Isolated production modules.
        monkeypatch: Provider network replacement.
    """
    class BrokenCollector:
        """Collector whose storage is unavailable."""

        async def record_llm_call(self, **kwargs: Any) -> None:
            """Fail like a locked SQLite database."""
            raise OSError("database is locked")

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), fail=True, cache=False)

    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=BrokenCollector())
    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    monkeypatch.setattr(stats_modules.model, "log", _ErrorLog(), raising=False)
    model = stats_modules.model.create_model_instance("vllm:local")
    with pytest.raises(RuntimeError, match="provider unavailable"):
        await model.ainvoke("hello")


@pytest.mark.asyncio
async def test_configured_agent_fallback_models_are_recorded(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Record both the failed primary and successful configured fallback model.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)
    stats_modules.settings.llm_config.model_priorities = {
        "story_model": [{"openai": ["broken", "working"]}]
    }

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(
            callbacks=kwargs.get("callbacks"), fail=model_name.endswith(":broken"), cache=False,
        )

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    # Replace only provider construction inside LangChain's fallback middleware.
    import importlib
    fallback_module = importlib.import_module("langchain.agents.middleware.model_fallback")
    monkeypatch.setattr(fallback_module, "init_chat_model", offline_init)
    primary, fallback = stats_modules.manager.ModelManager().get_model("story_model")
    model = stats_modules.model.create_model_instance(primary)
    agent = create_agent(model, tools=[], middleware=[fallback])
    response = await agent.ainvoke(
        {"messages": [HumanMessage(content="hello")]},
        config={"metadata": {"guild_id": "123"}},
    )
    assert response["messages"][-1].content == "ok"
    assert [(row[1], row[2], row[-1]) for row in read_rows(db_path, "llm_call_events")] == [
        ("123", "openai:broken", 0), ("123", "openai:working", 1),
    ]


@pytest.mark.asyncio
async def test_memory_group_records_structured_failure_and_raw_retry_with_guild(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retain a message group's guild across structured failure and raw fallback.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
    """
    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(
            callbacks=kwargs.get("callbacks"), fail_tool_binding=True,
            response_content='{"fragments": []}', cache=False,
        )

    def priority_list(agent_type: str) -> list[str]:
        return ["vllm:local"]

    def system_prompt() -> str:
        return "Summarize the messages."

    def available(model_name: str) -> bool:
        return True

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    def circuit_breaker() -> types.SimpleNamespace:
        return types.SimpleNamespace(is_available=available)

    monkeypatch.setattr(stats_modules.memory, "get_model_circuit_breaker", circuit_breaker)
    service = stats_modules.memory.EventSummarizationService.__new__(
        stats_modules.memory.EventSummarizationService
    )
    service.settings = types.SimpleNamespace(vllm_url="http://memory-vllm.invalid")
    service.model_manager = types.SimpleNamespace(get_model_priority_list=priority_list)
    service._get_system_prompt = system_prompt
    message = types.SimpleNamespace(
        guild=types.SimpleNamespace(id=123),
        created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        author=types.SimpleNamespace(display_name="Alice"), content="hello",
    )
    assert await service._process_message_group([message]) == []
    assert [(row[1], row[2], row[-1]) for row in read_rows(db_path, "llm_call_events")] == [
        ("123", "vllm:local", 0), ("123", "vllm:local", 1),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("as_manager", [False, True])
async def test_existing_model_and_invocation_callbacks_survive(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    as_manager: bool,
) -> None:
    """Preserve constructor callbacks and callbacks supplied at invocation time.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
        as_manager: Whether callbacks use a manager rather than a list.
    """
    from uuid import UUID
    from langchain_core.outputs import LLMResult

    class AuditCallback(AsyncCallbackHandler):
        """Write independent callback lifecycle evidence to a temporary file."""

        async def on_llm_end(
            self, response: LLMResult, *, run_id: UUID, **kwargs: Any,
        ) -> None:
            """Persist evidence that an existing callback received the model result.

            Args:
                response: Real LangChain model result.
                run_id: Run identifier.
                **kwargs: Framework callback fields.
            """
            with (tmp_path / "audit.txt").open("a") as stream:
                stream.write(response.generations[0][0].text + "\n")

    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), cache=False)

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    callback = AuditCallback()
    callbacks = CallbackManager([callback]) if as_manager else [callback]
    model = stats_modules.model.create_model_instance("vllm:local", callbacks=callbacks)
    await model.ainvoke("hello", config={"callbacks": [AuditCallback()]})
    assert (tmp_path / "audit.txt").read_text().splitlines() == ["ok", "ok"]
    assert len(read_rows(db_path, "llm_call_events")) == 1


@pytest.mark.asyncio
async def test_agent_tool_loop_records_each_model_round(
    stats_modules: types.SimpleNamespace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Record two model rounds rather than one enclosing tool-using agent run.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
        monkeypatch: Provider network replacement.
    """
    from langchain_core.tools import tool

    @tool
    def lookup() -> str:
        """Return a lookup result.

        Returns:
            A deterministic lookup result.
        """
        return "lookup result"

    db_path = tmp_path / "stats.db"
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    stats_modules.singleton.bot = types.SimpleNamespace(stats_collector=collector)

    def offline_init(model_name: str, **kwargs: Any) -> BaseChatModel:
        return OfflineChatModel(callbacks=kwargs.get("callbacks"), use_tool=True, cache=False)

    monkeypatch.setattr(stats_modules.model, "init_chat_model", offline_init)
    model = stats_modules.model.create_model_instance("vllm:local", guild_id="123")
    agent = create_agent(model, tools=[lookup])
    response = await agent.ainvoke({"messages": [HumanMessage(content="hello")]})
    assert response["messages"][-1].content == "ok"
    assert [(row[1], row[2], row[-1]) for row in read_rows(db_path, "llm_call_events")] == [
        ("123", "vllm:local", 1), ("123", "vllm:local", 1),
    ]


@pytest.mark.asyncio
async def test_existing_database_rows_survive_initialization(
    stats_modules: types.SimpleNamespace, tmp_path: Path,
) -> None:
    """Keep historical events intact when initializing and appending new records.

    Args:
        stats_modules: Isolated production modules.
        tmp_path: Temporary database root.
    """
    db_path = tmp_path / "stats.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(stats_modules.collector._SCHEMA_SQL)
        connection.execute(
            "INSERT INTO command_events VALUES (?, ?, ?, ?, ?)",
            (42, "123", "456", "legacy", 1000.0),
        )
        connection.execute(
            "INSERT INTO llm_call_events VALUES (?, ?, ?, ?, ?, ?)",
            (42, "123", "legacy", 1000.0, 25.0, 1),
        )
    collector = stats_modules.collector.StatsCollector(str(db_path))
    await collector.initialize()
    await collector.record_command("123", "456", "new", timestamp=2000.0)
    await collector.record_llm_call("123", "new", 30.0, False, timestamp=2000.0)
    assert read_rows(db_path, "command_events") == [
        (42, "123", "456", "legacy", 1000.0), (43, "123", "456", "new", 2000.0),
    ]
    assert read_rows(db_path, "llm_call_events") == [
        (42, "123", "legacy", 1000.0, 25.0, 1), (43, "123", "new", 2000.0, 30.0, 0),
    ]
