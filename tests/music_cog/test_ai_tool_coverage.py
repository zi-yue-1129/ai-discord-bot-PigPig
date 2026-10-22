"""Every music action a user can take is either an AI tool or deliberately kept away from the AI.

The slash commands and the player's buttons are scanned in a fresh interpreter (so test doubles
from other tests cannot hide a gap). A new command or button without an entry in
``MUSIC_ACTION_TOOLS`` or ``MUSIC_ACTIONS_NOT_FOR_AI`` fails here, which is the point: the bot
once had a button for autoplay but no tool, and answered "autoplay is on" by changing the loop mode.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent.parent

_SCAN = '''
import ast
import importlib
import json
import pkgutil
from pathlib import Path
from types import SimpleNamespace

import cogs
from discord import app_commands
from discord.ext import commands

from llm.tools.music_tools import MUSIC_ACTION_TOOLS, MUSIC_ACTIONS_NOT_FOR_AI, MusicTools


def leaves(command, prefix=""):
    if isinstance(command, app_commands.Group):
        for child in command.commands:
            yield from leaves(child, prefix + command.name + " ")
    else:
        yield prefix + command.name


actions, seen = [], set()
for info in pkgutil.walk_packages(cogs.__path__, "cogs."):
    if info.ispkg or not info.name.startswith("cogs.music"):
        continue
    module = importlib.import_module(info.name)
    for value in vars(module).values():
        if isinstance(value, type) and issubclass(value, commands.Cog) and value.__module__ == module.__name__ and value not in seen:
            seen.add(value)
            prefix = value.__cog_group_name__ + " " if issubclass(value, commands.GroupCog) else ""
            for command in value.__cog_app_commands__:
                actions.extend("command:" + name for name in leaves(command, prefix))

tree = ast.parse(Path("cogs/music_lib/ui/controls.py").read_text(encoding="utf-8"))
controls = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        for keyword in node.keywords:
            if keyword.arg == "custom_id" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                kind = "menu" if getattr(node.func, "attr", "") == "Select" else "button"
                controls.add(f"{kind}:{keyword.value.value}")
        if getattr(node.func, "attr", "") == "_add_queue_menu" and node.args and isinstance(node.args[0], ast.Constant):
            controls.add("menu:" + node.args[0].value)
    if isinstance(node, ast.ClassDef) and node.name == "QueueSongActions":
        for inner in ast.walk(node):
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str) and inner.value.startswith("queue_") and inner.value.count("_") >= 1 and inner.value in ("queue_play_next", "queue_remove"):
                controls.add("button:" + inner.value)
actions.extend(sorted(controls))

runtime = SimpleNamespace(
    bot=SimpleNamespace(),
    message=SimpleNamespace(guild=None, author=SimpleNamespace(id=1), channel=SimpleNamespace(id=1)),
    logger=None,
)
tool_names = sorted(tool.name for tool in MusicTools(runtime).get_tools())
print(json.dumps({
    "actions": sorted(actions),
    "tools": MUSIC_ACTION_TOOLS,
    "not_for_ai": MUSIC_ACTIONS_NOT_FOR_AI,
    "tool_names": tool_names,
}))
'''


def _scan() -> dict:
    """Runs the scan in a fresh interpreter at the repository root and returns its JSON."""
    done = subprocess.run(
        [sys.executable, "-c", _SCAN], cwd=ROOT, capture_output=True, text=True, timeout=180, check=False
    )
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_every_music_command_and_control_is_an_ai_tool_or_deliberately_not() -> None:
    result = _scan()
    known = set(result["tools"]) | set(result["not_for_ai"])

    missing = [action for action in result["actions"] if action not in known]

    assert missing == [], (
        "These music actions have no AI tool and are not listed as deliberately kept from the AI. "
        "Add a tool, or add them with a reason to MUSIC_ACTIONS_NOT_FOR_AI in llm/tools/music_tools.py: "
        f"{missing}"
    )


def test_the_coverage_lists_name_no_action_that_no_longer_exists() -> None:
    result = _scan()
    known = set(result["tools"]) | set(result["not_for_ai"])

    stale = sorted(known - set(result["actions"]))

    assert stale == [], f"These entries match no command or control any more: {stale}"


def test_an_action_is_not_both_a_tool_and_deliberately_not() -> None:
    result = _scan()

    both = sorted(set(result["tools"]) & set(result["not_for_ai"]))

    assert both == []


def test_every_tool_named_in_the_coverage_exists() -> None:
    result = _scan()
    tools: Dict[str, str] = result["tools"]

    unknown = sorted({tool for tool in tools.values() if tool not in result["tool_names"]})

    assert unknown == []


def test_every_deliberate_omission_says_why() -> None:
    result = _scan()
    reasons: Dict[str, str] = result["not_for_ai"]

    unexplained: List[str] = [action for action, reason in reasons.items() if len(reason.strip()) < 15]

    assert unexplained == []
