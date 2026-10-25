"""Create instrumented chat models, including OpenAI-compatible vLLM models."""
from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Any
from uuid import UUID

from langchain.chat_models import init_chat_model
from langchain_core.callbacks import AsyncCallbackHandler, BaseCallbackManager
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from addons.logging import get_logger
from addons.settings import llm_config
from addons.tokens import tokens
from function import func

if TYPE_CHECKING:
    from dashboard.services.stats_collector import StatsCollector

log = get_logger(server_id="Bot", source=__name__)


class ModelStatsCallback(AsyncCallbackHandler):
    """Persist one event for each completed or failed LangChain model run.

    Timing is keyed by run ID so concurrent, batched, bound, and streaming calls
    share the same instrumentation. Guild ID ``0`` denotes calls without a guild
    context. Invocation metadata can supply a guild for a shared model instance.
    """

    raise_error: bool = False
    run_inline: bool = True

    def __init__(self, model_name: str, guild_id: str) -> None:
        """Initialize per-model recording state.

        Args:
            model_name: Original provider-qualified model identifier.
            guild_id: Guild context, or ``0`` for a context-free invocation.
        """
        self.model_name = model_name
        self.guild_id = guild_id
        self._runs: dict[UUID, tuple[float, float, str, StatsCollector]] = {}

    async def on_chat_model_start(
        self, serialized: dict[str, Any], messages: list[list[BaseMessage]], *,
        run_id: UUID, metadata: dict[str, Any] | None = None, **kwargs: Any,
    ) -> None:
        """Capture wall-clock start time and a monotonic duration baseline.

        Args:
            serialized: LangChain model description.
            messages: Input batches.
            run_id: Unique invocation identifier.
            metadata: Invocation metadata, optionally containing guild_id.
            **kwargs: Additional LangChain callback fields.

        Statistics are auxiliary: a missing collector or a null guild ID is logged
        at error level and the invocation is simply not recorded. It must never
        raise, because that would fail the real model call.
        """
        collector = getattr(func.bot, "stats_collector", None)
        if collector is None:
            log.error("Stats collector is unavailable; model invocation %s is not recorded", self.model_name)
            return
        guild_id = (metadata or {}).get("guild_id", self.guild_id)
        if guild_id is None:
            log.error("Model invocation guild_id is None; %s is not recorded", self.model_name)
            return
        self._runs[run_id] = (time.time(), time.perf_counter(), str(guild_id), collector)

    async def on_llm_end(
        self, response: LLMResult, *, run_id: UUID, **kwargs: Any,
    ) -> None:
        """Record a successful provider invocation.

        Args:
            response: Provider result, before downstream output parsing.
            run_id: Unique invocation identifier.
            **kwargs: Additional LangChain callback fields.
        """
        await self._record(run_id, success=True)

    async def on_llm_error(
        self, error: BaseException, *, run_id: UUID, **kwargs: Any,
    ) -> None:
        """Record provider errors, including timeout cancellation and stream errors.

        Args:
            error: Original provider exception or cancellation.
            run_id: Unique invocation identifier.
            **kwargs: Additional LangChain callback fields.
        """
        await self._record(run_id, success=False)

    async def _record(self, run_id: UUID, success: bool) -> None:
        """Persist a terminal event without including SQLite latency in duration.

        Recording failures are logged and swallowed so they cannot fail the model call.
        """
        run = self._runs.pop(run_id, None)
        if run is None:
            return
        timestamp, started_at, guild_id, collector = run
        duration_ms = (time.perf_counter() - started_at) * 1000
        try:
            await collector.record_llm_call(
                guild_id=guild_id, model_name=self.model_name,
                duration_ms=duration_ms, success=success, timestamp=timestamp,
            )
        except Exception:
            # Statistics are auxiliary; a storage failure must not break or mask the
            # user-facing model call, so execution continues after logging the traceback.
            log.error("Failed to record LLM call statistics for %s", self.model_name, exc_info=True)


def _output_limit_options(model_name: str) -> dict[str, Any]:
    """Return the provider option that caps how many tokens one call may generate.

    Args:
        model_name: Provider-qualified identifier, such as ``vllm:gemma4-26b``.

    Returns:
        The constructor option for the configured cap, or an empty dict when the cap is
        disabled or the provider's option name is not known.
    """
    cap = llm_config.max_output_tokens
    if cap <= 0:
        return {}
    if model_name.startswith("google_genai:"):
        return {"max_output_tokens": cap}
    if model_name.startswith(("vllm:", "openai:", "anthropic:")) or _endpoint_name(model_name):
        return {"max_tokens": cap}
    return {}


def _endpoint_name(model_name: str) -> str | None:
    """Return the configured OpenAI-compatible endpoint that serves a model string, if any.

    Args:
        model_name: Provider-qualified identifier, such as ``steak:qwen``.

    Returns:
        The endpoint name from ``openai_endpoints`` in llm.yaml, or None when the
        provider prefix is not a configured endpoint.
    """
    provider = model_name.split(":", 1)[0]
    return provider if provider in llm_config.openai_endpoints else None


def create_model_instance(
    model_name: str, *, guild_id: str = "0", limit_output: bool = False, **kwargs: Any,
) -> BaseChatModel:
    """Create a chat model with statistics attached to its invocation lifecycle.

    vLLM models use ChatOpenAI with the configured OpenAI-compatible endpoint.
    The callback retains the original model name and survives tool bindings,
    structured output, agent execution, and synchronous or asynchronous streams.
    Existing caller callbacks are preserved. Recording failures are logged at error
    level and never interrupt the model call.

    Args:
        model_name: Provider-qualified identifier, such as ``vllm:gemma4:26b``.
        guild_id: Guild context, or ``0`` when no guild applies. Per-invocation
            ``metadata.guild_id`` overrides this value for shared instances.
        limit_output: Cap the tokens one call may generate at the configured
            ``max_output_tokens``, so a model stuck in a loop is stopped by the server.
            An explicit cap in ``kwargs`` takes precedence.
        **kwargs: Options forwarded to the provider constructor.

    Returns:
        A chat model with usage-statistics instrumentation.
    """
    if limit_output:
        for option, value in _output_limit_options(model_name).items():
            kwargs.setdefault(option, value)
    endpoint_name = _endpoint_name(model_name)
    if model_name.startswith("vllm:"):
        provider_options: dict[str, Any] = {
            "base_url": f"{llm_config.vllm_url}/v1",
            "api_key": tokens.vllm_api_key,
        }
        provider_options.update(kwargs)
        model = init_chat_model(
            f"openai:{model_name[len('vllm:'):]}", **provider_options,
        )
    elif endpoint_name is not None:
        endpoint = llm_config.openai_endpoints[endpoint_name]
        key_variable = endpoint["api_key_env"]
        api_key = os.environ.get(key_variable)
        if not api_key:
            raise ValueError(
                f"Endpoint '{endpoint_name}' needs the API key in the {key_variable} environment variable"
            )
        provider_options = {"base_url": endpoint["base_url"], "api_key": api_key}
        provider_options.update(kwargs)
        model = init_chat_model(
            f"openai:{model_name[len(endpoint_name) + 1:]}", **provider_options,
        )
    else:
        model = init_chat_model(model_name, **kwargs)
    callback = ModelStatsCallback(model_name, guild_id)
    if isinstance(model.callbacks, BaseCallbackManager):
        model.callbacks = model.callbacks.copy()
        model.callbacks.add_handler(callback)
    else:
        model.callbacks = [*(model.callbacks or []), callback]
    return model


__all__ = ["create_model_instance"]
