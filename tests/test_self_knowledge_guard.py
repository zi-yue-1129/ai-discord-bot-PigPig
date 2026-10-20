"""The bot can only describe itself as well as its commands and tools describe themselves.

These checks load the real cogs and tool modules in a fresh interpreter (so test doubles from
other tests cannot hide a problem) and fail when someone adds a command or tool without text.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent

_SCAN_COMMANDS = """
import importlib, json, pkgutil
from discord import app_commands
from discord.ext import commands
import cogs

def leaves(command, prefix=""):
    if isinstance(command, app_commands.Group):
        for child in command.commands:
            yield from leaves(child, prefix + command.name + " ")
    else:
        yield prefix + command.name, command

offenders, seen, total = [], set(), 0
for info in pkgutil.walk_packages(cogs.__path__, "cogs."):
    if info.ispkg:
        continue
    module = importlib.import_module(info.name)
    for value in vars(module).values():
        if isinstance(value, type) and issubclass(value, commands.Cog) and value.__module__ == module.__name__ and value not in seen:
            seen.add(value)
            for command in value.__cog_app_commands__:
                for name, leaf in leaves(command):
                    total += 1
                    if (leaf.description or "").strip() in ("", "…"):
                        offenders.append(name)
print(json.dumps({"total": total, "offenders": offenders}))
"""

_SCAN_TOOLS = """
import importlib, json, pkgutil
from types import SimpleNamespace
import llm.tools as package

runtime = SimpleNamespace(
    bot=SimpleNamespace(),
    message=SimpleNamespace(guild=None, author=SimpleNamespace(id=1), channel=SimpleNamespace(id=1)),
    logger=None,
)
offenders, total = [], 0
for info in pkgutil.iter_modules(package.__path__):
    module = importlib.import_module("llm.tools." + info.name)
    for name, value in vars(module).items():
        if isinstance(value, type) and name.endswith("Tools") and value.__module__ == module.__name__:
            for tool in value(runtime).get_tools():
                total += 1
                if len((tool.description or "").strip()) < 20:
                    offenders.append(tool.name)
print(json.dumps({"total": total, "offenders": offenders}))
"""


def _scan(script: str) -> dict:
    """Run ``script`` in a fresh interpreter at the repository root and return its JSON."""
    done = subprocess.run(
        [sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, timeout=180, check=False
    )
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_every_slash_command_has_a_real_description() -> None:
    result = _scan(_SCAN_COMMANDS)

    assert result["total"] > 30
    assert result["offenders"] == []


def test_every_ai_tool_has_a_real_description() -> None:
    result: dict = _scan(_SCAN_TOOLS)
    offenders: List[str] = result["offenders"]

    assert result["total"] > 30
    assert offenders == []
