"""Isolate usage-statistics tests from production configuration and storage."""
from __future__ import annotations

import importlib.util
import logging
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from usage_stats.runtime import FRAMEWORK_MODULES

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_source(name: str, relative_path: str) -> types.ModuleType:
    """Load a production module without importing unrelated package initializers.

    Args:
        name: Isolated module name.
        relative_path: Source path relative to the worktree.

    Returns:
        The loaded production module.
    """
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def stats_modules(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> types.SimpleNamespace:
    """Load real recording code with only configuration and service boundaries stubbed.

    Args:
        monkeypatch: Scoped dependency replacement.
        tmp_path: Temporary storage root.

    Returns:
        Production modules and their isolated bot singleton.
    """
    for name, module in FRAMEWORK_MODULES.items():
        monkeypatch.setitem(sys.modules, name, module)

    def stub(name: str, **attributes: Any) -> types.ModuleType:
        module = types.ModuleType(name)
        module.__dict__.update(attributes)
        monkeypatch.setitem(sys.modules, name, module)
        return module

    def get_logger(*args: Any, **kwargs: Any) -> logging.Logger:
        return logging.getLogger("usage_stats_tests")

    async def report_error(error: Exception, details: str) -> None:
        raise error

    singleton = types.SimpleNamespace(bot=None, report_error=report_error)
    settings = stub(
        "addons.settings",
        llm_config=types.SimpleNamespace(vllm_url="http://vllm.invalid", llm_call_timeout=1.0),
        prompt_config=types.SimpleNamespace(),
        MemoryConfig=object,
    )
    monkeypatch.setattr(sys.modules["addons"], "settings", settings)
    stub("addons.logging", get_logger=get_logger)
    stub("addons.tokens", tokens=types.SimpleNamespace(vllm_api_key="test-key"))
    stub("function", ROOT_DIR=str(tmp_path), func=singleton)
    stub("cogs.memory.db.stats_storage", StatsStorage=object)
    collector = load_source("_usage_stats_collector", "dashboard/services/stats_collector.py")
    cog = load_source("_usage_stats_cog", "cogs/stats_cog.py")
    model = load_source("_usage_model_init", "llm/utils/model_init.py")
    stub("llm.utils.model_init", create_model_instance=model.create_model_instance)
    stub("llm.model_manager", ModelManager=object)
    stub("llm.model_circuit_breaker", get_model_circuit_breaker=object)
    memory = load_source(
        "_usage_memory_summary", "cogs/memory/services/event_summarization_service.py"
    )
    manager = load_source("_usage_model_manager", "llm/model_manager.py")
    return types.SimpleNamespace(
        collector=collector, cog=cog, model=model, memory=memory,
        singleton=singleton, settings=settings, manager=manager,
    )
