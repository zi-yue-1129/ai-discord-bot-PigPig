"""Root pytest configuration.

Pre-loads the real ``addons.settings`` and ``discord`` modules, and isolates
the ``sys.modules`` stubs that individual test modules install at import time.

Many test modules replace project packages (``cogs``, ``addons.settings``,
``function`` ...) with lightweight stubs at module level. Because pytest
imports every test module during collection, before any test runs, those
stubs used to leak into every module collected afterwards and made the
suite's result depend on collection order. The hooks below record the
``sys.modules`` changes each test module makes while it is imported, undo
them right after collection, and re-apply them only while that module's
tests run.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Generator

import discord
import pytest

# Cache the real settings module before any test module installs a stub.
importlib.import_module("addons.settings")

sys.modules["discord"] = discord

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MISSING: Any = object()
_SYS_MODULES_DELTA_KEY = pytest.StashKey[dict]()


def _needs_isolation(module: Any) -> bool:
    """Return whether a ``sys.modules`` entry must be scoped to one test module.

    Stubs (objects without an import spec) and project modules (which may have
    bound stub symbols at import time) are isolated. Real third-party and
    standard-library modules are left cached, since some C extensions cannot
    be imported twice in one process.

    Args:
        module: A value stored in ``sys.modules``.

    Returns:
        True if the entry must be reverted outside its test module.
    """
    if getattr(module, "__spec__", None) is None:
        return True
    module_file = getattr(module, "__file__", None)
    if module_file is None:
        return False
    return Path(module_file).resolve().is_relative_to(_PROJECT_ROOT)


def _diff_sys_modules(before: dict[str, Any]) -> dict[str, Any]:
    """Compute the isolated ``sys.modules`` changes made since *before*.

    Args:
        before: A shallow copy of ``sys.modules`` taken earlier.

    Returns:
        Mapping of module name to its new value, or ``_MISSING`` if removed.
    """
    delta: dict[str, Any] = {}
    for name, module in sys.modules.items():
        previous = before.get(name, _MISSING)
        if previous is module:
            continue
        if previous is not _MISSING or _needs_isolation(module):
            delta[name] = module
    for name in before:
        if name not in sys.modules:
            delta[name] = _MISSING
    return delta


def _apply_sys_modules(changes: dict[str, Any]) -> dict[str, Any]:
    """Apply *changes* to ``sys.modules`` and return what they replaced.

    Args:
        changes: Mapping of module name to value, or ``_MISSING`` to remove.

    Returns:
        Mapping that, when applied, restores the previous state.
    """
    previous: dict[str, Any] = {}
    for name, module in changes.items():
        previous[name] = sys.modules.get(name, _MISSING)
        if module is _MISSING:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module
    return previous


@pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector: pytest.Collector) -> Generator[None, None, None]:
    """Record and undo the ``sys.modules`` changes a test module makes on import.

    Args:
        collector: The collector being collected.

    Yields:
        Control to the default collection implementation.
    """
    is_test_module = isinstance(collector, pytest.Module)
    before = dict(sys.modules) if is_test_module else {}
    yield
    if is_test_module:
        delta = _diff_sys_modules(before)
        collector.stash[_SYS_MODULES_DELTA_KEY] = delta
        _apply_sys_modules({name: before.get(name, _MISSING) for name in delta})


@pytest.fixture(autouse=True, scope="module")
def _isolated_sys_modules(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Re-apply the current module's ``sys.modules`` stubs while its tests run.

    Project modules first imported during the run are dropped afterwards, as
    they may have bound this module's stubs.

    Args:
        request: The pytest fixture request for the test module.

    Yields:
        Control to the module's tests.
    """
    delta = request.node.stash.get(_SYS_MODULES_DELTA_KEY, {})
    previous = _apply_sys_modules(delta)
    before_run = dict(sys.modules)
    yield
    added_during_run = {
        name: _MISSING
        for name, module in _diff_sys_modules(before_run).items()
        if name not in previous and module is not _MISSING
    }
    _apply_sys_modules(added_during_run)
    _apply_sys_modules(previous)
